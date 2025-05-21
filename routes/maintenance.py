"""
Maintenance Routes Module

This module provides routes for maintenance scheduling, management, and reporting.
"""

import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc, distinct, and_, or_
import pandas as pd
import json

from models.maintenance import (
    MaintenanceSchedule, MaintenanceRecord, MaintenancePart, 
    MaintenancePartUsage, MaintenanceStatus, MaintenanceType
)
from models.asset import Asset
from app import db
from utils.activity_logger import log_activity
from utils.maintenance_integration import sync_maintenance_data

# Create the blueprint
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')

@maintenance_bp.route('/')
@login_required
def index():
    """Maintenance dashboard page"""
    # Get upcoming maintenance schedules
    upcoming = MaintenanceSchedule.query.filter(
        MaintenanceSchedule.status == MaintenanceStatus.SCHEDULED,
        MaintenanceSchedule.scheduled_date >= datetime.utcnow()
    ).order_by(MaintenanceSchedule.scheduled_date).limit(10).all()
    
    # Get overdue maintenance
    overdue = MaintenanceSchedule.query.filter(
        MaintenanceSchedule.status == MaintenanceStatus.SCHEDULED,
        MaintenanceSchedule.scheduled_date < datetime.utcnow()
    ).order_by(MaintenanceSchedule.scheduled_date).limit(10).all()
    
    # Get in-progress maintenance
    in_progress = MaintenanceSchedule.query.filter(
        MaintenanceSchedule.status == MaintenanceStatus.IN_PROGRESS
    ).order_by(MaintenanceSchedule.scheduled_date).all()
    
    # Get recently completed maintenance
    completed = MaintenanceRecord.query.filter(
        MaintenanceRecord.end_time != None
    ).order_by(desc(MaintenanceRecord.end_time)).limit(10).all()
    
    # Summary statistics
    stats = {
        'total_scheduled': MaintenanceSchedule.query.filter(
            MaintenanceSchedule.status == MaintenanceStatus.SCHEDULED
        ).count(),
        'total_overdue': MaintenanceSchedule.query.filter(
            MaintenanceSchedule.status == MaintenanceStatus.SCHEDULED,
            MaintenanceSchedule.scheduled_date < datetime.utcnow()
        ).count(),
        'total_in_progress': MaintenanceSchedule.query.filter(
            MaintenanceSchedule.status == MaintenanceStatus.IN_PROGRESS
        ).count(),
        'total_completed_this_month': MaintenanceRecord.query.filter(
            MaintenanceRecord.end_time != None,
            MaintenanceRecord.end_time >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        ).count()
    }
    
    return render_template('maintenance/index.html', 
                           upcoming=upcoming, 
                           overdue=overdue,
                           in_progress=in_progress,
                           completed=completed,
                           stats=stats)

@maintenance_bp.route('/schedule')
@login_required
def schedule():
    """View maintenance schedule calendar"""
    # Get all scheduled maintenance for the next 30 days
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)
    
    schedules = MaintenanceSchedule.query.filter(
        MaintenanceSchedule.scheduled_date.between(start_date, end_date)
    ).all()
    
    # Prepare data for the calendar
    calendar_data = []
    for schedule in schedules:
        calendar_data.append({
            'id': schedule.id,
            'title': f"{schedule.asset.name}: {schedule.title}",
            'start': schedule.scheduled_date.isoformat(),
            'end': (schedule.scheduled_date + timedelta(hours=schedule.estimated_duration_hours)).isoformat(),
            'url': url_for('maintenance.view_schedule', schedule_id=schedule.id),
            'color': get_status_color(schedule.status)
        })
    
    return render_template('maintenance/schedule.html', 
                          calendar_data=json.dumps(calendar_data))

@maintenance_bp.route('/schedule/new', methods=['GET', 'POST'])
@login_required
def new_schedule():
    """Create a new maintenance schedule"""
    if request.method == 'POST':
        try:
            # Extract data from form
            asset_id = int(request.form.get('asset_id'))
            title = request.form.get('title')
            description = request.form.get('description', '')
            scheduled_date = datetime.strptime(request.form.get('scheduled_date'), '%Y-%m-%dT%H:%M')
            estimated_duration = float(request.form.get('estimated_duration', 1.0))
            recurrence_interval = int(request.form.get('recurrence_interval', 0))
            maintenance_type = MaintenanceType(request.form.get('maintenance_type'))
            priority = int(request.form.get('priority', 3))
            technician_id = request.form.get('technician_id')
            if not technician_id:
                technician_id = None
            else:
                technician_id = int(technician_id)
            job_site_id = request.form.get('job_site_id')
            if not job_site_id:
                job_site_id = None
            else:
                job_site_id = int(job_site_id)
            estimated_cost = request.form.get('estimated_cost')
            if estimated_cost:
                estimated_cost = float(estimated_cost)
            
            # Create new maintenance schedule
            schedule = MaintenanceSchedule(
                asset_id=asset_id,
                title=title,
                description=description,
                scheduled_date=scheduled_date,
                estimated_duration_hours=estimated_duration,
                recurrence_interval_days=recurrence_interval,
                maintenance_type=maintenance_type,
                priority=priority,
                assigned_technician_id=technician_id,
                job_site_id=job_site_id,
                estimated_cost=estimated_cost,
                created_by_id=current_user.id
            )
            
            db.session.add(schedule)
            db.session.commit()
            
            # Log the activity
            log_activity(
                'maintenance_scheduled',
                current_user.id,
                f"Scheduled maintenance '{title}' for asset #{asset_id}",
                metadata={
                    'asset_id': asset_id,
                    'scheduled_date': scheduled_date.isoformat(),
                    'maintenance_type': maintenance_type.value
                }
            )
            
            flash('Maintenance schedule created successfully', 'success')
            return redirect(url_for('maintenance.view_schedule', schedule_id=schedule.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating maintenance schedule: {str(e)}", 'danger')
    
    # Get assets for dropdown
    assets = Asset.query.order_by(Asset.name).all()
    
    return render_template('maintenance/new_schedule.html', 
                          assets=assets,
                          maintenance_types=[t.value for t in MaintenanceType])

@maintenance_bp.route('/schedule/<int:schedule_id>')
@login_required
def view_schedule(schedule_id):
    """View a maintenance schedule"""
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    
    # Get related maintenance records
    records = MaintenanceRecord.query.filter_by(schedule_id=schedule_id).order_by(desc(MaintenanceRecord.start_time)).all()
    
    return render_template('maintenance/view_schedule.html', 
                          schedule=schedule,
                          records=records)

@maintenance_bp.route('/schedule/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_schedule(schedule_id):
    """Edit a maintenance schedule"""
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    
    if request.method == 'POST':
        try:
            # Update schedule with form data
            schedule.title = request.form.get('title')
            schedule.description = request.form.get('description', '')
            schedule.scheduled_date = datetime.strptime(request.form.get('scheduled_date'), '%Y-%m-%dT%H:%M')
            schedule.estimated_duration_hours = float(request.form.get('estimated_duration', 1.0))
            schedule.recurrence_interval_days = int(request.form.get('recurrence_interval', 0))
            schedule.maintenance_type = MaintenanceType(request.form.get('maintenance_type'))
            schedule.priority = int(request.form.get('priority', 3))
            
            technician_id = request.form.get('technician_id')
            if not technician_id:
                schedule.assigned_technician_id = None
            else:
                schedule.assigned_technician_id = int(technician_id)
                
            job_site_id = request.form.get('job_site_id')
            if not job_site_id:
                schedule.job_site_id = None
            else:
                schedule.job_site_id = int(job_site_id)
                
            estimated_cost = request.form.get('estimated_cost')
            if estimated_cost:
                schedule.estimated_cost = float(estimated_cost)
            else:
                schedule.estimated_cost = None
                
            status = request.form.get('status')
            if status:
                schedule.status = MaintenanceStatus(status)
            
            db.session.commit()
            
            # Log the activity
            log_activity(
                'maintenance_updated',
                current_user.id,
                f"Updated maintenance '{schedule.title}' for asset #{schedule.asset_id}",
                metadata={
                    'asset_id': schedule.asset_id,
                    'scheduled_date': schedule.scheduled_date.isoformat(),
                    'maintenance_type': schedule.maintenance_type.value,
                    'status': schedule.status.value
                }
            )
            
            flash('Maintenance schedule updated successfully', 'success')
            return redirect(url_for('maintenance.view_schedule', schedule_id=schedule.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating maintenance schedule: {str(e)}", 'danger')
    
    # Get assets for dropdown
    assets = Asset.query.order_by(Asset.name).all()
    
    return render_template('maintenance/edit_schedule.html', 
                          schedule=schedule,
                          assets=assets,
                          maintenance_types=[t.value for t in MaintenanceType],
                          status_types=[s.value for s in MaintenanceStatus])

@maintenance_bp.route('/schedule/<int:schedule_id>/delete', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    """Delete a maintenance schedule"""
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    
    try:
        # Save info for activity log
        asset_id = schedule.asset_id
        title = schedule.title
        
        db.session.delete(schedule)
        db.session.commit()
        
        # Log the activity
        log_activity(
            'maintenance_deleted',
            current_user.id,
            f"Deleted maintenance '{title}' for asset #{asset_id}",
            metadata={
                'asset_id': asset_id
            }
        )
        
        flash('Maintenance schedule deleted successfully', 'success')
        return redirect(url_for('maintenance.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting maintenance schedule: {str(e)}", 'danger')
        return redirect(url_for('maintenance.view_schedule', schedule_id=schedule_id))

@maintenance_bp.route('/record/new', methods=['GET', 'POST'])
@login_required
def new_record():
    """Create a new maintenance record"""
    schedule_id = request.args.get('schedule_id')
    schedule = None
    if schedule_id:
        schedule = MaintenanceSchedule.query.get(schedule_id)
    
    if request.method == 'POST':
        try:
            # Extract data from form
            asset_id = int(request.form.get('asset_id'))
            title = request.form.get('title')
            description = request.form.get('description', '')
            maintenance_type = MaintenanceType(request.form.get('maintenance_type'))
            start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
            
            end_time_str = request.form.get('end_time')
            end_time = None
            if end_time_str:
                end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
                
            actual_duration = request.form.get('actual_duration')
            if actual_duration:
                actual_duration = float(actual_duration)
            
            actual_cost = request.form.get('actual_cost')
            if actual_cost:
                actual_cost = float(actual_cost)
                
            parts_used = request.form.get('parts_used', '')
            
            technician_id = request.form.get('technician_id')
            if not technician_id:
                technician_id = None
            else:
                technician_id = int(technician_id)
                
            job_site_id = request.form.get('job_site_id')
            if not job_site_id:
                job_site_id = None
            else:
                job_site_id = int(job_site_id)
                
            notes = request.form.get('notes', '')
            findings = request.form.get('findings', '')
            follow_up_required = 'follow_up_required' in request.form
            
            schedule_id = request.form.get('schedule_id')
            if not schedule_id:
                schedule_id = None
            else:
                schedule_id = int(schedule_id)
                # Update the related schedule status if this record completes it
                if end_time and schedule_id:
                    schedule = MaintenanceSchedule.query.get(schedule_id)
                    if schedule:
                        schedule.status = MaintenanceStatus.COMPLETED
            
            # Create new maintenance record
            record = MaintenanceRecord(
                schedule_id=schedule_id,
                asset_id=asset_id,
                title=title,
                description=description,
                maintenance_type=maintenance_type,
                start_time=start_time,
                end_time=end_time,
                actual_duration_hours=actual_duration,
                actual_cost=actual_cost,
                parts_used=parts_used,
                technician_id=technician_id,
                job_site_id=job_site_id,
                notes=notes,
                findings=findings,
                follow_up_required=follow_up_required,
                submitted_by_id=current_user.id
            )
            
            db.session.add(record)
            db.session.commit()
            
            # Log the activity
            log_activity(
                'maintenance_recorded',
                current_user.id,
                f"Recorded maintenance '{title}' for asset #{asset_id}",
                metadata={
                    'asset_id': asset_id,
                    'maintenance_type': maintenance_type.value,
                    'completed': end_time is not None
                }
            )
            
            flash('Maintenance record created successfully', 'success')
            if schedule_id:
                return redirect(url_for('maintenance.view_schedule', schedule_id=schedule_id))
            else:
                return redirect(url_for('maintenance.view_record', record_id=record.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating maintenance record: {str(e)}", 'danger')
    
    # Get assets for dropdown
    assets = Asset.query.order_by(Asset.name).all()
    
    return render_template('maintenance/new_record.html', 
                          assets=assets,
                          schedule=schedule,
                          maintenance_types=[t.value for t in MaintenanceType])

@maintenance_bp.route('/record/<int:record_id>')
@login_required
def view_record(record_id):
    """View a maintenance record"""
    record = MaintenanceRecord.query.get_or_404(record_id)
    
    return render_template('maintenance/view_record.html', record=record)

@maintenance_bp.route('/parts')
@login_required
def parts_inventory():
    """View parts inventory"""
    parts = MaintenancePart.query.order_by(MaintenancePart.name).all()
    
    # Calculate inventory statistics
    stats = {
        'total_parts': len(parts),
        'total_value': sum(part.quantity_on_hand * part.unit_cost for part in parts if part.unit_cost),
        'low_stock_count': sum(1 for part in parts if part.quantity_on_hand <= part.reorder_level)
    }
    
    return render_template('maintenance/parts_inventory.html', 
                          parts=parts,
                          stats=stats)

@maintenance_bp.route('/reports')
@login_required
def reports():
    """Maintenance reports dashboard"""
    # Calculate report statistics
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    # Maintenance completion stats
    current_month_completed = MaintenanceRecord.query.filter(
        MaintenanceRecord.end_time != None,
        MaintenanceRecord.end_time >= current_month_start
    ).count()
    
    prev_month_completed = MaintenanceRecord.query.filter(
        MaintenanceRecord.end_time != None,
        MaintenanceRecord.end_time >= prev_month_start,
        MaintenanceRecord.end_time < current_month_start
    ).count()
    
    # Calculate maintenance costs
    current_month_costs = db.session.query(func.sum(MaintenanceRecord.actual_cost)).filter(
        MaintenanceRecord.end_time != None,
        MaintenanceRecord.end_time >= current_month_start
    ).scalar() or 0
    
    prev_month_costs = db.session.query(func.sum(MaintenanceRecord.actual_cost)).filter(
        MaintenanceRecord.end_time != None,
        MaintenanceRecord.end_time >= prev_month_start,
        MaintenanceRecord.end_time < current_month_start
    ).scalar() or 0
    
    # Get assets with most maintenance
    top_assets = db.session.query(
        Asset.id, Asset.name, Asset.asset_id, 
        func.count(MaintenanceRecord.id).label('maintenance_count')
    ).join(MaintenanceRecord).group_by(Asset.id).order_by(
        desc('maintenance_count')
    ).limit(10).all()
    
    stats = {
        'current_month_completed': current_month_completed,
        'prev_month_completed': prev_month_completed,
        'percent_change_completed': calculate_percent_change(prev_month_completed, current_month_completed),
        'current_month_costs': current_month_costs,
        'prev_month_costs': prev_month_costs,
        'percent_change_costs': calculate_percent_change(prev_month_costs, current_month_costs),
        'top_assets': top_assets
    }
    
    return render_template('maintenance/reports.html', stats=stats)

@maintenance_bp.route('/api/sync', methods=['POST'])
@login_required
def sync_external_data():
    """Sync maintenance data with external systems"""
    try:
        result = sync_maintenance_data()
        
        log_activity(
            'maintenance_sync',
            current_user.id,
            f"Synced maintenance data with external system",
            metadata=result
        )
        
        return jsonify({
            'success': True,
            'message': f"Successfully synced {result['imported']} records",
            'details': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error syncing maintenance data: {str(e)}"
        }), 500

@maintenance_bp.route('/export', methods=['POST'])
@login_required
def export_maintenance_data():
    """Export maintenance data to Excel"""
    report_type = request.form.get('report_type')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        # End of current month
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)
    
    # Create Excel export based on report type
    if report_type == 'schedules':
        data = export_schedules(start_date, end_date)
        filename = f"maintenance_schedules_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
    elif report_type == 'completed':
        data = export_completed_maintenance(start_date, end_date)
        filename = f"completed_maintenance_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
    elif report_type == 'costs':
        data = export_maintenance_costs(start_date, end_date)
        filename = f"maintenance_costs_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
    else:
        return jsonify({
            'success': False,
            'message': f"Unknown report type: {report_type}"
        }), 400
    
    # Save the Excel file
    export_dir = os.path.join(current_app.root_path, 'exports')
    os.makedirs(export_dir, exist_ok=True)
    export_path = os.path.join(export_dir, filename)
    data.to_excel(export_path, index=False)
    
    # Log the activity
    log_activity(
        'maintenance_export',
        current_user.id,
        f"Exported maintenance {report_type} report",
        metadata={
            'report_type': report_type,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'filename': filename
        }
    )
    
    return jsonify({
        'success': True,
        'message': 'Export created successfully',
        'download_url': url_for('download_export', export_path=filename)
    })

# Helper functions
def get_status_color(status):
    """Get a color for the calendar event based on status"""
    color_map = {
        MaintenanceStatus.SCHEDULED: '#3498db',  # Blue
        MaintenanceStatus.IN_PROGRESS: '#f39c12',  # Orange
        MaintenanceStatus.COMPLETED: '#2ecc71',  # Green
        MaintenanceStatus.OVERDUE: '#e74c3c',  # Red
        MaintenanceStatus.CANCELED: '#95a5a6',  # Gray
    }
    return color_map.get(status, '#3498db')

def calculate_percent_change(old_value, new_value):
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 100 if new_value > 0 else 0
    return round(((new_value - old_value) / old_value) * 100, 2)

def export_schedules(start_date, end_date):
    """Export maintenance schedules to DataFrame"""
    schedules = MaintenanceSchedule.query.filter(
        MaintenanceSchedule.scheduled_date.between(start_date, end_date)
    ).all()
    
    data = []
    for schedule in schedules:
        data.append({
            'ID': schedule.id,
            'Asset ID': schedule.asset.asset_id if schedule.asset else '',
            'Asset Name': schedule.asset.name if schedule.asset else '',
            'Title': schedule.title,
            'Description': schedule.description,
            'Scheduled Date': schedule.scheduled_date,
            'Duration (Hours)': schedule.estimated_duration_hours,
            'Maintenance Type': schedule.maintenance_type.value if schedule.maintenance_type else '',
            'Priority': schedule.priority,
            'Status': schedule.status.value if schedule.status else '',
            'Assigned Technician': schedule.technician.name if schedule.technician else '',
            'Job Site': schedule.job_site.name if schedule.job_site else '',
            'Estimated Cost': schedule.estimated_cost,
            'Created By': schedule.created_by.name if schedule.created_by else '',
            'Created At': schedule.created_at,
            'Updated At': schedule.updated_at,
        })
    
    return pd.DataFrame(data)

def export_completed_maintenance(start_date, end_date):
    """Export completed maintenance records to DataFrame"""
    records = MaintenanceRecord.query.filter(
        MaintenanceRecord.end_time != None,
        MaintenanceRecord.end_time.between(start_date, end_date)
    ).all()
    
    data = []
    for record in records:
        data.append({
            'ID': record.id,
            'Asset ID': record.asset.asset_id if record.asset else '',
            'Asset Name': record.asset.name if record.asset else '',
            'Title': record.title,
            'Description': record.description,
            'Maintenance Type': record.maintenance_type.value if record.maintenance_type else '',
            'Start Time': record.start_time,
            'End Time': record.end_time,
            'Duration (Hours)': record.actual_duration_hours,
            'Actual Cost': record.actual_cost,
            'Parts Used': record.parts_used,
            'Technician': record.technician.name if record.technician else '',
            'Job Site': record.job_site.name if record.job_site else '',
            'Notes': record.notes,
            'Findings': record.findings,
            'Follow-up Required': record.follow_up_required,
            'Submitted By': record.submitted_by.name if record.submitted_by else '',
            'Submitted At': record.created_at,
        })
    
    return pd.DataFrame(data)

def export_maintenance_costs(start_date, end_date):
    """Export maintenance costs by asset to DataFrame"""
    # Get all completed maintenance in the date range
    records = MaintenanceRecord.query.filter(
        MaintenanceRecord.end_time != None,
        MaintenanceRecord.end_time.between(start_date, end_date)
    ).all()
    
    # Group by asset and calculate costs
    asset_costs = {}
    for record in records:
        asset_id = record.asset_id
        asset_name = record.asset.name if record.asset else f"Asset ID: {asset_id}"
        asset_key = f"{asset_name} ({record.asset.asset_id})" if record.asset else f"Asset ID: {asset_id}"
        
        if asset_key not in asset_costs:
            asset_costs[asset_key] = {
                'asset_id': record.asset.asset_id if record.asset else '',
                'asset_name': asset_name,
                'total_cost': 0,
                'maintenance_count': 0,
                'maintenance_hours': 0,
                'types': {}
            }
        
        # Add cost if available
        if record.actual_cost:
            asset_costs[asset_key]['total_cost'] += record.actual_cost
        
        # Increment count
        asset_costs[asset_key]['maintenance_count'] += 1
        
        # Add maintenance hours if available
        if record.actual_duration_hours:
            asset_costs[asset_key]['maintenance_hours'] += record.actual_duration_hours
        
        # Track by maintenance type
        maint_type = record.maintenance_type.value if record.maintenance_type else 'unknown'
        if maint_type not in asset_costs[asset_key]['types']:
            asset_costs[asset_key]['types'][maint_type] = {
                'count': 0,
                'cost': 0
            }
        
        asset_costs[asset_key]['types'][maint_type]['count'] += 1
        if record.actual_cost:
            asset_costs[asset_key]['types'][maint_type]['cost'] += record.actual_cost
    
    # Flatten data for DataFrame
    data = []
    for asset_key, asset_data in asset_costs.items():
        row = {
            'Asset ID': asset_data['asset_id'],
            'Asset Name': asset_data['asset_name'],
            'Total Cost': asset_data['total_cost'],
            'Maintenance Count': asset_data['maintenance_count'],
            'Maintenance Hours': asset_data['maintenance_hours'],
            'Cost Per Maintenance': asset_data['total_cost'] / asset_data['maintenance_count'] if asset_data['maintenance_count'] > 0 else 0,
            'Cost Per Hour': asset_data['total_cost'] / asset_data['maintenance_hours'] if asset_data['maintenance_hours'] > 0 else 0,
        }
        
        # Add maintenance type breakdowns
        for maint_type, type_data in asset_data['types'].items():
            row[f"{maint_type.capitalize()} Count"] = type_data['count']
            row[f"{maint_type.capitalize()} Cost"] = type_data['cost']
        
        data.append(row)
    
    return pd.DataFrame(data)
@maintenance_bp.route('/')
def index():
    """Handler for /"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/index.html')
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return render_template('error.html', error=str(e)), 500

@maintenance_bp.route('/schedule')
def schedule():
    """Handler for /schedule"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/schedule.html')
    except Exception as e:
        logger.error(f"Error in schedule: {e}")
        return render_template('error.html', error=str(e)), 500

@maintenance_bp.route('/schedule/new')
def schedule_new():
    """Handler for /schedule/new"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/schedule_new.html')
    except Exception as e:
        logger.error(f"Error in schedule_new: {e}")
        return render_template('error.html', error=str(e)), 500

@maintenance_bp.route('/schedule/<int:schedule_id>')
def schedule_<int:schedule_id>():
    """Handler for /schedule/<int:schedule_id>"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/schedule_<int:schedule_id>.html')
    except Exception as e:
        logger.error(f"Error in schedule_<int:schedule_id>: {e}")
        return render_template('error.html', error=str(e)), 500

@maintenance_bp.route('/schedule/<int:schedule_id>/edit')
def schedule_<int:schedule_id>_edit():
    """Handler for /schedule/<int:schedule_id>/edit"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/schedule_<int:schedule_id>_edit.html')
    except Exception as e:
        logger.error(f"Error in schedule_<int:schedule_id>_edit: {e}")
        return render_template('error.html', error=str(e)), 500

@maintenance_bp.route('/schedule/<int:schedule_id>/delete')
def schedule_<int:schedule_id>_delete():
    """Handler for /schedule/<int:schedule_id>/delete"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/schedule_<int:schedule_id>_delete.html')
    except Exception as e:
        logger.error(f"Error in schedule_<int:schedule_id>_delete: {e}")
        return render_template('error.html', error=str(e)), 500

@maintenance_bp.route('/record/new')
def record_new():
    """Handler for /record/new"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/record_new.html')
    except Exception as e:
        logger.error(f"Error in record_new: {e}")
        return render_template('error.html', error=str(e)), 500

@maintenance_bp.route('/record/<int:record_id>')
def record_<int:record_id>():
    """Handler for /record/<int:record_id>"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/record_<int:record_id>.html')
    except Exception as e:
        logger.error(f"Error in record_<int:record_id>: {e}")
        return render_template('error.html', error=str(e)), 500

@maintenance_bp.route('/parts')
def parts():
    """Handler for /parts"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/parts.html')
    except Exception as e:
        logger.error(f"Error in parts: {e}")
        return render_template('error.html', error=str(e)), 500

@maintenance_bp.route('/reports')
def reports():
    """Handler for /reports"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/reports.html')
    except Exception as e:
        logger.error(f"Error in reports: {e}")
        return render_template('error.html', error=str(e)), 500

@maintenance_bp.route('/api/sync')
def api_sync():
    """Handler for /api/sync"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/api_sync.html')
    except Exception as e:
        logger.error(f"Error in api_sync: {e}")
        return render_template('error.html', error=str(e)), 500

@maintenance_bp.route('/export')
def export():
    """Handler for /export"""
    try:
        # Add your route handler logic here
        return render_template('maintenance/export.html')
    except Exception as e:
        logger.error(f"Error in export: {e}")
        return render_template('error.html', error=str(e)), 500
