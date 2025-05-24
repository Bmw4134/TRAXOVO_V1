"""
TRAXORA Fleet Management System - System Admin Routes

This module provides routes for system administration tasks, including
full-stack synchronization checks and system health monitoring.
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from utils.full_stack_sync_scanner import run_scan

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
system_admin_bp = Blueprint('system_admin', __name__, url_prefix='/admin')

@system_admin_bp.route('/')
def index():
    """System admin dashboard"""
    return render_template('system_admin/index.html')

@system_admin_bp.route('/sync-check')
def sync_check():
    """Run a full-stack sync check and display results"""
    try:
        # Run the sync scanner
        results = run_scan()
        
        # Get the report data
        report = results['report']
        html_report = results['html_report']
        
        # Render the sync check page with the report data
        return render_template('system_admin/sync_check.html', 
                              report=report,
                              html_report_url=html_report['url'],
                              timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Error running sync check: {str(e)}")
        flash(f"Error running sync check: {str(e)}", "danger")
        return redirect(url_for('system_admin.index'))

@system_admin_bp.route('/database-check')
def database_check():
    """Check database integrity and display results"""
    # This will be implemented in a future update
    flash("Database integrity check will be available in a future update.", "info")
    return redirect(url_for('system_admin.index'))

@system_admin_bp.route('/run-kaizen-sync-test')
def run_kaizen_sync_test():
    """Run the Kaizen sync test script"""
    try:
        import kaizen_sync_tester
        kaizen_sync_tester.run_tests()
        flash("Kaizen sync test completed successfully.", "success")
    except Exception as e:
        logger.error(f"Error running Kaizen sync test: {str(e)}")
        flash(f"Error running Kaizen sync test: {str(e)}", "danger")
    
    return redirect(url_for('system_admin.index'))