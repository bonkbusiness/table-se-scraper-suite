from exclusions import is_excluded
from scraper.fetch import get_soup
from urllib.parse import urljoin, urlparse

BASE_URL = "https://www.table.se"

def build_category_tree():
    """
    Build the full category tree, then prune after.
    Returns a list of main category nodes, each with nested subcategories.
    """
    soup = get_soup(BASE_URL + "/produkter/")
    if not soup:
        print("Failed to load main category page.")
        return []

    seen = set()
    main_categories = []

    for a in soup.find_all("a", href=True):
        href = a['href']
        url = urljoin(BASE_URL, href)
        if url in seen:
            continue
        parsed = urlparse(href)
        # Only include direct children of /produkter/
        if parsed.path.startswith("/produkter/") and not "/page/" in parsed.path and not "/nyheter/" in parsed.path:
            path_parts = [p for p in parsed.path.split("/") if p]
            if len(path_parts) == 2 or (len(path_parts) == 3 and path_parts[2] == ""):
                catname = a.get_text(strip=True)
                if catname and catname != "HEM":
                    seen.add(url)
                    main_categories.append({"name": catname, "url": url})

    tree = [build_node(cat['name'], cat['url'], seen) for cat in main_categories]
    # Prune excluded nodes after full tree is built
    pruned_tree = [prune_excluded_nodes(node) for node in tree if prune_excluded_nodes(node)]
    return pruned_tree

def build_node(name, url, seen):
    """
    Recursively build a category node and its subcategories, using the global seen set.
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
        # Heuristic: subcategory if path is one level deeper
        if parsed.path.startswith("/produkter/") and len(path_parts) > 2 and name.lower() not in ("hem",):
            subcat_name = a.get_text(strip=True)
            if subcat_name and subcat_name != "HEM":
                subnode = build_node(subcat_name, sub_url, seen)
                if subnode:
                    subcats.append(subnode)
    node["subs"] = subcats
    return node

def prune_excluded_nodes(node):
    """
    Recursively prune nodes whose URL matches an exclusion.
    Keeps parents, but removes excluded children.
    """
    if is_excluded(node["url"]):
        print(f"Pruned excluded node: {node['url']}")
        return None
    if "subs" in node:
        pruned_subs = []
        for sub in node["subs"]:
            pruned = prune_excluded_nodes(sub)
            if pruned:
                pruned_subs.append(pruned)
        node["subs"] = pruned_subs
    return node
