"""
Asset-Driver Mapping Routes

This module contains routes for managing asset-driver relationships.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sqlalchemy import desc

from main import db, Asset, Driver, AssetDriverMapping
from utils.asset_driver_mapper import import_asset_driver_assignments, get_unique_drivers

asset_drivers = Blueprint('asset_drivers', __name__, url_prefix='/asset-drivers')

@asset_drivers.route('/')
@login_required
def index():
    """
    Display asset-driver relationships dashboard
    """
    return render_template('asset_drivers/list.html')

@asset_drivers.route('/api/data')
@login_required
def api_data():
    """
    API endpoint to get asset-driver assignment data
    """
    try:
        # Calculate statistics
        total_assets = Asset.query.filter_by(active=True).count()
        total_drivers = Driver.query.filter_by(active=True).count()
        
        # Get assigned assets count
        assigned_assets = db.session.query(AssetDriverMapping.asset_id)\
            .filter_by(is_current=True)\
            .distinct()\
            .count()
        
        # Get assigned drivers count
        assigned_drivers = db.session.query(AssetDriverMapping.driver_id)\
            .filter_by(is_current=True)\
            .distinct()\
            .count()
        
        # Calculate assignments by category
        asset_categories = db.session.query(
            Asset.asset_category, 
            db.func.count(AssetDriverMapping.id)
        ).join(
            AssetDriverMapping, 
            Asset.id == AssetDriverMapping.asset_id
        ).filter(
            AssetDriverMapping.is_current == True
        ).group_by(
            Asset.asset_category
        ).all()
        
        # Get driver assignments by department
        driver_departments = db.session.query(
            Driver.department, 
            db.func.count(AssetDriverMapping.id)
        ).join(
            AssetDriverMapping, 
            Driver.id == AssetDriverMapping.driver_id
        ).filter(
            AssetDriverMapping.is_current == True
        ).group_by(
            Driver.department
        ).all()
        
        # Get current assignments (last 20)
        current_assignments = AssetDriverMapping.query.filter_by(
            is_current=True
        ).order_by(
            desc(AssetDriverMapping.start_date)
        ).limit(20).all()
        
        # Format the results
        assignments_data = []
        for assignment in current_assignments:
            asset = Asset.query.get(assignment.asset_id)
            driver = Driver.query.get(assignment.driver_id)
            
            if asset and driver:
                assignments_data.append({
                    'id': assignment.id,
                    'asset_id': asset.id,
                    'asset_identifier': asset.asset_identifier,
                    'asset_description': asset.description,
                    'driver_id': driver.id,
                    'driver_name': driver.name,
                    'driver_department': driver.department,
                    'start_date': assignment.start_date.strftime('%Y-%m-%d'),
                    'days_assigned': (datetime.now().date() - assignment.start_date).days
                })
        
        # Format the category and department data
        categories_data = [{'name': cat, 'count': count} for cat, count in asset_categories]
        departments_data = [{'name': dept if dept else 'Unknown', 'count': count} 
                          for dept, count in driver_departments]
        
        # Return the formatted data
        return jsonify({
            'success': True,
            'statistics': {
                'total_assets': total_assets,
                'total_drivers': total_drivers,
                'assigned_assets': assigned_assets,
                'assigned_drivers': assigned_drivers,
                'assignment_rate': round((assigned_assets / total_assets * 100) if total_assets > 0 else 0, 1),
                'driver_assignment_rate': round((assigned_drivers / total_drivers * 100) if total_drivers > 0 else 0, 1)
            },
            'categories': categories_data,
            'departments': departments_data,
            'assignments': assignments_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@asset_drivers.route('/list')
@login_required
def list_assignments():
    """
    List all asset-driver assignments
    """
    # Get query parameters
    is_current = request.args.get('current', 'true') == 'true'
    asset_filter = request.args.get('asset', '')
    driver_filter = request.args.get('driver', '')
    department_filter = request.args.get('department', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build the query
    query = AssetDriverMapping.query
    
    # Apply filters
    if is_current:
        query = query.filter_by(is_current=True)
    
    if asset_filter:
        assets = Asset.query.filter(Asset.asset_identifier.like(f'%{asset_filter}%')).all()
        asset_ids = [a.id for a in assets]
        query = query.filter(AssetDriverMapping.asset_id.in_(asset_ids))
    
    if driver_filter:
        drivers = Driver.query.filter(Driver.name.like(f'%{driver_filter}%')).all()
        driver_ids = [d.id for d in drivers]
        query = query.filter(AssetDriverMapping.driver_id.in_(driver_ids))
    
    if department_filter:
        drivers = Driver.query.filter(Driver.department == department_filter).all()
        driver_ids = [d.id for d in drivers]
        query = query.filter(AssetDriverMapping.driver_id.in_(driver_ids))
    
    # Execute the query with pagination
    paginated = query.order_by(desc(AssetDriverMapping.start_date)).paginate(page=page, per_page=per_page)
    
    # Get all departments for the filter dropdown
    departments = Driver.query.with_entities(Driver.department).distinct().all()
    departments = [d[0] for d in departments if d[0]]
    
    return render_template(
        'asset_drivers/list.html', 
        assignments=paginated.items,
        pagination=paginated,
        is_current=is_current,
        asset_filter=asset_filter,
        driver_filter=driver_filter,
        department_filter=department_filter,
        departments=departments
    )

@asset_drivers.route('/assign', methods=['GET', 'POST'])
@login_required
def assign():
    """
    Assign a driver to an asset
    """
    if request.method == 'POST':
        asset_id = request.form.get('asset_id')
        driver_id = request.form.get('driver_id')
        start_date_str = request.form.get('start_date')
        notes = request.form.get('notes', '')
        
        # Validate
        if not asset_id or not driver_id or not start_date_str:
            flash('All fields are required', 'danger')
            return redirect(url_for('asset_drivers.assign'))
        
        try:
            # Convert start date to datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
            # Check if there's already a current assignment for this asset
            existing = AssetDriverMapping.query.filter_by(
                asset_id=asset_id,
                is_current=True
            ).first()
            
            # If there's an existing assignment, end it
            if existing:
                existing.is_current = False
                existing.end_date = start_date - timedelta(days=1)
                db.session.add(existing)
            
            # Create the new assignment
            new_assignment = AssetDriverMapping(
                asset_id=asset_id,
                driver_id=driver_id,
                start_date=start_date,
                is_current=True,
                notes=notes
            )
            
            db.session.add(new_assignment)
            db.session.commit()
            
            flash('Assignment created successfully', 'success')
            return redirect(url_for('asset_drivers.list_assignments'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating assignment: {str(e)}', 'danger')
            return redirect(url_for('asset_drivers.assign'))
    
    # GET request - show the assign form
    assets = Asset.query.filter_by(active=True).order_by(Asset.asset_identifier).all()
    drivers = Driver.query.filter_by(active=True).order_by(Driver.name).all()
    
    return render_template(
        'asset_drivers/assign.html',
        assets=assets,
        drivers=drivers,
        today=datetime.now().strftime('%Y-%m-%d')
    )

@asset_drivers.route('/end-assignment/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def end_assignment(assignment_id):
    """
    End an asset-driver assignment
    """
    # Get the assignment
    assignment = AssetDriverMapping.query.get_or_404(assignment_id)
    
    if request.method == 'POST':
        end_date_str = request.form.get('end_date')
        notes = request.form.get('notes', '')
        
        # Validate
        if not end_date_str:
            flash('End date is required', 'danger')
            return redirect(url_for('asset_drivers.end_assignment', assignment_id=assignment_id))
        
        try:
            # Convert end date to datetime
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            # Validate end date is after start date
            if end_date < assignment.start_date:
                flash('End date must be after start date', 'danger')
                return redirect(url_for('asset_drivers.end_assignment', assignment_id=assignment_id))
            
            # Update the assignment
            assignment.is_current = False
            assignment.end_date = end_date
            
            # Append to existing notes
            if notes:
                if assignment.notes:
                    assignment.notes = f"{assignment.notes}\n\nEnded: {notes}"
                else:
                    assignment.notes = f"Ended: {notes}"
            
            db.session.add(assignment)
            db.session.commit()
            
            flash('Assignment ended successfully', 'success')
            return redirect(url_for('asset_drivers.list_assignments'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error ending assignment: {str(e)}', 'danger')
            return redirect(url_for('asset_drivers.end_assignment', assignment_id=assignment_id))
    
    # GET request - show the end assignment form
    asset = Asset.query.get(assignment.asset_id)
    driver = Driver.query.get(assignment.driver_id)
    
    return render_template(
        'asset_drivers/end_assignment.html',
        assignment=assignment,
        asset=asset,
        driver=driver,
        today=datetime.now().strftime('%Y-%m-%d')
    )

@asset_drivers.route('/history/<int:asset_id>')
@login_required
def asset_history(asset_id):
    """
    View assignment history for an asset
    """
    asset = Asset.query.get_or_404(asset_id)
    assignments = AssetDriverMapping.query.filter_by(asset_id=asset_id).order_by(desc(AssetDriverMapping.start_date)).all()
    
    # Get the drivers for each assignment
    drivers = {}
    for assignment in assignments:
        drivers[assignment.id] = Driver.query.get(assignment.driver_id)
    
    return render_template(
        'asset_drivers/history.html',
        asset=asset,
        assignments=assignments,
        drivers=drivers,
        type='asset'
    )

@asset_drivers.route('/driver-history/<int:driver_id>')
@login_required
def driver_history(driver_id):
    """
    View assignment history for a driver
    """
    driver = Driver.query.get_or_404(driver_id)
    assignments = AssetDriverMapping.query.filter_by(driver_id=driver_id).order_by(desc(AssetDriverMapping.start_date)).all()
    
    # Get the assets for each assignment
    assets = {}
    for assignment in assignments:
        assets[assignment.id] = Asset.query.get(assignment.asset_id)
    
    return render_template(
        'asset_drivers/history.html',
        driver=driver,
        assignments=assignments,
        assets=assets,
        type='driver'
    )

@asset_drivers.route('/import-assignments')
@login_required
def import_assignments():
    """
    Import asset-driver assignments from source files
    """
    result = import_asset_driver_assignments()
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')
        
    return redirect(url_for('asset_drivers.list_assignments'))

@asset_drivers.route('/discover-drivers')
@login_required
def discover_drivers():
    """
    Discover new drivers from source files
    """
    try:
        # Get unique drivers from timecard data
        unique_drivers = get_unique_drivers()
        
        # Check which ones already exist in the database
        existing_ids = [d.employee_id for d in Driver.query.all()]
        
        # Filter to only new drivers
        new_drivers = [d for d in unique_drivers if d['employee_id'] not in existing_ids]
        
        # Add them to the database
        for driver_data in new_drivers:
            driver = Driver(
                name=driver_data['name'],
                employee_id=driver_data['employee_id'],
                department=driver_data.get('department'),
                region=driver_data.get('region'),
                active=True
            )
            db.session.add(driver)
        
        if new_drivers:
            db.session.commit()
            flash(f'Added {len(new_drivers)} new drivers from source files', 'success')
        else:
            flash('No new drivers found in source files', 'info')
            
        return redirect(url_for('asset_drivers.list_assignments'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error discovering drivers: {str(e)}', 'danger')
        return redirect(url_for('asset_drivers.list_assignments'))