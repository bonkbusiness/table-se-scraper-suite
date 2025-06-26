# Table.se Scraper Suite – Concrete Completion Checklist

## 1. Modular Scraper: Core Functionality

- [ ] **Category Extraction**
  - [ ] Fully traverse all category levels (main, sub, sub-sub) on table.se
  - [ ] Exclude categories based on `exclusions.py` logic
  - [ ] Unit tests for category extraction

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
