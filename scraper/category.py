"""
Category extraction for table.se

- Traverses all main, sub, and sub-sub categories
- Applies exclusion logic via exclusions.py
- Returns a tree of categories
"""

from exclusions import is_excluded
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE_URL = "https://www.table.se"

def extract_category_tree():
    """
    Build the full category tree for table.se, with exclusions applied.
    Returns a list of category nodes (dicts with name, url, subs[]).
    """
    resp = requests.get(BASE_URL + "/produkter/")
    soup = BeautifulSoup(resp.text, "html.parser")
    seen = set()
    main_categories = []

    # Find all main categories
    for a in soup.find_all("a", href=True):
        href = a['href']
        url = urljoin(BASE_URL, href)
        if url in seen:
            continue
        parsed = urlparse(href)
        if parsed.path.startswith("/produkter/") and not "/page/" in parsed.path and not "/nyheter/" in parsed.path:
            path_parts = [p for p in parsed.path.split("/") if p]
            if len(path_parts) == 2 or (len(path_parts) == 3 and path_parts[2] == ""):
                catname = a.get_text(strip=True)
                if catname and catname != "HEM":
                    seen.add(url)
                    main_categories.append({"name": catname, "url": url})

    tree = []
    for cat in main_categories:
        node = build_category_node(cat["name"], cat["url"], seen)
        if node:
            tree.append(node)
    # Prune excluded nodes after building full tree
    tree = [prune_excluded_nodes(node) for node in tree if prune_excluded_nodes(node)]
    return tree

def build_category_node(name, url, seen):
    """
    Recursively build a category node with its subcategories.
    """
    if url in seen:
        return None
    seen.add(url)
    node = {"name": name, "url": url, "subs": []}
    soup = get_soup(url)
    if not soup:
        return node
    subcats = []
    for a in soup.find_all("a", href=True):
        href = a['href']
        sub_url = urljoin(BASE_URL, href)
        if sub_url in seen:
            continue
        parsed = urlparse(href)
        path_parts = [p for p in parsed.path.split("/") if p]
        # Heuristic: subcategory if path is one longer than parent
        if (
            parsed.path.startswith("/produkter/")
            and len(path_parts) > 2
            and name.lower() not in ("hem",)
        ):
            subcat_name = a.get_text(strip=True)
            if subcat_name and subcat_name != "HEM":
                subnode = build_category_node(subcat_name, sub_url, seen)
                if subnode:
                    subcats.append(subnode)
    node["subs"] = subcats
    return node

def prune_excluded_nodes(node):
    """
    Prune this node and all children if excluded (via exclusions.py).
    """
    if is_excluded(node["url"]):
        return None
    if "subs" in node:
        pruned_subs = []
        for sub in node["subs"]:
            pruned = prune_excluded_nodes(sub)
            if pruned:
                pruned_subs.append(pruned)
        node["subs"] = pruned_subs
    return node

def get_soup(url, timeout=20):
    """
    Downloads a URL and returns a BeautifulSoup object (or None if failed).
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return None
