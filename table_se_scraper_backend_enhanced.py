"""
Enhanced backend for Table.se scraper: Adds performance, reliability, maintainability, and data quality improvements.
- Keeps original scraper and exporter functions untouched.
- Call and use these enhanced functions from your main script as needed.
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import Any, Dict, List, Optional
import logging
import os
import traceback

from bs4 import BeautifulSoup

def should_skip_url(url):
    for prefix in EXCLUDED_URL_PREFIXES:
        if url.startswith(prefix):
            return True
    return False

# ================
# 1. Logging Setup
# ================
logger = logging.getLogger("table_scraper_enhanced")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
handler.setFormatter(formatter)
if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

def logprint(msg: str):
    print(msg)
    logger.info(msg)

# =========================
# 2. Parallel Fetch Utility
# =========================
def parallel_map(func, iterable, max_workers=8, desc="Working..."):
    """
    Parallel map with progress display.
    """
    from tqdm import tqdm
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(func, item): item for item in iterable}
        for future in tqdm(as_completed(futures), total=len(futures), desc=desc):
            try:
                results.append(future.result())
            except Exception as e:
                logger.warning(f"Exception in parallel_map: {e}")
    return results

# ========================
# 2a. Category extraction (3 levels deep)
# ========================
def extract_category_tree():
    resp = requests.get(BASE_URL + "/produkter/")
    soup = BeautifulSoup(resp.text, "html.parser")
    main_categories = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a['href']
        url = urljoin(BASE_URL, href)
        if should_skip_url(url):
            logprint(f"Skipping excluded main category (by URL): {url}")
            continue
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
        if should_skip_url(cat["url"]):
            logprint(f"Skipping excluded category (by URL): {cat['url']}")
            continue
        node = {"name": cat["name"], "url": cat["url"], "subs": []}
        sub_soup = get_soup(cat["url"])
        subcats = []
        seen_sub = set()
        if sub_soup:
            for a in sub_soup.find_all("a", href=True):
                href = a['href']
                url_sub = urljoin(BASE_URL, href)
                if should_skip_url(url_sub):
                    logprint(f"Skipping excluded subcategory (by URL): {url_sub}")
                    continue
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
            if should_skip_url(sub["url"]):
                logprint(f"Skipping excluded sub-subcategory (by URL): {sub['url']}")
                continue
            subsub_soup = get_soup(sub["url"])
            subsubs = []
            seen_subsub = set()
            if subsub_soup:
                for a in subsub_soup.find_all("a", href=True):
                    href = a['href']
                    url2 = urljoin(BASE_URL, href)
                    if should_skip_url(url2):
                        logprint(f"Skipping excluded sub-subcategory (by URL): {url2}")
                        continue
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



# ================================
# 3. Request Throttling & Retries
# ================================
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Thread-local session for thread-safety
thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        thread_local.session = session
    return thread_local.session

def get_soup_with_retries(url: str, throttle: float = 0.7, max_retries: int = 3) -> Optional[BeautifulSoup]:
    """
    Like get_soup, but with built-in retries and request throttling.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            session = get_session()
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            time.sleep(throttle)
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            logger.warning(f"Fetch failed ({url}), attempt {attempt+1}/{max_retries}: {e}")
            last_exc = e
            time.sleep(1.5 * (attempt + 1))
    logger.error(f"Giving up on {url}: {last_exc}")
    return None

# =======================================
# 4. Deduplication, Field Completeness QC
# =======================================
def deduplicate_products(products: List[Dict[str, Any]], key_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Remove duplicate products based on a tuple of key fields (default: ['Namn', 'Artikelnummer']).
    """
    if not key_fields:
        key_fields = ["Namn", "Artikelnummer"]
    seen = set()
    deduped = []
    for prod in products:
        key = tuple(prod.get(field, "") for field in key_fields)
        if key not in seen:
            seen.add(key)
            deduped.append(prod)
    return deduped

def check_field_completeness(products: List[Dict[str, Any]], required_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Returns a list of products missing any of the required fields.
    """
    if not required_fields:
        required_fields = ["Namn", "Artikelnummer", "Pris inkl. moms (värde)", "Produkt-URL"]
    incomplete = []
    for prod in products:
        for field in required_fields:
            if not prod.get(field):
                incomplete.append(prod)
                break
    return incomplete

# =======================================
# 5. Progress Bar Utility
# =======================================
def progress_iter(iterable, desc="Processing"):
    try:
        from tqdm import tqdm
        return tqdm(iterable, desc=desc)
    except ImportError:
        # fallback if tqdm not available
        return iterable

# =======================================
# 6. Modularization Helpers (for splitting)
# =======================================
# (No-op here, but recommend: main.py, scraper.py, exporter.py, utils.py for real modularization.)

# =======================================
# 7. Type Hints and Docstrings: Example for Scrape Function
# =======================================
def extract_products_from_category_enhanced(category_url: str) -> List[str]:
    """
    Enhanced version of extract_products_from_category:
    - Uses get_soup_with_retries for resilience.
    - Throttles requests.
    - Returns product URLs found.
    """
    product_urls = set()
    page = 1
    while True:
        paged_url = f"{category_url}?page={page}" if page > 1 else category_url
        soup = get_soup_with_retries(paged_url)
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
    logger.info(f"Hittade {len(product_urls)} produkter i kategori: {category_url}")
    return list(product_urls)

# =======================================
# 8. Example Usage: Enhanced Deep Scraper
# =======================================
def scrape_all_products_deep_enhanced(tree: List[Dict[str, Any]], skip_func, extract_func, max_workers=8) -> List[Dict[str, Any]]:
    """
    Parallelized, resilient deep scrape of all products from a category tree.
    - skip_func: function to determine if a category should be skipped
    - extract_func: function to extract product data from a URL
    """
    all_products = []
    product_url_category_map = []

    # Collect all product URLs with their category paths (parallel subcat/subsubcat scraping)
    def collect_product_urls(cat_path, url):
        if skip_func(cat_path[-1]):
            return []
        urls = extract_products_from_category_enhanced(url)
        return [(u, list(cat_path)) for u in urls]

    # Traverse tree and collect URLs
    categories_to_scrape = []

    def traverse(node, path):
        name = node["name"]
        url = node["url"]
        new_path = path + [name]
        if node.get("subs"):
            for sub in node["subs"]:
                traverse(sub, new_path)
        else:
            categories_to_scrape.append((new_path, url))

    for cat in tree:
        traverse(cat, [])

    # Parallel fetch of product URLs
    results = parallel_map(
        lambda pair: collect_product_urls(pair[0], pair[1]),
        categories_to_scrape,
        max_workers=max_workers,
        desc="Fetching product URLs"
    )
    for batch in results:
        product_url_category_map.extend(batch)

    # Deduplicate URLs
    seen_urls = set()
    unique_url_cat = []
    for url, cat_path in product_url_category_map:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_url_cat.append((url, cat_path))

    # Parallel fetch of product data
    def fetch_with_category(url_cat):
        url, cat_path = url_cat
        try:
            prod = extract_func(url)
            if prod:
                # Attach category info if not present
                if "Category" not in prod and len(cat_path) > 0:
                    prod["Category"] = cat_path[0]
                if "Subcategory" not in prod and len(cat_path) > 1:
                    prod["Subcategory"] = cat_path[1]
                if "Sub-Subcategory" not in prod and len(cat_path) > 2:
                    prod["Sub-Subcategory"] = cat_path[2]
                return prod
        except Exception as e:
            logger.warning(f"Could not extract product at {url}: {e}")
        return None

    all_products = parallel_map(
        fetch_with_category, unique_url_cat, max_workers=max_workers, desc="Fetching product data"
    )
    # Remove Nones
    all_products = [p for p in all_products if p]
    return all_products

# =======================================
# 9. Example: Data Quality Check on Export
# =======================================
def export_with_completeness_check(products, export_func, **export_kwargs):
    """
    Exports products and logs any incomplete entries.

    Parameters:
        products (list): List of product dicts to export.
        export_func (callable): Function to export products (e.g., export_to_xlsx). Must not be None.
        **export_kwargs: Extra arguments for the export function.

    Raises:
        ValueError: If export_func is None or not callable.

    Returns:
        The result of the export_func (usually the output file name).
    """
    if not callable(export_func):
        raise ValueError("export_func must be a callable export function (e.g., export_to_xlsx), but got None or non-callable instead.")
    incomplete = check_field_completeness(products)
    if incomplete:
        logger.warning(f"Warning: {len(incomplete)} products are missing required fields.")
    # Deduplicate
    products = deduplicate_products(products)
    return export_func(products, **export_kwargs)

# =======================================
# 10. Upgraded Main Enhanced Workflow with Fallback and Traceback Logging
# =======================================
def main_enhanced(
    extract_category_tree_func,
    skip_func,
    extract_func,
    export_func,
    max_workers=8,
    fallback_export_func=None
):
    """
    Enhanced workflow with export fallback and traceback logging:
    - category tree extraction
    - parallelized deep scrape
    - deduplication and completeness check
    - export with fallback and full traceback logging on error

    Parameters:
        extract_category_tree_func: function to fetch category tree
        skip_func: function to filter categories
        extract_func: function to fetch product data
        export_func: main export function (e.g., export_to_xlsx)
        max_workers: level of parallelism
        fallback_export_func: optional fallback export function (e.g., backup_export_to_csv)
    Returns:
        (exported_file, fallback_used, error_traceback)
    """
    logprint("==== STARTAR ENHANCED TABLE.SE SCRAPER ====")
    error_traceback = None
    fallback_used = False
    exported_file = None
    try:
        tree = extract_category_tree_func()
        products = scrape_all_products_deep_enhanced(
            tree, skip_func, extract_func, max_workers=max_workers
        )
        exported_file = export_with_completeness_check(products, export_func)
        logprint("==== KLAR! ====")
        return exported_file, fallback_used, error_traceback
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Export or scraping failed: {e}\nFull traceback:\n{tb}")
        error_traceback = tb
        # Fallback export if provided
        if fallback_export_func is not None:
            try:
                logprint("Försöker fallback-export...")
                # Use the products, if available, else fail
                # If scrape failed, cannot fallback
                if 'products' in locals() and products:
                    exported_file = fallback_export_func(products)
                    fallback_used = True
                    if exported_file:
                        logprint(f"Fallback-export lyckades: {exported_file}")
                    else:
                        logprint("Fallback-export misslyckades.")
                else:
                    logprint("Fallback-export kunde inte göras: ingen produktdata.")
            except Exception as fb_e:
                fb_tb = traceback.format_exc()
                logger.error(f"Fallback export failed: {fb_e}\nFull traceback:\n{fb_tb}")
                error_traceback += "\n\nFallback export failed:\n" + fb_tb
        logprint("==== AVSLUTAD MED FEL ====")
        return exported_file, fallback_used, error_traceback

# =========== End of Enhanced Backend ===========
