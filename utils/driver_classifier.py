"""
TRAXORA GENIUS CORE | Driver Classifier Module

This module implements the classification logic from the master sheet,
determining status like:
- On Time
- Late
- Early End
- Not On Job

Following strict workbook logic hierarchy from 'Start Time & Job' sheet.
"""
import logging
from datetime import datetime, time, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Classification constants
ON_TIME = 'On Time'
LATE = 'Late'
EARLY_END = 'Early End'
NOT_ON_JOB = 'Not On Job'
UNKNOWN = 'Unknown'

# Time thresholds (configurable)
LATE_THRESHOLD_MINUTES = 15
EARLY_END_THRESHOLD_MINUTES = 15


def classify_driver(driver_data, scheduled_start=None, scheduled_end=None, job_site=None, 
                    job_assignments=None, asset_data=None, geo_validations=None):
    """
    Classify a driver's status based on workbook logic

    Args:
        driver_data (dict): Driver data including actual start/end times and locations
        scheduled_start (time): Scheduled start time
        scheduled_end (time): Scheduled end time
        job_site (dict): Job site info
        job_assignments (dict): Job assignments from master sheet
        asset_data (dict): Asset data from Asset List
        geo_validations (list): Geo-validation results from geo_validator

    Returns:
        dict: Classification results with status, reasons, etc.
    """
    # Initialize results
    classification = {
        'status': UNKNOWN,
        'minutes_late': 0,
        'minutes_early_end': 0,
        'reasons': [],
        'validation_score': 0,
        'data_sources': []
    }

    # Track data sources for full traceability
    if 'sources' in driver_data:
        for source, data in driver_data['sources'].items():
            classification['data_sources'].append(source)

    # Skip classification if no scheduled times
    if not scheduled_start or not scheduled_end:
        classification['status'] = UNKNOWN
        classification['reasons'].append("No scheduled times available")
        return classification

    # Get actual start/end times
    actual_start = driver_data.get('actual_start_time')
    actual_end = driver_data.get('actual_end_time')

    # Check if driver has any activity data
    if not actual_start and not actual_end:
        classification['status'] = UNKNOWN
        classification['reasons'].append("No activity data available")
        return classification

    # Convert time objects to datetime for comparison
    today = datetime.now().date()
    sched_start_dt = datetime.combine(today, scheduled_start)
    sched_end_dt = datetime.combine(today, scheduled_end)
    
    # Check for late start
    if actual_start:
        actual_start_dt = datetime.combine(today, actual_start)
        
        # Calculate minutes late
        if actual_start_dt > sched_start_dt:
            delta = actual_start_dt - sched_start_dt
            minutes_late = int(delta.total_seconds() / 60)
            
            if minutes_late >= LATE_THRESHOLD_MINUTES:
                classification['status'] = LATE
                classification['minutes_late'] = minutes_late
                classification['reasons'].append(f"Started {minutes_late} minutes late")
    
    # Check for early end
    if actual_end:
        actual_end_dt = datetime.combine(today, actual_end)
        
        # Calculate minutes early end
        if actual_end_dt < sched_end_dt:
            delta = sched_end_dt - actual_end_dt
            minutes_early = int(delta.total_seconds() / 60)
            
            if minutes_early >= EARLY_END_THRESHOLD_MINUTES:
                # If already marked as LATE, keep that status
                if classification['status'] != LATE:
                    classification['status'] = EARLY_END
                classification['minutes_early_end'] = minutes_early
                classification['reasons'].append(f"Ended {minutes_early} minutes early")
    
    # Check Not On Job using geo-validation
    if geo_validations and job_site:
        # If driver was never at the assigned job site
        valid_locations = [v for v in geo_validations if v.get('is_valid')]
        
        if not valid_locations:
            # Override other classifications with NOT_ON_JOB
            classification['status'] = NOT_ON_JOB
            classification['reasons'] = ["Driver never at assigned job site"]
            # Keep timing info for reference
    
    # If no issues found and we have activity data, mark as On Time
    if classification['status'] == UNKNOWN and (actual_start or actual_end):
        classification['status'] = ON_TIME
        classification['reasons'] = ["Driver on time at assigned job"]
    
    # Calculate validation score (0-100)
    # Higher score = more confidence in the classification
    score = 0
    
    # Base score from data source quality
    if 'Asset List' in classification['data_sources']:
        score += 25  # Asset List is primary source of truth
    if 'Driving History' in classification['data_sources']:
        score += 25  # Driving history for time validation
    if 'Activity Detail' in classification['data_sources']:
        score += 25  # Activity detail for location validation
    
    # Penalize inconsistent data
    if len(classification['reasons']) > 1:
        score -= 10 * (len(classification['reasons']) - 1)
    
    # Ensure score is between 0-100
    classification['validation_score'] = max(0, min(100, score))
    
    return classification


def validate_job_assignment(driver_name, asset_id, job_number, assignments):
    """
    Validate job assignment from the master sheet

    Args:
        driver_name (str): Driver name
        asset_id (str): Asset ID
        job_number (str): Job number
        assignments (dict): Job assignments

    Returns:
        dict: Validation results
    """
    # Check if driver is assigned to this asset
    asset_match = False
    for assignment in assignments:
        if assignment.get('driver_name') == driver_name and assignment.get('asset_id') == asset_id:
            asset_match = True
            break
    
    # Check if asset is assigned to this job
    job_match = False
    for assignment in assignments:
        if assignment.get('asset_id') == asset_id and assignment.get('job_number') == job_number:
            job_match = True
            break
    
    return {
        'is_valid': asset_match and job_match,
        'asset_match': asset_match,
        'job_match': job_match,
        'validation_details': {
            'driver_name': driver_name,
            'asset_id': asset_id,
            'job_number': job_number
        }
    }


def get_status_counts(classifications):
    """
    Get counts for each status

    Args:
        classifications (list): List of classification results

    Returns:
        dict: Counts for each status
    """
    counts = {
        'total': len(classifications),
        'on_time': 0,
        'late': 0,
        'early_end': 0,
        'not_on_job': 0,
        'unknown': 0
    }
    
    for classification in classifications:
        status = classification.get('status', UNKNOWN).lower().replace(' ', '_')
        counts[status] = counts.get(status, 0) + 1
    
    return counts


def get_time_statistics(classifications):
    """
    Calculate time statistics for classifications

    Args:
        classifications (list): List of classification results

    Returns:
        dict: Time statistics
    """
    stats = {
        'avg_minutes_late': 0,
        'max_minutes_late': 0,
        'avg_minutes_early_end': 0,
        'max_minutes_early_end': 0,
        'late_drivers': [],
        'early_end_drivers': []
    }
    
    # Collect late and early end drivers
    late_minutes = []
    early_minutes = []
    
    for classification in classifications:
        if classification.get('status') == LATE:
            late_minutes.append(classification.get('minutes_late', 0))
            stats['late_drivers'].append({
                'driver_name': classification.get('driver_name', 'Unknown'),
                'minutes_late': classification.get('minutes_late', 0)
            })
        
        if classification.get('status') == EARLY_END:
            early_minutes.append(classification.get('minutes_early_end', 0))
            stats['early_end_drivers'].append({
                'driver_name': classification.get('driver_name', 'Unknown'),
                'minutes_early_end': classification.get('minutes_early_end', 0)
            })
    
    # Calculate averages and maximums
    if late_minutes:
        stats['avg_minutes_late'] = sum(late_minutes) / len(late_minutes)
        stats['max_minutes_late'] = max(late_minutes)
    
    if early_minutes:
        stats['avg_minutes_early_end'] = sum(early_minutes) / len(early_minutes)
        stats['max_minutes_early_end'] = max(early_minutes)
    
    # Sort drivers by minutes
    stats['late_drivers'].sort(key=lambda x: x['minutes_late'], reverse=True)
    stats['early_end_drivers'].sort(key=lambda x: x['minutes_early_end'], reverse=True)
    
    return stats