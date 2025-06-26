import logging
import os
from datetime import datetime

LOG_DIR = "logs"

def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)

def get_log_filename(prefix="table_produkter", ext="log", timestamp=None):
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(LOG_DIR, f"{prefix}_{timestamp}.{ext}")

def setup_logging(prefix="table_produkter", timestamp=None):
    ensure_log_dir()
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = get_log_filename(prefix, "log", timestamp)
    logging.basicConfig(
        level=logging.INFO,
        filename=log_file,
        filemode='a',
        format='%(asctime)s %(levelname)s:%(message)s'
    )
    root_logger = logging.getLogger()
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(logging.StreamHandler())

def logprint(msg):
    print(msg)
    logging.info(msg)