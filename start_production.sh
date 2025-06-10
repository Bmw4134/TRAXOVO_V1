#!/bin/bash
# Production startup script for Cloud Run

# Set production environment variables
export FLASK_ENV=production
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Use PORT environment variable provided by Cloud Run, fallback to 8080 (Cloud Run default)
PORT=${PORT:-8080}

echo "Starting application on port $PORT"

# Start gunicorn with Cloud Run optimized settings
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --worker-class sync \
    --timeout 300 \
    --keepalive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    main:app