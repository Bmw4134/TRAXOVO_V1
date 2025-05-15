"""
Maintenance Blueprint

This module provides routes and functionality for equipment maintenance management, including:
- Maintenance schedule tracking
- Work order management
- Maintenance cost analysis
- Preventive maintenance alerts
"""

from flask import Blueprint, render_template, jsonify, request, current_app, flash
from flask_login import login_required, current_user
import logging
import json
from datetime import datetime, timedelta
import pandas as pd

from app import db
from models import Asset, MaintenanceRecord
from gauge_api import get_asset_data

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')

@maintenance_bp.route('/')
@login_required
def index():
    """Render the main maintenance dashboard."""
    return render_template('maintenance/index.html', 
                          title="Maintenance Management",
                          module="maintenance")

@maintenance_bp.route('/analytics')
@login_required
def analytics():
    """Render maintenance analytics page."""
    return render_template('maintenance/analytics.html', 
                          title="Maintenance Analytics",
                          module="maintenance")

@maintenance_bp.route('/work-orders')
@login_required
def work_orders():
    """Render work orders management page."""
    return render_template('maintenance/work_orders.html', 
                          title="Work Orders",
                          module="maintenance")

@maintenance_bp.route('/roi')
@login_required
def roi():
    """Render maintenance ROI analysis page."""
    return render_template('maintenance/roi.html', 
                          title="Maintenance ROI",
                          module="maintenance")

@maintenance_bp.route('/api/work-orders')
@login_required
def api_work_orders():
    """Get work orders as JSON data."""
    try:
        # Placeholder for actual work order data
        work_orders = [
            {
                "id": 1,
                "asset_identifier": "EX-81",
                "service_type": "Preventive Maintenance",
                "service_date": "2025-05-10",
                "status": "Completed"
            },
            {
                "id": 2,
                "asset_identifier": "DT-11",
                "service_type": "Repair",
                "service_date": "2025-05-12",
                "status": "In Progress"
            },
            {
                "id": 3,
                "asset_identifier": "LP-116",
                "service_type": "Inspection",
                "service_date": "2025-05-15",
                "status": "Scheduled"
            }
        ]
        return jsonify(work_orders)
    except Exception as e:
        logger.error(f"Error retrieving work orders: {e}")
        return jsonify({"error": str(e)}), 500

def register_blueprint(app):
    """Register the maintenance blueprint with the app."""
    app.register_blueprint(maintenance_bp)
    return maintenance_bp