"""
Performance and Robustness wrappers for Table.se scraper.
Add retry, logging, polite crawling, and proxy support.

Usage:
    from table_se_scraper_performance import robust_scrape, setup_logging

    setup_logging()
    robust_scrape(your_scrape_function, url, retries=3, delay=2)
"""

import time
import logging
from functools import wraps
import random

def setup_logging(logfile="scraper.log"):
    logging.basicConfig(
        filename=logfile,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    print(f"Logging set up to {logfile}")

def robust_scrape(scrape_func, url, retries=3, delay=2, backoff=2, proxies=None):
    """
    Wrap any scraping function for retry and polite crawling.
    """
    for attempt in range(1, retries + 1):
        try:
            if proxies:
                # Assume scrape_func accepts proxies as kwarg
                result = scrape_func(url, proxies=proxies)
            else:
                result = scrape_func(url)
            logging.info(f"Success: {url}")
            # Random polite sleep
            time.sleep(delay + random.uniform(0, 1))
            return result
        except Exception as e:
            logging.warning(f"Attempt {attempt} failed for {url}: {e}")
            time.sleep(delay * (backoff ** (attempt - 1)))
    logging.error(f"All retries failed for {url}")
    return None