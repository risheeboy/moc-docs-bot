"""JSON logging configuration for structured logging."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import structlog


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON-structured logs."""

    def __init__(self, service_name: str):
        """Initialize JSON formatter.

        Args:
            service_name: Name of the service for logging context
        """
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request ID if available
        if hasattr(record, "request_id") and record.request_id:
            log_data["request_id"] = record.request_id

        # Add extra fields
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


class StructuredLogger:
    """Wrapper around structlog for consistent logging."""

    def __init__(self, logger: structlog.BoundLogger):
        """Initialize structured logger.

        Args:
            logger: The underlying structlog logger
        """
        self.logger = logger

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **(extra or {}), **kwargs)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message."""
        self.logger.info(message, **(extra or {}), **kwargs)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **(extra or {}), **kwargs)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False, **kwargs):
        """Log error message."""
        self.logger.error(message, **(extra or {}), exc_info=exc_info, **kwargs)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **(extra or {}), **kwargs)


def setup_json_logging(service_name: str) -> StructuredLogger:
    """Setup JSON structured logging.

    Args:
        service_name: Name of the service

    Returns:
        Configured structured logger
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Setup standard logging handler
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    logger.handlers = []

    # Add JSON formatter to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter(service_name))
    logger.addHandler(handler)

    # Get structlog logger
    struct_logger = structlog.get_logger(service_name)
    return StructuredLogger(struct_logger)
