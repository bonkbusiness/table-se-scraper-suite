# Table.se Scraper Suite — User Guide

**Experimental scraper and data extractor for Table.se**

---

## 🚀 Quick Start

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the scraper**

   ```bash
   python table_se_scraper.py
   ```

3. **Find the export**

   The main Excel export is saved in your script directory, e.g.  
   `table_produkter_YYYYMMDD_HHMMSS.xlsx`

---

## 📦 Repository Structure

```text
table-se-scraper-suite/
├── table_se_scraper.py                 # Main entry point
├── table_se_scraper_backend_enhanced.py# Parallel scraping backend
├── table_se_smart_scanner.py           # Data validation & smart scan
├── table_se_export_utils.py            # Optional export functions
├── table_se_scraper_performance.py     # Retry, logging, polite scraping
├── table_se_cli.py                     # Interactive CLI
├── table_se_viz.py                     # Progress visualization (Streamlit)
├── requirements.txt
├── .gitignore
├── README.md
└── USER_GUIDE.md                       # This guide
```

---

## 🟢 Core Usage

### **Basic: Scrape and Export**

- Run the main script:

  ```bash
  python table_se_scraper.py
  ```

- The script scrapes categories & products, validates data, and saves an Excel file.
- You’ll see output like:

  ```
  Export till XLSX klar: table_produkter_20250625_153005.xlsx
  ```

### **Optional: Export to Google Drive, Email, S3, or Dropbox**

- In the main script, after export, you may call (uncomment) any of:
    ```python
    from table_se_export_utils import (
        export_to_gdrive, export_via_email, export_to_s3, export_to_dropbox
    )

    # Google Drive
    # export_to_gdrive(xlsx_path, gdrive_dir='/content/drive/MyDrive/')

    # Email (set env vars YAGMAIL_USER/YAGMAIL_PASS)
    # export_via_email(xlsx_path, recipient_email="your@email.com")

    # S3 (set up AWS credentials)
    # export_to_s3(xlsx_path, bucket="your-bucket", object_name="exports/yourfile.xlsx")

    # Dropbox (get a Dropbox access token)
    # export_to_dropbox(xlsx_path, dropbox_path="/exports/yourfile.xlsx", access_token="YOUR_DROPBOX_ACCESS_TOKEN")
    ```

---

## ⚡️ Advanced & Optional Features

### **Performance & Robustness**

- **Logging:**  
  Enable logging to a file for all scraping activity and errors:

    ```python
   from table_se_scraper_performance import setup_logging, robust_scrape
   setup_logging()
   # logs to scraper.log
    ```

- **Retry & Polite Crawling:**  
  Wrap your scraping functions for automatic retries and polite delays:

    ```python
    from table_se_scraper_performance import robust_scrape
    robust_scrape(my_extract_func, url, retries=3, delay=2)
    ```

- **Proxy support:**  
  Pass a `proxies` dict to `robust_scrape` if you need to use a proxy.

### **Interactive CLI Mode**

- Run:

    ```bash
    python table_se_cli.py
    ```

- Follow prompts to choose scraping/export options interactively.

### **Live Progress Visualization**

- Requires [Streamlit](https://streamlit.io/):

    ```bash
    pip install streamlit
    streamlit run table_se_viz.py
    ```

- Shows a live dashboard of progress.  
  _(Current version is a simulation; for live data, connect log/progress from your main script.)_

---

## 🧐 Validation & Smart Error Checking

- The suite automatically flags suspicious or invalid product data using `table_se_smart_scanner.py`.
- You can extend validation by editing `validate_product()` in that file.

---

## 🛠️ Good to Know & Troubleshooting

- **Credentials & API Keys:**  
  - Email export: set `YAGMAIL_USER` & `YAGMAIL_PASS` as environment variables.
  - S3: configure AWS credentials (via AWS CLI or environment).
  - Dropbox: create an app, generate an access token from [Dropbox developer console](https://www.dropbox.com/developers/apps).

- **Where’s the export?**  
  - Excel files are saved in your working directory unless you specify otherwise.

- **Slow performance?**  
  - Lower the number of workers in `main_enhanced()` or increase delays using `robust_scrape`.

- **Errors?**  
  - Check `scraper.log` for details if logging is enabled.

- **How to scrape only specific categories?**  
  - Edit `table_se_scraper.py`, modify category extraction logic as needed.

---

## 🔄 Typical Workflow Example

1. **Install, run, and get export:**
   ```bash
   pip install -r requirements.txt
   python table_se_scraper.py
   ```

2. **Export to Google Drive (Colab):**
   ```python
   from table_se_export_utils import export_to_gdrive
   export_to_gdrive(xlsx_path)
   ```

3. **Send by email:**
   ```python
   from table_se_export_utils import export_via_email
   export_via_email(xlsx_path, recipient_email="me@mydomain.com")
   ```

4. **Run with CLI for options:**
   ```bash
   python table_se_cli.py
   ```

5. **See live progress (demo):**
   ```bash
   streamlit run table_se_viz.py
   ```

---

## ✨ Extending and Contributing

- Add new export methods by extending `table_se_export_utils.py`.
- Add new validation logic in `table_se_smart_scanner.py`.
- PRs and issues are welcome! See the [GitHub repo](https://github.com/bonkbusiness/table-se-scraper-suite).

---

## 📋 Requirements

See `requirements.txt`.  
Main libraries:  
- requests  
- beautifulsoup4  
- openpyxl  
- tqdm  
- numpy  
- streamlit (for visualization)  
- yagmail, boto3, dropbox (for optional exports)

---

## 📣 Where to Get Help

- GitHub issues: [Open an issue](https://github.com/bonkbusiness/table-se-scraper-suite/issues)
- This user guide: `USER_GUIDE.md`
- Project README

---

_Bonkbusiness 2025 — experimental. Use at your own risk!_