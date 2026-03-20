#!/bin/sh
set -e

# Wait for database to be ready (optional, for PostgreSQL)
# Until we have a proper health check, we'll just try a few times
if echo "$DB_URL" | grep -q "postgresql"; then
  echo "Waiting for database..."
  for i in $(seq 1 30); do
    python -c "import asyncpg; asyncpg.connect('$DB_URL')" && break
    echo "Database not ready yet, waiting..."
    sleep 1
  done
fi

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting Wake-on-LAN API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
