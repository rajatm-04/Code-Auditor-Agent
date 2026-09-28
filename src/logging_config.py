"""
Logging configuration.
Combines Rich console output with persistent file logging.
"""

import logging
import os
from typing import Optional
from rich.logging import RichHandler


def setup_logging(log_file: Optional[str] = None, verbose: bool = False) -> logging.Logger:
    """Configures root logger with Rich terminal formatting and optional file logger."""
    level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger("repo_auditor")
    logger.setLevel(level)

    # Clear existing handlers to prevent duplicate lines
    if logger.hasHandlers():
        logger.handlers.clear()

    # 1. Console handler (Rich)
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,
        show_path=False,
        markup=True,
    )
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # 2. File handler (if log_file specified)
    if log_file:
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger