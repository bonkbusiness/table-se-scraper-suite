"""
exporter/qc.py

Quality control and data validation for the Table.se scraper suite.
Includes functions to check field completeness and find duplicates.
"""

def check_field_completeness(products, required_fields=None):
    """
    Identify products missing any required field.

    Args:
        products (list of dict): List of products.
        required_fields (list of str): Fields required for completeness.

    Returns:
        list of dict: List of incomplete product records.
    """
    if not required_fields:
        required_fields = ["Namn", "Artikelnummer", "Pris inkl. moms (värde)", "Produkt-URL"]
    incomplete = []
    for prod in products:
        for field in required_fields:
            if not prod.get(field):
                incomplete.append(prod)
                break
    return incomplete

def find_duplicate_products(products, key_fields=None):
    """
    Find duplicate products based on key fields.

    Args:
        products (list of dict): List of products.
        key_fields (list of str): Fields to define uniqueness.

    Returns:
        list of tuple: List of (key, [product1, product2, ...]) for duplicates.
    """
    if not key_fields:
        key_fields = ["Namn", "Artikelnummer"]
    lookup = {}
    for prod in products:
        key = tuple(prod.get(field, "") for field in key_fields)
        lookup.setdefault(key, []).append(prod)
    duplicates = [(k, v) for k, v in lookup.items() if len(v) > 1]
    return duplicates
