"""
TRAXOVO Enterprise Automation Platform - Main Entry Point
Complete end-to-end business automation system for Troy
"""

from troy_automation_nexus import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)