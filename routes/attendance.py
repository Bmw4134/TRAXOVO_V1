"""
Driver Attendance Module

This module handles routes for displaying and analyzing driver attendance data.
"""
from datetime import datetime, timedelta
import calendar
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from sqlalchemy import func, desc, and_
from app import db
from models.reports import Driver, DriverAttendance, Jobsite

# Create blueprint
attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance', methods=['GET'])
@login_required
def attendance_dashboard():
    """Display the driver attendance dashboard"""
    # Get query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    driver_id = request.args.get('driver_id')
    jobsite_id = request.args.get('jobsite_id')
    flag_filter = request.args.get('flag')
    
    # Set default date range to current month if not provided
    today = datetime.today()
    if not start_date_str:
        start_date = datetime(today.year, today.month, 1).date()
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = datetime(today.year, today.month, 1).date()
    
    if not end_date_str:
        # Default to last day of current month
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, last_day).date()
    else:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            # Default to today if invalid
            end_date = today.date()
    
    # Build the base query
    query = db.session.query(
        DriverAttendance,
        Driver
    ).join(
        Driver, DriverAttendance.driver_id == Driver.id
    ).filter(
        DriverAttendance.date.between(start_date, end_date)
    )
    
    # Apply filters if provided
    if driver_id:
        query = query.filter(DriverAttendance.driver_id == driver_id)
    
    if jobsite_id:
        query = query.filter(DriverAttendance.jobsite_id == jobsite_id)
    
    if flag_filter:
        if flag_filter == 'late_start':
            query = query.filter(DriverAttendance.late_start == True)
        elif flag_filter == 'early_end':
            query = query.filter(DriverAttendance.early_end == True)
        elif flag_filter == 'no_jobsite':
            query = query.filter(DriverAttendance.no_jobsite == True)
        elif flag_filter == 'any_flag':
            query = query.filter(
                (DriverAttendance.late_start == True) | 
                (DriverAttendance.early_end == True) | 
                (DriverAttendance.no_jobsite == True)
            )
    
    # Order by date descending
    query = query.order_by(desc(DriverAttendance.date))
    
    # Execute query
    attendance_records = query.all()
    
    # Get all drivers and jobsites for filter dropdowns
    drivers = Driver.query.order_by(Driver.name).all()
    jobsites = Jobsite.query.order_by(Jobsite.name).all()
    
    # Calculate summary statistics
    total_records = len(attendance_records)
    total_hours = sum(record[0].total_hours or 0 for record in attendance_records)
    billable_hours = sum(record[0].billable_hours or 0 for record in attendance_records)
    
    # Count flags
    late_starts = sum(1 for record in attendance_records if record[0].late_start)
    early_ends = sum(1 for record in attendance_records if record[0].early_end)
    no_jobsites = sum(1 for record in attendance_records if record[0].no_jobsite)
    
    # Calculate efficiency
    efficiency = (billable_hours / total_hours * 100) if total_hours > 0 else 0
    
    return render_template(
        'attendance/dashboard.html',
        attendance_records=attendance_records,
        drivers=drivers,
        jobsites=jobsites,
        start_date=start_date,
        end_date=end_date,
        selected_driver_id=driver_id,
        selected_jobsite_id=jobsite_id,
        selected_flag=flag_filter,
        stats={
            'total_records': total_records,
            'total_hours': total_hours,
            'billable_hours': billable_hours,
            'efficiency': efficiency,
            'late_starts': late_starts,
            'early_ends': early_ends,
            'no_jobsites': no_jobsites
        }
    )

@attendance_bp.route('/attendance/api/summary', methods=['GET'])
@login_required
def attendance_summary_api():
    """API endpoint for attendance summary data"""
    # Get query parameters
    period = request.args.get('period', 'week')  # 'day', 'week', 'month'
    
    # Calculate date range based on period
    today = datetime.today()
    if period == 'day':
        start_date = today.date()
        end_date = today.date()
    elif period == 'week':
        # Start from Monday of current week
        start_date = (today - timedelta(days=today.weekday())).date()
        end_date = today.date()
    else:  # month
        start_date = datetime(today.year, today.month, 1).date()
        end_date = today.date()
    
    # Query for summary data
    data = db.session.query(
        func.date(DriverAttendance.date).label('date'),
        func.count(DriverAttendance.id).label('total'),
        func.sum(func.cast(DriverAttendance.late_start, db.Integer)).label('late_starts'),
        func.sum(func.cast(DriverAttendance.early_end, db.Integer)).label('early_ends'),
        func.sum(func.cast(DriverAttendance.no_jobsite, db.Integer)).label('no_jobsites'),
        func.sum(DriverAttendance.total_hours).label('total_hours'),
        func.sum(DriverAttendance.billable_hours).label('billable_hours')
    ).filter(
        DriverAttendance.date.between(start_date, end_date)
    ).group_by(
        func.date(DriverAttendance.date)
    ).order_by(
        func.date(DriverAttendance.date)
    ).all()
    
    # Format for chart display
    result = {
        'dates': [str(row.date) for row in data],
        'total_records': [row.total for row in data],
        'late_starts': [row.late_starts or 0 for row in data],
        'early_ends': [row.early_ends or 0 for row in data],
        'no_jobsites': [row.no_jobsites or 0 for row in data],
        'total_hours': [float(row.total_hours or 0) for row in data],
        'billable_hours': [float(row.billable_hours or 0) for row in data],
    }
    
    return jsonify(result)

@attendance_bp.route('/attendance/api/driver-stats', methods=['GET'])
@login_required
def driver_stats_api():
    """API endpoint for driver-specific statistics"""
    # Get query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Set default date range to current month if not provided
    today = datetime.today()
    if not start_date_str:
        start_date = datetime(today.year, today.month, 1).date()
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = datetime(today.year, today.month, 1).date()
    
    if not end_date_str:
        end_date = today.date()
    else:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            end_date = today.date()
    
    # Query for driver statistics
    driver_stats = db.session.query(
        Driver.id,
        Driver.name,
        func.count(DriverAttendance.id).label('attendance_count'),
        func.sum(func.cast(DriverAttendance.late_start, db.Integer)).label('late_starts'),
        func.sum(func.cast(DriverAttendance.early_end, db.Integer)).label('early_ends'),
        func.sum(func.cast(DriverAttendance.no_jobsite, db.Integer)).label('no_jobsites'),
        func.sum(DriverAttendance.total_hours).label('total_hours'),
        func.sum(DriverAttendance.billable_hours).label('billable_hours')
    ).join(
        DriverAttendance, Driver.id == DriverAttendance.driver_id
    ).filter(
        DriverAttendance.date.between(start_date, end_date)
    ).group_by(
        Driver.id, Driver.name
    ).order_by(
        func.sum(DriverAttendance.total_hours).desc()
    ).all()
    
    # Format for chart display
    result = {
        'drivers': [driver.name for driver in driver_stats],
        'attendance_counts': [driver.attendance_count for driver in driver_stats],
        'late_starts': [driver.late_starts or 0 for driver in driver_stats],
        'early_ends': [driver.early_ends or 0 for driver in driver_stats],
        'no_jobsites': [driver.no_jobsites or 0 for driver in driver_stats],
        'total_hours': [float(driver.total_hours or 0) for driver in driver_stats],
        'billable_hours': [float(driver.billable_hours or 0) for driver in driver_stats],
        'efficiency': [
            round((float(driver.billable_hours or 0) / float(driver.total_hours or 1)) * 100, 2) 
            for driver in driver_stats
        ]
    }
    
    return jsonify(result)