"""
Driver Module Routes (Fixed Version)

This module contains routes for the driver module, handling driver attendance reports,
driver lists, and related functionality.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, abort, flash, send_from_directory
from flask_login import login_required, current_user
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)
error_logger = logging.getLogger("error")

# Create a blueprint for driver module routes
driver_module_bp = Blueprint('driver_module', __name__, url_prefix='/drivers')

def get_daily_report(date_str=None):
    """
    Get the daily attendance report data
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        dict: Report data or fallback report if not found
    """
    try:
        # If no date provided, use today
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Try to load from JSON file first
        json_path = f"exports/daily_reports/daily_report_{date_str}.json"
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                report_data = json.load(f)
                logger.info(f"Loaded report data from JSON for date {date_str}")
                
                # Ensure all required fields are present
                if 'date' not in report_data:
                    report_data['date'] = date_str
                
                if 'report_date' not in report_data:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        report_data['report_date'] = date_obj.strftime('%A, %B %d, %Y')
                    except:
                        report_data['report_date'] = date_str
                
                return report_data
        
        # Try to load from Excel file as fallback
        excel_path = f"exports/daily_reports/{date_str}_DailyDriverReport.xlsx"
        alt_excel_path = f"exports/daily_reports/daily_report_{date_str}.xlsx"
        
        if os.path.exists(excel_path):
            df = pd.read_excel(excel_path)
            drivers = df.to_dict('records')
        elif os.path.exists(alt_excel_path):
            df = pd.read_excel(alt_excel_path)
            drivers = df.to_dict('records')
        else:
            # Fallback to empty drivers list
            drivers = []
        
        # Create the report data structure
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        report_data = {
            'date': date_str,
            'report_date': date_obj.strftime('%A, %B %d, %Y'),
            'drivers': drivers
        }
        
        return report_data
    
    except Exception as e:
        logger.error(f"Error getting daily report for date {date_str}: {e}")
        
        # Return a fallback report
        try:
            if date_str:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%A, %B %d, %Y')
            else:
                date_str = datetime.now().strftime('%Y-%m-%d')
                formatted_date = datetime.now().strftime('%A, %B %d, %Y')
        except:
            date_str = datetime.now().strftime('%Y-%m-%d')
            formatted_date = date_str
        
        return {
            'date': date_str,
            'report_date': formatted_date,
            'drivers': []
        }

@driver_module_bp.route('/')
@login_required
def index():
    """Driver module index page"""
    return render_template('drivers/index.html')

@driver_module_bp.route('/daily-report', methods=['GET', 'POST'])
@login_required
def daily_report():
    """Daily driver attendance report page"""
    try:
        # Get date parameter with safe fallback
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Get report data
        report = get_daily_report(date_str)
        
        # Set up available dates (previous 7 days)
        today = datetime.now()
        available_dates = []
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            formatted_date = date.strftime('%a, %b %d')
            available_dates.append({
                'date': date_str,
                'formatted_date': formatted_date
            })
        
        # Calculate stats
        total_drivers = len(report.get('drivers', []))
        on_time_count = sum(1 for driver in report.get('drivers', []) if driver.get('status') == 'On Time')
        late_count = sum(1 for driver in report.get('drivers', []) if driver.get('status') == 'Late')
        early_departure_count = sum(1 for driver in report.get('drivers', []) if driver.get('status') == 'Early Departure')
        not_found_count = sum(1 for driver in report.get('drivers', []) if driver.get('status') == 'Not Found')
        
        # Add stats to report
        report['total_drivers'] = total_drivers
        report['on_time_count'] = on_time_count
        report['late_count'] = late_count
        report['early_departure_count'] = early_departure_count
        report['not_found_count'] = not_found_count
        
        # Group drivers by status
        late_drivers = [d for d in report.get('drivers', []) if d.get('status') == 'Late']
        early_departures = [d for d in report.get('drivers', []) if d.get('status') == 'Early Departure']
        not_found = [d for d in report.get('drivers', []) if d.get('status') == 'Not Found']
        
        # Add grouped drivers to report
        report['late_drivers'] = late_drivers
        report['early_departures'] = early_departures
        report['not_found'] = not_found
        
        return render_template('drivers/daily_report.html', 
                              report=report, 
                              available_dates=available_dates)
    
    except Exception as e:
        logger.error(f"Error rendering daily report: {e}")
        error_logger.error(f"Error rendering daily report: {e}")
        flash(f"Error loading report: {str(e)}", "danger")
        return render_template('error.html', error_message=f"Error loading report: {str(e)}")

@driver_module_bp.route('/download/daily-report/excel/<date_str>')
@login_required
def download_excel_report(date_str):
    """Download Excel report for a specific date"""
    try:
        # Set up file paths with multiple fallback options
        filename = f"{date_str}_DailyDriverReport.xlsx"
        alt_filename = f"daily_report_{date_str}.xlsx"
        
        # Define search directories from most specific to most general
        search_dirs = [
            os.path.join(current_app.root_path, 'exports', 'daily_reports'),
            os.path.join(current_app.root_path, 'static', 'exports', 'daily_reports'),
            os.path.join(current_app.root_path, 'exports'),
            os.path.join(current_app.root_path, 'static', 'exports')
        ]
        
        # Try to find the file in each directory
        for directory in search_dirs:
            if os.path.exists(os.path.join(directory, filename)):
                return send_from_directory(directory=directory, path=filename, as_attachment=True)
            
            if os.path.exists(os.path.join(directory, alt_filename)):
                return send_from_directory(directory=directory, path=alt_filename, as_attachment=True)
        
        # File not found
        flash("Excel report not found", "danger")
        return redirect(url_for('driver_module.daily_report', date=date_str))
    
    except Exception as e:
        logger.error(f"Error downloading Excel report: {e}")
        flash(f"Error downloading report: {str(e)}", "danger")
        return redirect(url_for('driver_module.daily_report', date=date_str))

@driver_module_bp.route('/download/daily-report/pdf/<date_str>')
@login_required
def download_pdf_report(date_str):
    """Download PDF report for a specific date"""
    try:
        # Set up file paths with multiple fallback options
        filename = f"{date_str}_DailyDriverReport.pdf"
        alt_filename = f"daily_report_{date_str}.pdf"
        
        # Define search directories from most specific to most general
        search_dirs = [
            os.path.join(current_app.root_path, 'exports', 'daily_reports'),
            os.path.join(current_app.root_path, 'static', 'exports', 'daily_reports'),
            os.path.join(current_app.root_path, 'exports'),
            os.path.join(current_app.root_path, 'static', 'exports')
        ]
        
        # Try to find the file in each directory
        for directory in search_dirs:
            if os.path.exists(os.path.join(directory, filename)):
                return send_from_directory(directory=directory, path=filename, as_attachment=True)
            
            if os.path.exists(os.path.join(directory, alt_filename)):
                return send_from_directory(directory=directory, path=alt_filename, as_attachment=True)
        
        # File not found
        flash("PDF report not found", "danger")
        return redirect(url_for('driver_module.daily_report', date=date_str))
    
    except Exception as e:
        logger.error(f"Error downloading PDF report: {e}")
        flash(f"Error downloading report: {str(e)}", "danger")
        return redirect(url_for('driver_module.daily_report', date=date_str))

@driver_module_bp.route('/download/<path:filename>')
@login_required
def download_file(filename):
    """Download a file from the exports directory"""
    try:
        directory = os.path.join(current_app.root_path, 'exports')
        return send_from_directory(directory=directory, path=filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        flash(f"Error downloading file: {str(e)}", "danger")
        return redirect(url_for('driver_module.index'))