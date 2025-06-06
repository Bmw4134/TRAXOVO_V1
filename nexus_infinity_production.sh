#!/bin/bash
# NEXUS Infinity Production Server Startup

echo "Starting NEXUS Infinity Production Server..."
echo "System: Linux"
echo "Deployment: Local Server Production Mode"

export NEXUS_INFINITY_MODE=PRODUCTION
export FLASK_ENV=production

# Start production server
gunicorn --bind 0.0.0.0:5000 \
         --workers 4 \
         --timeout 120 \
         --preload \
         --max-requests 1000 \
         --max-requests-jitter 100 \
         main:app

echo "NEXUS Infinity Production Server Started"
