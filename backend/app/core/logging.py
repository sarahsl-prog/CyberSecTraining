"""
Logging configuration using loguru.

This module provides a centralized logging setup for the entire application.
Each service/module can have its own log file while sharing a common format.

Usage:
    from app.core.logging import get_logger

    logger = get_logger("scanner")  # Creates/uses logs/scanner.log
    logger.info("Starting scan...")
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from app.config import settings


# Define the log directory relative to the backend folder
LOG_DIR = Path(__file__).parent.parent.parent / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Common log format for all loggers
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Simpler format for file logging (no color codes)
FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{name}:{function}:{line} | "
    "{message}"
)

# Track which loggers have been configured to avoid duplicates
_configured_loggers: set[str] = set()

# Flag to track if base logger has been set up
_base_configured = False


def setup_logging() -> None:
    """
    Initialize the base logging configuration.

    This should be called once at application startup. It configures:
    - Console output with colors (for development)
    - Main application log file

    Note: Individual service loggers are configured on-demand via get_logger().
    """
    global _base_configured

    if _base_configured:
        return

    # Remove default logger
    logger.remove()

    # Add console handler with color support
    logger.add(
        sys.stderr,
        format=LOG_FORMAT,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=settings.debug,
    )

    # Add main application log file
    logger.add(
        LOG_DIR / "app.log",
        format=FILE_FORMAT,
        level=settings.log_level,
        rotation="10 MB",      # Rotate when file reaches 10MB
        retention="5 days",    # Keep logs for 5 days
        compression="zip",     # Compress rotated logs
        backtrace=True,
        diagnose=settings.debug,
        enqueue=True,          # Thread-safe logging
    )

    _base_configured = True
    logger.info(f"Logging initialized. Log directory: {LOG_DIR}")


def get_logger(name: str, log_to_file: bool = True) -> "logger":
    """
    Get a logger instance for a specific module/service.

    Each named logger can optionally have its own dedicated log file.
    This is useful for separating logs from different services (e.g., scanner,
    vulnerability detector, LLM service) for easier debugging.

    Args:
        name: The name of the logger/module (e.g., "scanner", "llm", "api")
        log_to_file: Whether to create a dedicated log file for this logger

    Returns:
        A loguru logger instance bound to the given name

    Example:
        >>> logger = get_logger("scanner")
        >>> logger.info("Starting network scan")
        >>> # This logs to both console and logs/scanner.log
    """
    global _configured_loggers

    # Ensure base logging is configured
    if not _base_configured:
        setup_logging()

    # Create a bound logger with the module name
    bound_logger = logger.bind(name=name)

    # Add dedicated file handler if not already configured
    if log_to_file and name not in _configured_loggers:
        log_file = LOG_DIR / f"{name}.log"

        # Add file handler for this specific logger
        # Use filter to only log messages from this logger
        logger.add(
            log_file,
            format=FILE_FORMAT,
            level=settings.log_level,
            rotation="10 MB",
            retention="5 days",
            compression="zip",
            backtrace=True,
            diagnose=settings.debug,
            enqueue=True,
            filter=lambda record: record["extra"].get("name") == name,
        )

        _configured_loggers.add(name)
        bound_logger.info(f"Logger '{name}' initialized with file: {log_file}")

    return bound_logger


def log_function_call(func_name: str, **kwargs) -> None:
    """
    Utility to log function calls with parameters.

    Useful for audit logging and debugging.

    Args:
        func_name: Name of the function being called
        **kwargs: Parameters passed to the function
    """
    params = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    logger.debug(f"Calling {func_name}({params})")


class LogContext:
    """
    Context manager for adding contextual information to log messages.

    Usage:
        with LogContext(scan_id="abc123", target="192.168.1.0/24"):
            logger.info("Starting scan")  # Includes scan_id and target
    """

    def __init__(self, **context):
        """
        Initialize log context.

        Args:
            **context: Key-value pairs to add to log context
        """
        self.context = context
        self._token = None

    def __enter__(self):
        """Enter the context, binding context variables."""
        self._token = logger.contextualize(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        if self._token:
            self._token.__exit__(exc_type, exc_val, exc_tb)
        return False


# Specialized loggers for common use cases

def get_scanner_logger() -> "logger":
    """Get the logger for network scanning operations."""
    return get_logger("scanner")


def get_api_logger() -> "logger":
    """Get the logger for API operations."""
    return get_logger("api")


def get_vulnerability_logger() -> "logger":
    """Get the logger for vulnerability detection."""
    return get_logger("vulnerability")


def get_llm_logger() -> "logger":
    """Get the logger for LLM operations."""
    return get_logger("llm")


def get_audit_logger() -> "logger":
    """
    Get the audit logger for security-sensitive operations.

    This logger is specifically for audit trail purposes:
    - Network scans initiated
    - User consent acknowledgments
    - Data access events
    """
    return get_logger("audit")
