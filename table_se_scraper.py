# ========================
# 1. Install dependencies
# ========================
# !pip install requests beautifulsoup4 openpyxl

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
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from urllib.parse import urljoin, urlparse

from exclusions import EXCLUDED_CATEGORIES, EXCLUDED_PRODUCTS
from product_cache import get_cached_product, update_cache, hash_content
from table_se_scraper_backend_enhanced import main_enhanced
from table_se_scraper_performance import setup_logging, robust_scrape
from table_se_smart_scanner import smart_scan_products
setup_logging()
import logging

def logprint(msg):
    print(msg)
    logging.info(msg)

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

def extract_only_numbers(text):
    """Extract only digits from the input string."""
    if not text:
        return ""
    return "".join(re.findall(r"\d+", text))

def extract_only_number_value(text):
    """Extracts only the number (integer or decimal) and removes negatives."""
    if not text:
        return ""
    # Replace comma with dot
    text = text.replace(",", ".")
    # Find all positive numbers (integer or decimal, ignore negative sign)
    matches = re.findall(r"\d+(?:\.\d+)?", text)
    if matches:
        # Join if there are multiple number groups (e.g., "1 299,00" or "1 299.00")
        return "".join(matches)
    return ""

def parse_measurements(text):
    """Parse measurements, mapping L/D/B/H to full Swedish names and cm, ignoring negatives."""
    result = {
        "Mått (text)": text,
        "Längd (värde)": "", "Längd (enhet)": "",
        "Bredd (värde)": "", "Bredd (enhet)": "",
        "Höjd (värde)": "", "Höjd (enhet)": "",
        "Diameter (värde)": "", "Diameter (enhet)": "",
    }
    if not text:
        return result
    # Replace minus with nothing
    clean_text = text.replace("-", "")
    # Standardize cm
    clean_text = re.sub(r"\bcentimeter\b", "cm", clean_text, flags=re.IGNORECASE)
    # Replace L/D/B/H with full names (Swedish)
    label_map = {"L": "Längd", "D": "Djup", "B": "Bredd", "H": "Höjd"}
    # Pattern: (L|D|B|H) num [x ...] cm
    parts = re.findall(r"([LDBH])\s*([0-9]+(?:[.,][0-9]+)?)", clean_text)
    unit = "cm" if "cm" in clean_text else ""
    for short, val in parts:
        full = label_map.get(short)
        if full:
            result[f"{full} (värde)"] = re.sub(r"[^\d.]", "", val)
            result[f"{full} (enhet)"] = unit
    # Also handle Diameter
    m_dia = re.match(r"[ØO]\s*\.?\s*(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)", clean_text)
    if m_dia:
        result["Diameter (värde)"], result["Diameter (enhet)"] = m_dia.groups()
        # Remove minus if present
        result["Diameter (värde)"] = result["Diameter (värde)"].replace("-", "")
    # Fallback to old patterns if needed
    if not any(result[f"{label} (värde)"] for label in ["Längd", "Djup", "Bredd", "Höjd", "Diameter"]):
        # Try old logic as fallback
        m3 = re.match(r"(\d+)[x×](\d+)[x×](\d+)\s*([a-zA-Z]+)", clean_text)
        if m3:
            result["Längd (värde)"], result["Bredd (värde)"], result["Höjd (värde)"], enhet = m3.groups()
            result["Längd (enhet)"] = result["Bredd (enhet)"] = result["Höjd (enhet)"] = enhet
        else:
            m_single = re.match(r"(Längd|Bredd|Höjd|Diameter|Djup)?\s*:?\.?\s*(\d+)\s*([a-zA-Z]+)", clean_text, re.IGNORECASE)
            if m_single:
                label, value, enhet = m_single.groups()
                if label:
                    label = label.capitalize()
                    result[f"{label} (värde)"] = value
                    result[f"{label} (enhet)"] = enhet
                else:
                    result["Längd (värde)"] = value
                    result["Längd (enhet)"] = enhet
    # Remove negatives if any (should be already handled)
    for key in result:
        if "värde" in key and result[key]:
            result[key] = result[key].replace("-", "")
    return result

def parse_value_unit(text):
    val_unit = re.match(r"^\s*([\d.,]+)\s*([^\d\s]+.*)?$", text or "")
    if val_unit:
        value, unit = val_unit.groups()
        value = value.replace(",", ".")
        return value, (unit or "").strip()
    return "", ""

def should_skip(catname):
    EXCLUDE_NORMALIZED = [normalize_text(x) for x in EXCLUDED_CATEGORIES]
    return normalize_text(catname) in EXCLUDE_NORMALIZED

def should_skip_product(product_data):
    namn = product_data.get("Namn", "")
    artikelnummer = product_data.get("Artikelnummer", "")
    produkturl = product_data.get("Produkt-URL", "")
    for excl in EXCLUDED_PRODUCTS:
        if excl in namn or excl in artikelnummer or excl in produkturl:
            return True
    return False

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
def extract_product_data(product_url):
    soup = get_soup(product_url)
    if not soup:
        logprint(f"Kunde inte ladda produkt: {product_url}")
        return None

    # Artikelnummer: <strong> inside .woocommerce-product-details__short-description
    short_desc = soup.select_one(".woocommerce-product-details__short-description")
    artikelnummer = ""
    if short_desc:
        strong = short_desc.find("strong")
        if strong:
            artikelnummer = strong.get_text(strip=True)
    # PATCH: Artikelnummer only numbers
    artikelnummer = extract_only_numbers(artikelnummer)

    # Hash the relevant HTML for change detection
    content_hash = hash_content(soup.prettify())

    # Try the cache
    cached = get_cached_product(artikelnummer, content_hash)
    if cached:
        logprint(f"Produkt {artikelnummer} laddad från cache.")
        return cached

    # Namn: h1.edgtf-single-product-title[itemprop='name']
    namn = ""
    selectors = [
        "h1.edgtf-single-product-title[itemprop='name']",
        "h1.product_title"
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            namn = el.get_text(strip=True)
            break

    # Pris inkl. moms: .product_price_in
    pris_inkl_elem = soup.select_one(".product_price_in")
    pris_inkl = (
        pris_inkl_elem.get_text(strip=True)
        if pris_inkl_elem else ""
    )
    # PATCH: Pris inkl. moms only numbers
    pris_inkl = extract_only_number_value(pris_inkl)

    # Pris exkl. moms: .product_price_ex
    pris_exkl_elem = soup.select_one(".product_price_ex")
    pris_exkl = (
        pris_exkl_elem.get_text(strip=True)
        if pris_exkl_elem else ""
    )
    # PATCH: Pris exkl. moms only numbers
    pris_exkl = extract_only_number_value(pris_exkl)

    # Produktbild-URL: as before
    produktbild_url = ""
    img = soup.select_one(".woocommerce-product-gallery__image img")
    if img and img.get("src"):
        produktbild_url = img.get("src")

    # ===================
    # More Info Section
    # ===================
    more_info = soup.select_one('.product_more_info.vc_col-md-6')
    info_dict = {}
    if more_info:
        for p in more_info.find_all('p'):
            # Process <p> content with <br> for each line
            lines = []
            for elem in p.contents:
                if isinstance(elem, str):
                    lines.extend(elem.split('\n'))
                elif getattr(elem, 'name', None) == 'br':
                    lines.append('\n')
                else:
                    lines.append(elem.get_text())
            text = ''.join(lines)
            for line in text.split('\n'):
                line = line.strip()
                if not line or ':' not in line:
                    continue
                label, value = line.split(':', 1)
                label = label.strip().capitalize()
                value = value.strip()
                info_dict[label] = value

    farg = info_dict.get('Färg', '')
    material = info_dict.get('Material', '')
    serie = info_dict.get('Serie', '')
    matt_text = info_dict.get('Mått', '') or info_dict.get('Mått (text)', '')
    diameter_text = info_dict.get('Diameter', '')
    kapacitet_text = info_dict.get('Kapacitet', '')
    volym_text = info_dict.get('Volym', '')

    # PATCH: Parse measurements with new logic (L->Längd, etc., no negatives, cm normalization)
    mått_dict = parse_measurements(matt_text)
    diameter_v, diameter_e = parse_value_unit(diameter_text)
    if not diameter_v and mått_dict.get("Diameter (värde)"):
        diameter_v = mått_dict.get("Diameter (värde)")
        diameter_e = mått_dict.get("Diameter (enhet)")
    kap_v, kap_e = parse_value_unit(kapacitet_text)
    vol_v, vol_e = parse_value_unit(volym_text)
    längd_v, längd_e = mått_dict.get("Längd (värde)"), mått_dict.get("Längd (enhet)")
    bredd_v, bredd_e = mått_dict.get("Bredd (värde)"), mått_dict.get("Bredd (enhet)")
    höjd_v, höjd_e = mått_dict.get("Höjd (värde)"), mått_dict.get("Höjd (enhet)")

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
        "Färg": farg,
        "Material": material,
        "Serie": serie,
        "Produktbild-URL": produktbild_url,
        "Produkt-URL": product_url
    }

    # Update cache after successful extraction
    update_cache(artikelnummer, data, content_hash)
    logprint(f"Extraherad produkt: {namn} (URL: {product_url})")
    return data

def extract_products_from_category(category_url):
    soup = get_soup(category_url)
    if not soup:
        return []
    product_urls = []
    # Page through if there are multiple pages
    next_page = True
    page_number = 1
    while next_page:
        prods = soup.select(".product a.woocommerce-LoopProduct-link, .products .product a")
        for a in prods:
            href = a.get("href")
            if href:
                url = urljoin(BASE_URL, href)
                if url not in product_urls:
                    product_urls.append(url)
        # Look for next page
        next_btn = soup.select_one(".page-numbers .next")
        if next_btn and next_btn.get("href"):
            next_url = urljoin(BASE_URL, next_btn.get("href"))
            page_number += 1
            soup = get_soup(next_url)
            if not soup:
                break
        else:
            next_page = False
    return product_urls

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
    
def get_all_headers(data):
    """
    Returns a list of all unique keys appearing in any dict in data, prioritizing main fields first.
    """
    if not data:
        return []
    headers = set()
    for row in data:
        headers.update(row.keys())
    priority = ["Category", "Subcategory", "Sub-Subcategory"]
    ordered = [h for h in priority if h in headers]
    rest = sorted(h for h in headers if h not in priority)
    return ordered + rest

def backup_export_to_csv(data, base_name="table_produkter_backup"):
    """
    Fallback to CSV export if XLSX fails.
    """
    if not data:
        print("Ingen data att exportera till CSV.")
        return None
    filename = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    headers = set()
    for row in data:
        headers.update(row.keys())
    headers = sorted(headers)
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        print(f"Backup export till CSV klar: {filename}")
        return filename
    except Exception as e:
        print(f"Fel vid backup-CSV-export: {e}")
        logging.error(f"CSV backup export failed: {e}")
        return None

def export_to_xlsx(data, base_name="table_produkter"):
    if not data:
        print("Ingen data att exportera till XLSX.")
        return None
    filename = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Produkter"

    headers = get_all_headers(data)
    ws.append(headers)

    # Formatting headers
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFFFF")
        cell.fill = PatternFill("solid", fgColor="FF212121")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(bottom=Side(style="medium", color="FFB0BEC5"))

    for row in data:
        ws.append([row.get(h, "") for h in headers])
        row_idx = ws.max_row
        category = row.get("Category") or row.get("category") or ""
        subcategory = row.get("Subcategory") or row.get("subcategory") or ""
        # pastel_color_for_category must be defined elsewhere in your codebase
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

    for col in ws.columns:
        max_length = max(len(str(cell.value) or "") for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 6

    try:
        wb.save(filename)
        print(f"Export till XLSX klar: {filename}")
    except Exception as e:
        print(f"Fel vid sparande av XLSX: {e}")
        logging.error(f"XLSX export failed: {e}")
        return None
    return filename

def safe_export_to_xlsx_with_backup(data, base_name="table_produkter"):
    """
    Tries to export to XLSX, falls back to CSV if it fails.
    Returns the filename and a flag indicating if fallback was used.
    """
    filename = export_to_xlsx(data, base_name)
    if filename is not None:
        return filename, False
    print("XLSX-export misslyckades, försöker backup till CSV...")
    backup_filename = backup_export_to_csv(data, base_name + "_backup")
    return backup_filename, True if backup_filename else False

def export_errors_to_xlsx(errors, base_name="table_produkter_errors"):
    if not errors:
        print("Inga valideringsfel att exportera.")
        return None
    filename = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Produktfel"
    ws.append(["Index", "Feltyp", "Produktinfo"])
    for idx, err in enumerate(errors):
        ws.append([
            idx + 1,
            err.get("error_type", str(err.get("type", ""))),
            str(err.get("product", err))
        ])
    try:
        wb.save(filename)
        print(f"Export av fel till XLSX klar: {filename}")
    except Exception as e:
        print(f"Fel vid sparande av fel-XLSX: {e}")
        logging.error(f"XLSX error export failed: {e}")
        # Backup to CSV for errors too
        backup_filename = backup_export_to_csv(errors, base_name + "_backup")
        if backup_filename:
            print("Felrapport exporterades som CSV istället för XLSX.")
            return backup_filename
        return None
    return filename

# ========================
# 7. Enhanced Main Entrypoint (Parallelized, Smart Scan, Separate Error XLSX)
# ========================
def enhanced_main_with_scan_and_error_file():
    # --- FIX: Use main_enhanced for scraping, but handle export here ---
    products = main_enhanced(
        extract_category_tree_func=extract_category_tree,
        skip_func=should_skip,
        extract_func=extract_product_data,
        export_func=lambda x: x,  # Return products directly
        max_workers=8
    )
    if not products:
        logprint("Ingen data skrapades.")
        return None, None

    scanned_products, product_errors = smart_scan_products(products)
    if product_errors:
        logprint(f"Smart scanner hittade {len(product_errors)} felaktiga produkter. Se logg och felrapport för detaljer.")
        error_xlsx = export_errors_to_xlsx(product_errors)
    else:
        error_xlsx = None

    #xlsx_file = export_to_xlsx(scanned_products)
    
    xlsx_file, fallback_used = safe_export_to_xlsx_with_backup(scanned_products)
    if fallback_used:
    print("Varning: Resultat exporterades som CSV istället för XLSX på grund av problem.")
    
    return xlsx_file, error_xlsx

# ========================
# 8. Run and download (Colab-friendly)
# ========================
def main():
    xlsx_path, error_xlsx_path = enhanced_main_with_scan_and_error_file()
    print("Main scraping/export complete.")
    return xlsx_path, error_xlsx_path

if __name__ == "__main__":
    xlsx_path, error_xlsx_path = enhanced_main_with_scan_and_error_file()
    if xlsx_path:
        print(f"Din fil {xlsx_path} är skapad.")
        try:
            from google.colab import files
            files.download(xlsx_path)
        except ImportError:
            pass
    if error_xlsx_path:
        print(f"Felrapport {error_xlsx_path} är skapad.")
        try:
            from google.colab import files
            files.download(error_xlsx_path)
        except ImportError:
            pass
    if not xlsx_path:
        print("Ingen produktfil skapades.")
    if not error_xlsx_path:
        print("Ingen felrapport skapades.")
