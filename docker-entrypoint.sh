#!/bin/sh
set -e

# Set default values if not provided
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"

# Execute uvicorn with the configured host and port
exec uvicorn main:app --host "$HOST" --port "$PORT"
