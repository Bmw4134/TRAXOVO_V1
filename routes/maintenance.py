"""
Maintenance scheduling controller for the fleet management system.

This module handles all routes and business logic for the maintenance scheduling
system, including task creation, updates, and completion.
"""
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload

from db import db
from models.maintenance import (
    MaintenanceTask, MaintenanceHistory, MaintenanceSchedule, MaintenancePart,
    MaintenanceNotification, MaintenanceType, MaintenancePriority, MaintenanceStatus
)
from models import Asset, User

# Create blueprint
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')


@maintenance_bp.route('/')
@login_required
def index():
    """Display the maintenance dashboard."""
    # Get query parameters
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')
    priority_filter = request.args.get('priority', 'all')
    asset_filter = request.args.get('asset', 'all')
    date_range = request.args.get('date_range', '30')
    
    # Base query with eager loading of relationships
    query = MaintenanceTask.query.options(
        joinedload(MaintenanceTask.asset),
        joinedload(MaintenanceTask.technician)
    )
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter(MaintenanceTask.status == status_filter)
        
    if type_filter != 'all':
        query = query.filter(MaintenanceTask.maintenance_type == type_filter)
        
    if priority_filter != 'all':
        query = query.filter(MaintenanceTask.priority == priority_filter)
        
    if asset_filter != 'all':
        query = query.filter(MaintenanceTask.asset_id == int(asset_filter))
    
    # Apply date range filter
    today = date.today()
    if date_range == '7':
        date_limit = today - timedelta(days=7)
        future_limit = today + timedelta(days=7)
    elif date_range == '14':
        date_limit = today - timedelta(days=14)
        future_limit = today + timedelta(days=14)
    elif date_range == '30':
        date_limit = today - timedelta(days=30)
        future_limit = today + timedelta(days=30)
    elif date_range == '90':
        date_limit = today - timedelta(days=90)
        future_limit = today + timedelta(days=90)
    else:
        date_limit = today - timedelta(days=365)
        future_limit = today + timedelta(days=365)
    
    query = query.filter(
        or_(
            and_(
                MaintenanceTask.status != MaintenanceStatus.COMPLETED,
                MaintenanceTask.scheduled_date >= date_limit
            ),
            and_(
                MaintenanceTask.status == MaintenanceStatus.COMPLETED,
                MaintenanceTask.completed_date >= date_limit
            )
        )
    )
    
    # Get tasks in order of scheduled date
    maintenance_tasks = query.order_by(MaintenanceTask.scheduled_date).all()
    
    # Check for overdue tasks and update status if needed
    for task in maintenance_tasks:
        if (task.status != MaintenanceStatus.COMPLETED and 
            task.status != MaintenanceStatus.CANCELLED and
            task.is_overdue):
            
            task.status = MaintenanceStatus.OVERDUE
            db.session.add(task)
    
    # Commit any status changes
    db.session.commit()
    
    # Get all assets for the asset selector
    assets = Asset.query.filter_by(active=True).order_by(Asset.label).all()
    
    # Calculate maintenance stats
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    thirty_days_ahead = today + timedelta(days=30)
    
    # Get count of upcoming maintenance in next 30 days
    upcoming_count = MaintenanceTask.query.filter(
        MaintenanceTask.scheduled_date > today,
        MaintenanceTask.scheduled_date <= thirty_days_ahead,
        MaintenanceTask.status != MaintenanceStatus.COMPLETED,
        MaintenanceTask.status != MaintenanceStatus.CANCELLED
    ).count()
    
    # Get count of completed maintenance in last 30 days
    completed_count = MaintenanceTask.query.filter(
        MaintenanceTask.status == MaintenanceStatus.COMPLETED,
        MaintenanceTask.completed_date >= thirty_days_ago,
        MaintenanceTask.completed_date <= today
    ).count()
    
    # Get count of overdue maintenance
    overdue_count = MaintenanceTask.query.filter(
        MaintenanceTask.status == MaintenanceStatus.OVERDUE
    ).count()
    
    # Get average days to completion for the last 30 days
    avg_days_result = db.session.query(
        func.avg(
            func.julianday(MaintenanceTask.completed_date) - 
            func.julianday(MaintenanceTask.scheduled_date)
        )
    ).filter(
        MaintenanceTask.status == MaintenanceStatus.COMPLETED,
        MaintenanceTask.completed_date >= thirty_days_ago,
        MaintenanceTask.completed_date <= today
    ).scalar()
    
    avg_days = round(avg_days_result) if avg_days_result else 7
    
    # Compile stats
    maintenance_stats = {
        'upcoming': upcoming_count,
        'completed': completed_count,
        'overdue': overdue_count,
        'avg_days': avg_days
    }
    
    return render_template(
        'maintenance.html',
        maintenance_tasks=maintenance_tasks,
        assets=assets,
        maintenance_stats=maintenance_stats,
        status_filter=status_filter,
        type_filter=type_filter,
        priority_filter=priority_filter,
        asset_filter=asset_filter,
        date_range=date_range,
        MaintenanceType=MaintenanceType,
        MaintenancePriority=MaintenancePriority,
        MaintenanceStatus=MaintenanceStatus
    )


@maintenance_bp.route('/add', methods=['POST'])
@login_required
def add_maintenance():
    """Add a new maintenance task."""
    try:
        # Get form data
        asset_id = request.form.get('asset_id')
        maintenance_type = request.form.get('maintenance_type')
        title = request.form.get('title')
        description = request.form.get('description')
        scheduled_date = request.form.get('scheduled_date')
        due_date = request.form.get('due_date') or None
        assigned_to = request.form.get('assigned_to')
        priority = request.form.get('priority', 'medium')
        estimated_cost = request.form.get('estimated_cost') or None
        estimated_hours = request.form.get('estimated_hours') or None
        notes = request.form.get('notes')
        
        # Create maintenance task
        task = MaintenanceTask(
            asset_id=asset_id,
            maintenance_type=maintenance_type,
            title=title,
            description=description,
            scheduled_date=datetime.strptime(scheduled_date, '%Y-%m-%d').date(),
            due_date=datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None,
            assigned_to=assigned_to,
            priority=priority,
            estimated_cost=float(estimated_cost) if estimated_cost else None,
            estimated_hours=float(estimated_hours) if estimated_hours else None,
            notes=notes,
            status=MaintenanceStatus.SCHEDULED
        )
        
        # Save to database
        db.session.add(task)
        db.session.commit()
        
        flash('Maintenance task scheduled successfully.', 'success')
        return redirect(url_for('maintenance.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error scheduling maintenance: {str(e)}', 'danger')
        return redirect(url_for('maintenance.index'))


@maintenance_bp.route('/update', methods=['POST'])
@login_required
def update_maintenance():
    """Update an existing maintenance task."""
    try:
        # Get form data
        task_id = request.form.get('task_id')
        asset_id = request.form.get('asset_id')
        maintenance_type = request.form.get('maintenance_type')
        title = request.form.get('title')
        description = request.form.get('description')
        scheduled_date = request.form.get('scheduled_date')
        due_date = request.form.get('due_date') or None
        assigned_to = request.form.get('assigned_to')
        priority = request.form.get('priority')
        estimated_cost = request.form.get('estimated_cost') or None
        estimated_hours = request.form.get('estimated_hours') or None
        notes = request.form.get('notes')
        status = request.form.get('status')
        completion_notes = request.form.get('completion_notes')
        
        # Find task
        task = MaintenanceTask.query.get(task_id)
        if not task:
            flash('Maintenance task not found.', 'danger')
            return redirect(url_for('maintenance.index'))
        
        # Check if status is changing to completed
        is_newly_completed = status == 'completed' and task.status != MaintenanceStatus.COMPLETED
        
        # Update task attributes
        task.asset_id = asset_id
        task.maintenance_type = maintenance_type
        task.title = title
        task.description = description
        task.scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
        task.due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None
        task.assigned_to = assigned_to
        task.priority = priority
        task.estimated_cost = float(estimated_cost) if estimated_cost else None
        task.estimated_hours = float(estimated_hours) if estimated_hours else None
        task.notes = notes
        task.status = status
        task.completion_notes = completion_notes
        
        # If newly completed, record the completion date
        if is_newly_completed:
            task.completed_date = date.today()
            
            # Also create a maintenance history record
            history = MaintenanceHistory(
                asset_id=task.asset_id,
                maintenance_task_id=task.id,
                date=date.today(),
                service_type=task.maintenance_type.value,
                description=task.description,
                performed_by=task.assigned_to,
                cost=task.actual_cost or task.estimated_cost,
                notes=task.completion_notes,
                # These would come from the asset data if available
                odometer=None,
                engine_hours=None
            )
            db.session.add(history)
        
        # Save changes
        db.session.add(task)
        db.session.commit()
        
        flash('Maintenance task updated successfully.', 'success')
        return redirect(url_for('maintenance.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating maintenance task: {str(e)}', 'danger')
        return redirect(url_for('maintenance.index'))


@maintenance_bp.route('/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_maintenance(task_id):
    """Mark a maintenance task as completed."""
    try:
        task = MaintenanceTask.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'})
        
        if task.status == MaintenanceStatus.COMPLETED:
            return jsonify({'success': False, 'message': 'Task is already completed'})
        
        # Update task
        task.status = MaintenanceStatus.COMPLETED
        task.completed_date = date.today()
        
        # Create history record
        history = MaintenanceHistory(
            asset_id=task.asset_id,
            maintenance_task_id=task.id,
            date=date.today(),
            service_type=task.maintenance_type.value,
            description=task.description,
            performed_by=task.assigned_to,
            cost=task.actual_cost or task.estimated_cost,
            notes=task.completion_notes,
            # These would come from the asset data if available
            odometer=None,
            engine_hours=None
        )
        
        db.session.add(task)
        db.session.add(history)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Task marked as completed'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@maintenance_bp.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_maintenance(task_id):
    """Delete a maintenance task."""
    try:
        task = MaintenanceTask.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'})
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@maintenance_bp.route('/task/<int:task_id>')
@login_required
def get_task_details(task_id):
    """Get details for a specific maintenance task."""
    task = MaintenanceTask.query.options(
        joinedload(MaintenanceTask.asset),
        joinedload(MaintenanceTask.parts)
    ).get(task_id)
    
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'})
    
    # Get maintenance history for this asset
    history = MaintenanceHistory.query.filter_by(
        asset_id=task.asset_id
    ).order_by(MaintenanceHistory.date.desc()).limit(5).all()
    
    # Format history records
    history_items = [
        {
            'date': h.date.strftime('%m/%d/%Y'),
            'service_type': h.service_type,
            'description': h.description
        }
        for h in history
    ]
    
    # Format parts
    parts = [
        {
            'name': p.part_name,
            'part_number': p.part_number,
            'quantity': p.quantity,
            'unit_cost': p.unit_cost,
            'total_cost': p.total_cost
        }
        for p in task.parts
    ]
    
    # Convert task to dictionary
    task_data = {
        'id': task.id,
        'asset': {
            'id': task.asset.id,
            'label': task.asset.label,
            'identifier': task.asset.asset_identifier,
            'image_url': task.asset.image_url if hasattr(task.asset, 'image_url') else None
        },
        'title': task.title,
        'description': task.description,
        'type': task.maintenance_type.value,
        'priority': task.priority.value,
        'status': task.status.value,
        'scheduled_date': task.scheduled_date.strftime('%m/%d/%Y'),
        'due_date': task.due_date.strftime('%m/%d/%Y') if task.due_date else None,
        'completed_date': task.completed_date.strftime('%m/%d/%Y') if task.completed_date else None,
        'assigned_to': task.assigned_to,
        'estimated_cost': task.estimated_cost,
        'actual_cost': task.actual_cost,
        'estimated_hours': task.estimated_hours,
        'actual_hours': task.actual_hours,
        'notes': task.notes,
        'completion_notes': task.completion_notes,
        'parts': parts,
        'history': history_items
    }
    
    return jsonify({'success': True, 'task': task_data})


@maintenance_bp.route('/schedules')
@login_required
def maintenance_schedules():
    """Display all maintenance schedules."""
    schedules = MaintenanceSchedule.query.options(
        joinedload(MaintenanceSchedule.asset)
    ).order_by(MaintenanceSchedule.next_due).all()
    
    assets = Asset.query.filter_by(active=True).order_by(Asset.label).all()
    
    return render_template(
        'maintenance_schedules.html',
        schedules=schedules,
        assets=assets,
        MaintenanceType=MaintenanceType
    )


@maintenance_bp.route('/schedule/add', methods=['POST'])
@login_required
def add_schedule():
    """Add a new maintenance schedule."""
    try:
        # Get form data
        asset_id = request.form.get('asset_id')
        title = request.form.get('title')
        description = request.form.get('description')
        maintenance_type = request.form.get('maintenance_type')
        frequency_type = request.form.get('frequency_type')
        frequency_value = request.form.get('frequency_value')
        last_performed = request.form.get('last_performed') or None
        estimated_cost = request.form.get('estimated_cost') or None
        estimated_hours = request.form.get('estimated_hours') or None
        notes = request.form.get('notes')
        
        # Create schedule
        schedule = MaintenanceSchedule(
            asset_id=asset_id,
            title=title,
            description=description,
            maintenance_type=maintenance_type,
            frequency_type=frequency_type,
            frequency_value=int(frequency_value),
            last_performed=datetime.strptime(last_performed, '%Y-%m-%d').date() if last_performed else None,
            estimated_cost=float(estimated_cost) if estimated_cost else None,
            estimated_hours=float(estimated_hours) if estimated_hours else None,
            notes=notes,
            is_active=True
        )
        
        # Calculate next due date
        if schedule.last_performed:
            schedule.next_due = schedule.calculate_next_due()
        
        # Save to database
        db.session.add(schedule)
        db.session.commit()
        
        flash('Maintenance schedule created successfully.', 'success')
        return redirect(url_for('maintenance.maintenance_schedules'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating maintenance schedule: {str(e)}', 'danger')
        return redirect(url_for('maintenance.maintenance_schedules'))


@maintenance_bp.route('/schedule/update', methods=['POST'])
@login_required
def update_schedule():
    """Update an existing maintenance schedule."""
    try:
        # Get form data
        schedule_id = request.form.get('schedule_id')
        asset_id = request.form.get('asset_id')
        title = request.form.get('title')
        description = request.form.get('description')
        maintenance_type = request.form.get('maintenance_type')
        frequency_type = request.form.get('frequency_type')
        frequency_value = request.form.get('frequency_value')
        last_performed = request.form.get('last_performed') or None
        estimated_cost = request.form.get('estimated_cost') or None
        estimated_hours = request.form.get('estimated_hours') or None
        notes = request.form.get('notes')
        is_active = request.form.get('is_active') == 'on'
        
        # Find schedule
        schedule = MaintenanceSchedule.query.get(schedule_id)
        if not schedule:
            flash('Maintenance schedule not found.', 'danger')
            return redirect(url_for('maintenance.maintenance_schedules'))
        
        # Check if last_performed date changed
        last_performed_changed = False
        if last_performed:
            new_last_performed = datetime.strptime(last_performed, '%Y-%m-%d').date()
            if schedule.last_performed != new_last_performed:
                last_performed_changed = True
                schedule.last_performed = new_last_performed
        
        # Update schedule attributes
        schedule.asset_id = asset_id
        schedule.title = title
        schedule.description = description
        schedule.maintenance_type = maintenance_type
        schedule.frequency_type = frequency_type
        schedule.frequency_value = int(frequency_value)
        schedule.estimated_cost = float(estimated_cost) if estimated_cost else None
        schedule.estimated_hours = float(estimated_hours) if estimated_hours else None
        schedule.notes = notes
        schedule.is_active = is_active
        
        # Recalculate next due date if needed
        if last_performed_changed or not schedule.next_due:
            schedule.next_due = schedule.calculate_next_due()
        
        # Save changes
        db.session.add(schedule)
        db.session.commit()
        
        flash('Maintenance schedule updated successfully.', 'success')
        return redirect(url_for('maintenance.maintenance_schedules'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating maintenance schedule: {str(e)}', 'danger')
        return redirect(url_for('maintenance.maintenance_schedules'))


@maintenance_bp.route('/schedule/generate/<int:schedule_id>', methods=['POST'])
@login_required
def generate_task_from_schedule(schedule_id):
    """Generate a maintenance task from a schedule."""
    try:
        schedule = MaintenanceSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({'success': False, 'message': 'Schedule not found'})
        
        # Create new task
        task = MaintenanceTask(
            asset_id=schedule.asset_id,
            title=schedule.title,
            description=schedule.description,
            maintenance_type=schedule.maintenance_type,
            priority=MaintenancePriority.MEDIUM,
            status=MaintenanceStatus.SCHEDULED,
            scheduled_date=schedule.next_due or date.today(),
            due_date=(schedule.next_due + timedelta(days=7)) if schedule.next_due else (date.today() + timedelta(days=7)),
            estimated_cost=schedule.estimated_cost,
            estimated_hours=schedule.estimated_hours,
            notes=schedule.notes + "\n\nGenerated from maintenance schedule."
        )
        
        db.session.add(task)
        
        # Update the schedule's next due date
        if schedule.frequency_type in ['days', 'weeks', 'months']:
            # Set last_performed to now
            schedule.last_performed = date.today()
            # Calculate next due date
            schedule.next_due = schedule.calculate_next_due()
            db.session.add(schedule)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Task generated successfully',
            'task_id': task.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@maintenance_bp.route('/reports')
@login_required
def maintenance_reports():
    """Display maintenance reports and analytics."""
    return render_template('maintenance_reports.html')


@maintenance_bp.route('/parts/<int:task_id>')
@login_required
def task_parts(task_id):
    """Display parts for a specific maintenance task."""
    task = MaintenanceTask.query.get(task_id)
    if not task:
        flash('Maintenance task not found.', 'danger')
        return redirect(url_for('maintenance.index'))
    
    parts = MaintenancePart.query.filter_by(maintenance_task_id=task_id).all()
    
    return render_template(
        'maintenance_parts.html',
        task=task,
        parts=parts
    )


@maintenance_bp.route('/part/add', methods=['POST'])
@login_required
def add_part():
    """Add a part to a maintenance task."""
    try:
        # Get form data
        task_id = request.form.get('task_id')
        part_name = request.form.get('part_name')
        part_number = request.form.get('part_number')
        quantity = request.form.get('quantity')
        unit_cost = request.form.get('unit_cost') or None
        vendor = request.form.get('vendor')
        notes = request.form.get('notes')
        
        # Create part
        part = MaintenancePart(
            maintenance_task_id=task_id,
            part_name=part_name,
            part_number=part_number,
            quantity=int(quantity),
            unit_cost=float(unit_cost) if unit_cost else None,
            vendor=vendor,
            notes=notes
        )
        
        # Save to database
        db.session.add(part)
        db.session.commit()
        
        flash('Part added successfully.', 'success')
        return redirect(url_for('maintenance.task_parts', task_id=task_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding part: {str(e)}', 'danger')
        return redirect(url_for('maintenance.index'))


def register_maintenance_blueprint(app):
    """Register the maintenance blueprint with the app."""
    app.register_blueprint(maintenance_bp)
    print("Registered maintenance blueprint")
    return app