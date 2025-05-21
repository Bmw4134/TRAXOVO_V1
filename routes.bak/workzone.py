"""
Work Zone Analysis Module

This module handles routes for displaying and analyzing work zone efficiency.
"""
from datetime import datetime, timedelta
import calendar
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from sqlalchemy import func, desc, and_
from app import db
from models.reports import Jobsite, WorkZoneHours, DriverAttendance

# Create blueprint
workzone_bp = Blueprint('workzone', __name__)

@workzone_bp.route('/workzone', methods=['GET'])
@login_required
def workzone_dashboard():
    """Display the work zone analysis dashboard"""
    # Get query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    jobsite_id = request.args.get('jobsite_id')
    efficiency_threshold = request.args.get('efficiency')
    
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
        # Default to today
        end_date = today.date()
    else:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            end_date = today.date()
    
    # Build the base query
    query = db.session.query(
        WorkZoneHours,
        Jobsite
    ).join(
        Jobsite, WorkZoneHours.jobsite_id == Jobsite.id
    ).filter(
        WorkZoneHours.date.between(start_date, end_date)
    )
    
    # Apply jobsite filter if provided
    if jobsite_id:
        query = query.filter(WorkZoneHours.jobsite_id == jobsite_id)
    
    # Apply efficiency threshold filter if provided
    if efficiency_threshold:
        try:
            threshold = float(efficiency_threshold)
            query = query.filter(WorkZoneHours.efficiency_percentage <= threshold)
        except ValueError:
            pass
    
    # Order by date descending
    query = query.order_by(desc(WorkZoneHours.date))
    
    # Execute query
    workzone_records = query.all()
    
    # Get all jobsites for filter dropdown
    jobsites = Jobsite.query.order_by(Jobsite.name).all()
    
    # Calculate summary statistics
    total_hours = sum(record[0].total_hours or 0 for record in workzone_records)
    equipment_hours = sum(record[0].equipment_hours or 0 for record in workzone_records)
    labor_hours = sum(record[0].labor_hours or 0 for record in workzone_records)
    expected_hours = sum(record[0].expected_hours or 0 for record in workzone_records)
    
    # Calculate overall efficiency
    if expected_hours > 0:
        overall_efficiency = (total_hours / expected_hours) * 100
    else:
        overall_efficiency = 0
    
    # Get jobsite efficiency rankings
    jobsite_efficiency = db.session.query(
        Jobsite.id,
        Jobsite.name,
        Jobsite.code,
        func.sum(WorkZoneHours.total_hours).label('total_hours'),
        func.sum(WorkZoneHours.expected_hours).label('expected_hours'),
        (func.sum(WorkZoneHours.total_hours) / func.sum(WorkZoneHours.expected_hours) * 100).label('efficiency')
    ).join(
        WorkZoneHours, Jobsite.id == WorkZoneHours.jobsite_id
    ).filter(
        WorkZoneHours.date.between(start_date, end_date),
        WorkZoneHours.expected_hours > 0
    ).group_by(
        Jobsite.id, Jobsite.name, Jobsite.code
    ).order_by(
        desc((func.sum(WorkZoneHours.total_hours) / func.sum(WorkZoneHours.expected_hours) * 100))
    ).limit(10).all()
    
    return render_template(
        'workzone/dashboard.html',
        workzone_records=workzone_records,
        jobsites=jobsites,
        start_date=start_date,
        end_date=end_date,
        selected_jobsite_id=jobsite_id,
        efficiency_threshold=efficiency_threshold,
        stats={
            'total_hours': total_hours,
            'equipment_hours': equipment_hours,
            'labor_hours': labor_hours,
            'expected_hours': expected_hours,
            'overall_efficiency': overall_efficiency,
            'record_count': len(workzone_records)
        },
        jobsite_efficiency=jobsite_efficiency
    )

@workzone_bp.route('/workzone/api/efficiency-trend', methods=['GET'])
@login_required
def efficiency_trend_api():
    """API endpoint for work zone efficiency trend data"""
    # Get query parameters
    jobsite_id = request.args.get('jobsite_id')
    period = request.args.get('period', 'week')  # 'day', 'week', 'month'
    limit = int(request.args.get('limit', 30))  # Default to 30 days
    
    # Calculate date range based on period
    today = datetime.today()
    if period == 'day':
        # Last X days
        end_date = today.date()
        start_date = end_date - timedelta(days=limit-1)
        group_by = func.date(WorkZoneHours.date)
        date_format = '%Y-%m-%d'
    elif period == 'week':
        # Last X weeks
        end_date = today.date()
        start_date = end_date - timedelta(weeks=limit)
        # Group by week number
        group_by = func.date_trunc('week', WorkZoneHours.date)
        date_format = 'Week of %Y-%m-%d'
    else:  # month
        # Last X months
        end_date = today.date()
        start_date = datetime(today.year - (limit // 12), today.month - (limit % 12), 1).date()
        if start_date > end_date:
            start_date = datetime(today.year - 1, today.month, 1).date()
        # Group by month
        group_by = func.date_trunc('month', WorkZoneHours.date)
        date_format = '%Y-%m'
    
    # Build the base query
    query = db.session.query(
        group_by.label('period'),
        func.sum(WorkZoneHours.total_hours).label('total_hours'),
        func.sum(WorkZoneHours.equipment_hours).label('equipment_hours'),
        func.sum(WorkZoneHours.labor_hours).label('labor_hours'),
        func.sum(WorkZoneHours.expected_hours).label('expected_hours'),
        (func.sum(WorkZoneHours.total_hours) / func.sum(WorkZoneHours.expected_hours) * 100).label('efficiency')
    ).filter(
        WorkZoneHours.date.between(start_date, end_date),
        WorkZoneHours.expected_hours > 0
    )
    
    # Apply jobsite filter if provided
    if jobsite_id:
        query = query.filter(WorkZoneHours.jobsite_id == jobsite_id)
    
    # Group and order the results
    query = query.group_by(group_by).order_by(group_by)
    
    # Execute query
    trend_data = query.all()
    
    # Format for chart display
    result = {
        'periods': [row.period.strftime(date_format) if hasattr(row.period, 'strftime') else str(row.period) for row in trend_data],
        'total_hours': [float(row.total_hours or 0) for row in trend_data],
        'equipment_hours': [float(row.equipment_hours or 0) for row in trend_data],
        'labor_hours': [float(row.labor_hours or 0) for row in trend_data],
        'expected_hours': [float(row.expected_hours or 0) for row in trend_data],
        'efficiency': [float(row.efficiency or 0) for row in trend_data]
    }
    
    return jsonify(result)

@workzone_bp.route('/workzone/api/geospatial', methods=['GET'])
@login_required
def geospatial_api():
    """API endpoint for geospatial work zone data"""
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
    
    # Query for geospatial data with efficiency metrics
    jobsite_data = db.session.query(
        Jobsite.id,
        Jobsite.name,
        Jobsite.code,
        Jobsite.latitude,
        Jobsite.longitude,
        func.sum(WorkZoneHours.total_hours).label('total_hours'),
        func.sum(WorkZoneHours.expected_hours).label('expected_hours'),
        (func.sum(WorkZoneHours.total_hours) / func.nullif(func.sum(WorkZoneHours.expected_hours), 0) * 100).label('efficiency'),
        func.count(WorkZoneHours.id).label('record_count')
    ).join(
        WorkZoneHours, Jobsite.id == WorkZoneHours.jobsite_id
    ).filter(
        WorkZoneHours.date.between(start_date, end_date),
        Jobsite.latitude.isnot(None),
        Jobsite.longitude.isnot(None)
    ).group_by(
        Jobsite.id, Jobsite.name, Jobsite.code, Jobsite.latitude, Jobsite.longitude
    ).all()
    
    # Format for map display
    result = {
        'jobsites': [{
            'id': jobsite.id,
            'name': jobsite.name,
            'code': jobsite.code,
            'latitude': float(jobsite.latitude) if jobsite.latitude else None,
            'longitude': float(jobsite.longitude) if jobsite.longitude else None,
            'total_hours': float(jobsite.total_hours or 0),
            'expected_hours': float(jobsite.expected_hours or 0),
            'efficiency': float(jobsite.efficiency or 0),
            'record_count': jobsite.record_count
        } for jobsite in jobsite_data if jobsite.latitude and jobsite.longitude]
    }
    
    return jsonify(result)