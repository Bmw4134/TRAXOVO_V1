"""
Driver export functionality module for TRAXORA
"""
import os
import logging
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, flash, send_file
from flask_login import login_required

from app import db
from utils.export_functions import (
    ensure_exports_folder, 
    generate_unique_filename,
    export_to_csv,
    export_to_excel
)

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
driver_exports_bp = Blueprint('driver_exports', __name__)

# Define exports folder
EXPORTS_FOLDER = 'exports'

@driver_exports_bp.route('/export_report', methods=['GET'])
@login_required
def export_report():
    """Export a driver report using real database data"""
    # Get request parameters
    report_type = request.args.get('type', 'daily')
    export_format = request.args.get('format', 'xlsx')
    date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    region_id = request.args.get('region')
    direct_download = request.args.get('direct', 'false') == 'true'
    
    try:
        # Parse the date for filtering records
        try:
            report_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            report_date = datetime.now().date()
        
        # Ensure exports folder exists
        ensure_exports_folder()
        
        # Generate unique filename
        filename = generate_unique_filename(report_type, report_date, region_id, export_format)
        file_path = os.path.join(EXPORTS_FOLDER, filename)
        
        # Import database models
        from models.driver_attendance import AttendanceRecord, DriverAttendance, JobSiteAttendance
        
        # Prepare data for the report
        attendance_records = []
        
        if report_type == 'daily':
            try:
                # Query for attendance records on the specified date
                query = db.session.query(
                    AttendanceRecord, DriverAttendance, JobSiteAttendance
                ).join(
                    DriverAttendance, AttendanceRecord.driver_id == DriverAttendance.id
                ).join(
                    JobSiteAttendance, AttendanceRecord.assigned_job_id == JobSiteAttendance.id, isouter=True
                ).filter(
                    AttendanceRecord.date == report_date
                )
                
                # Apply region filter if specified
                if region_id:
                    query = query.filter(DriverAttendance.division == region_id)
                
                # Execute the query
                records = query.all()
                
                # Process records for export
                for record, driver, job_site in records:
                    status = "On Time"
                    if record.late_start:
                        status = "Late Start"
                    elif record.early_end:
                        status = "Early End"
                    elif record.not_on_job:
                        status = "Not on Job"
                    
                    attendance_records.append({
                        'employee_id': driver.employee_id,
                        'name': driver.full_name,
                        'division': driver.division or 'Unknown',
                        'job_site': job_site.name if job_site else 'Unknown',
                        'status': status,
                        'date': record.date,
                        'expected_start': record.expected_start_time,
                        'actual_start': record.actual_start_time,
                        'expected_end': record.expected_end_time,
                        'actual_end': record.actual_end_time,
                        'notes': record.notes,
                        'vehicle': record.asset_id
                    })
                
                # Define field mappings for export (field_name -> display_name)
                field_mappings = {
                    'employee_id': 'Employee ID',
                    'name': 'Name',
                    'division': 'Division',
                    'job_site': 'Job Site',
                    'status': 'Status',
                    'date': 'Date',
                    'expected_start': 'Expected Start',
                    'actual_start': 'Actual Start',
                    'expected_end': 'Expected End',
                    'actual_end': 'Actual End',
                    'notes': 'Notes',
                    'vehicle': 'Vehicle'
                }
                
                # Create the export file
                if export_format == 'csv':
                    export_to_csv(file_path, attendance_records, field_mappings.keys())
                elif export_format == 'xlsx':
                    export_to_excel(file_path, attendance_records, field_mappings, sheet_title="Driver Attendance")
                else:
                    flash(f"Unsupported format: {export_format}", "danger")
                    return redirect(url_for('driver_module.daily_report'))
                
            except Exception as e:
                logger.error(f"Error creating export: {str(e)}", exc_info=True)
                flash(f"Error creating export: {str(e)}", "danger")
                return redirect(url_for('driver_module.daily_report'))
        
        else:
            flash(f"Unsupported report type: {report_type}", "danger")
            return redirect(url_for('driver_module.index'))
        
        # Log the export
        logger.info(f"Successfully generated {report_type} report in {export_format} format")
        
        # Create download URL
        download_url = url_for('driver_exports.download_export', filename=filename)
        
        # Return appropriate response
        if direct_download:
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            flash(f"Report generated successfully. <a href='{download_url}'>Download {filename}</a>", "success")
            
            if report_type == 'daily':
                return redirect(url_for('driver_module.daily_report', date=date_param))
            else:
                return redirect(url_for('driver_module.index'))
    
    except Exception as e:
        logger.error(f"Error in export_report: {str(e)}", exc_info=True)
        flash(f"Error generating report: {str(e)}", "danger")
        return redirect(url_for('driver_module.index'))


@driver_exports_bp.route('/download_export/<filename>', methods=['GET'])
@login_required
def download_export(filename):
    """Download a previously exported file"""
    try:
        file_path = os.path.join(EXPORTS_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            flash(f"Requested file not found: {filename}", "danger")
            return redirect(url_for('driver_module.index'))
    except Exception as e:
        logger.error(f"Error downloading export: {str(e)}")
        flash(f"Error downloading export: {str(e)}", "danger")
        return redirect(url_for('driver_module.index'))