"""
Logging Module
Enhanced logging utilities for CADHY addon with file rotation support.
Similar to BlenderGIS and Sverchok logging patterns.
"""

import logging
import os
import sys
from enum import Enum
from logging.handlers import RotatingFileHandler
from typing import Optional

# Module-level logger
_logger: Optional[logging.Logger] = None
_file_handler: Optional[RotatingFileHandler] = None
_initialized: bool = False

# Log directory and file paths
LOG_DIR = os.path.join(os.path.expanduser("~"), ".cadhy")
LOG_FILE = os.path.join(LOG_DIR, "cadhy.log")
LOG_MAX_BYTES = 500_000  # 500KB per file
LOG_BACKUP_COUNT = 3


class LogLevel(Enum):
    """Log levels."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR


def _ensure_log_directory() -> bool:
    """Ensure log directory exists.

    Returns:
        True if directory exists or was created, False on error.
    """
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        return True
    except OSError as e:
        print(f"[CADHY] Warning: Could not create log directory: {e}")
        return False


def setup_logging(log_level: str = "INFO", log_to_file: bool = True, max_files: int = 3) -> logging.Logger:
    """
    Initialize or reconfigure CADHY logging.

    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to write logs to file
        max_files: Maximum number of log backup files

    Returns:
        Configured logger instance
    """
    global _logger, _file_handler, _initialized

    if _logger is None:
        _logger = logging.getLogger("CADHY")
        _logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level
        _logger.propagate = False  # Don't propagate to root logger

    # Get numeric log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Console handler (always present)
    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in _logger.handlers
    ):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(logging.Formatter("[CADHY] %(levelname)s: %(message)s"))
        _logger.addHandler(console_handler)
    else:
        # Update existing console handler level
        for h in _logger.handlers:
            if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler):
                h.setLevel(numeric_level)

    # File handler (optional)
    if log_to_file:
        if _file_handler is None and _ensure_log_directory():
            try:
                _file_handler = RotatingFileHandler(
                    LOG_FILE,
                    maxBytes=LOG_MAX_BYTES,
                    backupCount=max_files,
                    encoding="utf-8",
                )
                _file_handler.setLevel(logging.DEBUG)  # Capture everything to file
                _file_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                    )
                )
                _logger.addHandler(_file_handler)
            except OSError as e:
                print(f"[CADHY] Warning: Could not create log file handler: {e}")
    elif _file_handler is not None:
        # Remove file handler if disabled
        _logger.removeHandler(_file_handler)
        _file_handler.close()
        _file_handler = None

    _initialized = True
    return _logger


def get_logger() -> logging.Logger:
    """
    Get or create the CADHY logger.

    Returns:
        Logger instance
    """
    global _logger

    if _logger is None or not _initialized:
        # Initialize with defaults, will be reconfigured when preferences are loaded
        setup_logging()

    return _logger


def reconfigure_from_preferences() -> None:
    """Reconfigure logging based on addon preferences.

    Call this after Blender fully initializes and preferences are available.
    """
    try:
        import bpy

        addon = bpy.context.preferences.addons.get("cadhy")
        if addon and addon.preferences:
            prefs = addon.preferences
            setup_logging(
                log_level=prefs.log_level,
                log_to_file=prefs.log_to_file,
                max_files=prefs.log_max_files,
            )
            log_debug("Logging reconfigured from preferences")
    except Exception:
        # Preferences not available yet, use defaults
        pass


def log_debug(message: str) -> None:
    """Log debug message."""
    get_logger().debug(message)


def log_info(message: str) -> None:
    """Log info message."""
    get_logger().info(message)


def log_warning(message: str) -> None:
    """Log warning message."""
    get_logger().warning(message)


def log_error(message: str) -> None:
    """Log error message."""
    get_logger().error(message)


def log_exception(message: str) -> None:
    """Log error message with exception traceback."""
    get_logger().exception(message)


def report_to_blender(operator, level: str, message: str) -> None:
    """
    Report message through Blender's reporting system.

    Args:
        operator: Blender operator instance
        level: Report level ('INFO', 'WARNING', 'ERROR')
        message: Message to report
    """
    operator.report({level}, f"[CADHY] {message}")

    # Also log to file
    log_func = {
        "INFO": log_info,
        "WARNING": log_warning,
        "ERROR": log_error,
    }.get(level, log_info)
    log_func(f"Blender Report: {message}")


class OperationLogger:
    """Context manager for logging operations with timing and error handling."""

    def __init__(self, operation_name: str, operator=None):
        """
        Initialize operation logger.

        Args:
            operation_name: Name of the operation
            operator: Optional Blender operator for reporting
        """
        self.operation_name = operation_name
        self.operator = operator
        self.success = False
        self.message = ""
        self._start_time = None

    def __enter__(self):
        import time

        self._start_time = time.time()
        log_info(f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        elapsed = time.time() - self._start_time if self._start_time else 0

        if exc_type is not None:
            log_error(f"Failed: {self.operation_name} - {exc_val} (after {elapsed:.2f}s)")
            log_exception(f"Exception details for {self.operation_name}")
            if self.operator:
                report_to_blender(self.operator, "ERROR", f"{self.operation_name} failed: {exc_val}")
            return False

        if self.success:
            log_info(f"Completed: {self.operation_name} ({elapsed:.2f}s)")
            if self.operator and self.message:
                report_to_blender(self.operator, "INFO", self.message)

        return False

    def set_success(self, message: str = "") -> None:
        """Mark operation as successful."""
        self.success = True
        self.message = message or f"{self.operation_name} completed successfully"

    def set_warning(self, message: str) -> None:
        """Log a warning during operation."""
        log_warning(f"{self.operation_name}: {message}")
        if self.operator:
            report_to_blender(self.operator, "WARNING", message)


def get_log_file_path() -> str:
    """Get the path to the log file.

    Returns:
        Path to cadhy.log file
    """
    return LOG_FILE


def get_log_file_contents(max_lines: int = 100) -> str:
    """Get the last N lines from the log file.

    Args:
        max_lines: Maximum number of lines to return

    Returns:
        Log file contents as string
    """
    if not os.path.exists(LOG_FILE):
        return "Log file not found"

    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            lines = f.readlines()
            return "".join(lines[-max_lines:])
    except OSError as e:
        return f"Could not read log file: {e}"
