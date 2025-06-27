## 1. Modular Scraper: Core Functionality

### A. Category Extraction

- [x] 1.1 Fully traverse all category levels (main, sub, sub-sub) on table.se  
  _Implemented in `scraper/category.py` as `extract_category_tree()`_
- [x] 1.2 Exclude categories based on exclusions.py logic  
  _Uses `is_excluded()` and `prune_excluded_nodes()`_
- [x] 1.3 Unit tests for category extraction  
  _`tests/test_category.py` covers: full tree, exclusions, edge cases_

### B. Refactoring

- [x] Code modularized: moved and cleaned up to `scraper/category.py`
- [x] All exclusion and recursion logic included
- [x] Interface is clean and predictable

### C. Tests

- [x] Unit tests implemented for all major modules
  - [x] Mocked HTML for category/product
  - [x] Mocked `is_excluded` for exclusions
  - [x] Tests for: all nodes, exclusions, structure, empty/broken categories, deep nesting

### D. Documentation

- [x] Docstrings for all public functions/classes
- [x] Major functions well-commented and self-explanatory
- [x] README.md: project vision, usage, dev guide, changelog

---

## E. Product URL Extraction

- [x] Extract all product URLs from every (sub)category, including pagination
- [x] Avoid duplicates and respect exclusions
- [x] Functions in `scraper/product.py`
- [x] Unit tests in `tests/test_product.py`
- [x] Comprehensive docstrings

---

## Product Data Extraction

- [x] Extract all key fields: name, SKU, prices (incl/excl), materials, colors, sizes, images, etc.
- [x] Caching for previously scraped products
- [x] Handle/log missing or invalid fields gracefully

---

## Backend Parallelization & Robustness

- [x] Scrape categories & products in parallel (threaded, via ThreadPoolExecutor)
- [x] Retry failed requests, throttle as needed (CLI flags)
- [x] Centralized logging for all scraping steps

---

## 2. Exporter: Data Output

### XLSX Export

- [x] Export all products to XLSX (in `exporter/xlsx.py`)
- [x] Auto-create output directories if missing

### CSV Export

- [x] Export all products to CSV (in `exporter/csv.py`)

### Error and QC Reporting

- [x] Deduplicate products (`exporter/qc.py`)
- [x] Check field completeness and create error reports in XLSX
- [x] Optionally, export errors to CSV

### External Export

- [ ] Stub or implementation for external API/data push (`exporter/external.py`)

---

## 3. Orchestration & Main Entrypoint

- [x] Main Workflow (`main.py`):
  - [x] Extracts category tree
  - [x] Extracts all product URLs
  - [x] Scrapes all product data
  - [x] Runs deduplication & QC
  - [x] Exports to XLSX & CSV
  - [x] Exports error reports
  - [x] Logs progress & errors
  - [x] Configurable via CLI or config file (output dir, parallelism, etc)
- [ ] Dependency Injection: orchestrator passes functions/objects between modules, no hard-coded imports

---

## 4. Performance & Robustness

- [x] Retries and Throttling: All HTTP requests use retry/backoff and polite crawling
- [x] Logging: File + console logging, with timestamps and levels
- [ ] Respect rate limits & avoid blocks (planned: rate limiting middleware)
- [ ] Asyncio support for even higher throughput (planned)

---

## 5. Testing & Quality

- [x] Unit tests for all major functions (category, product, exporter, QC)
- [x] Mock HTTP for reproducibility
- [x] End-to-end test run on table.se (shortened scope for dev)
- [ ] Validation: sample manual checks (output matches website, all products/fields covered)
- [ ] CI integration for automated tests

---

## 6. Documentation

- [x] README.md: Project vision, structure, roadmap, usage, dev guide, changelog
- [x] Docstrings: All public functions/classes documented

---

## 7. Extensibility & Configurability

- [x] Exclusions: Easy to update/add exclusion logic
- [x] Export formats: Easy to add new exporters (JSON, XML, API, etc.)
- [ ] Config files: Optional—support for YAML/TOML config for advanced options

---

## 8. Polish, Release & Iterate

- [x] Review, refactor, and optimize codebase
- [x] Tag v1.0 release
- [ ] Plan next iteration (feature requests, new sites, enhancements)
- [ ] Dockerize the scraper for easy deployment

---

## 9. Advanced Features (Planned)

- [ ] Progress bars with tqdm for user feedback
- [ ] Async/streamed scraping (aiohttp)
- [ ] Chunked/streamed output (e.g., JSONL, DB)
- [ ] Logging to external monitoring (Sentry, Slack)
- [ ] Exponential backoff for retries
- [ ] Rate limiting support
- [ ] Incremental scraping/resume support
- [ ] Config file support for CLI defaults
- [ ] Advanced unit/integration tests with mocks
- [ ] External API/data push

---

## Summary

**DONE:**  
- Modularization, category & product extraction, parallelization, caching, robust exclusion logic, QC, deduplication, XLSX/CSV export, CLI, centralized logging, docstrings, most documentation, and developer checklist.

**TO DO (PRIORITY):**  
- External exporter API, advanced config file support, Dockerization, incremental/resume scraping, advanced error handling, rate limiting, progress bars, CI integration, advanced manual validation, and ongoing testing/documentation polish.
