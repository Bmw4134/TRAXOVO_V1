"""
Reports routes for the SYSTEMSMITH application.

This module handles the routes related to generating and accessing reports.
"""
import os
import logging
import json
from datetime import datetime
from flask import Blueprint, render_template, request, send_file, jsonify
from flask_login import login_required

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the reports blueprint
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
def index():
    """Reports landing page with links to all available reports."""
    return render_template('reports/index.html', title='Reports', datetime=datetime)

@reports_bp.route('/driver-reports')
@login_required
def driver_reports():
    """List all available driver reports."""
    return render_template('reports/driver_reports.html', title='Driver Reports')

@reports_bp.route('/download/<path:report_path>')
@login_required
def download_report(report_path):
    """Download a specific report file."""
    try:
        # Check if the file exists
        if not os.path.exists(report_path):
            logger.error(f"Report file not found: {report_path}")
            return render_template('error.html', error=f"Report file not found: {report_path}"), 404
        
        # Return the file for download
        return send_file(report_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        return render_template('error.html', error=str(e)), 500

@reports_bp.route('/download-export/<path:export_path>')
@login_required
def download_export(export_path):
    """Download a specific export file."""
    try:
        # Check if the file exists
        if not os.path.exists(export_path):
            logger.error(f"Export file not found: {export_path}")
            return render_template('error.html', error=f"Export file not found: {export_path}"), 404
        
        # Return the file for download
        return send_file(export_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading export: {e}")
        return render_template('error.html', error=str(e)), 500

@reports_bp.route('/view/<path:report_path>')
@login_required
def view_report(report_path):
    """View a specific report file in-browser."""
    try:
        # Check if the file exists
        if not os.path.exists(report_path):
            logger.error(f"Report file not found: {report_path}")
            return render_template('error.html', error=f"Report file not found: {report_path}"), 404
        
        # TODO: Implement file viewing based on file type
        return render_template('reports/view_report.html', report_path=report_path)
    except Exception as e:
        logger.error(f"Error viewing report: {e}")
        return render_template('error.html', error=str(e)), 500

@reports_bp.route('/daily-driver')
@login_required
def daily_driver_report():
    """Generate daily driver reports (Late Start, Early End, Not On Job)."""
    try:
        return render_template('reports/daily_driver.html', title='Daily Driver Report')
    except Exception as e:
        logger.error(f"Error in daily driver report: {e}")
        return render_template('error.html', error=str(e)), 500