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
import sys

class FancyFormatter(logging.Formatter):
    ICONS = {
        logging.DEBUG: "🐞",
        logging.INFO: "📝",
        logging.WARNING: "😬",
        logging.ERROR: "💥",
        logging.CRITICAL: "🔥"
    }
    COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[1;41m"  # Bold + Red BG
    }
    RESET = "\033[0m"

    def format(self, record):
        icon = self.ICONS.get(record.levelno, "")
        color = self.COLORS.get(record.levelno, "")
        # Including module and line number
        msg = super().format(record)
        return f"{color}{icon} {msg}{self.RESET}"

def setup_logging(logfile="scraper.log"):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Remove all handlers (avoid duplicates if setup_logging is called multiple times)
    logger.handlers = []

    # File handler - plain but rich with context
    file_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(module)s:%(lineno)d]: %(message)s", datefmt="%H:%M:%S"
    )
    fh = logging.FileHandler(logfile)
    fh.setFormatter(file_formatter)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    # Console handler - color + icon + context
    console_formatter = FancyFormatter(
        "%(asctime)s %(levelname)s [%(module)s:%(lineno)d]: %(message)s", datefmt="%H:%M:%S"
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(console_formatter)
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    print(f"Logging set up to {logfile} (file, plain) and console (color, icons)")

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
