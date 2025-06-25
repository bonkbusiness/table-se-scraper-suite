# Table.se Scraper Suite

_A robust, modular, and precise Python scraper for [Table.se](https://www.table.se)_

**Features:**
- Parallel scraping of product categories and products
- Smart validation and anomaly detection of product data
- Export to Excel with category-based color coding
- Multiple export options: local, Google Drive, email, S3, Dropbox (via plugin module)
- Modular structure for easy extension

---

## Repository Structure

```text
table-se-scraper-suite/
├── table_se_scraper.py
├── table_se_scraper_backend_enhanced.py
├── table_se_smart_scanner.py
├── table_se_export_utils.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## File Overview & Main Functions

### **1. `table_se_scraper.py`**
- **Main entry point** for scraping Table.se
- Handles category and product extraction
- Exports scraped data to Excel (`export_to_xlsx`)
- Usage:
    ```bash
    python table_se_scraper.py
    ```
- **Main functions:**
    - `extract_category_tree()`
    - `extract_products_from_category(url)`
    - `extract_product_data(url)`
    - `scrape_all_products_deep()`
    - `export_to_xlsx(data, base_name)`
    - `main()` — orchestrates scraping and export

### **2. `table_se_scraper_backend_enhanced.py`**
- Provides **parallel and robust backend** logic
- Manages multithreading, deduplication, and error handling
- Used by `table_se_scraper.py` as `main_enhanced()`
- **Main functions:**
    - `main_enhanced(extract_category_tree_func, skip_func, extract_func, export_func, max_workers)`

### **3. `table_se_smart_scanner.py`**
- **Smart scanner/validator** module
- Validates product data, detects anomalies, and reports errors
- Used for post-processing to ensure data quality
- **Main functions:**
    - `smart_scan_products(products)`
    - `validate_product(product)`
    - `report_product_errors(errors)`

### **4. `table_se_export_utils.py`**
- **Optional export utilities module**
- Lets you easily export the resulting `.xlsx` file to various destinations
- **Functions (all optional, call as needed):**
    - `export_to_gdrive(local_filepath, gdrive_dir)`
    - `export_via_email(local_filepath, recipient_email, subject, body)`
    - `export_to_s3(local_filepath, bucket, object_name)`
    - `export_to_dropbox(local_filepath, dropbox_path, access_token)`

---

## Usage

### **Basic Scraping & Export (Local)**
1. Install requirements:
    ```bash
    pip install -r requirements.txt
    ```
2. Run the main script:
    ```bash
    python table_se_scraper.py
    ```
3. After scraping, you will see:
    ```
    Export till XLSX klar: table_produkter_YYYYMMDD_HHMMSS.xlsx
    ```

### **Optional: Export to Cloud/Email (Uncomment to Use)**

After the Excel file is created (the variable is `xlsx_path`), you can use export options from `table_se_export_utils.py`:

```python
from table_se_export_utils import export_to_gdrive, export_via_email, export_to_s3, export_to_dropbox

# Google Drive (Colab/Jupyter)
# export_to_gdrive(xlsx_path, gdrive_dir='/content/drive/MyDrive/')

# Email (requires yagmail, and set env vars YAGMAIL_USER/YAGMAIL_PASS)
# export_via_email(xlsx_path, recipient_email="your@email.com")

# S3 (requires boto3 and AWS credentials)
# export_to_s3(xlsx_path, bucket="your-bucket", object_name="exports/yourfile.xlsx")

# Dropbox (requires dropbox token)
# export_to_dropbox(xlsx_path, dropbox_path="/exports/yourfile.xlsx", access_token="YOUR_DROPBOX_ACCESS_TOKEN")
```

Uncomment the relevant lines in your script to enable.

---

## Advanced

- **Validation:**  
  The smart scanner is used for validating and flagging problematic products.  
  You can use/extend `smart_scan_products()` in `table_se_smart_scanner.py`.

- **Parallelism:**  
  By default, `main_enhanced()` uses up to 8 worker threads. You can adjust this for faster or more conservative scraping.

- **Extensibility:**  
  You can add new export methods by extending `table_se_export_utils.py`.

---

## FAQ

**Q: How do I upload exports to Google Drive or S3?**  
A: Uncomment the relevant function call in your script and ensure the dependencies (and credentials) are set up.

**Q: Can I add more validation rules?**  
A: Yes! Edit `validate_product()` in `table_se_smart_scanner.py`.

**Q: How do I change the export filename/location?**  
A: Pass a different `base_name` to `export_to_xlsx()` in `table_se_scraper.py`.

---

## Requirements

See `requirements.txt`. Most common dependencies are:
- requests
- beautifulsoup4
- openpyxl
- tqdm
- numpy

---

## License

Experimental use only.  
Bonkbusiness 2025 — For support, open an issue!
