"""
Driver Reports Module Routes

This module provides routes and functionality for the Driver Reports module,
which tracks driver attendance, late starts, early ends, and instances where
drivers were not on their assigned job sites.
"""
from datetime import datetime, timedelta
import json
import pandas as pd
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_
from models.driver_attendance import Driver, JobSite, AttendanceRecord, AttendanceStats
from app import db
from utils.export_helpers import generate_excel, generate_csv, generate_pdf


# Create blueprint
drivers_bp = Blueprint('drivers', __name__, url_prefix='/drivers')


@drivers_bp.route('/')
@login_required
def index():
    """Driver Reports module main page"""
    return render_template('drivers/index.html')


@drivers_bp.route('/dashboard')
@login_required
def dashboard():
    """Driver Reports dashboard page"""
    return render_template('drivers/dashboard.html')


@drivers_bp.route('/dashboard/kpi-data')
@login_required
def dashboard_kpi_data():
    """Get KPI data for dashboard"""
    # Get filter parameters
    date_range = request.args.get('date_range', 'last_7_days')
    division = request.args.get('division', 'all')
    department = request.args.get('department', 'all')
    issue_type = request.args.get('issue_type', 'all')
    
    # Calculate date range
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today
    
    if date_range == 'today':
        start_date = today
    elif date_range == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = start_date
    elif date_range == 'last_7_days':
        start_date = today - timedelta(days=7)
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
    elif date_range == 'last_month':
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1
        start_date = today.replace(year=last_month_year, month=last_month, day=1)
        end_date = today.replace(day=1) - timedelta(days=1)
    elif date_range == 'custom':
        start_str = request.args.get('start_date')
        end_str = request.args.get('end_date')
        if start_str and end_str:
            try:
                start_date = datetime.strptime(start_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_str, '%Y-%m-%d')
            except ValueError:
                start_date = today - timedelta(days=7)
        else:
            start_date = today - timedelta(days=7)
    else:
        start_date = today - timedelta(days=7)
    
    # Build query filters
    filters = [
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date
    ]
    
    if division != 'all':
        filters.append(Driver.division == division)
    
    if department != 'all':
        filters.append(Driver.department == department)
    
    if issue_type != 'all':
        if issue_type == 'late_start':
            filters.append(AttendanceRecord.late_start == True)
        elif issue_type == 'early_end':
            filters.append(AttendanceRecord.early_end == True)
        elif issue_type == 'not_on_job':
            filters.append(AttendanceRecord.not_on_job == True)
    
    # Query attendance records with count of issues
    late_starts = db.session.query(func.count(AttendanceRecord.id)).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).filter(
        AttendanceRecord.late_start == True,
        *filters
    ).scalar() or 0
    
    early_ends = db.session.query(func.count(AttendanceRecord.id)).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).filter(
        AttendanceRecord.early_end == True,
        *filters
    ).scalar() or 0
    
    not_on_job = db.session.query(func.count(AttendanceRecord.id)).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).filter(
        AttendanceRecord.not_on_job == True,
        *filters
    ).scalar() or 0
    
    total_records = db.session.query(func.count(AttendanceRecord.id)).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).filter(*filters).scalar() or 0
    
    on_time_rate = 0
    if total_records > 0:
        on_time_count = total_records - (late_starts + early_ends + not_on_job)
        on_time_rate = round((on_time_count / total_records) * 100)
    
    # Get trend data (comparing to previous period)
    prev_start_date = start_date - (end_date - start_date)
    prev_end_date = start_date - timedelta(days=1)
    
    prev_filters = [
        AttendanceRecord.date >= prev_start_date,
        AttendanceRecord.date <= prev_end_date
    ]
    
    if division != 'all':
        prev_filters.append(Driver.division == division)
    
    if department != 'all':
        prev_filters.append(Driver.department == department)
    
    prev_late_starts = db.session.query(func.count(AttendanceRecord.id)).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).filter(
        AttendanceRecord.late_start == True,
        *prev_filters
    ).scalar() or 0
    
    prev_early_ends = db.session.query(func.count(AttendanceRecord.id)).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).filter(
        AttendanceRecord.early_end == True,
        *prev_filters
    ).scalar() or 0
    
    prev_not_on_job = db.session.query(func.count(AttendanceRecord.id)).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).filter(
        AttendanceRecord.not_on_job == True,
        *prev_filters
    ).scalar() or 0
    
    prev_total_records = db.session.query(func.count(AttendanceRecord.id)).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).filter(*prev_filters).scalar() or 0
    
    prev_on_time_rate = 0
    if prev_total_records > 0:
        prev_on_time_count = prev_total_records - (prev_late_starts + prev_early_ends + prev_not_on_job)
        prev_on_time_rate = round((prev_on_time_count / prev_total_records) * 100)
    
    # Calculate trends
    late_trend = calculate_trend(late_starts, prev_late_starts)
    early_trend = calculate_trend(early_ends, prev_early_ends)
    not_on_job_trend = calculate_trend(not_on_job, prev_not_on_job)
    on_time_trend = on_time_rate - prev_on_time_rate
    
    return jsonify({
        'late_starts': {
            'value': late_starts,
            'trend': late_trend,
            'trend_direction': 'down' if late_trend < 0 else 'neutral' if late_trend == 0 else 'up'
        },
        'early_ends': {
            'value': early_ends,
            'trend': early_trend,
            'trend_direction': 'down' if early_trend < 0 else 'neutral' if early_trend == 0 else 'up'
        },
        'not_on_job': {
            'value': not_on_job,
            'trend': not_on_job_trend,
            'trend_direction': 'down' if not_on_job_trend < 0 else 'neutral' if not_on_job_trend == 0 else 'up'
        },
        'on_time_rate': {
            'value': on_time_rate,
            'trend': on_time_trend,
            'trend_direction': 'up' if on_time_trend > 0 else 'neutral' if on_time_trend == 0 else 'down'
        }
    })


def calculate_trend(current, previous):
    """Calculate percentage trend between current and previous values"""
    if previous == 0:
        return 100 if current > 0 else 0
    
    change = current - previous
    percentage = (change / previous) * 100
    return round(percentage)


@drivers_bp.route('/dashboard/trend-data')
@login_required
def dashboard_trend_data():
    """Get trend data for dashboard charts"""
    # Get filter parameters
    days = int(request.args.get('days', 30))
    division = request.args.get('division', 'all')
    department = request.args.get('department', 'all')
    
    # Calculate date range
    end_date = datetime.now().replace(hour=23, minute=59, second=59)
    start_date = end_date - timedelta(days=days)
    
    # Build query filters
    filters = [
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date
    ]
    
    if division != 'all':
        filters.append(Driver.division == division)
    
    if department != 'all':
        filters.append(Driver.department == department)
    
    # Query daily attendance records
    daily_data = []
    current_date = start_date
    
    while current_date <= end_date:
        day_start = current_date.replace(hour=0, minute=0, second=0)
        day_end = current_date.replace(hour=23, minute=59, second=59)
        
        daily_filters = filters.copy()
        daily_filters.extend([
            AttendanceRecord.date >= day_start,
            AttendanceRecord.date <= day_end
        ])
        
        late_starts = db.session.query(func.count(AttendanceRecord.id)).join(
            Driver, AttendanceRecord.driver_id == Driver.id
        ).filter(
            AttendanceRecord.late_start == True,
            *daily_filters
        ).scalar() or 0
        
        early_ends = db.session.query(func.count(AttendanceRecord.id)).join(
            Driver, AttendanceRecord.driver_id == Driver.id
        ).filter(
            AttendanceRecord.early_end == True,
            *daily_filters
        ).scalar() or 0
        
        not_on_job = db.session.query(func.count(AttendanceRecord.id)).join(
            Driver, AttendanceRecord.driver_id == Driver.id
        ).filter(
            AttendanceRecord.not_on_job == True,
            *daily_filters
        ).scalar() or 0
        
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'late_starts': late_starts,
            'early_ends': early_ends,
            'not_on_job': not_on_job
        })
        
        current_date += timedelta(days=1)
    
    return jsonify(daily_data)


@drivers_bp.route('/dashboard/recent-issues')
@login_required
def dashboard_recent_issues():
    """Get recent attendance issues for the dashboard table"""
    # Get filter parameters
    date_range = request.args.get('date_range', 'last_7_days')
    division = request.args.get('division', 'all')
    department = request.args.get('department', 'all')
    issue_type = request.args.get('issue_type', 'all')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Calculate date range
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today
    
    if date_range == 'today':
        start_date = today
    elif date_range == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = start_date
    elif date_range == 'last_7_days':
        start_date = today - timedelta(days=7)
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
    elif date_range == 'last_month':
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1
        start_date = today.replace(year=last_month_year, month=last_month, day=1)
        end_date = today.replace(day=1) - timedelta(days=1)
    elif date_range == 'custom':
        start_str = request.args.get('start_date')
        end_str = request.args.get('end_date')
        if start_str and end_str:
            try:
                start_date = datetime.strptime(start_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_str, '%Y-%m-%d')
            except ValueError:
                start_date = today - timedelta(days=7)
        else:
            start_date = today - timedelta(days=7)
    else:
        start_date = today - timedelta(days=7)
    
    # Build query
    query = db.session.query(
        AttendanceRecord, Driver, JobSite
    ).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).join(
        JobSite, AttendanceRecord.assigned_job_id == JobSite.id
    ).filter(
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date
    )
    
    # Apply filters
    if division != 'all':
        query = query.filter(Driver.division == division)
    
    if department != 'all':
        query = query.filter(Driver.department == department)
    
    if issue_type != 'all':
        if issue_type == 'late_start':
            query = query.filter(AttendanceRecord.late_start == True)
        elif issue_type == 'early_end':
            query = query.filter(AttendanceRecord.early_end == True)
        elif issue_type == 'not_on_job':
            query = query.filter(AttendanceRecord.not_on_job == True)
        else:
            # At least one issue type
            query = query.filter(or_(
                AttendanceRecord.late_start == True,
                AttendanceRecord.early_end == True,
                AttendanceRecord.not_on_job == True
            ))
    else:
        # At least one issue type
        query = query.filter(or_(
            AttendanceRecord.late_start == True,
            AttendanceRecord.early_end == True,
            AttendanceRecord.not_on_job == True
        ))
    
    # Order by date (most recent first)
    query = query.order_by(AttendanceRecord.date.desc())
    
    # Paginate results
    total_records = query.count()
    records = query.limit(per_page).offset((page - 1) * per_page).all()
    
    # Format results
    result = []
    for record, driver, job_site in records:
        actual_job_site = None
        if record.actual_job_id:
            actual_job_site = db.session.get(JobSite, record.actual_job_id)
        
        item = {
            'id': record.id,
            'date': record.date.strftime('%m/%d/%Y'),
            'driver': driver.full_name,
            'asset_id': record.asset_id,
            'job_site': job_site.job_number,
            'issue_type': record.issue_type,
            'expected': format_expected_actual(record, job_site, actual_job_site),
            'actual': format_expected_actual(record, job_site, actual_job_site, is_actual=True),
            'difference': format_difference(record, job_site, actual_job_site)
        }
        result.append(item)
    
    return jsonify({
        'data': result,
        'total': total_records,
        'page': page,
        'per_page': per_page,
        'pages': (total_records + per_page - 1) // per_page
    })


def format_expected_actual(record, job_site, actual_job_site, is_actual=False):
    """Format expected or actual values based on the issue type"""
    if record.not_on_job:
        return actual_job_site.job_number if is_actual and actual_job_site else job_site.job_number
    
    if record.late_start:
        time_to_format = record.actual_start_time if is_actual else record.expected_start_time
        if time_to_format:
            return time_to_format.strftime('%I:%M %p')
        return 'Unknown'
    
    if record.early_end:
        time_to_format = record.actual_end_time if is_actual else record.expected_end_time
        if time_to_format:
            return time_to_format.strftime('%I:%M %p')
        return 'Unknown'
    
    return '-'


def format_difference(record, job_site, actual_job_site):
    """Format difference values based on the issue type"""
    if record.not_on_job:
        return 'Wrong Site'
    
    if record.late_start:
        return f"{record.late_minutes} mins"
    
    if record.early_end:
        return f"{record.early_minutes} mins"
    
    return '-'


@drivers_bp.route('/driver-list')
@login_required
def driver_list():
    """Driver list page"""
    return render_template('drivers/driver_list.html')


@drivers_bp.route('/api/drivers')
@login_required
def api_drivers():
    """API endpoint to get driver data for the driver list"""
    # Get filter parameters
    division = request.args.get('division', 'all')
    department = request.args.get('department', 'all')
    is_active = request.args.get('is_active', 'all')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    
    # Build query
    query = db.session.query(Driver)
    
    # Apply filters
    if division != 'all':
        query = query.filter(Driver.division == division)
    
    if department != 'all':
        query = query.filter(Driver.department == department)
    
    if is_active != 'all':
        is_active_bool = is_active.lower() == 'true'
        query = query.filter(Driver.is_active == is_active_bool)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            Driver.first_name.ilike(search_term),
            Driver.last_name.ilike(search_term),
            Driver.employee_id.ilike(search_term)
        ))
    
    # Get total count
    total_drivers = query.count()
    
    # Order and paginate
    query = query.order_by(Driver.last_name, Driver.first_name)
    drivers = query.limit(per_page).offset((page - 1) * per_page).all()
    
    # Format results
    result = []
    for driver in drivers:
        # Get current asset and job (most recent attendance record)
        latest_record = db.session.query(AttendanceRecord).filter(
            AttendanceRecord.driver_id == driver.id
        ).order_by(AttendanceRecord.date.desc()).first()
        
        current_asset = latest_record.asset_id if latest_record else '-'
        
        current_job = '-'
        if latest_record and latest_record.assigned_job_id:
            job_site = db.session.get(JobSite, latest_record.assigned_job_id)
            if job_site:
                current_job = job_site.job_number
        
        # Get attendance score (last 30 days)
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        total_records = db.session.query(func.count(AttendanceRecord.id)).filter(
            AttendanceRecord.driver_id == driver.id,
            AttendanceRecord.date >= thirty_days_ago
        ).scalar() or 0
        
        issue_records = db.session.query(func.count(AttendanceRecord.id)).filter(
            AttendanceRecord.driver_id == driver.id,
            AttendanceRecord.date >= thirty_days_ago,
            or_(
                AttendanceRecord.late_start == True,
                AttendanceRecord.early_end == True,
                AttendanceRecord.not_on_job == True
            )
        ).scalar() or 0
        
        attendance_score = 100
        if total_records > 0:
            attendance_score = round(((total_records - issue_records) / total_records) * 100)
        
        item = {
            'id': driver.id,
            'employee_id': driver.employee_id,
            'name': driver.full_name,
            'division': driver.division,
            'department': driver.department,
            'current_asset': current_asset,
            'current_job': current_job,
            'attendance_score': attendance_score,
            'is_active': driver.is_active
        }
        result.append(item)
    
    return jsonify({
        'data': result,
        'total': total_drivers,
        'page': page,
        'per_page': per_page,
        'pages': (total_drivers + per_page - 1) // per_page
    })


@drivers_bp.route('/driver/<int:driver_id>')
@login_required
def driver_detail(driver_id):
    """Driver detail page"""
    driver = db.session.get(Driver, driver_id)
    if not driver:
        flash('Driver not found', 'danger')
        return redirect(url_for('drivers.driver_list'))
    
    return render_template('drivers/driver_detail.html', driver=driver)


@drivers_bp.route('/api/driver/<int:driver_id>/metrics')
@login_required
def api_driver_metrics(driver_id):
    """API endpoint to get attendance metrics for a specific driver"""
    driver = db.session.get(Driver, driver_id)
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404
    
    # Calculate date ranges
    today = datetime.now()
    thirty_days_ago = today - timedelta(days=30)
    sixty_days_ago = today - timedelta(days=60)
    ninety_days_ago = today - timedelta(days=90)
    
    # Current period metrics (last 30 days)
    current_late_starts = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.driver_id == driver_id,
        AttendanceRecord.date >= thirty_days_ago,
        AttendanceRecord.late_start == True
    ).scalar() or 0
    
    current_early_ends = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.driver_id == driver_id,
        AttendanceRecord.date >= thirty_days_ago,
        AttendanceRecord.early_end == True
    ).scalar() or 0
    
    current_not_on_job = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.driver_id == driver_id,
        AttendanceRecord.date >= thirty_days_ago,
        AttendanceRecord.not_on_job == True
    ).scalar() or 0
    
    current_total = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.driver_id == driver_id,
        AttendanceRecord.date >= thirty_days_ago
    ).scalar() or 0
    
    current_score = 100
    if current_total > 0:
        current_score = round(((current_total - (current_late_starts + current_early_ends + current_not_on_job)) / current_total) * 100)
    
    # Previous period metrics (30-60 days ago)
    prev_late_starts = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.driver_id == driver_id,
        AttendanceRecord.date >= sixty_days_ago,
        AttendanceRecord.date < thirty_days_ago,
        AttendanceRecord.late_start == True
    ).scalar() or 0
    
    prev_early_ends = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.driver_id == driver_id,
        AttendanceRecord.date >= sixty_days_ago,
        AttendanceRecord.date < thirty_days_ago,
        AttendanceRecord.early_end == True
    ).scalar() or 0
    
    prev_not_on_job = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.driver_id == driver_id,
        AttendanceRecord.date >= sixty_days_ago,
        AttendanceRecord.date < thirty_days_ago,
        AttendanceRecord.not_on_job == True
    ).scalar() or 0
    
    prev_total = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.driver_id == driver_id,
        AttendanceRecord.date >= sixty_days_ago,
        AttendanceRecord.date < thirty_days_ago
    ).scalar() or 0
    
    prev_score = 100
    if prev_total > 0:
        prev_score = round(((prev_total - (prev_late_starts + prev_early_ends + prev_not_on_job)) / prev_total) * 100)
    
    # Calculate trends
    late_trend = calculate_trend(current_late_starts, prev_late_starts)
    early_trend = calculate_trend(current_early_ends, prev_early_ends)
    not_on_job_trend = calculate_trend(current_not_on_job, prev_not_on_job)
    score_trend = current_score - prev_score
    
    # Get current assignment
    latest_record = db.session.query(AttendanceRecord).filter(
        AttendanceRecord.driver_id == driver_id
    ).order_by(AttendanceRecord.date.desc()).first()
    
    current_asset = latest_record.asset_id if latest_record else '-'
    current_job = '-'
    
    if latest_record and latest_record.assigned_job_id:
        job_site = db.session.get(JobSite, latest_record.assigned_job_id)
        if job_site:
            current_job = job_site.job_number
    
    # Format response
    response = {
        'driver': {
            'id': driver.id,
            'name': driver.full_name,
            'employee_id': driver.employee_id,
            'division': driver.division,
            'department': driver.department,
            'current_asset': current_asset,
            'current_job': current_job,
            'is_active': driver.is_active
        },
        'metrics': {
            'attendance_score': {
                'value': current_score,
                'trend': score_trend,
                'trend_direction': 'up' if score_trend > 0 else 'neutral' if score_trend == 0 else 'down'
            },
            'late_starts': {
                'value': current_late_starts,
                'trend': late_trend,
                'trend_direction': 'down' if late_trend < 0 else 'neutral' if late_trend == 0 else 'up'
            },
            'early_ends': {
                'value': current_early_ends,
                'trend': early_trend,
                'trend_direction': 'down' if early_trend < 0 else 'neutral' if early_trend == 0 else 'up'
            },
            'not_on_job': {
                'value': current_not_on_job,
                'trend': not_on_job_trend,
                'trend_direction': 'down' if not_on_job_trend < 0 else 'neutral' if not_on_job_trend == 0 else 'up'
            }
        }
    }
    
    return jsonify(response)


@drivers_bp.route('/api/driver/<int:driver_id>/attendance-history')
@login_required
def api_driver_attendance_history(driver_id):
    """API endpoint to get attendance history for a specific driver"""
    driver = db.session.get(Driver, driver_id)
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404
    
    # Get filter parameters
    days = int(request.args.get('days', 30))
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Query attendance records
    query = db.session.query(
        AttendanceRecord, JobSite
    ).join(
        JobSite, AttendanceRecord.assigned_job_id == JobSite.id
    ).filter(
        AttendanceRecord.driver_id == driver_id,
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date
    ).order_by(AttendanceRecord.date.desc())
    
    # Count total records
    total_records = query.count()
    
    # Paginate results
    records = query.limit(per_page).offset((page - 1) * per_page).all()
    
    # Format results
    result = []
    for record, job_site in records:
        actual_job_site = None
        if record.actual_job_id:
            actual_job_site = db.session.get(JobSite, record.actual_job_id)
        
        # Determine status
        status = "On Time"
        status_class = "success"
        
        if record.not_on_job:
            status = "Wrong Job"
            status_class = "danger"
        elif record.late_start:
            status = "Late Start"
            status_class = "danger"
        elif record.early_end:
            status = "Early End"
            status_class = "warning"
        
        # Format notes
        notes = record.notes if record.notes else "-"
        
        item = {
            'id': record.id,
            'date': record.date.strftime('%m/%d/%Y'),
            'asset_id': record.asset_id,
            'job_site': job_site.job_number,
            'start_time': record.actual_start_time.strftime('%I:%M %p') if record.actual_start_time else '-',
            'end_time': record.actual_end_time.strftime('%I:%M %p') if record.actual_end_time else '-',
            'status': status,
            'status_class': status_class,
            'notes': notes
        }
        result.append(item)
    
    return jsonify({
        'data': result,
        'total': total_records,
        'page': page,
        'per_page': per_page,
        'pages': (total_records + per_page - 1) // per_page
    })


@drivers_bp.route('/api/driver/<int:driver_id>/attendance-chart')
@login_required
def api_driver_attendance_chart(driver_id):
    """API endpoint to get data for the driver attendance chart"""
    driver = db.session.get(Driver, driver_id)
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404
    
    # Get filter parameters
    days = int(request.args.get('days', 90))
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Query attendance records by day
    attendance_data = []
    current_date = start_date
    
    while current_date <= end_date:
        day_start = current_date.replace(hour=0, minute=0, second=0)
        day_end = current_date.replace(hour=23, minute=59, second=59)
        
        # Get records for the day
        day_records = db.session.query(AttendanceRecord).filter(
            AttendanceRecord.driver_id == driver_id,
            AttendanceRecord.date >= day_start,
            AttendanceRecord.date <= day_end
        ).all()
        
        # Skip days with no records
        if day_records:
            # Count issues
            late_starts = sum(1 for r in day_records if r.late_start)
            early_ends = sum(1 for r in day_records if r.early_end)
            not_on_job = sum(1 for r in day_records if r.not_on_job)
            total = len(day_records)
            on_time = total - (late_starts + early_ends + not_on_job)
            
            # Calculate score
            score = 100
            if total > 0:
                score = round((on_time / total) * 100)
            
            attendance_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'score': score,
                'late_starts': late_starts,
                'early_ends': early_ends,
                'not_on_job': not_on_job
            })
        
        current_date += timedelta(days=1)
    
    return jsonify(attendance_data)


@drivers_bp.route('/job-sites')
@login_required
def job_sites():
    """Job sites page"""
    return render_template('drivers/job_sites.html')


@drivers_bp.route('/api/job-sites')
@login_required
def api_job_sites():
    """API endpoint to get job site data"""
    # Get filter parameters
    division = request.args.get('division', 'all')
    is_active = request.args.get('is_active', 'all')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    
    # Build query
    query = db.session.query(JobSite)
    
    # Apply filters
    if division != 'all':
        query = query.filter(JobSite.division == division)
    
    if is_active != 'all':
        is_active_bool = is_active.lower() == 'true'
        query = query.filter(JobSite.is_active == is_active_bool)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            JobSite.job_number.ilike(search_term),
            JobSite.name.ilike(search_term),
            JobSite.location.ilike(search_term)
        ))
    
    # Get total count
    total_job_sites = query.count()
    
    # Order and paginate
    query = query.order_by(JobSite.job_number)
    job_sites = query.limit(per_page).offset((page - 1) * per_page).all()
    
    # Calculate last 30 days statistics for each job site
    today = datetime.now()
    thirty_days_ago = today - timedelta(days=30)
    
    result = []
    for job_site in job_sites:
        # Get active drivers count
        active_drivers = db.session.query(func.count(func.distinct(AttendanceRecord.driver_id))).filter(
            AttendanceRecord.assigned_job_id == job_site.id,
            AttendanceRecord.date >= thirty_days_ago
        ).scalar() or 0
        
        # Count issues
        late_starts = db.session.query(func.count(AttendanceRecord.id)).filter(
            AttendanceRecord.assigned_job_id == job_site.id,
            AttendanceRecord.date >= thirty_days_ago,
            AttendanceRecord.late_start == True
        ).scalar() or 0
        
        early_ends = db.session.query(func.count(AttendanceRecord.id)).filter(
            AttendanceRecord.assigned_job_id == job_site.id,
            AttendanceRecord.date >= thirty_days_ago,
            AttendanceRecord.early_end == True
        ).scalar() or 0
        
        not_on_job = db.session.query(func.count(AttendanceRecord.id)).filter(
            AttendanceRecord.assigned_job_id == job_site.id,
            AttendanceRecord.date >= thirty_days_ago,
            AttendanceRecord.not_on_job == True
        ).scalar() or 0
        
        total_records = db.session.query(func.count(AttendanceRecord.id)).filter(
            AttendanceRecord.assigned_job_id == job_site.id,
            AttendanceRecord.date >= thirty_days_ago
        ).scalar() or 0
        
        attendance_score = 100
        if total_records > 0:
            attendance_score = round(((total_records - (late_starts + early_ends + not_on_job)) / total_records) * 100)
        
        item = {
            'id': job_site.id,
            'job_number': job_site.job_number,
            'name': job_site.name or job_site.job_number,
            'location': job_site.location or '-',
            'division': job_site.division or '-',
            'active_drivers': active_drivers,
            'late_starts': late_starts,
            'early_ends': early_ends,
            'not_on_job': not_on_job,
            'attendance_score': attendance_score,
            'is_active': job_site.is_active
        }
        result.append(item)
    
    return jsonify({
        'data': result,
        'total': total_job_sites,
        'page': page,
        'per_page': per_page,
        'pages': (total_job_sites + per_page - 1) // per_page
    })


@drivers_bp.route('/job-site/<int:job_site_id>')
@login_required
def job_site_detail(job_site_id):
    """Job site detail page"""
    job_site = db.session.get(JobSite, job_site_id)
    if not job_site:
        flash('Job site not found', 'danger')
        return redirect(url_for('drivers.job_sites'))
    
    return render_template('drivers/job_site_detail.html', job_site=job_site)


@drivers_bp.route('/api/job-site/<int:job_site_id>/metrics')
@login_required
def api_job_site_metrics(job_site_id):
    """API endpoint to get attendance metrics for a specific job site"""
    job_site = db.session.get(JobSite, job_site_id)
    if not job_site:
        return jsonify({'error': 'Job site not found'}), 404
    
    # Calculate date ranges
    today = datetime.now()
    thirty_days_ago = today - timedelta(days=30)
    sixty_days_ago = today - timedelta(days=60)
    
    # Current period metrics (last 30 days)
    current_late_starts = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.assigned_job_id == job_site_id,
        AttendanceRecord.date >= thirty_days_ago,
        AttendanceRecord.late_start == True
    ).scalar() or 0
    
    current_early_ends = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.assigned_job_id == job_site_id,
        AttendanceRecord.date >= thirty_days_ago,
        AttendanceRecord.early_end == True
    ).scalar() or 0
    
    current_not_on_job = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.assigned_job_id == job_site_id,
        AttendanceRecord.date >= thirty_days_ago,
        AttendanceRecord.not_on_job == True
    ).scalar() or 0
    
    current_total = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.assigned_job_id == job_site_id,
        AttendanceRecord.date >= thirty_days_ago
    ).scalar() or 0
    
    current_score = 100
    if current_total > 0:
        current_score = round(((current_total - (current_late_starts + current_early_ends + current_not_on_job)) / current_total) * 100)
    
    # Previous period metrics (30-60 days ago)
    prev_late_starts = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.assigned_job_id == job_site_id,
        AttendanceRecord.date >= sixty_days_ago,
        AttendanceRecord.date < thirty_days_ago,
        AttendanceRecord.late_start == True
    ).scalar() or 0
    
    prev_early_ends = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.assigned_job_id == job_site_id,
        AttendanceRecord.date >= sixty_days_ago,
        AttendanceRecord.date < thirty_days_ago,
        AttendanceRecord.early_end == True
    ).scalar() or 0
    
    prev_not_on_job = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.assigned_job_id == job_site_id,
        AttendanceRecord.date >= sixty_days_ago,
        AttendanceRecord.date < thirty_days_ago,
        AttendanceRecord.not_on_job == True
    ).scalar() or 0
    
    prev_total = db.session.query(func.count(AttendanceRecord.id)).filter(
        AttendanceRecord.assigned_job_id == job_site_id,
        AttendanceRecord.date >= sixty_days_ago,
        AttendanceRecord.date < thirty_days_ago
    ).scalar() or 0
    
    prev_score = 100
    if prev_total > 0:
        prev_score = round(((prev_total - (prev_late_starts + prev_early_ends + prev_not_on_job)) / prev_total) * 100)
    
    # Get active drivers count
    active_drivers = db.session.query(func.count(func.distinct(AttendanceRecord.driver_id))).filter(
        AttendanceRecord.assigned_job_id == job_site_id,
        AttendanceRecord.date >= thirty_days_ago
    ).scalar() or 0
    
    # Calculate trends
    late_trend = calculate_trend(current_late_starts, prev_late_starts)
    early_trend = calculate_trend(current_early_ends, prev_early_ends)
    not_on_job_trend = calculate_trend(current_not_on_job, prev_not_on_job)
    score_trend = current_score - prev_score
    
    # Format response
    response = {
        'job_site': {
            'id': job_site.id,
            'job_number': job_site.job_number,
            'name': job_site.name or job_site.job_number,
            'location': job_site.location or '-',
            'division': job_site.division or '-',
            'active_drivers': active_drivers,
            'is_active': job_site.is_active
        },
        'metrics': {
            'attendance_score': {
                'value': current_score,
                'trend': score_trend,
                'trend_direction': 'up' if score_trend > 0 else 'neutral' if score_trend == 0 else 'down'
            },
            'late_starts': {
                'value': current_late_starts,
                'trend': late_trend,
                'trend_direction': 'down' if late_trend < 0 else 'neutral' if late_trend == 0 else 'up'
            },
            'early_ends': {
                'value': current_early_ends,
                'trend': early_trend,
                'trend_direction': 'down' if early_trend < 0 else 'neutral' if early_trend == 0 else 'up'
            },
            'not_on_job': {
                'value': current_not_on_job,
                'trend': not_on_job_trend,
                'trend_direction': 'down' if not_on_job_trend < 0 else 'neutral' if not_on_job_trend == 0 else 'up'
            }
        }
    }
    
    return jsonify(response)


@drivers_bp.route('/api/job-site/<int:job_site_id>/attendance-history')
@login_required
def api_job_site_attendance_history(job_site_id):
    """API endpoint to get attendance history for a specific job site"""
    job_site = db.session.get(JobSite, job_site_id)
    if not job_site:
        return jsonify({'error': 'Job site not found'}), 404
    
    # Get filter parameters
    days = int(request.args.get('days', 30))
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Query attendance records
    query = db.session.query(
        AttendanceRecord, Driver
    ).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).filter(
        AttendanceRecord.assigned_job_id == job_site_id,
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date
    ).order_by(AttendanceRecord.date.desc())
    
    # Count total records
    total_records = query.count()
    
    # Paginate results
    records = query.limit(per_page).offset((page - 1) * per_page).all()
    
    # Format results
    result = []
    for record, driver in records:
        # Determine status
        status = "On Time"
        status_class = "success"
        
        if record.not_on_job:
            status = "Wrong Job"
            status_class = "danger"
        elif record.late_start:
            status = "Late Start"
            status_class = "danger"
        elif record.early_end:
            status = "Early End"
            status_class = "warning"
        
        item = {
            'id': record.id,
            'date': record.date.strftime('%m/%d/%Y'),
            'driver': driver.full_name,
            'asset_id': record.asset_id,
            'start_time': record.actual_start_time.strftime('%I:%M %p') if record.actual_start_time else '-',
            'end_time': record.actual_end_time.strftime('%I:%M %p') if record.actual_end_time else '-',
            'status': status,
            'status_class': status_class,
            'notes': record.notes or '-'
        }
        result.append(item)
    
    return jsonify({
        'data': result,
        'total': total_records,
        'page': page,
        'per_page': per_page,
        'pages': (total_records + per_page - 1) // per_page
    })


@drivers_bp.route('/reports')
@login_required
def reports():
    """Reports page for the Driver Reports module"""
    return render_template('drivers/reports.html')


@drivers_bp.route('/api/report/generate', methods=['POST'])
@login_required
def api_generate_report():
    """API endpoint to generate reports"""
    data = request.json
    
    report_type = data.get('report_type', 'daily_driver')
    date_range = data.get('date_range', 'last_7_days')
    division = data.get('division', 'all')
    format = data.get('format', 'excel')
    include_charts = data.get('include_charts', True)
    include_raw_data = data.get('include_raw_data', True)
    
    # Calculate date range
    today = datetime.now()
    end_date = today
    
    if date_range == 'today':
        start_date = today
    elif date_range == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = start_date
    elif date_range == 'last_7_days':
        start_date = today - timedelta(days=7)
    elif date_range == 'last_30_days':
        start_date = today - timedelta(days=30)
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
    elif date_range == 'last_month':
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1
        start_date = today.replace(year=last_month_year, month=last_month, day=1)
        end_date = today.replace(day=1) - timedelta(days=1)
    elif date_range == 'custom':
        start_str = data.get('start_date')
        end_str = data.get('end_date')
        if start_str and end_str:
            try:
                start_date = datetime.strptime(start_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_str, '%Y-%m-%d')
            except ValueError:
                start_date = today - timedelta(days=7)
        else:
            start_date = today - timedelta(days=7)
    else:
        start_date = today - timedelta(days=7)
    
    # Build query filters
    filters = [
        AttendanceRecord.date >= start_date,
        AttendanceRecord.date <= end_date
    ]
    
    if division != 'all':
        filters.append(Driver.division == division)
    
    # Get driver records based on report type
    if report_type == 'daily_driver':
        # Get daily summary of all driver attendance
        result = generate_daily_driver_report(filters, start_date, end_date, division, format, include_charts, include_raw_data)
    elif report_type == 'weekly_summary':
        # Get weekly summary with trends
        result = generate_weekly_summary_report(filters, start_date, end_date, division, format, include_charts, include_raw_data)
    elif report_type == 'driver_performance':
        # Get individual driver performance reports
        result = generate_driver_performance_report(filters, start_date, end_date, division, format, include_charts, include_raw_data)
    elif report_type == 'job_site_performance':
        # Get job site performance reports
        result = generate_job_site_performance_report(filters, start_date, end_date, division, format, include_charts, include_raw_data)
    elif report_type == 'executive_summary':
        # Get executive summary reports
        result = generate_executive_summary_report(filters, start_date, end_date, division, format)
    else:
        return jsonify({'error': 'Invalid report type'}), 400
    
    if not result:
        return jsonify({'error': 'Failed to generate report'}), 500
    
    # Return file URL
    return jsonify({
        'success': True,
        'file_url': result['file_url'],
        'filename': result['filename']
    })


def generate_daily_driver_report(filters, start_date, end_date, division, format, include_charts, include_raw_data):
    """Generate a daily driver report"""
    # Query attendance records
    records = db.session.query(
        AttendanceRecord, Driver, JobSite
    ).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).join(
        JobSite, AttendanceRecord.assigned_job_id == JobSite.id
    ).filter(*filters).order_by(AttendanceRecord.date.desc()).all()
    
    if not records:
        return None
    
    # Format data for report
    formatted_records = []
    for record, driver, job_site in records:
        actual_job_site = None
        if record.actual_job_id:
            actual_job_site = db.session.get(JobSite, record.actual_job_id)
        
        item = {
            'Date': record.date.strftime('%m/%d/%Y'),
            'Driver': driver.full_name,
            'Employee ID': driver.employee_id,
            'Division': driver.division or '-',
            'Asset ID': record.asset_id or '-',
            'Job Site': job_site.job_number,
            'Expected Start': record.expected_start_time.strftime('%I:%M %p') if record.expected_start_time else '-',
            'Actual Start': record.actual_start_time.strftime('%I:%M %p') if record.actual_start_time else '-',
            'Expected End': record.expected_end_time.strftime('%I:%M %p') if record.expected_end_time else '-',
            'Actual End': record.actual_end_time.strftime('%I:%M %p') if record.actual_end_time else '-',
            'Late Start': 'Yes' if record.late_start else 'No',
            'Early End': 'Yes' if record.early_end else 'No',
            'Not On Job': 'Yes' if record.not_on_job else 'No',
            'Actual Job': actual_job_site.job_number if actual_job_site else '-',
            'Late Minutes': record.late_minutes if record.late_start else 0,
            'Early Minutes': record.early_minutes if record.early_end else 0,
            'Notes': record.notes or '-'
        }
        formatted_records.append(item)
    
    # Create summary data
    total_records = len(formatted_records)
    late_starts = sum(1 for r in formatted_records if r['Late Start'] == 'Yes')
    early_ends = sum(1 for r in formatted_records if r['Early End'] == 'Yes')
    not_on_job = sum(1 for r in formatted_records if r['Not On Job'] == 'Yes')
    on_time = total_records - (late_starts + early_ends + not_on_job)
    on_time_rate = round((on_time / total_records) * 100) if total_records > 0 else 0
    
    summary_data = {
        'Total Records': total_records,
        'Late Starts': late_starts,
        'Early Ends': early_ends,
        'Not On Job': not_on_job,
        'On Time': on_time,
        'On-Time Rate': f"{on_time_rate}%"
    }
    
    # Generate report based on format
    if format == 'excel':
        return generate_excel_report('Daily_Driver_Report', formatted_records, summary_data, start_date, end_date, division)
    elif format == 'csv':
        return generate_csv_report('Daily_Driver_Report', formatted_records, start_date, end_date, division)
    elif format == 'pdf':
        return generate_pdf_report('Daily_Driver_Report', formatted_records, summary_data, start_date, end_date, division)
    else:
        return None


def generate_weekly_summary_report(filters, start_date, end_date, division, format, include_charts, include_raw_data):
    """Generate a weekly summary report with trends"""
    # Group records by week
    weekly_data = []
    
    # Calculate first day of week
    def get_week_start(date):
        return date - timedelta(days=date.weekday())
    
    # Calculate each week's range
    current_week_start = get_week_start(start_date)
    
    while current_week_start <= end_date:
        week_end = current_week_start + timedelta(days=6)
        
        # Query attendance records for the week
        week_filters = filters.copy()
        week_filters.extend([
            AttendanceRecord.date >= current_week_start,
            AttendanceRecord.date <= min(week_end, end_date)
        ])
        
        # Count issues for the week
        late_starts = db.session.query(func.count(AttendanceRecord.id)).join(
            Driver, AttendanceRecord.driver_id == Driver.id
        ).filter(
            AttendanceRecord.late_start == True,
            *week_filters
        ).scalar() or 0
        
        early_ends = db.session.query(func.count(AttendanceRecord.id)).join(
            Driver, AttendanceRecord.driver_id == Driver.id
        ).filter(
            AttendanceRecord.early_end == True,
            *week_filters
        ).scalar() or 0
        
        not_on_job = db.session.query(func.count(AttendanceRecord.id)).join(
            Driver, AttendanceRecord.driver_id == Driver.id
        ).filter(
            AttendanceRecord.not_on_job == True,
            *week_filters
        ).scalar() or 0
        
        total_records = db.session.query(func.count(AttendanceRecord.id)).join(
            Driver, AttendanceRecord.driver_id == Driver.id
        ).filter(*week_filters).scalar() or 0
        
        on_time = total_records - (late_starts + early_ends + not_on_job)
        on_time_rate = round((on_time / total_records) * 100) if total_records > 0 else 0
        
        # Add week data
        weekly_data.append({
            'Week Start': current_week_start.strftime('%m/%d/%Y'),
            'Week End': min(week_end, end_date).strftime('%m/%d/%Y'),
            'Total Records': total_records,
            'Late Starts': late_starts,
            'Early Ends': early_ends,
            'Not On Job': not_on_job,
            'On Time': on_time,
            'On-Time Rate': f"{on_time_rate}%"
        })
        
        # Move to next week
        current_week_start = week_end + timedelta(days=1)
    
    if not weekly_data:
        return None
    
    # Calculate overall summary
    total_records = sum(week['Total Records'] for week in weekly_data)
    late_starts = sum(week['Late Starts'] for week in weekly_data)
    early_ends = sum(week['Early Ends'] for week in weekly_data)
    not_on_job = sum(week['Not On Job'] for week in weekly_data)
    on_time = sum(week['On Time'] for week in weekly_data)
    on_time_rate = round((on_time / total_records) * 100) if total_records > 0 else 0
    
    summary_data = {
        'Total Records': total_records,
        'Late Starts': late_starts,
        'Early Ends': early_ends,
        'Not On Job': not_on_job,
        'On Time': on_time,
        'On-Time Rate': f"{on_time_rate}%"
    }
    
    # Generate report based on format
    if format == 'excel':
        return generate_excel_report('Weekly_Summary_Report', weekly_data, summary_data, start_date, end_date, division)
    elif format == 'csv':
        return generate_csv_report('Weekly_Summary_Report', weekly_data, start_date, end_date, division)
    elif format == 'pdf':
        return generate_pdf_report('Weekly_Summary_Report', weekly_data, summary_data, start_date, end_date, division)
    else:
        return None


def generate_driver_performance_report(filters, start_date, end_date, division, format, include_charts, include_raw_data):
    """Generate a driver performance report"""
    # Group records by driver
    driver_records = {}
    
    # Query all records
    records = db.session.query(
        AttendanceRecord, Driver
    ).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).filter(*filters).all()
    
    if not records:
        return None
    
    # Group by driver
    for record, driver in records:
        if driver.id not in driver_records:
            driver_records[driver.id] = {
                'Driver': driver.full_name,
                'Employee ID': driver.employee_id,
                'Division': driver.division or '-',
                'Total Records': 0,
                'Late Starts': 0,
                'Early Ends': 0,
                'Not On Job': 0,
                'On Time': 0,
                'On-Time Rate': 0
            }
        
        driver_records[driver.id]['Total Records'] += 1
        
        if record.late_start:
            driver_records[driver.id]['Late Starts'] += 1
        
        if record.early_end:
            driver_records[driver.id]['Early Ends'] += 1
        
        if record.not_on_job:
            driver_records[driver.id]['Not On Job'] += 1
    
    # Calculate on-time rate for each driver
    for driver_id, data in driver_records.items():
        data['On Time'] = data['Total Records'] - (data['Late Starts'] + data['Early Ends'] + data['Not On Job'])
        data['On-Time Rate'] = f"{round((data['On Time'] / data['Total Records']) * 100)}%" if data['Total Records'] > 0 else "0%"
    
    # Convert to list
    driver_performance = list(driver_records.values())
    
    # Sort by on-time rate (descending)
    driver_performance.sort(key=lambda x: int(x['On-Time Rate'].rstrip('%')), reverse=True)
    
    # Calculate overall summary
    total_records = sum(driver['Total Records'] for driver in driver_performance)
    late_starts = sum(driver['Late Starts'] for driver in driver_performance)
    early_ends = sum(driver['Early Ends'] for driver in driver_performance)
    not_on_job = sum(driver['Not On Job'] for driver in driver_performance)
    on_time = sum(driver['On Time'] for driver in driver_performance)
    on_time_rate = round((on_time / total_records) * 100) if total_records > 0 else 0
    
    summary_data = {
        'Total Records': total_records,
        'Late Starts': late_starts,
        'Early Ends': early_ends,
        'Not On Job': not_on_job,
        'On Time': on_time,
        'On-Time Rate': f"{on_time_rate}%"
    }
    
    # Generate report based on format
    if format == 'excel':
        return generate_excel_report('Driver_Performance_Report', driver_performance, summary_data, start_date, end_date, division)
    elif format == 'csv':
        return generate_csv_report('Driver_Performance_Report', driver_performance, start_date, end_date, division)
    elif format == 'pdf':
        return generate_pdf_report('Driver_Performance_Report', driver_performance, summary_data, start_date, end_date, division)
    else:
        return None


def generate_job_site_performance_report(filters, start_date, end_date, division, format, include_charts, include_raw_data):
    """Generate a job site performance report"""
    # Group records by job site
    job_site_records = {}
    
    # Query all records
    records = db.session.query(
        AttendanceRecord, JobSite
    ).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).join(
        JobSite, AttendanceRecord.assigned_job_id == JobSite.id
    ).filter(*filters).all()
    
    if not records:
        return None
    
    # Group by job site
    for record, job_site in records:
        if job_site.id not in job_site_records:
            job_site_records[job_site.id] = {
                'Job Number': job_site.job_number,
                'Location': job_site.location or '-',
                'Division': job_site.division or '-',
                'Total Records': 0,
                'Late Starts': 0,
                'Early Ends': 0,
                'Not On Job': 0,
                'On Time': 0,
                'On-Time Rate': 0,
                'Active Drivers': set()
            }
        
        job_site_records[job_site.id]['Total Records'] += 1
        job_site_records[job_site.id]['Active Drivers'].add(record.driver_id)
        
        if record.late_start:
            job_site_records[job_site.id]['Late Starts'] += 1
        
        if record.early_end:
            job_site_records[job_site.id]['Early Ends'] += 1
        
        if record.not_on_job:
            job_site_records[job_site.id]['Not On Job'] += 1
    
    # Calculate on-time rate for each job site
    for job_site_id, data in job_site_records.items():
        data['On Time'] = data['Total Records'] - (data['Late Starts'] + data['Early Ends'] + data['Not On Job'])
        data['On-Time Rate'] = f"{round((data['On Time'] / data['Total Records']) * 100)}%" if data['Total Records'] > 0 else "0%"
        data['Active Drivers'] = len(data['Active Drivers'])
    
    # Convert to list
    job_site_performance = list(job_site_records.values())
    
    # Sort by on-time rate (descending)
    job_site_performance.sort(key=lambda x: int(x['On-Time Rate'].rstrip('%')), reverse=True)
    
    # Calculate overall summary
    total_records = sum(site['Total Records'] for site in job_site_performance)
    late_starts = sum(site['Late Starts'] for site in job_site_performance)
    early_ends = sum(site['Early Ends'] for site in job_site_performance)
    not_on_job = sum(site['Not On Job'] for site in job_site_performance)
    on_time = sum(site['On Time'] for site in job_site_performance)
    on_time_rate = round((on_time / total_records) * 100) if total_records > 0 else 0
    
    summary_data = {
        'Total Records': total_records,
        'Late Starts': late_starts,
        'Early Ends': early_ends,
        'Not On Job': not_on_job,
        'On Time': on_time,
        'On-Time Rate': f"{on_time_rate}%"
    }
    
    # Generate report based on format
    if format == 'excel':
        return generate_excel_report('Job_Site_Performance_Report', job_site_performance, summary_data, start_date, end_date, division)
    elif format == 'csv':
        return generate_csv_report('Job_Site_Performance_Report', job_site_performance, start_date, end_date, division)
    elif format == 'pdf':
        return generate_pdf_report('Job_Site_Performance_Report', job_site_performance, summary_data, start_date, end_date, division)
    else:
        return None


def generate_executive_summary_report(filters, start_date, end_date, division, format):
    """Generate an executive summary report"""
    # Get division data
    division_records = {}
    
    # Query all records grouped by division
    records = db.session.query(
        AttendanceRecord, Driver
    ).join(
        Driver, AttendanceRecord.driver_id == Driver.id
    ).filter(*filters).all()
    
    if not records:
        return None
    
    # Group by division
    for record, driver in records:
        division_name = driver.division or 'Undefined'
        
        if division_name not in division_records:
            division_records[division_name] = {
                'Division': division_name,
                'Total Records': 0,
                'Late Starts': 0,
                'Early Ends': 0,
                'Not On Job': 0,
                'On Time': 0,
                'On-Time Rate': 0,
                'Active Drivers': set()
            }
        
        division_records[division_name]['Total Records'] += 1
        division_records[division_name]['Active Drivers'].add(driver.id)
        
        if record.late_start:
            division_records[division_name]['Late Starts'] += 1
        
        if record.early_end:
            division_records[division_name]['Early Ends'] += 1
        
        if record.not_on_job:
            division_records[division_name]['Not On Job'] += 1
    
    # Calculate on-time rate for each division
    for division_name, data in division_records.items():
        data['On Time'] = data['Total Records'] - (data['Late Starts'] + data['Early Ends'] + data['Not On Job'])
        data['On-Time Rate'] = f"{round((data['On Time'] / data['Total Records']) * 100)}%" if data['Total Records'] > 0 else "0%"
        data['Active Drivers'] = len(data['Active Drivers'])
    
    # Convert to list
    division_performance = list(division_records.values())
    
    # Calculate overall summary
    total_records = sum(div['Total Records'] for div in division_performance)
    late_starts = sum(div['Late Starts'] for div in division_performance)
    early_ends = sum(div['Early Ends'] for div in division_performance)
    not_on_job = sum(div['Not On Job'] for div in division_performance)
    on_time = sum(div['On Time'] for div in division_performance)
    on_time_rate = round((on_time / total_records) * 100) if total_records > 0 else 0
    active_drivers = sum(div['Active Drivers'] for div in division_performance)
    
    summary_data = {
        'Period': f"{start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}",
        'Active Drivers': active_drivers,
        'Total Records': total_records,
        'Late Starts': late_starts,
        'Early Ends': early_ends,
        'Not On Job': not_on_job,
        'On Time': on_time,
        'On-Time Rate': f"{on_time_rate}%"
    }
    
    # Generate report based on format
    if format == 'excel':
        return generate_excel_report('Executive_Summary_Report', division_performance, summary_data, start_date, end_date, division)
    elif format == 'csv':
        return generate_csv_report('Executive_Summary_Report', division_performance, start_date, end_date, division)
    elif format == 'pdf':
        return generate_pdf_report('Executive_Summary_Report', division_performance, summary_data, start_date, end_date, division)
    else:
        return None


def generate_excel_report(report_name, data, summary_data, start_date, end_date, division):
    """Generate an Excel report"""
    try:
        # Create DataFrame from data
        df = pd.DataFrame(data)
        
        # Generate Excel file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_name.replace(' ', '_')}_{timestamp}.xlsx"
        filepath = f"exports/driver_reports/{filename}"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Create Excel writer
        writer = pd.ExcelWriter(filepath, engine='openpyxl')
        
        # Write data to excel
        df.to_excel(writer, sheet_name='Data', index=False)
        
        # Write summary to excel
        summary_df = pd.DataFrame([summary_data])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Save the excel file
        writer.close()
        
        # Return file URL
        return {
            'file_url': f"/exports/driver_reports/{filename}",
            'filename': filename
        }
    except Exception as e:
        current_app.logger.error(f"Error generating Excel report: {e}")
        return None


def generate_csv_report(report_name, data, start_date, end_date, division):
    """Generate a CSV report"""
    try:
        # Create DataFrame from data
        df = pd.DataFrame(data)
        
        # Generate CSV file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_name.replace(' ', '_')}_{timestamp}.csv"
        filepath = f"exports/driver_reports/{filename}"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write to CSV
        df.to_csv(filepath, index=False)
        
        # Return file URL
        return {
            'file_url': f"/exports/driver_reports/{filename}",
            'filename': filename
        }
    except Exception as e:
        current_app.logger.error(f"Error generating CSV report: {e}")
        return None


def generate_pdf_report(report_name, data, summary_data, start_date, end_date, division):
    """Generate a PDF report"""
    try:
        # Generate PDF file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_name.replace(' ', '_')}_{timestamp}.pdf"
        filepath = f"exports/driver_reports/{filename}"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Create PDF
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        
        # Create document
        doc = SimpleDocTemplate(filepath, pagesize=landscape(letter))
        elements = []
        
        # Add styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Add title
        elements.append(Paragraph(f"TRAXORA {report_name}", title_style))
        elements.append(Spacer(1, 12))
        
        # Add date range
        date_range = f"Period: {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
        if division != 'all':
            date_range += f" | Division: {division}"
        elements.append(Paragraph(date_range, normal_style))
        elements.append(Spacer(1, 12))
        
        # Add summary
        elements.append(Paragraph("Summary", subtitle_style))
        elements.append(Spacer(1, 6))
        
        # Create summary table
        summary_table_data = []
        for key, value in summary_data.items():
            summary_table_data.append([key, value])
        
        summary_table = Table(summary_table_data, colWidths=[200, 100])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1),
             6),
            ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 12))
        
        # Add data
        elements.append(Paragraph("Data", subtitle_style))
        elements.append(Spacer(1, 6))
        
        # Create data table
        if data:
            # Get column headers
            table_data = [list(data[0].keys())]
            
            # Add rows
            for row in data:
                table_data.append(list(row.values()))
            
            # Create table
            data_table = Table(table_data, repeatRows=1)
            data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))
            elements.append(data_table)
        
        # Build PDF
        doc.build(elements)
        
        # Return file URL
        return {
            'file_url': f"/exports/driver_reports/{filename}",
            'filename': filename
        }
    except Exception as e:
        current_app.logger.error(f"Error generating PDF report: {e}")
        return None