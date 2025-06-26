# Table.se Scraper Suite

A modular, high-performance, and extensible web scraper and exporter for [table.se](https://www.table.se/).  
Designed for reliability, maintainability, and easy integration with further tools or external systems.

---

## Project Vision & Progress

### 1. What We Have So Far

**A. Legacy State**
- Monolithic scripts (`table_se_scraper.py`, `table_se_scraper_backend_enhanced.py`, `table_se_scraper_performance.py`)
- All logic (scraping, parsing, exporting, logging, etc.) mixed together
- Some parallelization, caching, robust error handling
- Output: XLSX, CSV, and error reporting
- Smart scanning for product validation

**B. Modularization Progress**
- **Scraper modules:**  
  - `scraper/category.py` (category tree extraction)
  - `scraper/product.py` (product data, product URL extraction)
  - `scraper/backend.py` (orchestration, parallelization)
  - `scraper/utils.py` (helpers, parsing, logging, cache)
- **Exporter modules:**  
  - `exporter/xlsx.py` (XLSX export)
  - `exporter/csv.py` (CSV export)
  - `exporter/qc.py` (QC, deduplication, completeness)
  - `exporter/external.py` (API, integrations)
- **Exclusion logic:**  
  - `exclusions.py` (site-specific skip rules)
- **Caching:**  
  - `scraper/cache.py` (product cache for re-scrapes)
- **Performance:**  
  - Robust requests, retries, thread pools, logging

**C. What’s Good:**
- Well-separated modules
- Parallel scraping
- Site-specific selectors and parsing
- Quality control (QC) and error export
- Designed for extensibility

---

### 2. What We Need To Do

**A. Ensure Complete Workflow**
- **Entrypoint:** Main script (`main.py` or `cli.py`) that wires all modules
- **Category-tree to products:** Confirm full traversal (all levels, all products, no duplicates)
- **Full data coverage:** All product fields (name, price, SKU, sizes, images, etc.)
- **Export:** XLSX & CSV, re-usable for any output location
- **Error & QC:** Full product validation, error reporting
- **External APIs:** Optionally, push/export to other platforms

**B. Robustness & Polish**
- **Retry, throttle, politeness:** Don’t get rate-limited or blocked
- **Logging:** Centralized and clear, for debugging and auditing
- **Configurable:** Easy to add new exclusion rules, targets, export formats
- **Testing:** Add test cases for each module (unit/integration)

**C. Documentation**
- **README:** Usage, architecture, developer docs
- **Docstrings:** For all public functions and modules

---

### 3. How We Tie It All Together

**A. Main Orchestrator**
- A main script (e.g., `main.py`) that:
    1. Loads configuration (output paths, exclusions, etc)
    2. Calls category extraction
    3. Calls product URL extraction (in parallel)
    4. Calls product data extraction (in parallel, with cache)
    5. Runs QC and deduplication
    6. Exports results via chosen exporters
    7. Handles errors, writes logs, outputs error reports

**B. Dependency Injection**
- The orchestrator passes functions/objects between modules (not hard-coding dependencies)

**C. Extensibility**
- Easy to add new scrapers, exporters, QC checks, or site integrations
- Modular config (YAML/TOML/ENV/args) for output, target, and performance tuning

---

### 4. Improve, Reiterate, Implement, Analyze

**A. Iterative Process**
- **Step 1:** Build/verify minimal end-to-end flow (from scrape to export)
- **Step 2:** Add full error handling, logging, and config
- **Step 3:** Profile performance; parallelize or optimize as needed
- **Step 4:** Run real-world test: scrape full table.se, check for completeness, QC, output
- **Step 5:** Tweak selectors, handle edge cases, improve resilience
- **Step 6:** Document, refactor, test
- **Step 7:** Repeat until “bulletproof”

---

## Example: Main Orchestrator Skeleton

```python
from scraper.backend import scrape_all_products_parallel
from exporter.xlsx import export_to_xlsx
from exporter.csv import export_to_csv
from exporter.qc import deduplicate_products, check_field_completeness, export_errors_to_xlsx

def main():
    # Scrape
    products = scrape_all_products_parallel()
    # QC
    products = deduplicate_products(products)
    errors = check_field_completeness(products)
    # Export
    export_to_xlsx(products, "exports/table_products.xlsx")
    export_to_csv(products, "exports/table_products.csv")
    if errors:
        export_errors_to_xlsx(errors, "exports/table_errors.xlsx")
    print("Done.")

if __name__ == "__main__":
    main()
```

---

## Next Steps

- [ ] Concrete checklist for completion, testing, and polish (TBD below)
- [ ] Usage instructions
- [ ] Developer documentation

---
