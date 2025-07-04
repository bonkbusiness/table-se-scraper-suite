# Table.se Scraper Suite

## Overview

A robust, modular Python suite for scraping and exporting product data from [table.se](https://www.table.se). Designed for extensibility, resilience, and maintainability, it supports category and product extraction, parallel scraping, quality control (QC), deduplication, error reporting, and multiple output formats (XLSX, CSV).

---

## Features

- **Product Datapoints:** All modules (scraper, exporters, QC) now use a harmonized, comprehensive set of product fields
- **Modular architecture:** Each workflow (category, product, export, QC) is a dedicated module.
- **Parallel scraping:** Categories and products fetched in parallel, with retries & throttling.
- **Exclusion logic:** Easily skip unwanted categories/products via `exclusions.py`.
- **QC & Deduplication:** Automated completeness checks and duplicate detection.
- **Exporters:** Output to XLSX and CSV with auto-generated filenames.
- **Caching:** Product cache avoids redundant scrapes; supports incremental runs.
- **Configurable:** CLI options for parallelism, retries, output, and more.
- **Extensible:** Add new exporters, scrapers, or QC logic easily.
- **Testing:** Unit tests for core modules; testable with mocks.
- **Documentation:** Docstrings, usage guides, and developer notes.

---

# Changelog

## v1.1 (2025-06-27)

### Harmonization & Refactoring

- **Standardized Product Datapoints:**  
  All modules (scraper/product.py, exporter/xlsx.py, exporter/csv.py, scraper/scanner.py, scraper/utils.py) use a unified, documented set of product fields, ensuring that exports and QC are always in sync with the scraper.
- **Exporter Updates:**  
  Both CSV and XLSX exporters use the full field set, including new fields like `Extra data`, `Beskrivning`, and all measurements (length, width, height, etc.).
- **QC/Validation Improvements:**  
  QC routines now validate presence and formatting of these standardized fields.
- **Extensive Documentation:**  
  All core files now include clear docstrings, usage examples, and documentation for every field exported and processed.
- **README Update:**  
  Full list of product fields and new workflow explanations added for clarity.
- **Developer Notes:**  
  Added guidance to keep field lists in sync across modules.
- **Bugfixes:**  
  - Fixed category key harmonization in scanner and utils.
  - Improved error handling/logging in all pipelines.


### v1.0 (2024-2025)

**Initial Release & Modularization**
- Split legacy monoliths (`table_se_scraper.py`, etc.) into:
    - `scraper/category.py`: Category tree extraction (all levels, exclusions)
    - `scraper/product.py`: Product URL extraction (pagination, exclusions), product data extraction
    - `scraper/utils.py`: All helpers (color, value/unit parsing, filenames, deduplication, etc.)
    - `scraper/backend.py`: Parallel scraping, orchestration, CLI
    - `exporter/xlsx.py`, `csv.py`, `qc.py`: Data output, deduplication, completeness/error reporting
    - `exclusions.py`: Central skip logic
    - `main.py`: CLI entrypoint, config, wiring

**Implemented**
- Parallel scraping with retries, throttling, and central logging
- Full product field extraction (name, SKU, price, sizes, colors, materials, image, etc.)
- Caching for repeated runs; change-detection for products
- QC: duplicate and incomplete product detection
- Automated output file naming
- Exclusion logic for categories/products
- Modular, testable code with docstrings everywhere
- Unit tests for all major modules
- Output: XLSX, CSV, error reports
- Developer checklist and docs

**Planned/Upcoming**
- Async/streamed scraping (aiohttp)
- More exporters (API, DB)
- Progress bars (tqdm)
- Incremental scraping/resume support
- Dockerization
- Config via YAML/ENV
- External monitoring (Sentry, Slack)
- CI/CD pipeline
- Advanced error handling

---

## Quickstart

### 1. Install requirements

```bash
pip install -r requirements.txt
```

### 2. Scrape All Products (Full Pipeline)

```bash
python main.py --max-workers 8 --retries 2 --output products.json
```

Options:
- `--max-workers`: Number of threads (default: 8)
- `--retries`: Retries for failed requests (default: 2)
- `--output`: Output JSON file (default: products_<timestamp>.json)
- `--throttle`: Delay between requests (default: 0.7)
- `--cache`: Enable HTTP requests caching
- `--review-export`: Also export flagged products (Excel)

### 3. Export to XLSX/CSV

After scraping, use:

```bash
python -m exporter.xlsx
python -m exporter.csv
```
Or use the main script, which exports automatically after scraping.

---

## Running in Google Colab

You can run this project in [Google Colab](https://colab.research.google.com/):

### 1. Clone the repository

```python
!git clone https://github.com/bonkbusiness/table-se-scraper-suite.git
%cd table-se-scraper-suite
```

### 2. Install dependencies

```python
!pip install -r requirements.txt
```

If you get errors about missing system libraries (like `libxml2`), run:

```python
!apt-get install -y libxml2-dev libxslt1-dev
```

### 3. Run the scraper

```python
!python main.py --max-workers 4 --retries 2 --output products.json --throttle 1.0
```
You may want to use fewer workers (e.g. `--max-workers 2`) to avoid resource limits in Colab.

### 4. Download your results

```python
from google.colab import files
files.download('products.json')
# Or:
# files.download('export/products.xlsx')
```

### 5. Analyze results in Colab

```python
import pandas as pd
df = pd.read_json('products.json')
df.head()
```

**Tips:**
- Colab may time out or disconnect on long runs; start with smaller test runs.
- For very large scrapes, consider running locally or on a server.
- Always respect table.se's robots.txt and terms of service.

---

## Usage: Common Workflows

### Category Extraction

```python
from scraper.category import extract_category_tree

tree = extract_category_tree()
# tree is a list of dicts:
# { "name": str, "url": str, "color": str, "level": int, "subs": [...] }
```

### Product URL Extraction

```python
from scraper.product import extract_all_product_urls

product_urls = extract_all_product_urls(tree)
```

### Product Data Extraction

```python
from scraper.product import scrape_product

for url in product_urls:
    product = scrape_product(url)
```

### Quality Control & Deduplication

```python
from exporter.qc import deduplicate_products, check_field_completeness

products = deduplicate_products(products)
errors = check_field_completeness(products)
```

### Exporting

```python
from exporter.xlsx import export_to_xlsx
from exporter.csv import export_to_csv

export_to_xlsx(products, "exports/products.xlsx")
export_to_csv(products, "exports/products.csv")
```

---

## Repo Structure

```
scraper/
    category.py        # Category extraction logic
    product.py         # Product URL and data extraction
    utils.py           # All shared helpers/utilities
    backend.py         # Orchestration, parallelization
    cache.py           # Caching layer
    __init__.py
exporter/
    xlsx.py            # XLSX export
    csv.py             # CSV export
    qc.py              # QC, deduplication, completeness
    __init__.py
exclusions.py          # Site-specific exclusion rules
main.py                # Main orchestrator CLI
requirements.txt
tests/                 # Unit tests for all modules
README.md
CHECKLIST.md           # Concrete completion checklist
```

---

## Configuration

- **Exclusions:** Edit `exclusions.py` to update skip rules.
- **Output:** Use CLI flags or `make_output_filename()` to customize output location/format.
- **Parallelism:** Adjust `--max-workers` for performance.
- **Retry/Throttle:** Tune scraping politeness via CLI flags.
- **Custom fields:** Extend product/category extraction with new keys as needed.

---

## Developer How-To

- **Add new helpers:** Only define in `scraper/utils.py`. Import everywhere else.
- **Change category structure:** Update keys in both `category.py` and `product.py` (see below).
- **Add exporters:** Drop a new file in `exporter/` and import it in `main.py`.
- **Write tests:** Place in `tests/`, use mocks for HTTP.

---

## Category Dict Structure (for devs)

All category nodes/dicts use this canonical structure:

```python
{
    "name": str,
    "url": str,
    "color": str,
    "level": int,
    "subs": [ ... ]  # (list of subcategories, same structure recursively)
}
```

This structure is consistent across `category.py`, `product.py`, exporters, and tests.

---

## FAQ

- **Where do I add a new helper?** Only in `scraper/utils.py`.
- **How do I exclude a category/product?** Add skip logic to `exclusions.py`.
- **How do I run tests?** `pytest` or `python -m unittest discover`
- **Where is duplicate detection?** `exporter/qc.py`
- **How do I change the output file/folder?** Use the CLI flags or `make_output_filename()`.

---

## License

MIT (see `LICENSE`).

---

## Credits

- Inspired by real-world e-commerce scraping needs.
- Open to contributions—see [CONTRIBUTING.md] if present, or open a PR!
