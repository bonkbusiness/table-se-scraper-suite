"""
scraper/category.py

Category extraction and tree traversal utilities for the Table.se Scraper Suite.

This module provides functions to:
    - Extract the full category tree from the Table.se mega menu.
    - Traverse the extracted tree for robust testing and validation.
    - Extract all product URLs under every category, skipping excluded URLs.

Features:
    - Recursively parses the mega menu HTML for unlimited category depth.
    - Attaches color and level metadata to each category node.
    - Excludes unwanted categories and products via exclusions.py.
    - Provides helper functions for robustness checks and tree traversal.

USAGE:
    from scraper.category import extract_category_tree, extract_product_urls

    category_tree = extract_category_tree()
    product_urls = extract_product_urls(category_tree)

DEPENDENCIES:
    - requests, BeautifulSoup (bs4), urllib.parse
    - scraper.utils (for pastel_gradient_color, etc.)
    - exclusions (for is_excluded)

Author: bonkbusiness
License: MIT
"""

import requests
from typing import List, Dict, Any, Generator, Set
from exclusions import is_excluded
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from scraper.utils import (
    get_category_levels,
    build_category_colors,
    pastel_gradient_color,
)

BASE_URL = "https://www.table.se"

def get_soup(url: str, timeout: int = 20) -> BeautifulSoup:
    """
    Fetch the HTML content of a URL and parse it with BeautifulSoup.

    Args:
        url (str): The URL to fetch.
        timeout (int): Timeout in seconds.

    Returns:
        BeautifulSoup: Parsed soup object, or None if request fails.
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"DEBUG: get_soup failed for {url} with {e}")
        return None

def parse_menu_ul(ul, level: int = 0) -> List[Dict[str, Any]]:
    """
    Recursively parse a <ul> mega menu for categories.

    Args:
        ul (Tag): BeautifulSoup <ul> element.
        level (int): Current tree depth.

    Returns:
        list: Category dicts with keys: name, url, color, level, subs.
    """
    categories = []
    if not ul:
        return categories
    for li in ul.find_all("li", recursive=False):
        a = li.find("a", href=True)
        if not a:
            continue
        href = a['href']
        if "/produkter/" not in href:
            continue
        name = a.get_text(strip=True)
        url = urljoin(BASE_URL, href)
        sub_ul = li.find("ul")
        subs = parse_menu_ul(sub_ul, level + 1) if sub_ul else []
        color = pastel_gradient_color(level)
        categories.append({
            "name": name,
            "url": url,
            "color": color,
            "level": level,
            "subs": subs
        })
    return categories

def extract_category_tree() -> List[Dict[str, Any]]:
    """
    Extract the full category tree from the Table.se homepage mega menu.

    Returns:
        list: Top-level category dicts, each with subs (recursive).

    Raises:
        RuntimeError: If mega menu navigation is not found.
    """
    resp = requests.get(BASE_URL)
    soup = BeautifulSoup(resp.text, "html.parser")

    nav = soup.select_one("nav.edgtf-main-menu")
    if nav is None:
        raise RuntimeError("Mega menu navigation not found")
    uls = nav.find_all("ul")
    top_ul = max(uls, key=lambda ul: len(ul.find_all("li", recursive=False)), default=None)
    if not top_ul:
        return []
    tree = parse_menu_ul(top_ul)
    tree = [node for node in tree if node]
    return tree

# === Robustness/Validation Helpers ===

def get_top_level_names(category_tree: List[Dict[str, Any]]) -> Set[str]:
    """
    Returns a set of uppercase names for all top-level categories.

    Args:
        category_tree (list): The category tree.

    Returns:
        set: Uppercase names for presence and deduplication checks.
    """
    return {node['name'].upper() for node in category_tree}

def has_subcategories(category_tree: List[Dict[str, Any]]) -> bool:
    """
    Returns True if any top-level category has subcategories.

    Args:
        category_tree (list): The category tree.

    Returns:
        bool: True if any category has subs.
    """
    return any(node['subs'] for node in category_tree)

def all_category_urls(category_tree: List[Dict[str, Any]]) -> Generator[str, None, None]:
    """
    Yields all category URLs in the tree (top-level and subs).

    Args:
        category_tree (list): The category tree.

    Yields:
        str: Category URLs.
    """
    for node in category_tree:
        yield node['url']
        if node.get('subs'):
            yield from all_category_urls(node['subs'])

def all_category_names(category_tree: List[Dict[str, Any]]) -> Generator[str, None, None]:
    """
    Yields all category names in the tree (top-level and subs, uppercase).

    Args:
        category_tree (list): The category tree.

    Yields:
        str: Uppercase category names.
    """
    for node in category_tree:
        yield node['name'].upper()
        if node.get('subs'):
            yield from all_category_names(node['subs'])

def has_duplicate_top_level_names(category_tree: List[Dict[str, Any]]) -> bool:
    """
    Returns True if any top-level category name is duplicated.

    Args:
        category_tree (list): The category tree.

    Returns:
        bool: True if duplicates exist.
    """
    names = [node['name'].upper() for node in category_tree]
    return len(names) != len(set(names))

def all_urls_are_valid(category_tree: List[Dict[str, Any]]) -> bool:
    """
    Returns True if all URLs in the category tree start with the proper prefix.

    Args:
        category_tree (list): The category tree.

    Returns:
        bool: True if all URLs are valid.
    """
    prefix = "https://www.table.se/produkter/"
    return all(url.startswith(prefix) for url in all_category_urls(category_tree))

def no_excluded_categories_present(category_tree: List[Dict[str, Any]]) -> bool:
    """
    Returns True if no category URL in the tree is excluded according to exclusions.py.

    Args:
        category_tree (list): The category tree.

    Returns:
        bool: True if no excluded URLs are present.
    """
    return all(not is_excluded(url) for url in all_category_urls(category_tree))

# === Product URL Extraction ===

def extract_product_urls_from_category(category_url: str) -> Generator[str, None, None]:
    """
    Yields all product URLs from a category page.
    Table.se does NOT use pagination, so only one request per category.
    Skips excluded product URLs via is_excluded.

    Args:
        category_url (str): The category page URL.

    Yields:
        str: Product URLs.
    """
    soup = get_soup(category_url)
    if not soup:
        return
    for a in soup.find_all("a", class_="woocommerce-LoopProduct-link", href=True):
        product_url = urljoin(category_url, a['href'])
        if not is_excluded(product_url):
            yield product_url

def extract_product_urls(category_tree: List[Dict[str, Any]]) -> Set[str]:
    """
    Traverse the category tree and extract all unique product URLs, skipping excluded products.

    Args:
        category_tree (list): Output from extract_category_tree().

    Returns:
        set: Unique (non-excluded) product URLs (strings).
    """
    product_urls = set()
    def traverse(node):
        for url in extract_product_urls_from_category(node["url"]):
            product_urls.add(url)
        for sub in node.get("subs", []):
            traverse(sub)
    for node in category_tree:
        traverse(node)
    return product_urls