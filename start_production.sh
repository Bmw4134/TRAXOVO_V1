#!/bin/bash
# Production startup script for Cloud Run

# Set production environment variables
export FLASK_ENV=production
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Use PORT environment variable provided by Cloud Run, fallback to 5000
PORT=${PORT:-5000}

# Start gunicorn with production settings
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class sync \
    --timeout 120 \
    --keepalive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    main:app