"""
scraper/scanner.py

Validation, anomaly detection, and review export utilities for the Table.se Scraper Suite.

This module provides:
    - Product data validation: checks required fields, value formats, and more
    - Robust selectors for HTML parsing
    - Statistical anomaly/outlier detection on numeric fields
    - Logging of validation reports
    - Export of flagged products (with errors) to Excel for human review
    - Pipeline-style bulk product scanning and filtering

Usage:
    from scraper.scanner import scan_products

    filtered, product_errors = scan_products(products, review_export=True)

Author: bonkbusiness
License: MIT
"""

import re
import numpy as np  # Ensure numpy is installed
from typing import List, Dict, Any, Tuple, Optional

from scraper.logging import get_logger

logger = get_logger("scanner")

# -- Product datapoints (from scraper/product.py, kept in sync with export) --
PRODUCT_DATAPOINTS = [
    "Namn",
    "Artikelnummer",
    "Färg",
    "Material",
    "Serie",
    "Pris exkl. moms (värde)",
    "Pris exkl. moms (enhet)",
    "Pris inkl. moms (värde)",
    "Pris inkl. moms (enhet)",
    "Längd (värde)", "Längd (enhet)",
    "Bredd (värde)", "Bredd (enhet)",
    "Höjd (värde)", "Höjd (enhet)",
    "Djup (värde)", "Djup (enhet)",
    "Diameter (värde)", "Diameter (enhet)",
    "Kapacitet (värde)", "Kapacitet (enhet)",
    "Volym (värde)", "Volym (enhet)",
    "Vikt (värde)", "Vikt (enhet)",
    "Data (text)",
    "Kategori (parent)",
    "Kategori (sub)",
    "Produktbild-URL",
    "Produkt-URL",
    "Beskrivning",
    "Extra data",
]

def validate_product(product: Dict[str, Any], required_fields=None) -> List[str]:
    """
    Validate a product dictionary according to required fields and value rules.

    Args:
        product (dict): The product data to validate.
        required_fields (list, optional): Override required fields.

    Returns:
        list: Validation error messages (empty if valid).
    """
    REQUIRED_FIELDS = [
        "Namn", "Artikelnummer", "Pris inkl. moms (värde)", "Produkt-URL", "Produktbild-URL"
    ]
    if not required_fields:
        required_fields = REQUIRED_FIELDS
    errors = []
    for field in required_fields:
        if not str(product.get(field, "")).strip():
            errors.append(f"Missing: {field}")
    try:
        price = float(str(product.get("Pris inkl. moms (värde)", "0")).replace(",", "."))
        if price <= 0:
            errors.append("Price must be positive")
    except Exception:
        errors.append("Price is not a number")
    sku = str(product.get("Artikelnummer", ""))
    if sku and not re.match(r"^[A-Za-z0-9\- ]+$", sku):
        errors.append("Artikelnummer (SKU) may have invalid characters")
    img = str(product.get("Produktbild-URL", ""))
    if not img or img.strip() == "" or img.endswith("placeholder.png"):
        errors.append("Missing or placeholder product image")
    # Note: Category field names for compatibility with product.py (Kategori (parent)/Kategori (sub))
    if not (product.get("Kategori (parent)") or product.get("Kategori (sub)")
            or product.get("Category") or product.get("category")):
        errors.append("Missing category")
    url = str(product.get("Produkt-URL", ""))
    if url and not url.startswith("http"):
        errors.append("Invalid product URL")
    namn = str(product.get("Namn", ""))
    if namn and len(namn) < 3:
        errors.append("Suspiciously short product name")
    return errors

def robust_select_one(soup, selectors: List[str]) -> Optional[str]:
    for sel in selectors:
        elem = soup.select_one(sel)
        if elem:
            text = elem.get_text(strip=True)
            if text:
                return text
    return None

def robust_select_attr(soup, selectors: List[str], attr: str) -> Optional[str]:
    for sel in selectors:
        elem = soup.select_one(sel)
        if elem and elem.has_attr(attr):
            val = elem.get(attr, "").strip()
            if val:
                return val
    return None

def detect_anomalies(products: List[Dict[str, Any]], field: str, z_thresh: float = 3.5) -> List[Tuple[int, Any]]:
    values = []
    idx_map = []
    for idx, prod in enumerate(products):
        try:
            v = float(str(prod.get(field, "")).replace(",", "."))
            values.append(v)
            idx_map.append(idx)
        except Exception:
            continue
    if not values or len(values) < 3:
        return []
    values_np = np.array(values)
    median = np.median(values_np)
    diff = np.abs(values_np - median)
    mad = np.median(diff)
    if mad == 0:
        return []
    modified_z = 0.6745 * (values_np - median) / mad
    outliers = [(idx_map[i], values[i]) for i in range(len(values)) if abs(modified_z[i]) > z_thresh]
    return outliers

def log_validation_report(products: List[Dict[str, Any]], product_errors: Dict[str, List[str]]):
    total = len(products)
    flagged = len(product_errors)
    logger.info(f"Validation Summary: {flagged}/{total} products flagged with issues.")
    if flagged > 0:
        logger.info("First 5 flagged examples:")
        for i, (key, errs) in enumerate(product_errors.items()):
            logger.info(f"Product {key}: {errs}")
            if i >= 4:
                break

def export_flagged_products(products: List[Dict[str, Any]], product_errors: Dict[str, List[str]], filename: str = "flagged_products_review.xlsx"):
    try:
        from openpyxl import Workbook  # Ensure openpyxl is installed
        wb = Workbook()
        ws = wb.active
        ws.title = "Flagged Products"
        headers = PRODUCT_DATAPOINTS + ["Validation Errors"]
        ws.append(headers)
        for prod in products:
            key = prod.get("Artikelnummer") or prod.get("Produkt-URL")
            errs = product_errors.get(key)
            if errs:
                row = [prod.get(h, "") for h in PRODUCT_DATAPOINTS]
                row.append("; ".join(errs))
                ws.append(row)
        wb.save(filename)
        logger.info(f"Flagged products exported for review: {filename}")
    except Exception as e:
        logger.error(f"Failed to export flagged products: {e}")

def scan_products(
    products: List[Dict[str, Any]],
    required_fields=None,
    anomaly_field="Pris inkl. moms (värde)",
    anomaly_z=3.5,
    review_export=True,
    export_filename="flagged_products_review.xlsx"
) -> Tuple[List[Dict[str, Any]], Dict[str, List[str]]]:
    
    """
    Validate and filter a list of products, flagging errors and anomalies, and optionally exporting flagged products.

    Args:
        products (list): List of product dicts to scan.
        required_fields (list, optional): Override required fields.
        anomaly_field (str): Numeric field to check for outliers.
        anomaly_z (float): Z-score threshold for anomalies.
        review_export (bool): If True, export flagged products for review.
        export_filename (str): Output Excel filename for flagged products.

    Returns:
        tuple: (filtered_products, product_errors)
            filtered_products: Valid products (list)
            product_errors: Dict of product key -> error list
    """

    product_errors = {}
    filtered = []
    for i, prod in enumerate(products):
        errs = validate_product(prod, required_fields)
        key = prod.get("Artikelnummer") or prod.get("Produkt-URL") or f"idx_{i}"
        if errs:
            product_errors[key] = errs
        else:
            filtered.append(prod)
    outliers = detect_anomalies(products, anomaly_field, z_thresh=anomaly_z)
    for idx, val in outliers:
        key = products[idx].get("Artikelnummer") or products[idx].get("Produkt-URL") or f"idx_{idx}"
        msg = f"{anomaly_field} outlier: {val}"
        product_errors.setdefault(key, []).append(msg)
    log_validation_report(products, product_errors)
    if review_export and product_errors:
        export_flagged_products(products, product_errors, filename=export_filename)
    return filtered, product_errors