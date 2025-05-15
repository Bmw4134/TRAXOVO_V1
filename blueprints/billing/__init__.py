"""
Billing Blueprint

This module provides routes and functionality for equipment billing management, including:
- Monthly billing allocation review
- Billing comparison and approval workflow
- Region-based billing export generation
- Billing history tracking
"""

from flask import Blueprint, render_template, jsonify, request, current_app, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
import logging
import json
import os
from datetime import datetime, timedelta
import pandas as pd

from app import db
from models import Asset
from utils.reports import compare_billing_files, generate_region_billing_exports

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

@billing_bp.route('/')
@login_required
def index():
    """Render the main billing management dashboard."""
    return render_template('billing/index.html', 
                          title="Billing Management",
                          module="billing")

@billing_bp.route('/compare')
@login_required
def compare():
    """Render billing comparison page."""
    # Get comparison results
    comparison = compare_billing_files()
    
    return render_template('billing/compare.html', 
                          title="Billing Comparison",
                          module="billing",
                          comparison=comparison)

@billing_bp.route('/exports')
@login_required
def exports():
    """Render billing exports page."""
    # Get list of existing exports
    export_dir = 'exports/billings'
    exports = []
    
    if os.path.exists(export_dir):
        for date_dir in sorted(os.listdir(export_dir), reverse=True):
            date_path = os.path.join(export_dir, date_dir)
            if os.path.isdir(date_path):
                date_exports = []
                for export_file in os.listdir(date_path):
                    if export_file.endswith(('.xlsx', '.csv')):
                        date_exports.append({
                            'filename': export_file,
                            'path': os.path.join(date_path, export_file),
                            'size': os.path.getsize(os.path.join(date_path, export_file)),
                            'created': datetime.fromtimestamp(os.path.getctime(os.path.join(date_path, export_file)))
                        })
                if date_exports:
                    exports.append({
                        'date': date_dir,
                        'files': date_exports
                    })
    
    return render_template('billing/exports.html', 
                          title="Billing Exports",
                          module="billing",
                          exports=exports)

@billing_bp.route('/history')
@login_required
def history():
    """Render billing history page."""
    return render_template('billing/history.html', 
                          title="Billing History",
                          module="billing")

@billing_bp.route('/api/comparison')
@login_required
def api_comparison():
    """Get billing comparison data as JSON."""
    try:
        comparison = compare_billing_files()
        return jsonify(comparison)
    except Exception as e:
        logger.error(f"Error retrieving billing comparison: {e}")
        return jsonify({"error": str(e)}), 500

@billing_bp.route('/api/generate-exports', methods=['POST'])
@login_required
def api_generate_exports():
    """Generate region-based billing exports."""
    try:
        # Get approved changes from request
        approved_changes = request.json.get('approved_changes')
        
        # Generate exports
        result = generate_region_billing_exports(approved_changes)
        
        if result['status'] == 'success':
            flash('Billing exports generated successfully', 'success')
        else:
            flash(f'Error generating billing exports: {result.get("message", "Unknown error")}', 'error')
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error generating billing exports: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@billing_bp.route('/download/<path:filename>')
@login_required
def download_export(filename):
    """Download a billing export file."""
    try:
        # Construct full path
        file_path = os.path.join('exports/billings', filename)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            flash(f'File not found: {filename}', 'error')
            return redirect(url_for('billing.exports'))
            
        # Send file for download
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading export file: {e}")
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('billing.exports'))

def register_blueprint(app):
    """Register the billing blueprint with the app."""
    app.register_blueprint(billing_bp)
    return billing_bp