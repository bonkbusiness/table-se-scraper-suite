"""
exporter/xlsx.py

Exports product dictionaries to XLSX (Excel), with support for Table.se's product field set,
parent/subcategory columns, and QC pipeline integration.

Features:
- Exports a list of product dicts to an XLSX file, sorted by a configurable key ("Namn" by default).
- Uses a fixed column order for consistency with Table.se exports.
- Includes "Kategori (parent)" and "Kategori (sub)" columns for parent and subcategory information.
- Uses logging for status and error messages (integrates with scraper.logging).
- Can be used directly for exporting already quality-controlled data, or via the QC pipeline entrypoint.
- Compatible with the man-in-the-middle QC logic in exporter/qc.py.

API:
- export_to_xlsx(data, filename, sort_key="Namn")
    Exports the given list of dicts to an XLSX file.
    Returns the filename on success, or None on error.

- export_products_with_qc(products, filename, error_filename=None)
    Orchestrates deduplication and completeness-checking (via exporter.qc), then exports only valid products to XLSX.
    Optionally exports products with missing fields to a separate XLSX.
    Returns the filename of the main XLSX on success, or None on error.

Typical usage:
    from exporter.xlsx import export_products_with_qc
    export_products_with_qc(products, "output.xlsx", error_filename="errors.xlsx")
"""

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import os
from scraper.logging import get_logger

logger = get_logger("xlsx-export")

def export_to_xlsx(data, filename, sort_key="Namn"):
    """
    Export a list of product dicts to XLSX, sorted by sort_key.
    Each product dict may include 'Kategori (parent)' and 'Kategori (sub)' fields for parent and subcategories.
    Returns the filename or None on error.

    Args:
        data: List[Dict[str, Any]] -- List of product dictionaries.
        filename: str -- Path to output XLSX file.
        sort_key: str -- Which field to sort products by (default "Namn").

    Returns:
        str or None
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
        logger.warning("Ingen data att exportera till XLSX.")
        return None
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        data_sorted = sorted(data, key=lambda x: x.get(sort_key, "").lower())
        wb = Workbook()
        ws = wb.active
        ws.title = "Produkter"
        # Header row
        for col_num, col in enumerate(COLUMN_ORDER, 1):
            cell = ws.cell(row=1, column=col_num, value=col)
            cell.font = Font(bold=True, color="FFFFFFFF")
            cell.fill = PatternFill("solid", fgColor="FF212121")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(bottom=Side(style="medium", color="FFB0BEC5"))
        # Data rows
        for row_num, row in enumerate(data_sorted, 2):
            for col_num, col in enumerate(COLUMN_ORDER, 1):
                ws.cell(row=row_num, column=col_num, value=row.get(col, ""))
        # Autosize columns
        for col_num, col in enumerate(COLUMN_ORDER, 1):
            ws.column_dimensions[get_column_letter(col_num)].width = max(12, len(col) + 2)
        wb.save(filename)
        logger.info(f"Export till XLSX klar: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Fel vid sparande av XLSX: {e}")
        return None

def export_products_with_qc(products, filename, error_filename=None):
    """
    Main entrypoint for the QC pipeline: deduplicate, check completeness, and export to XLSX.
    Optionally export products with missing fields to a separate XLSX file.

    Args:
        products: List[Dict[str, Any]] -- Raw product list (may be unfiltered).
        filename: str -- Main output XLSX file.
        error_filename: str or None -- Optional error output XLSX file.

    Returns:
        str or None -- The filename of the main XLSX export, or None on error.
    """
    from exporter.qc import deduplicate_products, check_field_completeness, export_errors_to_xlsx

    deduped = deduplicate_products(products)
    incomplete = check_field_completeness(deduped)
    valid = [p for p in deduped if p not in incomplete]
    exported = export_to_xlsx(valid, filename)
    logger.info(f"QC-pipeline: Exporterade {len(valid)} produkter till {filename}")
    if error_filename and incomplete:
        export_errors_to_xlsx(
            [{"error_type": "missing_fields", "product": p} for p in incomplete],
            error_filename
        )
        logger.info(f"QC-pipeline: Exporterade {len(incomplete)} felaktiga produkter till {error_filename}")
    return exported
