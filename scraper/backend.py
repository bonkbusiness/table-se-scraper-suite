from .category import extract_category_tree
from .product import scrape_product
from exclusions import is_excluded
from concurrent.futures import ThreadPoolExecutor, as_completed
from .product import extract_products_from_category

#all_urls = extract_products_from_category("https://www.table.se/produkter/some-category/")

def collect_product_urls_from_tree(tree, extract_products_from_category):
    """
    Traverse the category tree and collect product URLs using the given extraction function.
    """
    product_urls = set()
    
    def recurse(node):
        url = node.get("url")
        if not is_excluded(url):
            # You may want to implement a site-specific extract_products_from_category in scraper/product.py
            urls = extract_products_from_category(url)
            product_urls.update(urls)
        for sub in node.get("subs", []):
            recurse(sub)
    
    for cat in tree:
        recurse(cat)
    return list(product_urls)

def scrape_all_products(extract_products_from_category):
    """
    Orchestrates the full scraping process:
    - Extracts the category tree
    - Traverses to collect all product URLs
    - Scrapes each product page in parallel
    - Deduplicates and returns the products
    """
    tree = extract_category_tree()
    product_urls = collect_product_urls_from_tree(tree, extract_products_from_category)
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
