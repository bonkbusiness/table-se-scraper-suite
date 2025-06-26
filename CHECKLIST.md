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
