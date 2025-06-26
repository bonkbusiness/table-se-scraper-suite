import logging
import time
import json
import argparse
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .category import extract_category_tree
from .product import extract_products_from_category, scrape_product
from exclusions import is_excluded

# import sentry_sdk  # Uncomment and configure if using Sentry
# sentry_sdk.init(dsn="YOUR_SENTRY_DSN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def collect_product_urls_from_tree_parallel(
    tree: List[Dict[str, Any]], 
    max_workers: int = 8, 
    retries: int = 2
) -> List[str]:
    """
    Traverse the category tree and collect product URLs in parallel for each category node.
    Returns a deduplicated list of product URLs.
    """
    category_urls = []

    def recurse(node: Dict[str, Any]):
        url = node.get("url")
        if url and not is_excluded(url):
            category_urls.append(url)
        for sub in node.get("subs", []):
            recurse(sub)

    for cat in tree:
        recurse(cat)

    all_product_urls = set()
    total = len(category_urls)
    logging.info(f"Collecting product URLs from {total} categories using {max_workers} workers.")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(_extract_products_with_retry, url, retries): url
            for url in category_urls
        }
        for idx, future in enumerate(as_completed(future_to_url), 1):
            url = future_to_url[future]
            try:
                product_urls = future.result()
                all_product_urls.update(product_urls)
                logging.info(f"[{idx}/{total}] Collected {len(product_urls)} products from {url}")
            except Exception as e:
                logging.error(f"[{idx}/{total}] Failed to collect products from {url}: {type(e).__name__}: {e}")
                # sentry_sdk.capture_exception(e)

    return list(all_product_urls)

def _extract_products_with_retry(url: str, retries: int = 2, delay: int = 2) -> List[str]:
    """
    Call extract_products_from_category() with advanced retry and error handling.
    """
    import requests
    for attempt in range(retries + 1):
        try:
            return extract_products_from_category(url)
        except requests.exceptions.RequestException as e:
            logging.warning(f"Network error on {url}: {e} (attempt {attempt + 1}/{retries})")
            # sentry_sdk.capture_exception(e)
            if attempt < retries:
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                raise
        except Exception as e:
            logging.error(f"Non-network error on {url}: {type(e).__name__}: {e}")
            # sentry_sdk.capture_exception(e)
            raise

def scrape_all_products_parallel(
    max_workers: int = 8, 
    retries: int = 2
) -> List[Dict[str, Any]]:
    """
    Orchestrates the full scraping process in parallel.
    """
    tree = extract_category_tree()
    product_urls = collect_product_urls_from_tree_parallel(
        tree, max_workers=max_workers, retries=retries
    )
    products = []
    seen = set()
    total = len(product_urls)
    logging.info(f"Scraping {total} products using {max_workers} workers.")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(_scrape_product_with_retry, url, retries): url
            for url in product_urls
        }
        for idx, future in enumerate(as_completed(future_to_url), 1):
            url = future_to_url[future]
            try:
                prod = future.result()
                if prod:
                    key = (prod.get("Namn"), prod.get("Artikelnummer"))
                    if key not in seen:
                        seen.add(key)
                        products.append(prod)
                        logging.info(f"[{idx}/{total}] Scraped product: {key}")
            except Exception as e:
                logging.error(f"[{idx}/{total}] Failed to scrape product {url}: {type(e).__name__}: {e}")
                # sentry_sdk.capture_exception(e)
    return products

def _scrape_product_with_retry(url: str, retries: int = 2, delay: int = 2) -> Dict[str, Any]:
    """
    Call scrape_product() with advanced retry and error handling.
    """
    import requests
    for attempt in range(retries + 1):
        try:
            return scrape_product(url)
        except requests.exceptions.RequestException as e:
            logging.warning(f"Network error scraping {url}: {e} (attempt {attempt + 1}/{retries})")
            # sentry_sdk.capture_exception(e)
            if attempt < retries:
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                raise
        except Exception as e:
            logging.error(f"Non-network error scraping {url}: {type(e).__name__}: {e}")
            # sentry_sdk.capture_exception(e)
            raise

def main():
    parser = argparse.ArgumentParser(
        description="Table.se Product Scraper Backend CLI"
    )
    parser.add_argument(
        "--max-workers", type=int, default=8,
        help="Number of parallel threads (default: 8)"
    )
    parser.add_argument(
        "--retries", type=int, default=2,
        help="Number of retries for failed requests (default: 2)"
    )
    parser.add_argument(
        "--output", type=str, default="products.json",
        help="Output JSON file (default: products.json)"
    )
    args = parser.parse_args()

    products = scrape_all_products_parallel(
        max_workers=args.max_workers,
        retries=args.retries
    )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    logging.info(f"Scraped {len(products)} unique products. Saved to {args.output}")

if __name__ == "__main__":
    main()