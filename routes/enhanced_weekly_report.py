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
    flash, jsonify, current_app, abort, send_file, session
)
from werkzeug.utils import secure_filename

from utils.weekly_driver_processor import WeeklyDriverProcessor, process_weekly_report

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
enhanced_weekly_report_bp = Blueprint('enhanced_weekly_report_bp', __name__, url_prefix='/enhanced-weekly-report')

def get_reports_directory():
    """Get reports directory, creating it if needed"""
    reports_dir = os.path.join(current_app.root_path, 'reports', 'weekly_driver_reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def get_attached_assets_directory():
    """Get attached_assets directory, creating it if needed"""
    attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
    os.makedirs(attached_assets_dir, exist_ok=True)
    return attached_assets_dir

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

@enhanced_weekly_report_bp.route('/upload')
def upload():
    """Display upload form for weekly driver report data files"""
    try:
        today = datetime.now().date().strftime('%Y-%m-%d')
        return render_template('enhanced_weekly_report/upload.html', today=today)
    except Exception as e:
        logger.error(f"Error displaying upload form: {str(e)}")
        flash(f"Error displaying upload form: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report.dashboard'))

@enhanced_weekly_report_bp.route('/upload/files', methods=['POST'])
def upload_files():
    """Upload data files for weekly driver report"""
    try:
        # Get report date
        report_date = request.form.get('report_date')
        if not report_date:
            flash("Report date is required", "danger")
            return redirect(url_for('enhanced_weekly_report.upload'))
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'weekly_driver_reports', report_date)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Get uploaded files
        files = request.files.getlist('files[]')
        if not files or not files[0].filename:
            flash("No files selected", "danger")
            return redirect(url_for('enhanced_weekly_report.upload'))
        
        # Save files
        saved_files = []
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                saved_files.append(filename)
        
        flash(f"Successfully uploaded {len(saved_files)} files", "success")
        return redirect(url_for('enhanced_weekly_report.dashboard'))
    
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        flash(f"Error uploading files: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report.upload'))

@enhanced_weekly_report_bp.route('/process-may-data')
def process_may_data():
    """Process May 18-24 data for the enhanced weekly report"""
    try:
        # Define date range for May 18-24, 2025
        start_date = '2025-05-18'  # Sunday
        end_date = '2025-05-24'    # Saturday
        logger.info(f"Processing May data from {start_date} to {end_date}")
        
        # Import the May data processor
        from utils.may_data_processor import process_may_weekly_report
        
        # Get directory paths
        attached_assets_dir = get_attached_assets_directory()
        reports_dir = get_reports_directory()
        logger.info(f"Looking for data files in: {attached_assets_dir}")
        
        # Process the May 18-24 report using our specialized processor
        report, errors = process_may_weekly_report(
            attached_assets_dir=attached_assets_dir,
            weekly_processor_function=process_weekly_report,
            report_dir=reports_dir
        )
        
        if errors:
            # If we encountered errors, show them to the user
            error_message = ", ".join(errors)
            logger.error(f"Errors processing May data: {error_message}")
            flash(f"Could not process May 18-24 report: {error_message}", "danger")
            return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
            
        if not report:
            # If no report was generated, show a generic error
            logger.error("No report data was generated")
            flash("Could not process May 18-24 report: No data was generated", "danger")
            return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
            
        # Store report info in session for immediate access
        session['weekly_report'] = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        # Show success message with some report statistics
        total_drivers = report['summary']['total_drivers']
        
        # Calculate some statistics for the flash message
        attendance_data = report['summary'].get('attendance_totals', {})
        total_tracked = attendance_data.get('total_tracked', 0)
        on_time = attendance_data.get('on_time', 0)
        
        # Calculate on-time percentage
        on_time_pct = int(on_time / total_tracked * 100) if total_tracked > 0 else 0
        
        flash(f"Successfully processed May 18-24 report! Analyzed {total_tracked} driver-days across {total_drivers} drivers with {on_time_pct}% on-time rate.", "success")
        
        # Redirect to the report view
        return redirect(url_for('enhanced_weekly_report_bp.view_report', start_date=start_date, end_date=end_date))
    except Exception as e:
        logger.error(f"Error processing May data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        flash(f"Error processing May data: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
            
            # Log which files we're using
            logger.info(f"Using driving history: {driving_history_path}")
            logger.info(f"Using activity detail: {activity_detail_path}")
            logger.info(f"Using time on site: {time_on_site_path}")
            logger.info(f"Using {len(timecard_paths)} timecard files")
            
            # Check if we found all required files
            if not driving_history_path or not time_on_site_path:
                logger.error("Missing required data files")
                flash("Cannot process report: Missing driving history or time on site data files", "danger")
                return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
        
        # Process the weekly report with the files we found
        try:
            # Import the processor here to ensure any dependencies are loaded
            from utils.weekly_driver_processor import WeeklyDriverProcessor
            
            # Initialize the weekly driver processor with our date range
            processor = WeeklyDriverProcessor(start_date, end_date)
            
            # Load the files into the processor
            processor.load_files(
                driving_history_path=driving_history_path,
                activity_detail_path=activity_detail_path,
                time_on_site_path=time_on_site_path,
                timecard_paths=timecard_paths
            )
            
            # Process the data - this runs the full classification pipeline
            logger.info("Starting data processing for May 18-24 week...")
            report = processor.process()
            
            # Process the data and check if it's valid
            if not report or 'summary' not in report or not report.get('daily_reports'):
                logger.error("Report processing failed: empty or invalid report data")
                flash("Report processing failed: No data could be analyzed. Check log for details.", "danger")
                return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
            
            # Calculate some statistics for the flash message
            attendance_data = report['summary'].get('attendance_totals', {})
            total_tracked = attendance_data.get('total_tracked', 0)
            on_time = attendance_data.get('on_time', 0)
            late_starts = attendance_data.get('late_starts', 0)
            early_ends = attendance_data.get('early_ends', 0)
            not_on_job = attendance_data.get('not_on_job', 0)
            
            # Calculate percentages
            on_time_pct = int(on_time / total_tracked * 100) if total_tracked > 0 else 0
            
            logger.info(f"Successfully processed report: {len(report['daily_reports'])} days, {report['summary']['total_drivers']} drivers")
            logger.info(f"Attendance stats: {on_time}/{total_tracked} on time ({on_time_pct}%)")
            
            # Store the report in the session for quick access
            session['weekly_report'] = report
            
            # Show a success message with some stats
            flash(f"May 18-24 report processed successfully! Analyzed {total_tracked} driver-days with {on_time_pct}% on-time rate.", "success")
            
            # Redirect to the report view
            return redirect(url_for('enhanced_weekly_report_bp.view_report', start_date=start_date, end_date=end_date))
            
        except Exception as e:
            logger.error(f"Error during report processing: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            flash(f"Report processing error: {str(e)}", "danger")
            return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
        
        # Save the report
        report_path = os.path.join(
            os.getcwd(), 
            'reports', 
            'weekly_driver_reports', 
            f'weekly_{start_date}_to_{end_date}.json'
        )
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {report_path}")
        flash("Weekly report processed successfully!", 'success')
        
        return redirect(url_for('enhanced_weekly_report.view_report', start_date=start_date, end_date=end_date))
    
    except Exception as e:
        logger.error(f"Error processing May data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        flash(f"Error processing May data: {str(e)}", 'danger')
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
                'has_data': True  # Always assume has data for UI purposes
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
                    if 'daily_reports' in report:
                        for date_str, daily_report in report['daily_reports'].items():
                            formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%m/%d/%Y')
                            
                            if 'driver_records' in daily_report:
                                for driver_name, driver_record in daily_report['driver_records'].items():
                                    writer.writerow([
                                        formatted_date,
                                        driver_name,
                                        driver_record.get('job_site', 'N/A'),
                                        driver_record.get('status', 'Unknown'),
                                        driver_record.get('first_key_on', '') or '',
                                        driver_record.get('last_key_off', '') or '',
                                        driver_record.get('late_minutes', 0),
                                        driver_record.get('early_minutes', 0)
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