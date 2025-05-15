"""
Driver Attendance Report Module

This module processes fleet data to generate attendance reports, identifying:
- Late starts (LS)
- Early ends (EE)
- Not on job (NOJ) issues

The module supports two main reports:
1. Same-Day Report (LS/NOJ) - Using morning data for the current day
2. Prior-Day Report (LS/EE/NOJ) - Using complete data from the previous day
"""
import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta, time

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for attendance rules
START_TIME_THRESHOLD = time(7, 30)  # Expected start time: 7:30 AM
END_TIME_THRESHOLD = time(16, 30)   # Expected end time: 4:30 PM
MIN_HOURS_ON_SITE = 8.0             # Minimum expected hours on site

# Data directories
DATA_DIR = 'data'
REPORTS_DIR = os.path.join(DATA_DIR, 'reports')
CYA_BACKUP_DIR = os.path.join(DATA_DIR, 'cya_backup')

# Ensure directories exist
for directory in [DATA_DIR, REPORTS_DIR, CYA_BACKUP_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_asset_driver_mapping():
    """
    Get the mapping of assets to drivers from the database or mapping file.
    This allows us to identify which driver is assigned to each vehicle/equipment.
    
    Returns:
        dict: Mapping of asset IDs to driver information
    """
    # TODO: Replace with actual database query or file parsing
    # In a real implementation, this would pull from the database or parse
    # the asset-driver mapping file
    
    # For now, return a placeholder mapping
    mapping = {}
    
    try:
        # Try to load from a mapping file if it exists
        mapping_file = os.path.join(DATA_DIR, 'asset_driver_mapping.json')
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                mapping = json.load(f)
                logger.info(f"Loaded {len(mapping)} asset-driver mappings from file")
    except Exception as e:
        logger.error(f"Error loading asset-driver mapping: {e}")
    
    # If we didn't get any mappings, try to extract from asset labels
    if not mapping:
        # This is a fallback to extract driver names from asset labels
        # It assumes that asset labels might contain driver names in parentheses
        # Like "PT-123 (John Doe)"
        logger.warning("No explicit mapping found. Attempting to extract from asset labels.")
    
    return mapping

def extract_driver_from_asset(asset):
    """
    Extract driver information from asset data, looking at label, notes, or other fields
    
    Args:
        asset (dict): Asset data dictionary
    
    Returns:
        dict: Driver information or None if not found
    """
    driver_info = None
    
    if asset.get('label'):
        # Try to extract driver name from label
        # Example: "PT-123 (John Doe)" -> extract "John Doe"
        label = asset.get('label')
        if '(' in label and ')' in label:
            start = label.find('(') + 1
            end = label.find(')')
            if start < end:
                driver_name = label[start:end].strip()
                if driver_name and driver_name.lower() not in ['', 'open', 'vacant', 'unassigned']:
                    driver_info = {
                        'name': driver_name,
                        'source': 'label'
                    }
    
    return driver_info

def determine_job_site(asset):
    """
    Determine the job site for an asset based on location, GPS, and other factors
    
    Args:
        asset (dict): Asset data dictionary
    
    Returns:
        str: Job site identifier or None if not determinable
    """
    # TODO: Implement real job site determination
    # This could be based on:
    # 1. GPS coordinates and geofencing
    # 2. Explicit job site assignment in the database
    # 3. Pattern analysis of historical locations
    
    # For now, just return the location field if it exists
    return asset.get('location') or asset.get('site') or None

def analyze_attendance_same_day(assets):
    """
    Analyze the current day's data for attendance issues (LS, NOJ)
    
    Args:
        assets (list): List of asset dictionaries for the current day
    
    Returns:
        dict: Analysis results including flagged drivers
    """
    results = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total_assets': len(assets),
        'total_drivers': 0,
        'late_starts': [],
        'not_on_job': [],
        'flagged_drivers': []
    }
    
    # Get driver mapping
    driver_mapping = get_asset_driver_mapping()
    
    # Current time reference
    now = datetime.now()
    cutoff_time = datetime.combine(now.date(), START_TIME_THRESHOLD)
    
    for asset in assets:
        # Skip inactive assets
        if asset.get('active') is False:
            continue
        
        # Get driver info
        asset_id = asset.get('asset_identifier')
        driver_info = driver_mapping.get(asset_id)
        
        if not driver_info:
            driver_info = extract_driver_from_asset(asset)
        
        if not driver_info:
            # Skip assets without identifiable drivers
            continue
            
        results['total_drivers'] += 1
        
        # Check for late start
        if asset.get('ignition') is False:
            # Vehicle not started yet
            results['late_starts'].append({
                'asset_id': asset_id,
                'asset_label': asset.get('label'),
                'driver': driver_info.get('name'),
                'location': asset.get('location'),
                'last_active': asset.get('event_date_time_string')
            })
            
            results['flagged_drivers'].append({
                'driver': driver_info.get('name'),
                'issue': 'Late Start',
                'asset': asset.get('label') or asset_id,
                'location': asset.get('location'),
                'details': f"Vehicle not started as of {now.strftime('%H:%M')}",
                'timestamp': now.isoformat()
            })
        
        # Check for not on job site
        job_site = determine_job_site(asset)
        if not job_site or 'office' in job_site.lower() or 'yard' in job_site.lower():
            # Asset is not on a job site
            results['not_on_job'].append({
                'asset_id': asset_id,
                'asset_label': asset.get('label'),
                'driver': driver_info.get('name'),
                'location': asset.get('location'),
                'last_active': asset.get('event_date_time_string')
            })
            
            results['flagged_drivers'].append({
                'driver': driver_info.get('name'),
                'issue': 'Not On Job',
                'asset': asset.get('label') or asset_id,
                'location': asset.get('location') or 'Unknown',
                'details': f"Not at job site as of {now.strftime('%H:%M')}",
                'timestamp': now.isoformat()
            })
    
    return results

def analyze_attendance_prior_day(assets):
    """
    Analyze the previous day's data for attendance issues (LS, EE, NOJ)
    
    Args:
        assets (list): List of asset dictionaries for the previous day
    
    Returns:
        dict: Analysis results including flagged drivers
    """
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    results = {
        'date': yesterday.strftime('%Y-%m-%d'),
        'total_assets': len(assets),
        'total_drivers': 0,
        'late_starts': [],
        'early_ends': [],
        'not_on_job': [],
        'flagged_drivers': []
    }
    
    # Get driver mapping
    driver_mapping = get_asset_driver_mapping()
    
    # Set up time thresholds for previous day
    start_cutoff = datetime.combine(yesterday, START_TIME_THRESHOLD)
    end_cutoff = datetime.combine(yesterday, END_TIME_THRESHOLD)
    
    for asset in assets:
        # Skip inactive assets
        if asset.get('active') is False:
            continue
        
        # Get driver info
        asset_id = asset.get('asset_identifier')
        driver_info = driver_mapping.get(asset_id)
        
        if not driver_info:
            driver_info = extract_driver_from_asset(asset)
        
        if not driver_info:
            # Skip assets without identifiable drivers
            continue
            
        results['total_drivers'] += 1
        
        # TODO: Extract actual start and end times from asset history
        # This would require additional asset history data
        
        # For now, use placeholder logic
        event_time_str = asset.get('event_date_time_string')
        event_time = None
        
        try:
            if event_time_str:
                # Try to parse the event time
                event_time = datetime.strptime(event_time_str, '%m/%d/%Y %I:%M:%S %p')
        except Exception as e:
            logger.warning(f"Could not parse event time: {event_time_str} - {e}")
        
        # Placeholder logic for attendance issues
        # In a real implementation, this would use the asset's history to determine
        # actual start and end times for the previous day
        
        # Here, we're just using the latest event time as a proxy
        if event_time and event_time.date() == yesterday:
            # Check if the vehicle was active on the previous day
            
            # Late start check
            if event_time > start_cutoff and asset.get('ignition') is True:
                # First ignition event was after the start cutoff
                results['late_starts'].append({
                    'asset_id': asset_id,
                    'asset_label': asset.get('label'),
                    'driver': driver_info.get('name'),
                    'location': asset.get('location'),
                    'start_time': event_time.strftime('%H:%M')
                })
                
                results['flagged_drivers'].append({
                    'driver': driver_info.get('name'),
                    'issue': 'Late Start',
                    'asset': asset.get('label') or asset_id,
                    'location': asset.get('location'),
                    'details': f"Started at {event_time.strftime('%H:%M')} (expected by {START_TIME_THRESHOLD.strftime('%H:%M')})",
                    'timestamp': yesterday.strftime('%Y-%m-%d')
                })
            
            # Early end check
            if event_time < end_cutoff and asset.get('ignition') is False:
                # Last ignition off event was before the end cutoff
                results['early_ends'].append({
                    'asset_id': asset_id,
                    'asset_label': asset.get('label'),
                    'driver': driver_info.get('name'),
                    'location': asset.get('location'),
                    'end_time': event_time.strftime('%H:%M')
                })
                
                results['flagged_drivers'].append({
                    'driver': driver_info.get('name'),
                    'issue': 'Early End',
                    'asset': asset.get('label') or asset_id,
                    'location': asset.get('location'),
                    'details': f"Ended at {event_time.strftime('%H:%M')} (expected after {END_TIME_THRESHOLD.strftime('%H:%M')})",
                    'timestamp': yesterday.strftime('%Y-%m-%d')
                })
            
            # Not on job check
            job_site = determine_job_site(asset)
            if not job_site or 'office' in job_site.lower() or 'yard' in job_site.lower():
                # Asset was not on a job site
                results['not_on_job'].append({
                    'asset_id': asset_id,
                    'asset_label': asset.get('label'),
                    'driver': driver_info.get('name'),
                    'location': asset.get('location'),
                    'last_active': event_time.strftime('%H:%M')
                })
                
                results['flagged_drivers'].append({
                    'driver': driver_info.get('name'),
                    'issue': 'Not On Job',
                    'asset': asset.get('label') or asset_id,
                    'location': asset.get('location') or 'Unknown',
                    'details': f"Not at job site during work hours",
                    'timestamp': yesterday.strftime('%Y-%m-%d')
                })
    
    return results

def generate_email_body(report_data, report_type):
    """
    Generate email body text for the report
    
    Args:
        report_data (dict): The report data
        report_type (str): 'same_day' or 'prior_day'
    
    Returns:
        str: Formatted email body text
    """
    today = datetime.now().strftime('%m/%d/%Y')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%m/%d/%Y')
    
    if report_type == 'same_day':
        subject = f"DAILY REPORT: Same-Day Late Start & Not On Job Report - {today}"
        date_string = today
    else:
        subject = f"DAILY REPORT: Prior-Day (Late Start, Early End, Not On Job) - {yesterday}"
        date_string = yesterday
    
    # Start building the email body
    body = f"""
SYSTEMSMITH FLEET REPORT: {date_string}
=========================================================

"""
    
    # Summary section
    body += f"""
SUMMARY:
--------
Total Drivers Analyzed: {report_data.get('total_drivers', 0)}
Total Issues Detected: {len(report_data.get('flagged_drivers', []))}
  - Late Starts: {len(report_data.get('late_starts', []))}
"""
    
    if report_type == 'prior_day':
        body += f"  - Early Ends: {len(report_data.get('early_ends', []))}\n"
    
    body += f"  - Not On Job: {len(report_data.get('not_on_job', []))}\n\n"
    
    # Flagged drivers section
    if report_data.get('flagged_drivers'):
        body += """
FLAGGED DRIVERS:
---------------
"""
        for idx, driver in enumerate(report_data.get('flagged_drivers', []), 1):
            body += f"{idx}. {driver.get('driver', 'Unknown Driver')} - {driver.get('issue')}\n"
            body += f"   Asset: {driver.get('asset', 'Unknown')}\n"
            body += f"   Location: {driver.get('location', 'Unknown')}\n"
            body += f"   Details: {driver.get('details', '')}\n\n"
    else:
        body += """
FLAGGED DRIVERS:
---------------
None - All drivers are compliant today!

"""
    
    # Footer section
    body += f"""
=========================================================
This report was automatically generated on {datetime.now().strftime('%m/%d/%Y at %H:%M:%S')}
by SYSTEMSMITH FLEET INTELLIGENCE SYSTEM.

For questions, please contact the fleet management team.
"""
    
    return body

def generate_same_day_report(assets=None):
    """
    Generate the same-day LS/NOJ report
    
    Args:
        assets (list, optional): List of asset dictionaries. If None, data will be fetched.
    
    Returns:
        dict: Report data including email body and recipients
    """
    logger.info("Generating same-day LS/NOJ report")
    
    if assets is None:
        # Need to fetch assets if not provided
        logger.warning("No assets provided for same-day report. Unable to continue.")
        return None
    
    # Analyze attendance
    analysis = analyze_attendance_same_day(assets)
    
    # Generate email body
    email_body = generate_email_body(analysis, 'same_day')
    
    # Add report metadata
    report_data = {
        'type': 'same_day',
        'generated_at': datetime.now().isoformat(),
        'data': analysis,
        'email_body': email_body,
        'recipients': [
            'fleet_manager@example.com',
            'operations@example.com'
        ],
        'flagged_drivers': analysis.get('flagged_drivers', [])
    }
    
    # Save report to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(REPORTS_DIR, f'same_day_report_{timestamp}.json')
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Same-day report saved to {report_file}")
    except Exception as e:
        logger.error(f"Failed to save same-day report: {e}")
    
    return report_data

def generate_prior_day_report(assets=None):
    """
    Generate the prior-day LS/EE/NOJ report
    
    Args:
        assets (list, optional): List of asset dictionaries. If None, data will be fetched.
    
    Returns:
        dict: Report data including email body and recipients
    """
    logger.info("Generating prior-day LS/EE/NOJ report")
    
    if assets is None:
        # Need to fetch assets if not provided
        logger.warning("No assets provided for prior-day report. Unable to continue.")
        return None
    
    # Analyze attendance
    analysis = analyze_attendance_prior_day(assets)
    
    # Generate email body
    email_body = generate_email_body(analysis, 'prior_day')
    
    # Add report metadata
    report_data = {
        'type': 'prior_day',
        'generated_at': datetime.now().isoformat(),
        'data': analysis,
        'email_body': email_body,
        'recipients': [
            'fleet_manager@example.com',
            'operations@example.com',
            'hr@example.com'  # HR included for attendance issues
        ],
        'flagged_drivers': analysis.get('flagged_drivers', [])
    }
    
    # Save report to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(REPORTS_DIR, f'prior_day_report_{timestamp}.json')
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Prior-day report saved to {report_file}")
    except Exception as e:
        logger.error(f"Failed to save prior-day report: {e}")
    
    return report_data

# Testing function
if __name__ == "__main__":
    # Test the report generation
    from gauge_api import get_asset_data
    
    assets = get_asset_data(force_update=False)
    
    if assets:
        # Generate same-day report
        same_day_report = generate_same_day_report(assets)
        print(f"Generated same-day report with {len(same_day_report['flagged_drivers'])} flagged drivers")
        
        # Generate prior-day report
        prior_day_report = generate_prior_day_report(assets)
        print(f"Generated prior-day report with {len(prior_day_report['flagged_drivers'])} flagged drivers")
    else:
        print("No asset data available for testing")