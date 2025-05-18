"""
Maintenance Module for TRAXORA

This module handles maintenance scheduling, tracking, and reporting
for fleet assets across the TRAXORA system.
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

from utils.activity_logger import log_activity, log_navigation

# Create blueprint
maintenance_module_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')

# Sample maintenance data - in a real app, this would come from the database
SAMPLE_MAINTENANCE_SCHEDULES = [
    {
        'id': 1,
        'asset_id': 'T-101',
        'asset_name': 'CAT Excavator 349F',
        'task': 'Oil Change',
        'frequency': 'Every 250 hours',
        'last_completed': datetime.now() - timedelta(days=45),
        'next_due': datetime.now() + timedelta(days=15),
        'status': 'Scheduled',
        'tech_assigned': 'John Doe',
        'priority': 'High'
    },
    {
        'id': 2,
        'asset_id': 'T-102',
        'asset_name': 'Dozer D6',
        'task': 'Hydraulic System Inspection',
        'frequency': 'Monthly',
        'last_completed': datetime.now() - timedelta(days=22),
        'next_due': datetime.now() + timedelta(days=8),
        'status': 'Scheduled',
        'tech_assigned': 'Sarah Johnson',
        'priority': 'Medium'
    },
    {
        'id': 3,
        'asset_id': 'T-103',
        'asset_name': 'Backhoe 420F',
        'task': 'Brake System Service',
        'frequency': 'Every 500 hours',
        'last_completed': datetime.now() - timedelta(days=60),
        'next_due': datetime.now() - timedelta(days=2),
        'status': 'Overdue',
        'tech_assigned': 'Unassigned',
        'priority': 'Critical'
    },
    {
        'id': 4,
        'asset_id': 'T-104',
        'asset_name': 'Wheel Loader 966M',
        'task': 'Complete Inspection',
        'frequency': 'Quarterly',
        'last_completed': datetime.now() - timedelta(days=85),
        'next_due': datetime.now() + timedelta(days=5),
        'status': 'Scheduled',
        'tech_assigned': 'Mike Wilson',
        'priority': 'High'
    },
    {
        'id': 5,
        'asset_id': 'T-105',
        'asset_name': 'Skid Steer 242D',
        'task': 'Filter Replacement',
        'frequency': 'Every 200 hours',
        'last_completed': datetime.now() - timedelta(days=30),
        'next_due': datetime.now() + timedelta(days=30),
        'status': 'Scheduled',
        'tech_assigned': 'Tom Johnson',
        'priority': 'Medium'
    }
]

SAMPLE_TECHNICIANS = [
    {'id': 1, 'name': 'John Doe', 'role': 'Lead Technician', 'available': True},
    {'id': 2, 'name': 'Sarah Johnson', 'role': 'Maintenance Tech', 'available': True},
    {'id': 3, 'name': 'Mike Wilson', 'role': 'Maintenance Tech', 'available': True},
    {'id': 4, 'name': 'Tom Johnson', 'role': 'Junior Technician', 'available': False},
    {'id': 5, 'name': 'Emily Davis', 'role': 'Senior Technician', 'available': True}
]

SAMPLE_MAINTENANCE_TASKS = [
    'Oil Change',
    'Hydraulic System Inspection',
    'Brake System Service',
    'Complete Inspection',
    'Filter Replacement',
    'Transmission Service',
    'Engine Tune-up',
    'Tire Rotation',
    'Fluid Check and Top-off',
    'Electrical System Check',
    'Cooling System Service',
    'Track Tension Adjustment',
    'Undercarriage Inspection',
    'Air Filter Replacement',
    'Fuel System Service'
]

SAMPLE_MAINTENANCE_RECORDS = [
    {
        'id': 1,
        'asset_id': 'T-101',
        'task': 'Oil Change',
        'date_completed': datetime.now() - timedelta(days=45),
        'technician': 'John Doe',
        'notes': 'Replaced with synthetic oil as per manufacturer recommendation.',
        'parts_used': 'Oil filter, 10W-30 synthetic oil (8 qts)',
        'labor_hours': 1.5,
        'cost': 275.50
    },
    {
        'id': 2,
        'asset_id': 'T-102',
        'task': 'Hydraulic System Inspection',
        'date_completed': datetime.now() - timedelta(days=22),
        'technician': 'Sarah Johnson',
        'notes': 'All systems functioning properly. Replaced worn hydraulic hose.',
        'parts_used': 'Hydraulic hose (1)',
        'labor_hours': 2.0,
        'cost': 320.75
    },
    {
        'id': 3,
        'asset_id': 'T-103',
        'task': 'Complete Inspection',
        'date_completed': datetime.now() - timedelta(days=60),
        'technician': 'Mike Wilson',
        'notes': 'Several issues identified - see detailed report.',
        'parts_used': 'Various seals and gaskets',
        'labor_hours': 4.5,
        'cost': 850.25
    }
]

@maintenance_module_bp.route('/')
@login_required
def index():
    """Maintenance dashboard page"""
    # Log the navigation to maintenance dashboard
    log_navigation(request.referrer or '/', 'maintenance.index')
    
    # Count the items by status
    scheduled_count = sum(1 for m in SAMPLE_MAINTENANCE_SCHEDULES if m['status'] == 'Scheduled')
    overdue_count = sum(1 for m in SAMPLE_MAINTENANCE_SCHEDULES if m['status'] == 'Overdue')
    completed_count = len(SAMPLE_MAINTENANCE_RECORDS)
    
    # Calculate metrics
    upcoming_week = sum(1 for m in SAMPLE_MAINTENANCE_SCHEDULES 
                        if (m['next_due'] - datetime.now()).days <= 7 and m['status'] == 'Scheduled')
    
    return render_template(
        'maintenance/index.html',
        title='Maintenance Dashboard',
        schedules=SAMPLE_MAINTENANCE_SCHEDULES,
        technicians=SAMPLE_TECHNICIANS,
        scheduled_count=scheduled_count,
        overdue_count=overdue_count,
        completed_count=completed_count,
        upcoming_week=upcoming_week
    )

@maintenance_module_bp.route('/schedules')
@login_required
def maintenance_schedules():
    """View all maintenance schedules"""
    log_navigation(request.referrer or '/', 'maintenance.maintenance_schedules')
    
    return render_template(
        'maintenance/schedules.html',
        title='Maintenance Schedules',
        schedules=SAMPLE_MAINTENANCE_SCHEDULES
    )

@maintenance_module_bp.route('/schedule/<int:schedule_id>')
@login_required
def schedule_detail(schedule_id):
    """View details of a specific maintenance schedule"""
    log_navigation(request.referrer or '/', f'maintenance.schedule_detail({schedule_id})')
    
    # Find the schedule by ID
    schedule = next((s for s in SAMPLE_MAINTENANCE_SCHEDULES if s['id'] == schedule_id), None)
    
    if not schedule:
        flash('Maintenance schedule not found', 'danger')
        return redirect(url_for('maintenance.maintenance_schedules'))
    
    return render_template(
        'maintenance/schedule_detail.html',
        title=f'Schedule Detail: {schedule["asset_name"]}',
        schedule=schedule,
        technicians=SAMPLE_TECHNICIANS
    )

@maintenance_module_bp.route('/records')
@login_required
def maintenance_records():
    """View all maintenance records"""
    log_navigation(request.referrer or '/', 'maintenance.maintenance_records')
    
    return render_template(
        'maintenance/records.html',
        title='Maintenance Records',
        records=SAMPLE_MAINTENANCE_RECORDS
    )

@maintenance_module_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_schedule():
    """Create a new maintenance schedule"""
    log_navigation(request.referrer or '/', 'maintenance.create_schedule')
    
    if request.method == 'POST':
        # In a real app, this would save to a database
        flash('Maintenance schedule created successfully', 'success')
        log_activity('maintenance_create', 'Created a new maintenance schedule')
        return redirect(url_for('maintenance.maintenance_schedules'))
    
    return render_template(
        'maintenance/create_schedule.html',
        title='Create Maintenance Schedule',
        tasks=SAMPLE_MAINTENANCE_TASKS,
        technicians=SAMPLE_TECHNICIANS
    )

@maintenance_module_bp.route('/technicians')
@login_required
def technicians():
    """View all maintenance technicians"""
    log_navigation(request.referrer or '/', 'maintenance.technicians')
    
    return render_template(
        'maintenance/technicians.html',
        title='Maintenance Technicians',
        technicians=SAMPLE_TECHNICIANS
    )

@maintenance_module_bp.route('/complete/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def complete_maintenance(schedule_id):
    """Mark a maintenance schedule as complete"""
    log_navigation(request.referrer or '/', f'maintenance.complete_maintenance({schedule_id})')
    
    # Find the schedule by ID
    schedule = next((s for s in SAMPLE_MAINTENANCE_SCHEDULES if s['id'] == schedule_id), None)
    
    if not schedule:
        flash('Maintenance schedule not found', 'danger')
        return redirect(url_for('maintenance.maintenance_schedules'))
    
    if request.method == 'POST':
        # In a real app, this would update the database
        flash('Maintenance marked as complete', 'success')
        log_activity('maintenance_complete', f'Completed maintenance task for {schedule["asset_name"]}')
        return redirect(url_for('maintenance.maintenance_schedules'))
    
    return render_template(
        'maintenance/complete_form.html',
        title=f'Complete Maintenance: {schedule["asset_name"]}',
        schedule=schedule,
        technicians=SAMPLE_TECHNICIANS,
        tasks=SAMPLE_MAINTENANCE_TASKS
    )