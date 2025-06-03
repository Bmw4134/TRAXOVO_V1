"""
TRAXORA Dashboard Application - Standalone Version
"""

import logging
import os
from flask import Flask, render_template, redirect, url_for, jsonify
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24))

# Import the dashboard blueprint
from routes.dashboard import dashboard_bp

# Register the dashboard blueprint
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

# Main route - redirect to dashboard
@app.route('/')
def index():
    """Redirect to the enhanced dashboard"""
    return redirect(url_for('dashboard.dashboard_v2'))

# Assets API route for the map
@app.route('/api/assets', methods=['GET'])
def api_assets():
    """Return mock asset data for the map"""
    # Sample asset locations
    asset_locations = [
        {'id': 'EX-65', 'type': 'Excavator', 'lat': 32.7865, 'lng': -96.7986, 'job': '2024-019'},
        {'id': 'EX-74', 'type': 'Excavator', 'lat': 32.7516, 'lng': -96.8339, 'job': '2023-032'},
        {'id': 'LD-45', 'type': 'Loader', 'lat': 32.8075, 'lng': -96.8148, 'job': '2024-016'},
        {'id': 'DZ-31', 'type': 'Dozer', 'lat': 32.7641, 'lng': -96.7596, 'job': '2023-034'},
        {'id': 'TK-103', 'type': 'Truck', 'lat': 32.7972, 'lng': -96.8192, 'job': '2024-025'}
    ]
    return jsonify(asset_locations)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)