"""Structured JSON logging setup using structlog (§6 of Shared Contracts)."""

import logging
import sys
import structlog
from typing import Optional
from datetime import datetime
import uuid


def get_request_id() -> str:
    """Get current request ID from context or generate new one."""
    return getattr(structlog.contextvars, "request_id", None) or str(uuid.uuid4())


def setup_json_logging(service_name: str, log_level: str = "INFO") -> None:
    """Configure structured JSON logging with structlog.

    Sets up logging to produce JSON output with these required fields:
    - timestamp: ISO 8601 UTC with milliseconds
    - level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    - service: Docker service name
    - request_id: UUID v4 for tracing
    - message: Human-readable log message
    - logger: Python module path

    Args:
        service_name: Docker service name (e.g., 'api-gateway', 'rag-service')
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
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

    # Configure Python logging for root logger
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(),
                    "foreign_pre_chain": [
                        structlog.stdlib.add_logger_name,
                        structlog.stdlib.add_log_level,
                        structlog.processors.TimeStamper(fmt="iso"),
                    ],
                },
            },
            "handlers": {
                "default": {
                    "level": log_level,
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": log_level,
                    "propagate": True,
                },
            },
        }
    )

    # Get root logger and add service name to context
    logger = structlog.get_logger()
    logger = logger.bind(service=service_name)


def get_logger(name: str, request_id: Optional[str] = None) -> structlog.BoundLogger:
    """Get a logger instance bound with service context.

    Args:
        name: Logger name (usually __name__)
        request_id: Optional request ID for tracing

    Returns:
        Bound logger instance with service context
    """
    logger = structlog.get_logger(name)

    # Bind request_id if provided
    if request_id:
        logger = logger.bind(request_id=request_id)

    return logger


def log_with_context(
    logger: structlog.BoundLogger,
    level: str,
    message: str,
    request_id: Optional[str] = None,
    **extra: dict,
) -> None:
    """Log with automatic request ID and context.

    Args:
        logger: Bound logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        request_id: Optional request ID
        **extra: Additional context fields
    """
    if request_id:
        logger = logger.bind(request_id=request_id)

    log_func = getattr(logger, level.lower())
    log_func(message, **extra)


# FastAPI integration helper
class LoggingMiddleware:
    """FastAPI middleware for automatic request logging.

    Logs all incoming requests with method, path, status code, and duration.
    """

    def __init__(self, app: any, service_name: str):
        """Initialize middleware.

        Args:
            app: FastAPI application
            service_name: Service name for context
        """
        self.app = app
        self.service_name = service_name

    async def __call__(self, scope: dict, receive: any, send: any) -> None:
        """ASGI middleware handler."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = self._get_request_id(scope)
        logger = structlog.get_logger(__name__).bind(
            request_id=request_id,
            service=self.service_name,
        )

        # Store request ID in context for downstream use
        scope["request_id"] = request_id

        await self.app(scope, receive, send)

    @staticmethod
    def _get_request_id(scope: dict) -> str:
        """Extract request ID from headers or generate new one."""
        headers = scope.get("headers", [])
        for header_name, header_value in headers:
            if header_name.lower() == b"x-request-id":
                return header_value.decode()
        return str(uuid.uuid4())
