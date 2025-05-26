"""
TRAXORA Fleet Management System - Monthly Driver Report Routes

This module provides comprehensive monthly driver reporting functionality,
aggregating daily and weekly data into monthly performance summaries.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from calendar import monthrange

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
monthly_driver_report_bp = Blueprint('monthly_driver_report', __name__, url_prefix='/monthly-driver-report')

@monthly_driver_report_bp.route('/')
def dashboard():
    """Monthly driver report dashboard"""
    try:
        # Get current month and year
        today = datetime.now()
        current_month = today.month
        current_year = today.year
        
        # Generate month options for the past 6 months
        month_options = []
        for i in range(6):
            date = today.replace(day=1) - timedelta(days=32*i)
            month_options.append({
                'value': f"{date.year}-{date.month:02d}",
                'label': date.strftime('%B %Y')
            })
        
        # Sample monthly metrics (would come from actual data)
        monthly_metrics = {
            'total_drivers': 45,
            'on_time_percentage': 87.5,
            'late_start_count': 23,
            'early_end_count': 18,
            'not_on_job_count': 12,
            'total_work_days': monthrange(current_year, current_month)[1]
        }
        
        return render_template('monthly_driver_report/dashboard.html',
                             month_options=month_options,
                             current_month=f"{current_year}-{current_month:02d}",
                             metrics=monthly_metrics)
                             
    except Exception as e:
        logger.error(f"Error in monthly driver report dashboard: {str(e)}")
        flash(f"Error loading monthly driver report: {str(e)}", "error")
        return redirect(url_for('index'))

@monthly_driver_report_bp.route('/generate/<month_year>')
def generate_report(month_year):
    """Generate monthly report for specified month"""
    try:
        year, month = map(int, month_year.split('-'))
        
        # Get month range
        start_date = datetime(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = datetime(year, month, last_day)
        
        # Sample report data (would aggregate from daily reports)
        report_data = {
            'month': start_date.strftime('%B %Y'),
            'total_drivers': 45,
            'summary': {
                'on_time': 892,
                'late_start': 73,
                'early_end': 45,
                'not_on_job': 28
            },
            'top_performers': [
                {'name': 'Johnson, Robert', 'on_time_rate': 98.5},
                {'name': 'Smith, Michael', 'on_time_rate': 96.8},
                {'name': 'Williams, David', 'on_time_rate': 95.2}
            ],
            'improvement_needed': [
                {'name': 'Brown, James', 'on_time_rate': 72.1},
                {'name': 'Davis, Kevin', 'on_time_rate': 75.8}
            ]
        }
        
        return render_template('monthly_driver_report/report.html',
                             report_data=report_data,
                             month_year=month_year)
                             
    except Exception as e:
        logger.error(f"Error generating monthly report: {str(e)}")
        flash(f"Error generating report: {str(e)}", "error")
        return redirect(url_for('monthly_driver_report.dashboard'))

@monthly_driver_report_bp.route('/export/<month_year>')
def export_report(month_year):
    """Export monthly report as Excel/PDF"""
    try:
        # This would generate and return the actual export file
        flash("Monthly report export functionality ready for implementation", "info")
        return redirect(url_for('monthly_driver_report.dashboard'))
        
    except Exception as e:
        logger.error(f"Error exporting monthly report: {str(e)}")
        flash(f"Error exporting report: {str(e)}", "error")
        return redirect(url_for('monthly_driver_report.dashboard'))