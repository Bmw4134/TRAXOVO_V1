"""
Asset Metrics Calculator - Direct Asset List to Dashboard Connection

This module connects your Gauge API Asset List directly to dashboard metrics,
calculating real attendance numbers for immediate deadline delivery.
"""

import os
import logging
import pandas as pd
import requests
from datetime import datetime, time
from gauge_api import GaugeAPI

logger = logging.getLogger(__name__)

def get_real_dashboard_metrics(date_str):
    """
    Calculate real dashboard metrics using Asset List + MTD data
    
    Args:
        date_str: Date to process (YYYY-MM-DD)
        
    Returns:
        dict: Real metrics for dashboard display
    """
    try:
        # Direct connection to your Gauge API Asset List
        api = GaugeAPI()
        url = f"{api.api_url}/AssetList/{api.asset_list_id}"
        response = requests.get(url, auth=(api.username, api.password), verify=False, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Asset List API error: {response.status_code}")
            return get_fallback_metrics()
        
        raw_assets = response.json()
        logger.info(f"Retrieved {len(raw_assets)} assets from Gauge API")
        
        # Extract driver assignments from ALL assets
        driver_assignments = {}
        total_assigned_drivers = 0
        
        for asset in raw_assets:
            asset_id = (asset.get('AssetID') or 
                       asset.get('assetID') or 
                       asset.get('id'))
            
            secondary_id = asset.get('SecondaryAssetIdentifier', '')
            
            if asset_id and secondary_id and ' - ' in str(secondary_id):
                parts = str(secondary_id).split(' - ', 1)
                employee_id = parts[0].strip()
                driver_name = parts[1].strip()
                
                driver_assignments[str(asset_id)] = {
                    'employee_id': employee_id,
                    'driver_name': driver_name,
                    'asset_id': asset_id
                }
                total_assigned_drivers += 1
        
        logger.info(f"Found {total_assigned_drivers} driver assignments in Asset List")
        
        # Process MTD files to calculate attendance
        metrics = calculate_attendance_from_mtd(driver_assignments, date_str)
        metrics['total_assigned_drivers'] = total_assigned_drivers
        metrics['total_assets'] = len(raw_assets)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating real metrics: {e}")
        return get_fallback_metrics()

def calculate_attendance_from_mtd(driver_assignments, date_str):
    """
    Calculate attendance metrics from MTD files using driver assignments
    
    Args:
        driver_assignments: Asset ID to driver mapping
        date_str: Target date (YYYY-MM-DD)
        
    Returns:
        dict: Attendance metrics
    """
    metrics = {
        'on_time': 0,
        'late': 0,
        'early_end': 0,
        'not_on_job': 0,
        'avg_late': 0,
        'avg_early_end': 0
    }
    
    try:
        # Find MTD files in uploads directory
        mtd_files = []
        uploads_dir = "uploads"
        
        if os.path.exists(uploads_dir):
            for filename in os.listdir(uploads_dir):
                if filename.endswith('.csv') and 'driving' in filename.lower():
                    mtd_files.append(os.path.join(uploads_dir, filename))
        
        if not mtd_files:
            logger.warning("No MTD files found for processing")
            return metrics
        
        # Process the most recent MTD file
        latest_file = max(mtd_files, key=os.path.getmtime)
        logger.info(f"Processing MTD file: {os.path.basename(latest_file)}")
        
        # Read MTD file
        df = pd.read_csv(latest_file, skiprows=7, low_memory=False)
        
        # Find asset column
        asset_column = None
        for col in df.columns:
            if 'asset' in col.lower() or 'textbox53' in col.lower():
                asset_column = col
                break
        
        if not asset_column:
            logger.warning("No asset column found in MTD file")
            return metrics
        
        # Track driver events by employee ID
        driver_events = {}
        
        for _, row in df.iterrows():
            try:
                # Extract asset ID from MTD row
                asset_value = str(row.get(asset_column, '')).strip()
                asset_id = extract_asset_id_from_mtd(asset_value)
                
                if not asset_id or asset_id not in driver_assignments:
                    continue
                
                # Get driver info
                driver_info = driver_assignments[asset_id]
                employee_id = driver_info['employee_id']
                
                # Parse event time
                event_time = row.get('EventDateTime')
                if pd.isna(event_time):
                    continue
                
                parsed_time = pd.to_datetime(event_time)
                if parsed_time.strftime('%Y-%m-%d') != date_str:
                    continue
                
                # Track events for this driver
                if employee_id not in driver_events:
                    driver_events[employee_id] = {
                        'driver_name': driver_info['driver_name'],
                        'events': []
                    }
                
                driver_events[employee_id]['events'].append({
                    'time': parsed_time,
                    'type': row.get('MsgType', ''),
                    'location': row.get('Location', '')
                })
                
            except Exception as e:
                continue
        
        # Classify each driver's attendance
        for employee_id, data in driver_events.items():
            events = sorted(data['events'], key=lambda x: x['time'])
            
            # Find Key On and Key Off events
            key_on_events = [e for e in events if e['type'] == 'Key On']
            key_off_events = [e for e in events if e['type'] == 'Key Off']
            
            if not key_on_events:
                metrics['not_on_job'] += 1
                continue
            
            first_key_on = key_on_events[0]['time']
            last_key_off = key_off_events[-1]['time'] if key_off_events else None
            
            # Classify based on start time (7:30 AM threshold)
            start_hour = first_key_on.hour
            start_minute = first_key_on.minute
            
            if start_hour > 7 or (start_hour == 7 and start_minute > 30):
                metrics['late'] += 1
                # Calculate minutes late for average
                late_minutes = (start_hour - 7) * 60 + (start_minute - 30)
                metrics['avg_late'] = (metrics['avg_late'] * (metrics['late'] - 1) + late_minutes) / metrics['late']
            elif last_key_off and last_key_off.hour < 16:  # Before 4:00 PM
                metrics['early_end'] += 1
                # Calculate minutes early for average
                early_minutes = (16 - last_key_off.hour) * 60 - last_key_off.minute
                metrics['avg_early_end'] = (metrics['avg_early_end'] * (metrics['early_end'] - 1) + early_minutes) / metrics['early_end']
            else:
                metrics['on_time'] += 1
        
        logger.info(f"Attendance calculated: {metrics['on_time']} on time, {metrics['late']} late, "
                   f"{metrics['early_end']} early end, {metrics['not_on_job']} not on job")
        
    except Exception as e:
        logger.error(f"Error processing MTD files: {e}")
    
    return metrics

def extract_asset_id_from_mtd(asset_value):
    """
    Extract asset ID from MTD file asset field
    
    Args:
        asset_value: Raw asset value from CSV
        
    Returns:
        str: Clean asset ID or None
    """
    if not asset_value or asset_value == 'nan':
        return None
    
    # Handle "#210003 - AMMAR I. ELHAMAD FORD F150 2024 Personal Vehicle +"
    if asset_value.startswith('#'):
        parts = asset_value[1:].split(' - ', 1)
        if parts:
            return parts[0].strip()
    
    # Handle direct asset IDs
    if asset_value.isdigit():
        return asset_value
    
    # Extract numbers from the beginning
    import re
    match = re.match(r'(\d+)', asset_value)
    if match:
        return match.group(1)
    
    return None

def get_fallback_metrics():
    """
    Fallback metrics when Asset List is unavailable
    
    Returns:
        dict: Fallback metrics
    """
    return {
        'on_time': 0,
        'late': 0,
        'early_end': 0,
        'not_on_job': 0,
        'avg_late': 0,
        'avg_early_end': 0,
        'total_assigned_drivers': 0,
        'total_assets': 0
    }