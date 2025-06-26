"""
main.py

Main entry point for the Table.se Scraper Suite.
Builds the category tree, scrapes product data, runs QC, and exports results.
"""

from scraper.backend import scrape_all_products
from exporter.xlsx import export_to_xlsx
from exporter.csv import export_to_csv
from exporter.qc import check_field_completeness, find_duplicate_products

def main():
    # Scrape all products (full pipeline: category, product, deduplication)
    products = scrape_all_products()

    # Quality control: completeness and duplicates
    incomplete = check_field_completeness(products)
    duplicates = find_duplicate_products(products)

    print(f"Total products: {len(products)}")
    print(f"Incomplete products: {len(incomplete)}")
    print(f"Duplicate products: {len(duplicates)}")

    # Export results
    export_to_xlsx(products, "products.xlsx")
    export_to_csv(products, "products.csv")

    # Optionally, export incomplete/duplicate lists for review
    if incomplete:
        export_to_csv(incomplete, "products_incomplete.csv")
    if duplicates:
        # Flatten duplicates for CSV export
        flat_dupes = [p for _, group in duplicates for p in group]
        export_to_csv(flat_dupes, "products_duplicates.csv")

if __name__ == "__main__":
    main()
