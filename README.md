# Table.se Scraper Suite

A modular, robust, and production-ready scraper for [Table.se](https://www.table.se), featuring interactive CLI, blazing-fast parallel scraping, smart validation, rich exports, and beautiful, developer-friendly logging.

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
- **Exclusions Handling**:  
  - `exclusions.py` allows you to define product/category exclusions, or other filtering logic.
- **Highly Modular**:  
  - Each feature lives in its own file, so you can mix, match, or extend with ease.
- **Colab-Friendly**:  
  - Tips and code snippets for running in Google Colab are included below.
- **Ready for CI/Automation**:  
  - Designed to run in notebooks, scripts, or automated pipelines.

---

## 🗂️ **File Overview**

| File                                | Purpose/Description                                                                                   |
|--------------------------------------|------------------------------------------------------------------------------------------------------|
| `table_se_cli.py`                   | Interactive CLI to run the scraper and choose export destinations.                                   |
| `table_se_scraper.py`               | Main scraping logic: categories, products, export to XLSX. Calls logging and backend enhancements.   |
| `table_se_scraper_performance.py`   | Logging setup (`setup_logging()`), retry wrappers, polite delays, proxy support.                     |
| `table_se_smart_scanner.py`         | Validates scraped data for missing/suspect fields, outliers, SKU/image checks.                       |
| `table_se_scraper_backend_enhanced.py` | Fast, threaded scraping, deduplication, completeness checks before export.                        |
| `table_se_export_utils.py`          | Exports to Google Drive, Email, S3, Dropbox.                                                         |
| `table_se_viz.py`                   | Live Streamlit dashboard (progress, logs, data preview).                                             |
| `exclusions.py`                     | List or logic of product/category exclusions (e.g., skip certain brands, categories, etc.).          |
| `requirements.txt`                  | All required Python packages for easy setup.                                                         |

---

## 🖥️ **Screenshots**

> *(Replace these with actual screenshots from your runs!)*

### Interactive CLI
![CLI screenshot](screenshots/cli.png)

### Colorful Logs in Terminal
![Logs screenshot](screenshots/logs.png)

### Smart Data Scanner Output
![Scanner screenshot](screenshots/scanner.png)

### Streamlit Dashboard
![Dashboard screenshot](screenshots/dashboard.png)

---

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
  Add a function to `table_se_export_utils.py` and call from `table_se_cli.py`.
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
5. **Smart Scanner** (`table_se_smart_scanner.py`) validates/flags bad data →  
6. **Exclusions** (`exclusions.py`) filters out unwanted data →  
7. **Export Utils** (`table_se_export_utils.py`) send XLSX where you want →  
8. **Logs everywhere**: All steps log events, warnings, errors, and successes.

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
