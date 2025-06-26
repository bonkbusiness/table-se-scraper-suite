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
import logging
import os
import csv
import traceback
import colorsys

from exclusions import EXCLUDED_URL_PREFIXES
from product_cache import get_cached_product, update_cache, hash_content
from table_se_scraper_backend_enhanced import (
    extract_category_tree,
    should_skip_url,
    extract_product_data  # now this import will work!
)

from table_se_scraper_performance import robust_scrape
from table_se_smart_scanner import smart_scan_products

# ========================
# 2a. Output Directories & Naming
# ========================
EXPORT_DIR = "exports"
BACKUP_DIR = "backups"
LOG_DIR = "logs"

def ensure_directories():
    for d in [EXPORT_DIR, BACKUP_DIR, LOG_DIR]:
        os.makedirs(d, exist_ok=True)

def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_export_filename(prefix="table_produkter", ext="xlsx", timestamp=None):
    if not timestamp:
        timestamp = get_timestamp()
    return os.path.join(EXPORT_DIR, f"{prefix}_{timestamp}.{ext}")

def get_backup_filename(prefix="table_produkter_backup", ext="csv", timestamp=None):
    if not timestamp:
        timestamp = get_timestamp()
    return os.path.join(BACKUP_DIR, f"{prefix}_{timestamp}.{ext}")

def get_log_filename(prefix="table_produkter", ext="log", timestamp=None):
    if not timestamp:
        timestamp = get_timestamp()
    return os.path.join(LOG_DIR, f"{prefix}_{timestamp}.{ext}")

def setup_logging(prefix="table_produkter", timestamp=None):
    ensure_directories()
    if not timestamp:
        timestamp = get_timestamp()
    log_file = get_log_filename(prefix, "log", timestamp)
    logging.basicConfig(
        level=logging.INFO,
        filename=log_file,
        filemode='a',
        format='%(asctime)s %(levelname)s:%(message)s'
    )
    # Only add a StreamHandler if not present (avoid duplicate logs)
    root_logger = logging.getLogger()
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(logging.StreamHandler())

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

def sort_products(data, sort_key="Namn"):
    """Sorts products by the given sort_key (default: 'Namn')"""
    return sorted(data, key=lambda x: x.get(sort_key, "").lower())

def pastel_gradient_color(seed, total, idx, sat=0.25, light=0.85):
    """Generate a pastel color in hex, distributed along a hue gradient."""
    h = (seed + idx/float(max(total,1))) % 1.0
    r, g, b = colorsys.hls_to_rgb(h, light, sat)
    return f"{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"

def get_category_levels(row):
    """Returns (parent, sub, subsub) for the row, empty string if missing."""
    return (
        row.get("Category", "") or row.get("category", ""),
        row.get("Subcategory", "") or row.get("subcategory", ""),
        row.get("Sub-Subcategory", "") or row.get("sub-subcategory", ""),
    )

def build_category_colors(data):
    """Assign a unique pastel color for each category, subcategory, sub-subcategory."""
    parents = sorted(set(get_category_levels(row)[0] for row in data if get_category_levels(row)[0]))
    subcats = sorted(set((get_category_levels(row)[0], get_category_levels(row)[1]) for row in data if get_category_levels(row)[1]))
    subsubs = sorted(set(get_category_levels(row) for row in data if get_category_levels(row)[2]))

    parent_colors = {cat: pastel_gradient_color(0.05, len(parents), idx) for idx, cat in enumerate(parents)}
    subcat_colors = {cat: pastel_gradient_color(0.3, len(subcats), idx) for idx, cat in enumerate(subcats)}
    subsub_colors = {cat: pastel_gradient_color(0.6, len(subsubs), idx) for idx, cat in enumerate(subsubs)}

    def get_color(row):
        parent, sub, subsub = get_category_levels(row)
        if subsub and (parent, sub, subsub) in subsub_colors:
            return f"FF{subsub_colors[(parent, sub, subsub)]}"
        elif sub and (parent, sub) in subcat_colors:
            return f"FF{subcat_colors[(parent, sub)]}"
        elif parent and parent in parent_colors:
            return f"FF{parent_colors[parent]}"
        return "FFFFFFFF"  # White fallback
    return get_color

def get_soup(url, timeout=20):
    """
    Downloads a URL and returns a BeautifulSoup object (or None if failed).
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logprint(f"Fel vid hämtning av {url}: {e}")
        return None

def extract_only_number_value(text):
    """
    Extracts a numeric value (as string, with dot as decimal separator) from a messy string.
    Example: "1 234,00 kr" -> "1234.00"
    """
    if not text:
        return ""
    cleaned = text.replace(" ", "").replace("\xa0", "")
    cleaned = cleaned.replace(",", ".")
    match = re.search(r"\d*\.?\d+", cleaned)
    return match.group(0) if match else ""

def extract_only_numbers(text):
    """Extract only digits from the input string."""
    return "".join(filter(str.isdigit, str(text)))

# ========================
# 4. Export and Backup (single modern versions only)
# ========================
def export_to_xlsx(data, prefix="table_produkter", timestamp=None, sort_key="Namn"):
    """
    Export a list of product dicts to XLSX in the exports/ folder, sorted by sort_key.
    Returns the filename or None on error.
    """
    COLUMN_ORDER = [
        "Namn",
        "Artikelnummer",
        "Färg",
        "Material",
        "Serie",
        "Pris exkl. moms (värde)",
        "Pris exkl. moms (enhet)",
        "Pris inkl. moms (värde)",
        "Pris inkl. moms (enhet)",
        "Mått (text)",
        "Längd (värde)", "Längd (enhet)",
        "Bredd (värde)", "Bredd (enhet)",
        "Höjd (värde)", "Höjd (enhet)",
        "Djup (värde)", "Djup (enhet)",
        "Diameter (värde)", "Diameter (enhet)",
        "Kapacitet (värde)", "Kapacitet (enhet)",
        "Volym (värde)", "Volym (enhet)",
        "Produktbild-URL",
        "Produkt-URL"
    ]
    if not data:
        print("Ingen data att exportera till XLSX.")
        return None
    ensure_directories()
    if not timestamp:
        timestamp = get_timestamp()
    filename = get_export_filename(prefix, "xlsx", timestamp)
    try:
        data_sorted = sort_products(data, sort_key=sort_key)
        wb = Workbook()
        ws = wb.active
        ws.title = "Produkter"
        for col_num, col in enumerate(COLUMN_ORDER, 1):
            cell = ws.cell(row=1, column=col_num, value=col)
            cell.font = Font(bold=True, color="FFFFFFFF")
            cell.fill = PatternFill("solid", fgColor="FF212121")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(bottom=Side(style="medium", color="FFB0BEC5"))
        for row_num, row in enumerate(data_sorted, 2):
            for col_num, col in enumerate(COLUMN_ORDER, 1):
                ws.cell(row=row_num, column=col_num, value=row.get(col, ""))
        for col_num, col in enumerate(COLUMN_ORDER, 1):
            ws.column_dimensions[get_column_letter(col_num)].width = max(12, len(col) + 2)
        wb.save(filename)
        print(f"Export till XLSX klar: {filename}")
        return filename
    except Exception as e:
        print(f"Fel vid sparande av XLSX: {e}")
        logging.error(f"XLSX export failed: {e}")
        return None

def backup_export_to_csv(data, prefix="table_produkter_backup", timestamp=None, sort_key="Namn"):
    """
    Export a list of product dicts to CSV in the backups/ folder, sorted by sort_key.
    Returns the filename or None on error.
    """
    COLUMN_ORDER = [
        "Namn",
        "Artikelnummer",
        "Färg",
        "Material",
        "Serie",
        "Pris exkl. moms (värde)",
        "Pris exkl. moms (enhet)",
        "Pris inkl. moms (värde)",
        "Pris inkl. moms (enhet)",
        "Mått (text)",
        "Längd (värde)", "Längd (enhet)",
        "Bredd (värde)", "Bredd (enhet)",
        "Höjd (värde)", "Höjd (enhet)",
        "Djup (värde)", "Djup (enhet)",
        "Diameter (värde)", "Diameter (enhet)",
        "Kapacitet (värde)", "Kapacitet (enhet)",
        "Volym (värde)", "Volym (enhet)",
        "Produktbild-URL",
        "Produkt-URL"
    ]
    if not data:
        print("Ingen data att exportera till CSV.")
        return None
    ensure_directories()
    if not timestamp:
        timestamp = get_timestamp()
    filename = get_backup_filename(prefix, "csv", timestamp)
    try:
        data_sorted = sort_products(data, sort_key=sort_key)
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMN_ORDER)
            writer.writeheader()
            for row in data_sorted:
                writer.writerow({col: row.get(col, "") for col in COLUMN_ORDER})
        print(f"Backup export till CSV klar: {filename}")
        return filename
    except Exception as e:
        print(f"Fel vid backup-CSV-export: {e}")
        logging.error(f"CSV backup export failed: {e}")
        return None

def export_errors_to_xlsx(errors, prefix="table_produkter_errors", timestamp=None):
    """
    Export error list to the exports/ folder with timestamp.
    """
    if not errors:
        print("Inga valideringsfel att exportera.")
        return None
    ensure_directories()
    if not timestamp:
        timestamp = get_timestamp()
    filename = get_export_filename(prefix, "xlsx", timestamp)
    try:
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
        wb.save(filename)
        print(f"Export av fel till XLSX klar: {filename}")
        return filename
    except Exception as e:
        print(f"Fel vid sparande av fel-XLSX: {e}")
        logging.error(f"XLSX error export failed: {e}")
        return None


# ========================
# 5. Scraper functions (3-level deep)
# ========================

def parse_value_unit(text):
    """
    Splits a string like '12 cm' or '10,5L' into ('12', 'cm') or ('10.5', 'L').
    Returns ('', '') if nothing found or input is None/empty.
    """
    if not text:
        return "", ""
    text = str(text).replace(",", ".")
    match = re.search(r"([\d.]+)\s*([a-zA-ZåäöÅÄÖ%]*)", text)
    if match:
        value, unit = match.group(1), match.group(2)
        return value.strip(), unit.strip()
    return "", ""

def parse_measurements(matt_text):
    """
    Parses measurement text and returns a dict of measurement values.
    Finds Längd, Bredd, Höjd, Djup (or D), Diameter.
    """
    result = {}
    if not matt_text:
        return result
    lines = matt_text.split(",")
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        label = parts[0].capitalize()
        value, unit = "", ""
        if len(parts) > 1:
            value, unit = parse_value_unit(" ".join(parts[1:]))
        # Standardize keys
        if label in ["Längd", "L"]:
            result["Längd (värde)"] = value
            result["Längd (enhet)"] = unit
        elif label in ["Bredd", "B"]:
            result["Bredd (värde)"] = value
            result["Bredd (enhet)"] = unit
        elif label in ["Höjd", "H"]:
            result["Höjd (värde)"] = value
            result["Höjd (enhet)"] = unit
        elif label in ["Djup", "D"]:
            result["Djup (värde)"] = value
            result["Djup (enhet)"] = unit
        elif label in ["Diameter", "Diam." ,"Diam"]:
            result["Diameter (värde)"] = value
            result["Diameter (enhet)"] = unit
        else:
            result["Mått (text)"] = matt_text
    return result

def extract_products_from_category(category_url):
    if should_skip_url(category_url):
        logprint(f"Skipping excluded category (by URL): {category_url}")
        return []
    soup = get_soup(category_url)
    if not soup:
        return []
    product_urls = []
    while True:
        prods = soup.select(".product a.woocommerce-LoopProduct-link, .products .product a")
        valid_urls_this_page = []
        for a in prods:
            href = a.get("href")
            if href:
                url = urljoin(BASE_URL, href)
                if should_skip_url(url):
                    logprint(f"Skipping excluded product (by URL): {url}")
                    continue
                if url not in product_urls:
                    valid_urls_this_page.append(url)
        if not valid_urls_this_page:
            break
        product_urls.extend(valid_urls_this_page)
        next_btn = soup.select_one(".page-numbers .next")
        if next_btn and next_btn.get("href"):
            next_url = urljoin(BASE_URL, next_btn.get("href"))
            soup = get_soup(next_url)
            if not soup:
                break
        else:
            break
    return product_urls
    
# ========================
# 6. Enhanced Main Entrypoint (uses new export functions everywhere)
# ========================
def enhanced_main_with_scan_and_error_file():
    ensure_directories()
    timestamp = get_timestamp()
    setup_logging(timestamp=timestamp)
    exported_file, fallback_used, error_traceback = main_enhanced(
        extract_category_tree_func=extract_category_tree,
        skip_func=should_skip_url,
        extract_func=extract_product_data,
        export_func=lambda data: export_to_xlsx(data, timestamp=timestamp),
        max_workers=8,
        fallback_export_func=lambda data: backup_export_to_csv(data, timestamp=timestamp)
    )
    # Smart scan after export (if exported_file is a data list)
    try:
        scanned_products, product_errors = smart_scan_products([])  # default empty
        if isinstance(exported_file, list):
            scanned_products, product_errors = smart_scan_products(exported_file)
        elif isinstance(exported_file, str):
            scanned_products, product_errors = [], []
    except Exception as e:
        print("Fel vid smart scanning av produkter:", e)
        scanned_products, product_errors = [], []
    error_xlsx = None
    if product_errors:
        logprint(f"Smart scanner hittade {len(product_errors)} felaktiga produkter. Se logg och felrapport för detaljer.")
        error_xlsx = export_errors_to_xlsx(product_errors, timestamp=timestamp)
    if fallback_used:
        print("⚠️ Exporten gick till CSV istället för XLSX.")
    if error_traceback:
        print("❗ Fullständig felrapport:\n", error_traceback)
    return exported_file, error_xlsx

# ========================
# 7. Run and download (Colab-friendly, only new exports)
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

