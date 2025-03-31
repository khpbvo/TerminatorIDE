"""Logging utilities for TerminatorIDE."""

import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path


def setup_logger(name="terminatoride", log_level=logging.DEBUG):
    """Set up a logger with file and console handlers."""
    # Create logs directory in user's home folder
    log_dir = Path.home() / ".terminatoride" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create a timestamp-based log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{name}_{timestamp}.log"

    # Configure logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear existing handlers if any
    if logger.handlers:
        logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Less verbose for console

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Log startup information
    logger.info(f"Logger initialized, writing to {log_file}")

    return logger


def log_exception(logger, message="Exception occurred", exc_info=None):
    """Log an exception with full traceback."""
    if exc_info is None:
        exc_type, exc_value, exc_traceback = sys.exc_info()
    else:
        exc_type, exc_value, exc_traceback = exc_info

    if exc_traceback:
        stack_trace = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
    else:
        stack_trace = "No traceback available"

    logger.error(f"{message}: {exc_value}\nTraceback:\n{stack_trace}")
