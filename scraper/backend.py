"""
scraper/backend.py

Backend orchestration module for the Table.se Scraper Suite.

This module provides the main scraping pipeline for Table.se, including:
    - Category tree extraction
    - Parallelized product URL collection
    - Parallelized product detail scraping with caching and retry logic
    - Post-processing, including QC/validation and filtered export

Features:
    - Configurable parallelism, retry, throttle, and caching via CLI arguments
    - Robust logging at all stages for diagnostics and monitoring
    - Utilizes a persistent cache to avoid redundant network requests and improve efficiency
    - Exclusion logic for URLs and categories
    - Exports cleaned data to JSON, and optionally flagged products for human review

USAGE:
    python -m scraper.backend [options]

CLI OPTIONS:
    --max-workers     Number of parallel threads (default: 8)
    --retries         Number of retries for failed requests (default: 2)
    --output          Output JSON file path (default: products_<timestamp>.json)
    --throttle        Base throttle delay between requests (default: 0.7s)
    --cache           Enable HTTP requests caching (requires requests-cache)
    --review-export   Export flagged products for review (Excel)

DEPENDENCIES:
    - scraper.cache
    - scraper.fetch
    - scraper.scanner
    - scraper.utils
    - scraper.category
    - scraper.product
    - exclusions

Author: bonkbusiness
License: MIT
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
from typing import List, Dict, Any

import logging
from scraper.cache import Cache
from scraper.fetch import fetch_url, enable_requests_cache
from scraper.scanner import scan_products
from scraper.utils import deduplicate, make_output_filename
from .category import extract_category_tree
from .product import extract_products_from_category, scrape_product
from exclusions import is_excluded

# Progress bars
from tqdm import tqdm  # pip install tqdm

logger = logging.getLogger("scraper.backend")
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s'
)

# Instantiate a persistent cache object for all operations
cache = Cache()

def collect_product_urls(
    tree: List[Dict[str, Any]],
    max_workers: int = 8,
    retries: int = 2,
    throttle: float = 0.7
) -> List[str]:
    """
    Parallel collection of all product URLs from the category tree.

    Args:
        tree (list): List of category tree nodes (dicts).
        max_workers (int): Number of parallel threads.
        retries (int): Number of retries for failed category fetches.
        throttle (float): Base throttle delay (seconds).

    Returns:
        list: Unique product URLs (strings).
    """
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
                # Fetch and cache category page HTML
                if cache.exists(url):
                    html = cache.get(url)
                    logger.debug(f"Category cache hit: {url}")
                else:
                    html = fetch_url(url, throttle=throttle, max_retries=retries)
                    cache.set(url, html, Cache.hash_content(html))
                    logger.debug(f"Fetched and cached category: {url}")
                # Always pass the category URL to extract_products_from_category
                return extract_products_from_category(url)
            except Exception as e:
                logger.warning(f"Error fetching category {url}, attempt {attempt+1}/{retries}: {e}")
                if attempt < retries:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to fetch category {url} after {retries+1} attempts")
        return []

    bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_products, url): url for url in category_urls}
        # tqdm for categories processed
        for future in tqdm(as_completed(future_to_url), total=len(future_to_url),
                           desc="Categories Processed", bar_format=bar_format):
            url = future_to_url[future]
            try:
                urls = future.result()
                all_product_urls.update(urls)
                logger.info(f"Collected {len(urls)} products from {url}")
            except Exception as e:
                logger.error(f"Error in collecting products from {url}: {e}")

    result = deduplicate(list(all_product_urls))
    logger.info(f"Total unique product URLs collected: {len(result)}")
    return result

def scrape_products(
    product_urls: List[str],
    max_workers: int = 8,
    retries: int = 2,
    throttle: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Parallel scraping of product details with caching and deduplication.

    Args:
        product_urls (list): List of product URLs to scrape.
        max_workers (int): Number of parallel threads.
        retries (int): Number of retries for failed scrapes.
        throttle (float): Base throttle delay (seconds).

    Returns:
        list: Product dictionaries with all parsed fields.
    """
    results = []
    seen_keys = set()
    logger.info(f"Scraping {len(product_urls)} products using {max_workers} workers.")

    def process(url):
        for attempt in range(retries + 1):
            try:
                # Fetch/cached HTML for product page
                if cache.exists(url):
                    html = cache.get(url)
                    logger.debug(f"Product cache hit (raw HTML): {url}")
                else:
                    html = fetch_url(url, throttle=throttle, max_retries=retries)
                    cache.set(url, html, Cache.hash_content(html))
                    logger.debug(f"Fetched and cached product HTML: {url}")

                # Scrape product details using the product scraper
                product = scrape_product(url)
                if not product:
                    return None

                # Deduplicate on (SKU, URL)
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

    bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(process, url): url for url in product_urls}
        # tqdm for products scraped
        for future in tqdm(as_completed(future_to_url), total=len(future_to_url),
                           desc="Products Scraped", bar_format=bar_format):
            try:
                prod = future.result()
                if prod:
                    results.append(prod)
            except Exception as e:
                logger.error(f"Error in product scrape: {e}")

    logger.info(f"Scraped {len(results)} products.")
    return results

def main():
    """
    CLI entrypoint for backend scraping pipeline.
    Handles argument parsing, pipeline orchestration, and output.
    """
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
    bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
    with open(args.output, "w", encoding="utf-8") as f:
        # tqdm for exporting (writing) products
        for idx, product in enumerate(tqdm(filtered_products, desc="Products Exported", bar_format=bar_format)):
            if idx == 0:
                f.write("[\n")
            else:
                f.write(",\n")
            json.dump(product, f, ensure_ascii=False, indent=2)
        if filtered_products:
            f.write("\n]\n")
        else:
            f.write("[]\n")
    logger.info(f"Exported {len(filtered_products)} products to {args.output}")

if __name__ == "__main__":
    main()