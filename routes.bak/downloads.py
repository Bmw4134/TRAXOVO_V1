"""
Routes for handling file downloads from the exports directory.
"""
from flask import Blueprint, render_template, send_from_directory, current_app, abort
import os
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Create a blueprint for download routes
downloads_bp = Blueprint('downloads', __name__, url_prefix='/downloads')

@downloads_bp.route('/')
def download_page():
    """Render the download page"""
    return render_template('download.html')

@downloads_bp.route('/daily-reports/<path:filename>')
def download_daily_report(filename):
    """Download a daily report file"""
    try:
        reports_dir = os.path.join(current_app.root_path, 'exports/daily_reports')
        return send_from_directory(directory=reports_dir, path=filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        abort(404)

@downloads_bp.route('/corrected')
def download_corrected():
    """Download the corrected PM allocations package"""
    exports_dir = 'exports'
    filename = 'CORRECTED_PM_ALLOCATIONS_PACKAGE_APRIL_2025.zip'
    return send_from_directory(
        os.path.join(current_app.root_path, exports_dir),
        filename,
        as_attachment=True
    )

@downloads_bp.route('/original')
def download_original():
    """Download the original PM allocations package"""
    exports_dir = 'exports'
    filename = 'PM_ALLOCATIONS_FINAL_PACKAGE_APRIL_2025.zip'
    return send_from_directory(
        os.path.join(current_app.root_path, exports_dir),
        filename,
        as_attachment=True
    )