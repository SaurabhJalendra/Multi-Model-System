"""Logging utilities for SKAI."""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

# Configure logging formats
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)

# Log levels
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def setup_logger(
    name: str,
    level: str = "info",
    log_file: Optional[str] = None,
    detailed: bool = False,
) -> logging.Logger:
    """Set up and configure a logger.

    Args:
        name: Name of the logger
        level: Log level (debug, info, warning, error, critical)
        log_file: Path to log file (if None, logs to console only)
        detailed: Whether to use detailed log format

    Returns:
        Configured logger instance
    """
    # Convert level string to logging level
    log_level = LOG_LEVELS.get(level.lower(), logging.INFO)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False  # Don't propagate to parent loggers

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Select format
    log_format = DETAILED_LOG_FORMAT if detailed else DEFAULT_LOG_FORMAT
    formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Create a default logger for the SKAI system
def get_skai_logger(
    module_name: str = "skai",
    level: str = "info",
    log_to_file: bool = False,
    detailed: bool = False,
) -> logging.Logger:
    """Get a logger for SKAI components.

    Args:
        module_name: Name of the module (will be prefixed with 'skai')
        level: Log level
        log_to_file: Whether to log to a file
        detailed: Whether to use detailed log format

    Returns:
        Configured logger
    """
    logger_name = f"skai.{module_name}" if module_name != "skai" else "skai"
    
    log_file = None
    if log_to_file:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Create a log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = f"logs/{logger_name.replace('.', '_')}_{timestamp}.log"
    
    return setup_logger(logger_name, level, log_file, detailed) 