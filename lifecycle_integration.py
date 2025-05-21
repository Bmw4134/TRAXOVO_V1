#!/usr/bin/env python3
"""
Lifecycle Integration Module

Integrates the equipment lifecycle module with other system components:
- Driver identity verification
- Daily Driver Report generation
- Asset Map dashboard
- Audit logging
"""

import os
import json
import logging
from datetime import datetime
import equipment_lifecycle as lifecycle

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
AUDIT_LOG_DIR = 'logs/lifecycle'
os.makedirs(AUDIT_LOG_DIR, exist_ok=True)


def filter_active_assets_for_report(report_data, date_str=None):
    """
    Filter a Daily Driver Report to exclude disposed assets.
    
    Args:
        report_data: The report data dictionary
        date_str: The date to check asset status against
    
    Returns:
        The filtered report data
    """
    if not date_str:
        date_str = report_data.get('date')
    
    if not date_str:
        logger.warning("No date provided for asset filtering")
        return report_data
    
    # Create a copy to avoid modifying the original
    filtered_data = report_data.copy()
    
    # Filter drivers to include only those with active assets
    filtered_drivers = []
    excluded_count = 0
    
    for driver in report_data.get('drivers', []):
        asset_id = driver.get('asset_id')
        if not asset_id:
            # Keep drivers without asset ID
            filtered_drivers.append(driver)
            continue
        
        # Check asset status
        status = lifecycle.get_asset_status(asset_id, date_str)
        
        # Add status to driver record
        driver_with_status = driver.copy()
        driver_with_status['asset_status'] = status
        
        # Include only active assets (or unknown status)
        if status in [lifecycle.STATUS_ACTIVE, lifecycle.STATUS_UNKNOWN]:
            filtered_drivers.append(driver_with_status)
        else:
            excluded_count += 1
            # Log exclusion
            logger.info(f"Excluded {asset_id} ({driver.get('name')}) from report - status: {status}")
    
    # Update report data
    filtered_data['drivers'] = filtered_drivers
    
    # Update summary statistics
    if 'summary' in filtered_data:
        filtered_data['summary']['excluded_assets'] = excluded_count
        filtered_data['summary']['original_total'] = filtered_data['summary'].get('total', 0)
        filtered_data['summary']['total'] = len(filtered_drivers)
    
    # Add lifecycle metadata
    if 'metadata' not in filtered_data:
        filtered_data['metadata'] = {}
    
    filtered_data['metadata']['lifecycle_filtered'] = True
    filtered_data['metadata']['lifecycle_filter_date'] = date_str
    filtered_data['metadata']['excluded_assets_count'] = excluded_count
    
    return filtered_data


def validate_driver_asset_assignment(driver_id, asset_id, date_str=None):
    """
    Validate if a driver is correctly assigned to an asset on a specific date.
    
    Args:
        driver_id: The driver ID
        asset_id: The asset ID
        date_str: The date to check the assignment against
    
    Returns:
        bool: True if the assignment is valid, False otherwise
    """
    # First check asset status
    status = lifecycle.get_asset_status(asset_id, date_str)
    if status != lifecycle.STATUS_ACTIVE:
        logger.warning(f"Asset {asset_id} is not active on {date_str} (status: {status})")
        return False
    
    # Check driver assignment
    current_driver = lifecycle.get_current_driver(asset_id, date_str)
    if not current_driver:
        # If no driver is assigned, consider it valid (absence of data shouldn't block operations)
        return True
    
    # Check if the assigned driver matches
    if current_driver.lower() != driver_id.lower():
        logger.warning(f"Driver mismatch for asset {asset_id} on {date_str}: expected {current_driver}, got {driver_id}")
        return False
    
    return True


def audit_telematics_data(source_file, date_str=None):
    """
    Audit telematics data to flag any records from disposed assets.
    
    Args:
        source_file: The telematics data file path
        date_str: The date to check asset status against
    
    Returns:
        dict: Audit results with flagged records
    """
    import pandas as pd
    import os
    
    audit_results = {
        'source_file': os.path.basename(source_file),
        'date': date_str or datetime.now().strftime('%Y-%m-%d'),
        'processed_at': datetime.now().isoformat(),
        'total_records': 0,
        'flagged_records': 0,
        'flagged_assets': set(),
        'details': []
    }
    
    try:
        # Determine file type and delimiter
        if source_file.lower().endswith('.csv'):
            with open(source_file, 'r') as f:
                header = f.readline().strip()
            
            delimiter = ',' if ',' in header else ';'
            df = pd.read_csv(source_file, delimiter=delimiter)
        elif source_file.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(source_file)
        else:
            logger.error(f"Unsupported file format: {source_file}")
            return audit_results
        
        # Normalize column names
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Find asset column
        asset_col = None
        for col in ['asset', 'asset_id', 'equipment', 'equipment_id', 'vehicle', 'vehicle_id']:
            if col in df.columns:
                asset_col = col
                break
        
        if not asset_col:
            logger.warning(f"No asset column found in {source_file}")
            return audit_results
        
        # Process each row
        audit_results['total_records'] = len(df)
        
        for _, row in df.iterrows():
            asset_id = str(row[asset_col]).strip() if pd.notna(row[asset_col]) else None
            
            if not asset_id or asset_id.lower() in ['nan', 'none', 'null', '']:
                continue
            
            # Check asset status
            status = lifecycle.get_asset_status(asset_id, date_str)
            
            # Flag records from disposed assets
            if status == lifecycle.STATUS_DISPOSED:
                audit_results['flagged_records'] += 1
                audit_results['flagged_assets'].add(asset_id)
                
                # Extract row data for audit
                row_data = {col: str(row[col]) for col in df.columns if pd.notna(row[col])}
                row_data['flagged_reason'] = f"Asset {asset_id} is disposed"
                
                audit_results['details'].append(row_data)
        
        # Convert set to list for JSON serialization
        audit_results['flagged_assets'] = list(audit_results['flagged_assets'])
        
        # Log audit results
        logger.info(f"Audit results for {os.path.basename(source_file)}: "
                   f"{audit_results['flagged_records']} flagged out of {audit_results['total_records']} records "
                   f"({len(audit_results['flagged_assets'])} unique assets)")
        
        # Save audit results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audit_file = os.path.join(AUDIT_LOG_DIR, f"audit_{timestamp}_{os.path.basename(source_file)}.json")
        
        with open(audit_file, 'w') as f:
            # Limit details to 100 records to avoid huge files
            limited_results = audit_results.copy()
            if len(limited_results['details']) > 100:
                limited_results['details'] = limited_results['details'][:100]
                limited_results['details_truncated'] = True
            
            json.dump(limited_results, f, indent=2)
        
        return audit_results
    
    except Exception as e:
        logger.error(f"Error auditing telematics data: {e}")
        return audit_results


def initialize_sample_data():
    """
    Initialize sample lifecycle data for testing and demonstration.
    
    This creates a set of sample acquisition and disposal records
    that match the actual fleet data.
    """
    import pandas as pd
    
    try:
        # Try to load equipment billing data
        equipment_billing_path = 'attached_assets/EQ MONTHLY BILLINGS WORKING SPREADSHEET - APRIL 2025.xlsx'
        if not os.path.exists(equipment_billing_path):
            logger.warning(f"Equipment billing file not found: {equipment_billing_path}")
            return False
        
        # Load workbook
        workbook = pd.ExcelFile(equipment_billing_path)
        
        # Load asset list sheet
        asset_sheet = None
        for sheet_name in ['FLEET', 'Asset List', 'Equip Table']:
            if sheet_name in workbook.sheet_names:
                asset_sheet = pd.read_excel(workbook, sheet_name=sheet_name)
                break
        
        if asset_sheet is None:
            logger.warning("No asset list sheet found in equipment billing workbook")
            return False
        
        # Normalize column names
        asset_sheet.columns = [str(col).strip().lower().replace(' ', '_') for col in asset_sheet.columns]
        
        # Find relevant columns
        asset_col = None
        driver_col = None
        division_col = None
        
        for col in ['asset', 'asset_id', 'equipment', 'equipment_id']:
            if col in asset_sheet.columns:
                asset_col = col
                break
        
        for col in ['driver', 'driver_name', 'employee', 'employee_name']:
            if col in asset_sheet.columns:
                driver_col = col
                break
        
        for col in ['division', 'department', 'region', 'area']:
            if col in asset_sheet.columns:
                division_col = col
                break
        
        if not asset_col or not driver_col:
            logger.warning("Required columns not found in asset list sheet")
            return False
        
        # Process assets
        assets_processed = 0
        disposed_assets = 0
        
        # Calculate dates
        from datetime import datetime, timedelta
        
        acquisition_date = datetime(2025, 1, 1).date()  # Jan 1, 2025
        disposal_date = datetime(2025, 4, 30).date()  # Apr 30, 2025
        
        # Process each row
        for _, row in asset_sheet.iterrows():
            asset_id = str(row[asset_col]).strip() if pd.notna(row[asset_col]) else None
            driver_id = str(row[driver_col]).strip() if pd.notna(row[driver_col]) else None
            
            # Skip empty data
            if not asset_id or not driver_id:
                continue
            
            # Get division if available, default to Houston
            division = str(row[division_col]).strip() if division_col and pd.notna(row[division_col]) else "Houston"
            
            # Dispose approximately 10% of assets (every 10th asset)
            should_dispose = assets_processed % 10 == 0
            
            # Record acquisition for all assets
            lifecycle.record_acquisition(asset_id, driver_id, division, acquisition_date)
            
            # Record disposal for selected assets
            if should_dispose:
                lifecycle.record_disposal(asset_id, disposal_date, "other", "Disposed for demonstration")
                disposed_assets += 1
            
            assets_processed += 1
        
        logger.info(f"Initialized lifecycle data for {assets_processed} assets ({disposed_assets} disposed)")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing sample lifecycle data: {e}")
        return False


# Initialize sample data when module is imported
if not os.path.exists('data/asset_registry.json'):
    logger.info("Initializing sample lifecycle data")
    initialize_sample_data()