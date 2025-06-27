"""
main.py

Main entry point for the Table.se Scraper Suite.
Builds the category tree, scrapes product data, runs QC, and exports results.
"""
import logging
from scraper.logging import LoggerFactory
from scraper.category import extract_category_tree
from scraper.product import extract_all_product_urls
from scraper.backend import scrape_products  # <-- FIX: import the plural function
from scraper.utils import make_output_filename
from exporter.xlsx import export_to_xlsx
from exporter.csv import export_to_csv
from exporter.qc import check_field_completeness, find_duplicate_products

def main():
    # Set up logging as FIRST operation
    LoggerFactory.setup(prefix="scrape", to_stdout=True, log_level=logging.INFO)
    logger = LoggerFactory.get_logger(__name__)

    logger.info("Starting Table.se Scraper Suite...")

    # Build the category tree first
    category_tree = extract_category_tree()
    logger.info("Extracted category tree.")

    # Gather all product URLs using the category tree
    product_urls = extract_all_product_urls(category_tree)
    logger.info(f"Extracted {len(product_urls)} product URLs.")

    # Scrape products (pass all URLs to the plural scrape_products function)
    products = scrape_products(product_urls)
    logger.info(f"Scraped {len(products)} products.")

    # Quality control: completeness and duplicates
    incomplete = check_field_completeness(products)
    duplicates = find_duplicate_products(products)

    logger.info(f"Total products: {len(products)}")
    logger.info(f"Incomplete products: {len(incomplete)}")
    logger.info(f"Duplicate products: {len(duplicates)}")

    # Export results using the standardized file naming convention
    export_to_xlsx(products, make_output_filename('products', 'xlsx', 'exports'))
    export_to_csv(products, make_output_filename('products', 'csv', 'exports'))

    # Optionally, export incomplete/duplicate lists for review
    if incomplete:
        export_to_csv(incomplete, make_output_filename('products_incomplete', 'csv', 'exports'))
        logger.info(f"Exported incomplete products ({len(incomplete)} items).")
    if duplicates:
        # Flatten duplicates for CSV export
        flat_dupes = [p for _, group in duplicates for p in group]
        export_to_csv(flat_dupes, make_output_filename('products_duplicates', 'csv', 'exports'))
        logger.info(f"Exported duplicates ({len(flat_dupes)} items).")

if __name__ == "__main__":
    main()