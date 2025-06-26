from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import os

def export_to_xlsx(data, filename, sort_key="Namn"):
    """
    Export a list of product dicts to XLSX, sorted by sort_key.
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
        "Produktbild-URL",
        "Produkt-URL"
    ]
    if not data:
        print("Ingen data att exportera till XLSX.")
        return None
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        data_sorted = sorted(data, key=lambda x: x.get(sort_key, "").lower())
        wb = Workbook()
        ws = wb.active
        ws.title = "Produkter"
        for col_num, col in enumerate(COLUMN_ORDER, 1):
            cell = ws.cell(row=1, column=col_num, value=col)
            cell.font = Font(bold=True, color="FFFFFFFF")
            cell.fill = PatternFill("solid", fgColor="FF212121")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(bottom=Side(style="medium", color="FFB0BEC5"))
        for row_num, row in enumerate(data_sorted, 2):
            for col_num, col in enumerate(COLUMN_ORDER, 1):
                ws.cell(row=row_num, column=col_num, value=row.get(col, ""))
        for col_num, col in enumerate(COLUMN_ORDER, 1):
            ws.column_dimensions[get_column_letter(col_num)].width = max(12, len(col) + 2)
        wb.save(filename)
        print(f"Export till XLSX klar: {filename}")
        return filename
    except Exception as e:
        print(f"Fel vid sparande av XLSX: {e}")
        return None
