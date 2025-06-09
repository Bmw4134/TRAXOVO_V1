"""
TRAXOVO ∞ Executive Deployment Module
Production-ready deployment wrapper for main application
"""

from main import app

# Export the Flask app for gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)