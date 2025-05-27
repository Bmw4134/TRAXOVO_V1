"""
Job Module - Job Site Management and Operations
Track job sites, assignments, and operational metrics
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import json
import os
import logging
from datetime import datetime, timedelta

job_module_bp = Blueprint('job_module', __name__)
logger = logging.getLogger(__name__)

@job_module_bp.route('/jobs')
def job_dashboard():
    """Main job management dashboard"""
    try:
        return render_template('job_dashboard.html')
    except Exception as e:
        logger.error(f"Error loading job dashboard: {e}")
        flash('Error loading job dashboard', 'error')
        return redirect(url_for('index'))

@job_module_bp.route('/jobs/active')
def active_jobs():
    """Active job sites listing"""
    try:
        return render_template('active_jobs.html')
    except Exception as e:
        logger.error(f"Error loading active jobs: {e}")
        flash('Error loading active jobs', 'error')
        return redirect(url_for('job_module.job_dashboard'))

@job_module_bp.route('/jobs/assignments')
def job_assignments():
    """Job assignments and scheduling"""
    try:
        return render_template('job_assignments.html')
    except Exception as e:
        logger.error(f"Error loading job assignments: {e}")
        flash('Error loading job assignments', 'error')
        return redirect(url_for('job_module.job_dashboard'))

@job_module_bp.route('/jobs/performance')
def job_performance():
    """Job performance metrics and analytics"""
    try:
        return render_template('job_performance.html')
    except Exception as e:
        logger.error(f"Error loading job performance: {e}")
        flash('Error loading job performance', 'error')
        return redirect(url_for('job_module.job_dashboard'))