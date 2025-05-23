"""
TRAXORA Fleet Management System - Enhanced Weekly Driver Report Routes

This module provides routes for processing and generating enhanced weekly driver reports
using the new modern UI style across the TRAXORA dashboard.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, jsonify, current_app, abort, send_file
)
from werkzeug.utils import secure_filename

from utils.weekly_driver_processor import WeeklyDriverProcessor, process_weekly_report

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
enhanced_weekly_report_bp = Blueprint('enhanced_weekly_report', __name__, url_prefix='/enhanced-weekly-report')

def get_reports_directory():
    """Get reports directory, creating it if needed"""
    reports_dir = os.path.join(current_app.root_path, 'reports', 'weekly_driver_reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def get_attached_assets_directory():
    """Get attached_assets directory"""
    return os.path.join(current_app.root_path, 'attached_assets')

@enhanced_weekly_report_bp.route('/')
def dashboard():
    """Enhanced weekly driver report dashboard"""
    try:
        # Get the requested week's date range
        today = datetime.now().date()
        
        # Default to previous Sunday as start date
        days_since_sunday = today.weekday() + 1  # +1 because Sunday is 6 in Python's weekday()
        if days_since_sunday == 7:  # If today is Sunday
            days_since_sunday = 0
        
        # Calculate default date range (previous Sunday to Saturday)
        start_of_week = today - timedelta(days=days_since_sunday)
        end_of_week = start_of_week + timedelta(days=6)
        
        # Format dates for display
        start_date_str = start_of_week.strftime('%Y-%m-%d')
        end_date_str = end_of_week.strftime('%Y-%m-%d')
        
        # Check if report exists for default week
        reports_dir = get_reports_directory()
        weekly_report_path = os.path.join(reports_dir, f"weekly_{start_date_str}_to_{end_date_str}.json")
        report_exists = os.path.exists(weekly_report_path)
        
        # Get list of weeks with reports
        available_weeks = []
        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                if filename.startswith('weekly_') and filename.endswith('.json'):
                    # Extract date range from filename
                    date_part = filename[7:-5]  # Remove 'weekly_' and '.json'
                    if '_to_' in date_part:
                        start_date, end_date = date_part.split('_to_')
                        try:
                            # Parse dates
                            start = datetime.strptime(start_date, '%Y-%m-%d').date()
                            end = datetime.strptime(end_date, '%Y-%m-%d').date()
                            
                            # Add to list
                            available_weeks.append({
                                'start_date': start_date,
                                'end_date': end_date,
                                'start_formatted': start.strftime('%b %d, %Y'),
                                'end_formatted': end.strftime('%b %d, %Y'),
                                'formatted_range': f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}",
                                'filename': filename
                            })
                        except ValueError:
                            continue
        
        # Sort weeks by start date (newest first)
        available_weeks.sort(key=lambda x: x['start_date'], reverse=True)
        
        # Check for our test week (May 18-23, 2025)
        test_week = {
            'start_date': '2025-05-18',
            'end_date': '2025-05-23',
            'start_formatted': 'May 18, 2025',
            'end_formatted': 'May 23, 2025',
            'formatted_range': 'May 18 - May 23, 2025',
        }
        
        test_weekly_report_path = os.path.join(reports_dir, f"weekly_{test_week['start_date']}_to_{test_week['end_date']}.json")
        test_report_exists = os.path.exists(test_weekly_report_path)
        
        return render_template(
            'enhanced_weekly_report/dashboard.html',
            start_date=start_date_str,
            end_date=end_date_str,
            start_formatted=start_of_week.strftime('%b %d, %Y'),
            end_formatted=end_of_week.strftime('%b %d, %Y'),
            report_exists=report_exists,
            available_weeks=available_weeks,
            test_week=test_week,
            test_report_exists=test_report_exists
        )
    
    except Exception as e:
        logger.error(f"Error displaying enhanced weekly driver report dashboard: {str(e)}")
        flash(f"Error displaying dashboard: {str(e)}", "danger")
        return render_template('enhanced_weekly_report/dashboard.html')

@enhanced_weekly_report_bp.route('/process-test-data', methods=['POST'])
def process_test_data():
    """Process test data for May 18-23, 2025"""
    try:
        start_date = "2025-05-18"
        end_date = "2025-05-23"
        
        # Check if files exist in attached_assets
        attached_assets_dir = get_attached_assets_directory()
        
        driving_history_path = os.path.join(attached_assets_dir, "DrivingHistory (19).csv")
        activity_detail_path = os.path.join(attached_assets_dir, "ActivityDetail (13).csv")
        time_on_site_path = os.path.join(attached_assets_dir, "AssetsTimeOnSite (8).csv")
        timecard_path = os.path.join(attached_assets_dir, "Timecards - 2025-05-18 - 2025-05-24 (3).xlsx")
        
        logger.info(f"Checking for files in {attached_assets_dir}")
        logger.info(f"Driving History: {os.path.exists(driving_history_path)}")
        logger.info(f"Activity Detail: {os.path.exists(activity_detail_path)}")
        logger.info(f"Time On Site: {os.path.exists(time_on_site_path)}")
        logger.info(f"Timecard: {os.path.exists(timecard_path)}")
        
        if not os.path.exists(driving_history_path):
            flash("DrivingHistory file not found in attached_assets", "danger")
            return redirect(url_for('enhanced_weekly_report.dashboard'))
        
        if not os.path.exists(activity_detail_path):
            flash("ActivityDetail file not found in attached_assets", "danger")
            return redirect(url_for('enhanced_weekly_report.dashboard'))
        
        if not os.path.exists(time_on_site_path):
            flash("AssetsTimeOnSite file not found in attached_assets", "danger")
            return redirect(url_for('enhanced_weekly_report.dashboard'))
        
        # Process the weekly report
        logger.info("Processing test data for May 18-23, 2025")
        
        # List all files in the attached_assets directory
        logger.info("Files in attached_assets directory:")
        for filename in os.listdir(attached_assets_dir):
            if filename.endswith('.csv') or filename.endswith('.xlsx'):
                logger.info(f"- {filename}")
        
        # Create report directories if needed
        reports_dir = get_reports_directory()
        os.makedirs(reports_dir, exist_ok=True)
        
        data_dir = os.path.join(current_app.root_path, 'data', 'weekly_driver_reports')
        os.makedirs(data_dir, exist_ok=True)
        
        # Process report
        weekly_report = process_weekly_report(
            start_date=start_date,
            end_date=end_date,
            driving_history_path="DrivingHistory (19).csv",
            activity_detail_path="ActivityDetail (13).csv",
            time_on_site_path="AssetsTimeOnSite (8).csv",
            timecard_paths=["Timecards - 2025-05-18 - 2025-05-24 (3).xlsx", "Timecards - 2025-05-18 - 2025-05-24 (4).xlsx"],
            from_attached_assets=True
        )
        
        if weekly_report:
            # Count drivers in the report for validation
            driver_count = 0
            if 'summary' in weekly_report and 'driver_attendance' in weekly_report['summary']:
                driver_count = len(weekly_report['summary']['driver_attendance'])
            
            flash(f"Successfully processed test data for May 18-23, 2025 with {driver_count} drivers", "success")
            return redirect(url_for('enhanced_weekly_report.view_report', start_date=start_date, end_date=end_date))
        else:
            flash("Error processing test data - no report was generated", "danger")
            return redirect(url_for('enhanced_weekly_report.dashboard'))
    
    except Exception as e:
        logger.error(f"Error processing test data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        flash(f"Error processing test data: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report.dashboard'))

@enhanced_weekly_report_bp.route('/view/<start_date>/<end_date>')
def view_report(start_date, end_date):
    """View an enhanced weekly driver report"""
    try:
        # Get report from file
        report_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.json")
        
        if not os.path.exists(report_path):
            flash("Report not found", "danger")
            return redirect(url_for('enhanced_weekly_report.dashboard'))
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Parse dates for display
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get dates in range
        date_range = []
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            formatted_date = current_date.strftime('%a, %b %d')
            
            date_range.append({
                'date': date_str,
                'formatted': formatted_date,
                'has_data': date_str in report.get('daily_reports', {})
            })
            
            current_date += timedelta(days=1)
        
        return render_template(
            'enhanced_weekly_report/view.html',
            report=report,
            start_date=start_date,
            end_date=end_date,
            start_formatted=start.strftime('%b %d, %Y'),
            end_formatted=end.strftime('%b %d, %Y'),
            date_range=date_range
        )
    
    except Exception as e:
        logger.error(f"Error viewing enhanced weekly report: {str(e)}")
        flash(f"Error viewing weekly report: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report.dashboard'))

@enhanced_weekly_report_bp.route('/api/day/<date>')
def api_day_data(date):
    """API endpoint to get data for a specific day"""
    try:
        # Get daily report from file
        daily_report_path = os.path.join(get_reports_directory(), date, f"driver_report_{date}.json")
        
        if not os.path.exists(daily_report_path):
            return jsonify({"error": "Report not found"}), 404
        
        with open(daily_report_path, 'r') as f:
            report = json.load(f)
        
        return jsonify(report)
    
    except Exception as e:
        logger.error(f"Error getting day data: {str(e)}")
        return jsonify({"error": f"Error getting day data: {str(e)}"}), 500

@enhanced_weekly_report_bp.route('/api/weekly/<start_date>/<end_date>')
def api_weekly_data(start_date, end_date):
    """API endpoint to get data for a weekly report"""
    try:
        # Get report from file
        report_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.json")
        
        if not os.path.exists(report_path):
            return jsonify({"error": "Report not found"}), 404
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        return jsonify(report)
    
    except Exception as e:
        logger.error(f"Error getting weekly data: {str(e)}")
        return jsonify({"error": f"Error getting weekly data: {str(e)}"}), 500

@enhanced_weekly_report_bp.route('/download/<start_date>/<end_date>/<format>')
def download_report(start_date, end_date, format):
    """Download a weekly driver report in the specified format"""
    try:
        # Get report from file
        report_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.json")
        
        if not os.path.exists(report_path):
            flash("Report not found", "danger")
            return redirect(url_for('enhanced_weekly_report.dashboard'))
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        if format == 'json':
            # Send JSON file
            return send_file(
                report_path,
                as_attachment=True,
                download_name=f"weekly_driver_report_{start_date}_to_{end_date}.json",
                mimetype='application/json'
            )
        elif format == 'csv':
            # Create CSV file from report data
            csv_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.csv")
            
            try:
                # Create CSV file with driver data
                with open(csv_path, 'w', newline='') as csvfile:
                    import csv
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow(['Date', 'Driver', 'Job Site', 'Status', 'First Key On', 'Last Key Off', 'Late Minutes', 'Early Minutes'])
                    
                    # Write driver data for each day
                    for date_str, daily_report in report['daily_reports'].items():
                        formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%m/%d/%Y')
                        
                        for driver_name, driver_record in daily_report['driver_records'].items():
                            writer.writerow([
                                formatted_date,
                                driver_name,
                                driver_record['job_site'],
                                driver_record['status'],
                                driver_record['first_key_on'] or '',
                                driver_record['last_key_off'] or '',
                                driver_record['late_minutes'],
                                driver_record['early_minutes']
                            ])
                
                # Send CSV file
                return send_file(
                    csv_path,
                    as_attachment=True,
                    download_name=f"weekly_driver_report_{start_date}_to_{end_date}.csv",
                    mimetype='text/csv'
                )
            except Exception as csv_error:
                logger.error(f"Error creating CSV file: {str(csv_error)}")
                flash(f"Error creating CSV file: {str(csv_error)}", "danger")
                return redirect(url_for('enhanced_weekly_report.view_report', start_date=start_date, end_date=end_date))
        else:
            flash(f"Unsupported format: {format}", "danger")
            return redirect(url_for('enhanced_weekly_report.view_report', start_date=start_date, end_date=end_date))
    
    except Exception as e:
        logger.error(f"Error downloading weekly report: {str(e)}")
        flash(f"Error downloading weekly report: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report.dashboard'))