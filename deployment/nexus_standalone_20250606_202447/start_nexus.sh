#!/bin/bash
# NEXUS Standalone Startup Script

echo "Starting NEXUS Intelligent Automation Platform..."

# Set environment variables
export FLASK_APP=main.py
export FLASK_ENV=production

# Install dependencies
pip install -r requirements_standalone.txt

# Initialize database
python3 -c "from app_nexus import db; db.create_all()"

# Start the application
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 main:app
