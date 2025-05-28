"""
Attendance Analysis Routes
This module contains routes for displaying attendance analytics and trend data.
"""
import os
import numpy as np
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from models.attendance import Driver, JobSite, AttendanceRecord, AttendanceTrend
from db import db

# Create the attendance blueprint
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/')
@login_required
def index():
    """Attendance dashboard main page."""
    return redirect(url_for('attendance.trends'))

@attendance_bp.route('/trends')
@login_required
def trends():
    """Display attendance trends and analytics."""
    # Get query parameters
    date_range = request.args.get('date_range', '30')
    try:
        date_range = int(date_range)
    except ValueError:
        date_range = 30
    
    region = request.args.get('region', 'all')
    incident_type = request.args.get('incident_type', 'all')
    
    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=date_range)
    
    # Base query for attendance records
    base_query = AttendanceRecord.query.filter(
        AttendanceRecord.report_date.between(start_date, end_date)
    )
    
    # Apply region filter if specified
    if region != 'all':
        # Join with driver to filter by region
        base_query = base_query.join(Driver).filter(Driver.region == region)
    
    # Apply incident type filter if specified
    if incident_type != 'all':
        base_query = base_query.filter(AttendanceRecord.status_type == incident_type.upper())
    
    # Get summary counts
    summary = {
        'total_incidents': base_query.count(),
        'late_starts': base_query.filter(AttendanceRecord.status_type == 'LATE_START').count(),
        'early_ends': base_query.filter(AttendanceRecord.status_type == 'EARLY_END').count(),
        'not_on_job': base_query.filter(AttendanceRecord.status_type == 'NOT_ON_JOB').count()
    }
    
    # Get all available regions
    regions = [r[0] for r in Driver.query.with_entities(Driver.region).distinct().all() if r[0]]
    
    # Get daily data for chart
    daily_data = {}
    date_range_list = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(date_range)]
    date_range_list.reverse()  # Oldest to newest
    
    daily_data['dates'] = date_range_list
    daily_data['late_starts'] = []
    daily_data['early_ends'] = []
    daily_data['not_on_job'] = []
    
    for date_str in date_range_list:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Query counts for each status type on this date
        late_count = base_query.filter(
            AttendanceRecord.report_date == date_obj,
            AttendanceRecord.status_type == 'LATE_START'
        ).count()
        
        early_count = base_query.filter(
            AttendanceRecord.report_date == date_obj,
            AttendanceRecord.status_type == 'EARLY_END'
        ).count()
        
        noj_count = base_query.filter(
            AttendanceRecord.report_date == date_obj,
            AttendanceRecord.status_type == 'NOT_ON_JOB'
        ).count()
        
        daily_data['late_starts'].append(late_count)
        daily_data['early_ends'].append(early_count)
        daily_data['not_on_job'].append(noj_count)
    
    # Get top drivers with attendance issues
    top_drivers_query = db.session.query(
        AttendanceRecord.driver_id,
        func.count(AttendanceRecord.id).label('total_incidents')
    ).filter(
        AttendanceRecord.report_date.between(start_date, end_date)
    )
    
    if incident_type != 'all':
        top_drivers_query = top_drivers_query.filter(AttendanceRecord.status_type == incident_type.upper())
    
    top_drivers_query = top_drivers_query.group_by(
        AttendanceRecord.driver_id
    ).order_by(
        desc('total_incidents')
    ).limit(10)
    
    top_drivers = []
    for driver_id, total_incidents in top_drivers_query.all():
        driver = Driver.query.get(driver_id)
        if driver:
            # Calculate trend (change from previous period)
            prev_start_date = start_date - timedelta(days=date_range)
            prev_end_date = end_date - timedelta(days=date_range)
            
            prev_incidents = AttendanceRecord.query.filter(
                AttendanceRecord.driver_id == driver_id,
                AttendanceRecord.report_date.between(prev_start_date, prev_end_date)
            )
            
            if incident_type != 'all':
                prev_incidents = prev_incidents.filter(AttendanceRecord.status_type == incident_type.upper())
            
            prev_count = prev_incidents.count()
            
            if prev_count > 0:
                trend = ((total_incidents - prev_count) / prev_count) * 100
            else:
                trend = 100 if total_incidents > 0 else 0
                
            top_drivers.append({
                'id': driver.id,
                'name': driver.name,
                'employee_id': driver.employee_id,
                'asset_id': driver.asset_id,
                'total_incidents': total_incidents,
                'trend': round(trend)
            })
    
    # Get top job sites with attendance issues
    top_sites_query = db.session.query(
        AttendanceRecord.job_site_id,
        func.count(AttendanceRecord.id).label('total_incidents')
    ).filter(
        AttendanceRecord.report_date.between(start_date, end_date)
    )
    
    if incident_type != 'all':
        top_sites_query = top_sites_query.filter(AttendanceRecord.status_type == incident_type.upper())
    
    top_sites_query = top_sites_query.group_by(
        AttendanceRecord.job_site_id
    ).order_by(
        desc('total_incidents')
    ).limit(10)
    
    top_sites = []
    for site_id, total_incidents in top_sites_query.all():
        site = JobSite.query.get(site_id)
        if site:
            # Calculate trend (change from previous period)
            prev_start_date = start_date - timedelta(days=date_range)
            prev_end_date = end_date - timedelta(days=date_range)
            
            prev_incidents = AttendanceRecord.query.filter(
                AttendanceRecord.job_site_id == site_id,
                AttendanceRecord.report_date.between(prev_start_date, prev_end_date)
            )
            
            if incident_type != 'all':
                prev_incidents = prev_incidents.filter(AttendanceRecord.status_type == incident_type.upper())
            
            prev_count = prev_incidents.count()
            
            if prev_count > 0:
                trend = ((total_incidents - prev_count) / prev_count) * 100
            else:
                trend = 100 if total_incidents > 0 else 0
                
            top_sites.append({
                'id': site.id,
                'name': site.name,
                'job_number': site.job_number,
                'total_incidents': total_incidents,
                'trend': round(trend)
            })
    
    # Weekly heatmap data
    weekly_heatmap = []
    days_of_week = 7
    hours_of_day = 14  # 5 AM to 7 PM
    
    for day in range(days_of_week):  # 0=Monday to 6=Sunday
        for hour in range(5, 19):  # 5 AM to 7 PM
            # Count incidents for this day of week and hour of day
            day_query = base_query.filter(
                func.extract('dow', AttendanceRecord.report_date) == (day + 1) % 7 + 1
            )
            
            # For Late Start, use actual_start hour, for Early End use actual_end hour
            if incident_type == 'late_start':
                hour_count = day_query.filter(
                    AttendanceRecord.status_type == 'LATE_START',
                    func.extract('hour', AttendanceRecord.actual_start) == hour
                ).count()
            elif incident_type == 'early_end':
                hour_count = day_query.filter(
                    AttendanceRecord.status_type == 'EARLY_END',
                    func.extract('hour', AttendanceRecord.actual_end) == hour
                ).count()
            else:
                hour_count = day_query.filter(
                    AttendanceRecord.status_type.in_(['LATE_START', 'EARLY_END', 'NOT_ON_JOB']),
                    func.extract('hour', AttendanceRecord.report_date) == hour
                ).count()
            
            weekly_heatmap.append({'x': hour, 'y': day, 'v': hour_count})
    
    return render_template(
        'attendance_trends.html',
        title='Attendance Trends',
        summary=summary,
        daily_data=daily_data,
        weekly_heatmap=weekly_heatmap,
        top_drivers=top_drivers,
        top_sites=top_sites,
        date_range=date_range,
        region=region,
        regions=regions,
        incident_type=incident_type
    )

@attendance_bp.route('/driver/<int:driver_id>')
@login_required
def driver_details(driver_id):
    """Display detailed attendance history for a specific driver."""
    driver = Driver.query.get_or_404(driver_id)
    
    # Get query parameters
    date_range = request.args.get('date_range', '90')
    try:
        date_range = int(date_range)
    except ValueError:
        date_range = 90
    
    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=date_range)
    
    # Get attendance records for this driver
    attendance_records = AttendanceRecord.query.filter(
        AttendanceRecord.driver_id == driver_id,
        AttendanceRecord.report_date.between(start_date, end_date)
    ).order_by(
        AttendanceRecord.report_date.desc()
    ).all()
    
    # Count by incident type
    late_starts = sum(1 for r in attendance_records if r.status_type == 'LATE_START')
    early_ends = sum(1 for r in attendance_records if r.status_type == 'EARLY_END')
    not_on_job = sum(1 for r in attendance_records if r.status_type == 'NOT_ON_JOB')
    
    return render_template(
        'driver_details.html',
        title=f'Driver Details: {driver.name}',
        driver=driver,
        attendance_records=attendance_records,
        late_starts=late_starts,
        early_ends=early_ends,
        not_on_job=not_on_job,
        date_range=date_range
    )
@attendance_bp.route('/')
def index():
    """Handler for /"""
    try:
        # Add your route handler logic here
        return render_template('attendance/index.html')
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return render_template('error.html', error=str(e)), 500

@attendance_bp.route('/trends')
def trends():
    """Handler for /trends"""
    try:
        # Add your route handler logic here
        return render_template('attendance/trends.html')
    except Exception as e:
        logger.error(f"Error in trends: {e}")
        return render_template('error.html', error=str(e)), 500

@attendance_bp.route('/driver/<int:driver_id>')
def driver_details(driver_id):
    """Handler for driver details page"""
    try:
        # Add your route handler logic here
        return render_template('attendance/driver_details.html', driver_id=driver_id)
    except Exception as e:
        logger.error(f"Error in driver_details: {e}")
        return render_template('error.html', error=str(e)), 500
