from .category import build_category_tree
from .product import scrape_product
from .utils import logprint
from exclusions import is_excluded
from concurrent.futures import ThreadPoolExecutor, as_completed

def traverse_category_tree(tree):
    product_urls = set()

    def recurse(node):
        url = node.get("url")
        logprint(f"Visiting category: {node.get('name')} ({url})")
        # Implement product URL extraction logic as per your site structure here
        # For demonstration, assume extract_products_from_category_enhanced exists
        from .product import extract_products_from_category_enhanced
        if not is_excluded(url):
            urls = extract_products_from_category_enhanced(url)
            product_urls.update(urls)
        for sub in node.get("subs", []):
            recurse(sub)

    for cat in tree:
        recurse(cat)

    logprint(f"Discovered {len(product_urls)} products.")
    return list(product_urls)

def scrape_all_products():
    tree = build_category_tree()
    product_urls = traverse_category_tree(tree)
    products = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url = {executor.submit(scrape_product, url): url for url in product_urls}
        for future in as_completed(future_to_url):
            prod = future.result()
            if prod and prod.get("Namn"):
                products.append(prod)
    # Deduplication can be added here
    logprint(f"After deduplication: {len(products)} products.")
    return products