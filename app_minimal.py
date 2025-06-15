"""
TRAXOVO Watson Intelligence Platform - Production Deployment
Complete system with driver and attendance modules using real data
"""

# Import the complete Watson Intelligence Platform
from watson_recovery import app

# For Cloud Run deployment - bind to port from environment
import os
port = int(os.environ.get('PORT', 8080))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=False)