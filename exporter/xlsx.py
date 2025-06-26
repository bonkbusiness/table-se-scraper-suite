"""
exporter/xlsx.py

Exports a list of product dictionaries to an XLSX file (Excel format).
"""

import openpyxl

def export_to_xlsx(products, filename):
    """
    Export a list of product dicts to an XLSX file.

    Args:
        products (list of dict): The product data to export.
        filename (str): Output .xlsx file path.
    """
    if not products:
        print("No products to export.")
        return

    # Collect all unique keys for header
    headers = set()
    for prod in products:
        headers.update(prod.keys())
    headers = sorted(headers)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Products"

    # Write header
    ws.append(headers)

    # Write product rows
    for prod in products:
        row = [prod.get(h, "") for h in headers]
        ws.append(row)

    wb.save(filename)
    print(f"Exported {len(products)} products to {filename}")
