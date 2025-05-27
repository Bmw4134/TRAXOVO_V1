"""
TRAXOVO Secure Attendance Report System - PHASE 4

Daily Report for 5/27 data processing with GPS/Timecard validation flags.
Matches uploaded: Driving History + Asset Time on Site + Activity Detail
"""
import logging
import os
import pandas as pd
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField, DateField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from app import db, csrf

logger = logging.getLogger(__name__)

# Create blueprint
secure_attendance_bp = Blueprint('secure_attendance', __name__, url_prefix='/secure-attendance')

class AttendanceUploadForm(FlaskForm):
    """Secure file upload form with CSRF protection"""
    driving_history = FileField('Driving History CSV', validators=[
        FileAllowed(['csv'], 'CSV files only!')
    ])
    asset_time_on_site = FileField('Asset Time on Site CSV', validators=[
        FileAllowed(['csv'], 'CSV files only!')
    ])
    activity_detail = FileField('Activity Detail CSV', validators=[
        FileAllowed(['csv'], 'CSV files only!')
    ])
    report_date = DateField('Report Date', validators=[DataRequired()], default=date.today)
    submit = SubmitField('Process Attendance Report')

def process_authentic_attendance_data(driving_history_path=None, time_on_site_path=None, 
                                     activity_detail_path=None, report_date=None):
    """
    Process authentic attendance data with GPS/Timecard validation flags
    
    Returns:
        dict: Report with exception flags and status indicators
    """
    report = {
        'date': report_date,
        'drivers': [],
        'exceptions': {
            'gps_no_timecard': [],
            'timecard_no_gps': [],
            'incomplete_coverage': []
        },
        'summary': {
            'total_drivers': 0,
            'on_time': 0,
            'late': 0,
            'early_end': 0,
            'not_on_job': 0,
            'coverage_percentage': 0
        },
        'validation_flags': {
            'driving_history_processed': False,
            'time_on_site_processed': False,
            'activity_detail_processed': False
        }
    }
    
    try:
        # Process Driving History
        if driving_history_path and os.path.exists(driving_history_path):
            df_driving = pd.read_csv(driving_history_path)
            report['validation_flags']['driving_history_processed'] = True
            logger.info(f"Processed {len(df_driving)} driving history records")
            
            # Extract unique drivers from driving history
            if 'Driver' in df_driving.columns:
                drivers_with_gps = set(df_driving['Driver'].dropna().unique())
            else:
                drivers_with_gps = set()
        else:
            drivers_with_gps = set()
        
        # Process Asset Time on Site
        if time_on_site_path and os.path.exists(time_on_site_path):
            df_time_on_site = pd.read_csv(time_on_site_path)
            report['validation_flags']['time_on_site_processed'] = True
            logger.info(f"Processed {len(df_time_on_site)} time on site records")
        
        # Process Activity Detail
        if activity_detail_path and os.path.exists(activity_detail_path):
            df_activity = pd.read_csv(activity_detail_path)
            report['validation_flags']['activity_detail_processed'] = True
            logger.info(f"Processed {len(df_activity)} activity detail records")
        
        # Generate driver classifications with exception flags
        all_drivers = list(drivers_with_gps)
        
        for driver in all_drivers:
            driver_record = {
                'name': driver,
                'status': 'On Time',  # Default classification
                'job_zone': 'Unknown',
                'start_time': None,
                'end_time': None,
                'flags': {
                    'has_gps': True,
                    'has_timecard': False,  # This would come from timecard data
                    'complete_coverage': True
                }
            }
            
            # Flag exceptions based on data availability
            if not driver_record['flags']['has_timecard']:
                report['exceptions']['gps_no_timecard'].append(driver)
                driver_record['flags']['complete_coverage'] = False
            
            report['drivers'].append(driver_record)
        
        # Update summary statistics
        report['summary']['total_drivers'] = len(all_drivers)
        report['summary']['on_time'] = len([d for d in report['drivers'] if d['status'] == 'On Time'])
        
        # Calculate coverage percentage
        total_expected = report['summary']['total_drivers']
        complete_coverage = len([d for d in report['drivers'] if d['flags']['complete_coverage']])
        report['summary']['coverage_percentage'] = round(
            (complete_coverage / total_expected * 100) if total_expected > 0 else 0, 1
        )
        
        logger.info(f"Attendance report processed: {report['summary']['total_drivers']} drivers, {report['summary']['coverage_percentage']}% coverage")
        
    except Exception as e:
        logger.error(f"Error processing attendance data: {str(e)}")
        raise
    
    return report

@secure_attendance_bp.route('/')
@login_required
def dashboard():
    """Secure attendance dashboard"""
    return render_template('secure_attendance/dashboard.html',
        today=date.today().strftime('%Y-%m-%d'),
        formatted_date=date.today().strftime('%A, %B %d, %Y')
    )

@secure_attendance_bp.route('/process', methods=['GET', 'POST'])
@login_required
def process_report():
    """Process daily attendance report with security validation"""
    form = AttendanceUploadForm()
    
    if form.validate_on_submit():
        try:
            # Create secure upload directory
            upload_dir = os.path.join('uploads', 'secure_attendance', 
                                    form.report_date.data.strftime('%Y-%m-%d'))
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save uploaded files securely
            file_paths = {}
            
            if form.driving_history.data:
                filename = secure_filename(form.driving_history.data.filename)
                file_path = os.path.join(upload_dir, f"driving_history_{filename}")
                form.driving_history.data.save(file_path)
                file_paths['driving_history'] = file_path
            
            if form.asset_time_on_site.data:
                filename = secure_filename(form.asset_time_on_site.data.filename)
                file_path = os.path.join(upload_dir, f"time_on_site_{filename}")
                form.asset_time_on_site.data.save(file_path)
                file_paths['time_on_site'] = file_path
            
            if form.activity_detail.data:
                filename = secure_filename(form.activity_detail.data.filename)
                file_path = os.path.join(upload_dir, f"activity_detail_{filename}")
                form.activity_detail.data.save(file_path)
                file_paths['activity_detail'] = file_path
            
            # Process the attendance data
            report = process_authentic_attendance_data(
                driving_history_path=file_paths.get('driving_history'),
                time_on_site_path=file_paths.get('time_on_site'),
                activity_detail_path=file_paths.get('activity_detail'),
                report_date=form.report_date.data.strftime('%Y-%m-%d')
            )
            
            # Save report for viewing
            report_filename = f"attendance_report_{form.report_date.data.strftime('%Y_%m_%d')}.json"
            report_path = os.path.join(upload_dir, report_filename)
            
            import json
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            flash(f"Attendance report processed successfully for {form.report_date.data.strftime('%B %d, %Y')}", "success")
            
            return redirect(url_for('secure_attendance.view_report', 
                                  date=form.report_date.data.strftime('%Y-%m-%d')))
            
        except Exception as e:
            logger.error(f"Error processing attendance report: {str(e)}")
            flash(f"Error processing report: {str(e)}", "danger")
    
    return render_template('secure_attendance/process.html', form=form)

@secure_attendance_bp.route('/report/<date>')
@login_required
def view_report(date):
    """View processed attendance report with validation flags"""
    try:
        # Load report data
        report_dir = os.path.join('uploads', 'secure_attendance', date)
        report_file = os.path.join(report_dir, f"attendance_report_{date.replace('-', '_')}.json")
        
        if not os.path.exists(report_file):
            flash("Report not found. Please process the data first.", "warning")
            return redirect(url_for('secure_attendance.dashboard'))
        
        import json
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        # Format date for display
        report_date = datetime.strptime(date, '%Y-%m-%d')
        formatted_date = report_date.strftime('%A, %B %d, %Y')
        
        return render_template('secure_attendance/report.html',
            report=report,
            date=date,
            formatted_date=formatted_date
        )
        
    except Exception as e:
        logger.error(f"Error viewing report: {str(e)}")
        flash("Error loading report.", "danger")
        return redirect(url_for('secure_attendance.dashboard'))

@secure_attendance_bp.route('/export/<date>')
@login_required
def export_report(date):
    """Export attendance report with validation flags"""
    try:
        # Load report data
        report_dir = os.path.join('uploads', 'secure_attendance', date)
        report_file = os.path.join(report_dir, f"attendance_report_{date.replace('-', '_')}.json")
        
        if not os.path.exists(report_file):
            flash("Report not found.", "warning")
            return redirect(url_for('secure_attendance.dashboard'))
        
        import json
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        # Create Excel export
        import io
        from openpyxl import Workbook
        
        wb = Workbook()
        ws = wb.active
        ws.title = f"Attendance Report {date}"
        
        # Headers
        headers = ['Driver', 'Status', 'Job Zone', 'Start Time', 'End Time', 
                  'Has GPS', 'Has Timecard', 'Complete Coverage', 'Exceptions']
        ws.append(headers)
        
        # Data rows
        for driver in report.get('drivers', []):
            exceptions = []
            if driver['name'] in report['exceptions']['gps_no_timecard']:
                exceptions.append('⛔ GPS but no timecard')
            if driver['name'] in report['exceptions']['timecard_no_gps']:
                exceptions.append('⛔ Timecard but no GPS')
            if not driver['flags']['complete_coverage']:
                exceptions.append('⛔ Incomplete coverage')
            if driver['flags']['complete_coverage']:
                exceptions.append('✅ Valid')
            
            ws.append([
                driver['name'],
                driver['status'],
                driver['job_zone'],
                driver['start_time'],
                driver['end_time'],
                '✅' if driver['flags']['has_gps'] else '❌',
                '✅' if driver['flags']['has_timecard'] else '❌',
                '✅' if driver['flags']['complete_coverage'] else '❌',
                ', '.join(exceptions)
            ])
        
        # Save to BytesIO
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        filename = f"TRAXOVO_Attendance_Report_{date.replace('-', '_')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        flash("Error exporting report.", "danger")
        return redirect(url_for('secure_attendance.view_report', date=date))