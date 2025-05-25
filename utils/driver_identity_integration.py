"""
Driver Identity Integration Module

This module integrates the Asset-Driver mapping system with the rest of the TRAXORA application,
ensuring consistent driver identification across all reports by using the Secondary Asset Identifier
as the source of truth.
"""

import os
import pandas as pd
import logging
from datetime import datetime

from utils.asset_driver_mapper import (
    get_driver_for_asset,
    get_asset_for_driver,
    get_all_mapped_drivers,
    refresh_mapping
)

logger = logging.getLogger(__name__)

def enhance_driving_history_with_driver_info(driving_history_df):
    """
    Enhance driving history data with consistent driver information from asset mapping.
    
    Args:
        driving_history_df (DataFrame): Driving history DataFrame
        
    Returns:
        DataFrame: Enhanced driving history with driver information
    """
    if driving_history_df is None or driving_history_df.empty:
        return driving_history_df
        
    enhanced_df = driving_history_df.copy()
    
    # Add driver columns if they don't exist
    if 'employee_id' not in enhanced_df.columns:
        enhanced_df['employee_id'] = None
    if 'employee_name' not in enhanced_df.columns:
        enhanced_df['employee_name'] = None
    
    # Process each row to add driver information
    for idx, row in enhanced_df.iterrows():
        asset_id = row.get('Asset ID') or row.get('asset_id') or row.get('vehicle_id')
        if asset_id:
            driver_info = get_driver_for_asset(asset_id)
            if driver_info:
                enhanced_df.at[idx, 'employee_id'] = driver_info.get('employee_id')
                enhanced_df.at[idx, 'employee_name'] = driver_info.get('employee_name')
    
    return enhanced_df

def enhance_attendance_data_with_driver_info(attendance_df):
    """
    Enhance attendance data with consistent driver information from asset mapping.
    
    Args:
        attendance_df (DataFrame): Attendance data DataFrame
        
    Returns:
        DataFrame: Enhanced attendance data with driver information
    """
    if attendance_df is None or attendance_df.empty:
        return attendance_df
        
    enhanced_df = attendance_df.copy()
    
    # Add driver columns if they don't exist
    if 'employee_id' not in enhanced_df.columns:
        enhanced_df['employee_id'] = None
    if 'employee_name' not in enhanced_df.columns:
        enhanced_df['employee_name'] = None
    if 'driver_vehicle' not in enhanced_df.columns:
        enhanced_df['driver_vehicle'] = None
    
    # Process each row to add driver information
    for idx, row in enhanced_df.iterrows():
        # Try to find driver info by asset ID first
        asset_id = row.get('vehicle_id') or row.get('asset_id')
        
        if asset_id:
            driver_info = get_driver_for_asset(asset_id)
            if driver_info:
                enhanced_df.at[idx, 'employee_id'] = driver_info.get('employee_id')
                enhanced_df.at[idx, 'employee_name'] = driver_info.get('employee_name')
                enhanced_df.at[idx, 'driver_vehicle'] = f"{driver_info.get('asset_make', '')} {driver_info.get('asset_model', '')}".strip()
                continue
        
        # If we couldn't find by asset ID, try by driver name if available
        driver_name = row.get('driver_name') or row.get('Driver Name')
        if driver_name:
            # Try to match driver name with employee names in our mapping
            all_drivers = get_all_mapped_drivers()
            for driver in all_drivers:
                if driver.get('employee_name') and driver_name.lower() in driver.get('employee_name').lower():
                    enhanced_df.at[idx, 'employee_id'] = driver.get('employee_id')
                    enhanced_df.at[idx, 'employee_name'] = driver.get('employee_name')
                    enhanced_df.at[idx, 'driver_vehicle'] = f"{driver.get('asset_make', '')} {driver.get('asset_model', '')}".strip()
                    break
    
    return enhanced_df

def validate_driver_vehicle_assignments():
    """
    Validate driver-vehicle assignments by checking for inconsistencies.
    
    Returns:
        dict: Validation results
    """
    all_drivers = get_all_mapped_drivers()
    
    # Check for duplicate assignments
    employee_ids = {}
    asset_ids = {}
    issues = []
    
    for driver in all_drivers:
        employee_id = driver.get('employee_id')
        asset_id = driver.get('asset_id')
        
        # Check for duplicate employee IDs
        if employee_id:
            if employee_id in employee_ids:
                issues.append({
                    'type': 'duplicate_employee',
                    'employee_id': employee_id,
                    'employee_name': driver.get('employee_name'),
                    'asset1': asset_id,
                    'asset2': employee_ids[employee_id]
                })
            else:
                employee_ids[employee_id] = asset_id
        
        # Check for duplicate asset IDs
        if asset_id in asset_ids:
            issues.append({
                'type': 'duplicate_asset',
                'asset_id': asset_id,
                'employee1': asset_ids[asset_id],
                'employee2': employee_id
            })
        else:
            asset_ids[asset_id] = employee_id
    
    return {
        'total_mappings': len(all_drivers),
        'valid_mappings': len(all_drivers) - len(issues),
        'issues': issues
    }

def get_driver_details(employee_id=None, employee_name=None):
    """
    Get detailed information about a driver by ID or name.
    
    Args:
        employee_id (str): Employee ID
        employee_name (str): Employee name
        
    Returns:
        dict: Driver details including asset information
    """
    all_drivers = get_all_mapped_drivers()
    
    # Search by ID
    if employee_id:
        for driver in all_drivers:
            if driver.get('employee_id') == str(employee_id).strip():
                return driver
    
    # Search by name
    if employee_name:
        for driver in all_drivers:
            if driver.get('employee_name') and employee_name.lower() in driver.get('employee_name').lower():
                return driver
    
    return None

def import_assets_list(file_path):
    """
    Import an assets list Excel file into the system.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        dict: Import results
    """
    if not os.path.exists(file_path):
        return {'success': False, 'message': f'File not found: {file_path}'}
    
    try:
        # Copy the file to the attached_assets directory
        target_dir = os.path.join(os.getcwd(), 'attached_assets')
        os.makedirs(target_dir, exist_ok=True)
        
        target_path = os.path.join(target_dir, 'AssetsListExport.xlsx')
        
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Save to target location
        df.to_excel(target_path, index=False)
        
        # Refresh the mapping
        mapping_count = refresh_mapping()
        
        return {
            'success': True,
            'message': f'Successfully imported assets list with {mapping_count} entries',
            'count': mapping_count
        }
    except Exception as e:
        logger.error(f"Error importing assets list: {str(e)}")
        return {'success': False, 'message': f'Error importing assets list: {str(e)}'}

def generate_driver_asset_report():
    """
    Generate a comprehensive report of all driver-asset mappings.
    
    Returns:
        DataFrame: Report of driver-asset mappings
    """
    all_drivers = get_all_mapped_drivers()
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(all_drivers)
    
    # Add timestamp
    df['report_date'] = datetime.now().strftime('%Y-%m-%d')
    df['report_time'] = datetime.now().strftime('%H:%M:%S')
    
    return df