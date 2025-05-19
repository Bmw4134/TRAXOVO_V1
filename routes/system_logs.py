"""
System Logs Module

This module provides routes for viewing system logs and monitoring the application.
"""

from flask import Blueprint, render_template, request, jsonify
from utils.structured_logger import get_log_entries
import os
from pathlib import Path

# Create blueprint
logs_bp = Blueprint('system_logs', __name__, url_prefix='/logs')

@logs_bp.route('/')
def index():
    """Display log viewer dashboard"""
    # Get list of available log files
    log_files = []
    log_dir = Path('logs')
    
    if log_dir.exists():
        for file in log_dir.glob('*.log'):
            log_files.append(file.name)
    
    # Default to error.log if it exists
    default_log = 'error.log' if 'error.log' in log_files else (log_files[0] if log_files else None)
    
    # Get selected log file from query params
    selected_log = request.args.get('log_file', default_log)
    max_entries = int(request.args.get('max_entries', 100))
    level = request.args.get('level')
    
    # Get log entries
    log_entries = []
    if selected_log:
        log_entries = get_log_entries(selected_log, max_entries, level)
    
    return render_template('logs/viewer.html', 
                          log_files=log_files,
                          selected_log=selected_log,
                          log_entries=log_entries,
                          max_entries=max_entries,
                          level=level)


@logs_bp.route('/api/entries')
def get_entries():
    """API endpoint for fetching log entries"""
    log_file = request.args.get('log_file', 'error.log')
    max_entries = int(request.args.get('max_entries', 100))
    level = request.args.get('level')
    
    entries = get_log_entries(log_file, max_entries, level)
    return jsonify(entries)


def register_blueprint(app):
    """Register the blueprint with the application"""
    app.register_blueprint(logs_bp)
    app.logger.info("Registered System Logs blueprint")