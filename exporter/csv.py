"""
exporter/csv.py

Exports product dictionaries to CSV, with support for Table.se's full product field set and QC pipeline integration.

Features:
- Exports a list of product dicts to a CSV file, sorted by a configurable key ("Namn" by default).
- Uses a fixed column order for consistency with other Table.se exports.
- Includes "Kategori (parent)" and "Kategori (sub)" columns for parent and subcategory information.
- Logging is used for all status and error messages.
- Can be used directly for exporting already quality-controlled data, or via the QC pipeline entrypoint.
- Compatible with the man-in-the-middle QC logic in exporter/qc.py.

Datapoints/columns exported (see scraper/product.py extraction):
    - Namn
    - Artikelnummer
    - Färg
    - Material
    - Serie
    - Pris exkl. moms (värde)
    - Pris exkl. moms (enhet)
    - Pris inkl. moms (värde)
    - Pris inkl. moms (enhet)
    - Längd (värde)
    - Längd (enhet)
    - Bredd (värde)
    - Bredd (enhet)
    - Höjd (värde)
    - Höjd (enhet)
    - Djup (värde)
    - Djup (enhet)
    - Diameter (värde)
    - Diameter (enhet)
    - Kapacitet (värde)
    - Kapacitet (enhet)
    - Volym (värde)
    - Volym (enhet)
    - Vikt (värde)
    - Vikt (enhet)
    - Data (text)
    - Kategori (parent)
    - Kategori (sub)
    - Produktbild-URL
    - Produkt-URL
    - Beskrivning
    - Extra data

API:
- export_to_csv(data, filename, sort_key="Namn")
    Exports the given list of dicts to a CSV file.
    Returns the filename on success, or None on error.

- export_products_with_qc(products, filename, error_filename=None)
    Orchestrates deduplication and completeness-checking (via exporter.qc), then exports only valid products to CSV.
    Optionally exports products with missing fields to a separate CSV.
    Returns the filename of the main CSV on success, or None on error.

Typical usage:
    from exporter.csv import export_products_with_qc
    export_products_with_qc(products, "output.csv", error_filename="errors.csv")

"""

import csv
import os
from scraper.logging import get_logger

logger = get_logger("csv-export")

PRODUCT_COLUMN_ORDER = [
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

def export_to_csv(data, filename, sort_key="Namn"):
    """
    Export a list of product dicts to CSV, sorted by sort_key.
    Each product dict may include all fields listed in PRODUCT_COLUMN_ORDER.
    Returns the filename or None on error.
    """
    if not data:
        logger.warning("Ingen data att exportera till CSV.")
        return None
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        data_sorted = sorted(data, key=lambda x: x.get(sort_key, "").lower())
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=PRODUCT_COLUMN_ORDER)
            writer.writeheader()
            for row in data_sorted:
                writer.writerow({col: row.get(col, "") for col in PRODUCT_COLUMN_ORDER})
        logger.info(f"Export till CSV klar: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Fel vid CSV-export: {e}")
        return None

def export_products_with_qc(products, filename, error_filename=None):
    """
    Main entrypoint for the QC pipeline: deduplicate, check completeness, and export to CSV.
    Optionally export products with missing fields to a separate CSV file.

    Args:
        products: List[Dict[str, Any]] -- Raw product list (may be unfiltered).
        filename: str -- Main output CSV file.
        error_filename: str or None -- Optional error output CSV file.

    Returns:
        str or None -- The filename of the main CSV export, or None on error.
    """
    from exporter.qc import deduplicate_products, check_field_completeness, export_errors_to_csv

    deduped = deduplicate_products(products)
    incomplete = check_field_completeness(deduped)
    valid = [p for p in deduped if p not in incomplete]
    exported = export_to_csv(valid, filename)
    logger.info(f"QC-pipeline: Exporterade {len(valid)} produkter till {filename}")
    if error_filename and incomplete:
        export_errors_to_csv(
            [{"error_type": "missing_fields", "product": p} for p in incomplete],
            error_filename
        )
        logger.info(f"QC-pipeline: Exporterade {len(incomplete)} felaktiga produkter till {error_filename}")
    return exported