"""
TRAXOVO Fleet Management System - Minimal Deployment Core
Lightweight version for successful deployment with full restoration capability
"""

from flask import Flask, render_template, redirect, url_for
import os

# Create minimal Flask app for deployment
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traxovo-deployment-key")

@app.route('/')
def index():
    """TRAXOVO main dashboard - minimal deployment version"""
    return render_template('minimal_dashboard.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "healthy", "app": "TRAXOVO Fleet Management", "version": "minimal-core"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)