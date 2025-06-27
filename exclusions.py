"""
exclusions.py

Defines URL exclusion logic for the Table.se Scraper Suite.

This module specifies which product/category URLs should be ignored during scraping.
Primarily used to avoid scraping unwanted or unsupported sections (such as containers, technology, tents, etc.)
and to keep the dataset clean.

FUNCTIONS:
    - is_excluded(url): Returns True if a given URL matches any exclusion prefix.

USAGE:
    from exclusions import is_excluded

    if is_excluded(product_url):
        # Skip this URL
        continue

Author: bonkbusiness
License: MIT
"""

from typing import List

EXCLUDED_URL_PREFIXES: List[str] = [
    "https://www.table.se/produkter/container/",
    "https://www.table.se/produkter/teknik/",
    "https://www.table.se/produkter/talt/",
    # Add more as needed; these are excluded from scraping.
]

def is_excluded(url: str) -> bool:
    """
    Check if the provided URL should be excluded from scraping.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL starts with any of the defined exclusion prefixes, else False.

    Example:
        >>> is_excluded("https://www.table.se/produkter/container/box123")
        True
        >>> is_excluded("https://www.table.se/produkter/bord/123")
        False
    """
    return any(url.startswith(prefix) for prefix in EXCLUDED_URL_PREFIXES)