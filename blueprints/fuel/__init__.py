"""
Fuel Blueprint

This module provides routes and functionality for fuel management and analytics, including:
- Fuel consumption tracking
- Fuel efficiency analysis
- Fuel card reconciliation
- Fuel cost analysis by equipment type
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
fuel_bp = Blueprint('fuel', __name__, url_prefix='/fuel')

@fuel_bp.route('/')
@login_required
def index():
    """Render the main fuel management dashboard."""
    return render_template('fuel/index.html', 
                          title="Fuel Management Dashboard",
                          module="fuel")

@fuel_bp.route('/analytics')
@login_required
def analytics():
    """Render fuel analytics page."""
    return render_template('fuel/analytics.html', 
                          title="Fuel Analytics",
                          module="fuel")

@fuel_bp.route('/reconciliation')
@login_required
def reconciliation():
    """Render fuel card reconciliation page."""
    return render_template('fuel/reconciliation.html', 
                          title="Fuel Card Reconciliation",
                          module="fuel")

@fuel_bp.route('/api/consumption')
@login_required
def api_consumption():
    """Get fuel consumption metrics as JSON data."""
    try:
        # Placeholder for actual fuel consumption data
        consumption = {
            "total_gallons": 18526.4,
            "total_cost": 74105.60,
            "average_price_per_gallon": 4.00,
            "by_category": [
                {"name": "Excavators", "gallons": 5236.8, "cost": 20947.20},
                {"name": "Dozers", "gallons": 4982.4, "cost": 19929.60},
                {"name": "Loaders", "gallons": 3622.2, "cost": 14488.80},
                {"name": "Trucks", "gallons": 4685.0, "cost": 18740.00}
            ]
        }
        return jsonify(consumption)
    except Exception as e:
        logger.error(f"Error retrieving fuel consumption data: {e}")
        return jsonify({"error": str(e)}), 500

def register_blueprint(app):
    """Register the fuel blueprint with the app."""
    app.register_blueprint(fuel_bp)
    return fuel_bp