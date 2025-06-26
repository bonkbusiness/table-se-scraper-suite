# Table.se Scraper Suite – Concrete Completion Checklist

## 1. Modular Scraper: Core Functionality

# Scraper Category Extraction Checklist

## A. Core Functionality

- [x] **1.1 Fully traverse all category levels (main, sub, sub-sub) on table.se**
    - Implemented in `scraper/category.py` as `extract_category_tree()`, `build_category_node()`
- [x] **1.2 Exclude categories based on exclusions.py logic**
    - Uses `is_excluded()` from `exclusions.py` and `prune_excluded_nodes()`
- [x] **1.3 Unit tests for category extraction**
    - `tests/test_category.py` covers: full tree, exclusions, edge cases

## B. Refactoring

- [x] **Code moved and cleaned up to `scraper/category.py`**
- [x] **All exclusion and recursion logic included**
- [x] **Interface is clean: input/output are minimal and predictable**

## C. Tests

- [x] **Unit tests draft and implemented**
    - Mocked HTML structure
    - Mocked `is_excluded` for exclusions
    - Tests for: all nodes found, exclusions, tree structure, empty/broken categories, deep nesting

## D. Documentation

- [x] **Docstrings for all public functions in `scraper/category.py`**
- [x] **Major functions are self-explanatory with comments where needed**

---

## What’s Next?

- [ ] (Optional) Add tests for 404s/redirects/network errors
- [ ] (Optional) Integrate tests in CI pipeline
- [ ] (Optional) High-level documentation/readme for module usage

---

- [ ] **Product URL Extraction**
  - [ ] Correctly extract all product URLs from every (sub)category, including pagination
  - [ ] Avoid duplicates and respect exclusions

Product URL Extraction — Requirements

    Correctly extract all product URLs
        From every category and subcategory page (recursively)
        Must handle paginated category pages
    Avoid duplicates
        Only unique product URLs in the final list/tree
    Respect exclusions
        Exclude products/categories as defined in exclusions.py (is_excluded)
    Modular, testable, and clean interface
        Functions in e.g. scraper/product_url.py
        Unit tests in tests/test_product_url.py
        Docstrings for all public functions

Action Steps
1. Implement in scraper/product_url.py

    Function to accept a category tree (from previous step)
    For each node:
        Traverse all (sub)categories
        For each category URL:
            Follow pagination (?page=2, etc.)
            Extract all product URLs from each page
            Skip excluded ones
    Build a unique set/list of product URLs

Suggested interface:
Python

def extract_product_urls(category_tree):
    """
    Given a category tree, extract all unique product URLs, handling pagination and exclusions.

    Args:
        category_tree (list): Output from extract_category_tree()

    Returns:
        set: Unique product URLs (as strings)
    """

2. Unit Tests in tests/test_product_url.py

    Mock HTML for paginated category pages (simulate next/prev, “page 2”, etc.)
    Mock is_excluded
    Test:
        All products found (across pages and subcategories)
        Exclusions are respected
        Duplicates are avoided
        Edge cases: empty category, broken HTML, no products, last page, etc.

3. Docstrings and Comments

    Clear docstrings for all public functions

Example Structure
Code

scraper/
  category.py
  product_url.py    # <--- new/updated
tests/
  test_category.py
  test_product_url.py



---

- [ ] **Product Data Extraction**
  - [ ] Extract all key fields: name, SKU, prices (incl/excl), materials, colors, sizes, images, etc.
  - [ ] Caching for previously scraped products
  - [ ] Handle and log missing/invalid fields gracefully

- [ ] **Parallelization & Robustness**
  - [ ] Scrape categories & products in parallel (threaded)
  - [ ] Retry failed requests, throttle as needed
  - [ ] Centralized logging for all scraping steps

---

## 2. Exporter: Data Output

- [ ] **XLSX Export**
  - [ ] Export all products to XLSX (in `exporter/xlsx.py`)
  - [ ] Auto-create output directories if missing

- [ ] **CSV Export**
  - [ ] Export all products to CSV (in `exporter/csv.py`)

- [ ] **Error and QC Reporting**
  - [ ] Deduplicate products (`exporter/qc.py`)
  - [ ] Check field completeness and create error reports in XLSX
  - [ ] Optionally, export errors to CSV

- [ ] **External Export**
  - [ ] Stub or implementation for external API/data push (`exporter/external.py`)

---

## 3. Orchestration & Main Entrypoint

- [ ] **Main Workflow**
  - [ ] End-to-end script (`main.py`) that:
    - [ ] Extracts category tree
    - [ ] Extracts all product URLs
    - [ ] Scrapes all product data
    - [ ] Runs deduplication & QC
    - [ ] Exports to XLSX & CSV
    - [ ] Exports error reports
    - [ ] Logs progress & errors
  - [ ] Configurable via CLI or config file (output dir, parallelism, etc)

- [ ] **Dependency Injection**
  - [ ] Orchestrator passes functions/objects between modules, no hard-coded imports

---

## 4. Performance & Robustness

- [ ] **Retries and Throttling**
  - [ ] All HTTP requests use retry/backoff and polite crawling
  - [ ] Respect rate limits & avoid blocks

- [ ] **Logging**
  - [ ] File + console logging, with timestamps and levels

---

## 5. Testing & Quality

- [ ] **Unit Tests**
  - [ ] For all major functions (category, product, exporter, QC)
  - [ ] Mock HTTP for reproducibility

- [ ] **End-to-End Test**
  - [ ] Test run on table.se (shortened scope for dev)

- [ ] **Validation**
  - [ ] Sample manual checks: output matches website, all products/fields covered

---

## 6. Documentation

- [ ] **README.md**
  - [x] Project vision, structure, and roadmap (see above)
  - [ ] Usage instructions (running, config, output)
  - [ ] Developer/contributor guide

- [ ] **Docstrings**
  - [ ] All public functions/classes are documented

---

## 7. Extensibility & Configurability

- [ ] **Exclusions**
  - [ ] Easy to update/add exclusion logic

- [ ] **Export Formats**
  - [ ] Easy to add new exporters (JSON, XML, API, etc.)

- [ ] **Config Files**
  - [ ] Optional: support for YAML/TOML config for advanced options

---

## 8. Polish, Release & Iterate

- [ ] Review, refactor, and optimize codebase
- [ ] Tag v1.0 release
- [ ] Plan next iteration (feature requests, new sites, enhancements)

---
