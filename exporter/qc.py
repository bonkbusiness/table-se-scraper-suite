"""
exporter/qc.py

Quality control and data validation for the Table.se scraper suite.
Includes functions to check field completeness, find duplicates, and export errors.
"""

from typing import List, Dict, Any, Optional, Tuple
from openpyxl import Workbook

try:
    from scraper.logging import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger

logger = get_logger("qc")

def deduplicate_products(
    products: List[Dict[str, Any]],
    key_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Remove duplicate products based on a tuple of key fields (default: ['Namn', 'Artikelnummer']).
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
        else:
            logger.debug(f"Duplicate found and removed: {key}")
    logger.info(f"Deduplicated products: {len(products)} -> {len(deduped)}")
    return deduped

def check_field_completeness(
    products: List[Dict[str, Any]],
    required_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Returns a list of products missing any of the required fields.
    """
    if not required_fields:
        required_fields = ["Namn", "Artikelnummer", "Pris inkl. moms (värde)", "Produkt-URL"]
    incomplete = []
    for prod in products:
        for field in required_fields:
            if not prod.get(field):
                logger.debug(f"Product missing field {field}: {prod.get('Artikelnummer', prod)}")
                incomplete.append(prod)
                break
    logger.info(f"Products with missing fields: {len(incomplete)} / {len(products)}")
    return incomplete

def find_duplicate_products(
    products: List[Dict[str, Any]],
    key_fields: Optional[List[str]] = None
) -> List[Tuple[Tuple, List[Dict[str, Any]]]]:
    """
    Find duplicate products based on key fields.

    Returns:
        list of (key, [product1, product2, ...]) for duplicates.
    """
    if not key_fields:
        key_fields = ["Namn", "Artikelnummer"]
    lookup = {}
    for prod in products:
        key = tuple(prod.get(field, "") for field in key_fields)
        lookup.setdefault(key, []).append(prod)
    duplicates = [(k, v) for k, v in lookup.items() if len(v) > 1]
    for key, group in duplicates:
        logger.warning(f"Duplicate key {key}: {len(group)} occurrences")
    return duplicates

def export_errors_to_xlsx(errors: List[Dict[str, Any]], filename: str) -> Optional[str]:
    """
    Export error list to the given xlsx filename.
    """
    if not errors:
        logger.info("No validation errors to export.")
        return None
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Produktfel"
        ws.append(["Index", "Feltyp", "Produktinfo"])
        for idx, err in enumerate(errors):
            ws.append([
                idx + 1,
                err.get("error_type", str(err.get("type", ""))),
                str(err.get("product", err))
            ])
        wb.save(filename)
        logger.info(f"Exported errors to XLSX: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving errors XLSX: {e}")
        return None

# Optionally, integrate with scanner.validate_product for deeper validation:
def validate_products_with_scanner(
    products: List[Dict[str, Any]],
    required_fields: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """
    Uses scanner.validate_product to get detailed error lists.
    Returns a dict of {sku or idx: [error messages]}.
    """
    try:
        from scraper.scanner import validate_product
    except ImportError:
        logger.warning("scanner.validate_product not available.")
        return {}
    errors = {}
    for idx, prod in enumerate(products):
        issues = validate_product(prod, required_fields=required_fields)
        if issues:
            key = prod.get("Artikelnummer") or f"idx_{idx}"
            errors[key] = issues
            logger.debug(f"Validation issues for {key}: {issues}")
    logger.info(f"Scanner flagged {len(errors)} products with issues.")
    return errors
