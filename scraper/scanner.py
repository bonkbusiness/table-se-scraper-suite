"""
scanner.py

A smart scanner/validator module to assist and enhance the accuracy of your Table.se scraper.
Keeps your original scraper untouched. Plug in after scraping or per product.

Implements:
1. Content Validation (field checks, type checks, value logic)
3. Selector Robustness (fallbacks, auto-detection)
4. Anomaly Detection (simple stat outlier checks)
5. Logging and Reporting (flagged items, summary)
6. Human-in-the-loop (flagged products to separate report for review)
"""

import re
import logging
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger("smart_scanner")
logger.setLevel(logging.INFO)

# ========== 1. Content Validation ==========

def validate_product(product: Dict[str, Any], required_fields=None) -> List[str]:
    """
    Returns list of validation errors for a product dict.
    - Checks for required fields and plausible values.
    """
    if not required_fields:
        required_fields = ["Namn", "Artikelnummer", "Pris inkl. moms (värde)", "Produkt-URL"]
    errors = []
    for field in required_fields:
        if not product.get(field):
            errors.append(f"Missing: {field}")
    # Price checks
    try:
        price = float(product.get("Pris inkl. moms (värde)", "0").replace(",", "."))
        if price <= 0:
            errors.append("Price must be positive")
    except Exception:
        errors.append("Price is not a number")
    # SKU pattern
    sku = product.get("Artikelnummer", "")
    if sku and not re.match(r"^[A-Za-z0-9\- ]+$", sku):
        errors.append("Artikelnummer (SKU) may have invalid characters")
    # Image URL
    img = product.get("Produktbild-URL", "")
    if not img or img.strip() == "" or img.endswith("placeholder.png"):
        errors.append("Missing or placeholder product image")
    # Category
    if not product.get("Category") and not product.get("category"):
        errors.append("Missing category")
    # Optionally add more checks
    return errors

# ========== 3. Selector Robustness ==========

def robust_select_one(soup, selectors: List[str]) -> Optional[str]:
    """
    Try a list of selectors, return the first non-empty result as text.
    """
    for sel in selectors:
        elem = soup.select_one(sel)
        if elem:
            text = elem.get_text(strip=True)
            if text:
                return text
    return None

def robust_select_attr(soup, selectors: List[str], attr: str) -> Optional[str]:
    """
    Try a list of selectors, return the first non-empty result as an attribute.
    """
    for sel in selectors:
        elem = soup.select_one(sel)
        if elem and elem.has_attr(attr):
            val = elem.get(attr, "").strip()
            if val:
                return val
    return None

# ========== 4. Anomaly Detection ==========

def detect_anomalies(products: List[Dict[str, Any]], field: str, z_thresh: float = 3.5) -> List[Tuple[int, Any]]:
    """
    Returns list of (index, value) for products with field value as a strong outlier.
    Uses modified Z-score method.
    """
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
    import numpy as np
    median = np.median(values)
    diff = np.abs(values - median)
    mad = np.median(diff)
    if mad == 0:
        return []
    modified_z = 0.6745 * (values - median) / mad
    outliers = [(idx_map[i], values[i]) for i in range(len(values)) if abs(modified_z[i]) > z_thresh]
    return outliers

# ========== 5. Logging and Reporting ==========

def log_validation_report(products: List[Dict[str, Any]], product_errors: List[List[str]]):
    """
    Logs a summary report of validation errors.
    """
    total = len(products)
    flagged = sum(1 for errs in product_errors if errs)
    logger.info(f"Validation Summary: {flagged}/{total} products flagged with issues.")
    if flagged > 0:
        logger.info("First 5 flagged examples:")
        count = 0
        for idx, errs in enumerate(product_errors):
            if errs:
                logger.info(f"Product {idx+1} ({products[idx].get('Produkt-URL')}): {errs}")
                count += 1
                if count >= 5:
                    break

def export_flagged_products(products: List[Dict[str, Any]], product_errors: List[List[str]], filename: str = "flagged_products_review.xlsx"):
    """
    Exports flagged products with their errors to a separate Excel file for human review.
    """
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Flagged Products"
        # Compose headers
        headers = list(products[0].keys()) + ["Validation Errors"]
        ws.append(headers)
        for prod, errs in zip(products, product_errors):
            if errs:
                row = [prod.get(h, "") for h in headers[:-1]]
                row.append("; ".join(errs))
                ws.append(row)
        wb.save(filename)
        logger.info(f"Flagged products exported for review: {filename}")
    except Exception as e:
        logger.error(f"Failed to export flagged products: {e}")

# ========== 6. Human-in-the-loop Integration ==========

def scan_products(products: List[Dict[str, Any]], required_fields=None, anomaly_field="Pris inkl. moms (värde)", anomaly_z=3.5, review_export=True) -> Tuple[List[Dict[str, Any]], List[List[str]]]:
    """
    Runs full smart scan:
    - Validates each product
    - Detects price anomalies
    - Logs a summary
    - Optionally exports flagged products for human review

    Returns the (products, product_errors) tuple.
    """
    product_errors = []
    for prod in products:
        errs = validate_product(prod, required_fields)
        product_errors.append(errs)
    # Anomaly detection
    outliers = detect_anomalies(products, anomaly_field, z_thresh=anomaly_z)
    for idx, val in outliers:
        product_errors[idx].append(f"{anomaly_field} outlier: {val}")
    log_validation_report(products, product_errors)
    # Optionally export flagged products
    if review_export and any(product_errors):
        export_flagged_products(products, product_errors)
    return products, product_errors
