"""
Interactive CLI for Table.se Scraper Suite

Run:
    python table_se_cli.py

Lets you choose scrape options and export methods interactively.
"""

import sys
from table_se_scraper import main as full_scrape
from table_se_export_utils import (
    export_to_gdrive, export_via_email, export_to_s3, export_to_dropbox
)

def cli():
    print("==== Table.se Scraper CLI ====")
    print("1. Scrape all products")
    print("2. Exit")
    choice = input("Choose an option: ").strip()
    if choice == '1':
        print("Scraping...")
        xlsx_path = full_scrape()
        print(f"Exported to {xlsx_path}")
        print("Export options:")
        print("  1. Google Drive")
        print("  2. Email")
        print("  3. Amazon S3")
        print("  4. Dropbox")
        print("  5. Skip")
        export_choice = input("Choose export option: ").strip()
        if export_choice == '1':
            gdrive_dir = input("Google Drive directory (default /content/drive/MyDrive/): ").strip() or "/content/drive/MyDrive/"
            export_to_gdrive(xlsx_path, gdrive_dir)
        elif export_choice == '2':
            email = input("Recipient email: ").strip()
            export_via_email(xlsx_path, recipient_email=email)
        elif export_choice == '3':
            bucket = input("S3 Bucket: ").strip()
            obj = input("S3 Object name (default: filename): ").strip() or None
            export_to_s3(xlsx_path, bucket=bucket, object_name=obj)
        elif export_choice == '4':
            path = input("Dropbox path (e.g. /exports/yourfile.xlsx): ").strip()
            token = input("Dropbox access token: ").strip()
            export_to_dropbox(xlsx_path, dropbox_path=path, access_token=token)
        else:
            print("No export performed.")
    else:
        print("Bye!")
        sys.exit(0)

if __name__ == "__main__":
    cli()