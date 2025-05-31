"""
MTD Asset-Based Processor

This module processes MTD data using the Asset List lookup approach,
matching Asset IDs to driver assignments via Secondary Asset Identifier.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from gauge_api_legacy import get_asset_list

logger = logging.getLogger(__name__)

def load_asset_list():
    """
    Load the Asset List to get driver-vehicle assignments
    
    Returns:
        dict: Asset ID mapped to driver info
    """
    try:
        # Get asset list from Gauge API
        asset_data = get_asset_list()
        
        if not asset_data:
            logger.error("No asset data available from Gauge API")
            return {}
        
        # Create mapping: Asset ID -> Driver Info
        asset_mapping = {}
        
        for asset in asset_data:
            asset_id = asset.get('AssetID')
            secondary_id = asset.get('SecondaryAssetIdentifier', '')
            
            if asset_id and secondary_id:
                # Parse driver info from Secondary Asset Identifier "210013 - Shaylor, Matthew C"
                if ' - ' in secondary_id:
                    parts = secondary_id.split(' - ', 1)
                    employee_id = parts[0].strip()
                    driver_name = parts[1].strip()
                    
                    asset_mapping[str(asset_id)] = {
                        'employee_id': employee_id,
                        'driver_name': driver_name,
                        'secondary_id': secondary_id,
                        'asset_label': asset.get('AssetLabel', ''),
                        'asset_type': asset.get('AssetType', '')
                    }
        
        logger.info(f"Loaded {len(asset_mapping)} asset-driver mappings")
        return asset_mapping
        
    except Exception as e:
        logger.error(f"Error loading asset list: {e}")
        return {}

def process_mtd_file_efficiently(file_path, asset_mapping, target_date=None):
    """
    Process a single MTD file efficiently using asset mapping
    
    Args:
        file_path: Path to MTD file
        asset_mapping: Asset ID to driver mapping
        target_date: Specific date to filter (YYYY-MM-DD) or None for all dates
        
    Returns:
        list: Driver activity records
    """
    driver_records = []
    
    try:
        # Read file with proper CSV parsing
        df = pd.read_csv(file_path, skiprows=7, low_memory=False)
        
        if df.empty:
            return driver_records
        
        # Look for Asset ID column (might be named differently)
        asset_id_column = None
        for col in df.columns:
            if 'asset' in col.lower() and ('id' in col.lower() or 'label' in col.lower()):
                asset_id_column = col
                break
        
        if not asset_id_column:
            # Try to extract from other columns
            if 'Textbox53' in df.columns:
                asset_id_column = 'Textbox53'
        
        if not asset_id_column:
            logger.warning(f"No Asset ID column found in {file_path}")
            return driver_records
        
        # Process only records with known asset assignments
        for _, row in df.iterrows():
            try:
                # Extract asset ID
                asset_value = str(row.get(asset_id_column, '')).strip()
                
                # Try to parse asset ID from various formats
                asset_id = extract_asset_id(asset_value)
                
                if not asset_id or asset_id not in asset_mapping:
                    continue
                
                # Get driver info from asset mapping
                driver_info = asset_mapping[asset_id]
                
                # Extract date and time information
                event_time = row.get('EventDateTime')
                if pd.isna(event_time) or not event_time:
                    continue
                
                try:
                    parsed_time = pd.to_datetime(event_time)
                    record_date = parsed_time.strftime('%Y-%m-%d')
                    
                    # Filter by target date if specified
                    if target_date and record_date != target_date:
                        continue
                    
                    # Create driver record
                    driver_record = {
                        'asset_id': asset_id,
                        'employee_id': driver_info['employee_id'],
                        'driver_name': driver_info['driver_name'],
                        'date': record_date,
                        'event_time': parsed_time,
                        'event_type': row.get('MsgType', ''),
                        'location': row.get('Location', ''),
                        'latitude': row.get('Latitude'),
                        'longitude': row.get('Longitude')
                    }
                    
                    driver_records.append(driver_record)
                    
                except Exception as e:
                    continue
                    
            except Exception as e:
                continue
    
    except Exception as e:
        logger.error(f"Error processing MTD file {file_path}: {e}")
    
    return driver_records

def extract_asset_id(asset_value):
    """
    Extract asset ID from various formats
    
    Args:
        asset_value: Raw asset value from CSV
        
    Returns:
        str: Clean asset ID or None
    """
    if not asset_value or asset_value == 'nan':
        return None
    
    # Handle formats like "#210003 - AMMAR I. ELHAMAD FORD F150 2024 Personal Vehicle +"
    if asset_value.startswith('#'):
        # Extract number after #
        parts = asset_value[1:].split(' - ', 1)
        if parts:
            return parts[0].strip()
    
    # Handle direct asset IDs
    if asset_value.isdigit():
        return asset_value
    
    # Try to extract numbers from the beginning
    import re
    match = re.match(r'(\d+)', asset_value)
    if match:
        return match.group(1)
    
    return None

def classify_driver_attendance(driver_records, date_str):
    """
    Classify driver attendance for a specific date
    
    Args:
        driver_records: List of driver activity records
        date_str: Date to process (YYYY-MM-DD)
        
    Returns:
        dict: Classification results
    """
    # Group records by driver
    drivers = {}
    
    for record in driver_records:
        if record['date'] != date_str:
            continue
            
        driver_key = record['employee_id']
        if driver_key not in drivers:
            drivers[driver_key] = {
                'employee_id': record['employee_id'],
                'driver_name': record['driver_name'],
                'events': []
            }
        
        drivers[driver_key]['events'].append(record)
    
    # Classify each driver
    classifications = {
        'on_time': 0,
        'late': 0,
        'early_end': 0,
        'not_on_job': 0,
        'driver_records': []
    }
    
    for driver_key, driver_data in drivers.items():
        events = sorted(driver_data['events'], key=lambda x: x['event_time'])
        
        # Find first Key On and last Key Off
        key_on_events = [e for e in events if e['event_type'] == 'Key On']
        key_off_events = [e for e in events if e['event_type'] == 'Key Off']
        
        first_key_on = key_on_events[0] if key_on_events else None
        last_key_off = key_off_events[-1] if key_off_events else None
        
        # Classify based on times
        status = 'not_on_job'
        start_time = None
        end_time = None
        
        if first_key_on:
            start_time = first_key_on['event_time'].strftime('%H:%M')
            start_hour = first_key_on['event_time'].hour
            start_minute = first_key_on['event_time'].minute
            
            # Late if after 7:30 AM
            if start_hour > 7 or (start_hour == 7 and start_minute > 30):
                status = 'late'
            else:
                status = 'on_time'
        
        if last_key_off:
            end_time = last_key_off['event_time'].strftime('%H:%M')
            end_hour = last_key_off['event_time'].hour
            
            # Early end if before 4:00 PM (16:00)
            if end_hour < 16:
                status = 'early_end'
        
        # Update classification counts
        classifications[status] += 1
        
        # Add to driver records
        driver_record = {
            'employee_id': driver_data['employee_id'],
            'driver_name': driver_data['driver_name'],
            'status': status,
            'start_time': start_time,
            'end_time': end_time,
            'total_events': len(events),
            'job_site': 'Unknown'  # Could be enhanced with location mapping
        }
        
        classifications['driver_records'].append(driver_record)
    
    return classifications

def process_mtd_data_with_assets(upload_dir, target_date=None):
    """
    Process MTD data using Asset List approach
    
    Args:
        upload_dir: Directory containing MTD files
        target_date: Specific date to process (YYYY-MM-DD) or None for range
        
    Returns:
        dict: Processing results
    """
    # Load asset mapping
    asset_mapping = load_asset_list()
    
    if not asset_mapping:
        logger.error("No asset mapping available")
        return {}
    
    logger.info(f"Processing MTD data with {len(asset_mapping)} asset assignments")
    
    # Collect all driver records
    all_driver_records = []
    
    # Process each MTD file
    for filename in os.listdir(upload_dir):
        if filename.endswith('.csv') and ('driving' in filename.lower() or 'history' in filename.lower()):
            file_path = os.path.join(upload_dir, filename)
            
            logger.info(f"Processing {filename}")
            
            driver_records = process_mtd_file_efficiently(file_path, asset_mapping, target_date)
            all_driver_records.extend(driver_records)
    
    if not all_driver_records:
        logger.warning("No driver records found in MTD files")
        return {}
    
    # Get date range from records
    dates = sorted(set(record['date'] for record in all_driver_records))
    
    if not dates:
        return {}
    
    # Process attendance for each date (or just target date)
    results = {}
    
    if target_date:
        process_dates = [target_date] if target_date in dates else []
    else:
        process_dates = dates
    
    for date_str in process_dates:
        logger.info(f"Classifying attendance for {date_str}")
        
        date_records = [r for r in all_driver_records if r['date'] == date_str]
        classification = classify_driver_attendance(date_records, date_str)
        
        results[date_str] = {
            'date': date_str,
            'summary': {
                'total_drivers': len(classification['driver_records']),
                'on_time': classification['on_time'],
                'late': classification['late'],
                'early_end': classification['early_end'],
                'not_on_job': classification['not_on_job']
            },
            'driver_records': classification['driver_records']
        }
    
    logger.info(f"Processed {len(results)} dates with MTD data")
    return results