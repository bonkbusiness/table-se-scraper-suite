from .category import extract_category_tree
from .product import extract_products_from_category, scrape_product
from exclusions import is_excluded
from concurrent.futures import ThreadPoolExecutor, as_completed

def collect_product_urls_from_tree_parallel(tree):
    """
    Traverse the category tree and collect product URLs in parallel for each category.
    """
    category_urls = []

    def recurse(node):
        url = node.get("url")
        if not is_excluded(url):
            category_urls.append(url)
        for sub in node.get("subs", []):
            recurse(sub)

    for cat in tree:
        recurse(cat)

    all_product_urls = set()
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(extract_products_from_category, url): url for url in category_urls}
        for future in as_completed(futures):
            product_urls = future.result()
            all_product_urls.update(product_urls)

    return list(all_product_urls)

def scrape_all_products_parallel():
    """
    Orchestrates the full scraping process in parallel:
    - Extracts the category tree
    - Collects product URLs in parallel per category
    - Scrapes each product page in parallel
    - Deduplicates and returns the products
    """
    tree = extract_category_tree()
    product_urls = collect_product_urls_from_tree_parallel(tree)
    products = []
    seen = set()
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url = {executor.submit(scrape_product, url): url for url in product_urls}
        for future in as_completed(future_to_url):
            prod = future.result()
            if prod:
                key = (prod.get("Namn"), prod.get("Artikelnummer"))
                if key not in seen:
                    seen.add(key)
                    products.append(prod)
    return products
