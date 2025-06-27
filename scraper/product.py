"""
Product scraping module for table.se

This module provides functions to extract product URLs from all category pages (no pagination),
and to scrape detailed product data from individual product pages. It is designed for the specific
structure of table.se, as of 2024, and integrates with the main scraper suite's caching and exclusion logic.

Functions:
    - extract_products_from_category: Get all product URLs from a category (no pagination).
    - extract_all_product_urls: Traverse a category tree and return all unique product URLs.
    - scrape_product: Extract all relevant fields from a table.se product page into a dictionary.
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

from scraper.scanner import robust_select_one, robust_select_attr
from scraper.logging import get_logger

logger = get_logger(__name__)

BASE_URL = "https://www.table.se"

def _extract_product_links(soup):
    """
    Return set of product URLs from soup.
    Table.se uses <a class="woocommerce-LoopProduct-link" href="...">
    """
    return {
        urljoin(BASE_URL, a.get("href"))
        for a in soup.find_all("a", class_="woocommerce-LoopProduct-link", href=True)
    }

def extract_products_from_category(category_url):
    """
    Given a category URL, return a list of all product page URLs in that category.
    Table.se does NOT use pagination: all products are listed on a single page.
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

def extract_all_product_urls(category_tree):
    """
    Traverse the full category tree and extract all unique product URLs.
    Logs progress for each category.
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

def _get_text_or_empty(soup, selector):
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else ""

def _parse_more_info(more_info):
    info_dict = {}
    if not more_info:
        return info_dict
    for p in more_info.find_all('p'):
        # Clean out HTML tags and unescape entities
        text = ''.join([elem if isinstance(elem, str) else elem.get_text() for elem in p.contents]).strip()
        text = strip_html(text)
        text = normalize_whitespace(text)
        if not text:
            continue
        if text.upper().startswith("MÅTT:"):
            value = text.replace("MÅTT:", "").strip()
            br_split = [t.strip() for t in text.split("<br />") if t.strip()]
            if len(br_split) > 1:
                value = " ".join(br_split[1:])
            info_dict["Mått (text)"] = value
        elif ":" in text:
            label, value = text.split(":", 1)
            info_dict[label.strip().capitalize()] = value.strip()
    return info_dict

def scrape_product(product_url):
    """
    Scrape all relevant product data fields from a table.se product page.
    Uses robust selectors for resilience.
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

    # Use robust selectors for main fields, fallback to legacy selectors as needed
    namn = robust_select_one(soup, [
        ".edgtf-single-product-title",
        "h1.product_title",
        "h1[itemprop='name']",
        "h1"
    ]) or normalize_whitespace(_get_text_or_empty(soup, ".edgtf-single-product-title"))

    artikelnummer = robust_select_one(soup, [
        ".sku",
        "[itemprop='sku']",
        "[data-product-sku]",
        ".woocommerce-product-details__short-description strong",
        "span:contains('Artikelnummer') + span"
    ]) or extract_only_numbers(_get_text_or_empty(soup, ".woocommerce-product-details__short-description strong"))

    pris_inkl_raw = robust_select_one(soup, [
        ".product_price_in",
        ".price .amount",
        ".woocommerce-Price-amount",
        ".product-price",
        "[itemprop='price']"
    ]) or _get_text_or_empty(soup, ".product_price_in")
    pris_inkl = parse_price(pris_inkl_raw)

    pris_exkl_raw = robust_select_one(soup, [
        ".product_price_ex"
    ]) or _get_text_or_empty(soup, ".product_price_ex")
    pris_exkl = parse_price(pris_exkl_raw)

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
    info_dict = _parse_more_info(more_info)

    farg = info_dict.get('Färg', '')
    material = info_dict.get('Material', '')
    serie = info_dict.get('Serie', '')
    matt_text = info_dict.get('Mått (text)', '')

    mått_dict = parse_measurements(matt_text) if matt_text else {}
    diameter_v, diameter_e = parse_value_unit(info_dict.get('Diameter', ''))
    kap_v, kap_e = parse_value_unit(info_dict.get('Kapacitet', ''))
    vol_v, vol_e = parse_value_unit(info_dict.get('Volym', ''))
    längd_v, längd_e = mått_dict.get("Längd (värde)"), mått_dict.get("Längd (enhet)")
    bredd_v, bredd_e = mått_dict.get("Bredd (värde)"), mått_dict.get("Bredd (enhet)")
    höjd_v, höjd_e = mått_dict.get("Höjd (värde)"), mått_dict.get("Höjd (enhet)")
    djup_v, djup_e = mått_dict.get("Djup (värde)"), mått_dict.get("Djup (enhet)")

    # Canonical URL for robust product URL, fallback to input
    canonical = soup.find("link", rel="canonical")
    produkt_url = canonical["href"] if (canonical and canonical.has_attr("href") and validate_url(canonical["href"])) else product_url

    content_hash = hash_content(soup.prettify())
    cached = get_cached_product(artikelnummer, content_hash)
    if cached:
        return cached

    data = {
        "Namn": namn,
        "Artikelnummer": artikelnummer,
        "Färg": farg,
        "Material": material,
        "Serie": serie,
        "Pris exkl. moms (värde)": pris_exkl,
        "Pris exkl. moms (enhet)": "kr" if pris_exkl else "",
        "Pris inkl. moms (värde)": pris_inkl,
        "Pris inkl. moms (enhet)": "kr" if pris_inkl else "",
        "Mått (text)": matt_text,
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
        "Produktbild-URL": produktbild_url,
        "Produkt-URL": produkt_url,
        "Beskrivning": beskrivning
    }
    update_cache(artikelnummer, data, content_hash)
    return data