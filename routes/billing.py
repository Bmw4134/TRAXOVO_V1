"""
TRAXORA Fleet Management System - Billing Module

This module provides routes and functionality for the Billing module,
including PM allocation management and billing report generation.
"""
import os
import logging
import pandas as pd
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename

import sys
import os

# Add the parent directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db
from models import PMAllocation, JobSite, Asset, User, ActivityLog

logger = logging.getLogger(__name__)

# Create blueprint
billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_excel(file_path):
    """Load an Excel file into a pandas DataFrame"""
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        logger.error(f"Error loading Excel file {file_path}: {str(e)}")
        return None

def process_pm_allocations(ragle_file_path, pm_file_paths, verify_with_asset_list=True):
    """
    Process PM allocation files and compare against the base RAGLE file
    
    Args:
        ragle_file_path: Path to the base RAGLE file
        pm_file_paths: List of paths to PM allocation files
        verify_with_asset_list: Whether to verify allocations against the Asset List
        
    Returns:
        dict: Results of the processing
    """
    try:
        # Load the base RAGLE file
        ragle_df = load_excel(ragle_file_path)
        if ragle_df is None:
            return {'error': 'Failed to load RAGLE file'}
        
        # Load the PM allocation files
        pm_dfs = []
        for path in pm_file_paths:
            pm_df = load_excel(path)
            if pm_df is not None:
                pm_dfs.append(pm_df)
        
        if not pm_dfs:
            return {'error': 'No valid PM allocation files found'}
        
        # Process the files to extract job numbers and allocated amounts
        job_allocations = {}
        
        # Process RAGLE file
        job_column = find_job_column(ragle_df)
        amount_column = find_amount_column(ragle_df)
        
        if job_column is None or amount_column is None:
            return {'error': 'Could not find job number or amount columns in RAGLE file'}
        
        # Extract original allocations from RAGLE
        for _, row in ragle_df.iterrows():
            job_number = str(row[job_column])
            amount = float(row[amount_column]) if pd.notna(row[amount_column]) else 0.0
            
            if job_number not in job_allocations:
                job_allocations[job_number] = {
                    'original': 0.0,
                    'allocations': {}
                }
            
            job_allocations[job_number]['original'] += amount
        
        # Process PM allocation files
        for i, pm_df in enumerate(pm_dfs):
            pm_name = f"PM {i+1}"
            
            job_column = find_job_column(pm_df)
            amount_column = find_amount_column(pm_df)
            
            if job_column is None or amount_column is None:
                logger.warning(f"Could not find job number or amount columns in PM file {i+1}")
                continue
            
            for _, row in pm_df.iterrows():
                job_number = str(row[job_column])
                amount = float(row[amount_column]) if pd.notna(row[amount_column]) else 0.0
                
                if job_number not in job_allocations:
                    # If job doesn't exist in RAGLE, create it
                    job_allocations[job_number] = {
                        'original': 0.0,
                        'allocations': {}
                    }
                
                job_allocations[job_number]['allocations'][pm_name] = amount
        
        # Calculate totals and differences
        results = {
            'job_allocations': [],
            'ragle_total': 0.0,
            'allocated_total': 0.0,
            'difference_total': 0.0,
            'pm_names': [f"PM {i+1}" for i in range(len(pm_dfs))]
        }
        
        for job_number, data in job_allocations.items():
            original_amount = data['original']
            allocated_amounts = data['allocations']
            total_allocated = sum(allocated_amounts.values())
            difference = total_allocated - original_amount
            
            # Create record for this job
            job_record = {
                'job_number': job_number,
                'original_amount': original_amount,
                'allocated_amounts': allocated_amounts,
                'total_allocated': total_allocated,
                'difference': difference
            }
            
            # Verify job exists in the system if verify_with_asset_list is True
            if verify_with_asset_list:
                job_site = JobSite.query.filter_by(job_number=job_number).first()
                job_record['verified'] = job_site is not None
            else:
                job_record['verified'] = True
            
            results['job_allocations'].append(job_record)
            
            # Update totals
            results['ragle_total'] += original_amount
            results['allocated_total'] += total_allocated
            results['difference_total'] += difference
        
        # Sort by job number
        results['job_allocations'].sort(key=lambda x: x['job_number'])
        
        return results
    except Exception as e:
        logger.error(f"Error processing PM allocations: {str(e)}")
        return {'error': str(e)}

def find_job_column(df):
    """Find the column containing job numbers"""
    possible_columns = ['Job', 'Job Number', 'JobNumber', 'Job #', 'Job No', 'JobNo']
    
    # Check if any of the possible column names exist
    for col in possible_columns:
        if col in df.columns:
            return col
    
    # Check for columns that might contain job numbers
    for col in df.columns:
        if 'job' in str(col).lower():
            return col
    
    return None

def find_amount_column(df):
    """Find the column containing allocation amounts"""
    possible_columns = ['Amount', 'Total', 'Allocation', 'Allocated Amount', 'Value']
    
    # Check if any of the possible column names exist
    for col in possible_columns:
        if col in df.columns:
            return col
    
    # Check for columns that might contain amounts
    for col in df.columns:
        if any(keyword in str(col).lower() for keyword in ['amount', 'total', 'allocat', 'value']):
            return col
    
    return None

@billing_bp.route('/pm-allocation')
def pm_allocation():
    """PM Allocation main page"""
    # Get recent allocations
    recent_allocations = PMAllocation.query.order_by(PMAllocation.created_at.desc()).limit(10).all()
    
    return render_template(
        'billing/pm_allocation.html',
        recent_allocations=recent_allocations
    )

@billing_bp.route('/pm-allocation-processor', methods=['GET', 'POST'])
def pm_allocation_processor():
    """PM Allocation file processor page"""
    if request.method == 'POST':
        # Check if files were submitted
        if 'ragle_file' not in request.files:
            flash('Missing RAGLE file', 'error')
            return redirect(request.url)
        
        ragle_file = request.files['ragle_file']
        
        # Validate RAGLE file
        if not allowed_file(ragle_file.filename):
            flash('Invalid RAGLE file format. Only CSV and Excel files are allowed.', 'error')
            return redirect(request.url)
        
        # Get PM allocation files
        pm_files = []
        for i in range(10):  # Allow up to 10 PM files
            key = f'pm_file_{i}'
            if key in request.files and request.files[key].filename != '':
                pm_file = request.files[key]
                if not allowed_file(pm_file.filename):
                    flash(f'Invalid PM file {i+1} format. Only CSV and Excel files are allowed.', 'error')
                    return redirect(request.url)
                pm_files.append(pm_file)
        
        if not pm_files:
            flash('No PM allocation files submitted', 'error')
            return redirect(request.url)
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'pm_allocations')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the uploaded files
        ragle_path = os.path.join(upload_dir, secure_filename(ragle_file.filename))
        ragle_file.save(ragle_path)
        
        pm_paths = []
        for i, pm_file in enumerate(pm_files):
            pm_path = os.path.join(upload_dir, secure_filename(pm_file.filename))
            pm_file.save(pm_path)
            pm_paths.append(pm_path)
        
        # Process the files
        try:
            # Get verify_with_asset_list option
            verify_with_asset_list = request.form.get('verify_with_asset_list') == 'on'
            
            # Process the files
            results = process_pm_allocations(ragle_path, pm_paths, verify_with_asset_list)
            
            if 'error' in results:
                flash(f"Error processing files: {results['error']}", 'error')
                return redirect(request.url)
            
            # Store results in session for the results page
            # (In a real application, you might store these in the database)
            session = {
                'pm_allocation_results': results,
                'ragle_file': os.path.basename(ragle_path),
                'pm_files': [os.path.basename(path) for path in pm_paths]
            }
            
            flash('Files processed successfully', 'success')
            return render_template(
                'billing/pm_allocation_results.html',
                results=results,
                ragle_file=os.path.basename(ragle_path),
                pm_files=[os.path.basename(path) for path in pm_paths]
            )
        except Exception as e:
            flash(f"Error processing files: {str(e)}", 'error')
            return redirect(request.url)
    
    return render_template('billing/pm_allocation_processor.html')

@billing_bp.route('/api/pm-allocations')
def api_pm_allocations():
    """API endpoint to get PM allocations"""
    try:
        # Query parameters for filtering
        month = request.args.get('month')
        job_number = request.args.get('job_number')
        
        # Base query
        query = PMAllocation.query
        
        # Apply filters if provided
        if month:
            query = query.filter(PMAllocation.month == month)
        
        if job_number:
            query = query.filter(PMAllocation.job_number == job_number)
        
        # Get the allocations
        allocations = query.order_by(PMAllocation.month.desc(), PMAllocation.job_number).all()
        
        # Prepare the response
        result = []
        for allocation in allocations:
            allocation_data = {
                'id': allocation.id,
                'job_number': allocation.job_number,
                'month': allocation.month,
                'pm_name': allocation.pm_name,
                'original_amount': allocation.original_amount,
                'allocated_amount': allocation.allocated_amount,
                'status': allocation.status,
                'created_by': allocation.creator.username if allocation.creator else None,
                'approved_by': allocation.approver.username if allocation.approver else None,
                'created_at': allocation.created_at.isoformat()
            }
            result.append(allocation_data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in api_pm_allocations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@billing_bp.route('/reconcile', methods=['POST'])
def reconcile():
    """API endpoint to reconcile PM allocations"""
    try:
        data = request.json
        
        if not data or 'allocations' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        allocations = data['allocations']
        
        # Process and store the allocations
        for allocation in allocations:
            job_number = allocation.get('job_number')
            month = allocation.get('month')
            pm_name = allocation.get('pm_name')
            original_amount = allocation.get('original_amount')
            allocated_amount = allocation.get('allocated_amount')
            
            if not all([job_number, month, pm_name, original_amount, allocated_amount]):
                continue
            
            # Check if the job exists
            job_site = JobSite.query.filter_by(job_number=job_number).first()
            
            # Create or update the allocation
            pm_allocation = PMAllocation.query.filter_by(
                job_number=job_number,
                month=month,
                pm_name=pm_name
            ).first()
            
            if pm_allocation:
                # Update existing allocation
                pm_allocation.original_amount = original_amount
                pm_allocation.allocated_amount = allocated_amount
                pm_allocation.status = 'updated'
            else:
                # Create new allocation
                pm_allocation = PMAllocation(
                    organization_id=job_site.organization_id if job_site else None,
                    job_number=job_number,
                    month=month,
                    pm_name=pm_name,
                    original_amount=original_amount,
                    allocated_amount=allocated_amount,
                    status='pending',
                    created_by=current_user.id if current_user.is_authenticated else None
                )
                db.session.add(pm_allocation)
            
            # Log the action
            log = ActivityLog(
                user_id=current_user.id if current_user.is_authenticated else None,
                action='reconcile_pm_allocation',
                object_type='pm_allocation',
                object_id=pm_allocation.id if pm_allocation.id else None,
                details={
                    'job_number': job_number,
                    'month': month,
                    'pm_name': pm_name,
                    'original_amount': original_amount,
                    'allocated_amount': allocated_amount
                }
            )
            db.session.add(log)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Allocations reconciled successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in reconcile: {str(e)}")
        return jsonify({'error': str(e)}), 500