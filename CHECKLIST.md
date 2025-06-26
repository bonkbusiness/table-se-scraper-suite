# Table.se Scraper Suite – Concrete Completion Checklist

## 1. Modular Scraper: Core Functionality

### A. Category Extraction

- [x] 1.1 Fully traverse all category levels (main, sub, sub-sub) on table.se  
  _Implemented in `scraper/category.py` as `extract_category_tree()`, `build_category_node()`_
- [x] 1.2 Exclude categories based on exclusions.py logic  
  _Uses `is_excluded()` from exclusions.py and `prune_excluded_nodes()`_
- [x] 1.3 Unit tests for category extraction  
  _`tests/test_category.py` covers: full tree, exclusions, edge cases_

### B. Refactoring

- [x] Code moved and cleaned up to `scraper/category.py`
- [x] All exclusion and recursion logic included
- [x] Interface is clean: input/output are minimal and predictable

### C. Tests

- [x] Unit tests draft and implemented
  - [x] Mocked HTML structure
  - [x] Mocked `is_excluded` for exclusions
  - [x] Tests for: all nodes found, exclusions, tree structure, empty/broken categories, deep nesting

### D. Documentation

- [x] Docstrings for all public functions in `scraper/category.py`
- [x] Major functions are self-explanatory with comments where needed

## E. Product URL Extraction

- [x] Extract all product URLs from every (sub)category, including pagination
  - [x] Traverse all category and subcategory pages
  - [x] Handle paginated category pages (`?page=2`, etc.)
- [x] Avoid duplicates and respect exclusions
  - [x] Only unique product URLs in the final result
  - [x] Exclude products/categories via `is_excluded()`
- [x] Modular, testable, and clean interface
  - [x] Functions in `scraper/product.py`
  - [x] Unit tests in `tests/test_product.py`
  - [x] Comprehensive docstrings

---

## Next Steps

- [x] Implement `extract_product_urls()` in `scraper/product.py` (covered by `extract_all_product_urls`)
- [x] Draft and implement tests in `tests/test_product.py`
- [x] Add docstrings & comments to all new functions
- [ ] (Optional) Add tests for 404s/redirects/network errors
- [ ] (Optional) Integrate tests in CI pipeline
- [ ] (Optional) High-level documentation/readme for module usage

---

## Product Data Extraction (Future/Planned)

- [x] Extract all key fields: name, SKU, prices (incl/excl), materials, colors, sizes, images, etc.
- [x] Caching for previously scraped products
- [x] Handle and log missing/invalid fields gracefully

---

### Backend Parallelization & Robustness

- [ ] Scrape categories & products in parallel (threaded)
- [ ] Retry failed requests, throttle as needed
- [ ] Centralized logging for all scraping steps

1. Advanced Error Handling / Monitoring

    Better Exception Types: Distinguish between network errors, parsing errors, and exclusion failures for granular logging and smarter retries.
    Alerting: Integrate with tools like Sentry, Slack, or email to notify you of repeated failures or critical issues.
    Timeouts: Ensure all network requests have timeouts to avoid stuck threads.
    Backoff: Use exponential backoff for retries to avoid hammering the site.

2. Performance & Scalability

    Asyncio: For I/O-bound scraping, consider asyncio + aiohttp for even higher throughput.
    Multiprocessing: For CPU-bound parsing (rare but possible), support for multiprocessing pools.
    Rate Limiting: Throttle requests to avoid getting blocked/banned by the target site.

3. Data Pipeline & Output

    Streaming Results: Write products incrementally to output (e.g., JSONL or a database) instead of holding all in memory, for huge catalogs.
    Resume Support: Save progress so interrupted runs can resume where they left off.
    Data Validation: Add schema validation for your product dicts before writing.
    Output to DB: Support for writing to SQLite, Postgres, or other DBs for larger-scale use.

4. CLI & User Experience

    Progress Bars: Use tqdm for live progress bars on URL and product scraping.
    Verbose/Quiet Modes: Add CLI switches for controlling logging verbosity.
    Dry Run: Option to just collect URLs or categories, without scraping products.
    Customizable Fields: Allow user to choose which fields to extract or output.

5. Testability & Maintainability

    Unit and Integration Tests: Mock network calls for fast, reliable tests.
    Dependency Injection: Allow for easier mocking/injecting of fetch/scrape functions.
    Coverage Checking: Ensure high code/test coverage.

6. Documentation & DevOps

    README: Usage, CLI options, troubleshooting, extending.
    CI/CD: Automated tests on push/PR.
    Dockerization: Dockerfile for reproducible environments.
    Config Files: Allow config via YAML/JSON/env, not just CLI.

7. Advanced Scraping Features

    Captcha/Anti-bot Handling: Detect and alert if scraping is blocked.
    Proxy Support: Allow scraping through proxies or Tor.
    Session/Cookie Handling: Persist cookies for login-required or session-based sites.


- [ ] Add progress bars with tqdm for user feedback
- [ ] Switch to asyncio/aiohttp for faster I/O
- [ ] Support chunked/streamed output (e.g., JSONL or DB)
- [ ] Add logging to external monitoring (Sentry, Slack)
- [ ] Implement exponential backoff for retries
- [ ] Add rate limiting support
- [ ] Add config file support for CLI defaults
- [ ] Add option for incremental scraping/resuming
- [ ] Add advanced unit/integration tests with mocks
- [ ] Dockerize the scraper for easy deployment
      
---

## 2. Exporter: Data Output

### XLSX Export

- [ ] Export all products to XLSX (in `exporter/xlsx.py`)
- [ ] Auto-create output directories if missing

### CSV Export

- [ ] Export all products to CSV (in `exporter/csv.py`)

### Error and QC Reporting

- [ ] Deduplicate products (`exporter/qc.py`)
- [ ] Check field completeness and create error reports in XLSX
- [ ] Optionally, export errors to CSV

### External Export

- [ ] Stub or implementation for external API/data push (`exporter/external.py`)

---

## 3. Orchestration & Main Entrypoint

- [ ] Main Workflow  
  End-to-end script (`main.py`) that:
  - [ ] Extracts category tree
  - [ ] Extracts all product URLs
  - [ ] Scrapes all product data
  - [ ] Runs deduplication & QC
  - [ ] Exports to XLSX & CSV
  - [ ] Exports error reports
  - [ ] Logs progress & errors
  - [ ] Configurable via CLI or config file (output dir, parallelism, etc)

- [ ] Dependency Injection  
  Orchestrator passes functions/objects between modules, no hard-coded imports

---

## 4. Performance & Robustness

- [ ] Retries and Throttling
  - [ ] All HTTP requests use retry/backoff and polite crawling
  - [ ] Respect rate limits & avoid blocks

- [ ] Logging
  - [ ] File + console logging, with timestamps and levels

---

## 5. Testing & Quality

- [ ] Unit Tests
  - [ ] For all major functions (category, product, exporter, QC)
  - [ ] Mock HTTP for reproducibility

- [ ] End-to-End Test
  - [ ] Test run on table.se (shortened scope for dev)

- [ ] Validation
  - [ ] Sample manual checks: output matches website, all products/fields covered

---

## 6. Documentation

- [ ] README.md
  - [ ] Project vision, structure, and roadmap (see above)
  - [ ] Usage instructions (running, config, output)
  - [ ] Developer/contributor guide

- [ ] Docstrings
  - [ ] All public functions/classes are documented

---

## 7. Extensibility & Configurability

- [ ] Exclusions
  - [ ] Easy to update/add exclusion logic

- [ ] Export Formats
  - [ ] Easy to add new exporters (JSON, XML, API, etc.)

- [ ] Config Files
  - [ ] Optional: support for YAML/TOML config for advanced options

---

## 8. Polish, Release & Iterate

- [ ] Review, refactor, and optimize codebase
- [ ] Tag v1.0 release
- [ ] Plan next iteration (feature requests, new sites, enhancements)
      
