"""
HTTP middleware for structured request/response logging.

This middleware:
- Generates or extracts request ID from X-Request-ID header
- Sets request context (request_id, client_ip) for the duration of the request
- Logs request start and response outcome with structured JSON
- Adds X-Request-ID to response headers
- Ensures context cleanup even on exceptions
- Uses the "audit" logger for security-sensitive events (wake operations)
"""

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .logging_config import (
    clear_context,
    get_audit_logger,
    get_http_logger,
    set_request_context,
)

logger = get_http_logger()
audit_logger = get_audit_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs HTTP requests and responses with structured JSON.
    Also provides request context (request_id, client_ip) to downstream code.
    """

    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", "").strip()
        if not request_id:
            request_id = str(uuid.uuid4())

        # Extract client IP (considering proxy headers if present)
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.headers.get("X-Real-IP", "")
        if not client_ip:
            client_ip = request.client.host if request.client else ""

        # Set context for this request
        set_request_context(request_id, client_ip)

        # Log request start
        try:
            logger.info(
                "request_started",
                method=request.method,
                url=str(request.url),
                path=request.url.path,
                query_params=dict(request.query_params),
                client_ip=client_ip,
            )
        except Exception as e:
            # Never let logging failures break the request
            logger.error("failed_to_log_request_start", error=str(e))

        try:
            # Process the request
            response = await call_next(request)

            # Log response outcome
            status_code = response.status_code
            log_level = "info" if status_code < 400 else "warning"

            try:
                logger.log(
                    log_level,
                    "request_completed",
                    status_code=status_code,
                    method=request.method,
                    path=request.url.path,
                )
            except Exception as e:
                logger.error("failed_to_log_response", error=str(e), status_code=status_code)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Audit log for wake endpoints (security-sensitive)
            if "/wake" in request.url.path:
                try:
                    audit_logger.info(
                        "wake_request",
                        request_id=request_id,
                        client_ip=client_ip,
                        method=request.method,
                        path=request.url.path,
                        status_code=status_code,
                    )
                except Exception as e:
                    logger.error("failed_to_audit_wake_request", error=str(e))

            return response

        except Exception as exc:
            # Log unhandled exceptions
            try:
                logger.error(
                    "request_failed",
                    error=str(exc),
                    method=request.method,
                    path=request.url.path,
                    exc_info=True,
                )
            except Exception as e:
                logger.error("failed_to_log_exception", error=str(e))

            # Still add request ID to error response if possible
            if isinstance(exc, Response):
                exc.headers["X-Request-ID"] = request_id

            raise

        finally:
            # Always clear context
            clear_context()
