"""
April 2025 Billing Simulation Module

This module provides routes and functionality for simulating the April 2025 billing process
using the enhanced dashboard-based workflow instead of the legacy method.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Import activity logger
from utils.activity_logger import (
    log_navigation, log_document_upload, log_report_export,
    log_pm_process, log_invoice_generation
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize blueprint
april_billing_bp = Blueprint('april_billing', __name__, url_prefix='/april_billing')

# Constants
UPLOAD_FOLDER = os.path.join('uploads', 'billing_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXPORTS_FOLDER = os.path.join('exports', 'billing_reports')
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

RESULTS_FOLDER = os.path.join('reconcile', 'pm_results')
os.makedirs(RESULTS_FOLDER, exist_ok=True)

DATA_FOLDER = os.path.join('attached_assets')

# Load real April 2025 billing data
def load_april_billing_data():
    """
    Load April 2025 billing data from the attached assets folder
    """
    try:
        # Define file paths
        master_file_path = os.path.join(DATA_FOLDER, 'EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx')
        
        # Check if files exist
        if not os.path.exists(master_file_path):
            logger.error(f"Master file not found: {master_file_path}")
            return {
                'success': False,
                'error': 'Required data files not found',
                'data': generate_sample_data()
            }
        
        # Load data from excel files
        master_df = pd.read_excel(master_file_path, sheet_name='EQ ALLOCATIONS - ALL DIV')
        
        # Process raw data
        # Skip header rows - header is at row 3 (index 2) and data starts at row 4 (index 3)
        if master_df.shape[0] > 3:
            # Real header is at row 3
            header_row = 2
            data_start_row = 3
            
            # Extract column names from the header row
            column_names = master_df.iloc[header_row].values
            
            # Create a new DataFrame with the actual data and proper column names
            data_df = pd.DataFrame(master_df.iloc[data_start_row:].values, columns=column_names)
            
            # Clean up column names
            data_df.columns = [str(col).strip() if not pd.isna(col) else f"Unnamed_{i}" 
                              for i, col in enumerate(data_df.columns)]
            
            # Filter out any completely empty rows
            data_df = data_df.dropna(how='all')
            
            # Convert numerical columns to proper types
            numeric_columns = ['UNIT ALLOCATION', 'REVISION']
            for col in numeric_columns:
                if col in data_df.columns:
                    data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
            
            # Process the data for the dashboard
            regions = data_df['DIV'].dropna().unique() if 'DIV' in data_df.columns else []
            jobs = data_df['JOB'].dropna().unique() if 'JOB' in data_df.columns else []
            
            # Generate region summaries
            region_summaries = []
            for region in regions:
                region_data = data_df[data_df['DIV'] == region]
                region_summaries.append({
                    'region': region,
                    'asset_count': region_data['ASSET ID'].nunique(),
                    'job_count': region_data['JOB'].nunique(),
                    'total_units': region_data['UNIT ALLOCATION'].sum(),
                    'revised_units': region_data['REVISION'].sum(),
                    'jobs': region_data['JOB'].unique().tolist()
                })
                
            # Generate job summaries
            job_summaries = []
            for job in jobs:
                job_data = data_df[data_df['JOB'] == job]
                job_summaries.append({
                    'job': job,
                    'region': job_data['DIV'].iloc[0] if not job_data['DIV'].empty else 'Unknown',
                    'asset_count': job_data['ASSET ID'].nunique(),
                    'total_units': job_data['UNIT ALLOCATION'].sum(),
                    'revised_units': job_data['REVISION'].sum(),
                    'cost_codes': job_data['COST CODE'].dropna().unique().tolist()
                })
            
            # Convert to a list of dictionaries for the records
            records = []
            for _, row in data_df.iterrows():
                record = {}
                for col in data_df.columns:
                    record[col] = row[col]
                records.append(record)
            
            return {
                'success': True,
                'regions': regions.tolist(),
                'jobs': jobs.tolist(),
                'records': records,
                'region_summaries': region_summaries,
                'job_summaries': job_summaries,
                'total_assets': data_df['ASSET ID'].nunique(),
                'total_units': data_df['UNIT ALLOCATION'].sum(),
                'revised_units': data_df['REVISION'].sum()
            }
        else:
            logger.error(f"Invalid data format in master file: {master_file_path}")
            return {
                'success': False,
                'error': 'Invalid data format in master file',
                'data': generate_sample_data()
            }
            
    except Exception as e:
        logger.error(f"Error loading April billing data: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'data': generate_sample_data()
        }

def generate_sample_data():
    """Generate sample data for testing when real data isn't available"""
    regions = ['DFW', 'HOU', 'WTX']
    jobs = ['2024-019', '2024-025', '2024-030', '2022-008']
    
    region_summaries = []
    for region in regions:
        region_summaries.append({
            'region': region,
            'asset_count': 12,
            'job_count': 2,
            'total_units': 15.5,
            'revised_units': 16.2,
            'jobs': jobs[:2] if region == 'DFW' else jobs[2:]
        })
    
    job_summaries = []
    for job in jobs:
        job_summaries.append({
            'job': job,
            'region': 'DFW' if job in ['2024-019', '2024-025'] else 'HOU' if job == '2024-030' else 'WTX',
            'asset_count': 6,
            'total_units': 7.5,
            'revised_units': 8.0,
            'cost_codes': ['9000 100F', '9000 100M']
        })
    
    return {
        'regions': regions,
        'jobs': jobs,
        'region_summaries': region_summaries,
        'job_summaries': job_summaries,
        'total_assets': 36,
        'total_units': 45.0,
        'revised_units': 48.0
    }

def get_allocation_files():
    """Get list of April PM allocation files from the attached assets"""
    try:
        april_files = []
        
        # scan the attached_assets folder for April files
        for filename in os.listdir(DATA_FOLDER):
            if 'APRIL 2025' in filename.upper() and filename.endswith(('.xlsx', '.xlsm')):
                # Determine file type
                file_type = 'Original'
                if 'FINAL' in filename.upper() or 'REVISION' in filename.upper():
                    file_type = 'Final'
                elif 'ALLOCATED' in filename.upper() or 'CODED' in filename.upper():
                    file_type = 'Modified'
                
                # Determine region
                region = 'Unknown'
                if 'DFW' in filename.upper():
                    region = 'DFW'
                elif 'HOU' in filename.upper():
                    region = 'HOU'
                elif 'WTX' in filename.upper() or 'WEST TEXAS' in filename.upper():
                    region = 'WTX'
                
                # Add file info
                april_files.append({
                    'id': str(len(april_files) + 1),
                    'filename': filename,
                    'date_uploaded': '2025-05-15',
                    'uploaded_by': 'System Import',
                    'status': 'Final' if 'FINAL' in filename.upper() else 'Updated' if 'ALLOCATED' in filename.upper() else 'Original',
                    'file_type': file_type,
                    'region': region,
                    'path': os.path.join(DATA_FOLDER, filename)
                })
        
        return april_files
    except Exception as e:
        logger.error(f"Error scanning for allocation files: {str(e)}")
        return []

# Routes
@april_billing_bp.route('/')
@login_required
def index():
    """April 2025 billing simulation dashboard"""
    log_navigation('april_billing.index', 'Accessed April 2025 Billing Simulation')
    
    # Load the April billing data
    billing_data = load_april_billing_data()
    
    # Get allocation files
    allocation_files = get_allocation_files()
    
    # Create summary metrics
    summary = {
        'total_assets': billing_data.get('total_assets', 0),
        'total_jobs': len(billing_data.get('jobs', [])),
        'total_regions': len(billing_data.get('regions', [])),
        'total_units': billing_data.get('total_units', 0),
        'revised_units': billing_data.get('revised_units', 0),
        'total_difference': billing_data.get('revised_units', 0) - billing_data.get('total_units', 0),
        'month': 'April 2025'
    }
    
    return render_template('billing/april_simulation.html', 
                          billing_data=billing_data,
                          summary=summary,
                          allocation_files=allocation_files[:5], # Show only 5 recent files
                          regions=billing_data.get('region_summaries', []),
                          jobs=billing_data.get('job_summaries', []))

@april_billing_bp.route('/region/<region_id>')
@login_required
def region_detail(region_id):
    """Show detailed job and asset data for a specific region"""
    log_navigation(f'april_billing.region_detail.{region_id}', f'Viewed April 2025 Billing for {region_id} Region')
    
    # Load the April billing data
    billing_data = load_april_billing_data()
    
    # Filter data for this region
    region_data = [record for record in billing_data.get('records', []) 
                  if record.get('DIV') == region_id]
    
    # Get jobs for this region
    region_jobs = [job for job in billing_data.get('job_summaries', [])
                  if job.get('region') == region_id]
    
    # Get summary for this region
    region_summary = next((region for region in billing_data.get('region_summaries', [])
                          if region.get('region') == region_id), {})
    
    # Group assets by job
    jobs_with_assets = {}
    for record in region_data:
        job = record.get('JOB')
        if job not in jobs_with_assets:
            jobs_with_assets[job] = []
        
        jobs_with_assets[job].append(record)
    
    return render_template('billing/april_region_detail.html',
                          region_id=region_id,
                          region_summary=region_summary,
                          jobs=region_jobs,
                          jobs_with_assets=jobs_with_assets,
                          total_assets=len(region_data))

@april_billing_bp.route('/job/<job_id>')
@login_required
def job_detail(job_id):
    """Show detailed asset data for a specific job"""
    log_navigation(f'april_billing.job_detail.{job_id}', f'Viewed April 2025 Billing for Job {job_id}')
    
    # Load the April billing data
    billing_data = load_april_billing_data()
    
    # Filter data for this job
    job_data = [record for record in billing_data.get('records', []) 
               if record.get('JOB') == job_id]
    
    # Get summary for this job
    job_summary = next((job for job in billing_data.get('job_summaries', [])
                       if job.get('job') == job_id), {})
    
    # Group assets by cost code
    assets_by_cost_code = {}
    for record in job_data:
        cost_code = record.get('COST CODE', 'Unknown')
        if cost_code not in assets_by_cost_code:
            assets_by_cost_code[cost_code] = []
        
        assets_by_cost_code[cost_code].append(record)
    
    return render_template('billing/april_job_detail.html',
                          job_id=job_id,
                          job_summary=job_summary,
                          assets=job_data,
                          assets_by_cost_code=assets_by_cost_code,
                          total_assets=len(job_data))

@april_billing_bp.route('/asset/<asset_id>')
@login_required
def asset_detail(asset_id):
    """Show detailed information for a specific asset"""
    log_navigation(f'april_billing.asset_detail.{asset_id}', f'Viewed April 2025 Billing for Asset {asset_id}')
    
    # Load the April billing data
    billing_data = load_april_billing_data()
    
    # Find this asset
    asset_data = next((record for record in billing_data.get('records', []) 
                      if record.get('ASSET ID') == asset_id), {})
    
    if not asset_data:
        flash(f"Asset {asset_id} not found in April 2025 billing data", "danger")
        return redirect(url_for('april_billing.index'))
    
    return render_template('billing/april_asset_detail.html',
                          asset_id=asset_id,
                          asset_data=asset_data)

@april_billing_bp.route('/cost_codes')
@login_required
def cost_code_breakdown():
    """Show cost code breakdown for April 2025 billing"""
    log_navigation('april_billing.cost_code_breakdown', 'Viewed April 2025 Billing Cost Code Breakdown')
    
    # Load the April billing data
    billing_data = load_april_billing_data()
    
    # Group by cost code
    cost_code_data = {}
    
    for record in billing_data.get('records', []):
        cost_code = record.get('COST CODE', 'Unknown')
        
        if cost_code not in cost_code_data:
            cost_code_data[cost_code] = {
                'cost_code': cost_code,
                'total_units': 0,
                'revised_units': 0,
                'asset_count': 0,
                'jobs': set()
            }
        
        # Increment counters
        cost_code_data[cost_code]['total_units'] += record.get('UNIT ALLOCATION', 0) or 0
        cost_code_data[cost_code]['revised_units'] += record.get('REVISION', 0) or 0
        cost_code_data[cost_code]['asset_count'] += 1
        cost_code_data[cost_code]['jobs'].add(record.get('JOB', 'Unknown'))
    
    # Convert to list and calculate differences
    cost_codes = []
    for cc, data in cost_code_data.items():
        data['jobs'] = list(data['jobs'])
        data['job_count'] = len(data['jobs'])
        data['difference'] = data['revised_units'] - data['total_units']
        cost_codes.append(data)
    
    # Sort by largest cost codes first
    cost_codes.sort(key=lambda x: x['total_units'], reverse=True)
    
    return render_template('billing/april_cost_codes.html',
                          cost_codes=cost_codes)

@april_billing_bp.route('/export', methods=['GET'])
@login_required
def export_data():
    """Export April 2025 billing data in various formats"""
    report_type = request.args.get('type', 'summary')
    export_format = request.args.get('format', 'xlsx')
    region = request.args.get('region')
    job = request.args.get('job')
    cost_code = request.args.get('cost_code')
    
    # Log the export
    log_report_export(
        f'april_2025_billing_{report_type}',
        export_format,
        current_user.id if current_user.is_authenticated else None
    )
    
    try:
        # Load the data
        billing_data = load_april_billing_data()
        
        # Prepare file path
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"april_2025_billing_{report_type}_{timestamp}.{export_format}"
        filepath = os.path.join(EXPORTS_FOLDER, filename)
        
        # Filter the data if needed
        filtered_data = billing_data.get('records', [])
        
        if region:
            filtered_data = [record for record in filtered_data if record.get('DIV') == region]
            
        if job:
            filtered_data = [record for record in filtered_data if record.get('JOB') == job]
            
        if cost_code:
            filtered_data = [record for record in filtered_data if record.get('COST CODE') == cost_code]
        
        # Generate the export
        if export_format == 'xlsx':
            # Create Excel export
            writer = pd.ExcelWriter(filepath, engine='openpyxl')
            
            if report_type == 'summary':
                # Region summary sheet
                region_df = pd.DataFrame(billing_data.get('region_summaries', []))
                region_df.to_excel(writer, sheet_name='Regions', index=False)
                
                # Job summary sheet
                job_df = pd.DataFrame(billing_data.get('job_summaries', []))
                job_df.to_excel(writer, sheet_name='Jobs', index=False)
                
                # Full data
                data_df = pd.DataFrame(filtered_data)
                data_df.to_excel(writer, sheet_name='Detail', index=False)
                
            elif report_type == 'detail':
                # Just the detailed data
                data_df = pd.DataFrame(filtered_data)
                data_df.to_excel(writer, sheet_name='Detail', index=False)
                
            elif report_type == 'foundation':
                # Format for Foundation import - no headers
                data_df = pd.DataFrame(filtered_data)
                # Select only the required columns and order them correctly
                required_cols = ['JOB', 'COST CODE', 'EQUIPMENT', 'UNIT ALLOCATION']
                
                # Use REVISION if available and not NaN
                for i, record in data_df.iterrows():
                    if pd.notna(record.get('REVISION')):
                        data_df.at[i, 'UNIT ALLOCATION'] = record['REVISION']
                
                if all(col in data_df.columns for col in required_cols):
                    foundation_df = data_df[required_cols]
                    foundation_df.to_excel(writer, sheet_name='Foundation Import', 
                                          index=False, header=False)
                
            writer.close()
            
        elif export_format == 'csv':
            # Create CSV export
            data_df = pd.DataFrame(filtered_data)
            data_df.to_csv(filepath, index=False)
            
        elif export_format == 'json':
            # Create JSON export
            with open(filepath, 'w') as f:
                if report_type == 'summary':
                    json.dump({
                        'regions': billing_data.get('region_summaries', []),
                        'jobs': billing_data.get('job_summaries', []),
                        'detail': filtered_data
                    }, f, indent=2)
                else:
                    json.dump(filtered_data, f, indent=2)
        
        # Redirect to download the file
        return redirect(url_for('april_billing.download_export', filename=filename))
    
    except Exception as e:
        logger.error(f"Error exporting April billing data: {str(e)}")
        flash(f"Error generating export: {str(e)}", "danger")
        return redirect(url_for('april_billing.index'))

@april_billing_bp.route('/download/<filename>')
@login_required
def download_export(filename):
    """Download an exported file"""
    try:
        return send_file(
            os.path.join(EXPORTS_FOLDER, filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        flash(f"Error downloading file: {str(e)}", "danger")
        return redirect(url_for('april_billing.index'))