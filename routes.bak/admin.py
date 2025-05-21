"""
Admin Routes for TRAXORA

This module handles administrative routes including user management,
system settings, and activity log monitoring.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc

from models import User, ActivityLog, db
from utils.rbac import admin_required

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard"""
    return render_template('admin/index.html')


@admin_bp.route('/activity')
@login_required
@admin_required
def activity_logs():
    """View system activity logs"""
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    event_type = request.args.get('event_type')
    user_id = request.args.get('user_id', type=int)
    resource_type = request.args.get('resource_type')
    days = request.args.get('days', 7, type=int)
    
    # Base query
    query = ActivityLog.query
    
    # Apply filters
    if event_type:
        query = query.filter(ActivityLog.event_type == event_type)
    
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    if resource_type:
        query = query.filter(ActivityLog.resource_type == resource_type)
    
    # Filter by date range
    if days:
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ActivityLog.timestamp >= since_date)
    
    # Order by timestamp (most recent first)
    query = query.order_by(desc(ActivityLog.timestamp))
    
    # Paginate results
    logs = query.paginate(page=page, per_page=per_page)
    
    # Get all users for the filter dropdown
    users = User.query.all()
    
    # Get unique event types and resource types for filter dropdowns
    event_types = db.session.query(ActivityLog.event_type.distinct()).all()
    resource_types = db.session.query(ActivityLog.resource_type.distinct()).all()
    
    # Prepare event type list
    event_type_list = [et[0] for et in event_types if et[0]]
    
    # Prepare resource type list
    resource_type_list = [rt[0] for rt in resource_types if rt[0]]
    
    return render_template(
        'admin/activity_logs.html',
        logs=logs,
        users=users,
        event_types=event_type_list,
        resource_types=resource_type_list,
        selected_event_type=event_type,
        selected_user_id=user_id,
        selected_resource_type=resource_type,
        selected_days=days
    )


@admin_bp.route('/activity/export')
@login_required
@admin_required
def export_activity_logs():
    """Export activity logs as CSV"""
    import csv
    from io import StringIO
    from flask import Response
    
    # Get query parameters (same as activity_logs route)
    event_type = request.args.get('event_type')
    user_id = request.args.get('user_id', type=int)
    resource_type = request.args.get('resource_type')
    days = request.args.get('days', 7, type=int)
    
    # Base query
    query = ActivityLog.query
    
    # Apply filters
    if event_type:
        query = query.filter(ActivityLog.event_type == event_type)
    
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    if resource_type:
        query = query.filter(ActivityLog.resource_type == resource_type)
    
    # Filter by date range
    if days:
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ActivityLog.timestamp >= since_date)
    
    # Order by timestamp (most recent first)
    logs = query.order_by(desc(ActivityLog.timestamp)).all()
    
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow([
        'ID', 'Timestamp', 'User', 'Event Type', 'Resource Type', 
        'Resource ID', 'Action', 'Description', 'IP Address', 'Success'
    ])
    
    # Write data rows
    for log in logs:
        user_name = log.user.username if log.user else 'System'
        writer.writerow([
            log.id,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            user_name,
            log.event_type,
            log.resource_type or '',
            log.resource_id or '',
            log.action or '',
            log.description or '',
            log.ip_address or '',
            'Yes' if log.success else 'No'
        ])
    
    # Prepare response
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment;filename=activity_logs_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


@admin_bp.route('/activity/stats')
@login_required
@admin_required
def activity_stats():
    """Get activity statistics for charts"""
    from sqlalchemy import func
    
    # Get time range from request
    days = request.args.get('days', 7, type=int)
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get event counts by type
    event_counts = db.session.query(
        ActivityLog.event_type, 
        func.count(ActivityLog.id)
    ).filter(
        ActivityLog.timestamp >= since_date
    ).group_by(
        ActivityLog.event_type
    ).all()
    
    # Get event counts by day
    daily_counts = db.session.query(
        func.date(ActivityLog.timestamp),
        func.count(ActivityLog.id)
    ).filter(
        ActivityLog.timestamp >= since_date
    ).group_by(
        func.date(ActivityLog.timestamp)
    ).all()
    
    # Get top users by activity
    top_users = db.session.query(
        ActivityLog.user_id,
        func.count(ActivityLog.id)
    ).filter(
        ActivityLog.timestamp >= since_date,
        ActivityLog.user_id != None
    ).group_by(
        ActivityLog.user_id
    ).order_by(
        func.count(ActivityLog.id).desc()
    ).limit(5).all()
    
    # Get user names for top users
    top_users_data = []
    for user_id, count in top_users:
        user = User.query.get(user_id)
        if user:
            top_users_data.append({
                'user_id': user_id,
                'username': user.username,
                'count': count
            })
    
    # Prepare data for response
    data = {
        'event_counts': {event: count for event, count in event_counts},
        'daily_counts': {date.strftime('%Y-%m-%d'): count for date, count in daily_counts},
        'top_users': top_users_data
    }
    
    return jsonify(data)