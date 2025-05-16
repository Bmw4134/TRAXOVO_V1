"""
Asset-Driver Management Routes

This module provides routes and functionality for managing asset-driver relationships,
including assigning drivers to assets, importing assignments from files, and viewing
current and historical assignments.
"""

import os
import uuid
import pandas as pd
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from sqlalchemy import func, desc

from models.models import Asset, AssetDriverMapping
from models.core import Driver
from utils.asset_driver_mapper import process_assignment_file, validate_assignments
from app import db

# Create blueprint
asset_drivers_bp = Blueprint('asset_drivers', __name__, url_prefix='/asset-drivers')

@asset_drivers_bp.route('/')
@login_required
def asset_driver_list():
    """
    Display list of asset-driver assignments with filtering options
    """
    # Get filter parameters
    asset_id = request.args.get('asset_id', type=int)
    driver_id = request.args.get('driver_id', type=int)
    status = request.args.get('status')
    
    # Build query with filters
    query = AssetDriverMapping.query.join(Asset)
    
    if asset_id:
        query = query.filter(AssetDriverMapping.asset_id == asset_id)
    
    if driver_id:
        query = query.filter(AssetDriverMapping.driver_id == driver_id)
    
    if status == 'current':
        query = query.filter(AssetDriverMapping.is_current == True)
    elif status == 'historical':
        query = query.filter(AssetDriverMapping.is_current == False)
    
    # Get assignments with pagination
    assignments = query.order_by(desc(AssetDriverMapping.start_date)).all()
    
    # Get assets and drivers for filter dropdowns
    assets = Asset.query.order_by(Asset.asset_identifier).all()
    drivers = Driver.query.order_by(Driver.name).all()
    
    # Calculate statistics
    stats = {
        'total_assignments': AssetDriverMapping.query.count(),
        'current_assignments': AssetDriverMapping.query.filter_by(is_current=True).count(),
        'historical_assignments': AssetDriverMapping.query.filter_by(is_current=False).count(),
        'total_assets': Asset.query.count(),
        'assets_assigned': db.session.query(func.count(func.distinct(AssetDriverMapping.asset_id)))
                           .filter(AssetDriverMapping.is_current == True).scalar() or 0,
        'total_drivers': Driver.query.count(),
        'active_drivers': Driver.query.filter_by(active=True).count(),
    }
    
    # Calculate percentages
    stats['asset_assignment_percentage'] = round((stats['assets_assigned'] / stats['total_assets']) * 100 
                                              if stats['total_assets'] > 0 else 0)
    stats['driver_active_percentage'] = round((stats['active_drivers'] / stats['total_drivers']) * 100 
                                          if stats['total_drivers'] > 0 else 0)
    
    return render_template('asset_drivers/list.html', 
                          assignments=assignments,
                          assets=assets,
                          drivers=drivers,
                          stats=stats)

@asset_drivers_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_asset_drivers():
    """
    Import asset-driver assignments from a file
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '' or not file.filename:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            flash('Invalid file format. Please upload .xlsx, .xls, or .csv files.', 'danger')
            return redirect(request.url)
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_dir = os.path.join('uploads', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        # Get column configuration
        asset_column = request.form.get('asset_column', 'Asset ID')
        driver_column = request.form.get('driver_column', 'Driver ID')
        start_date_column = request.form.get('start_date_column', 'Start Date')
        has_header = 'has_header' in request.form
        end_previous = 'end_previous' in request.form
        
        # Process file
        session_id = str(uuid.uuid4())
        preview_data, valid_count = process_assignment_file(
            file_path, 
            asset_column=asset_column,
            driver_column=driver_column,
            start_date_column=start_date_column,
            has_header=has_header,
            end_previous=end_previous,
            session_id=session_id
        )
        
        return render_template('asset_drivers/import.html',
                              preview_data=preview_data,
                              valid_count=valid_count,
                              session_id=session_id,
                              has_valid_rows=valid_count > 0)
    
    return render_template('asset_drivers/import.html')

@asset_drivers_bp.route('/import/confirm', methods=['POST'])
@login_required
def confirm_import():
    """
    Confirm and finalize the import of asset-driver assignments
    """
    session_id = request.form.get('session_id')
    if not session_id:
        flash('Invalid session', 'danger')
        return redirect(url_for('asset_drivers.import_asset_drivers'))
    
    assignments = session.get(f'asset_driver_import_{session_id}', [])
    if not assignments:
        flash('No valid assignments found to import', 'danger')
        return redirect(url_for('asset_drivers.import_asset_drivers'))
    
    success_count = 0
    for data in assignments:
        if data.get('status') == 'valid':
            # End previous assignments if needed
            if data.get('end_previous', True):
                previous_assignments = AssetDriverMapping.query.filter_by(
                    asset_id=data['asset_id'],
                    is_current=True
                ).all()
                
                for prev in previous_assignments:
                    prev.is_current = False
                    prev.end_date = data['start_date'] or date.today()
            
            # Create new assignment
            assignment = AssetDriverMapping(
                asset_id=data['asset_id'],
                driver_id=data['driver_id'],
                start_date=data['start_date'] or date.today(),
                is_current=True
            )
            
            db.session.add(assignment)
            success_count += 1
    
    try:
        db.session.commit()
        flash(f'Successfully imported {success_count} asset-driver assignments', 'success')
        # Clean up session data
        session.pop(f'asset_driver_import_{session_id}', None)
    except Exception as e:
        db.session.rollback()
        flash(f'Error importing assignments: {str(e)}', 'danger')
    
    return redirect(url_for('asset_drivers.asset_driver_list'))

@asset_drivers_bp.route('/assign', methods=['GET', 'POST'])
@login_required
def assign_asset_driver():
    """
    Assign a driver to an asset
    """
    assets = Asset.query.filter_by(active=True).order_by(Asset.asset_identifier).all()
    drivers = Driver.query.filter_by(active=True).order_by(Driver.name).all()
    
    if request.method == 'POST':
        asset_id = request.form.get('asset_id', type=int)
        driver_id = request.form.get('driver_id', type=int)
        start_date_str = request.form.get('start_date')
        notes = request.form.get('notes', '')
        
        if not asset_id or not driver_id or not start_date_str:
            flash('Please fill in all required fields', 'danger')
            return render_template('asset_drivers/assign.html', 
                                  assets=assets, 
                                  drivers=drivers,
                                  title="Assign Driver to Asset",
                                  form_action=url_for('asset_drivers.assign_asset_driver'))
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
            # Check if asset already has a current assignment
            existing = AssetDriverMapping.query.filter_by(
                asset_id=asset_id,
                is_current=True
            ).first()
            
            if existing:
                # End previous assignment
                existing.is_current = False
                existing.end_date = start_date
            
            # Create new assignment
            assignment = AssetDriverMapping(
                asset_id=asset_id,
                driver_id=driver_id,
                start_date=start_date,
                is_current=True,
                notes=notes
            )
            
            db.session.add(assignment)
            db.session.commit()
            
            flash('Driver successfully assigned to asset', 'success')
            return redirect(url_for('asset_drivers.asset_driver_list'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error assigning driver: {str(e)}', 'danger')
    
    return render_template('asset_drivers/assign.html', 
                          assets=assets, 
                          drivers=drivers,
                          title="Assign Driver to Asset",
                          form_action=url_for('asset_drivers.assign_asset_driver'))

@asset_drivers_bp.route('/edit/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def edit_assignment(assignment_id):
    """
    Edit an existing asset-driver assignment
    """
    assignment = AssetDriverMapping.query.get_or_404(assignment_id)
    assets = Asset.query.filter_by(active=True).order_by(Asset.asset_identifier).all()
    drivers = Driver.query.filter_by(active=True).order_by(Driver.name).all()
    
    if request.method == 'POST':
        asset_id = request.form.get('asset_id', type=int)
        driver_id = request.form.get('driver_id', type=int)
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        is_current = 'is_current' in request.form
        notes = request.form.get('notes', '')
        
        if not asset_id or not driver_id or not start_date_str:
            flash('Please fill in all required fields', 'danger')
            return render_template('asset_drivers/assign.html', 
                                  assets=assets, 
                                  drivers=drivers,
                                  assignment=assignment,
                                  editing=True,
                                  title="Edit Asset-Driver Assignment",
                                  form_action=url_for('asset_drivers.edit_assignment', assignment_id=assignment_id))
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
            
            # Update assignment
            assignment.asset_id = asset_id
            assignment.driver_id = driver_id
            assignment.start_date = start_date
            assignment.end_date = end_date
            assignment.is_current = is_current
            assignment.notes = notes
            
            # If not current and no end date, set end date to today
            if not is_current and not end_date:
                assignment.end_date = date.today()
            
            db.session.commit()
            
            flash('Assignment updated successfully', 'success')
            return redirect(url_for('asset_drivers.asset_driver_list'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating assignment: {str(e)}', 'danger')
    
    return render_template('asset_drivers/assign.html', 
                          assets=assets, 
                          drivers=drivers,
                          assignment=assignment,
                          editing=True,
                          title="Edit Asset-Driver Assignment",
                          form_action=url_for('asset_drivers.edit_assignment', assignment_id=assignment_id))

@asset_drivers_bp.route('/end/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def end_assignment(assignment_id):
    """
    End an active asset-driver assignment
    """
    assignment = AssetDriverMapping.query.get_or_404(assignment_id)
    
    if not assignment.is_current:
        flash('This assignment has already ended', 'warning')
        return redirect(url_for('asset_drivers.asset_driver_list'))
    
    if request.method == 'POST':
        end_date_str = request.form.get('end_date')
        
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            
            assignment.is_current = False
            assignment.end_date = end_date
            
            db.session.commit()
            
            flash('Assignment ended successfully', 'success')
            return redirect(url_for('asset_drivers.asset_driver_list'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error ending assignment: {str(e)}', 'danger')
    
    return render_template('asset_drivers/end_assignment.html', 
                          assignment=assignment,
                          today=date.today().strftime('%Y-%m-%d'))