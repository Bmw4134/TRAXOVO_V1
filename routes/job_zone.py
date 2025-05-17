"""
Job Zone Routes for TRAXORA

This module contains routes for managing job zones and working hours.
"""
import json
from datetime import datetime, time
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.exceptions import NotFound
from app import db
from models.job_zone import JobZone, JobZoneWorkingHours, JobZoneActivity

# Create blueprint
job_zone_bp = Blueprint('job_zone', __name__, url_prefix='/job_zone')

@job_zone_bp.route('/')
@login_required
def index():
    """Display job zone management dashboard"""
    job_zones = JobZone.query.filter_by(active=True).all()
    
    # Get job sites for creating new zones
    from models import JobSite
    job_sites = JobSite.query.filter_by(active=True).all()
    
    return render_template(
        'job_zone/index.html',
        job_zones=job_zones,
        job_sites=job_sites
    )

@job_zone_bp.route('/create', methods=['POST'])
@login_required
def create_job_zone():
    """Create a new job zone"""
    try:
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description', '')
        job_site_id = request.form.get('job_site_id', type=int)
        
        # Get geofence coordinates
        latitude_min = request.form.get('latitude_min', type=float)
        latitude_max = request.form.get('latitude_max', type=float)
        longitude_min = request.form.get('longitude_min', type=float)
        longitude_max = request.form.get('longitude_max', type=float)
        
        # Create job zone
        job_zone = JobZone(
            name=name,
            description=description,
            job_site_id=job_site_id,
            latitude_min=latitude_min,
            latitude_max=latitude_max,
            longitude_min=longitude_min,
            longitude_max=longitude_max,
            zone_type=request.form.get('zone_type', 'work'),
            priority=request.form.get('priority', type=int, default=1)
        )
        
        db.session.add(job_zone)
        db.session.commit()
        
        # Add default working hours (Mon-Fri, 8am-5pm)
        for day in range(5):  # 0-4 = Monday-Friday
            hours = JobZoneWorkingHours(
                job_zone_id=job_zone.id,
                day_of_week=day,
                start_time=time(8, 0),
                end_time=time(17, 0),
                lunch_start=time(12, 0),
                lunch_end=time(13, 0),
                is_working_day=True
            )
            db.session.add(hours)
        
        # Weekend (not working days)
        for day in range(5, 7):  # 5-6 = Saturday-Sunday
            hours = JobZoneWorkingHours(
                job_zone_id=job_zone.id,
                day_of_week=day,
                start_time=time(8, 0),
                end_time=time(17, 0),
                is_working_day=False
            )
            db.session.add(hours)
            
        db.session.commit()
        
        flash('Job zone created successfully', 'success')
        return redirect(url_for('job_zone.index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating job zone: {str(e)}', 'danger')
        return redirect(url_for('job_zone.index'))

@job_zone_bp.route('/<int:job_zone_id>')
@login_required
def view_job_zone(job_zone_id):
    """View job zone details"""
    job_zone = JobZone.query.get_or_404(job_zone_id)
    
    # Get working hours for each day
    working_hours = {}
    for day in range(7):  # 0-6 = Monday-Sunday
        hours = JobZoneWorkingHours.query.filter_by(
            job_zone_id=job_zone_id,
            day_of_week=day,
            is_override=False
        ).first()
        
        if hours:
            working_hours[day] = hours
    
    # Get upcoming overrides
    today = datetime.utcnow().date()
    overrides = JobZoneWorkingHours.query.filter(
        JobZoneWorkingHours.job_zone_id == job_zone_id,
        JobZoneWorkingHours.is_override == True,
        JobZoneWorkingHours.date >= today
    ).order_by(JobZoneWorkingHours.date).all()
    
    # Get recent activity
    activities = JobZoneActivity.query.filter_by(
        job_zone_id=job_zone_id
    ).order_by(JobZoneActivity.entry_time.desc()).limit(10).all()
    
    return render_template(
        'job_zone/view.html',
        job_zone=job_zone,
        working_hours=working_hours,
        overrides=overrides,
        activities=activities,
        days_of_week=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    )

@job_zone_bp.route('/<int:job_zone_id>/update', methods=['POST'])
@login_required
def update_job_zone(job_zone_id):
    """Update job zone details"""
    job_zone = JobZone.query.get_or_404(job_zone_id)
    
    try:
        # Update basic details
        job_zone.name = request.form.get('name')
        job_zone.description = request.form.get('description', '')
        job_zone.zone_type = request.form.get('zone_type')
        job_zone.priority = request.form.get('priority', type=int)
        
        # Update geofence coordinates
        job_zone.latitude_min = request.form.get('latitude_min', type=float)
        job_zone.latitude_max = request.form.get('latitude_max', type=float)
        job_zone.longitude_min = request.form.get('longitude_min', type=float)
        job_zone.longitude_max = request.form.get('longitude_max', type=float)
        
        db.session.commit()
        
        flash('Job zone updated successfully', 'success')
        return redirect(url_for('job_zone.view_job_zone', job_zone_id=job_zone_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating job zone: {str(e)}', 'danger')
        return redirect(url_for('job_zone.view_job_zone', job_zone_id=job_zone_id))

@job_zone_bp.route('/<int:job_zone_id>/hours/<int:day>', methods=['POST'])
@login_required
def update_working_hours(job_zone_id, day):
    """Update working hours for a specific day"""
    # Check if job zone exists
    job_zone = JobZone.query.get_or_404(job_zone_id)
    
    # Get working hours for this day
    hours = JobZoneWorkingHours.query.filter_by(
        job_zone_id=job_zone_id,
        day_of_week=day,
        is_override=False
    ).first()
    
    if not hours:
        return jsonify({'error': 'Working hours not found'}), 404
    
    try:
        # Update working hours
        is_working_day = request.form.get('is_working_day') == 'true'
        hours.is_working_day = is_working_day
        
        if is_working_day:
            # Parse time strings
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            lunch_start = request.form.get('lunch_start')
            lunch_end = request.form.get('lunch_end')
            break_start = request.form.get('break_start')
            break_end = request.form.get('break_end')
            
            # Convert to time objects
            if start_time:
                hour, minute = map(int, start_time.split(':'))
                hours.start_time = time(hour, minute)
                
            if end_time:
                hour, minute = map(int, end_time.split(':'))
                hours.end_time = time(hour, minute)
                
            if lunch_start:
                hour, minute = map(int, lunch_start.split(':'))
                hours.lunch_start = time(hour, minute)
            else:
                hours.lunch_start = None
                
            if lunch_end:
                hour, minute = map(int, lunch_end.split(':'))
                hours.lunch_end = time(hour, minute)
            else:
                hours.lunch_end = None
                
            if break_start:
                hour, minute = map(int, break_start.split(':'))
                hours.break_start = time(hour, minute)
            else:
                hours.break_start = None
                
            if break_end:
                hour, minute = map(int, break_end.split(':'))
                hours.break_end = time(hour, minute)
            else:
                hours.break_end = None
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@job_zone_bp.route('/<int:job_zone_id>/override', methods=['POST'])
@login_required
def add_override(job_zone_id):
    """Add a working hours override for a specific date"""
    # Check if job zone exists
    job_zone = JobZone.query.get_or_404(job_zone_id)
    
    try:
        # Parse date
        override_date_str = request.form.get('override_date')
        override_date = datetime.strptime(override_date_str, '%Y-%m-%d').date()
        
        # Check if override already exists
        existing_override = JobZoneWorkingHours.query.filter_by(
            job_zone_id=job_zone_id,
            date=override_date,
            is_override=True
        ).first()
        
        if existing_override:
            return jsonify({'error': 'Override already exists for this date'}), 400
        
        # Create override
        is_working_day = request.form.get('is_working_day') == 'true'
        
        override = JobZoneWorkingHours(
            job_zone_id=job_zone_id,
            date=override_date,
            is_override=True,
            is_working_day=is_working_day
        )
        
        if is_working_day:
            # Parse time strings
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            lunch_start = request.form.get('lunch_start')
            lunch_end = request.form.get('lunch_end')
            
            # Convert to time objects
            if start_time:
                hour, minute = map(int, start_time.split(':'))
                override.start_time = time(hour, minute)
                
            if end_time:
                hour, minute = map(int, end_time.split(':'))
                override.end_time = time(hour, minute)
                
            if lunch_start:
                hour, minute = map(int, lunch_start.split(':'))
                override.lunch_start = time(hour, minute)
                
            if lunch_end:
                hour, minute = map(int, lunch_end.split(':'))
                override.lunch_end = time(hour, minute)
        
        db.session.add(override)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@job_zone_bp.route('/api/activities')
@login_required
def get_activities():
    """Get job zone activities for dashboard"""
    # Get filter parameters
    job_zone_id = request.args.get('job_zone_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    asset_id = request.args.get('asset_id', type=int)
    
    # Build query
    query = JobZoneActivity.query
    
    if job_zone_id:
        query = query.filter_by(job_zone_id=job_zone_id)
        
    if start_date:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(JobZoneActivity.entry_time >= start_datetime)
        
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        # Add a day to include the full end date
        end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
        query = query.filter(JobZoneActivity.entry_time <= end_datetime)
        
    if asset_id:
        query = query.filter_by(asset_id=asset_id)
    
    # Get results
    activities = query.order_by(JobZoneActivity.entry_time.desc()).limit(100).all()
    
    # Format results
    results = []
    for activity in activities:
        # Format times
        entry_time = activity.entry_time.strftime('%Y-%m-%d %H:%M:%S')
        exit_time = activity.exit_time.strftime('%Y-%m-%d %H:%M:%S') if activity.exit_time else None
        
        # Get related objects
        job_zone = activity.job_zone
        asset = activity.asset
        driver = activity.driver
        
        results.append({
            'id': activity.id,
            'job_zone': {
                'id': job_zone.id,
                'name': job_zone.name
            },
            'asset': {
                'id': asset.id,
                'identifier': asset.asset_identifier
            },
            'driver': {
                'id': driver.id if driver else None,
                'name': driver.name if driver else None
            },
            'entry_time': entry_time,
            'exit_time': exit_time,
            'duration_minutes': activity.duration_minutes,
            'is_within_working_hours': activity.is_within_working_hours
        })
    
    return jsonify(results)

@job_zone_bp.route('/report')
@login_required
def report():
    """Display job zone hours report"""
    # Get filter parameters
    start_date = request.args.get('start_date', datetime.utcnow().strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.utcnow().strftime('%Y-%m-%d'))
    job_site_id = request.args.get('job_site_id', type=int)
    
    # Get job sites for filter
    from models import JobSite
    job_sites = JobSite.query.filter_by(active=True).all()
    
    # Build query for job zones
    job_zones_query = JobZone.query.filter_by(active=True)
    
    if job_site_id:
        job_zones_query = job_zones_query.filter_by(job_site_id=job_site_id)
        
    job_zones = job_zones_query.all()
    
    # Convert dates
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
    
    # Get activities
    activities = JobZoneActivity.query.filter(
        JobZoneActivity.job_zone_id.in_([z.id for z in job_zones]),
        JobZoneActivity.entry_time >= start_datetime,
        JobZoneActivity.entry_time <= end_datetime
    ).order_by(JobZoneActivity.entry_time).all()
    
    # Prepare report data
    report_data = {}
    
    for activity in activities:
        # Group by job zone and date
        job_zone_id = activity.job_zone_id
        date_str = activity.entry_time.strftime('%Y-%m-%d')
        
        if job_zone_id not in report_data:
            report_data[job_zone_id] = {
                'name': activity.job_zone.name,
                'job_site': activity.job_zone.job_site.name,
                'dates': {}
            }
            
        if date_str not in report_data[job_zone_id]['dates']:
            report_data[job_zone_id]['dates'][date_str] = {
                'total_minutes': 0,
                'within_hours_minutes': 0,
                'outside_hours_minutes': 0,
                'activities': []
            }
        
        # Add activity
        duration = activity.duration_minutes or 0
        report_data[job_zone_id]['dates'][date_str]['total_minutes'] += duration
        
        if activity.is_within_working_hours:
            report_data[job_zone_id]['dates'][date_str]['within_hours_minutes'] += duration
        else:
            report_data[job_zone_id]['dates'][date_str]['outside_hours_minutes'] += duration
        
        # Add to activities list
        report_data[job_zone_id]['dates'][date_str]['activities'].append({
            'asset': activity.asset.asset_identifier,
            'driver': activity.driver.name if activity.driver else None,
            'entry_time': activity.entry_time.strftime('%H:%M'),
            'exit_time': activity.exit_time.strftime('%H:%M') if activity.exit_time else 'N/A',
            'duration_minutes': duration,
            'is_within_working_hours': activity.is_within_working_hours
        })
    
    return render_template(
        'job_zone/report.html',
        report_data=report_data,
        start_date=start_date,
        end_date=end_date,
        job_sites=job_sites,
        selected_job_site_id=job_site_id
    )