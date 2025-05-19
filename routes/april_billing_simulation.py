"""
April 2025 Billing Simulation Module

This module provides an improved workflow for handling the April 2025 billing process,
using an automated approach to extract and process billing data from source files.
"""

import os
import logging
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Import export functions
from utils.export_functions import (
    export_dataframe, export_fsi_format, ensure_exports_folder
)

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
april_billing_bp = Blueprint('april_billing', __name__, url_prefix='/april-billing')

# Constants
UPLOAD_FOLDER = 'uploads/april_billing'
PROCESSED_FOLDER = 'processed/april_billing'
EXPORTS_FOLDER = 'exports/april_billing'
MONTH_NAME = 'APRIL'
YEAR = '2025'

# Create necessary directories
for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, EXPORTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Global variables to store processed data
source_data = {
    'timecards': None,
    'daily_usage': None,
    'driving_history': None,
    'assets_time': None,
    'activity_detail': None,
    'allocations': None,
    'pm_revisions': None
}
processed_data = None
region_data = {}
job_data = {}
cost_code_data = {}
asset_data = {}
allocation_summary = {}

@april_billing_bp.route('/')
@login_required
def index():
    """April Billing Simulation Dashboard"""
    return render_template('billing/april_simulation.html', 
                           uploaded_files=get_uploaded_files(),
                           has_data=processed_data is not None,
                           summary=get_billing_summary() if processed_data is not None else None)

@april_billing_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload for billing data"""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('april_billing.index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('april_billing.index'))
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        file_type = request.form.get('file_type', 'allocation')
        if file_type == 'allocation':
            process_allocation_file(file_path, filename)
        else:
            process_pm_file(file_path, filename)
        
        flash(f'File {filename} uploaded and processed successfully!', 'success')
        return redirect(url_for('april_billing.index'))

@april_billing_bp.route('/process', methods=['POST'])
@login_required
def process_data():
    """Process uploaded data and generate billing allocations"""
    global processed_data, region_data, job_data, cost_code_data, asset_data, allocation_summary
    
    if not source_data:
        flash('No source data available for processing', 'error')
        return redirect(url_for('april_billing.index'))
    
    try:
        # Combine all source data
        combined_data = []
        for file_name, data in source_data.items():
            combined_data.append(data)
        
        if not combined_data:
            flash('No valid data found in uploaded files', 'error')
            return redirect(url_for('april_billing.index'))
        
        # Concatenate all dataframes
        processed_data = pd.concat(combined_data, ignore_index=True)
        
        # Apply business rules for billing
        processed_data = apply_billing_rules(processed_data)
        
        # Generate regional data
        region_data = generate_region_data(processed_data)
        
        # Generate job data
        job_data = generate_job_data(processed_data)
        
        # Generate cost code data
        cost_code_data = generate_cost_code_data(processed_data)
        
        # Generate asset data
        asset_data = {asset_id: row.to_dict() for asset_id, row in processed_data.iterrows()}
        
        # Generate allocation summary
        allocation_summary = generate_allocation_summary(processed_data)
        
        # Save processed data
        output_path = os.path.join(PROCESSED_FOLDER, f'april_2025_processed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        processed_data.to_csv(output_path, index=False)
        
        flash('Data processed successfully! You can now view the billing details.', 'success')
        return redirect(url_for('april_billing.index'))
    
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        flash(f'Error processing data: {str(e)}', 'error')
        return redirect(url_for('april_billing.index'))

@april_billing_bp.route('/region/<region_id>')
@login_required
def region_detail(region_id):
    """Display billing details for a specific region"""
    if processed_data is None:
        flash('No processed data available', 'error')
        return redirect(url_for('april_billing.index'))
    
    # Filter data for this region
    region_df = processed_data[processed_data['DIV'] == region_id]
    
    # Get jobs in this region
    region_jobs = region_df['JOB'].unique()
    jobs = []
    
    for job_id in region_jobs:
        job_df = region_df[region_df['JOB'] == job_id]
        job_info = {
            'job': job_id,
            'asset_count': len(job_df),
            'total_units': job_df['UNIT ALLOCATION'].sum(),
            'revised_units': job_df.apply(lambda x: x['REVISION'] if x['REVISION'] is not None else x['UNIT ALLOCATION'], axis=1).sum(),
            'cost_codes': job_df['COST CODE'].unique().tolist()
        }
        jobs.append(job_info)
    
    # Get assets by job
    jobs_with_assets = {}
    for job_id in region_jobs:
        job_df = region_df[region_df['JOB'] == job_id]
        jobs_with_assets[job_id] = job_df.to_dict('records')
    
    # Region summary
    region_summary = {
        'region_id': region_id,
        'asset_count': len(region_df),
        'job_count': len(region_jobs),
        'total_units': region_df['UNIT ALLOCATION'].sum(),
        'revised_units': region_df.apply(lambda x: x['REVISION'] if x['REVISION'] is not None else x['UNIT ALLOCATION'], axis=1).sum()
    }
    
    return render_template('billing/april_region_detail.html',
                          region_id=region_id,
                          region_summary=region_summary,
                          jobs=jobs,
                          jobs_with_assets=jobs_with_assets)

@april_billing_bp.route('/job/<job_id>')
@login_required
def job_detail(job_id):
    """Display billing details for a specific job"""
    if processed_data is None:
        flash('No processed data available', 'error')
        return redirect(url_for('april_billing.index'))
    
    # Filter data for this job
    job_df = processed_data[processed_data['JOB'] == job_id]
    
    if job_df.empty:
        flash(f'No data found for job {job_id}', 'error')
        return redirect(url_for('april_billing.index'))
    
    # Get assets grouped by cost code
    cost_codes = job_df['COST CODE'].unique()
    assets_by_cost_code = {}
    
    for cc in cost_codes:
        assets_by_cost_code[cc] = job_df[job_df['COST CODE'] == cc].to_dict('records')
    
    # Job summary
    job_summary = {
        'job': job_id,
        'region': job_df['DIV'].iloc[0],
        'asset_count': len(job_df),
        'total_units': job_df['UNIT ALLOCATION'].sum(),
        'revised_units': job_df.apply(lambda x: x['REVISION'] if x['REVISION'] is not None else x['UNIT ALLOCATION'], axis=1).sum(),
        'cost_codes': cost_codes
    }
    
    return render_template('billing/april_job_detail.html',
                          job_id=job_id,
                          job_summary=job_summary,
                          assets=job_df.to_dict('records'),
                          assets_by_cost_code=assets_by_cost_code)

@april_billing_bp.route('/cost-codes')
@login_required
def cost_code_detail():
    """Display billing details by cost code"""
    if processed_data is None:
        flash('No processed data available', 'error')
        return redirect(url_for('april_billing.index'))
    
    # Get all cost codes
    cost_codes = []
    all_cost_codes = processed_data['COST CODE'].unique()
    
    for cc in all_cost_codes:
        cc_df = processed_data[processed_data['COST CODE'] == cc]
        jobs = cc_df['JOB'].unique().tolist()
        
        original_units = cc_df['UNIT ALLOCATION'].sum()
        revised_units = cc_df.apply(lambda x: x['REVISION'] if x['REVISION'] is not None else x['UNIT ALLOCATION'], axis=1).sum()
        
        cost_code_info = {
            'cost_code': cc,
            'asset_count': len(cc_df),
            'job_count': len(jobs),
            'jobs': jobs,
            'total_units': original_units,
            'revised_units': revised_units,
            'difference': revised_units - original_units
        }
        cost_codes.append(cost_code_info)
    
    return render_template('billing/april_cost_codes.html',
                          cost_codes=cost_codes)

@april_billing_bp.route('/asset/<asset_id>')
@login_required
def asset_detail(asset_id):
    """Display billing details for a specific asset"""
    if processed_data is None:
        flash('No processed data available', 'error')
        return redirect(url_for('april_billing.index'))
    
    # Find asset in processed data
    asset_rows = processed_data[processed_data['ASSET ID'] == asset_id]
    
    if asset_rows.empty:
        flash(f'No data found for asset {asset_id}', 'error')
        return redirect(url_for('april_billing.index'))
    
    # Use the first row if multiple entries exist
    asset_data = asset_rows.iloc[0].to_dict()
    
    return render_template('billing/april_asset_detail.html',
                          asset_id=asset_id,
                          asset_data=asset_data)

@april_billing_bp.route('/export-data')
@login_required
def export_data():
    """Export processed data in various formats"""
    if processed_data is None:
        flash('No processed data available for export', 'error')
        return redirect(url_for('april_billing.index'))
    
    export_type = request.args.get('type', 'detail')
    export_format = request.args.get('format', 'xlsx')
    
    # Handle filters
    region = request.args.get('region')
    job = request.args.get('job')
    cost_code = request.args.get('cost_code')
    asset = request.args.get('asset')
    
    # Filter data based on parameters
    export_df = processed_data.copy()
    
    if region:
        export_df = export_df[export_df['DIV'] == region]
    
    if job:
        export_df = export_df[export_df['JOB'] == job]
    
    if cost_code:
        export_df = export_df[export_df['COST CODE'] == cost_code]
    
    if asset:
        export_df = export_df[export_df['ASSET ID'] == asset]
    
    # Generate appropriate filename
    filename_parts = ['april_2025']
    if region:
        filename_parts.append(f'region_{region}')
    if job:
        filename_parts.append(f'job_{job}')
    if cost_code:
        filename_parts.append(f'cc_{cost_code.replace(" ", "_")}')
    if asset:
        filename_parts.append(f'asset_{asset}')
    
    filename_parts.append(export_type)
    filename_parts.append(datetime.now().strftime('%Y%m%d_%H%M%S'))
    filename = '_'.join(filename_parts)
    
    # Create export file
    if export_type == 'foundation':
        return export_foundation_format(export_df, filename, export_format)
    else:
        return export_detail_format(export_df, filename, export_format)

def process_allocation_file(file_path, filename):
    """Process an allocation file and extract relevant data"""
    global source_data
    
    try:
        # Read the Excel file
        if file_path.endswith('.xlsx') or file_path.endswith('.xls') or file_path.endswith('.xlsm'):
            # Try to find the allocation sheet
            xl = pd.ExcelFile(file_path)
            allocation_sheet = None
            
            # Look for allocation sheet names
            allocation_keywords = ['EQ ALLOCATIONS', 'ALLOCATION', 'ALL DIV', 'ALL DIVISIONS', 'RAW DATA']
            
            for sheet in xl.sheet_names:
                if any(keyword in sheet.upper() for keyword in allocation_keywords):
                    allocation_sheet = sheet
                    break
            
            if not allocation_sheet:
                # Use the first sheet if no matching sheet name is found
                allocation_sheet = xl.sheet_names[0]
            
            # Read the allocation sheet
            df = pd.read_excel(file_path, sheet_name=allocation_sheet, header=None)
            
            # Find the header row (look for common column names)
            header_keywords = ['ASSET ID', 'EQUIPMENT', 'DRIVER', 'JOB', 'DIV', 'COST CODE', 'UNIT ALLOCATION']
            header_row = None
            
            for i in range(10):  # Check first 10 rows
                row_values = [str(val).upper() if val is not None else '' for val in df.iloc[i].values]
                if any(keyword in ' '.join(row_values) for keyword in header_keywords):
                    header_row = i
                    break
            
            if header_row is None:
                raise ValueError("Could not find header row in the allocation sheet")
            
            # Set the header and skip to data rows
            df.columns = df.iloc[header_row]
            df = df.iloc[header_row+1:].reset_index(drop=True)
            
            # Ensure required columns are present
            required_columns = ['ASSET ID', 'JOB', 'DIV', 'UNIT ALLOCATION']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                # Try to map common column names
                column_mapping = {
                    'ASSET': 'ASSET ID',
                    'ASSET NO': 'ASSET ID',
                    'EQUIPMENT NO': 'ASSET ID',
                    'DIVISION': 'DIV',
                    'UNITS': 'UNIT ALLOCATION',
                    'ALLOCATION': 'UNIT ALLOCATION',
                    'PROJECT': 'JOB',
                    'PROJECT NO': 'JOB',
                    'JOB NO': 'JOB'
                }
                
                for alt_name, std_name in column_mapping.items():
                    if std_name in missing_columns and alt_name in df.columns:
                        df.rename(columns={alt_name: std_name}, inplace=True)
                        missing_columns.remove(std_name)
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Filter out rows with missing essential data
            df = df.dropna(subset=['ASSET ID', 'JOB', 'DIV'])
            
            # Ensure numeric columns are numeric
            if 'UNIT ALLOCATION' in df.columns:
                df['UNIT ALLOCATION'] = pd.to_numeric(df['UNIT ALLOCATION'], errors='coerce')
            
            # Add revision column if not present
            if 'REVISION' not in df.columns:
                df['REVISION'] = None
            
            # Add note column if not present
            if 'NOTE / DETAIL' not in df.columns:
                df['NOTE / DETAIL'] = None
            
            # Standardize column names
            if 'COST CODE' not in df.columns:
                df['COST CODE'] = None
                
            if 'EQUIPMENT' not in df.columns:
                df['EQUIPMENT'] = df['ASSET ID']
                
            if 'DRIVER' not in df.columns:
                df['DRIVER'] = None
            
            # Store the processed data
            source_data[filename] = df
            logger.info(f"Processed allocation file {filename}: {len(df)} rows")
            
            return True
        else:
            raise ValueError("Unsupported file format. Please upload an Excel file.")
    
    except Exception as e:
        logger.error(f"Error processing allocation file {filename}: {e}")
        flash(f"Error processing file {filename}: {str(e)}", 'error')
        return False

def process_pm_file(file_path, filename):
    """Process a PM allocation file to extract revision data"""
    global source_data
    
    try:
        # Read the Excel file
        if file_path.endswith('.xlsx') or file_path.endswith('.xls') or file_path.endswith('.xlsm'):
            xl = pd.ExcelFile(file_path)
            
            # Try to identify PM allocation sheets
            pm_sheet = None
            pm_keywords = ['PM', 'REVISION', 'ALLOCATIONS', 'BILLING']
            
            for sheet in xl.sheet_names:
                if any(keyword in sheet.upper() for keyword in pm_keywords):
                    pm_sheet = sheet
                    break
            
            if not pm_sheet:
                # Use the first sheet if no matching sheet name is found
                pm_sheet = xl.sheet_names[0]
            
            # Read the PM sheet
            df = pd.read_excel(file_path, sheet_name=pm_sheet, header=None)
            
            # Find the header row (look for common column names)
            header_keywords = ['ASSET ID', 'EQUIPMENT', 'DRIVER', 'JOB', 'DIV', 'COST CODE', 'REVISION']
            header_row = None
            
            for i in range(10):  # Check first 10 rows
                row_values = [str(val).upper() if val is not None else '' for val in df.iloc[i].values]
                if any(keyword in ' '.join(row_values) for keyword in header_keywords):
                    header_row = i
                    break
            
            if header_row is None:
                raise ValueError("Could not find header row in the PM sheet")
            
            # Set the header and skip to data rows
            df.columns = df.iloc[header_row]
            df = df.iloc[header_row+1:].reset_index(drop=True)
            
            # Ensure required columns are present
            required_columns = ['ASSET ID', 'JOB', 'REVISION']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                # Try to map common column names
                column_mapping = {
                    'ASSET': 'ASSET ID',
                    'ASSET NO': 'ASSET ID',
                    'EQUIPMENT NO': 'ASSET ID',
                    'PM ALLOCATION': 'REVISION',
                    'REVISED UNITS': 'REVISION',
                    'PROJECT': 'JOB',
                    'PROJECT NO': 'JOB',
                    'JOB NO': 'JOB'
                }
                
                for alt_name, std_name in column_mapping.items():
                    if std_name in missing_columns and alt_name in df.columns:
                        df.rename(columns={alt_name: std_name}, inplace=True)
                        missing_columns.remove(std_name)
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Filter out rows with missing essential data
            df = df.dropna(subset=['ASSET ID', 'JOB'])
            
            # Ensure numeric columns are numeric
            if 'REVISION' in df.columns:
                df['REVISION'] = pd.to_numeric(df['REVISION'], errors='coerce')
            
            # Add standard columns if not present
            standard_columns = ['DIV', 'COST CODE', 'EQUIPMENT', 'DRIVER', 'UNIT ALLOCATION', 'NOTE / DETAIL']
            for col in standard_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Store the processed data
            source_data[filename] = df
            logger.info(f"Processed PM file {filename}: {len(df)} rows")
            
            return True
        else:
            raise ValueError("Unsupported file format. Please upload an Excel file.")
    
    except Exception as e:
        logger.error(f"Error processing PM file {filename}: {e}")
        flash(f"Error processing file {filename}: {str(e)}", 'error')
        return False

def apply_billing_rules(df):
    """Apply business rules for billing"""
    # 1. Ensure no asset is billed for more than 1.0 units total
    asset_units = df.groupby('ASSET ID')['UNIT ALLOCATION'].sum()
    overallocated_assets = asset_units[asset_units > 1.0].index
    
    if not overallocated_assets.empty:
        logger.info(f"Found {len(overallocated_assets)} over-allocated assets")
        
        # Adjust allocations for overallocated assets
        for asset in overallocated_assets:
            asset_rows = df[df['ASSET ID'] == asset]
            total_units = asset_rows['UNIT ALLOCATION'].sum()
            
            # Scale down each allocation proportionally
            for idx in asset_rows.index:
                original_units = df.at[idx, 'UNIT ALLOCATION']
                df.at[idx, 'UNIT ALLOCATION'] = original_units / total_units
                
                # Add a note about adjustment
                if pd.isna(df.at[idx, 'NOTE / DETAIL']) or df.at[idx, 'NOTE / DETAIL'] is None:
                    df.at[idx, 'NOTE / DETAIL'] = f"Auto-adjusted from {original_units:.2f} to {df.at[idx, 'UNIT ALLOCATION']:.2f}"
                else:
                    df.at[idx, 'NOTE / DETAIL'] += f"; Auto-adjusted from {original_units:.2f} to {df.at[idx, 'UNIT ALLOCATION']:.2f}"
    
    # 2. Handle cost codes based on job numbers
    for idx, row in df.iterrows():
        job_id = row['JOB']
        
        # Check if the cost code is missing or needs adjustment
        if pd.isna(row['COST CODE']) or row['COST CODE'] is None:
            # Legacy jobs (< 2023-014) always use 9000 100M
            if job_id.startswith(('2021-', '2022-')) or (job_id.startswith('2023-') and int(job_id.split('-')[1]) < 14):
                df.at[idx, 'COST CODE'] = '9000 100M'
            else:
                # Other jobs use fallback 9000 100F
                df.at[idx, 'COST CODE'] = '9000 100F'
    
    # 3. Apply PM revisions when present
    df['REVISION'] = df['REVISION'].fillna(df['UNIT ALLOCATION'])
    
    return df

def generate_region_data(df):
    """Generate regional summary data"""
    regions = {}
    for div, div_df in df.groupby('DIV'):
        regions[div] = {
            'region_id': div,
            'asset_count': len(div_df['ASSET ID'].unique()),
            'job_count': len(div_df['JOB'].unique()),
            'total_units': div_df['UNIT ALLOCATION'].sum(),
            'revised_units': div_df['REVISION'].sum(),
            'jobs': div_df['JOB'].unique().tolist()
        }
    return regions

def generate_job_data(df):
    """Generate job summary data"""
    jobs = {}
    for job, job_df in df.groupby('JOB'):
        jobs[job] = {
            'job_id': job,
            'region': job_df['DIV'].iloc[0],
            'asset_count': len(job_df['ASSET ID'].unique()),
            'cost_code_count': len(job_df['COST CODE'].unique()),
            'total_units': job_df['UNIT ALLOCATION'].sum(),
            'revised_units': job_df['REVISION'].sum(),
            'cost_codes': job_df['COST CODE'].unique().tolist()
        }
    return jobs

def generate_cost_code_data(df):
    """Generate cost code summary data"""
    cost_codes = {}
    for cc, cc_df in df.groupby('COST CODE'):
        cost_codes[cc] = {
            'cost_code': cc,
            'asset_count': len(cc_df['ASSET ID'].unique()),
            'job_count': len(cc_df['JOB'].unique()),
            'jobs': cc_df['JOB'].unique().tolist(),
            'total_units': cc_df['UNIT ALLOCATION'].sum(),
            'revised_units': cc_df['REVISION'].sum(),
            'difference': cc_df['REVISION'].sum() - cc_df['UNIT ALLOCATION'].sum()
        }
    return cost_codes

def generate_allocation_summary(df):
    """Generate overall allocation summary statistics"""
    return {
        'asset_count': len(df['ASSET ID'].unique()),
        'job_count': len(df['JOB'].unique()),
        'region_count': len(df['DIV'].unique()),
        'cost_code_count': len(df['COST CODE'].unique()),
        'total_units': df['UNIT ALLOCATION'].sum(),
        'revised_units': df['REVISION'].sum(),
        'difference': df['REVISION'].sum() - df['UNIT ALLOCATION'].sum(),
        'percent_change': ((df['REVISION'].sum() - df['UNIT ALLOCATION'].sum()) / df['UNIT ALLOCATION'].sum()) * 100 if df['UNIT ALLOCATION'].sum() > 0 else 0,
        'overallocated_assets': len(df.groupby('ASSET ID')['UNIT ALLOCATION'].sum()[df.groupby('ASSET ID')['UNIT ALLOCATION'].sum() > 1.0]),
        'revision_count': len(df[df['REVISION'] != df['UNIT ALLOCATION']])
    }

def export_detail_format(df, filename, format):
    """Export data in detailed format"""
    temp_dir = tempfile.mkdtemp()
    if format == 'csv':
        output_path = os.path.join(temp_dir, f'{filename}.csv')
        df.to_csv(output_path, index=False)
        return send_file(output_path, as_attachment=True, download_name=f'{filename}.csv')
    else:
        output_path = os.path.join(temp_dir, f'{filename}.xlsx')
        with pd.ExcelWriter(output_path) as writer:
            df.to_excel(writer, sheet_name='Detail', index=False)
        return send_file(output_path, as_attachment=True, download_name=f'{filename}.xlsx')

def export_foundation_format(df, filename, format):
    """Export data in Foundation software compatible format"""
    # Create a new dataframe with the required Foundation format
    foundation_df = pd.DataFrame()
    foundation_df['Job'] = df['JOB']
    foundation_df['Cost Code'] = df['COST CODE']
    foundation_df['Equipment'] = df['EQUIPMENT']
    
    # Use revised units when available, otherwise use original allocation
    foundation_df['Units'] = df.apply(lambda x: x['REVISION'] if x['REVISION'] is not None else x['UNIT ALLOCATION'], axis=1)
    
    temp_dir = tempfile.mkdtemp()
    if format == 'csv':
        output_path = os.path.join(temp_dir, f'{filename}.csv')
        foundation_df.to_csv(output_path, index=False, header=False)
        return send_file(output_path, as_attachment=True, download_name=f'{filename}.csv')
    else:
        output_path = os.path.join(temp_dir, f'{filename}.xlsx')
        with pd.ExcelWriter(output_path) as writer:
            foundation_df.to_excel(writer, sheet_name='FSI Import', index=False, header=False)
        return send_file(output_path, as_attachment=True, download_name=f'{filename}.xlsx')

def get_uploaded_files():
    """Get list of uploaded files"""
    return list(source_data.keys())

def get_billing_summary():
    """Get overall billing summary for dashboard"""
    if processed_data is None:
        return None
    
    return {
        'asset_count': len(processed_data['ASSET ID'].unique()),
        'job_count': len(processed_data['JOB'].unique()),
        'region_count': len(processed_data['DIV'].unique()),
        'cost_code_count': len(processed_data['COST CODE'].unique()),
        'total_units': processed_data['UNIT ALLOCATION'].sum(),
        'revised_units': processed_data.apply(lambda x: x['REVISION'] if x['REVISION'] is not None else x['UNIT ALLOCATION'], axis=1).sum(),
        'regions': processed_data['DIV'].unique().tolist(),
        'jobs': processed_data['JOB'].unique().tolist()
    }