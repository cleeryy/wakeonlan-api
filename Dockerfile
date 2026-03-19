# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY entrypoint.sh ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make entrypoint script executable
RUN chmod +x ./entrypoint.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

WORKDIR /app/app

# Use entrypoint to run migrations before starting
ENTRYPOINT ["/app/entrypoint.sh"]
