"""
Fringe Blueprint

This module provides routes and functionality for fringe benefit management, including:
- Driver-to-pickup assignment tracking
- Fringe benefit calculation
- Company vehicle usage monitoring
- Compliance reporting
"""

from flask import Blueprint, render_template, jsonify, request, current_app, flash
from flask_login import login_required, current_user
import logging
import json
from datetime import datetime, timedelta
import pandas as pd

from app import db
from models import Asset
from gauge_api_legacy import get_asset_data

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
fringe_bp = Blueprint('fringe', __name__, url_prefix='/fringe')

@fringe_bp.route('/')
@login_required
def index():
    """Render the main fringe benefit management dashboard."""
    return render_template('fringe/index.html', 
                          title="Fringe Benefit Management",
                          module="fringe")

@fringe_bp.route('/assignments')
@login_required
def assignments():
    """Render driver-to-pickup assignments page."""
    return render_template('fringe/assignments.html', 
                          title="Driver-to-Pickup Assignments",
                          module="fringe")

@fringe_bp.route('/compliance')
@login_required
def compliance():
    """Render compliance reporting page."""
    return render_template('fringe/compliance.html', 
                          title="Fringe Compliance",
                          module="fringe")

@fringe_bp.route('/api/assignments')
@login_required
def api_assignments():
    """Get driver-to-pickup assignments as JSON data."""
    try:
        # Placeholder for actual driver assignment data
        assignments = [
            {
                "asset_identifier": "PT-275",
                "driver": "Open Position",
                "type": "Pickup Truck",
                "use_type": "Business Only",
                "start_date": "2025-01-01"
            },
            {
                "asset_identifier": "PT-276",
                "driver": "Mario Moya",
                "type": "Pickup Truck",
                "use_type": "Personal & Business",
                "start_date": "2025-01-01"
            },
            {
                "asset_identifier": "PT-277",
                "driver": "Said Garcia",
                "type": "Pickup Truck",
                "use_type": "Personal & Business",
                "start_date": "2025-01-01"
            }
        ]
        return jsonify(assignments)
    except Exception as e:
        logger.error(f"Error retrieving driver assignments: {e}")
        return jsonify({"error": str(e)}), 500

def register_blueprint(app):
    """Register the fringe blueprint with the app."""
    app.register_blueprint(fringe_bp)
    return fringe_bp