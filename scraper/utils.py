"""
scraper/utils.py

Utility functions for the Table.se scraper.
Includes helpers for deduplication, parsing, and other generic tasks.
"""

def deduplicate_products(products, key_fields=None):
    """
    Remove duplicate product dicts from a list, using selected fields as the unique key.

    Args:
        products (list of dict): List of product records.
        key_fields (list of str): Fields to use as unique key. Defaults to ["Namn", "Artikelnummer"].

    Returns:
        list of dict: Deduplicated list.
    """
    if not key_fields:
        key_fields = ["Namn", "Artikelnummer"]
    seen = set()
    deduped = []
    for prod in products:
        key = tuple(prod.get(field, "") for field in key_fields)
        if key not in seen:
            seen.add(key)
            deduped.append(prod)
    return deduped

def safe_get(d, *fields, default=""):
    """
    Safely get nested values from dicts.
    Example: safe_get(product, 'pricing', 'price', default="N/A")
    """
    for field in fields:
        if isinstance(d, dict) and field in d:
            d = d[field]
        else:
            return default
    return d
