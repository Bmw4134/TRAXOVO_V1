"""
TRAXOVO Main Application - QQ Enhanced
Primary entry point using app_qq_enhanced.py
"""

# Import the QQ enhanced application
from app_qq_enhanced import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)