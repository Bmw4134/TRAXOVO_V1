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

def process_large_csv_in_chunks(file_path, chunksize=10000):
    """Process large CSV files in chunks to avoid memory issues"""
    chunks = []
    try:
        # Read the CSV in chunks
        for chunk in pd.read_csv(file_path, chunksize=chunksize, low_memory=False):
            # Process each chunk and store the result
            chunks.append(chunk)
        
        # Combine all processed chunks
        return pd.concat(chunks, ignore_index=True)
    except Exception as e:
        logger.error(f"Error processing CSV in chunks: {str(e)}")
        return None

def process_large_xlsx_in_chunks(file_path, sheet_name=0, chunksize=10000):
    """Process large Excel files in chunks using openpyxl"""
    try:
        # Get sheet names
        xls = pd.ExcelFile(file_path)
        if isinstance(sheet_name, int):
            sheet_name = xls.sheet_names[sheet_name]
        
        # Read the Excel file with optimized parameters
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine='openpyxl'
        )
        
        return df
    except Exception as e:
        logger.error(f"Error processing Excel in chunks: {str(e)}")
        return None

def extract_billing_data_from_driving_history(file_path):
    """Extract billing data from driving history CSV"""
    try:
        # Process CSV in chunks
        df = process_large_csv_in_chunks(file_path)
        
        if df is None:
            return None
            
        # Keep only relevant columns
        if 'Contact' in df.columns and 'Location' in df.columns:
            # Focus on rows with driver location info
            filtered_df = df[df['Location'].notna()]
            
            # Create derived columns for billing
            filtered_df['Date'] = pd.to_datetime(filtered_df['EventDateTime']).dt.date if 'EventDateTime' in df.columns else None
            filtered_df['Driver'] = filtered_df['Contact']
            filtered_df['Job Site'] = filtered_df['Location'].apply(lambda x: x.split(',')[0] if isinstance(x, str) and ',' in x else x)
            
            # Store driver-job site relationships
            logger.info(f"Extracted {len(filtered_df)} driving records from {file_path}")
            return filtered_df
        else:
            logger.error(f"Required columns not found in driving history file")
            return None
    except Exception as e:
        logger.error(f"Error extracting billing data from driving history: {str(e)}")
        return None

def extract_billing_data_from_daily_usage(file_path):
    """Extract billing data from daily usage CSV"""
    try:
        # Process CSV in chunks
        df = process_large_csv_in_chunks(file_path)
        
        if df is None:
            return None
            
        # Keep only relevant columns
        if 'AssetLabel' in df.columns and 'Date' in df.columns:
            # Create derived columns for billing
            filtered_df = df[df['AssetLabel'].notna()]
            
            # Extract asset and driver info
            filtered_df['Asset ID'] = filtered_df['AssetLabel'].apply(
                lambda x: x.split(' - ')[0].strip() if isinstance(x, str) and ' - ' in x else x
            )
            filtered_df['Driver'] = filtered_df['AssetLabel'].apply(
                lambda x: x.split(' - ')[1].strip() if isinstance(x, str) and ' - ' in x and len(x.split(' - ')) > 1 else ''
            )
            
            # Convert engine hours to decimal for billing
            if 'Engine1Hours' in filtered_df.columns:
                filtered_df['Hours'] = pd.to_numeric(filtered_df['Engine1Hours'], errors='coerce')
            
            logger.info(f"Extracted {len(filtered_df)} daily usage records from {file_path}")
            return filtered_df
        else:
            logger.error(f"Required columns not found in daily usage file")
            return None
    except Exception as e:
        logger.error(f"Error extracting billing data from daily usage: {str(e)}")
        return None

def extract_billing_data_from_assets_time(file_path):
    """Extract billing data from assets time on site CSV"""
    try:
        # Process CSV in chunks
        df = process_large_csv_in_chunks(file_path)
        
        if df is None:
            return None
            
        # Keep only relevant columns
        if 'Location' in df.columns and 'Asset' in df.columns:
            # Create derived columns for billing
            filtered_df = df[df['Location'].notna() & df['Asset'].notna()]
            
            # Extract job site from location
            filtered_df['Job Site'] = filtered_df['Location'].astype(str)
            
            # Extract asset ID from asset field
            filtered_df['Asset ID'] = filtered_df['Asset'].apply(
                lambda x: x.split(' ')[0].strip() if isinstance(x, str) and ' ' in x else x
            )
            
            # Calculate time on site as hours
            if 'TimeOnSite' in filtered_df.columns:
                filtered_df['Hours on Site'] = filtered_df['TimeOnSite'].apply(
                    lambda x: float(x.split(':')[0]) + float(x.split(':')[1])/60 
                    if isinstance(x, str) and ':' in x else 0
                )
            
            logger.info(f"Extracted {len(filtered_df)} asset time records from {file_path}")
            return filtered_df
        else:
            logger.error(f"Required columns not found in assets time file")
            return None
    except Exception as e:
        logger.error(f"Error extracting billing data from assets time: {str(e)}")
        return None

def process_timecards_file(file_path):
    """Process timecards Excel file"""
    try:
        # Use chunk processing for Excel
        df = process_large_xlsx_in_chunks(file_path)
        
        if df is None:
            return None
            
        # Check for expected columns
        required_columns = ['Employee ID', 'Name', 'Job', 'Date', 'Hours']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns in timecards: {missing_columns}")
            return None
            
        # Create processed dataframe with standardized columns
        processed_df = pd.DataFrame({
            'Employee ID': df['Employee ID'],
            'Name': df['Name'],
            'Job Number': df['Job'],
            'Date': pd.to_datetime(df['Date']),
            'Hours': df['Hours']
        })
        
        # Store in source data
        source_data['timecards'] = processed_df
        logger.info(f"Processed {len(processed_df)} timecard records")
        return processed_df
    except Exception as e:
        logger.error(f"Error processing timecards: {str(e)}")
        return None

def process_activity_detail_file(file_path):
    """Process large activity detail file in chunks"""
    try:
        # For very large files, use chunked processing
        df = process_large_csv_in_chunks(file_path, chunksize=5000)
        
        if df is None:
            logger.error("Failed to process activity detail file")
            return None
            
        # Keep only essential columns for billing
        essential_columns = [col for col in df.columns if any(
            key in col.lower() for key in ['asset', 'driver', 'job', 'site', 'time', 'date', 'hour', 'locat']
        )]
        
        if not essential_columns:
            essential_columns = df.columns[:20]  # Take first 20 columns if no match
        
        filtered_df = df[essential_columns].copy()
        
        # Store in source data - use smaller subset to avoid memory issues
        source_data['activity_detail'] = filtered_df.head(10000)  # Store only first 10000 rows in memory
        
        # Save full processed file for later access
        processed_file_path = os.path.join(PROCESSED_FOLDER, 'activity_detail_processed.csv')
        filtered_df.to_csv(processed_file_path, index=False)
        
        logger.info(f"Processed activity detail with {len(filtered_df)} records. Saved to {processed_file_path}")
        return True
    except Exception as e:
        logger.error(f"Error processing activity detail: {str(e)}")
        return None

def get_uploaded_files():
    """Get list of all uploaded files"""
    files = []
    
    for file_type, file_data in source_data.items():
        if file_data is not None:
            if isinstance(file_data, pd.DataFrame):
                row_count = len(file_data)
                files.append({
                    'name': file_type,
                    'type': 'DataFrame',
                    'records': row_count,
                    'status': 'Processed'
                })
            elif isinstance(file_data, bool) and file_data:
                files.append({
                    'name': file_type,
                    'type': 'Large File',
                    'records': 'N/A - Saved to disk',
                    'status': 'Processed'
                })
    
    # Check for processed allocation file
    if processed_data is not None:
        files.append({
            'name': 'master_allocation',
            'type': 'Processed Data',
            'records': len(processed_data),
            'status': 'Ready for Export'
        })
    
    # Add check for disk-saved files
    for file in os.listdir(PROCESSED_FOLDER):
        if file.endswith('.csv') and not any(f['name'] == file for f in files):
            files.append({
                'name': file,
                'type': 'Processed File',
                'records': 'Stored on disk',
                'status': 'Available'
            })
    
    return files

def get_billing_summary():
    """Get summary of billing data for dashboard"""
    if processed_data is None:
        return None
        
    summary = {
        'total_assets': len(processed_data['Asset ID'].unique()),
        'total_jobs': len(processed_data['Job'].unique()),
        'total_drivers': len(processed_data['Driver'].unique()) if 'Driver' in processed_data.columns else 0,
        'total_allocations': len(processed_data),
        'division_counts': {},
        'region_totals': {}
    }
    
    # Calculate division counts
    if 'Division' in processed_data.columns:
        division_counts = processed_data['Division'].value_counts().to_dict()
        summary['division_counts'] = division_counts
    
    # Calculate region totals (amount by region)
    if 'Region' in processed_data.columns and 'Amount' in processed_data.columns:
        region_totals = processed_data.groupby('Region')['Amount'].sum().to_dict()
        summary['region_totals'] = region_totals
    
    return summary

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
        processing_success = False
        
        # Handle different file types
        if 'timecard' in file_type.lower() or 'timecard' in filename.lower():
            # Process timecards
            result = process_timecards_file(file_path)
            processing_success = result is not None
            file_type = 'timecards'
            
        elif 'daily_usage' in file_type.lower() or 'dailyusage' in filename.lower():
            # Process daily usage
            df = extract_billing_data_from_daily_usage(file_path)
            source_data['daily_usage'] = df
            processing_success = df is not None
            file_type = 'daily_usage'
            
        elif 'driving' in file_type.lower() or 'driving' in filename.lower():
            # Process driving history
            df = extract_billing_data_from_driving_history(file_path)
            source_data['driving_history'] = df
            processing_success = df is not None
            file_type = 'driving_history'
            
        elif 'assets_time' in file_type.lower() or 'timeonsite' in filename.lower():
            # Process assets time on site
            df = extract_billing_data_from_assets_time(file_path)
            source_data['assets_time'] = df
            processing_success = df is not None
            file_type = 'assets_time'
            
        elif 'activity' in file_type.lower() or 'activity' in filename.lower():
            # Process activity detail (large file)
            result = process_activity_detail_file(file_path)
            processing_success = result is not None
            file_type = 'activity_detail'
            
        elif 'allocation' in file_type.lower() or 'ragle' in filename.lower():
            # Process RAGLE allocation file
            result = process_allocation_file(file_path)
            processing_success = result is not None
            file_type = 'allocations'
            
        elif 'pm' in file_type.lower() or 'revision' in filename.lower():
            # Process PM revision file
            result = process_pm_file(file_path)
            processing_success = result is not None
            file_type = 'pm_revisions'
            
        else:
            # Attempt auto-detection based on file extension and content
            logger.info(f"Attempting to auto-detect file type for {filename}")
            if filename.lower().endswith('.xlsx'):
                # Try to read as Excel and detect based on content
                try:
                    df = pd.read_excel(file_path, nrows=10)
                    columns = set(df.columns.str.lower())
                    
                    if any(col in columns for col in ['employee id', 'name', 'job']):
                        result = process_timecards_file(file_path)
                        processing_success = result is not None
                        file_type = 'timecards'
                    elif any(col in columns for col in ['allocation', 'unit', 'cost code']):
                        result = process_allocation_file(file_path)
                        processing_success = result is not None
                        file_type = 'allocations'
                    elif any(col in columns for col in ['revision', 'pm']):
                        result = process_pm_file(file_path)
                        processing_success = result is not None
                        file_type = 'pm_revisions'
                    else:
                        flash(f'Could not auto-detect file type for {filename}. Please specify file type.', 'warning')
                        return redirect(url_for('april_billing.index'))
                        
                except Exception as e:
                    logger.error(f"Error auto-detecting Excel file type: {str(e)}")
                    flash(f'Error processing file: {str(e)}', 'error')
                    return redirect(url_for('april_billing.index'))
                    
            elif filename.lower().endswith('.csv'):
                # Try to read as CSV and detect based on content
                try:
                    df = pd.read_csv(file_path, nrows=10)
                    columns = set(df.columns.str.lower())
                    
                    if any(col in columns for col in ['contact', 'location', 'eventdatetime']):
                        df = extract_billing_data_from_driving_history(file_path)
                        source_data['driving_history'] = df
                        processing_success = df is not None
                        file_type = 'driving_history'
                    elif any(col in columns for col in ['assetlabel', 'engine1hours']):
                        df = extract_billing_data_from_daily_usage(file_path)
                        source_data['daily_usage'] = df
                        processing_success = df is not None
                        file_type = 'daily_usage'
                    elif any(col in columns for col in ['timeonsite', 'asset']):
                        df = extract_billing_data_from_assets_time(file_path)
                        source_data['assets_time'] = df
                        processing_success = df is not None
                        file_type = 'assets_time'
                    elif any(col in columns for col in ['activity']):
                        result = process_activity_detail_file(file_path)
                        processing_success = result is not None
                        file_type = 'activity_detail'
                    else:
                        flash(f'Could not auto-detect file type for {filename}. Please specify file type.', 'warning')
                        return redirect(url_for('april_billing.index'))
                        
                except Exception as e:
                    logger.error(f"Error auto-detecting CSV file type: {str(e)}")
                    flash(f'Error processing file: {str(e)}', 'error')
                    return redirect(url_for('april_billing.index'))
            else:
                flash(f'Unsupported file type: {os.path.splitext(filename)[1]}', 'error')
                return redirect(url_for('april_billing.index'))
        
        if processing_success:
            flash(f'File {filename} uploaded and processed successfully as {file_type}!', 'success')
        else:
            flash(f'File uploaded but processing failed. Check logs for details.', 'error')
            
        return redirect(url_for('april_billing.index'))

@april_billing_bp.route('/process', methods=['POST'])
@login_required
def process_data():
    """Process uploaded data and generate billing allocations"""
    global processed_data, region_data, job_data, cost_code_data, asset_data, allocation_summary
    
    # Check if required source data is available
    missing_key_data = True
    for key_type in ['assets_time', 'daily_usage', 'driving_history']:
        if source_data.get(key_type) is not None:
            missing_key_data = False
            break
            
    if missing_key_data:
        flash('Missing required data sources. Please upload at least one of: Assets Time on Site, Daily Usage, or Driving History', 'error')
        return redirect(url_for('april_billing.index'))
    
    logger.info("Starting processing of April billing data")
    
    try:
        # 1. Create a master DataFrame with assets and their job allocations
        asset_jobs = pd.DataFrame()
        
        # Extract asset-job relationships from assets_time_on_site
        if source_data.get('assets_time') is not None:
            assets_df = source_data['assets_time']
            if isinstance(assets_df, pd.DataFrame) and len(assets_df) > 0:
                asset_job_df = assets_df[['Asset ID', 'Job Site', 'Hours on Site']].drop_duplicates()
                asset_job_df.rename(columns={'Job Site': 'Location'}, inplace=True)
                
                # Add to master dataframe
                asset_jobs = pd.concat([asset_jobs, asset_job_df], ignore_index=True)
                logger.info(f"Added {len(asset_job_df)} asset-job relationships from assets time data")
        
        # Extract asset info from daily_usage
        if source_data.get('daily_usage') is not None:
            daily_df = source_data['daily_usage']
            if isinstance(daily_df, pd.DataFrame) and len(daily_df) > 0:
                if 'Asset ID' in daily_df.columns and 'Driver' in daily_df.columns:
                    assets_usage_df = daily_df[['Asset ID', 'Driver']].drop_duplicates()
                    
                    # Add hours if available
                    if 'Hours' in daily_df.columns:
                        assets_usage_df['Hours'] = daily_df['Hours']
                    
                    # Merge with asset_jobs
                    if len(asset_jobs) > 0:
                        asset_jobs = asset_jobs.merge(
                            assets_usage_df, on='Asset ID', how='outer'
                        )
                    else:
                        asset_jobs = assets_usage_df.copy()
                        
                    logger.info(f"Added driver data for {len(assets_usage_df)} assets")
        
        # Extract driver-job relationships from driving_history
        if source_data.get('driving_history') is not None:
            driving_df = source_data['driving_history']
            if isinstance(driving_df, pd.DataFrame) and len(driving_df) > 0:
                if 'Driver' in driving_df.columns and 'Job Site' in driving_df.columns:
                    driver_job_df = driving_df[['Driver', 'Job Site']].drop_duplicates()
                    driver_job_df.rename(columns={'Job Site': 'Location'}, inplace=True)
                    
                    # If we have asset_jobs data but missing driver info, try to add it
                    if len(asset_jobs) > 0:
                        # For assets without driver info
                        if 'Driver' not in asset_jobs.columns:
                            asset_jobs['Driver'] = None
                            
                        # Match by location where possible
                        asset_jobs = asset_jobs.merge(
                            driver_job_df, on='Location', how='left', suffixes=('', '_driver')
                        )
                        
                        # Fill in missing driver info
                        mask = asset_jobs['Driver'].isna() & asset_jobs['Driver_driver'].notna()
                        asset_jobs.loc[mask, 'Driver'] = asset_jobs.loc[mask, 'Driver_driver']
                        
                        # Drop extra column
                        if 'Driver_driver' in asset_jobs.columns:
                            asset_jobs.drop('Driver_driver', axis=1, inplace=True)
                    else:
                        # Just keep the driver-location mapping for later
                        asset_jobs = driver_job_df.copy()
                        
                    logger.info(f"Added driver information from {len(driver_job_df)} driving records")
        
        # Load equipment data if available (for rates and equipment info)
        equipment_rates = {}
        if source_data.get('allocations') is not None:
            allocation_df = source_data['allocations']
            if isinstance(allocation_df, pd.DataFrame) and len(allocation_df) > 0:
                if 'Asset ID' in allocation_df.columns:
                    # Check for rate column with different possible names
                    rate_col = None
                    for col in ['Rate', 'RATE', 'Monthly Rate', 'Daily Rate']:
                        if col in allocation_df.columns:
                            rate_col = col
                            break
                    
                    # Check for equipment column with different possible names
                    equip_col = None
                    for col in ['Equipment', 'EQUIPMENT', 'Description', 'Asset Description']:
                        if col in allocation_df.columns:
                            equip_col = col
                            break
                    
                    # Extract equipment info
                    if rate_col or equip_col:
                        for _, row in allocation_df.iterrows():
                            asset_id = row['Asset ID']
                            equipment_rates[asset_id] = {}
                            
                            if rate_col:
                                equipment_rates[asset_id]['Rate'] = row[rate_col]
                            
                            if equip_col:
                                equipment_rates[asset_id]['Equipment'] = row[equip_col]
                        
                        logger.info(f"Loaded info for {len(equipment_rates)} equipment types")
        
        # 2. Process asset-job data to create allocations
        if len(asset_jobs) > 0:
            # Ensure we have required columns
            for col in ['Asset ID', 'Location', 'Driver']:
                if col not in asset_jobs.columns:
                    asset_jobs[col] = None
            
            # Fill missing values
            asset_jobs['Driver'] = asset_jobs['Driver'].fillna('Unassigned')
            asset_jobs['Location'] = asset_jobs['Location'].fillna('Unknown Site')
            
            # Handle hours data
            if 'Hours on Site' in asset_jobs.columns:
                asset_jobs['Hours on Site'] = pd.to_numeric(asset_jobs['Hours on Site'], errors='coerce').fillna(0)
            else:
                asset_jobs['Hours on Site'] = 0
                
            if 'Hours' in asset_jobs.columns:
                asset_jobs['Hours'] = pd.to_numeric(asset_jobs['Hours'], errors='coerce').fillna(0)
            else:
                asset_jobs['Hours'] = asset_jobs['Hours on Site']
            
            # Make sure Hours has some value for allocation
            asset_jobs.loc[asset_jobs['Hours'] == 0, 'Hours'] = 1.0  # Default to 1 hour if no data
            
            # Group by Asset ID and calculate total hours
            asset_totals = asset_jobs.groupby('Asset ID')['Hours'].sum().reset_index()
            asset_totals.rename(columns={'Hours': 'Total Hours'}, inplace=True)
            
            # Merge back to get percentage
            asset_jobs = asset_jobs.merge(asset_totals, on='Asset ID', how='left')
            
            # Calculate allocation units based on hours percentage
            asset_jobs['Units'] = asset_jobs.apply(
                lambda row: min(1.0, row['Hours'] / row['Total Hours']) if row['Total Hours'] > 0 else 0,
                axis=1
            )
            
            # Add rate and equipment info
            asset_jobs['Rate'] = asset_jobs['Asset ID'].apply(
                lambda x: equipment_rates.get(x, {}).get('Rate', 75.0)  # Default rate
            )
            
            asset_jobs['Equipment'] = asset_jobs['Asset ID'].apply(
                lambda x: equipment_rates.get(x, {}).get('Equipment', f"Equipment {x}")  # Default equipment name
            )
            
            # Calculate amount
            asset_jobs['Amount'] = asset_jobs['Units'] * asset_jobs['Rate']
            
            # Add region and division based on location
            def assign_region(location):
                if pd.isna(location) or not isinstance(location, str):
                    return 'DFW'  # Default region
                location = location.upper()
                if 'HOUSTON' in location or 'HOU' in location:
                    return 'HOU'
                elif 'WEST' in location or 'WT' in location:
                    return 'WT'
                else:
                    return 'DFW'
                    
            def assign_division(location):
                if pd.isna(location) or not isinstance(location, str):
                    return 'HWY'  # Default division
                location = location.upper()
                if 'UTILITY' in location or 'UTL' in location:
                    return 'UTL'
                else:
                    return 'HWY'
                    
            asset_jobs['Region'] = asset_jobs['Location'].apply(assign_region)
            asset_jobs['Division'] = asset_jobs['Location'].apply(assign_division)
            
            # Extract job number from location if possible
            def extract_job_number(location):
                if pd.isna(location) or not isinstance(location, str):
                    return '2024-001'  # Default job
                
                # Look for patterns like 2023-012, 2024-001, etc.
                import re
                job_match = re.search(r'(20\d{2}-\d{3})', location)
                if job_match:
                    return job_match.group(1)
                else:
                    # Generate a job number based on location
                    region = assign_region(location)
                    return f"{region}-{abs(hash(location)) % 1000:03d}"
                    
            asset_jobs['Job'] = asset_jobs['Location'].apply(extract_job_number)
            
            # Apply cost code rules:
            # Legacy jobs (< 2023-014) always use 9000 100M
            # Other jobs use PM revisions or fall back to 9000 100F
            def assign_cost_code(job):
                if pd.isna(job) or not isinstance(job, str):
                    return '9000 100F'  # Default cost code
                
                # Check if it's a legacy job (< 2023-014)
                if job.startswith('20'):
                    parts = job.split('-')
                    if len(parts) == 2:
                        try:
                            year = int(parts[0])
                            job_num = int(parts[1])
                            if year < 2023 or (year == 2023 and job_num < 14):
                                return '9000 100M'
                        except ValueError:
                            pass
                
                # Default for newer jobs
                return '9000 100F'
                
            asset_jobs['Cost Code'] = asset_jobs['Job'].apply(assign_cost_code)
            
            # Apply PM revisions if available
            if source_data.get('pm_revisions') is not None:
                pm_df = source_data['pm_revisions']
                if isinstance(pm_df, pd.DataFrame) and len(pm_df) > 0:
                    if 'Job' in pm_df.columns and 'Cost Code' in pm_df.columns and 'Asset ID' in pm_df.columns:
                        # Create a unique key for joining
                        pm_df['join_key'] = pm_df['Job'] + '_' + pm_df['Asset ID']
                        asset_jobs['join_key'] = asset_jobs['Job'] + '_' + asset_jobs['Asset ID']
                        
                        # Merge PM revision data
                        asset_jobs = asset_jobs.merge(
                            pm_df[['join_key', 'Cost Code', 'Units']],
                            on='join_key',
                            how='left',
                            suffixes=('', '_revision')
                        )
                        
                        # Apply PM revisions where available
                        if 'Units_revision' in asset_jobs.columns:
                            mask = asset_jobs['Units_revision'].notna()
                            asset_jobs.loc[mask, 'Units'] = asset_jobs.loc[mask, 'Units_revision']
                            asset_jobs.drop('Units_revision', axis=1, inplace=True)
                            
                        if 'Cost Code_revision' in asset_jobs.columns:
                            mask = asset_jobs['Cost Code_revision'].notna()
                            asset_jobs.loc[mask, 'Cost Code'] = asset_jobs.loc[mask, 'Cost Code_revision']
                            asset_jobs.drop('Cost Code_revision', axis=1, inplace=True)
                        
                        # Clean up
                        asset_jobs.drop('join_key', axis=1, inplace=True)
                        
                        logger.info("Applied PM revisions to allocations")
            
            # Apply billing rules: no asset may be billed for more than 1.0 units total
            over_allocated = []
            for asset_id, group in asset_jobs.groupby('Asset ID'):
                total_units = group['Units'].sum()
                if total_units > 1.0:
                    over_allocated.append(asset_id)
            
            # Fix over-allocated assets
            if over_allocated:
                logger.info(f"Fixing {len(over_allocated)} over-allocated assets")
                for asset_id in over_allocated:
                    mask = asset_jobs['Asset ID'] == asset_id
                    asset_rows = asset_jobs[mask].copy()
                    
                    # Scale down units proportionally
                    total_units = asset_rows['Units'].sum()
                    scale_factor = 1.0 / total_units
                    asset_jobs.loc[mask, 'Units'] = asset_jobs.loc[mask, 'Units'] * scale_factor
                    
                    # Recalculate amounts
                    asset_jobs.loc[mask, 'Amount'] = asset_jobs.loc[mask, 'Units'] * asset_jobs.loc[mask, 'Rate']
            
            # Set up processed data
            processed_data = asset_jobs.copy()
            
            # Ensure we have all required columns for the deliverables
            required_columns = [
                'Region', 'Division', 'Job', 'Asset ID', 'Equipment', 
                'Driver', 'Rate', 'Units', 'Amount', 'Cost Code'
            ]
            
            for col in required_columns:
                if col not in processed_data.columns:
                    processed_data[col] = ''
            
            # Generate region data
            region_data = generate_region_data(processed_data)
            
            # Generate job data
            job_data = generate_job_data(processed_data)
            
            # Generate cost code data
            cost_code_data = generate_cost_code_data(processed_data)
            
            # Generate asset data dictionary
            asset_data = {}
            for asset_id in processed_data['Asset ID'].unique():
                asset_data[asset_id] = processed_data[processed_data['Asset ID'] == asset_id].to_dict('records')
            
            # Generate allocation summary
            allocation_summary = generate_allocation_summary(processed_data)
            
            # Save processed data
            output_path = os.path.join(PROCESSED_FOLDER, f'april_2025_processed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            processed_data.to_csv(output_path, index=False)
            
            logger.info(f"Created billing allocations for {len(processed_data)} records")
            flash('Billing data processed successfully! You can now view the billing details and generate exports.', 'success')
            
        else:
            # If no asset-job data, create empty processed data
            processed_data = pd.DataFrame(columns=[
                'Region', 'Division', 'Job', 'Asset ID', 'Equipment', 
                'Driver', 'Rate', 'Units', 'Amount', 'Cost Code'
            ])
            
            flash('No asset-job relationships found in the uploaded files. Please check file contents.', 'warning')
            
        return redirect(url_for('april_billing.index'))
        
    except Exception as e:
        logger.error(f"Error processing billing data: {str(e)}")
        flash(f'Error processing billing data: {str(e)}', 'error')
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
        if 'Region' in export_df.columns:
            export_df = export_df[export_df['Region'] == region]
        elif 'DIV' in export_df.columns:
            export_df = export_df[export_df['DIV'] == region]
    
    if job:
        if 'Job' in export_df.columns:
            export_df = export_df[export_df['Job'] == job]
        elif 'JOB' in export_df.columns:
            export_df = export_df[export_df['JOB'] == job]
    
    if cost_code:
        if 'Cost Code' in export_df.columns:
            export_df = export_df[export_df['Cost Code'] == cost_code]
        elif 'COST CODE' in export_df.columns:
            export_df = export_df[export_df['COST CODE'] == cost_code]
    
    if asset:
        if 'Asset ID' in export_df.columns:
            export_df = export_df[export_df['Asset ID'] == asset]
        elif 'ASSET ID' in export_df.columns:
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
        # For Foundation format exports we need to ensure proper column names
        # since the export function expects specific column names
        column_mapping = {
            'Job': 'JOB', 'job': 'JOB', 'JOB': 'JOB',
            'Cost Code': 'COST CODE', 'cost_code': 'COST CODE', 'COST CODE': 'COST CODE',
            'Asset ID': 'ASSET ID', 'asset_id': 'ASSET ID', 'ASSET ID': 'ASSET ID',
            'Equipment': 'EQUIPMENT', 'equipment': 'EQUIPMENT', 'EQUIPMENT': 'EQUIPMENT',
            'Units': 'UNITS', 'units': 'UNITS', 'UNITS': 'UNITS',
            'Amount': 'AMOUNT', 'amount': 'AMOUNT', 'AMOUNT': 'AMOUNT',
            'Region': 'REGION', 'region': 'REGION', 'REGION': 'REGION',
            'Driver': 'DRIVER', 'driver': 'DRIVER', 'DRIVER': 'DRIVER'
        }
        
        # Rename columns based on mapping
        for old_col, new_col in column_mapping.items():
            if old_col in export_df.columns:
                export_df = export_df.rename(columns={old_col: new_col})
        
        # Make sure required columns exist
        for required_col in ['JOB', 'COST CODE', 'ASSET ID', 'EQUIPMENT', 'UNITS', 'AMOUNT']:
            if required_col not in export_df.columns:
                if required_col == 'UNITS' and 'Units' in export_df.columns:
                    export_df['UNITS'] = export_df['Units']
                elif required_col == 'AMOUNT' and 'Amount' in export_df.columns:
                    export_df['AMOUNT'] = export_df['Amount']
                else:
                    # Add empty column if missing
                    export_df[required_col] = ''
        
        # Extract only the required columns for Foundation export
        foundation_df = export_df[['JOB', 'COST CODE', 'ASSET ID', 'EQUIPMENT', 'UNITS', 'AMOUNT']]
        
        # Convert numeric columns to ensure proper calculations
        foundation_df['UNITS'] = pd.to_numeric(foundation_df['UNITS'], errors='coerce').fillna(0)
        foundation_df['AMOUNT'] = pd.to_numeric(foundation_df['AMOUNT'], errors='coerce').fillna(0)
        
        # Add region code for FSI export
        region_code = region if region else 'DFW'  # Default to DFW if no specific region filter
        
        # Use the export function to generate FSI format
        return export_fsi_format(
            df=foundation_df,
            region=region_code,
            month=MONTH_NAME,
            year=YEAR,
            subfolder='april_billing/foundation'
        )
    else:
        # For detail format, we don't need to reshape the data as much
        title = f"April 2025 Billing Detail"
        if region:
            title += f" - Region {region}"
        if job:
            title += f" - Job {job}"
        if cost_code:
            title += f" - CC {cost_code}"
        if asset:
            title += f" - Asset {asset}"
            
        export_path = export_dataframe(
            df=export_df,
            filename=filename,
            format_type=export_format,
            subfolder='april_billing/detail',
            title=title
        )
        
        if export_path:
            return send_file(export_path, as_attachment=True)
        else:
            flash('Error creating export file', 'error')
            return redirect(url_for('april_billing.index'))

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