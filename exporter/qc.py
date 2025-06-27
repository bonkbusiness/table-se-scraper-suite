"""
exporter/qc.py

Quality control and data validation utilities for the Table.se scraper suite.

This module acts as a "man-in-the-middle" between cache.py and exporters (xlsx.py, csv.py).
It ensures all product data is deduplicated, checked for completeness, and optionally validated
before being passed to exporters. It also provides error reporting for invalid records.

Exports:
- qc_and_export_to_xlsx
- qc_and_export_to_csv

QC functions (deduplication, completeness, etc.) are also available for direct use.
"""

from typing import List, Dict, Any, Optional, Tuple
from openpyxl import Workbook
import csv
import os

from scraper.logging import get_logger
from scraper.utils import normalize_text, normalize_whitespace
from scraper.utils import make_output_filename

logger = get_logger("qc")

def export_errors_to_xlsx(errors, filename=None):
    """
    Exports errors to an XLSX file, filename is auto-generated in error/ if not provided.
    """
    from openpyxl import Workbook
    import os

    if filename is None:
        filename = make_output_filename('errors', 'xlsx', 'error')
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Errors"
    ws.append(["error_type", "product"])
    for error in errors:
        ws.append([error.get("error_type", ""), str(error.get("product", ""))])
    wb.save(filename)
    return filename

# === Core QC Utility Functions ===

def deduplicate_products(
    products: List[Dict[str, Any]],
    key_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Remove duplicate products based on a tuple of normalized key fields.
    """
    if not key_fields:
        key_fields = ["Namn", "Artikelnummer"]
    seen = set()
    deduped = []
    for prod in products:
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
    """
    if not required_fields:
        required_fields = ["Namn", "Artikelnummer", "Pris inkl. moms (värde)", "Produkt-URL"]
    incomplete = []
    for prod in products:
        for field in required_fields:
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
    """
    if not key_fields:
        key_fields = ["Namn", "Artikelnummer"]
    lookup = {}
    for prod in products:
        key = tuple(normalize_text(normalize_whitespace(str(prod.get(field, "")))) for field in key_fields)
        lookup.setdefault(key, []).append(prod)
    duplicates = [(k, v) for k, v in lookup.items() if len(v) > 1]
    for key, group in duplicates:
        logger.warning(f"Duplicate key {key}: {len(group)} occurrences")
    return duplicates

def export_errors_to_xlsx(errors: List[Dict[str, Any]], filename: str) -> Optional[str]:
    """
    Export a list of product errors to an XLSX file.
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

def export_errors_to_csv(errors: List[Dict[str, Any]], filename: str) -> Optional[str]:
    """
    Export a list of product errors to a CSV file.
    """
    if not errors:
        logger.info("No validation errors to export.")
        return None
    try:
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Index", "Feltyp", "Produktinfo"])
            for idx, err in enumerate(errors):
                writer.writerow([
                    idx + 1,
                    err.get("error_type", str(err.get("type", ""))),
                    str(err.get("product", err))
                ])
        logger.info(f"Exported errors to CSV: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving errors CSV: {e}")
        return None

def validate_products_with_scanner(
    products: List[Dict[str, Any]],
    required_fields: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """
    Uses the scanner.validate_product function to get detailed error lists per product.
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

# === Man-in-the-middle QC + Export Pipeline Functions ===

def qc_and_export_to_xlsx(
    products: List[Dict[str, Any]],
    filename: str,
    error_filename: Optional[str] = None
) -> str:
    """
    Run full quality control on products and export valid products to XLSX.
    Invalid products are exported to a separate errors XLSX file if error_filename is specified.
    Returns the path to the exported XLSX file.
    """
    deduped = deduplicate_products(products)
    incomplete = check_field_completeness(deduped)
    valid = [p for p in deduped if p not in incomplete]
    # Optionally: use scanner-based validation here and filter further if desired

    # Export valid products
    from exporter.xlsx import export_to_xlsx
    export_to_xlsx(valid, filename)
    logger.info(f"Exported {len(valid)} valid products to {filename}")

    # Export errors if requested
    if error_filename and incomplete:
        export_errors_to_xlsx(
            [{"error_type": "missing_fields", "product": p} for p in incomplete],
            error_filename
        )
    return filename

def qc_and_export_to_csv(
    products: List[Dict[str, Any]],
    filename: str,
    error_filename: Optional[str] = None
) -> str:
    """
    Run full quality control on products and export valid products to CSV.
    Invalid products are exported to a separate errors CSV file if error_filename is specified.
    Returns the path to the exported CSV file.
    """
    deduped = deduplicate_products(products)
    incomplete = check_field_completeness(deduped)
    valid = [p for p in deduped if p not in incomplete]
    # Optionally: use scanner-based validation here and filter further if desired

    # Export valid products
    from exporter.csv import export_to_csv
    export_to_csv(valid, filename)
    logger.info(f"Exported {len(valid)} valid products to {filename}")

    # Export errors if requested
    if error_filename and incomplete:
        export_errors_to_csv(
            [{"error_type": "missing_fields", "product": p} for p in incomplete],
            error_filename
        )
    return filename
