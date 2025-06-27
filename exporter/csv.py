import csv
import os
from scraper.logging import get_logger

logger = get_logger("csv-export")

def export_to_csv(data, filename, sort_key="Namn"):
    """
    Export a list of product dicts to CSV, sorted by sort_key.
    Each product dict may include 'Kategori (parent)' and 'Kategori (sub)' fields for parent and subcategories.
    Returns the filename or None on error.
    """
    COLUMN_ORDER = [
        "Namn",
        "Artikelnummer",
        "Färg",
        "Material",
        "Serie",
        "Pris exkl. moms (värde)",
        "Pris exkl. moms (enhet)",
        "Pris inkl. moms (värde)",
        "Pris inkl. moms (enhet)",
        "Mått (text)",
        "Längd (värde)", "Längd (enhet)",
        "Bredd (värde)", "Bredd (enhet)",
        "Höjd (värde)", "Höjd (enhet)",
        "Djup (värde)", "Djup (enhet)",
        "Diameter (värde)", "Diameter (enhet)",
        "Kapacitet (värde)", "Kapacitet (enhet)",
        "Volym (värde)", "Volym (enhet)",
        "Kategori (parent)",
        "Kategori (sub)",
        "Produktbild-URL",
        "Produkt-URL"
    ]
    if not data:
        logger.warning("Ingen data att exportera till CSV.")
        return None
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        data_sorted = sorted(data, key=lambda x: x.get(sort_key, "").lower())
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMN_ORDER)
            writer.writeheader()
            for row in data_sorted:
                writer.writerow({col: row.get(col, "") for col in COLUMN_ORDER})
        logger.info(f"Export till CSV klar: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Fel vid CSV-export: {e}")
        return None

def export_products_with_qc(products, filename, error_filename=None):
    """
    Main entrypoint for QC pipeline: deduplicate, check completeness, and export to CSV.
    Optionally export errors to a separate CSV file.
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
