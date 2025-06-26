from exclusions import is_excluded
from scraper.fetch import get_soup

def extract_product_data(product_url):
    if is_excluded(product_url):
        print(f"Skipping excluded product: {product_url}")
        return None
    soup = get_soup(product_url)
    if not soup:
        return None
    # ... your extraction logic here ...
    return {}
