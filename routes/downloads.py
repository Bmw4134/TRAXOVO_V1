"""
Routes for handling file downloads from the exports directory.
"""
from flask import Blueprint, render_template, send_from_directory, current_app
import os

# Create a blueprint for download routes
downloads_bp = Blueprint('downloads', __name__)

@downloads_bp.route('/downloads')
def download_page():
    """Render the download page"""
    return render_template('download.html')

@downloads_bp.route('/download/corrected')
def download_corrected():
    """Download the corrected PM allocations package"""
    exports_dir = 'exports'
    filename = 'CORRECTED_PM_ALLOCATIONS_PACKAGE_APRIL_2025.zip'
    return send_from_directory(
        os.path.join(current_app.root_path, exports_dir),
        filename,
        as_attachment=True
    )

@downloads_bp.route('/download/original')
def download_original():
    """Download the original PM allocations package"""
    exports_dir = 'exports'
    filename = 'PM_ALLOCATIONS_FINAL_PACKAGE_APRIL_2025.zip'
    return send_from_directory(
        os.path.join(current_app.root_path, exports_dir),
        filename,
        as_attachment=True
    )