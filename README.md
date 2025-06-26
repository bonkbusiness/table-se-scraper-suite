# table-se-scraper-suite

Experimental scraper and data extractor for Table.se.

## Features

- Scrapes product data from Table.se, including detailed measurements and metadata.
- Caching system to avoid redundant network requests.
- Exports data to XLSX and CSV with customizable column order.
- Extracts and exports advanced product details, including dimensions, material, series, and more.

---

## ⚠️ Major Export Logic Refactor (see branch: `export-refactor`)

**Notice:**  
A major refactor of all export, backup, and error export logic has landed in the [`export-refactor`](https://github.com/bonkbusiness/table-se-scraper-suite/tree/export-refactor) branch (see [PR #1](https://github.com/bonkbusiness/table-se-scraper-suite/pull/1)).

- All exports, backups, and logs are now written to their own folders (`exports/`, `backups/`, `logs/`) with timestamped filenames.
- Only the modern, timestamped, folder-based export/backup functions are used throughout the codebase—no more legacy export code.
- Removed all legacy/duplicate export and backup functions.
- All error and fallback handling now uses these modern functions.
- Data is always sorted by name before export.
- The codebase is now more maintainable and robust, with clear file structure and improved error handling.
- **No changes were made to scraping/parsing logic or styling**—all data collection and formatting remains unchanged.

If you are depending on legacy export/backup code or direct file paths, **please update any scripts or downstream consumers accordingly**.

---

## ✨ **What’s New?**

- **Supercharged Logging**:  
  - Console logs are now colorful, emoji-rich, and show module/line number for easier debugging.
  - Logs are also written to `scraper.log` for post-run analysis.
- **Centralized Logging Setup**:  
  - `setup_logging()` in `table_se_scraper_performance.py` sets up all logging with one call—no more repeated boilerplate!
- **Parallel Scraping**:  
  - Backend now supports robust, multi-threaded scraping for speed and reliability.
- **Smart Data Validation**:  
  - `table_se_smart_scanner.py` checks all products for missing or suspicious data, price outliers, etc.
- **Separate Error Exports**:  
  - Validation errors/anomalies are now exported into a dedicated XLSX file.
- **Exclusions Handling**:  
  - `exclusions.py` allows you to define product/category exclusions, or other filtering logic.
- **Highly Modular**:  
  - Each feature lives in its own file, so you can mix, match, or extend with ease.
- **Colab-Friendly**:  
  - Tips and code snippets for running in Google Colab are included below.
- **Ready for CI/Automation**:  
  - Designed to run in notebooks, scripts, or automated pipelines.

- **Added support for "Djup" (Depth) dimension:** Now extracts "Djup" or "D" from product pages and includes it in exports.
- **Reordered export columns:** You can now control the order of columns in both XLSX and CSV exports.
- **Robust value/unit parsing:** Improved handling of measurements (e.g., "12 cm", "10,5L") for all relevant fields.
- **Bugfix:** Ensured `parse_value_unit` is always defined and available regardless of module import order or reloads.
- **Improved modularity:** All export and extraction logic explicitly includes new and existing data points for consistency.
  
---

## 🔄 **Changelog**

### [v17] 2025-06-26
- **Major export/backup refactor!**
- All exports, backups, and logs are now written to their own folders (`exports/`, `backups/`, `logs/`) with timestamped filenames.
- Only the modern, timestamped, folder-based export/backup functions are used everywhere—no more legacy export code.
- Removed all legacy/duplicate export and backup functions.
- All error and fallback handling now uses these modern functions.
- Data is always sorted by name before export.
- The codebase is now more maintainable and robust, with clear file structure and improved error handling.
- **No changes were made to scraping/parsing logic or styling**—these remain untouched.

### [v16] 2025-06-26
- Added support for extracting **"Djup"** (depth) from product pages, including detection as both "Djup" and "D".
- **Exports now include "Djup (värde)" and "Djup (enhet)"** in both XLSX and CSV files.
- **Explicit, customizable column order** for all exports (XLSX and CSV); columns are now consistently ordered and easier to manage.
- Improved and robust value/unit parsing for all relevant fields, including fallback/flexible handling.
- Fixed: `parse_value_unit` is now always defined and robust to import/reload issues.
- Improved measurement extraction logic for all relevant fields (length, width, height, depth, etc).
- Reordered export columns for clearer data presentation.
- Updated documentation to reflect new fields and export structure.

### [v15] 2025-06-25
- Main script now outputs **two XLSX files**: one for products, one for validation errors (if any).
- Improved error reporting for Colab and desktop environments.

### [v14] 2025-06-25
- Smart scanner (`smart_scan_products`) now runs after scraping.
- Detected anomalies are exported to a dedicated error XLSX.

### [v13] 2025-06-24
- Switched to `main_enhanced` backend for parallelized scraping.

### [v12] 2025-06-24
- Improved import order, added Colab install instructions, further modularization.

### [v11] 2025-06-23
- All direct `logging.basicConfig` removed; all scripts use `setup_logging()`.

### [v10] 2025-06-23
- Introduced centralized logging setup in `table_se_scraper_performance.py`.

### [v9] 2025-06-22
- Initial stable, modular release with product/category exclusion, caching, and XLSX export.

---

## 🗂️ **File Overview**

| File                                | Purpose/Description                                                                                   |
|--------------------------------------|------------------------------------------------------------------------------------------------------|
| `table_se_cli.py`                   | Interactive CLI to run the scraper and choose export destinations.                                   |
| `table_se_scraper.py`               | Main scraping logic: categories, products, export to XLSX, logging, backend enhancements, smart scan, and error export.   |
| `table_se_scraper_performance.py`   | Logging setup (`setup_logging()`), retry wrappers, polite delays, proxy support.                     |
| `table_se_smart_scanner.py`         | Validates scraped data for missing/suspect fields, outliers, SKU/image checks.                       |
| `table_se_scraper_backend_enhanced.py` | Fast, threaded scraping, deduplication, completeness checks before export.                        |
| `table_se_export_utils.py`          | Exports to Google Drive, Email, S3, Dropbox.                                                         |
| `table_se_viz.py`                   | Live Streamlit dashboard (progress, logs, data preview).                                             |
| `exclusions.py`                     | List or logic of product/category exclusions (e.g., skip certain brands, categories, etc.).          |
| `product_cache.py`                  | **Efficient product-level caching**: prevents redundant re-scraping, accelerates repeated runs, and enables change detection by storing product data with a hash of the scraped HTML. |
| `requirements.txt`                  | All required Python packages for easy setup.                                                         |

---

## Export Columns

The following columns are included in the export (in order):

- Namn
- Artikelnummer
- Färg
- Material
- Serie
- Pris exkl. moms (värde)
- Pris exkl. moms (enhet)
- Pris inkl. moms (värde)
- Pris inkl. moms (enhet)
- Mått (text)
- Längd (värde), Längd (enhet)
- Bredd (värde), Bredd (enhet)
- Höjd (värde), Höjd (enhet)
- Djup (värde), Djup (enhet)
- Diameter (värde), Diameter (enhet)
- Kapacitet (värde), Kapacitet (enhet)
- Volym (värde), Volym (enhet)
- Produktbild-URL
- Produkt-URL

## 🚀 **Quickstart**

### 1. **Install dependencies**

```bash
pip install -r requirements.txt
```

### 2. **Run the CLI**

```bash
python table_se_cli.py
```
- Prompts you to start scraping, choose export method (Google Drive, Email, S3, Dropbox, or skip).

### 3. **Or run the scraper directly**

```bash
python table_se_scraper.py
```

### 4. **Check logs**

- **Console:** Colorful, emoji, context-rich logs.
- **File:** See `scraper.log` for a persistent, detailed log.

### 5. **Live dashboard (optional)**

```bash
python table_se_viz.py
```
- Opens a Streamlit app for live progress and logs.

---

### `product_cache.py` — Purpose & Usage

- **Purpose:**  
  Optimizes scraping by caching each product’s data (in JSON files) keyed by article number and a hash of the product page’s content. Only products with changed HTML are re-scraped.  
- **How it works:**  
  - `hash_content(content)`: Returns a SHA-256 hash of the product page HTML.
  - `get_cached_product(artikelnummer, content_hash)`: Returns cached product data if the HTML hash matches; otherwise returns None (forces re-scrape).
  - `update_cache(artikelnummer, data, content_hash)`: Saves product data and hash to the cache directory.
- **Benefits:**  
  - **Massive speedup** for repeated runs.
  - **Change detection**: Only changed/updated products are re-scraped.
  - **File-based:** Each product is cached as a small JSON file under `product_cache/`.

---

## 🧑‍💻 **Using in Google Colab**

- **Upload your repo files, then:**
  ```python
  !pip install -r requirements.txt
  from table_se_scraper_performance import setup_logging
  setup_logging()
  from table_se_scraper import main
  main() # or your desired entry point
  ```
- **Download results:**
  - Use Colab’s file browser (left sidebar) to download `scraper.log`, XLSX files, etc.
- **Tips:**
  - Don’t use `input()` prompts in Colab. Prefer functions that accept parameters.
  - Use `%run table_se_scraper.py` or adapt code into a Colab cell.

---

## 🛠️ **Advanced Usage & Tips**

- **Customize Logging:**  
  Edit `setup_logging()` in `table_se_scraper_performance.py` for your own color theme, icons, or log level.
- **Add/Change Exclusions:**  
  Edit `exclusions.py` to skip certain brands, categories, or products.
- **Export to New Destinations:**  
  Add a function to `table_se_export_utils.py` and call from the CLI or your script.
- **Batch/CI runs:**  
  Script your runs, and use the log file for monitoring or debugging.
- **Notebook Use:**  
  Import scraper functions and call directly in your Jupyter or Colab notebooks.

---

## 🧩 **How Each File Works Together**

1. **CLI/Script calls** →  
2. **`setup_logging()`** (sets up all logging globally) →  
3. **Scraper core** (`table_se_scraper.py`) fetches categories/products →  
4. **Backend** (`table_se_scraper_backend_enhanced.py`) does parallel fetching, deduplication →  
5. **Product Cache** (`product_cache.py`) prevents redundant re-scraping, speeds up repeated runs, and detects product changes. →  
6. **Smart Scanner** (`table_se_smart_scanner.py`) validates/flags bad data and exports a separate error XLSX if needed →  
7. **Exclusions** (`exclusions.py`) filters out unwanted data →  
8. **Export Utils** (`table_se_export_utils.py`) send XLSX where you want →  
9. **Logs everywhere**: All steps log events, warnings, errors, and successes.

---

## 🔥 **Logging Example**

Console output:
```
📝 19:41:18 INFO [table_se_scraper:134]: Scraping started
😬 19:41:19 WARNING [table_se_scraper:155]: Rate limit approaching
💥 19:41:21 ERROR [table_se_scraper:202]: Could not fetch page
🔥 19:41:25 CRITICAL [table_se_scraper:304]: Scraper crashed!
```

File (`scraper.log`):
```
19:41:18 INFO [table_se_scraper:134]: Scraping started
19:41:19 WARNING [table_se_scraper:155]: Rate limit approaching
19:41:21 ERROR [table_se_scraper:202]: Could not fetch page
19:41:25 CRITICAL [table_se_scraper:304]: Scraper crashed!
```

---

## 📁 **Adding/Editing Exclusions**

Edit `exclusions.py` like this:
```python
# List of categories, brands, or product names to exclude
EXCLUDED_CATEGORIES = ["Gift Cards", "Special Offers"]
EXCLUDED_BRANDS = ["BrandX", "BrandY"]

def is_excluded(product):
    return (product['category'] in EXCLUDED_CATEGORIES or
            product['brand'] in EXCLUDED_BRANDS)
```
*Integrate this in your main scraper or scanner to skip matching products.*

---

## 📦 **Requirements**

See `requirements.txt`. Main packages:
- `requests`
- `beautifulsoup4`
- `openpyxl`
- `yagmail` (for email export)
- `boto3` (for S3 export)
- `dropbox`
- `streamlit`
- `colorama` or similar for logging (optional, but enhances colors in some terminals)

---

## 📝 **FAQ**

**Q: How do I add a new export method?**  
A: Add a function in `table_se_export_utils.py`, then call it from the CLI or your script.

**Q: How do I suppress colored logs?**  
A: Edit or remove the color codes in `FancyFormatter` in `table_se_scraper_performance.py`.

**Q: Can I run on Windows/Mac/Linux/Colab?**  
A: Yes—just make sure dependencies are installed. For Colab, see usage tips above.

---

## 👤 **Author**

[bonkbusiness](https://github.com/bonkbusiness)

---

## 📄 License

MIT — see [LICENSE](LICENSE)
