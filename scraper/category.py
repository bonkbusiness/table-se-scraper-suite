import requests
from exclusions import is_excluded
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from scraper.utils import (
    get_category_levels,
    build_category_colors,
    pastel_gradient_color,
)

BASE_URL = "https://www.table.se"

def get_soup(url, timeout=20):
    """
    Fetch the HTML content of a URL and parse it with BeautifulSoup.
    Returns a BeautifulSoup object, or None if the request fails.
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"DEBUG: get_soup failed for {url} with {e}")
        return None

def parse_menu_ul(ul, level=0):
    """
    Recursively parse a <ul> of the mega menu for categories.
    Returns a list of dicts with keys: name, url, color, level, and subs (list of subcategories).
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
        categories.append({"name": name, "url": url, "color": color, "level": level, "subs": subs})
    return categories

def extract_category_tree():
    """
    Extract the full category tree from the mega menu navigation on the homepage,
    including all subcategories, and exclude any categories as per exclusions.py.

    The returned structure is a list of dicts (top-level categories), each with:
      - name: str
      - url: str
      - color: str
      - level: int
      - subs: list (subcategories, same structure recursively)
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

# === HELPER FUNCTIONS FOR TEST ROBUSTNESS BELOW ===

def get_top_level_names(category_tree):
    """
    Returns a set of uppercase names for all top-level categories.
    Useful for presence and deduplication assertions.
    """
    return {node['name'].upper() for node in category_tree}

def has_subcategories(category_tree):
    """
    Returns True if any top-level category has subcategories.
    Useful for asserting that subcategories are present somewhere.
    """
    return any(node['subs'] for node in category_tree)

def all_category_urls(category_tree):
    """
    Generator yielding all category URLs in the tree (top-level and subs).
    Useful for asserting URL format and exclusions.
    """
    for node in category_tree:
        yield node['url']
        if node.get('subs'):
            yield from all_category_urls(node['subs'])

def all_category_names(category_tree):
    """
    Generator yielding all category names in the tree (top-level and subs).
    Useful for checking for duplicates at any level.
    """
    for node in category_tree:
        yield node['name'].upper()
        if node.get('subs'):
            yield from all_category_names(node['subs'])

def has_duplicate_top_level_names(category_tree):
    """
    Returns True if any top-level category name is duplicated.
    """
    names = [node['name'].upper() for node in category_tree]
    return len(names) != len(set(names))

def all_urls_are_valid(category_tree):
    """
    Returns True if all URLs in the category tree start with the proper prefix.
    """
    prefix = "https://www.table.se/produkter/"
    return all(url.startswith(prefix) for url in all_category_urls(category_tree))

def no_excluded_categories_present(category_tree):
    """
    Returns True if no category URL in the tree is excluded according to exclusions.py.
    """
    return all(not is_excluded(url) for url in all_category_urls(category_tree))

def extract_product_urls_from_category(category_url):
    """
    Yield all product URLs from a category page. 
    Table.se does NOT use pagination, so only one request per category.
    Skips excluded product URLs via is_excluded.
    """
    soup = get_soup(category_url)
    if not soup:
        return
    for a in soup.find_all("a", class_="woocommerce-LoopProduct-link", href=True):
        product_url = urljoin(category_url, a['href'])
        if not is_excluded(product_url):
            yield product_url

def extract_product_urls(category_tree):
    """
    Traverse the category tree and extract all unique product URLs, skipping excluded products.
    Args:
        category_tree (list): Output from extract_category_tree()
    Returns:
        set: Unique (non-excluded) product URLs (strings)
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