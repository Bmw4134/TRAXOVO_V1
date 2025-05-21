"""
PM Allocation Module

This module handles routes for PM allocation management and reconciliation.
"""

import os
import json
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the blueprint
pm_allocation_bp = Blueprint('pm_allocation', __name__, url_prefix='/billing')

@pm_allocation_bp.route('/pm-allocation-processor')
@login_required
def pm_allocation_processor():
    """Process PM allocation files"""
    return render_template('pm_allocation/processor.html')

@pm_allocation_bp.route('/auto-process-pm')
@login_required
def auto_process_pm():
    """Auto-detect and process PM allocation files"""
    return render_template('pm_allocation/auto_process.html')

@pm_allocation_bp.route('/pm-allocation-results')
@login_required
def pm_allocation_results():
    """Show PM allocation comparison results"""
    return render_template('pm_allocation/results.html')

@pm_allocation_bp.route('/pm-master-billing')
@login_required
def pm_master_billing():
    """PM Master Billing report"""
    return render_template('pm_allocation/master_billing.html')