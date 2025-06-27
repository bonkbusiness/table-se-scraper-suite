"""
scraper/logging.py

Centralized logging utilities for the Table.se Scraper Suite.

Features:
    - LoggerFactory: class to configure and manage both file and console logging.
        - Supports colored and emoji-enhanced logging to the console for improved readability.
        - Writes plain logs to time-stamped files in the "logs" directory.
    - get_logger: utility function to create or fetch a logger, ensuring file output.

Usage:
    from scraper.logging import LoggerFactory, get_logger

    # At the start of your main script:
    LoggerFactory.setup(prefix="scrape", to_stdout=True, log_level=logging.INFO)
    logger = LoggerFactory.get_logger(__name__)

    # For a simple file logger:
    logger = get_logger("my_module")

Notes:
    - Always call LoggerFactory.setup() once at application start for consistent logging.
    - Console output uses ANSI color codes and icons if the output is a TTY.
    - Log files are created under ./logs/ with a unique timestamp per run.

Author: bonkbusiness
License: MIT
"""

import logging
import os
import sys
from scraper.utils import make_output_filename
from datetime import datetime

class LoggerFactory:
    """
    Factory and configuration class for suite-wide logging.

    Use LoggerFactory.setup() at application start to configure both file and
    console handlers. Console logs include colors and emojis for clear status
    indication. File logs use a plain format for archival and debugging.
    """
    LOG_DIR = "logs"
    FORMAT = "[%(asctime)s][%(levelname)s][%(name)s]: %(message)s"
    DATEFMT = "%Y-%m-%d %H:%M:%S"
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
        """Ensure the log directory exists."""
        os.makedirs(cls.LOG_DIR, exist_ok=True)

    @classmethod
    def get_log_filename(cls, prefix="app"):
        """
        Generate a timestamped log file path.
        Args:
            prefix (str): Log file prefix (e.g., "scrape", "app").
        Returns:
            str: Full path to log file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(cls.LOG_DIR, f"{prefix}_{timestamp}.log")

    @classmethod
    def setup(cls, prefix="app", to_stdout=True, log_level=logging.INFO):
        """
        Set up logging for the application.
        Args:
            prefix (str): Prefix for log files.
            to_stdout (bool): If True, log to console with colors/icons.
            log_level: Logging level (e.g., logging.INFO).
        """
        cls.ensure_log_dir()
        log_file = cls.get_log_filename(prefix)
        # File handler: plain formatting
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
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
        """
        Formatter for colorized and emoji-enhanced console logging.
        """
        def __init__(self):
            super().__init__(LoggerFactory.FORMAT, datefmt=LoggerFactory.DATEFMT)

        def format(self, record):
            icon = LoggerFactory.LEVEL_ICONS.get(record.levelname, "")
            color = LoggerFactory.LEVEL_COLORS.get(record.levelname, "")
            msg = super().format(record)
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
        """
        Get (or create) a logger by name, after setup.
        Args:
            name (str|None): Logger name.
        Returns:
            logging.Logger
        """
        return logging.getLogger(name)

def get_logger(name):
    """
    Utility to get a simple file logger (with a standardized log filename).
    Args:
        name (str): Logger name.
    Returns:
        logging.Logger
    """
    log_file = make_output_filename('scrape', 'log', 'logs')
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_file, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    fh.setFormatter(formatter)
    # Prevent duplicate handlers
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == fh.baseFilename for h in logger.handlers):
        logger.addHandler(fh)
    return logger