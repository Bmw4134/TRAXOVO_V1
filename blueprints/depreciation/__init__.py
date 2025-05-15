"""
Depreciation & Lifecycle Blueprint

This module provides routes and functionality for asset depreciation and lifecycle management, including:
- Depreciation schedule tracking
- Net book value calculations
- Asset lifecycle analysis
- Acquisition and disposal tracking
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
depreciation_bp = Blueprint('depreciation', __name__, url_prefix='/depreciation')

@depreciation_bp.route('/')
@login_required
def index():
    """Render the main depreciation and lifecycle dashboard."""
    return render_template('depreciation/index.html', 
                          title="Depreciation & Lifecycle Management",
                          module="depreciation")

@depreciation_bp.route('/schedules')
@login_required
def schedules():
    """Render depreciation schedules page."""
    return render_template('depreciation/schedules.html', 
                          title="Depreciation Schedules",
                          module="depreciation")

@depreciation_bp.route('/acquisitions')
@login_required
def acquisitions():
    """Render acquisitions tracking page."""
    return render_template('depreciation/acquisitions.html', 
                          title="Asset Acquisitions",
                          module="depreciation")

@depreciation_bp.route('/disposals')
@login_required
def disposals():
    """Render asset disposals page."""
    return render_template('depreciation/disposals.html', 
                          title="Asset Disposals",
                          module="depreciation")

@depreciation_bp.route('/api/nbv')
@login_required
def api_nbv():
    """Get net book value data as JSON."""
    try:
        # Placeholder for actual NBV data
        nbv_data = {
            "total_original_cost": 12870000.00,
            "total_accumulated_depreciation": 4523000.00,
            "total_nbv": 8347000.00,
            "by_category": [
                {"name": "Excavators", "cost": 3254000.00, "accum_depr": 1127000.00, "nbv": 2127000.00},
                {"name": "Dozers", "cost": 2876000.00, "accum_depr": 982000.00, "nbv": 1894000.00},
                {"name": "Loaders", "cost": 2150000.00, "accum_depr": 752000.00, "nbv": 1398000.00},
                {"name": "Trucks", "cost": 4590000.00, "accum_depr": 1662000.00, "nbv": 2928000.00}
            ]
        }
        return jsonify(nbv_data)
    except Exception as e:
        logger.error(f"Error retrieving NBV data: {e}")
        return jsonify({"error": str(e)}), 500

def register_blueprint(app):
    """Register the depreciation blueprint with the app."""
    app.register_blueprint(depreciation_bp)