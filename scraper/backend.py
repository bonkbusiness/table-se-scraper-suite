import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
from typing import List, Dict, Any

import logging
from scraper.cache import Cache
from scraper.fetch import fetch_url, enable_requests_cache
from scraper.scanner import scan_products  # Updated: use the new scanner interface
from scraper.utils import deduplicate, make_output_filename
from .category import extract_category_tree
from .product import extract_products_from_category, scrape_product
from exclusions import is_excluded

logger = logging.getLogger("scraper.backend")
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s'
)

# Instantiate cache
cache = Cache()

def collect_product_urls(tree: List[Dict[str, Any]], max_workers: int = 8, retries: int = 2, throttle: float = 0.7) -> List[str]:
    """Parallel fetches product URLs from category tree."""
    category_urls = []

    def recurse(node):
        url = node.get("url")
        if url and not is_excluded(url):
            category_urls.append(url)
        for sub in node.get("subs", []):
            recurse(sub)

    for cat in tree:
        recurse(cat)

    all_product_urls = set()
    logger.info(f"Collecting product URLs from {len(category_urls)} categories using {max_workers} workers.")

    def fetch_products(url):
        for attempt in range(retries + 1):
            try:
                # Fetch and cache category page
                if cache.exists(url):
                    html = cache.get(url)
                    logger.debug(f"Category cache hit: {url}")
                else:
                    html = fetch_url(url, throttle=throttle, max_retries=retries)
                    cache.set(url, html, Cache.hash_content(html))
                    logger.debug(f"Fetched and cached category: {url}")
                # Pass the category URL, not HTML, to extract_products_from_category
                return extract_products_from_category(url)
            except Exception as e:
                logger.warning(f"Error fetching category {url}, attempt {attempt+1}/{retries}: {e}")
                if attempt < retries:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to fetch category {url} after {retries+1} attempts")
        return []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_products, url): url for url in category_urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                urls = future.result()
                all_product_urls.update(urls)
                logger.info(f"Collected {len(urls)} products from {url}")
            except Exception as e:
                logger.error(f"Error in collecting products from {url}: {e}")

    return deduplicate(list(all_product_urls))

def scrape_products(product_urls: List[str], max_workers: int = 8, retries: int = 2, throttle: float = 0.7) -> List[Dict[str, Any]]:
    """Parallel scraping with caching and content hash checking."""
    results = []
    seen_keys = set()
    logger.info(f"Scraping {len(product_urls)} products using {max_workers} workers.")

    def process(url):
        for attempt in range(retries + 1):
            try:
                # Fetch HTML (cache by URL) and hash for change detection
                if cache.exists(url):
                    html = cache.get(url)
                    logger.debug(f"Product cache hit (raw HTML): {url}")
                else:
                    html = fetch_url(url, throttle=throttle, max_retries=retries)
                    cache.set(url, html, Cache.hash_content(html))
                    logger.debug(f"Fetched and cached product HTML: {url}")

                # Use the product scraper
                product = scrape_product(url)  # Call the singular function, passing just the URL
                if not product:
                    return None

                # Use a key (SKU, Namn, or URL as fallback)
                sku = product.get("Artikelnummer") or product.get("Namn") or url
                key = (sku, url)
                if key in seen_keys:
                    return None
                seen_keys.add(key)

                logger.info(f"Scraped product: {sku}")
                return product
            except Exception as e:
                logger.warning(f"Error scraping {url}, attempt {attempt+1}/{retries}: {e}")
                if attempt < retries:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to scrape {url} after {retries+1} attempts")
        return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(process, url): url for url in product_urls}
        for future in as_completed(future_to_url):
            try:
                prod = future.result()
                if prod:
                    results.append(prod)
            except Exception as e:
                logger.error(f"Error in product scrape: {e}")

    return results

def main():
    parser = argparse.ArgumentParser(description="Table.se Product Scraper Backend CLI")
    parser.add_argument("--max-workers", type=int, default=8, help="Number of parallel threads (default: 8)")
    parser.add_argument("--retries", type=int, default=2, help="Number of retries for failed requests (default: 2)")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file (default: products_<timestamp>.json)")
    parser.add_argument("--throttle", type=float, default=0.7, help="Base throttle delay between requests (default: 0.7)")
    parser.add_argument("--cache", action="store_true", help="Enable HTTP requests caching (requires requests-cache)")
    parser.add_argument("--review-export", action="store_true", help="Export flagged products for human review (Excel)")
    args = parser.parse_args()

    if args.cache:
        enable_requests_cache(backend="sqlite", expire_after=3600)

    # 1. Extract category tree
    tree = extract_category_tree()
    # 2. Collect product URLs
    product_urls = collect_product_urls(tree, max_workers=args.max_workers, retries=args.retries, throttle=args.throttle)
    logger.info(f"Found {len(product_urls)} unique product URLs.")

    # 3. Scrape products (with cache and change detection)
    products = scrape_products(product_urls, max_workers=args.max_workers, retries=args.retries, throttle=args.throttle)

    # 4. Smart scan/validation (updated to use new scanner.py interface)
    filtered_products, product_errors = scan_products(
        products,
        review_export=args.review_export
    )
    flagged_count = len(product_errors)
    logger.info(f"Scan complete. {flagged_count} products flagged for review.")

    # 5. Export result (only valid products)
    if args.output is None:
        args.output = make_output_filename('products', 'json')
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(filtered_products, f, ensure_ascii=False, indent=2)
    logger.info(f"Exported {len(filtered_products)} products to {args.output}")

if __name__ == "__main__":
    main()