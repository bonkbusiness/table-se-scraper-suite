"""
scraper/product.py

Product scraping module for Table.se

This module provides functions to:
    - Extract product URLs from all category pages (no pagination)
    - Traverse a category tree and return all unique product URLs
    - Scrape detailed product data from individual product pages

Design:
    - Tailored for the Table.se site structure (as of 2024)
    - Integrates with caching and exclusion logic for robustness and efficiency
    - Extensible parsing logic for future-proofing as the site evolves

Main Functions:
    - extract_products_from_category(category_url): List[str]
    - extract_all_product_urls(category_tree): Set[str]
    - scrape_product(product_url, category_tree=None): Dict[str, Any]

Usage:
    from scraper.product import extract_all_product_urls, scrape_product

    product_urls = extract_all_product_urls(category_tree)
    product_data = [scrape_product(url, category_tree) for url in product_urls]

Author: bonkbusiness
License: MIT
"""

from .utils import (
    extract_only_number_value, parse_value_unit, parse_measurements, extract_only_numbers,
    parse_price, strip_html, validate_url, normalize_whitespace, safe_get, make_output_filename
)
from .cache import get_cached_product, update_cache, hash_content
from exclusions import is_excluded
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import re
import json

from scraper.scanner import robust_select_one, robust_select_attr
from scraper.logging import get_logger

from typing import List, Dict, Any, Optional, Set, Tuple

logger = get_logger(__name__)

BASE_URL = "https://www.table.se"

def _extract_product_links(soup: BeautifulSoup) -> Set[str]:
    """
    Extracts all product URLs from a BeautifulSoup-parsed category page.

    Args:
        soup (BeautifulSoup): Parsed HTML of the category page.

    Returns:
        set: Absolute product URLs found on the page.
    """
    return {
        urljoin(BASE_URL, a.get("href"))
        for a in soup.find_all("a", class_="woocommerce-LoopProduct-link", href=True)
    }

def extract_products_from_category(category_url: str) -> List[str]:
    """
    Get all product page URLs in a category (no pagination).

    Args:
        category_url (str): URL of the category page.

    Returns:
        list: Filtered product URLs (strings).
    """
    logger.info(f"Fetching products for category: {category_url}")
    try:
        resp = requests.get(category_url, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch {category_url}: {e}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    links = _extract_product_links(soup)
    filtered_links = {u for u in links if not is_excluded(u)}
    logger.info(f"Found {len(filtered_links)} products on category page: {category_url}")
    return list(filtered_links)

def extract_all_product_urls(category_tree: List[Dict[str, Any]]) -> Set[str]:
    """
    Traverse the full category tree and extract all unique product URLs.

    Args:
        category_tree (list): Output from extract_category_tree()

    Returns:
        set: Unique product URLs (strings)
    """
    product_urls = set()
    def traverse(node):
        logger.info(f"Processing category: {node['url']}")
        product_urls.update(extract_products_from_category(node["url"]))
        for sub in node.get("subs", []):
            traverse(sub)
    for node in category_tree:
        traverse(node)
    logger.info(f"Total unique product URLs collected: {len(product_urls)}")
    return product_urls

def _get_text_or_empty(soup: BeautifulSoup, selector: str) -> str:
    """
    Utility to select one element and return its stripped text, or empty string.

    Args:
        soup (BeautifulSoup): Parsed HTML
        selector (str): CSS selector

    Returns:
        str: Text content or empty string
    """
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else ""

def parse_price_string(price_str: str) -> Tuple[str, str]:
    """
    Parse price string to (value, unit).

    Args:
        price_str (str): Price string, e.g. "123 kr"

    Returns:
        tuple: (value, unit)
    """
    if not price_str:
        return "", ""
    m = re.match(r"([\d\.,]+)\s*([^\d\s]+)?", price_str.strip())
    if not m:
        return "", ""
    value = m.group(1).replace(",", ".")
    unit = m.group(2) or ""
    return value, unit

def parse_measurements_info(text: str) -> Dict[str, str]:
    """
    Handles strings like "L 165 cm B 82 cm H 74 cm" or "H 9 cm Ø 8 cm".
    Returns dict of recognized measurements.

    Args:
        text (str): Free-text measurements

    Returns:
        dict: Measurement keys and values
    """
    result = {}
    key_map = {
        "l": "Längd",
        "b": "Bredd",
        "h": "Höjd",
        "d": "Djup",
        "ø": "Diameter",
        "diameter": "Diameter",
        "kapacitet": "Kapacitet",
        "volym": "Volym",
        "vikt": "Vikt",
    }
    for m in re.finditer(r"([A-Za-zÅÄÖåäöøØ]+)[\s:]*([\d\.,]+)\s*([a-zA-ZåäöÅÄÖ%]*)", text):
        k, v, u = m.groups()
        k_norm = key_map.get(k.lower(), k.capitalize())
        result[f"{k_norm} (värde)"] = v.replace(",", ".")
        result[f"{k_norm} (enhet)"] = u
    return result

def parse_features_panel(panel_html: Any) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Parses the right-side feature panel from a Table.se product page.

    Args:
        panel_html: HTML content of the panel

    Returns:
        tuple: (main_fields_dict, extra_fields_dict)
    """
    measurements = {}
    main_fields = {}
    extra = {}
    if not panel_html:
        return main_fields, extra

    lines = re.split(r"<br\s*/?>|\n", str(panel_html))
    for line in lines:
        line = re.sub(r'<.*?>', '', line)  # Strip HTML tags
        line = normalize_whitespace(line)
        if not line or ":" not in line:
            continue
        label, value = [s.strip() for s in line.split(":", 1)]
        label_norm = label.lower()
        if label_norm == "mått":
            measurements = parse_measurements_info(value)
            main_fields["Data (text)"] = value
        elif label_norm in ("färg", "material", "serie", "kapacitet", "volym", "diameter", "vikt"):
            main_fields[label.capitalize()] = value
        else:
            extra[label] = value
    main_fields.update(measurements)
    return main_fields, extra

def get_category_hierarchy_from_url(url: str, category_tree: List[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Given a product URL and the category tree, return (parent, sub) category names.

    Args:
        url (str): Product URL
        category_tree (list): Category tree structure

    Returns:
        tuple: (parent_category_name, sub_category_name)
    """
    def search(node, parent_name=""):
        if node.get("url") and node["url"].rstrip('/') in url.rstrip('/'):
            return (parent_name, node.get("name", ""))
        for sub in node.get("subs", []):
            found = search(sub, node.get("name", ""))
            if found != ("", ""):
                return found
        return ("", "")
    for node in category_tree:
        result = search(node)
        if result != ("", ""):
            return result
    return ("", "")

def scrape_product(product_url: str, category_tree: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """
    Scrape all relevant product data fields from a Table.se product page.

    Args:
        product_url (str): URL of the product page
        category_tree (list, optional): Used to derive "Kategori (parent)" and "Kategori (sub)"

    Returns:
        dict or None: Scraped product data, or None on failure/exclusion
    """
    if is_excluded(product_url):
        return None
    try:
        resp = requests.get(product_url, timeout=20)
        if not resp.ok:
            logger.warning(f"Non-200 response for {product_url}: {resp.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Failed to fetch {product_url}: {e}")
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    if not soup:
        return None

    namn = robust_select_one(soup, [
        ".edgtf-single-product-title",
        "h1.product_title",
        "h1[itemprop='name']",
        "h1"
    ]) or normalize_whitespace(_get_text_or_empty(soup, ".edgtf-single-product-title"))

    artikelnummer_raw = robust_select_one(soup, [
        ".sku",
        "[itemprop='sku']",
        "[data-product-sku]",
        ".woocommerce-product-details__short-description strong",
        "span:contains('Artikelnummer') + span"
    ]) or extract_only_numbers(_get_text_or_empty(soup, ".woocommerce-product-details__short-description strong"))
    artikelnummer_digits = "".join(filter(str.isdigit, str(artikelnummer_raw)))

    pris_inkl_raw = robust_select_one(soup, [
        ".product_price_in",
        ".price .amount",
        ".woocommerce-Price-amount",
        ".product-price",
        "[itemprop='price']"
    ]) or _get_text_or_empty(soup, ".product_price_in")
    pris_inkl_v, pris_inkl_e = parse_price_string(pris_inkl_raw)

    pris_exkl_raw = robust_select_one(soup, [
        ".product_price_ex"
    ]) or _get_text_or_empty(soup, ".product_price_ex")
    pris_exkl_v, pris_exkl_e = parse_price_string(pris_exkl_raw)

    def price_format(val):
        try:
            val_float = float(val)
            if val_float == 0:
                return "0"
            return str(val_float) if "." not in str(val) or val_float % 1 != 0 else str(int(val_float))
        except Exception:
            return val

    pris_exkl_fmt = price_format(pris_exkl_v)
    pris_inkl_fmt = price_format(pris_inkl_v)

    produktbild_url = robust_select_attr(soup, [
        ".woocommerce-product-gallery__image img",
        ".product-gallery img",
        ".product-main-image img",
        "img.wp-post-image",
        "img[itemprop='image']"
    ], "src") or ""
    if not validate_url(produktbild_url):
        produktbild_url = ""

    beskrivning_raw = robust_select_one(soup, [
        "#tab-description .product_description_text p",
        ".woocommerce-Tabs-panel--description p",
        ".product_description_text p"
    ]) or _get_text_or_empty(soup, "#tab-description .product_description_text p")
    beskrivning = strip_html(beskrivning_raw)
    beskrivning = normalize_whitespace(beskrivning)

    more_info = soup.select_one('.product_more_info.vc_col-md-6')
    main_fields, extra_fields = parse_features_panel(more_info)

    farg = main_fields.get('Färg', '')
    material = main_fields.get('Material', '')
    serie = main_fields.get('Serie', '')
    data_text = main_fields.get('Data (text)', '')

    längd_v, längd_e = main_fields.get("Längd (värde)"), main_fields.get("Längd (enhet)")
    bredd_v, bredd_e = main_fields.get("Bredd (värde)"), main_fields.get("Bredd (enhet)")
    höjd_v, höjd_e = main_fields.get("Höjd (värde)"), main_fields.get("Höjd (enhet)")
    djup_v, djup_e = main_fields.get("Djup (värde)"), main_fields.get("Djup (enhet)")
    diameter_v, diameter_e = main_fields.get("Diameter (värde)"), main_fields.get("Diameter (enhet)")
    kap_v, kap_e = main_fields.get("Kapacitet (värde)"), main_fields.get("Kapacitet (enhet)")
    vol_v, vol_e = main_fields.get("Volym (värde)"), main_fields.get("Volym (enhet)")
    vikt_v, vikt_e = main_fields.get("Vikt (värde)"), main_fields.get("Vikt (enhet)")

    canonical = soup.find("link", rel="canonical")
    produkt_url = canonical["href"] if (canonical and canonical.has_attr("href") and validate_url(canonical["href"])) else product_url

    kategori_parent, kategori_sub = ("", "")
    if category_tree is not None:
        kategori_parent, kategori_sub = get_category_hierarchy_from_url(produkt_url, category_tree)

    content_hash = hash_content(soup.prettify())
    cached = get_cached_product(artikelnummer_digits, content_hash)
    if cached:
        return cached

    extra_data_dict = dict(extra_fields)
    extra_data_json = json.dumps(extra_data_dict, ensure_ascii=False, sort_keys=True) if extra_data_dict else ""

    data = {
        "Namn": namn,
        "Artikelnummer": artikelnummer_digits,
        "Färg": farg,
        "Material": material,
        "Serie": serie,
        "Pris exkl. moms (värde)": pris_exkl_fmt,
        "Pris exkl. moms (enhet)": pris_exkl_e or "kr" if pris_exkl_fmt else "",
        "Pris inkl. moms (värde)": pris_inkl_fmt,
        "Pris inkl. moms (enhet)": pris_inkl_e or "kr" if pris_inkl_fmt else "",
        "Längd (värde)": längd_v,
        "Längd (enhet)": längd_e,
        "Bredd (värde)": bredd_v,
        "Bredd (enhet)": bredd_e,
        "Höjd (värde)": höjd_v,
        "Höjd (enhet)": höjd_e,
        "Djup (värde)": djup_v,
        "Djup (enhet)": djup_e,
        "Diameter (värde)": diameter_v,
        "Diameter (enhet)": diameter_e,
        "Kapacitet (värde)": kap_v,
        "Kapacitet (enhet)": kap_e,
        "Volym (värde)": vol_v,
        "Volym (enhet)": vol_e,
        "Vikt (värde)": vikt_v,
        "Vikt (enhet)": vikt_e,
        "Data (text)": data_text,
        "Kategori (parent)": kategori_parent,
        "Kategori (sub)": kategori_sub,
        "Produktbild-URL": produktbild_url,
        "Produkt-URL": produkt_url,
        "Beskrivning": beskrivning,
        "Extra data": extra_data_json,
    }
    update_cache(artikelnummer_digits, data, content_hash)
    return data