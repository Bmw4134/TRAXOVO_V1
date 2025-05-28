
"""
TRAXOVO Fleet Management System - Full Intelligence Restored
All premium features now operational
"""

from flask import Flask, render_template, redirect, url_for
import os

# Import all premium route modules
from routes.smart_risk_analytics import smart_risk_bp
from routes.division_manager_access import division_manager_bp  
from routes.gps_validation import gps_validation_bp

# Create Flask app with full intelligence
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traxovo-full-intelligence")

# Register all premium blueprints
app.register_blueprint(smart_risk_bp)
app.register_blueprint(division_manager_bp)
app.register_blueprint(gps_validation_bp)

@app.route('/')
def index():
    """TRAXOVO main dashboard - full intelligence restored"""
    return render_template('intelligence_restored_dashboard.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "healthy", "app": "TRAXOVO Fleet Management", "intelligence": "fully_restored"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
