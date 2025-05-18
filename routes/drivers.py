"""
Driver Reports Routes

This module provides routes for the driver reports module,
which handles driver attendance, job site performance, and related analytics.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, send_file, abort
import pandas as pd
import json
import os
import logging
import io
from sqlalchemy import func, desc, and_, or_
from app import db
from models.driver_attendance import DriverAttendance, JobSiteAttendance, AttendanceRecord, AttendanceImportLog

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
drivers_bp = Blueprint('drivers', __name__, url_prefix='/drivers')


# Main routes
@drivers_bp.route('/')
def index():
    """Display the driver reports dashboard"""
    return render_template('drivers/index.html')


@drivers_bp.route('/dashboard/kpi-data')
def kpi_data():
    """Get KPI data for the dashboard"""
    try:
        # Parse filter parameters
        date_range = request.args.get('date_range', 'last_7_days')
        division = request.args.get('division', 'all_divisions')
        department = request.args.get('department', 'all_departments')
        issue_type = request.args.get('issue_type', 'all_issues')
        
        # Calculate date filter based on date_range
        end_date = datetime.now().date()
        start_date = None
        
        if date_range == 'today':
            start_date = end_date
        elif date_range == 'yesterday':
            start_date = end_date - timedelta(days=1)
            end_date = start_date
        elif date_range == 'last_7_days':
            start_date = end_date - timedelta(days=6)
        elif date_range == 'this_month':
            start_date = end_date.replace(day=1)
        elif date_range == 'last_month':
            last_month = end_date.month - 1
            year = end_date.year
            if last_month == 0:
                last_month = 12
                year -= 1
            start_date = datetime(year, last_month, 1).date()
            # Set end_date to the last day of last month
            if last_month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, last_month + 1, 1).date() - timedelta(days=1)
        elif date_range == 'custom_range':
            # If a custom range is specified, it should be sent in additional parameters
            custom_start = request.args.get('start_date')
            custom_end = request.args.get('end_date')
            if custom_start and custom_end:
                try:
                    start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
                    end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
                except ValueError:
                    # If parsing fails, default to last 7 days
                    start_date = end_date - timedelta(days=6)
            else:
                # Default to last 7 days if custom range is incomplete
                start_date = end_date - timedelta(days=6)
        else:
            # Default to last 7 days for unrecognized values
            start_date = end_date - timedelta(days=6)
        
        # Build base query with date filter
        base_query = AttendanceRecord.query.filter(
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        )
        
        # Apply division filter if specified
        if division != 'all_divisions':
            # Join with appropriate tables to filter by division
            base_query = base_query.join(Driver).filter(Driver.division == division.upper())
        
        # Apply department filter if specified
        if department != 'all_departments':
            # Join with appropriate tables to filter by department
            base_query = base_query.join(Driver, AttendanceRecord.driver_id == Driver.id).filter(Driver.department == department)
        
        # Count metrics
        total_records = base_query.count()
        late_starts = base_query.filter(AttendanceRecord.late_start == True).count()
        early_ends = base_query.filter(AttendanceRecord.early_end == True).count()
        not_on_job = base_query.filter(AttendanceRecord.not_on_job == True).count()
        
        # Calculate on-time rate
        on_time_rate = 100
        if total_records > 0:
            on_time_records = total_records - (late_starts + early_ends + not_on_job)
            on_time_rate = round((on_time_records / total_records) * 100)
        
        # Calculate previous period metrics for trend
        prev_end_date = start_date - timedelta(days=1)
        period_length = (end_date - start_date).days + 1
        prev_start_date = prev_end_date - timedelta(days=period_length - 1)
        
        prev_query = AttendanceRecord.query.filter(
            AttendanceRecord.date >= prev_start_date,
            AttendanceRecord.date <= prev_end_date
        )
        
        # Apply same filters to previous period
        if division != 'all_divisions':
            prev_query = prev_query.join(Driver).filter(Driver.division == division.upper())
        
        if department != 'all_departments':
            prev_query = prev_query.join(Driver, AttendanceRecord.driver_id == Driver.id).filter(Driver.department == department)
        
        prev_total = prev_query.count()
        prev_late_starts = prev_query.filter(AttendanceRecord.late_start == True).count()
        prev_early_ends = prev_query.filter(AttendanceRecord.early_end == True).count()
        prev_not_on_job = prev_query.filter(AttendanceRecord.not_on_job == True).count()
        
        # Calculate previous on-time rate
        prev_on_time_rate = 100
        if prev_total > 0:
            prev_on_time = prev_total - (prev_late_starts + prev_early_ends + prev_not_on_job)
            prev_on_time_rate = round((prev_on_time / prev_total) * 100)
        
        # Calculate trends
        late_starts_trend = 0
        early_ends_trend = 0
        not_on_job_trend = 0
        on_time_rate_trend = 0
        
        if prev_total > 0:
            # Avoid division by zero
            late_starts_trend = round((late_starts / total_records * 100) - (prev_late_starts / prev_total * 100))
            early_ends_trend = round((early_ends / total_records * 100) - (prev_early_ends / prev_total * 100))
            not_on_job_trend = round((not_on_job / total_records * 100) - (prev_not_on_job / prev_total * 100))
            
        on_time_rate_trend = on_time_rate - prev_on_time_rate
        
        # Determine trend directions
        late_starts_direction = 'up' if late_starts_trend > 0 else 'down' if late_starts_trend < 0 else 'none'
        early_ends_direction = 'up' if early_ends_trend > 0 else 'down' if early_ends_trend < 0 else 'none'
        not_on_job_direction = 'up' if not_on_job_trend > 0 else 'down' if not_on_job_trend < 0 else 'none'
        on_time_rate_direction = 'up' if on_time_rate_trend > 0 else 'down' if on_time_rate_trend < 0 else 'none'
        
        # For these metrics, up is bad, down is good (except for on-time rate)
        response = {
            'late_starts': {
                'value': late_starts,
                'trend': late_starts_trend,
                'trend_direction': late_starts_direction
            },
            'early_ends': {
                'value': early_ends,
                'trend': early_ends_trend,
                'trend_direction': early_ends_direction
            },
            'not_on_job': {
                'value': not_on_job,
                'trend': not_on_job_trend,
                'trend_direction': not_on_job_direction
            },
            'on_time_rate': {
                'value': on_time_rate,
                'trend': on_time_rate_trend,
                'trend_direction': on_time_rate_direction
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in kpi_data: {str(e)}")
        return jsonify({'error': str(e)}), 500


@drivers_bp.route('/dashboard/trend-data')
def trend_data():
    """Get trend data for the attendance trend chart"""
    try:
        # Get parameters
        days = int(request.args.get('days', 30))
        division = request.args.get('division', 'all_divisions')
        department = request.args.get('department', 'all_departments')
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # Generate list of dates
        date_list = []
        for i in range(days):
            date_list.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
        
        # Query attendance data
        query = db.session.query(
            AttendanceRecord.date,
            func.count(AttendanceRecord.id).label('total_records'),
            func.sum(AttendanceRecord.late_start.cast(db.Integer)).label('late_starts'),
            func.sum(AttendanceRecord.early_end.cast(db.Integer)).label('early_ends'),
            func.sum(AttendanceRecord.not_on_job.cast(db.Integer)).label('not_on_job')
        ).filter(
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        ).group_by(
            AttendanceRecord.date
        )
        
        # Apply division filter if specified
        if division != 'all_divisions':
            query = query.join(Driver).filter(Driver.division == division.upper())
        
        # Apply department filter if specified
        if department != 'all_departments':
            query = query.join(Driver, AttendanceRecord.driver_id == Driver.id).filter(Driver.department == department)
        
        # Execute query
        results = query.all()
        
        # Convert to dictionary with date as key
        data_by_date = {}
        for row in results:
            date_str = row.date.strftime('%Y-%m-%d')
            data_by_date[date_str] = {
                'date': date_str,
                'total_records': row.total_records,
                'late_starts': row.late_starts or 0,
                'early_ends': row.early_ends or 0,
                'not_on_job': row.not_on_job or 0
            }
        
        # Ensure all dates have data
        response_data = []
        for date_str in date_list:
            if date_str in data_by_date:
                response_data.append(data_by_date[date_str])
            else:
                response_data.append({
                    'date': date_str,
                    'total_records': 0,
                    'late_starts': 0,
                    'early_ends': 0,
                    'not_on_job': 0
                })
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error in trend_data: {str(e)}")
        return jsonify({'error': str(e)}), 500


@drivers_bp.route('/dashboard/recent-issues')
def recent_issues():
    """Get recent attendance issues for the dashboard"""
    try:
        # Parse filter parameters
        date_range = request.args.get('date_range', 'last_7_days')
        division = request.args.get('division', 'all_divisions')
        department = request.args.get('department', 'all_departments')
        issue_type = request.args.get('issue_type', 'all_issues')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Calculate date filter based on date_range
        end_date = datetime.now().date()
        start_date = None
        
        if date_range == 'today':
            start_date = end_date
        elif date_range == 'yesterday':
            start_date = end_date - timedelta(days=1)
            end_date = start_date
        elif date_range == 'last_7_days':
            start_date = end_date - timedelta(days=6)
        elif date_range == 'this_month':
            start_date = end_date.replace(day=1)
        elif date_range == 'last_month':
            last_month = end_date.month - 1
            year = end_date.year
            if last_month == 0:
                last_month = 12
                year -= 1
            start_date = datetime(year, last_month, 1).date()
            # Set end_date to the last day of last month
            if last_month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, last_month + 1, 1).date() - timedelta(days=1)
        elif date_range == 'custom_range':
            # If a custom range is specified, it should be sent in additional parameters
            custom_start = request.args.get('start_date')
            custom_end = request.args.get('end_date')
            if custom_start and custom_end:
                try:
                    start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
                    end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
                except ValueError:
                    # If parsing fails, default to last 7 days
                    start_date = end_date - timedelta(days=6)
            else:
                # Default to last 7 days if custom range is incomplete
                start_date = end_date - timedelta(days=6)
        else:
            # Default to last 7 days for unrecognized values
            start_date = end_date - timedelta(days=6)
        
        # Build base query with date filter
        base_query = AttendanceRecord.query.filter(
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        )
        
        # Apply division filter if specified
        if division != 'all_divisions':
            base_query = base_query.join(Driver).filter(Driver.division == division.upper())
        
        # Apply department filter if specified
        if department != 'all_departments':
            base_query = base_query.join(Driver, AttendanceRecord.driver_id == Driver.id).filter(Driver.department == department)
        
        # Apply issue type filter if specified
        if issue_type == 'late_start':
            base_query = base_query.filter(AttendanceRecord.late_start == True)
        elif issue_type == 'early_end':
            base_query = base_query.filter(AttendanceRecord.early_end == True)
        elif issue_type == 'not_on_job':
            base_query = base_query.filter(AttendanceRecord.not_on_job == True)
        else:
            # If all issues, filter for any issue
            base_query = base_query.filter(or_(
                AttendanceRecord.late_start == True,
                AttendanceRecord.early_end == True,
                AttendanceRecord.not_on_job == True
            ))
        
        # Join with related models for data retrieval
        base_query = base_query.join(Driver)
        base_query = base_query.join(JobSite, AttendanceRecord.assigned_job_id == JobSite.id)
        
        # Order by date (most recent first)
        base_query = base_query.order_by(desc(AttendanceRecord.date))
        
        # Get total count for pagination
        total_records = base_query.count()
        total_pages = (total_records + per_page - 1) // per_page  # Ceiling division
        
        # Apply pagination
        records = base_query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format the response
        result_data = []
        for record in records:
            # Determine issue type (prioritize not_on_job, then late_start, then early_end)
            issue_type_label = None
            if record.not_on_job:
                issue_type_label = "Not On Job"
            elif record.late_start:
                issue_type_label = "Late Start"
            elif record.early_end:
                issue_type_label = "Early End"
            else:
                issue_type_label = "Unknown Issue"
            
            # Format times for display
            expected_time = record.expected_start_time.strftime("%H:%M") if record.expected_start_time else "--:--"
            actual_time = record.actual_start_time.strftime("%H:%M") if record.actual_start_time else "--:--"
            
            # Calculate time difference in minutes
            time_diff = None
            if record.expected_start_time and record.actual_start_time and issue_type_label == "Late Start":
                diff = record.actual_start_time - record.expected_start_time
                time_diff = f"{int(diff.total_seconds() / 60)} min late"
            elif record.expected_end_time and record.actual_end_time and issue_type_label == "Early End":
                diff = record.expected_end_time - record.actual_end_time
                time_diff = f"{int(diff.total_seconds() / 60)} min early"
            else:
                time_diff = "N/A"
            
            result_data.append({
                'id': record.id,
                'date': record.date.strftime("%m/%d/%Y"),
                'driver': record.driver.full_name,
                'asset_id': record.asset_id or "N/A",
                'job_site': record.assigned_job.job_number,
                'issue_type': issue_type_label,
                'expected': expected_time,
                'actual': actual_time,
                'difference': time_diff
            })
        
        response = {
            'data': result_data,
            'page': page,
            'per_page': per_page,
            'total': total_records,
            'pages': total_pages
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in recent_issues: {str(e)}")
        return jsonify({'error': str(e)}), 500


@drivers_bp.route('/api/drivers')
def get_drivers():
    """Get list of drivers with filters and pagination"""
    try:
        # Parse filter parameters
        division = request.args.get('division', 'all_divisions')
        department = request.args.get('department', 'all_departments')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Build base query
        base_query = Driver.query
        
        # Apply division filter if specified
        if division != 'all_divisions':
            base_query = base_query.filter(Driver.division == division.upper())
        
        # Apply department filter if specified
        if department != 'all_departments':
            base_query = base_query.filter(Driver.department == department)
        
        # Apply search filter if specified
        if search:
            base_query = base_query.filter(or_(
                Driver.first_name.ilike(f'%{search}%'),
                Driver.last_name.ilike(f'%{search}%'),
                Driver.employee_id.ilike(f'%{search}%')
            ))
        
        # Get total count for pagination
        total_records = base_query.count()
        total_pages = (total_records + per_page - 1) // per_page  # Ceiling division
        
        # Apply pagination and ordering
        drivers = base_query.order_by(Driver.last_name).offset((page - 1) * per_page).limit(per_page).all()
        
        # Get latest records for each driver to find current asset and job
        driver_data = []
        for driver in drivers:
            # Get latest attendance record for this driver
            latest_record = AttendanceRecord.query.filter(
                AttendanceRecord.driver_id == driver.id
            ).order_by(desc(AttendanceRecord.date)).first()
            
            # Calculate attendance score (simple version)
            last_30_days_records = AttendanceRecord.query.filter(
                AttendanceRecord.driver_id == driver.id,
                AttendanceRecord.date >= (datetime.now().date() - timedelta(days=30))
            ).all()
            
            attendance_score = 100
            if last_30_days_records:
                total_issues = sum(1 for r in last_30_days_records if r.late_start or r.early_end or r.not_on_job)
                attendance_score = 100 - (total_issues / len(last_30_days_records) * 100)
                attendance_score = max(0, min(100, round(attendance_score)))
            
            # Get current job site name
            current_job = None
            if latest_record and latest_record.assigned_job:
                current_job = latest_record.assigned_job.job_number
            
            driver_data.append({
                'id': driver.id,
                'employee_id': driver.employee_id,
                'name': driver.full_name,
                'division': driver.division,
                'department': driver.department,
                'current_asset': latest_record.asset_id if latest_record else None,
                'current_job': current_job,
                'attendance_score': attendance_score,
                'is_active': driver.is_active
            })
        
        response = {
            'data': driver_data,
            'page': page,
            'per_page': per_page,
            'total': total_records,
            'pages': total_pages
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in get_drivers: {str(e)}")
        return jsonify({'error': str(e)}), 500


@drivers_bp.route('/api/driver/<int:driver_id>/metrics')
def driver_metrics(driver_id):
    """Get performance metrics for a specific driver"""
    try:
        # Get the driver
        driver = Driver.query.get_or_404(driver_id)
        
        # Get the latest record for current assignment
        latest_record = AttendanceRecord.query.filter(
            AttendanceRecord.driver_id == driver.id
        ).order_by(desc(AttendanceRecord.date)).first()
        
        # Current job site
        current_job = None
        if latest_record and latest_record.assigned_job:
            current_job = latest_record.assigned_job.job_number
        
        # Get attendance metrics for last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=29)
        
        current_records = AttendanceRecord.query.filter(
            AttendanceRecord.driver_id == driver.id,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        ).all()
        
        # Calculate metrics for current period
        current_total = len(current_records)
        current_late_starts = sum(1 for r in current_records if r.late_start)
        current_early_ends = sum(1 for r in current_records if r.early_end)
        current_not_on_job = sum(1 for r in current_records if r.not_on_job)
        
        # Calculate attendance score
        attendance_score = 100
        if current_total > 0:
            total_issues = current_late_starts + current_early_ends + current_not_on_job
            attendance_score = 100 - (total_issues / current_total * 100)
            attendance_score = max(0, min(100, round(attendance_score)))
        
        # Get metrics for previous 30 days for trend calculation
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=29)
        
        prev_records = AttendanceRecord.query.filter(
            AttendanceRecord.driver_id == driver.id,
            AttendanceRecord.date >= prev_start_date,
            AttendanceRecord.date <= prev_end_date
        ).all()
        
        # Calculate metrics for previous period
        prev_total = len(prev_records)
        prev_late_starts = sum(1 for r in prev_records if r.late_start)
        prev_early_ends = sum(1 for r in prev_records if r.early_end)
        prev_not_on_job = sum(1 for r in prev_records if r.not_on_job)
        
        # Calculate previous attendance score
        prev_attendance_score = 100
        if prev_total > 0:
            prev_total_issues = prev_late_starts + prev_early_ends + prev_not_on_job
            prev_attendance_score = 100 - (prev_total_issues / prev_total * 100)
            prev_attendance_score = max(0, min(100, round(prev_attendance_score)))
        
        # Calculate trends
        late_starts_trend = 0
        early_ends_trend = 0
        not_on_job_trend = 0
        attendance_score_trend = 0
        
        if prev_total > 0 and current_total > 0:
            late_starts_trend = round((current_late_starts / current_total * 100) - (prev_late_starts / prev_total * 100))
            early_ends_trend = round((current_early_ends / current_total * 100) - (prev_early_ends / prev_total * 100))
            not_on_job_trend = round((current_not_on_job / current_total * 100) - (prev_not_on_job / prev_total * 100))
        
        attendance_score_trend = attendance_score - prev_attendance_score
        
        # Determine trend directions
        late_starts_direction = 'up' if late_starts_trend > 0 else 'down' if late_starts_trend < 0 else 'none'
        early_ends_direction = 'up' if early_ends_trend > 0 else 'down' if early_ends_trend < 0 else 'none'
        not_on_job_direction = 'up' if not_on_job_trend > 0 else 'down' if not_on_job_trend < 0 else 'none'
        attendance_score_direction = 'up' if attendance_score_trend > 0 else 'down' if attendance_score_trend < 0 else 'none'
        
        response = {
            'driver': {
                'id': driver.id,
                'employee_id': driver.employee_id,
                'name': driver.full_name,
                'division': driver.division,
                'department': driver.department,
                'current_asset': latest_record.asset_id if latest_record else None,
                'current_job': current_job,
                'is_active': driver.is_active
            },
            'metrics': {
                'attendance_score': {
                    'value': attendance_score,
                    'trend': attendance_score_trend,
                    'trend_direction': attendance_score_direction
                },
                'late_starts': {
                    'value': current_late_starts,
                    'trend': late_starts_trend,
                    'trend_direction': late_starts_direction
                },
                'early_ends': {
                    'value': current_early_ends,
                    'trend': early_ends_trend,
                    'trend_direction': early_ends_direction
                },
                'not_on_job': {
                    'value': current_not_on_job,
                    'trend': not_on_job_trend,
                    'trend_direction': not_on_job_direction
                }
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in driver_metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500


@drivers_bp.route('/api/driver/<int:driver_id>/attendance-chart')
def driver_attendance_chart(driver_id):
    """Get attendance chart data for a specific driver"""
    try:
        # Get parameters
        days = int(request.args.get('days', 90))
        
        # Get the driver
        driver = Driver.query.get_or_404(driver_id)
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # Generate list of dates
        date_list = []
        for i in range(days):
            date_list.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
        
        # Query attendance data
        query = db.session.query(
            AttendanceRecord.date,
            func.sum(AttendanceRecord.late_start.cast(db.Integer)).label('late_starts'),
            func.sum(AttendanceRecord.early_end.cast(db.Integer)).label('early_ends'),
            func.sum(AttendanceRecord.not_on_job.cast(db.Integer)).label('not_on_job')
        ).filter(
            AttendanceRecord.driver_id == driver_id,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        ).group_by(
            AttendanceRecord.date
        )
        
        # Execute query
        results = query.all()
        
        # Convert to dictionary with date as key
        data_by_date = {}
        for row in results:
            date_str = row.date.strftime('%Y-%m-%d')
            # Calculate score for the day (1 point for each issue type)
            issues = (row.late_starts or 0) + (row.early_ends or 0) + (row.not_on_job or 0)
            score = 100 if issues == 0 else max(0, 100 - (issues * 33.33))
            
            data_by_date[date_str] = {
                'date': date_str,
                'score': round(score),
                'late_starts': row.late_starts or 0,
                'early_ends': row.early_ends or 0,
                'not_on_job': row.not_on_job or 0
            }
        
        # Ensure all dates have data
        response_data = []
        for date_str in date_list:
            if date_str in data_by_date:
                response_data.append(data_by_date[date_str])
            else:
                # Assume 100% score for days with no records (no issues)
                response_data.append({
                    'date': date_str,
                    'score': 100,
                    'late_starts': 0,
                    'early_ends': 0,
                    'not_on_job': 0
                })
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error in driver_attendance_chart: {str(e)}")
        return jsonify({'error': str(e)}), 500


@drivers_bp.route('/api/driver/<int:driver_id>/attendance-history')
def driver_attendance_history(driver_id):
    """Get attendance history for a specific driver with pagination"""
    try:
        # Get parameters
        days = int(request.args.get('days', 30))
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Get the driver
        driver = Driver.query.get_or_404(driver_id)
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # Query attendance records
        query = AttendanceRecord.query.filter(
            AttendanceRecord.driver_id == driver_id,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        ).order_by(desc(AttendanceRecord.date))
        
        # Get total count for pagination
        total_records = query.count()
        total_pages = (total_records + per_page - 1) // per_page  # Ceiling division
        
        # Apply pagination
        records = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format records for response
        result_data = []
        for record in records:
            # Determine status label
            status = "On Time"
            if record.not_on_job:
                status = "Wrong Job"
            elif record.late_start:
                status = "Late Start"
            elif record.early_end:
                status = "Early End"
            
            # Get job site name
            job_site = record.assigned_job.job_number if record.assigned_job else "Unknown"
            
            # Format start and end times
            start_time = record.actual_start_time.strftime("%H:%M") if record.actual_start_time else None
            end_time = record.actual_end_time.strftime("%H:%M") if record.actual_end_time else None
            
            result_data.append({
                'id': record.id,
                'date': record.date.strftime("%m/%d/%Y"),
                'asset_id': record.asset_id,
                'job_site': job_site,
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'notes': record.notes
            })
        
        response = {
            'data': result_data,
            'page': page,
            'per_page': per_page,
            'total': total_records,
            'pages': total_pages
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in driver_attendance_history: {str(e)}")
        return jsonify({'error': str(e)}), 500


@drivers_bp.route('/api/job-sites')
def get_job_sites():
    """Get list of job sites with filters and pagination"""
    try:
        # Parse filter parameters
        date_range = request.args.get('date_range', 'last_30_days')
        division = request.args.get('division', 'all_divisions')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Calculate date filter based on date_range
        end_date = datetime.now().date()
        start_date = None
        
        if date_range == 'today':
            start_date = end_date
        elif date_range == 'yesterday':
            start_date = end_date - timedelta(days=1)
            end_date = start_date
        elif date_range == 'last_7_days':
            start_date = end_date - timedelta(days=6)
        elif date_range == 'last_30_days':
            start_date = end_date - timedelta(days=29)
        elif date_range == 'this_month':
            start_date = end_date.replace(day=1)
        elif date_range == 'last_month':
            last_month = end_date.month - 1
            year = end_date.year
            if last_month == 0:
                last_month = 12
                year -= 1
            start_date = datetime(year, last_month, 1).date()
            # Set end_date to the last day of last month
            if last_month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, last_month + 1, 1).date() - timedelta(days=1)
        elif date_range == 'custom_range':
            # If a custom range is specified, it should be sent in additional parameters
            custom_start = request.args.get('start_date')
            custom_end = request.args.get('end_date')
            if custom_start and custom_end:
                try:
                    start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
                    end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
                except ValueError:
                    # If parsing fails, default to last 30 days
                    start_date = end_date - timedelta(days=29)
            else:
                # Default to last 30 days if custom range is incomplete
                start_date = end_date - timedelta(days=29)
        else:
            # Default to last 30 days for unrecognized values
            start_date = end_date - timedelta(days=29)
        
        # Build base query
        base_query = JobSite.query
        
        # Apply division filter if specified
        if division != 'all_divisions':
            base_query = base_query.filter(JobSite.division == division.upper())
        
        # Apply search filter if specified
        if search:
            base_query = base_query.filter(or_(
                JobSite.job_number.ilike(f'%{search}%'),
                JobSite.name.ilike(f'%{search}%'),
                JobSite.location.ilike(f'%{search}%')
            ))
        
        # Get total count for pagination
        total_records = base_query.count()
        total_pages = (total_records + per_page - 1) // per_page  # Ceiling division
        
        # Apply pagination and ordering
        job_sites = base_query.order_by(JobSite.job_number).offset((page - 1) * per_page).limit(per_page).all()
        
        # Format job sites for response
        result_data = []
        for job_site in job_sites:
            # Get attendance records for this job site in the date range
            records = AttendanceRecord.query.filter(
                AttendanceRecord.assigned_job_id == job_site.id,
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date
            ).all()
            
            # Count metrics
            late_starts = sum(1 for r in records if r.late_start)
            early_ends = sum(1 for r in records if r.early_end)
            not_on_job = sum(1 for r in records if r.not_on_job)
            
            # Count active drivers (unique drivers in the period)
            active_drivers = len(set(r.driver_id for r in records))
            
            # Calculate attendance score
            attendance_score = 100
            if records:
                total_issues = late_starts + early_ends + not_on_job
                attendance_score = 100 - (total_issues / len(records) * 100)
                attendance_score = max(0, min(100, round(attendance_score)))
            
            result_data.append({
                'id': job_site.id,
                'job_number': job_site.job_number,
                'name': job_site.name,
                'location': job_site.location,
                'division': job_site.division,
                'active_drivers': active_drivers,
                'late_starts': late_starts,
                'early_ends': early_ends,
                'not_on_job': not_on_job,
                'attendance_score': attendance_score,
                'is_active': job_site.is_active
            })
        
        response = {
            'data': result_data,
            'page': page,
            'per_page': per_page,
            'total': total_records,
            'pages': total_pages
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in get_job_sites: {str(e)}")
        return jsonify({'error': str(e)}), 500


@drivers_bp.route('/api/job-site/<int:job_site_id>/metrics')
def job_site_metrics(job_site_id):
    """Get performance metrics for a specific job site"""
    try:
        # Get the job site
        job_site = JobSite.query.get_or_404(job_site_id)
        
        # Get attendance metrics for last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=29)
        
        current_records = AttendanceRecord.query.filter(
            AttendanceRecord.assigned_job_id == job_site.id,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        ).all()
        
        # Count active drivers
        active_driver_ids = set(r.driver_id for r in current_records)
        active_drivers = len(active_driver_ids)
        
        # Calculate metrics for current period
        current_total = len(current_records)
        current_late_starts = sum(1 for r in current_records if r.late_start)
        current_early_ends = sum(1 for r in current_records if r.early_end)
        current_not_on_job = sum(1 for r in current_records if r.not_on_job)
        
        # Calculate attendance score
        attendance_score = 100
        if current_total > 0:
            total_issues = current_late_starts + current_early_ends + current_not_on_job
            attendance_score = 100 - (total_issues / current_total * 100)
            attendance_score = max(0, min(100, round(attendance_score)))
        
        # Get metrics for previous 30 days for trend calculation
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=29)
        
        prev_records = AttendanceRecord.query.filter(
            AttendanceRecord.assigned_job_id == job_site.id,
            AttendanceRecord.date >= prev_start_date,
            AttendanceRecord.date <= prev_end_date
        ).all()
        
        # Calculate metrics for previous period
        prev_total = len(prev_records)
        prev_late_starts = sum(1 for r in prev_records if r.late_start)
        prev_early_ends = sum(1 for r in prev_records if r.early_end)
        prev_not_on_job = sum(1 for r in prev_records if r.not_on_job)
        
        # Calculate previous attendance score
        prev_attendance_score = 100
        if prev_total > 0:
            prev_total_issues = prev_late_starts + prev_early_ends + prev_not_on_job
            prev_attendance_score = 100 - (prev_total_issues / prev_total * 100)
            prev_attendance_score = max(0, min(100, round(prev_attendance_score)))
        
        # Calculate trends
        late_starts_trend = 0
        early_ends_trend = 0
        not_on_job_trend = 0
        attendance_score_trend = 0
        
        if prev_total > 0 and current_total > 0:
            late_starts_trend = round((current_late_starts / current_total * 100) - (prev_late_starts / prev_total * 100))
            early_ends_trend = round((current_early_ends / current_total * 100) - (prev_early_ends / prev_total * 100))
            not_on_job_trend = round((current_not_on_job / current_total * 100) - (prev_not_on_job / prev_total * 100))
        
        attendance_score_trend = attendance_score - prev_attendance_score
        
        # Determine trend directions
        late_starts_direction = 'up' if late_starts_trend > 0 else 'down' if late_starts_trend < 0 else 'none'
        early_ends_direction = 'up' if early_ends_trend > 0 else 'down' if early_ends_trend < 0 else 'none'
        not_on_job_direction = 'up' if not_on_job_trend > 0 else 'down' if not_on_job_trend < 0 else 'none'
        attendance_score_direction = 'up' if attendance_score_trend > 0 else 'down' if attendance_score_trend < 0 else 'none'
        
        response = {
            'job_site': {
                'id': job_site.id,
                'job_number': job_site.job_number,
                'name': job_site.name,
                'location': job_site.location,
                'division': job_site.division,
                'active_drivers': active_drivers,
                'is_active': job_site.is_active
            },
            'metrics': {
                'attendance_score': {
                    'value': attendance_score,
                    'trend': attendance_score_trend,
                    'trend_direction': attendance_score_direction
                },
                'late_starts': {
                    'value': current_late_starts,
                    'trend': late_starts_trend,
                    'trend_direction': late_starts_direction
                },
                'early_ends': {
                    'value': current_early_ends,
                    'trend': early_ends_trend,
                    'trend_direction': early_ends_direction
                },
                'not_on_job': {
                    'value': current_not_on_job,
                    'trend': not_on_job_trend,
                    'trend_direction': not_on_job_direction
                }
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in job_site_metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500


@drivers_bp.route('/api/job-site/<int:job_site_id>/attendance-history')
def job_site_attendance_history(job_site_id):
    """Get attendance history for a specific job site with pagination"""
    try:
        # Get parameters
        days = int(request.args.get('days', 30))
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Get the job site
        job_site = JobSite.query.get_or_404(job_site_id)
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # Query attendance records
        query = AttendanceRecord.query.filter(
            AttendanceRecord.assigned_job_id == job_site.id,
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        ).order_by(desc(AttendanceRecord.date))
        
        # Get total count for pagination
        total_records = query.count()
        total_pages = (total_records + per_page - 1) // per_page  # Ceiling division
        
        # Apply pagination and join with Driver
        records = query.join(Driver).offset((page - 1) * per_page).limit(per_page).all()
        
        # Format records for response
        result_data = []
        for record in records:
            # Determine status label
            status = "On Time"
            if record.not_on_job:
                status = "Wrong Job"
            elif record.late_start:
                status = "Late Start"
            elif record.early_end:
                status = "Early End"
            
            # Format start and end times
            start_time = record.actual_start_time.strftime("%H:%M") if record.actual_start_time else None
            end_time = record.actual_end_time.strftime("%H:%M") if record.actual_end_time else None
            
            result_data.append({
                'id': record.id,
                'date': record.date.strftime("%m/%d/%Y"),
                'driver': record.driver.full_name,
                'asset_id': record.asset_id,
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'notes': record.notes
            })
        
        response = {
            'data': result_data,
            'page': page,
            'per_page': per_page,
            'total': total_records,
            'pages': total_pages
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in job_site_attendance_history: {str(e)}")
        return jsonify({'error': str(e)}), 500


@drivers_bp.route('/api/report/generate', methods=['POST'])
def generate_report():
    """Generate a report based on specified parameters"""
    try:
        # Parse request parameters
        params = request.get_json()
        
        report_type = params.get('report_type', 'daily_driver')
        date_range = params.get('date_range', 'last_7_days')
        division = params.get('division', 'all_divisions')
        format = params.get('format', 'excel')
        include_charts = params.get('include_charts', True)
        include_raw_data = params.get('include_raw_data', True)
        
        # TODO: Implement actual report generation logic
        # For now, return a mock response
        
        # Format current date for filename
        current_date = datetime.now().strftime('%Y%m%d')
        
        # Construct filename based on parameters
        filename = f"driver_report_{report_type}_{division}_{current_date}.{format}"
        
        # In a real implementation, we would:
        # 1. Query the database for the requested data
        # 2. Generate the report in the requested format
        # 3. Save the report to a file
        # 4. Return the URL to the file
        
        response = {
            'success': True,
            'file_url': f"/drivers/reports/{filename}",
            'report_type': report_type,
            'format': format
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in generate_report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@drivers_bp.route('/admin/import')
def import_data():
    """Display data import dashboard"""
    # Get import logs
    import_logs = AttendanceImportLog.query.order_by(desc(AttendanceImportLog.import_date)).limit(10).all()
    
    return render_template('drivers/import.html', import_logs=import_logs)


@drivers_bp.route('/admin/import/process', methods=['POST'])
def process_import():
    """Process data import"""
    # TODO: Implement actual import logic
    
    # Mock response for now
    response = {
        'success': True,
        'message': 'Import completed successfully',
        'records_processed': 0
    }
    
    return jsonify(response)