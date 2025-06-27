"""
main.py

Main entry point for the Table.se Scraper Suite.

This script orchestrates the scraping workflow:
    - Builds the category tree from the Table.se homepage navigation.
    - Extracts all unique product URLs from the category tree.
    - Scrapes detailed product data for each product URL.
    - Performs quality control (QC) to check for completeness and duplicates.
    - Exports the cleaned data to XLSX and CSV formats.
    - Optionally, exports incomplete and duplicate records for manual review.

USAGE:
    python main.py

DEPENDENCIES:
    - scraper.category: for category tree extraction.
    - scraper.product: for product URL extraction.
    - scraper.backend: for parallelized product scraping.
    - exporter.xlsx, exporter.csv: for exporting results.
    - exporter.qc: for QC utilities.
    - scraper.utils: for output file naming.
    - scraper.logging: for logging and diagnostics.

NOTES:
    - Logging is initialized as the very first step for robust diagnostics.
    - File naming for exports is standardized via make_output_filename.
    - Handles exceptions at all critical steps and logs errors for traceability.
    - Designed for extensibility and maintainability.

Author: bonkbusiness
License: MIT
"""

import logging
from scraper.logging import LoggerFactory
from scraper.category import extract_category_tree
from scraper.product import extract_all_product_urls
from scraper.backend import scrape_products
from scraper.utils import make_output_filename
from exporter.xlsx import export_to_xlsx
from exporter.csv import export_to_csv
from exporter.qc import check_field_completeness, find_duplicate_products

def run_scraper_pipeline():
    """
    Complete scraping, QC, and export pipeline for Table.se products.
    """
    # 1. Initialize logging early to capture all diagnostics
    LoggerFactory.setup(prefix="scrape", to_stdout=True, log_level=logging.INFO)
    logger = LoggerFactory.get_logger("main")
    logger.info("=== Starting Table.se Scraper Suite ===")

    # 2. Extract the category tree (site navigation)
    try:
        category_tree = extract_category_tree()
        logger.info("Extracted category tree successfully.")
    except Exception as e:
        logger.exception(f"Failed to extract category tree: {e}")
        return

    # 3. Gather all unique product URLs from the category tree
    try:
        product_urls = extract_all_product_urls(category_tree)
        logger.info(f"Found {len(product_urls)} unique product URLs.")
    except Exception as e:
        logger.exception(f"Failed to extract product URLs: {e}")
        return

    # 4. Scrape product details from all URLs
    try:
        products = scrape_products(product_urls)
        logger.info(f"Scraped {len(products)} products.")
    except Exception as e:
        logger.exception(f"Failed to scrape product details: {e}")
        return

    # 5. Quality control: check completeness and find duplicates
    incomplete = check_field_completeness(products)
    duplicates = find_duplicate_products(products)
    logger.info(f"QC Results - Total: {len(products)}, Incomplete: {len(incomplete)}, Duplicates: {len(duplicates)}")

    # 6. Export clean products to XLSX and CSV
    xlsx_path = make_output_filename('products', 'xlsx', 'exports')
    csv_path = make_output_filename('products', 'csv', 'exports')
    export_to_xlsx(products, xlsx_path)
    export_to_csv(products, csv_path)
    logger.info(f"Exported products to: {xlsx_path} and {csv_path}")

    # 7. Optionally export incomplete and duplicate records for review
    if incomplete:
        incomplete_csv = make_output_filename('products_incomplete', 'csv', 'exports')
        export_to_csv(incomplete, incomplete_csv)
        logger.info(f"Exported incomplete products: {incomplete_csv} ({len(incomplete)} records)")

    if duplicates:
        flat_duplicates = [item for _, group in duplicates for item in group]
        duplicates_csv = make_output_filename('products_duplicates', 'csv', 'exports')
        export_to_csv(flat_duplicates, duplicates_csv)
        logger.info(f"Exported duplicate products: {duplicates_csv} ({len(flat_duplicates)} records)")

    logger.info("=== Scraper pipeline completed successfully ===")

if __name__ == "__main__":
    run_scraper_pipeline()