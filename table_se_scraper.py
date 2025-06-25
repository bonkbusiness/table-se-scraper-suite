# ========================
# 1. Install dependencies
# ========================
!pip install requests beautifulsoup4 openpyxl

# ========================
# 2. Imports and Logging
# ========================
import requests
from bs4 import BeautifulSoup
import re
import unicodedata
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from urllib.parse import urljoin, urlparse

# ========================
# Imports main_enhanced from table_se_scraper_backend
# ========================
from table_se_scraper_backend_enhanced import main_enhanced


# ========================
# Imports scanner functions from table_se_smart_scanner
# ========================
from table_se_smart_scanner import smart_scan_products
products, product_errors = smart_scan_products(products)


import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)
logger = logging.getLogger("table_scraper")

def logprint(msg):
    print(msg)
    logger.info(msg)

BASE_URL = "https://www.table.se"

# ========================
# 3. Utility functions
# ========================
def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    trans = str.maketrans("åäö", "aao")
    text = text.translate(trans)
    text = unicodedata.normalize('NFKD', text).encode('ascii','ignore').decode()
    return text.strip()

def parse_measurements(text):
    result = {
        "Mått (text)": text,
        "Längd (värde)": "", "Längd (enhet)": "",
        "Bredd (värde)": "", "Bredd (enhet)": "",
        "Höjd (värde)": "", "Höjd (enhet)": "",
        "Diameter (värde)": "", "Diameter (enhet)": "",
    }
    if not text:
        return result
    m3 = re.match(r"(\d+)[x×](\d+)[x×](\d+)\s*([a-zA-Z]+)", text)
    if m3:
        result["Längd (värde)"], result["Bredd (värde)"], result["Höjd (värde)"], enhet = m3.groups()
        result["Längd (enhet)"] = result["Bredd (enhet)"] = result["Höjd (enhet)"] = enhet
        return result
    m_dia = re.match(r"[ØO]\s*\.?\s*(\d+)\s*([a-zA-Z]+)", text)
    if m_dia:
        result["Diameter (värde)"], result["Diameter (enhet)"] = m_dia.groups()
        return result
    m_single = re.match(r"(Längd|Bredd|Höjd|Diameter)?\s*:?\.?\s*(\d+)\s*([a-zA-Z]+)", text, re.IGNORECASE)
    if m_single:
        label, value, enhet = m_single.groups()
        if label:
            label = label.capitalize()
            result[f"{label} (värde)"] = value
            result[f"{label} (enhet)"] = enhet
        else:
            result["Längd (värde)"] = value
            result["Längd (enhet)"] = enhet
        return result
    return result

def parse_value_unit(text):
    val_unit = re.match(r"^\s*([\d.,]+)\s*([^\d\s]+.*)?$", text or "")
    if val_unit:
        value, unit = val_unit.groups()
        value = value.replace(",", ".")
        return value, (unit or "").strip()
    return "", ""

def should_skip(catname):
    EXCLUDE_RAW = [
        "Hyra container", "Förrådscontainrar", "Kylcontainrar", "Fryscontainrar", "Kök & disk", "Toalettbodar",
        "Kontorsbodar", "Eventcontainrar", "Specialcontainrar", "Containertillbehör", "Köpa container",
        "Begagnade containrar", "Self storage", "Flytt & förvaringsservice", "Transporter"
    ]
    EXCLUDE_NORMALIZED = [normalize_text(x) for x in EXCLUDE_RAW]
    return normalize_text(catname) in EXCLUDE_NORMALIZED

def get_soup(url):
    logprint(f"Hämtar: {url}")
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logprint(f"Kunde inte hämta {url}: {e}")
        return None

# ========================
# 4. Category extraction (3 levels deep)
# ========================
def extract_category_tree():
    resp = requests.get(BASE_URL + "/produkter/")
    soup = BeautifulSoup(resp.text, "html.parser")
    main_categories = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a['href']
        url = urljoin(BASE_URL, href)
        parsed = urlparse(href)
        if parsed.path.startswith("/produkter/") and not "/page/" in parsed.path and not "/nyheter/" in parsed.path:
            path_parts = [p for p in parsed.path.split("/") if p]
            if len(path_parts) == 2 or (len(path_parts) == 3 and path_parts[2] == ""):
                catname = a.get_text(strip=True)
                if catname and catname != "HEM" and url not in seen:
                    seen.add(url)
                    main_categories.append({"name": catname, "url": url})
    logprint(f"Hittade {len(main_categories)} huvudkategorier")

    tree = []
    for cat in main_categories:
        node = {"name": cat["name"], "url": cat["url"], "subs": []}
        sub_soup = get_soup(cat["url"])
        subcats = []
        seen_sub = set()
        if sub_soup:
            for a in sub_soup.find_all("a", href=True):
                href = a['href']
                url_sub = urljoin(BASE_URL, href)
                parsed = urlparse(href)
                path_parts = [p for p in parsed.path.split("/") if p]
                if (
                    len(path_parts) == 3 and
                    path_parts[0] == "produkter" and
                    path_parts[1] == urlparse(cat["url"]).path.split("/")[2]
                ):
                    catname = a.get_text(strip=True)
                    if catname and catname != "HEM" and url_sub not in seen_sub:
                        seen_sub.add(url_sub)
                        subcats.append({"name": catname, "url": url_sub})
        # Go one level deeper (sub-subcategories)
        for sub in subcats:
            subsub_soup = get_soup(sub["url"])
            subsubs = []
            seen_subsub = set()
            if subsub_soup:
                for a in subsub_soup.find_all("a", href=True):
                    href = a['href']
                    url2 = urljoin(BASE_URL, href)
                    parsed2 = urlparse(href)
                    path_parts2 = [p for p in parsed2.path.split("/") if p]
                    if (
                        len(path_parts2) == 4 and
                        path_parts2[0] == "produkter" and
                        path_parts2[1] == urlparse(cat["url"]).path.split("/")[2] and
                        path_parts2[2] == urlparse(sub["url"]).path.split("/")[3]
                    ):
                        name2 = a.get_text(strip=True)
                        if name2 and name2 != "HEM" and url2 not in seen_subsub:
                            seen_subsub.add(url2)
                            subsubs.append({"name": name2, "url": url2})
            sub["subs"] = subsubs
        node["subs"] = subcats
        tree.append(node)
    return tree

# ========================
# 5. Scraper functions (3-level deep)
# ========================
def extract_products_from_category(category_url):
    product_urls = set()
    page = 1
    while True:
        paged_url = f"{category_url}?page={page}" if page > 1 else category_url
        soup = get_soup(paged_url)
        if not soup:
            break
        product_links = soup.select("ul.products li.product a.woocommerce-LoopProduct-link")
        if not product_links:
            break
        for link in product_links:
            href = link.get("href")
            if href:
                product_urls.add(href)
        next_page = soup.select_one("a.next")
        if not next_page:
            break
        page += 1
    logprint(f"Hittade {len(product_urls)} produkter i kategori: {category_url}")
    return list(product_urls)

def extract_product_data(product_url):
    soup = get_soup(product_url)
    if not soup:
        logprint(f"Kunde inte ladda produkt: {product_url}")
        return None
    try:
        namn = soup.select_one("h1.product_title").get_text(strip=True)
    except Exception:
        namn = ""
    artikelnummer = soup.select_one(".sku").get_text(strip=True) if soup.select_one(".sku") else ""
    pris_inkl = soup.select_one("p.price ins .amount, p.price .amount")
    pris_inkl = pris_inkl.get_text(strip=True).replace("kr", "").replace(" ", "").replace(",", ".") if pris_inkl else ""
    pris_exkl = ""
    if pris_inkl:
        try:
            pris_exkl = str(round(float(pris_inkl)/1.25, 2))
        except Exception:
            pris_exkl = ""
    produktbild_url = ""
    img = soup.select_one(".woocommerce-product-gallery__image img")
    if img and img.get("src"):
        produktbild_url = img.get("src")
    attr_texts = {}
    attr_rows = soup.select(".woocommerce-product-attributes-item")
    for row in attr_rows:
        key = row.select_one(".woocommerce-product-attributes-item__label")
        val = row.select_one(".woocommerce-product-attributes-item__value")
        if key and val:
            attr_texts[key.get_text(strip=True).lower()] = val.get_text(" ", strip=True)
    m_att = attr_texts.get("mått", "")
    mått_dict = parse_measurements(m_att)
    d_att = attr_texts.get("diameter", "")
    diameter_v, diameter_e = parse_value_unit(d_att)
    if not diameter_v and mått_dict.get("Diameter (värde)"):
        diameter_v = mått_dict.get("Diameter (värde)")
        diameter_e = mått_dict.get("Diameter (enhet)")
    kap_att = attr_texts.get("kapacitet", "")
    kap_v, kap_e = parse_value_unit(kap_att)
    vol_att = attr_texts.get("volym", "")
    vol_v, vol_e = parse_value_unit(vol_att)
    längd_v, längd_e = mått_dict.get("Längd (värde)"), mått_dict.get("Längd (enhet)")
    bredd_v, bredd_e = mått_dict.get("Bredd (värde)"), mått_dict.get("Bredd (enhet)")
    höjd_v, höjd_e = mått_dict.get("Höjd (värde)"), mått_dict.get("Höjd (enhet)")
    färg = attr_texts.get("färg", "")
    material = attr_texts.get("material", "")
    serie = attr_texts.get("serie", "")
    data = {
        "Namn": namn,
        "Artikelnummer": artikelnummer,
        "Pris exkl. moms (värde)": pris_exkl,
        "Pris exkl. moms (enhet)": "kr" if pris_exkl else "",
        "Pris inkl. moms (värde)": pris_inkl,
        "Pris inkl. moms (enhet)": "kr" if pris_inkl else "",
        "Mått (text)": mått_dict.get("Mått (text)"),
        "Längd (värde)": längd_v,
        "Längd (enhet)": längd_e,
        "Bredd (värde)": bredd_v,
        "Bredd (enhet)": bredd_e,
        "Höjd (värde)": höjd_v,
        "Höjd (enhet)": höjd_e,
        "Diameter (värde)": diameter_v,
        "Diameter (enhet)": diameter_e,
        "Kapacitet (värde)": kap_v,
        "Kapacitet (enhet)": kap_e,
        "Volym (värde)": vol_v,
        "Volym (enhet)": vol_e,
        "Färg": färg,
        "Material": material,
        "Serie": serie,
        "Produktbild-URL": produktbild_url,
        "Produkt-URL": product_url
    }
    logprint(f"Extraherad produkt: {namn} (URL: {product_url})")
    return data

def scrape_all_products_deep():
    tree = extract_category_tree()
    all_products = []
    for cat in tree:
        if should_skip(cat["name"]):
            continue
        if cat["subs"]:
            for sub in cat["subs"]:
                if should_skip(sub["name"]):
                    continue
                if sub["subs"]:
                    for subsub in sub["subs"]:
                        if should_skip(subsub["name"]):
                            continue
                        urls = extract_products_from_category(subsub["url"])
                        for url in urls:
                            try:
                                pdata = extract_product_data(url)
                                if pdata:
                                    all_products.append(pdata)
                            except Exception as e:
                                logprint(f"Kunde inte extrahera produkt: {url} ({e})")
                else:
                    urls = extract_products_from_category(sub["url"])
                    for url in urls:
                        try:
                            pdata = extract_product_data(url)
                            if pdata:
                                all_products.append(pdata)
                        except Exception as e:
                            logprint(f"Kunde inte extrahera produkt: {url} ({e})")
        else:
            urls = extract_products_from_category(cat["url"])
            for url in urls:
                try:
                    pdata = extract_product_data(url)
                    if pdata:
                        all_products.append(pdata)
                except Exception as e:
                    logprint(f"Kunde inte extrahera produkt: {url} ({e})")
    logprint(f"Totalt antal produkter extraherade: {len(all_products)}")
    return all_products

# ========================
# 6. XLSX Exporter
# ========================
def pastel_color_for_category(category):
    pastel_palette = {
        "Möbler":             "FFB3E5FC", # Light Blue
        "Dukning":            "FFFFF9C4", # Light Yellow
        "Tält":               "FFDCEDC8", # Light Green
        "Bar & barutrustning":"FFFFCCBC", # Light Orange
        "Servering":          "FFFFF8E1", # Light Cream
        "Köksutrustning":     "FFD1C4E9", # Light Purple
        "Engångsartiklar":    "FFFFFDE7", # Pale Yellow
        "Garderob & entré":   "FFE1BEE7", # Pastel Lavender
        "Teknik & scen":      "FFB2EBF2", # Pastel Cyan
        "Containrar":         "FFFFE0B2", # Pastel Peach
        "Hyra container":     "FFFFF3E0", # Pastel Apricot
        "Köpa container":     "FFF8BBD0", # Pastel Pink
        "Self storage":       "FFB2DFDB", # Pastel Mint
        "Kylcontainrar":      "FFC5CAE9", # Pastel Indigo
        "Förrådscontainrar":  "FFFFF9C4", # Light Yellow
        "Kök & disk":         "FFDCEDC8", # Pastel Green
        "Toalettbodar":       "FFFFFDE7", # Pale Yellow
        "Kontorsbodar":       "FFE1F5FE", # Light Aquamarine
        "Eventcontainrar":    "FFFFF8E1", # Cream
        "Specialcontainrar":  "FFF3E5F5", # Pastel Purple
        "Containertillbehör": "FFF0F4C3", # Pastel Lime
        "Begagnade containrar":"FFD7CCC8", # Pastel Brown
        "Flytt & förvaringsservice":"FFFFF9C4", # Light Yellow
        "Transporter":        "FFE0F7FA", # Pastel Blue
        # Deep subcategories for Table.se
        "Bord":               "FFE3F2FD",
        "Stolar":             "FFE0F7FA",
        "Soffor & fåtöljer":  "FFF8BBD0",
        "Konferensmöbler":    "FFDCEDC8",
        "Loungemöbler":       "FFD7CCC8",
        "Utemöbler":          "FFFFF9C4",
        "Övriga möbler":      "FFFCE4EC",
        "Glas":               "FFE1F5FE",
        "Porslin":            "FFF3E5F5",
        "Bestick":            "FFEFEBE9",
        "Bordsdekor":         "FFF8BBD0",
        "Linne & överdrag":   "FFE0F7FA",
        "Tälttillbehör":      "FFF1F8E9",
        # Add more as needed
    }
    return pastel_palette.get(category, "FFF5F5F5")

def export_to_xlsx(data, base_name="table_produkter"):
    if not data:
        print("Ingen data att exportera till XLSX.")
        return None
    from datetime import datetime
    filename = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Produkter"

    headers = list(data[0].keys())
    # Insert Category, Subcategory, Sub-Subcategory at front if not already present
    for col in ["Category", "Subcategory", "Sub-Subcategory"]:
        if col not in headers and any(col in row for row in data):
            headers = [col] + headers

    ws.append(headers)

    # Header style: Material dark, bold, white text
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFFFF")
        cell.fill = PatternFill("solid", fgColor="FF212121")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(bottom=Side(style="medium", color="FFB0BEC5"))

    # Data rows: pastel color per category or subcategory
    for row in data:
        ws.append([row.get(h, "") for h in headers])
        row_idx = ws.max_row
        # Prefer category, then subcategory, then fallback
        category = row.get("Category") or row.get("category") or ""
        subcategory = row.get("Subcategory") or row.get("subcategory") or ""
        # Use subcategory color if present in palette, else category
        pastel_color = pastel_color_for_category(subcategory) if pastel_color_for_category(subcategory) != "FFF5F5F5" else pastel_color_for_category(category)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.fill = PatternFill("solid", fgColor=pastel_color)
            cell.font = Font(color="FF212121")
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            cell.border = Border(
                left=Side(style="thin", color="FFCFD8DC"),
                right=Side(style="thin", color="FFCFD8DC"),
                top=Side(style="thin", color="FFCFD8DC"),
                bottom=Side(style="thin", color="FFCFD8DC"),
            )

    # Dynamically set column widths with padding
    for col in ws.columns:
        max_length = max(len(str(cell.value) or "") for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 6

    wb.save(filename)
    print(f"Export till XLSX klar: {filename}")
    return filename

# ========================
# 7. Main function
# ========================
def main():
    logprint("==== STARTAR TABLE.SE SUPER-SCRAPER (3 nivåer) ====")
    products = scrape_all_products_deep()
    xlsx_file = None
    if products:
        xlsx_file = export_to_xlsx(products)
    logprint("==== KLAR! ====")
    return xlsx_file

# ========================
# 8. Run and download
# ========================


#xlsx_path = main()
#
#if xlsx_path:
#    from google.colab import files
#    files.download(xlsx_path)
#    print(f"Din fil {xlsx_path} är redo för nedladdning!")
#else:
#    print("Ingen fil skapades.")

if __name__ == "__main__":
    # Import your original functions if not in this file
    from table_se_scraper import (
        extract_category_tree,
        should_skip,
        extract_product_data,
        export_to_xlsx
    )

    # Run the enhanced workflow
    xlsx_path = main_enhanced(
        extract_category_tree_func=extract_category_tree,
        skip_func=should_skip,
        extract_func=extract_product_data,
        export_func=export_to_xlsx,
        max_workers=8  # Or however many threads you want
    )

    if xlsx_path:
        # For Colab: download file
        from google.colab import files
        files.download(xlsx_path)
        print(f"Din fil {xlsx_path} är redo för nedladdning!")
    else:
        print("Ingen fil skapades.")