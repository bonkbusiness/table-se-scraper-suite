"""
exporter/csv.py

Exports a list of product dictionaries to a CSV file.
"""

import csv

def export_to_csv(products, filename):
    """
    Export a list of product dicts to a CSV file.

    Args:
        products (list of dict): The product data to export.
        filename (str): Output .csv file path.
    """
    if not products:
        print("No products to export.")
        return

    # Collect all unique keys for header
    headers = set()
    for prod in products:
        headers.update(prod.keys())
    headers = sorted(headers)

    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for prod in products:
            writer.writerow(prod)

    print(f"Exported {len(products)} products to {filename}")
