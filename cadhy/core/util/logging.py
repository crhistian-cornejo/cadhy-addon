"""
Logging Module
Logging utilities for CADHY addon.
"""

import logging
from enum import Enum
from typing import Optional


class LogLevel(Enum):
    """Log levels."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR


# Module-level logger
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """
    Get or create the CADHY logger.

    Returns:
        Logger instance
    """
    global _logger

    if _logger is None:
        _logger = logging.getLogger("CADHY")
        _logger.setLevel(logging.DEBUG)

        # Console handler
        if not _logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter("[CADHY] %(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            _logger.addHandler(handler)

    return _logger


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


def report_to_blender(operator, level: str, message: str) -> None:
    """
    Report message through Blender's reporting system.

    Args:
        operator: Blender operator instance
        level: Report level ('INFO', 'WARNING', 'ERROR')
        message: Message to report
    """
    operator.report({level}, f"[CADHY] {message}")


class OperationLogger:
    """Context manager for logging operations."""

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

    def __enter__(self):
        log_info(f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            log_error(f"Failed: {self.operation_name} - {exc_val}")
            if self.operator:
                report_to_blender(self.operator, "ERROR", f"{self.operation_name} failed: {exc_val}")
            return False

        if self.success:
            log_info(f"Completed: {self.operation_name}")
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
