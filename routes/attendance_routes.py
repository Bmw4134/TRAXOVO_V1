"""
TRAXORA Fleet Management System - Attendance Routes

This module provides routes for the attendance reporting system,
including daily driver reports and enhanced weekly reports.
"""

import os
import logging
from datetime import datetime, timedelta
import json
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app

from utils.kaizen_blueprint_base import KaizenBlueprint

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
attendance_bp = KaizenBlueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.kaizen_route('/')
def index():
    """Attendance dashboard"""
    return render_template('attendance/index.html', 
                          timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@attendance_bp.kaizen_route('/daily_driver_report')
def daily_driver_report():
    """Daily Driver Report dashboard"""
    return render_template('attendance/daily_driver_report.html',
                          timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@attendance_bp.kaizen_route('/daily_driver_report/<date_str>')
def daily_driver_report_date(date_str):
    """Daily Driver Report for a specific date"""
    try:
        # Parse date
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Check if report exists
        report_file = os.path.join('reports', 'daily', f"{date_str}.json")
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                report_data = json.load(f)
                
            return render_template('attendance/daily_driver_report_view.html',
                                  date=date.strftime('%Y-%m-%d'),
                                  report_data=report_data,
                                  timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        else:
            flash(f"No report available for {date_str}", "warning")
            return redirect(url_for('attendance.daily_driver_report'))
    except ValueError:
        flash(f"Invalid date format: {date_str}. Use YYYY-MM-DD.", "danger")
        return redirect(url_for('attendance.daily_driver_report'))
    except Exception as e:
        logger.error(f"Error loading daily driver report for {date_str}: {str(e)}")
        flash(f"Error loading report: {str(e)}", "danger")
        return redirect(url_for('attendance.daily_driver_report'))

@attendance_bp.kaizen_route('/weekly_report')
def weekly_report():
    """Weekly Attendance Report dashboard"""
    return render_template('attendance/weekly_report.html',
                          timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@attendance_bp.kaizen_route('/weekly_report/<start_date>')
def weekly_report_date(start_date):
    """Weekly Attendance Report for a specific date range"""
    try:
        # Parse start date
        start = datetime.strptime(start_date, '%Y-%m-%d')
        
        # Calculate end date (7 days after start)
        end = start + timedelta(days=6)
        
        # Check if report exists
        report_file = os.path.join('reports', 'weekly', f"{start_date}_to_{end.strftime('%Y-%m-%d')}.json")
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                report_data = json.load(f)
                
            return render_template('attendance/weekly_report_view.html',
                                  start_date=start.strftime('%Y-%m-%d'),
                                  end_date=end.strftime('%Y-%m-%d'),
                                  report_data=report_data,
                                  timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        else:
            flash(f"No weekly report available for {start_date} to {end.strftime('%Y-%m-%d')}", "warning")
            return redirect(url_for('attendance.weekly_report'))
    except ValueError:
        flash(f"Invalid date format: {start_date}. Use YYYY-MM-DD.", "danger")
        return redirect(url_for('attendance.weekly_report'))
    except Exception as e:
        logger.error(f"Error loading weekly report for {start_date}: {str(e)}")
        flash(f"Error loading report: {str(e)}", "danger")
        return redirect(url_for('attendance.weekly_report'))

@attendance_bp.kaizen_route('/enhanced_weekly_report')
def enhanced_weekly_report():
    """Enhanced Weekly Report dashboard with advanced metrics"""
    return redirect(url_for('enhanced_weekly_report_bp.dashboard'))