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
# Create blueprint with a simple, consistent name and URL path
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

@enhanced_weekly_report_bp.route('/generate-report')
def generate_report():
    """
    Generate a new weekly report with current date range
    Default to the most recent week (Monday-Sunday)
    """
    # Get the current date
    today = datetime.now()
    
    # Find the most recent Monday
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday)
    
    # Set date range (Monday to Sunday)
    start_date = last_monday.strftime('%Y-%m-%d')
    end_date = (last_monday + timedelta(days=6)).strftime('%Y-%m-%d')
    
    # Store in session for future use
    session['report_start_date'] = start_date
    session['report_end_date'] = end_date
    
    # Redirect to the upload page with date range
    return redirect(url_for('enhanced_weekly_report_bp.dashboard', 
                           start_date=start_date, 
                           end_date=end_date))

@enhanced_weekly_report_bp.route('/demo-may-week')
def demo_may_week():
    """Process and display May 18-24 demo data"""
    try:
        from utils.demo_processor import process_may_week_report
        
        # Process demo report
        report_data = process_may_week_report()
        
        if not report_data:
            flash("Error processing demo data. Please check the logs for details.", "danger")
            return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
        
        # Define the date range for May week
        start_date = "2025-05-18"
        end_date = "2025-05-24"
        start_formatted = "May 18, 2025"
        end_formatted = "May 24, 2025"
        
        # Format start and end dates
        return render_template('enhanced_weekly_report/view.html',
                              report=report_data,
                              start_date="2025-05-18",
                              end_date="2025-05-24",
                              start_formatted=start_formatted,
                              end_formatted=end_formatted,
                              date_range=report_data.get('date_range', []))
    except Exception as e:
        logger.error(f"Error processing demo report: {str(e)}")
        flash(f"An error occurred while processing the demo report: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report_bp.dashboard'))

@enhanced_weekly_report_bp.route('/compare-methods')
@enhanced_weekly_report_bp.route('/compare_processing_methods')
def compare_methods():
    """Compare TRAXORA and alternative processing methods"""
    try:
        from utils.enhanced_attendance_engine import process_comparison_enhanced
        
        # Process comparison using the enhanced engine
        comparison_data = process_comparison_enhanced()
        
        if not comparison_data:
            flash("Error generating comparison. Please check the logs for details.", "danger")
            return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
        
        # Calculate start and end dates
        start_date = "2025-05-18"
        end_date = "2025-05-24"
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        start_formatted = start_datetime.strftime('%B %d, %Y')
        end_formatted = end_datetime.strftime('%B %d, %Y')
        
        # Render comparison template
        return render_template('enhanced_weekly_report/comparison.html',
                              comparison=comparison_data,
                              start_date=start_date,
                              end_date=end_date,
                              start_formatted=start_formatted,
                              end_formatted=end_formatted)
    except Exception as e:
        logger.error(f"Error comparing processing methods: {str(e)}")
        flash(f"An error occurred while comparing processing methods: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report_bp.dashboard'))

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
        
        # Get reports directory
        reports_dir = get_reports_directory()
        
        # Get list of recent reports
        reports = []
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
                            
                            # Load report data for metrics
                            report_path = os.path.join(reports_dir, filename)
                            try:
                                with open(report_path, 'r') as f:
                                    report_data = json.load(f)
                                    
                                # Extract summary metrics
                                summary = report_data.get('summary', {})
                                attendance = summary.get('attendance_totals', {})
                                
                                # Add to list
                                reports.append({
                                    'start_date': start_date,
                                    'end_date': end_date,
                                    'date_range': f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}",
                                    'summary': {
                                        'on_time': attendance.get('on_time', 0),
                                        'late': attendance.get('late_start', 0),
                                        'early_end': attendance.get('early_end', 0),
                                        'not_on_job': attendance.get('not_on_job', 0),
                                        'total': attendance.get('total_tracked', 0)
                                    }
                                })
                            except Exception as e:
                                logger.error(f"Error loading report data: {str(e)}")
                        except ValueError:
                            continue
        
        # Sort reports by start date (newest first)
        reports.sort(key=lambda x: x['start_date'], reverse=True)
        
        # Prepare metrics from the most recent report, or use defaults
        metrics = {
            'on_time': 0,
            'late': 0,
            'early_end': 0,
            'not_on_job': 0,
            'avg_late': 0,
            'avg_early_end': 0
        }
        
        if reports:
            most_recent = reports[0]
            metrics = {
                'on_time': most_recent['summary'].get('on_time', 0),
                'late': most_recent['summary'].get('late', 0),
                'early_end': most_recent['summary'].get('early_end', 0),
                'not_on_job': most_recent['summary'].get('not_on_job', 0),
                'avg_late': 15,  # Default average in minutes
                'avg_early_end': 20  # Default average in minutes
            }
        
        # Special case for May 18-24 report
        may_report_path = os.path.join(reports_dir, f"weekly_2025-05-18_to_2025-05-24.json")
        if os.path.exists(may_report_path):
            try:
                with open(may_report_path, 'r') as f:
                    may_data = json.load(f)
                    may_attendance = may_data.get('summary', {}).get('attendance_totals', {})
                    
                    # Use May data for metrics if it's the most recent or specifically requested
                    if not reports or request.args.get('show_may') == 'true':
                        metrics = {
                            'on_time': may_attendance.get('on_time', 0),
                            'late': may_attendance.get('late_start', 0),
                            'early_end': may_attendance.get('early_end', 0),
                            'not_on_job': may_attendance.get('not_on_job', 0),
                            'avg_late': 15,  # Example average in minutes
                            'avg_early_end': 20  # Example average in minutes
                        }
            except Exception as e:
                logger.error(f"Error loading May report data: {str(e)}")
        
        # Render the new dashboard template
        return render_template(
            'driver_reports_dashboard.html',
            reports=reports,
            metrics=metrics,
            start_date=start_date_str,
            end_date=end_date_str,
            billing_enabled=True
        )
    
    except Exception as e:
        logger.error(f"Error displaying driver reports dashboard: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        flash(f"Error displaying dashboard: {str(e)}", "danger")
        return render_template('driver_reports_dashboard.html', metrics={}, reports=[], billing_enabled=True)

@enhanced_weekly_report_bp.route('/upload')
def upload():
    """Display upload form for weekly driver report data files"""
    try:
        today = datetime.now().date().strftime('%Y-%m-%d')
        return render_template('enhanced_weekly_report/upload.html', today=today)
    except Exception as e:
        logger.error(f"Error displaying upload form: {str(e)}")
        flash(f"Error displaying upload form: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report_bp.dashboard'))

@enhanced_weekly_report_bp.route('/upload/files', methods=['POST'])
def upload_files():
    """Upload data files for weekly driver report"""
    try:
        # Get report date
        report_date = request.form.get('report_date')
        if not report_date:
            flash("Report date is required", "danger")
            return redirect(url_for('enhanced_weekly_report_bp.upload'))
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'weekly_driver_reports', report_date)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Get uploaded files
        files = request.files.getlist('files[]')
        if not files or not files[0].filename:
            flash("No files selected", "danger")
            return redirect(url_for('enhanced_weekly_report_bp.upload'))
        
        # Save files
        saved_files = []
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                saved_files.append(filename)
        
        flash(f"Successfully uploaded {len(saved_files)} files", "success")
        return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
    
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        flash(f"Error uploading files: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report_bp.upload'))

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

@enhanced_weekly_report_bp.route('/view/<start_date>/<end_date>')
def view_report(start_date, end_date):
    """View an enhanced weekly driver report"""
    try:
        # Get report from file
        report_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.json")
        
        if not os.path.exists(report_path):
            flash("Report not found. Please process the data first.", "warning")
            return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
        
        # Load report data
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)
        except Exception as e:
            logger.error(f"Error loading report JSON: {str(e)}")
            flash(f"Error loading report data: {str(e)}", "danger")
            return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
            
        # Add download URLs to the template context
        download_urls = {
            'csv': url_for('enhanced_weekly_report_bp.download_report', start_date=start_date, end_date=end_date, format='csv'),
            'json': url_for('enhanced_weekly_report_bp.download_report', start_date=start_date, end_date=end_date, format='json')
        }
        
        # Process dates for display
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Format for display
        start_formatted = start.strftime('%b %d, %Y')
        end_formatted = end.strftime('%b %d, %Y')
        
        # Generate the full date range for the week
        date_range = []
        current_date = start
        while current_date <= end:
            date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # Initialize daily driver records with an empty array for each day
        daily_driver_records = {}
        for date_str in date_range:
            # Add driver_records if missing from the report structure
            if date_str in report.get('daily_reports', {}):
                daily_report = report['daily_reports'][date_str]
                if 'driver_records' not in daily_report or not daily_report['driver_records']:
                    # If driver_records is missing, build it from drivers
                    driver_records = []
                    for driver_name, driver_info in daily_report.get('drivers', {}).items():
                        record = {
                            'driver_name': driver_name,
                            'attendance_status': driver_info.get('status', 'unknown'),
                            'job_site': driver_info.get('job_site', 'Unknown'),
                            'first_seen': driver_info.get('first_seen', ''),
                            'last_seen': driver_info.get('last_seen', ''),
                            'total_time': driver_info.get('hours_on_site', 0)
                        }
                        driver_records.append(record)
                    daily_report['driver_records'] = driver_records
                
                daily_driver_records[date_str] = daily_report.get('driver_records', [])
            else:
                daily_driver_records[date_str] = []
        
        # Calculate summary statistics
        daily_stats = []
        for date_str in date_range:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            date_formatted = date_obj.strftime('%A, %b %d')
            
            # Count attendance by status
            status_counts = {
                'on_time': 0,
                'late_start': 0,
                'early_end': 0,
                'not_on_job': 0,
                'total': 0
            }
            
            for driver_record in daily_driver_records.get(date_str, []):
                status = driver_record.get('attendance_status', 'unknown')
                if status in status_counts:
                    status_counts[status] += 1
                status_counts['total'] += 1
            
            # Calculate percentages
            if status_counts['total'] > 0:
                on_time_pct = int(status_counts['on_time'] / status_counts['total'] * 100)
            else:
                on_time_pct = 0
            
            daily_stats.append({
                'date': date_str,
                'formatted_date': date_formatted,
                'total_drivers': status_counts['total'],
                'on_time': status_counts['on_time'],
                'late_start': status_counts['late_start'],
                'early_end': status_counts['early_end'],
                'not_on_job': status_counts['not_on_job'],
                'on_time_pct': on_time_pct,
                'driver_records': daily_driver_records.get(date_str, [])
            })
        
        # Sort by date
        daily_stats.sort(key=lambda x: x['date'])
        
        # Process driver summary stats
        driver_stats = {}
        for date_str in date_range:
            for driver_record in daily_driver_records.get(date_str, []):
                driver_name = driver_record.get('driver_name', 'Unknown')
                status = driver_record.get('attendance_status', 'unknown')
                
                if driver_name not in driver_stats:
                    driver_stats[driver_name] = {
                        'name': driver_name,
                        'total_days': 0,
                        'on_time': 0,
                        'late_start': 0,
                        'early_end': 0,
                        'not_on_job': 0,
                        'daily_records': []
                    }
                
                driver_stats[driver_name]['total_days'] += 1
                if status in driver_stats[driver_name]:
                    driver_stats[driver_name][status] += 1
                
                # Add the daily record for this driver - handle None values safely
                first_seen_time = ''
                if driver_record.get('first_seen'):
                    first_seen_parts = driver_record.get('first_seen', '').split(' ')
                    if len(first_seen_parts) > 1:
                        first_seen_time = first_seen_parts[1]
                
                last_seen_time = ''
                if driver_record.get('last_seen'):
                    last_seen_parts = driver_record.get('last_seen', '').split(' ')
                    if len(last_seen_parts) > 1:
                        last_seen_time = last_seen_parts[1]
                
                driver_stats[driver_name]['daily_records'].append({
                    'date': date_str,
                    'status': status,
                    'first_seen': first_seen_time,
                    'last_seen': last_seen_time,
                    'job_site': driver_record.get('job_site', 'Unknown Job Site')
                })
        
        # Calculate percentages for each driver
        for driver_name, stats in driver_stats.items():
            if stats['total_days'] > 0:
                stats['on_time_pct'] = int(stats['on_time'] / stats['total_days'] * 100)
            else:
                stats['on_time_pct'] = 0
        
        # Convert to list and sort
        driver_stats_list = list(driver_stats.values())
        driver_stats_list.sort(key=lambda x: x['name'])
        
        # Prepare overall summary
        summary = report.get('summary', {})
        
        # Using the simplified template to avoid rendering issues
        return render_template(
            'enhanced_weekly_report/view_simple.html',
            start_date=start_date,
            end_date=end_date,
            start_formatted=start_formatted,
            end_formatted=end_formatted,
            daily_stats=daily_stats,
            driver_stats=driver_stats_list,
            report={'summary': summary}
        )
    
    except Exception as e:
        logger.error(f"Error viewing weekly report: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        flash(f"Error viewing report: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report_bp.dashboard'))

@enhanced_weekly_report_bp.route('/api/day/<date>')
def api_day_data(date):
    """API endpoint to get data for a specific day"""
    try:
        # Get the report from the request parameters or session
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            # If not provided, try to get from session
            if 'weekly_report' in session:
                report_info = session['weekly_report']
                start_date = report_info.get('start_date')
                end_date = report_info.get('end_date')
            else:
                return jsonify({'error': 'Report date range not provided'}), 400
        
        # Get report from file
        report_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.json")
        
        if not os.path.exists(report_path):
            return jsonify({'error': 'Report not found'}), 404
        
        # Load report data
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Get daily report for the requested date
        daily_report = report.get('daily_reports', {}).get(date)
        
        if not daily_report:
            return jsonify({'error': 'Date not found in report'}), 404
        
        return jsonify(daily_report)
    
    except Exception as e:
        logger.error(f"API error getting day data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@enhanced_weekly_report_bp.route('/api/weekly/<start_date>/<end_date>')
def api_weekly_data(start_date, end_date):
    """API endpoint to get data for a weekly report"""
    try:
        # Get report from file
        report_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.json")
        
        if not os.path.exists(report_path):
            return jsonify({'error': 'Report not found'}), 404
        
        # Load report data
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        return jsonify(report)
    
    except Exception as e:
        logger.error(f"API error getting weekly data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@enhanced_weekly_report_bp.route('/download/<start_date>/<end_date>/<format>')
def download_report(start_date, end_date, format):
    """Download a weekly driver report in the specified format"""
    try:
        # Get report from file
        report_path = os.path.join(get_reports_directory(), f"weekly_{start_date}_to_{end_date}.json")
        
        if not os.path.exists(report_path):
            flash("Report not found. Please process the data first.", "warning")
            return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
        
        # Load report data
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Prepare date formatting for filename
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        date_range = f"{start.strftime('%m%d')}-{end.strftime('%m%d')}"
        download_path = os.path.join(get_reports_directory(), f"traxora_driver_report_{date_range}.{format}")
        
        # Process data into requested format
        if format.lower() == 'csv':
            try:
                # Convert to CSV using pandas
                import pandas as pd
                
                # Prepare a flattened data structure for CSV
                flat_data = []
                
                # Add daily driver records for each day
                for date_str, daily_report in report.get('daily_reports', {}).items():
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    
                    for record in daily_report.get('driver_records', []):
                        flat_record = {
                            'Date': formatted_date,
                            'Driver Name': record.get('driver_name', ''),
                            'Employee ID': record.get('employee_id', ''),
                            'Status': record.get('attendance_status', ''),
                            'Job Site': record.get('job_site', ''),
                            'First Start': record.get('first_start_time', ''),
                            'Last End': record.get('last_end_time', ''),
                            'Hours': record.get('total_hours', 0),
                            'Vehicle ID': record.get('vehicle_id', ''),
                            'Notes': record.get('notes', '')
                        }
                        flat_data.append(flat_record)
                
                # Convert to DataFrame and then to CSV
                df = pd.DataFrame(flat_data)
                df.to_csv(download_path, index=False)
                
                return send_file(
                    download_path,
                    as_attachment=True,
                    download_name=f"traxora_driver_report_{date_range}.csv",
                    mimetype='text/csv'
                )
                
            except Exception as e:
                logger.error(f"Error generating CSV: {str(e)}")
                flash(f"Error generating CSV: {str(e)}", 'danger')
                return redirect(url_for('enhanced_weekly_report_bp.view_report', start_date=start_date, end_date=end_date))
        
        # JSON format
        elif format.lower() == 'json':
            # Dump JSON file
            with open(download_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            return send_file(
                download_path,
                as_attachment=True,
                download_name=f"traxora_driver_report_{date_range}.json",
                mimetype='application/json'
            )
            
        # PDF format
        elif format.lower() == 'pdf':
            try:
                from reportlab.lib.pagesizes import letter, landscape
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet
                
                doc = SimpleDocTemplate(download_path, pagesize=landscape(letter))
                elements = []
                
                # Add title
                styles = getSampleStyleSheet()
                title = Paragraph(f"TRAXORA Driver Report: {start_date} to {end_date}", styles['Heading1'])
                elements.append(title)
                elements.append(Spacer(1, 12))
                
                # Add summary data
                summary_data = [
                    ['Metric', 'Count', 'Percentage'],
                    ['On Time', str(report.get('summary', {}).get('counts', {}).get('on_time', 0)), 
                     f"{report.get('summary', {}).get('attendance_percentages', {}).get('on_time', 0)}%"],
                    ['Late Start', str(report.get('summary', {}).get('counts', {}).get('late_starts', 0)), 
                     f"{report.get('summary', {}).get('attendance_percentages', {}).get('late_starts', 0)}%"],
                    ['Early End', str(report.get('summary', {}).get('counts', {}).get('early_ends', 0)), 
                     f"{report.get('summary', {}).get('attendance_percentages', {}).get('early_ends', 0)}%"],
                    ['Not On Job', str(report.get('summary', {}).get('counts', {}).get('not_on_job', 0)), 
                     f"{report.get('summary', {}).get('attendance_percentages', {}).get('not_on_job', 0)}%"],
                    ['Total', str(report.get('summary', {}).get('total_drivers', 0)), '100%']
                ]
                
                summary_table = Table(summary_data, colWidths=[200, 100, 100])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(summary_table)
                elements.append(Spacer(1, 24))
                
                # Add detailed driver data
                data_rows = [['Date', 'Driver Name', 'Status', 'Start Time', 'End Time', 'Hours', 'Job Site']]
                
                for date_str, daily_report in report.get('daily_reports', {}).items():
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    
                    for driver in daily_report.get('driver_records', []):
                        data_rows.append([
                            formatted_date,
                            driver.get('driver_name', 'Unknown'),
                            driver.get('attendance_status', 'Unknown'),
                            driver.get('first_start_time', ''),
                            driver.get('last_end_time', ''),
                            driver.get('total_hours', ''),
                            driver.get('job_site', '')
                        ])
                
                # Sort by date and driver name
                data_rows[1:] = sorted(data_rows[1:], key=lambda x: (x[0], x[1]))
                
                detail_table = Table(data_rows, repeatRows=1)
                detail_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(Paragraph("Driver Detail", styles['Heading2']))
                elements.append(Spacer(1, 12))
                elements.append(detail_table)
                
                # Build PDF
                doc.build(elements)
                
                return send_file(
                    download_path,
                    as_attachment=True,
                    download_name=f"traxora_driver_report_{date_range}.pdf",
                    mimetype='application/pdf'
                )
                
            except ImportError as e:
                logger.error(f"PDF generation failed due to missing dependencies: {str(e)}")
                flash("PDF generation failed due to missing dependencies. Using CSV format instead.", "warning")
                format = 'csv'  # Fallback to CSV
                # Recursively call with CSV format
                return download_report(start_date, end_date, 'csv')
                
        # Excel format
        elif format.lower() == 'excel':
            try:
                import pandas as pd
                
                # Create DataFrame
                rows = []
                
                for date_str, daily_report in report.get('daily_reports', {}).items():
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    
                    for driver in daily_report.get('driver_records', []):
                        rows.append({
                            'Date': formatted_date,
                            'Driver Name': driver.get('driver_name', 'Unknown'),
                            'Status': driver.get('attendance_status', 'Unknown'),
                            'Start Time': driver.get('first_start_time', ''),
                            'End Time': driver.get('last_end_time', ''),
                            'Hours': driver.get('total_hours', ''),
                            'Job Site': driver.get('job_site', ''),
                            'Vehicle ID': driver.get('vehicle_id', ''),
                            'Notes': driver.get('notes', '')
                        })
                
                df = pd.DataFrame(rows)
                
                # Sort by date and driver name
                df.sort_values(by=['Date', 'Driver Name'], inplace=True)
                
                # Create Excel writer
                with pd.ExcelWriter(download_path, engine='openpyxl') as writer:
                    # Write summary sheet
                    summary_data = {
                        'Metric': ['On Time', 'Late Start', 'Early End', 'Not On Job', 'Total'],
                        'Count': [
                            report.get('summary', {}).get('counts', {}).get('on_time', 0),
                            report.get('summary', {}).get('counts', {}).get('late_starts', 0),
                            report.get('summary', {}).get('counts', {}).get('early_ends', 0),
                            report.get('summary', {}).get('counts', {}).get('not_on_job', 0),
                            report.get('summary', {}).get('total_drivers', 0)
                        ],
                        'Percentage': [
                            f"{report.get('summary', {}).get('attendance_percentages', {}).get('on_time', 0)}%",
                            f"{report.get('summary', {}).get('attendance_percentages', {}).get('late_starts', 0)}%",
                            f"{report.get('summary', {}).get('attendance_percentages', {}).get('early_ends', 0)}%",
                            f"{report.get('summary', {}).get('attendance_percentages', {}).get('not_on_job', 0)}%",
                            '100%'
                        ]
                    }
                    
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Write detail sheet
                    df.to_excel(writer, sheet_name='Driver Detail', index=False)
                
                return send_file(
                    download_path,
                    as_attachment=True,
                    download_name=f"traxora_driver_report_{date_range}.xlsx",
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
            except ImportError as e:
                logger.error(f"Excel generation failed due to missing dependencies: {str(e)}")
                flash("Excel generation failed due to missing dependencies. Using CSV format instead.", "warning")
                return download_report(start_date, end_date, 'csv')
        
        # Invalid format
        else:
            flash(f'Unsupported download format: {format}. Please choose CSV, JSON, PDF, or Excel.', 'warning')
            return redirect(url_for('enhanced_weekly_report_bp.view_report', start_date=start_date, end_date=end_date))
    
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        flash(f"Error downloading report: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report_bp.view_report', start_date=start_date, end_date=end_date))
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        date_range = f"{start.strftime('%m%d')}-{end.strftime('%m%d')}"
        
        if format == 'json':
            # Create a JSON file for download
            download_path = os.path.join(get_reports_directory(), f"traxora_driver_report_{date_range}.json")
            
            with open(download_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            return send_file(
                download_path,
                as_attachment=True,
                download_name=f"traxora_driver_report_{date_range}.json",
                mimetype='application/json'
            )
            
        elif format == 'csv':
            # Create a flattened CSV file with all daily data
            import csv
            
            download_path = os.path.join(get_reports_directory(), f"traxora_driver_report_{date_range}.csv")
            
            # Combine all daily records into a flat structure
            rows = []
            
            # Column headers
            headers = [
                'Date', 'Driver Name', 'Attendance Status',
                'First Start Time', 'Last End Time', 'Total Hours',
                'Job Site', 'Vehicle ID', 'Notes'
            ]
            
            # Add data rows
            for date_str, daily_report in report.get('daily_reports', {}).items():
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                formatted_date = date_obj.strftime('%m/%d/%Y')
                
                for driver in daily_report.get('driver_records', []):
                    rows.append([
                        formatted_date,
                        driver.get('driver_name', 'Unknown'),
                        driver.get('attendance_status', 'Unknown'),
                        driver.get('first_start_time', ''),
                        driver.get('last_end_time', ''),
                        driver.get('total_hours', ''),
                        driver.get('job_site', ''),
                        driver.get('vehicle_id', ''),
                        driver.get('notes', '')
                    ])
            
            # Sort by date and driver name
            rows.sort(key=lambda x: (x[0], x[1]))
            
            # Write CSV
            with open(download_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            
            return send_file(
                download_path,
                as_attachment=True,
                download_name=f"traxora_driver_report_{date_range}.csv",
                mimetype='text/csv'
            )
            
        else:
            flash(f"Unsupported download format: {format}", "danger")
            return redirect(url_for('enhanced_weekly_report_bp.view_report', start_date=start_date, end_date=end_date))
    
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        flash(f"Error downloading report: {str(e)}", "danger")
        return redirect(url_for('enhanced_weekly_report_bp.view_report', start_date=start_date, end_date=end_date))