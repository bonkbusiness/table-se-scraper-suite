# Table.se Scraper Suite

A robust, modular, and precise Python scraper for [Table.se](https://www.table.se) with:

- **Parallel scraping** for efficiency
- **Smart validation** and anomaly detection of products
- **Excel export** with colored rows and category/subcategory info
- **Extensible backend and scanner modules**

## Files

- `table_se_scraper.py` – Main entry and classic scraper logic (unchanged, readable)
- `table_se_scraper_backend_enhanced.py` – Parallel, robust backend (imported by main)
- `table_se_smart_scanner.py` – Smart post-scrape validator, anomaly detector, and reporting
- `requirements.txt` – All dependencies

## Usage

1. `pip install -r requirements.txt`
2. Run the main script:

    ```bash
    python table_se_scraper.py
    ```

3. After scraping, you’ll have an Excel file (with a timestamp) and optionally a flagged products report.

## Advanced

- To extend, plug in new validator modules or export modules.
- To upload or email exports, see the README section “Exporting and Sharing Files”.

## FAQ

**Q: How do I save exports to Google Drive or S3?**  
A: See the code comments or ask Copilot for ready-to-use upload snippets.

**Q: Can I add more validation rules?**  
A: Yes! Edit `table_se_smart_scanner.py` and add your logic to `validate_product()`.

---

Bonkbusiness 2025 — For support, open an issue!
