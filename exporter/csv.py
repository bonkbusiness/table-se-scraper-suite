import csv
import os

def export_to_csv(data, filename, sort_key="Namn"):
    """
    Export a list of product dicts to CSV, sorted by sort_key.
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
        print("Ingen data att exportera till CSV.")
        return None
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        data_sorted = sorted(data, key=lambda x: x.get(sort_key, "").lower())
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMN_ORDER)
            writer.writeheader()
            for row in data_sorted:
                writer.writerow({col: row.get(col, "") for col in COLUMN_ORDER})
        print(f"Backup export till CSV klar: {filename}")
        return filename
    except Exception as e:
        print(f"Fel vid backup-CSV-export: {e}")
        return None
