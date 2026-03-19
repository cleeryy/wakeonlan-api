"""
Structured JSON logging configuration with request context.

This module provides:
- Context variables for request-scoped data (request_id, client_ip)
- Custom processors to inject context into log entries
- Helper functions for managing request context
- Structlog configuration for JSON output to stdout
"""

import contextvars
import sys
import uuid
from typing import Any, Dict

import structlog
from structlog.processors import TimeStamper
from structlog.stdlib import BoundLogger
from structlog.typing import EventDict, Processor


# Context variables for request-scoped data
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
client_ip_var: contextvars.ContextVar[str] = contextvars.ContextVar("client_ip", default="")


def add_request_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Processor that adds request_id and client_ip from context vars to the event dict.
    """
    try:
        request_id = request_id_var.get()
        if request_id:
            event_dict["request_id"] = request_id
    except LookupError:
        pass

    try:
        client_ip = client_ip_var.get()
        if client_ip:
            event_dict["client_ip"] = client_ip
    except LookupError:
        pass

    return event_dict


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def set_request_context(request_id: str, client_ip: str = "") -> None:
    """
    Set request context variables.
    Call this at the beginning of a request.
    """
    request_id_var.set(request_id)
    client_ip_var.set(client_ip)


def clear_context() -> None:
    """Clear all request context variables."""
    try:
        request_id_var.set("")
    except LookupError:
        pass
    try:
        client_ip_var.set("")
    except LookupError:
        pass


def configure_logging() -> None:
    """Configure structlog for JSON output to stdout."""
    shared_processors: list[Processor] = [
        add_request_context,
        TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=shared_processors + [structlog.processors.JSONRenderer()],
        wrapper_class=BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Set up standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


# Convenience logger getters
def get_http_logger() -> BoundLogger:
    """Get logger for HTTP request/response logging."""
    return structlog.get_logger("http")


def get_audit_logger() -> BoundLogger:
    """Get logger for security/audit events (e.g., wake events)."""
    return structlog.get_logger("audit")


def get_application_logger() -> BoundLogger:
    """Get general application logger."""
    return structlog.get_logger("app")


# Auto-configure on import
configure_logging()
