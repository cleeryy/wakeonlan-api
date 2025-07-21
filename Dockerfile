# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first for better Docker layer caching
# This means if requirements don't change, Docker can reuse this layer
COPY requirements.txt .

# Copy application code
COPY app/ ./app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

WORKDIR /app/app

# Command to run the application :
# uvicorn "main:app" --host $HOST_ADDR --port $HOST_PORT
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
