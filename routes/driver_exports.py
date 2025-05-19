"""
Driver export functionality module for TRAXORA

This module provides specialized export functionality for driver reports,
including the new Daily Driver reports with 8am and 10am export options.
"""
import os
import logging
from datetime import datetime, time, timedelta
from flask import Blueprint, request, redirect, url_for, flash, send_file, render_template
from flask_login import login_required, current_user

from app import db
from utils.export_functions import (
    ensure_exports_folder, 
    generate_unique_filename,
    export_to_csv,
    export_to_excel,
    export_dataframe
)
from utils.email_sender import send_email

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
driver_exports_bp = Blueprint('driver_exports', __name__)

# Define exports folder
EXPORTS_FOLDER = 'exports'
DRIVER_EXPORTS_FOLDER = 'exports/driver_reports'

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


@driver_exports_bp.route('/daily_driver_report', methods=['GET', 'POST'])
@login_required
def daily_driver_report():
    """Generate Daily Driver report with 8am and 10am export options"""
    try:
        # Get request parameters
        export_time = request.args.get('export_time', '8am')  # Default to 8am report
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        region_id = request.args.get('region')
        export_format = request.args.get('format', 'xlsx')
        direct_download = request.args.get('direct', 'false') == 'true'
        
        # Parse the date for filtering records
        try:
            report_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            report_date = datetime.now().date()
            
        # Set time threshold based on export_time parameter
        if export_time == '9am':
            time_threshold = time(9, 0)  # 9:00 AM
            report_title = "9 AM Daily Driver Report"
            filename_prefix = "9am_driver_report"
        else:
            time_threshold = time(8, 0)  # 8:00 AM
            report_title = "8 AM Daily Driver Report"
            filename_prefix = "8am_driver_report"
            
        logger.info(f"Generating {export_time} Daily Driver report for {report_date}")
        
        # Import database models
        from models.driver_attendance import AttendanceRecord, DriverAttendance, JobSiteAttendance
        
        # Prepare data for the report
        attendance_records = []
        
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
            
            # Process records for export based on the time threshold
            for record, driver, job_site in records:
                # Determine if late based on expected start time and threshold time
                expected_start = None
                if record.expected_start_time:
                    if isinstance(record.expected_start_time, str):
                        try:
                            expected_start = datetime.strptime(record.expected_start_time, '%H:%M').time()
                        except ValueError:
                            # Try another format
                            try:
                                expected_start = datetime.strptime(record.expected_start_time, '%I:%M %p').time()
                            except ValueError:
                                expected_start = None
                    elif isinstance(record.expected_start_time, time):
                        expected_start = record.expected_start_time
                
                # Determine actual start time
                actual_start = None
                if record.actual_start_time:
                    if isinstance(record.actual_start_time, str):
                        try:
                            actual_start = datetime.strptime(record.actual_start_time, '%H:%M').time()
                        except ValueError:
                            # Try another format
                            try:
                                actual_start = datetime.strptime(record.actual_start_time, '%I:%M %p').time()
                            except ValueError:
                                actual_start = None
                    elif isinstance(record.actual_start_time, time):
                        actual_start = record.actual_start_time
                
                # Determine status based on export time
                # For 8am report: Only mark as late if expected start is before 8am and actual start is after 8am
                # For 10am report: Show all records, marking records as late if they started after expected time
                
                status = "On Time"
                include_in_report = True
                
                if export_time == '8am':
                    # Only include records where expected start is before 8am
                    if expected_start and expected_start < time_threshold:
                        if actual_start and actual_start > time_threshold:
                            status = "Late Start"
                        elif record.late_start:
                            status = "Late Start"
                    else:
                        # Skip records that don't need to start before 8am
                        include_in_report = False
                else:  # 9am report
                    # Include all records for the day
                    if record.late_start:
                        status = "Late Start"
                    elif record.early_end:
                        status = "Early End"
                    elif record.not_on_job:
                        status = "Not on Job"
                
                # Calculate time difference if available
                time_diff = None
                if expected_start and actual_start:
                    # Convert times to datetime for subtraction
                    expected_dt = datetime.combine(report_date, expected_start)
                    actual_dt = datetime.combine(report_date, actual_start)
                    # Calculate difference in minutes
                    diff = actual_dt - expected_dt
                    time_diff = int(diff.total_seconds() / 60)  # Convert to minutes
                
                if include_in_report:
                    attendance_records.append({
                        'Employee ID': driver.employee_id if hasattr(driver, 'employee_id') else '',
                        'Name': driver.full_name if hasattr(driver, 'full_name') else driver.name if hasattr(driver, 'name') else '',
                        'Division': driver.division if hasattr(driver, 'division') else '',
                        'Job Site': job_site.name if job_site and hasattr(job_site, 'name') else 'Unknown',
                        'Status': status,
                        'Date': report_date.strftime('%Y-%m-%d'),
                        'Expected Start': expected_start.strftime('%H:%M') if expected_start else '',
                        'Actual Start': actual_start.strftime('%H:%M') if actual_start else '',
                        'Minutes Late': time_diff if time_diff and time_diff > 0 else '',
                        'Notes': record.notes if hasattr(record, 'notes') else '',
                        'Vehicle': record.asset_id if hasattr(record, 'asset_id') else ''
                    })
            
            # Define column order for export
            column_order = [
                'Employee ID', 'Name', 'Division', 'Job Site', 'Status',
                'Date', 'Expected Start', 'Actual Start', 'Minutes Late', 'Notes', 'Vehicle'
            ]
            
            # Sort by status (late first) then by name
            attendance_records.sort(key=lambda x: (0 if x['Status'] == 'Late Start' else 1, x['Name']))
            
            # Ensure the export directory exists
            driver_export_dir = os.path.join(DRIVER_EXPORTS_FOLDER, export_time)
            os.makedirs(driver_export_dir, exist_ok=True)
            
            # Create filename with date
            filename = f"{filename_prefix}_{report_date.strftime('%Y%m%d')}"
            if region_id:
                filename += f"_{region_id}"
            
            # Create the export file
            if export_format.lower() == 'csv':
                export_path = os.path.join(driver_export_dir, f"{filename}.csv")
                
                # Export using pandas DataFrame for better handling
                import pandas as pd
                df = pd.DataFrame(attendance_records)
                # Reorder columns
                df = df[column_order]
                df.to_csv(export_path, index=False)
            else:  # Default to Excel
                export_path = os.path.join(driver_export_dir, f"{filename}.xlsx")
                
                # Use the export_dataframe function from utils
                export_dataframe(
                    df=pd.DataFrame(attendance_records)[column_order],
                    filename=filename,
                    format_type='xlsx',
                    subfolder=f'driver_reports/{export_time}',
                    title=f"{report_title} - {report_date.strftime('%Y-%m-%d')}"
                )
            
            # Create download URL
            download_url = url_for('driver_exports.download_export', 
                                   folder=f'driver_reports/{export_time}', 
                                   filename=os.path.basename(export_path))
            
            # Return appropriate response
            if direct_download:
                return send_file(export_path, as_attachment=True)
            else:
                flash(f"{export_time} Daily Driver report generated successfully. <a href='{download_url}'>Download Report</a>", "success")
                
                # Redirect back to driver module view
                return redirect(url_for('driver_module.daily_report', date=date_param))
                
        except Exception as e:
            logger.error(f"Error generating Daily Driver report: {str(e)}", exc_info=True)
            flash(f"Error generating report: {str(e)}", "danger")
            return redirect(url_for('driver_module.daily_report'))
        
    except Exception as e:
        logger.error(f"Error in daily_driver_report: {str(e)}", exc_info=True)
        flash(f"Error generating report: {str(e)}", "danger")
        return redirect(url_for('driver_module.index'))


@driver_exports_bp.route('/email_driver_report', methods=['GET'])
@login_required
def email_driver_report():
    """Email Daily Driver report with 8am and 9am export options"""
    try:
        # Get request parameters
        export_time = request.args.get('export_time', '8am')  # Default to 8am report
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        region_id = request.args.get('region')
        recipient_email = request.args.get('email')
        
        # Parse the date for filtering records
        try:
            report_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            report_date = datetime.now().date()
            
        # Set time threshold based on export_time parameter
        if export_time == '9am':
            time_threshold = time(9, 0)  # 9:00 AM
            report_title = "9 AM Daily Driver Report"
            filename_prefix = "9am_driver_report"
        else:
            time_threshold = time(8, 0)  # 8:00 AM
            report_title = "8 AM Daily Driver Report"
            filename_prefix = "8am_driver_report"
            
        logger.info(f"Preparing {export_time} Daily Driver report email for {report_date}")
        
        # Import database models
        from models.driver_attendance import AttendanceRecord, DriverAttendance, JobSiteAttendance
        
        # Prepare data for the report
        attendance_records = []
        
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
            
            # Process records for export based on the time threshold
            for record, driver, job_site in records:
                # Determine if late based on expected start time and threshold time
                expected_start = None
                if record.expected_start_time:
                    if isinstance(record.expected_start_time, str):
                        try:
                            expected_start = datetime.strptime(record.expected_start_time, '%H:%M').time()
                        except ValueError:
                            # Try another format
                            try:
                                expected_start = datetime.strptime(record.expected_start_time, '%I:%M %p').time()
                            except ValueError:
                                expected_start = None
                    elif isinstance(record.expected_start_time, time):
                        expected_start = record.expected_start_time
                
                # Determine actual start time
                actual_start = None
                if record.actual_start_time:
                    if isinstance(record.actual_start_time, str):
                        try:
                            actual_start = datetime.strptime(record.actual_start_time, '%H:%M').time()
                        except ValueError:
                            # Try another format
                            try:
                                actual_start = datetime.strptime(record.actual_start_time, '%I:%M %p').time()
                            except ValueError:
                                actual_start = None
                    elif isinstance(record.actual_start_time, time):
                        actual_start = record.actual_start_time
                
                # Determine status based on export time
                # For 8am report: Only mark as late if expected start is before 8am and actual start is after 8am
                # For 9am report: Show all records, marking records as late if they started after expected time
                
                status = "On Time"
                include_in_report = True
                
                if export_time == '8am':
                    # Only include records where expected start is before 8am
                    if expected_start and expected_start < time_threshold:
                        if actual_start and actual_start > time_threshold:
                            status = "Late Start"
                        elif record.late_start:
                            status = "Late Start"
                    else:
                        # Skip records that don't need to start before 8am
                        include_in_report = False
                else:  # 9am report
                    # Include all records for the day
                    if record.late_start:
                        status = "Late Start"
                    elif record.early_end:
                        status = "Early End"
                    elif record.not_on_job:
                        status = "Not on Job"
                
                # Calculate time difference if available
                time_diff = None
                if expected_start and actual_start:
                    # Convert times to datetime for subtraction
                    expected_dt = datetime.combine(report_date, expected_start)
                    actual_dt = datetime.combine(report_date, actual_start)
                    # Calculate difference in minutes
                    diff = actual_dt - expected_dt
                    time_diff = int(diff.total_seconds() / 60)  # Convert to minutes
                
                if include_in_report:
                    attendance_records.append({
                        'Employee ID': driver.employee_id if hasattr(driver, 'employee_id') else '',
                        'Name': driver.full_name if hasattr(driver, 'full_name') else driver.name if hasattr(driver, 'name') else '',
                        'Division': driver.division if hasattr(driver, 'division') else '',
                        'Job Site': job_site.name if job_site and hasattr(job_site, 'name') else 'Unknown',
                        'Status': status,
                        'Date': report_date.strftime('%Y-%m-%d'),
                        'Expected Start': expected_start.strftime('%H:%M') if expected_start else '',
                        'Actual Start': actual_start.strftime('%H:%M') if actual_start else '',
                        'Minutes Late': time_diff if time_diff and time_diff > 0 else '',
                        'Notes': record.notes if hasattr(record, 'notes') else '',
                        'Vehicle': record.asset_id if hasattr(record, 'asset_id') else ''
                    })
            
            # Define column order for export
            column_order = [
                'Employee ID', 'Name', 'Division', 'Job Site', 'Status',
                'Date', 'Expected Start', 'Actual Start', 'Minutes Late', 'Notes', 'Vehicle'
            ]
            
            # Sort by status (late first) then by name
            attendance_records.sort(key=lambda x: (0 if x['Status'] == 'Late Start' else 1, x['Name']))

            # Ensure the export directory exists
            driver_export_dir = os.path.join(DRIVER_EXPORTS_FOLDER, export_time)
            os.makedirs(driver_export_dir, exist_ok=True)
            
            # Create filename with date
            filename = f"{filename_prefix}_{report_date.strftime('%Y%m%d')}"
            if region_id:
                filename += f"_{region_id}"
            
            # Create the export file for attaching to email
            export_path = os.path.join(driver_export_dir, f"{filename}.xlsx")
            
            # Use pandas for export
            import pandas as pd
            df = pd.DataFrame(attendance_records)
            # Reorder columns
            df = df[column_order]
            
            # Export to Excel for email attachment
            export_dataframe(
                df=df,
                filename=filename,
                format_type='xlsx',
                subfolder=f'driver_reports/{export_time}',
                title=f"{report_title} - {report_date.strftime('%Y-%m-%d')}"
            )
            
            # Create HTML table for email content
            html_table = '<table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse; width: 100%;">'
            
            # Add header
            html_table += '<thead style="background-color: #4472C4; color: white;"><tr>'
            for col in column_order:
                html_table += f'<th>{col}</th>'
            html_table += '</tr></thead><tbody>'
            
            # Add data rows
            for i, record in enumerate(attendance_records):
                row_style = ' style="background-color: #E6E6E6;"' if i % 2 == 0 else ''
                status_style = ''
                if record['Status'] == 'Late Start':
                    status_style = ' style="background-color: #FFCCCC;"'
                elif record['Status'] == 'Early End':
                    status_style = ' style="background-color: #FFFFCC;"'
                elif record['Status'] == 'Not on Job':
                    status_style = ' style="background-color: #CCCCFF;"'
                
                html_table += f'<tr{row_style}>'
                for col in column_order:
                    if col == 'Status':
                        html_table += f'<td{status_style}>{record.get(col, "")}</td>'
                    else:
                        html_table += f'<td>{record.get(col, "")}</td>'
                html_table += '</tr>'
            
            html_table += '</tbody></table>'
            
            # Create email subject
            subject = f"TRAXORA {report_title} - {report_date.strftime('%B %d, %Y')}"
            
            # Create email HTML content
            html_content = f"""
            <html>
            <body>
                <h2>{report_title} - {report_date.strftime('%B %d, %Y')}</h2>
                <p>Please find the {export_time} Daily Driver Report attached and below.</p>
                
                <h3>Summary</h3>
                <p>
                    <strong>Total Drivers:</strong> {len(attendance_records)}<br>
                    <strong>On Time:</strong> {len([r for r in attendance_records if r['Status'] == 'On Time'])}<br>
                    <strong>Late Start:</strong> {len([r for r in attendance_records if r['Status'] == 'Late Start'])}<br>
                    <strong>Early End:</strong> {len([r for r in attendance_records if r['Status'] == 'Early End'])}<br>
                    <strong>Not on Job:</strong> {len([r for r in attendance_records if r['Status'] == 'Not on Job'])}
                </p>
                
                <h3>Detailed Report</h3>
                {html_table}
                
                <p>
                    <em>This report was automatically generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.</em><br>
                    <em>Please do not reply to this email. For any issues, contact support@systemsmith.com.</em>
                </p>
            </body>
            </html>
            """
            
            # Get email recipients
            recipients = []
            
            # If email is provided as a parameter, use it
            if recipient_email:
                recipients = [recipient_email]
            else:
                # Use system default recipients if available
                default_recipients = [
                    'driver-reports@systemsmith.com',
                    'operations@systemsmith.com'
                ]
                
                # If current user has email, include it
                if hasattr(current_user, 'email') and current_user.email:
                    recipients = [current_user.email] + default_recipients
                else:
                    recipients = default_recipients
            
            # Send email using the imported send_email function
            try:
                # Get the absolute path to the exported file
                attachment_path = os.path.join(os.getcwd(), EXPORTS_FOLDER, f'driver_reports/{export_time}', f"{filename}.xlsx")
                
                # Send email with attachment
                success, message = send_email(
                    subject=subject,
                    html_content=html_content,
                    recipients=recipients
                )
                
                if success:
                    flash(f"Successfully sent {export_time} report to {', '.join(recipients)}", "success")
                else:
                    flash(f"Error sending email: {message}", "warning")
                    
                # Log the action
                logger.info(f"Email for {export_time} Daily Driver report sent to {', '.join(recipients)}")
                
            except Exception as e:
                logger.error(f"Failed to send email: {str(e)}", exc_info=True)
                flash(f"Failed to send email: {str(e)}", "danger")
                
            return redirect(url_for('driver_module.daily_report', date=date_param))
            
        except Exception as e:
            logger.error(f"Error generating report for email: {str(e)}", exc_info=True)
            flash(f"Error generating report for email: {str(e)}", "danger")
            return redirect(url_for('driver_module.daily_report', date=date_param))
            
    except Exception as e:
        logger.error(f"Error in email_driver_report: {str(e)}", exc_info=True)
        flash(f"Error sending report: {str(e)}", "danger")
        return redirect(url_for('driver_module.daily_report'))


@driver_exports_bp.route('/download_export', methods=['GET'])
@login_required
def download_export():
    """Download a previously exported file"""
    try:
        folder = request.args.get('folder', '')
        filename = request.args.get('filename', '')
        
        if not filename:
            flash("No filename provided", "danger")
            return redirect(url_for('driver_module.index'))
        
        # Construct file path based on folder parameter
        if folder:
            file_path = os.path.join(EXPORTS_FOLDER, folder, filename)
        else:
            file_path = os.path.join(EXPORTS_FOLDER, filename)
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash(f"Requested file not found: {filename}", "danger")
            return redirect(url_for('driver_module.index'))
    except Exception as e:
        logger.error(f"Error downloading export: {str(e)}")
        flash(f"Error downloading export: {str(e)}", "danger")
        return redirect(url_for('driver_module.index'))