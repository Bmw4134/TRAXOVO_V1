"""
Main routes for the SYSTEMSMITH application
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
import os
from pathlib import Path

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main dashboard page"""
    # Sample data for dashboard display
    asset_count = 278
    late_starts_count = 12
    early_ends_count = 5
    not_on_job_count = 3
    last_sync_time = "11:30 AM"
    db_connected = True
    api_online = True
    
    return render_template('index.html',
                          asset_count=asset_count,
                          late_starts_count=late_starts_count,
                          early_ends_count=early_ends_count,
                          not_on_job_count=not_on_job_count,
                          last_sync_time=last_sync_time,
                          db_connected=db_connected,
                          api_online=api_online)

@main_bp.route('/assets')
@login_required
def assets():
    """Render the assets page"""
    return render_template('assets.html')

# Add more routes as needed from main.py