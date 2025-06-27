import logging
import os
import sys
from scraper.utils import make_output_filename
from datetime import datetime

class LoggerFactory:
    LOG_DIR = "logs"
    FORMAT = "[%(asctime)s][%(levelname)s][%(name)s]: %(message)s"
    DATEFMT = "%Y-%m-%d %H:%M:%S"
    # Icons (emojis) and colors (ANSI) for each level
    LEVEL_ICONS = {
        "DEBUG": "🐞",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🔥"
    }
    LEVEL_COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[41m", # Red background
    }
    RESET = "\033[0m"

    @classmethod
    def ensure_log_dir(cls):
        os.makedirs(cls.LOG_DIR, exist_ok=True)

    @classmethod
    def get_log_filename(cls, prefix="app"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(cls.LOG_DIR, f"{prefix}_{timestamp}.log")

    @classmethod
    def setup(cls, prefix="app", to_stdout=True, log_level=logging.INFO):
        """
        Set up logging to file (plain) and console (color + icons).
        Call once at program start.
        """
        cls.ensure_log_dir()
        log_file = cls.get_log_filename(prefix)
        # File handler: plain formatting
        file_handler = logging.FileHandler(log_file, mode='a')
        file_formatter = logging.Formatter(cls.FORMAT, datefmt=cls.DATEFMT)
        file_handler.setFormatter(file_formatter)
        handlers = [file_handler]

        # Console handler: colors + icons
        if to_stdout:
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(cls.ColoredFormatter())
            handlers.append(stream_handler)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        # Remove any duplicate handlers
        root_logger.handlers = []
        for handler in handlers:
            root_logger.addHandler(handler)

    class ColoredFormatter(logging.Formatter):
        def __init__(self):
            super().__init__(LoggerFactory.FORMAT, datefmt=LoggerFactory.DATEFMT)

        def format(self, record):
            icon = LoggerFactory.LEVEL_ICONS.get(record.levelname, "")
            color = LoggerFactory.LEVEL_COLORS.get(record.levelname, "")
            msg = super().format(record)

            # Split into lines, each event (line) is printed separately with icon/color
            # This avoids multi-line logs being cluttered into a single console event
            lines = msg.splitlines()
            formatted_lines = []
            for line in lines:
                if sys.stdout.isatty():
                    formatted_lines.append(f"{color}{icon} {line}{LoggerFactory.RESET}")
                else:
                    formatted_lines.append(f"{icon} {line}")
            return "\n".join(formatted_lines)

    @staticmethod
    def get_logger(name=None):
        return logging.getLogger(name)

def get_logger(name):
    log_file = make_output_filename('scrape', 'log', 'logs')
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_file, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    fh.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(fh)
    return logger
