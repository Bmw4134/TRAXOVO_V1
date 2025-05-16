"""
SYSTEMSMITH - Fleet Management and Reporting System

This file initializes the application and contains the entry point for the server.
"""
import os
import logging
from minimal import app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# The app is now imported directly from minimal.py

if __name__ == "__main__":
    # Development server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)