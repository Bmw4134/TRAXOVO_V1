"""
Driver Identity Attendance Integration

This module integrates the asset-driver mapping system with the attendance report generator,
ensuring consistent driver identification across all reports using the Secondary Asset Identifier.
"""

import logging
from datetime import datetime

from utils.asset_driver_mapper import get_driver_for_asset
from utils.driver_identity_integration import enhance_attendance_data_with_driver_info

# Set up logging
logger = logging.getLogger(__name__)

def enhance_daily_driver_report(driver_records):
    """
    Enhance daily driver report records with consistent driver identity information.
    
    Args:
        driver_records (list): List of driver record dictionaries
        
    Returns:
        list: Enhanced driver records
    """
    if not driver_records:
        return []
        
    enhanced_records = []
    
    for record in driver_records:
        # Try to get driver information from asset mapping
        asset_id = record.get('asset_id') or record.get('vehicle_id')
        
        if asset_id:
            driver_info = get_driver_for_asset(asset_id)
            
            if driver_info and driver_info.get('employee_id') and driver_info.get('employee_name'):
                # Use the consistent driver information from asset mapping
                record['driver_name'] = driver_info.get('employee_name')
                record['employee_id'] = driver_info.get('employee_id')
                record['vehicle_make'] = driver_info.get('asset_make')
                record['vehicle_model'] = driver_info.get('asset_model')
                record['driver_verified'] = True
        
        enhanced_records.append(record)
    
    return enhanced_records

def enhance_attendance_pipeline_results(attendance_results):
    """
    Enhance attendance pipeline results with consistent driver identities.
    
    Args:
        attendance_results (dict): Attendance pipeline results
        
    Returns:
        dict: Enhanced attendance results
    """
    if not attendance_results:
        return {}
        
    # Create a copy to avoid modifying the original
    enhanced_results = dict(attendance_results)
    
    # Enhance driver records
    driver_records = enhanced_results.get('driver_records', [])
    enhanced_records = enhance_daily_driver_report(driver_records)
    enhanced_results['driver_records'] = enhanced_records
    
    # Update the data sources to indicate identity verification
    data_sources = enhanced_results.get('data_sources', [])
    if isinstance(data_sources, dict):
        data_sources = []
    data_sources.append({
        'source': 'Secondary Asset Identifier',
        'timestamp': datetime.now().isoformat(),
        'type': 'identity_verification',
        'verified_count': sum(1 for r in enhanced_records if r.get('driver_verified', False))
    })
    enhanced_results['data_sources'] = data_sources
    
    return enhanced_results

def enhance_driver_data_from_files(driving_history_data, time_on_site_data=None):
    """
    Enhance driver data from source files with consistent identity information.
    
    Args:
        driving_history_data (list): List of driving history records
        time_on_site_data (list): List of time on site records
        
    Returns:
        tuple: (enhanced_driving_history, enhanced_time_on_site)
    """
    if driving_history_data:
        # Process driving history data with consistent driver information
        enhanced_driving_history = enhance_attendance_data_with_driver_info(driving_history_data)
    else:
        enhanced_driving_history = []
        
    if time_on_site_data:
        # Process time on site data with consistent driver information
        enhanced_time_on_site = enhance_attendance_data_with_driver_info(time_on_site_data)
    else:
        enhanced_time_on_site = []
        
    return enhanced_driving_history, enhanced_time_on_site