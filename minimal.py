#!/usr/bin/env python

"""
TRAXORA: Simplified Fleet Management Dashboard
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24))

# Data Storage (in-memory for demo)
assets = []
driver_reports = []

# Load sample data
def load_sample_data():
    """Load sample data for demonstration"""
    global assets, driver_reports
    
    # Sample assets
    assets = [
        {"id": 1, "name": "Truck 101", "status": "Active", "location": {"lat": 32.7767, "lng": -96.7970}, "type": "Truck"},
        {"id": 2, "name": "Excavator 202", "status": "Maintenance", "location": {"lat": 32.7801, "lng": -96.8003}, "type": "Heavy Equipment"},
        {"id": 3, "name": "Dozer 305", "status": "Active", "location": {"lat": 32.7665, "lng": -96.7799}, "type": "Heavy Equipment"},
        {"id": 4, "name": "Pickup 422", "status": "Active", "location": {"lat": 32.7977, "lng": -96.7966}, "type": "Light Vehicle"},
        {"id": 5, "name": "Crane 518", "status": "Inactive", "location": {"lat": 32.7873, "lng": -96.8075}, "type": "Heavy Equipment"}
    ]
    
    # Sample driver reports
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    driver_reports = [
        {"id": 1, "driver_name": "John Smith", "status": "LATE START", "job_site": "Project Alpha", "expected_start": yesterday.replace(hour=7, minute=0), "actual_start": yesterday.replace(hour=7, minute=45), "minutes_late": 45},
        {"id": 2, "driver_name": "Emma Johnson", "status": "EARLY END", "job_site": "Project Beta", "expected_end": yesterday.replace(hour=16, minute=0), "actual_end": yesterday.replace(hour=15, minute=15), "minutes_early": 45},
        {"id": 3, "driver_name": "Robert Davis", "status": "NOT ON JOB", "expected_job": "Project Charlie", "actual_job": "Project Delta", "time": yesterday.replace(hour=10, minute=30)},
        {"id": 4, "driver_name": "Sarah Wilson", "status": "LATE START", "job_site": "Project Echo", "expected_start": yesterday.replace(hour=7, minute=0), "actual_start": yesterday.replace(hour=7, minute=30), "minutes_late": 30},
        {"id": 5, "driver_name": "Michael Brown", "status": "EARLY END", "job_site": "Project Foxtrot", "expected_end": yesterday.replace(hour=16, minute=0), "actual_end": yesterday.replace(hour=15, minute=0), "minutes_early": 60},
    ]

# Home/Dashboard
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html', 
                          assets=assets,
                          asset_count=len(assets),
                          active_count=sum(1 for a in assets if a["status"] == "Active"),
                          maintenance_count=sum(1 for a in assets if a["status"] == "Maintenance"),
                          inactive_count=sum(1 for a in assets if a["status"] == "Inactive"))

# Daily Report
@app.route('/daily_report')
def daily_report():
    """Daily driver report page"""
    # Count incidents by type
    late_starts = [r for r in driver_reports if r["status"] == "LATE START"]
    early_ends = [r for r in driver_reports if r["status"] == "EARLY END"]
    not_on_job = [r for r in driver_reports if r["status"] == "NOT ON JOB"]
    total_records = len(driver_reports)
    on_time = total_records - (len(late_starts) + len(early_ends) + len(not_on_job))
    
    # Get yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    
    return render_template('daily_report.html',
                          report_date=yesterday,
                          total_records=total_records,
                          late_starts=len(late_starts),
                          early_ends=len(early_ends),
                          not_on_job=len(not_on_job),
                          on_time=on_time,
                          late_start_records=late_starts,
                          early_end_records=early_ends,
                          not_on_job_records=not_on_job)

# PM Allocation
@app.route('/pm_allocation')
def pm_allocation():
    """PM Allocation processor page"""
    return render_template('pm_allocation.html', 
                          recent_reports=[])

# Assets List
@app.route('/assets')
def assets_list():
    """Display list of all assets"""
    return render_template('assets.html', 
                          assets=assets)

# Asset Detail
@app.route('/asset/<int:asset_id>')
def asset_detail(asset_id):
    """Display details for a single asset"""
    asset = next((a for a in assets if a["id"] == asset_id), None)
    if not asset:
        return "Asset not found", 404
    return render_template('asset_detail.html', 
                          asset=asset)

# Load sample data when server starts
load_sample_data()

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)