"""
TRAXOVO ∞ Clarity Core - Production Deployment
Unified cinematic interface with QNIS enhancement
"""

# Import the main application with all QNIS endpoints
from app import app

# All routes are now properly imported from app.py

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)