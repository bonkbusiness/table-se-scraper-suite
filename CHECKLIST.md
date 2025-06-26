# Table.se Scraper Suite – Concrete Completion Checklist

## 1. Modular Scraper: Core Functionality

- [ ] **Category Extraction**
  - [ ] Fully traverse all category levels (main, sub, sub-sub) on table.se
  - [ ] Exclude categories based on `exclusions.py` logic
  - [ ] Unit tests for category extraction
        
📌 Step 1: Category Extraction

A. Functional Requirements

    Full Traversal: Script must crawl all category, subcategory, and sub-subcategory pages on table.se.
    Exclusion Logic: Must skip categories based on rules in exclusions.py (i.e., URLs or names to avoid).
    Unit Testing: Extraction logic should be independently testable for correctness and exclusion.

-1. Modular Scraper: Core Functionality
  Category Extraction
  1.1 Fully traverse all category levels (main, sub, sub-sub) on table.se

    Is it implemented?
    Yes, in principle.
        The function extract_category_tree() (from table_se_scraper_backend_enhanced.py) recursively traverses all main categories and their subcategories, building a tree.
        Helper: build_category_node(name, url, seen) manages recursion.
        It is already modular and ready to be migrated (or is already migrated) to scraper/category.py.

    Action:
        Confirm that this logic is now in scraper/category.py (or move it if not).
        Ensure it builds a complete tree (test on live site).

  1.2 Exclude categories based on exclusions.py logic

    Is it implemented?
    Yes.
        The pruning step uses is_excluded(url) to skip nodes after the tree is built.
        The function prune_excluded_nodes(node) recursively removes excluded nodes.

    Action:
        Confirm exclusions.py and is_excluded() are imported/used in scraper/category.py.
        Ensure excluded categories are not present in the final tree.

  1.3 Unit tests for category extraction

    Is it implemented?
    Not yet.
        There is no evidence of a tests/test_category.py or similar.

    Action:
        Create tests/test_category.py.
        Write tests that:
            Mock category HTML structure.
            Mock is_excluded to simulate exclusions.
            Validate that:
                The full tree is built when no exclusions.
                Excluded categories are actually pruned.
                Edge cases (no categories, deep nesting, broken HTML) are handled.
        Add to CI if possible.
      

B. What’s Already In-Place?

You already have (from table_se_scraper_backend_enhanced.py):

    extract_category_tree()
    build_category_node(name, url, seen)
    prune_excluded_nodes(node)
    Use of exclusions via is_excluded()

These are modular and mostly ready for scraper/category.py!
C. What Is Still Needed?

    Polish & Refactor: Move/clean code into scraper/category.py.
    Unit Tests: In tests/test_category.py (or similar)
        Test: full tree, structure, exclusions, edge-cases (empty/404/redirects).
    Docs: Docstrings for all public functions.

D. Next Steps

    Move/Refactor category extraction to scraper/category.py
        Ensure all exclusion and recursion logic is included.
        Clean up interface (inputs/outputs).

    Draft Unit Tests:
        Use a mock/fake HTML for categories and is_excluded logic.
        Test for:
            All nodes found
            Exclusions respected
            Correct tree structure

    Docstrings & Comments:
        Make all major functions self-explanatory.


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
