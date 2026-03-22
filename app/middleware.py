import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("http")

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured HTTP request/response logging."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Extract client IP (considering proxy headers if present)
        client_ip = request.client.host if request.client else "unknown"
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip()
        
        # Build log data
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", ""),
        }
        
        # Determine log level based on status code
        if response.status_code >= 500:
            logger.error("HTTP Request", extra=log_data)
        elif response.status_code >= 400:
            logger.warning("HTTP Request", extra=log_data)
        else:
            logger.info("HTTP Request", extra=log_data)
        
        return response
