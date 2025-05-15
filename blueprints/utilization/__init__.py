"""
Utilization Blueprint

This module provides routes and functionality for equipment utilization analytics, including:
- Utilization rate calculations
- Equipment efficiency metrics
- Utilization vs. cost analysis
- Idle time tracking
"""

from flask import Blueprint, render_template, jsonify, request, current_app, flash
from flask_login import login_required, current_user
import logging
import json
from datetime import datetime, timedelta
import pandas as pd

from app import db
from models import Asset
from gauge_api import get_asset_data

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
utilization_bp = Blueprint('utilization', __name__, url_prefix='/utilization')

@utilization_bp.route('/')
@login_required
def index():
    """Render the main utilization dashboard."""
    return render_template('utilization/index.html', 
                          title="Equipment Utilization Dashboard",
                          module="utilization")

@utilization_bp.route('/metrics')
@login_required
def metrics():
    """Get utilization metrics as JSON data."""
    try:
        # Placeholder for actual utilization metrics calculation
        metrics = {
            "average_utilization": 72.5,
            "idle_time_percentage": 18.2,
            "total_engine_hours": 14523,
            "by_category": [
                {"name": "Excavators", "utilization": 81.3},
                {"name": "Dozers", "utilization": 76.8},
                {"name": "Loaders", "utilization": 68.4},
                {"name": "Trucks", "utilization": 65.1}
            ]
        }
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error calculating utilization metrics: {e}")
        return jsonify({"error": str(e)}), 500

def register_blueprint(app):
    """Register the utilization blueprint with the app."""
    app.register_blueprint(utilization_bp)