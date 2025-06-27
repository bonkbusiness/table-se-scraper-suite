"""
exporter/qc.py

Quality control and data validation utilities for the Table.se scraper suite.

This module provides:
- Deduplication of products (with normalization)
- Checking field completeness
- Finding duplicate products (with normalization)
- Exporting validation errors to XLSX
- (Optional) Deep product validation via integration with scanner.validate_product

All functions use logging for reporting and diagnostics.
"""

from typing import List, Dict, Any, Optional, Tuple
from openpyxl import Workbook

from scraper.logging import get_logger
from scraper.utils import normalize_text, normalize_whitespace
# If you want to use more, import as needed.

logger = get_logger("qc")

def deduplicate_products(
    products: List[Dict[str, Any]],
    key_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Remove duplicate products based on a tuple of normalized key fields.

    Args:
        products (List[Dict[str, Any]]): List of product dictionaries.
        key_fields (Optional[List[str]]): Fields to use for deduplication 
            (default: ["Namn", "Artikelnummer"]).

    Returns:
        List[Dict[str, Any]]: Deduplicated list of products.
    """
    if not key_fields:
        key_fields = ["Namn", "Artikelnummer"]
    seen = set()
    deduped = []
    for prod in products:
        # Normalize each key field value for robust deduplication
        key = tuple(normalize_text(normalize_whitespace(str(prod.get(field, "")))) for field in key_fields)
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
    Identify products missing any required field.

    Args:
        products (List[Dict[str, Any]]): List of product dictionaries.
        required_fields (Optional[List[str]]): List of fields to check for completeness
            (default: ["Namn", "Artikelnummer", "Pris inkl. moms (värde)", "Produkt-URL"]).

    Returns:
        List[Dict[str, Any]]: List of products missing at least one required field.
    """
    if not required_fields:
        required_fields = ["Namn", "Artikelnummer", "Pris inkl. moms (värde)", "Produkt-URL"]
    incomplete = []
    for prod in products:
        for field in required_fields:
            # Normalize and check for empty/meaningless values
            value = normalize_whitespace(str(prod.get(field, "")))
            if not value:
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
    Find groups of duplicate products based on normalized key fields.

    Args:
        products (List[Dict[str, Any]]): List of product dictionaries.
        key_fields (Optional[List[str]]): Fields to define uniqueness (default: ["Namn", "Artikelnummer"]).

    Returns:
        List[Tuple[Tuple, List[Dict[str, Any]]]]: 
            List of (key, [product1, product2, ...]) tuples for duplicate groups.
    """
    if not key_fields:
        key_fields = ["Namn", "Artikelnummer"]
    lookup = {}
    for prod in products:
        # Normalize each key field value
        key = tuple(normalize_text(normalize_whitespace(str(prod.get(field, "")))) for field in key_fields)
        lookup.setdefault(key, []).append(prod)
    duplicates = [(k, v) for k, v in lookup.items() if len(v) > 1]
    for key, group in duplicates:
        logger.warning(f"Duplicate key {key}: {len(group)} occurrences")
    return duplicates

def export_errors_to_xlsx(errors: List[Dict[str, Any]], filename: str) -> Optional[str]:
    """
    Export a list of product errors to an XLSX file.

    Args:
        errors (List[Dict[str, Any]]): List of error dicts, typically with keys "error_type" and "product".
        filename (str): Filename for the XLSX export.

    Returns:
        Optional[str]: Filename if export succeeded, None otherwise.
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

def validate_products_with_scanner(
    products: List[Dict[str, Any]],
    required_fields: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """
    Uses the scanner.validate_product function to get detailed error lists per product.

    Args:
        products (List[Dict[str, Any]]): List of product dictionaries.
        required_fields (Optional[List[str]]): Fields to validate, or None for scanner default.

    Returns:
        Dict[str, List[str]]: Dictionary mapping product key (e.g., SKU or index)
            to a list of validation error messages.
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
