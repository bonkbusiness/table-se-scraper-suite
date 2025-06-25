"""
table_se_export_utils.py

Export utilities for Table.se scraper suite.
Keep all export-related options here. To enable/disable an export destination,
just uncomment/comment the corresponding code block in your main script.

Supports:
- Local file export (Excel, already handled in export_to_xlsx)
- Google Drive export (Colab/Jupyter)
- Email export (yagmail)
- S3 export (boto3)
- Dropbox export (dropbox)
"""

import os

# 1. Google Drive (Colab/Jupyter)
def export_to_gdrive(local_filepath, gdrive_dir='/content/drive/MyDrive/'):
    """
    Moves the exported file to Google Drive (Colab/Jupyter).
    """
    try:
        from shutil import move
        if not os.path.exists(gdrive_dir):
            print(f"Google Drive directory '{gdrive_dir}' not found. Make sure to mount your Google Drive first.")
            return
        dest_path = os.path.join(gdrive_dir, os.path.basename(local_filepath))
        move(local_filepath, dest_path)
        print(f"File moved to Google Drive: {dest_path}")
    except Exception as e:
        print(f"Could not move to Google Drive: {e}")

# 2. Email export (yagmail)
def export_via_email(local_filepath, recipient_email, subject="Table.se Export", body="Here is the exported file."):
    """
    Emails the exported file as an attachment using yagmail.
    """
    try:
        import yagmail
        # Set up your credentials as environment variables or directly here (not recommended for production)
        yag = yagmail.SMTP(user=os.environ.get("YAGMAIL_USER"), password=os.environ.get("YAGMAIL_PASS"))
        yag.send(
            to=recipient_email,
            subject=subject,
            contents=body,
            attachments=local_filepath
        )
        print(f"Emailed {local_filepath} to {recipient_email}")
    except Exception as e:
        print(f"Could not send email: {e}")

# 3. Amazon S3 export
def export_to_s3(local_filepath, bucket, object_name=None):
    """
    Uploads the file to an S3 bucket.
    """
    try:
        import boto3
        s3 = boto3.client('s3')
        if object_name is None:
            object_name = os.path.basename(local_filepath)
        s3.upload_file(local_filepath, bucket, object_name)
        print(f"Uploaded {local_filepath} to s3://{bucket}/{object_name}")
    except Exception as e:
        print(f"Could not upload to S3: {e}")

# 4. Dropbox export
def export_to_dropbox(local_filepath, dropbox_path, access_token):
    """
    Uploads the file to Dropbox.
    """
    try:
        import dropbox
        dbx = dropbox.Dropbox(access_token)
        with open(local_filepath, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
        print(f"Uploaded {local_filepath} to Dropbox at {dropbox_path}")
    except Exception as e:
        print(f"Could not upload to Dropbox: {e}")

# Example usage (uncomment the relevant lines in your main script after file is exported):

# -- Google Drive (Colab) --
# from table_se_export_utils import export_to_gdrive
# export_to_gdrive(xlsx_path, gdrive_dir='/content/drive/MyDrive/')

# -- Email --
# from table_se_export_utils import export_via_email
# export_via_email(xlsx_path, recipient_email="your@email.com")

# -- S3 --
# from table_se_export_utils import export_to_s3
# export_to_s3(xlsx_path, bucket="your-bucket", object_name="exports/yourfile.xlsx")

# -- Dropbox --
# from table_se_export_utils import export_to_dropbox
# export_to_dropbox(xlsx_path, dropbox_path="/exports/yourfile.xlsx", access_token="YOUR_DROPBOX_ACCESS_TOKEN")