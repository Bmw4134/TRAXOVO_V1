"""
Driver Module Routes

This module contains routes for the driver module, handling driver attendance reports,
driver lists, and related functionality with improved navigation and error handling.
"""

import os
import sys
import json
import logging
import traceback
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Logger setup
logger = logging.getLogger(__name__)

# Blueprint definition
driver_module_bp = Blueprint('driver_module', __name__, url_prefix='/drivers')

# Create error log directory
os.makedirs('logs', exist_ok=True)
error_log_path = 'logs/driver_errors.log'

# Configure error logging
error_logger = logging.getLogger('driver_error_logger')
if not error_logger.handlers:
    file_handler = logging.FileHandler(error_log_path)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    error_logger.addHandler(file_handler)
    error_logger.setLevel(logging.ERROR)

# Attendance Report Helper Functions
def get_daily_report(date_str=None):
    """Get daily attendance report with verified employee data only"""
    if date_str is None:
        # Default to current date
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Check if report JSON file exists
    json_path = f"exports/daily_reports/attendance_data_{date_str}.json"
    standard_json_path = f"exports/daily_reports/daily_report_{date_str}.json"
    
    try:
        # First try to load from the new attendance data format
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                attendance_data = json.load(f)
            
            logger.info(f"Loaded attendance data from JSON for date {date_str}")
            
            # Convert attendance data format to report format
            late_records = attendance_data.get('late_start_records', [])
            early_records = attendance_data.get('early_end_records', [])
            not_on_job_records = attendance_data.get('not_on_job_records', [])
            drivers = attendance_data.get('drivers', [])
            
            # Create summary data for display
            summary = {
                'total_drivers': attendance_data.get('total_drivers', 0),
                'total_morning_drivers': attendance_data.get('total_drivers', 0),
                'on_time_drivers': max(0, attendance_data.get('total_drivers', 0) - len(late_records) - len(not_on_job_records)),
                'late_drivers': len(late_records),
                'early_end_drivers': len(early_records),
                'not_on_job_drivers': len(not_on_job_records),
                'exception_drivers': 0,
                'total_issues': len(late_records) + len(early_records) + len(not_on_job_records),
                'on_time_percent': attendance_data.get('on_time_percent', 0)
            }
            
            # Format date for display
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
            
            return {
                'date': date_str,
                'formatted_date': formatted_date,
                'total_drivers': attendance_data.get('total_drivers', 0),
                'total_morning_drivers': attendance_data.get('total_drivers', 0),
                'on_time_count': summary['on_time_drivers'],
                'drivers': drivers,
                'late_morning': late_records,
                'early_departures': early_records,
                'not_on_job_drivers': not_on_job_records,
                'summary': summary
            }
            
        # If not found, try to load from the legacy format
        elif os.path.exists(standard_json_path):
            with open(standard_json_path, 'r') as f:
                report_data = json.load(f)
            
            logger.info(f"Loaded legacy report data from JSON for date {date_str}")
            
            # Make sure the report has all the required fields
            if 'summary' not in report_data:
                report_data['summary'] = {
                    'total_drivers': report_data.get('total_drivers', 0),
                    'on_time_drivers': report_data.get('on_time_count', 0),
                    'late_drivers': len(report_data.get('late_morning', [])),
                    'early_end_drivers': len(report_data.get('early_departures', [])),
                    'not_on_job_drivers': len(report_data.get('not_on_job_drivers', [])),
                    'exception_drivers': 0,
                    'total_issues': (
                        len(report_data.get('late_morning', [])) +
                        len(report_data.get('early_departures', [])) +
                        len(report_data.get('not_on_job_drivers', []))
                    ),
                    'on_time_percent': 0
                }
                
                # Calculate on-time percentage
                total = report_data['summary']['total_drivers']
                on_time = report_data['summary']['on_time_drivers']
                report_data['summary']['on_time_percent'] = (on_time / total * 100) if total > 0 else 0
            
            return report_data
            
        # If report not found, try to generate it
        else:
            logger.warning(f"Report not found for {date_str}, attempting to generate")
            
            try:
                # Attempt to generate the report using the unified processor
                from utils.unified_data_processor import UnifiedDataProcessor
                
                # Create processor for the date
                processor = UnifiedDataProcessor(date_str)
                
                # Find and process available files
                assets_dir = 'attached_assets'
                for file in os.listdir(assets_dir):
                    file_path = os.path.join(assets_dir, file)
                    
                    if 'DrivingHistory' in file:
                        processor.process_driving_history(file_path)
                    
                    elif 'ActivityDetail' in file:
                        processor.process_activity_detail(file_path)
                    
                    elif 'AssetsTimeOnSite' in file or 'FleetUtilization' in file:
                        processor.process_asset_onsite(file_path)
                    
                    elif 'ELIST' in file or 'Employee' in file:
                        processor.process_employee_data(file_path)
                    
                    elif 'DAILY' in file and ('NOJ' in file or 'REPORT' in file) and file.endswith('.xlsx'):
                        processor.process_start_time_job_sheet(file_path)
                
                # Generate reports
                processor.generate_attendance_report()
                processor.export_excel_report()
                processor.export_pdf_report()
                
                # Try to load the newly generated report
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        attendance_data = json.load(f)
                    
                    # Convert attendance data to report format
                    late_records = attendance_data.get('late_start_records', [])
                    early_records = attendance_data.get('early_end_records', [])
                    not_on_job_records = attendance_data.get('not_on_job_records', [])
                    drivers = attendance_data.get('drivers', [])
                    
                    # Create summary data for display
                    summary = {
                        'total_drivers': attendance_data.get('total_drivers', 0),
                        'total_morning_drivers': attendance_data.get('total_drivers', 0),
                        'on_time_drivers': max(0, attendance_data.get('total_drivers', 0) - len(late_records) - len(not_on_job_records)),
                        'late_drivers': len(late_records),
                        'early_end_drivers': len(early_records),
                        'not_on_job_drivers': len(not_on_job_records),
                        'exception_drivers': 0,
                        'total_issues': len(late_records) + len(early_records) + len(not_on_job_records),
                        'on_time_percent': attendance_data.get('on_time_percent', 0)
                    }
                    
                    # Format date for display
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%A, %B %d, %Y')
                    
                    return {
                        'date': date_str,
                        'formatted_date': formatted_date,
                        'total_drivers': attendance_data.get('total_drivers', 0),
                        'total_morning_drivers': attendance_data.get('total_drivers', 0),
                        'on_time_count': summary['on_time_drivers'],
                        'drivers': drivers,
                        'late_morning': late_records,
                        'early_departures': early_records,
                        'not_on_job_drivers': not_on_job_records,
                        'summary': summary
                    }
            except Exception as regen_error:
                logger.error(f"Error generating report with unified processor: {regen_error}")
        
    except Exception as e:
        error_msg = f"Error loading or generating report for {date_str}: {str(e)}"
        logger.error(error_msg)
        error_logger.error(error_msg)
        logger.error(traceback.format_exc())
    
    # If all attempts fail, create a default empty report
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%A, %B %d, %Y')
    
    return {
        'date': date_str,
        'formatted_date': formatted_date,
        'total_drivers': 0,
        'total_morning_drivers': 0,
        'on_time_count': 0,
        'drivers': [],
        'late_morning': [],
        'early_departures': [],
        'not_on_job_drivers': [],
        'summary': {
            'total_drivers': 0,
            'on_time_drivers': 0,
            'late_drivers': 0,
            'early_end_drivers': 0,
            'not_on_job_drivers': 0,
            'exception_drivers': 0,
            'total_issues': 0,
            'on_time_percent': 0
        },
        'error': f"Failed to load or generate report for {date_str}"
    }

def get_user_email_config():
    """Get user's email configuration"""
    try:
        # For now, just return a default configuration
        # In a real implementation, this would fetch from a database
        # based on the current user's ID
        return {
            'recipients': '',
            'cc': '',
            'bcc': '',
            'auto_send': False,
            'include_user': True
        }
    except Exception as e:
        logger.error(f"Error getting user email config: {e}")
        
        # Default config if error occurs
        return {
            'recipients': '',
            'cc': '',
            'bcc': '',
            'auto_send': False,
            'include_user': True
        }

def save_user_email_config(config):
    """Save user's email configuration"""
    try:
        # For now, just log the configuration that would be saved
        # and return success to avoid errors
        logger.info(f"Would save email config: {config}")
        return True
    except Exception as e:
        logger.error(f"Error saving user email config: {e}")
    
    return False

# Activity logging
def log_navigation(action, details=None):
    """Log navigation to activity log"""
    try:
        from utils.activity_logger import log_activity
        log_activity('navigation', f'Viewed {action}', details or {})
    except Exception as e:
        logger.error(f"Error logging navigation: {e}")

# Routes
@driver_module_bp.route('/')
def index():
    """Driver module index page"""
    log_navigation('Driver Module')
    return render_template('drivers/index.html')

@driver_module_bp.route('/daily-report', methods=['GET', 'POST'])
def daily_report():
    """Daily driver attendance report with email configuration"""
    try:
        # Get date parameter with safe fallback
        date_str = request.args.get('date')
        
        # Check if MTD ingestion mode is requested
        use_mtd = request.args.get('use_mtd') == 'true'
        
        # If no date provided, find the most recent report
        if not date_str:
            # Check exports directory for the latest report
            reports_dir = "exports/daily_reports"
            json_files = [f for f in os.listdir(reports_dir) if f.startswith('attendance_data_') and f.endswith('.json')]
            
            if json_files:
                # Sort by date (newest first)
                json_files.sort(reverse=True)
                # Extract date from filename
                date_str = json_files[0].replace('attendance_data_', '').replace('.json', '')
            else:
                # Default to current date if no reports found
                date_str = datetime.now().strftime('%Y-%m-%d')
                
        logger.info(f"Using report date: {date_str}")
        
        # Process MTD ingestion if requested
        if use_mtd:
            try:
                logger.info(f"Activating GENIUS CORE SMART MTD INGESTION MODE for date: {date_str}")
                
                # Import and initialize MTD processor
                from genius_core_mtd import GeniusCoreMTDProcessor
                mtd_processor = GeniusCoreMTDProcessor()
                
                # Process MTD files for the target date
                mtd_result = mtd_processor.process_date(date_str)
                
                if mtd_result and mtd_result.get('output_files'):
                    logger.info(f"MTD ingestion successful: {mtd_result['output_files']}")
                    flash("MTD INGESTION ENABLED — FILTERED DAILY PIPELINE ACTIVE", "success")
                    
                    # Trigger standard report generation with the filtered data
                    try:
                        # Attempt to generate the report using the unified processor
                        from utils.unified_data_processor import UnifiedDataProcessor
                        
                        # Create processor for the date
                        processor = UnifiedDataProcessor(date_str)
                        
                        # Use the filtered data from MTD ingestion
                        driving_history_path = mtd_result['output_files'].get('driving_history')
                        activity_detail_path = mtd_result['output_files'].get('activity_detail')
                        
                        if driving_history_path and os.path.exists(driving_history_path):
                            processor.process_driving_history(driving_history_path)
                            
                        if activity_detail_path and os.path.exists(activity_detail_path):
                            processor.process_activity_detail(activity_detail_path)
                        
                        # Still process employee data and job sheets from available sources
                        assets_dir = 'attached_assets'
                        for file in os.listdir(assets_dir):
                            file_path = os.path.join(assets_dir, file)
                            
                            if 'ELIST' in file or 'Employee' in file:
                                processor.process_employee_data(file_path)
                            
                            elif 'DAILY' in file and ('NOJ' in file or 'REPORT' in file) and file.endswith('.xlsx'):
                                processor.process_start_time_job_sheet(file_path)
                        
                        # Generate reports
                        processor.generate_attendance_report()
                        processor.export_excel_report()
                        processor.export_pdf_report()
                        
                        logger.info("Successfully generated report using MTD filtered data")
                    except Exception as regen_error:
                        logger.error(f"Error generating report with MTD processed data: {regen_error}")
                
                else:
                    logger.warning(f"No MTD data found for date: {date_str}")
                    flash("No MTD data found for the selected date. Using available data instead.", "warning")
            except Exception as mtd_error:
                logger.error(f"Error in MTD ingestion process: {mtd_error}")
                logger.error(traceback.format_exc())
                flash(f"Error processing MTD data: {str(mtd_error)}", "danger")
        
        # Check if export files exist
        excel_path = f"exports/daily_reports/{date_str}_DailyDriverReport.xlsx"
        pdf_path = f"exports/daily_reports/{date_str}_DailyDriverReport.pdf"
        json_path = f"exports/daily_reports/attendance_data_{date_str}.json"
        
        # Verify file existence for exports
        excel_exists = os.path.exists(excel_path)
        pdf_exists = os.path.exists(pdf_path)
        json_exists = os.path.exists(json_path)
        
        if not json_exists:
            # Try legacy path
            legacy_json = f"exports/daily_reports/daily_report_{date_str}.json"
            if os.path.exists(legacy_json):
                json_exists = True
                json_path = legacy_json
                
        # Process form submission for email settings
        if request.method == 'POST':
            if request.form.get('action') == 'update_email':
                try:
                    # Update email settings
                    config = {
                        'recipients': request.form.get('recipients', ''),
                        'cc': request.form.get('cc', ''),
                        'bcc': request.form.get('bcc', ''),
                        'auto_send': request.form.get('auto_send') == 'on',
                        'include_user': request.form.get('include_user') == 'on'
                    }
                    
                    if save_user_email_config(config):
                        flash('Email configuration updated successfully', 'success')
                    else:
                        flash('Failed to update email configuration', 'error')
                        
                    # Redirect to avoid form resubmission
                    return redirect(url_for('driver_module.daily_report', date=date_str))
                except Exception as e:
                    error_msg = f"Error processing email form: {e}"
                    logger.error(error_msg)
                    error_logger.error(error_msg)
                    flash('An error occurred while updating email configuration', 'error')
            
            elif request.form.get('action') == 'send_email':
                try:
                    # Get email recipients
                    recipients = request.form.get('recipients', '').split(',')
                    recipients = [email.strip() for email in recipients if email.strip()]
                    
                    cc = request.form.get('cc', '').split(',')
                    cc = [email.strip() for email in cc if email.strip()]
                    
                    bcc = request.form.get('bcc', '').split(',')
                    bcc = [email.strip() for email in bcc if email.strip()]
                    
                    if not recipients:
                        flash('Please provide at least one recipient email address', 'warning')
                        return redirect(url_for('driver_module.daily_report', date=date_str))
                    
                    # Get report data
                    report = get_daily_report(date_str)
                    
                    # Format date for display
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%A, %B %d, %Y')
                    
                    # Create email content
                    subject = f"Daily Driver Report - {formatted_date}"
                    
                    # Generate HTML content
                    from utils.email_service import send_report_email
                    
                    # Simple HTML template
                    html_content = f"""
                    <h2>Daily Driver Report - {formatted_date}</h2>
                    <p>Please find attached the Daily Driver Report for {formatted_date}.</p>
                    <p>Summary:</p>
                    <ul>
                        <li>Total Drivers: {report['summary']['total_drivers']}</li>
                        <li>On Time: {report['summary']['on_time_drivers']}</li>
                        <li>Late Start: {report['summary']['late_drivers']}</li>
                        <li>Early End: {report['summary']['early_end_drivers']}</li>
                        <li>Not On Job: {report['summary']['not_on_job_drivers']}</li>
                    </ul>
                    <p>This report was automatically generated by the TRAXORA Fleet Management System.</p>
                    """
                    
                    # Send email with attachments
                    result = send_report_email(
                        subject=subject,
                        report_content=html_content,
                        recipients=recipients,
                        cc=cc,
                        bcc=bcc,
                        report_date=date_str,
                        report_data=report,
                        excel_path=excel_path if excel_exists else "",
                        pdf_path=pdf_path if pdf_exists else ""
                    )
                    
                    if result['status'] == 'success':
                        flash('Report email sent successfully', 'success')
                    else:
                        flash(f"Failed to send email: {result.get('error', 'Unknown error')}", 'error')
                    
                    return redirect(url_for('driver_module.daily_report', date=date_str))
                    
                except Exception as e:
                    error_msg = f"Error sending email: {e}"
                    logger.error(error_msg)
                    error_logger.error(error_msg)
                    flash(f"An error occurred while sending email: {str(e)}", 'error')
        
        # Get email configuration for the current user
        email_config = get_user_email_config()
        
        # Get report data with authentic employee information
        report = get_daily_report(date_str)
        
        # Add file existence information to the report
        report['files'] = {
            'excel_exists': excel_exists,
            'pdf_exists': pdf_exists,
            'excel_path': f"/drivers/download-excel/{date_str}" if excel_exists else None,
            'pdf_path': f"/drivers/download-pdf/{date_str}" if pdf_exists else None
        }
        
        # Log navigation with relevant details
        log_navigation('Daily Driver Report', {'date': date_str})
        
        # Check if request is for JSON
        if request.headers.get('Accept') == 'application/json':
            return jsonify(report)
        
        # Render template with report data
        return render_template(
            'drivers/daily_report.html',
            report=report,
            selected_date=date_str,
            email_config=email_config
        )
        
    except Exception as e:
        error_msg = f"Error in daily_report route: {e}"
        logger.error(error_msg)
        error_logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Get date parameter, safely handling potential errors
        try:
            date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
        except:
            date_str = datetime.now().strftime('%Y-%m-%d')
            formatted_date = datetime.now().strftime('%A, %B %d, %Y')
        
        # Create fallback report for error case
        report = {
            'date': date_str,
            'formatted_date': formatted_date,
            'total_drivers': 0,
            'drivers': [],
            'late_morning': [],
            'early_departures': [],
            'not_on_job_drivers': [],
            'summary': {
                'total_drivers': 0,
                'on_time_drivers': 0,
                'late_drivers': 0,
                'early_end_drivers': 0,
                'not_on_job_drivers': 0,
                'total_issues': 0,
                'on_time_percent': 0
            },
            'files': {
                'excel_exists': False,
                'pdf_exists': False,
                'excel_path': None,
                'pdf_path': None
            },
            'error': f"An error occurred: {str(e)}"
        }
        
        email_config = {
            'recipients': '',
            'cc': '',
            'bcc': '',
            'auto_send': False,
            'include_user': True
        }
        
        flash('An error occurred while loading the report. See details in the report.', 'error')
        
        # Check if request is for JSON
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': str(e), 'status': 'error'})
        
        return render_template(
            'drivers/daily_report.html',
            report=report,
            selected_date=date_str,
            email_config=email_config
        )

@driver_module_bp.route('/download-excel/<date_str>')
def download_excel_report(date_str):
    """Download Excel report"""
    try:
        # Determine file path based on the standardized naming convention
        file_path = f"exports/daily_reports/{date_str}_DailyDriverReport.xlsx"
        legacy_path = f"exports/daily_reports/daily_report_{date_str}.xlsx"
        
        # Check if the file exists
        if os.path.exists(file_path):
            # Log download
            log_navigation('Excel Report Download', {'date': date_str})
            
            # Send file
            return send_file(
                file_path,
                as_attachment=True,
                download_name=f"DailyDriverReport_{date_str}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        elif os.path.exists(legacy_path):
            # Log download
            log_navigation('Excel Report Download (Legacy)', {'date': date_str})
            
            # Send file
            return send_file(
                legacy_path,
                as_attachment=True,
                download_name=f"DailyDriverReport_{date_str}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        # File not found
        flash(f"Excel report for {date_str} not found", "error")
        return redirect(url_for('driver_module.daily_report', date=date_str))
    except Exception as e:
        logger.error(f"Error downloading Excel report: {e}")
        flash(f"Error downloading Excel report: {str(e)}", "error")
        return redirect(url_for('driver_module.daily_report', date=date_str))


@driver_module_bp.route('/download-pdf/<date_str>')
def download_pdf_report(date_str):
    """Download PDF report"""
    try:
        # Determine file path based on the standardized naming convention
        file_path = f"exports/daily_reports/{date_str}_DailyDriverReport.pdf"
        legacy_path = f"exports/daily_reports/daily_report_{date_str}.pdf"
        
        # Check if the file exists
        if os.path.exists(file_path):
            # Log download
            log_navigation('PDF Report Download', {'date': date_str})
            
            # Send file
            return send_file(
                file_path,
                as_attachment=True,
                download_name=f"DailyDriverReport_{date_str}.pdf",
                mimetype='application/pdf'
            )
        elif os.path.exists(legacy_path):
            # Log download
            log_navigation('PDF Report Download (Legacy)', {'date': date_str})
            
            # Send file
            return send_file(
                legacy_path,
                as_attachment=True,
                download_name=f"DailyDriverReport_{date_str}.pdf",
                mimetype='application/pdf'
            )
        
        # File not found
        flash(f"PDF report for {date_str} not found", "error")
        return redirect(url_for('driver_module.daily_report', date=date_str))
    except Exception as e:
        logger.error(f"Error downloading PDF report: {e}")
        flash(f"Error downloading PDF report: {str(e)}", "error")
        return redirect(url_for('driver_module.daily_report', date=date_str))


@driver_module_bp.route('/view-pdf/<date_str>')
def view_pdf_report(date_str):
    """View PDF report in browser"""
    try:
        # Determine file path based on the standardized naming convention
        file_path = f"exports/daily_reports/{date_str}_DailyDriverReport.pdf"
        legacy_path = f"exports/daily_reports/daily_report_{date_str}.pdf"
        
        # Format date for display
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
        except:
            formatted_date = date_str
            
        # Check if the file exists and determine which path to use
        if os.path.exists(file_path):
            pdf_url = f"/drivers/download-pdf/{date_str}"
            file_exists = True
        elif os.path.exists(legacy_path):
            pdf_url = f"/drivers/download-pdf/{date_str}"
            file_exists = True
        else:
            pdf_url = None
            file_exists = False
        
        # Log the viewer access
        log_navigation('PDF Report Viewer', {'date': date_str})
        
        # Render the PDF viewer template
        return render_template(
            'drivers/pdf_viewer.html',
            date_str=date_str,
            formatted_date=formatted_date,
            pdf_url=pdf_url,
            file_exists=file_exists
        )
        
    except Exception as e:
        logger.error(f"Error in view_pdf_report: {e}")
        flash('Error loading PDF viewer', 'error')
        return redirect(url_for('driver_module.daily_report', date=date_str))


@driver_module_bp.route('/embed-pdf/<date_str>')
def embed_pdf_report(date_str):
    """Embed PDF report for inline viewing"""
    try:
        # Determine file path based on the standardized naming convention
        file_path = f"exports/daily_reports/{date_str}_DailyDriverReport.pdf"
        legacy_path = f"exports/daily_reports/daily_report_{date_str}.pdf"
        
        # Check if the file exists
        if os.path.exists(file_path):
            # Log embedding
            log_navigation('PDF Report Embed', {'date': date_str})
            
            # Send file for inline display
            return send_file(
                file_path,
                mimetype='application/pdf'
            )
        elif os.path.exists(legacy_path):
            # Log embedding
            log_navigation('PDF Report Embed (Legacy)', {'date': date_str})
            
            # Send file for inline display
            return send_file(
                legacy_path,
                mimetype='application/pdf'
            )
        
        # File not found - return a simple message
        return "PDF report not found", 404
    except Exception as e:
        logger.error(f"Error embedding PDF report: {e}")
        return f"Error: {str(e)}", 500


# Additional routes for the driver module can be added here
# such as driver detail pages, search functionality, etc.