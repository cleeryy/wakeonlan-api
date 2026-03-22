# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first for better Docker layer caching
# This means if requirements don't change, Docker can reuse this layer
COPY requirements.txt .

# Copy application code
COPY app/ ./app/
COPY tests/ ./tests/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script and make executable before switching to non-root user
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

WORKDIR /app/app

# Health check to ensure service is responding
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8080}/health')"

ENTRYPOINT ["docker-entrypoint.sh"]
