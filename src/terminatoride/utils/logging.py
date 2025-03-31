"""Logging utilities for TerminatorIDE."""

import logging
from pathlib import Path
from typing import Optional


def setup_logger(name: str, log_file: Optional[str] = None, level=logging.DEBUG):
    """Set up a logger that logs to both console and file.

    Args:
        name: Name of the logger
        log_file: Path to log file (relative to ~/.terminatoride/logs/)
        level: Logging level

    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path.home() / ".terminatoride" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Create formatter and add it to the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Add console handler to logger
    logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        file_path = log_dir / log_file
        file_handler = logging.FileHandler(str(file_path))
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
