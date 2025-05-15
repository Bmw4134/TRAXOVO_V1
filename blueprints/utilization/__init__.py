"""
Utilization Blueprint

This module provides routes and functionality for equipment utilization analysis, including:
- Utilization metrics and tracking
- Idle time analysis
- Equipment efficiency monitoring
- Utilization cost impact analysis
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

@utilization_bp.route('/analysis')
@login_required
def analysis():
    """Render utilization analysis page."""
    return render_template('utilization/analysis.html', 
                          title="Utilization Analysis",
                          module="utilization")

@utilization_bp.route('/idle-time')
@login_required
def idle_time():
    """Render idle time analysis page."""
    return render_template('utilization/idle_time.html', 
                          title="Idle Time Analysis",
                          module="utilization")

@utilization_bp.route('/api/metrics')
@login_required
def api_metrics():
    """Get utilization metrics as JSON data."""
    try:
        # Get real asset data from database
        assets = Asset.query.all()
        
        # Calculate active equipment
        active_count = len([a for a in assets if a.active])
        
        # Calculate sample metrics (would be calculated from real data in production)
        metrics = {
            "average_utilization": 72.5,
            "active_equipment": active_count,
            "idle_time_percentage": 18.2,
            "total_engine_hours": 14523,
            "by_category": [
                {"name": "Excavators", "utilization": 81.3, "idle": 12.7},
                {"name": "Dozers", "utilization": 76.8, "idle": 14.5},
                {"name": "Loaders", "utilization": 68.4, "idle": 20.1},
                {"name": "Trucks", "utilization": 65.1, "idle": 22.8},
                {"name": "Other", "utilization": 58.7, "idle": 27.5}
            ]
        }
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error retrieving utilization metrics: {e}")
        return jsonify({"error": str(e)}), 500

def register_blueprint(app):
    """Register the utilization blueprint with the app."""
    app.register_blueprint(utilization_bp)
    return utilization_bp