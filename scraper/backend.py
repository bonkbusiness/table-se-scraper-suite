"""
scraper/backend.py

Backend orchestration for the Table.se scraper suite.
Handles high-level scraping flow, traverses category trees, and collects product information.
"""

from scraper.category import build_category_tree
from scraper.product import extract_product_data
from scraper.utils import deduplicate_products

def traverse_category_tree(tree):
    """
    Recursively traverse the category tree and collect all product URLs.
    Returns a list of product URLs.
    """
    product_urls = []

    def _traverse(node):
        # Implement logic to find product URLs on a category page
        url = node.get("url")
        subs = node.get("subs", [])
        # Example: You might want to fetch the category page and collect all product links
        # For demonstration, we just print the category
        print(f"Visiting category: {node.get('name')} ({url})")
        # You would add soup parsing here to find product links, e.g.:
        #   for a in soup.find_all("a", class_="product-link"): ...
        #   product_urls.append(product_url)
        for sub in subs:
            _traverse(sub)

    for node in tree:
        _traverse(node)
    return product_urls

def scrape_all_products():
    """
    Full pipeline: build category tree, collect product URLs, scrape product data, and deduplicate.
    """
    tree = build_category_tree()
    product_urls = traverse_category_tree(tree)
    print(f"Discovered {len(product_urls)} products.")
    products = []
    for url in product_urls:
        prod = extract_product_data(url)
        if prod:
            products.append(prod)
    deduped = deduplicate_products(products)
    print(f"After deduplication: {len(deduped)} products.")
    return deduped
