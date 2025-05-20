"""
Consistency Engine for Driver Status Determination

This module provides a consistent way to determine driver status (late, early end, not on job)
based on various data sources, ensuring uniform status computation throughout the application.
"""

import os
import json
import logging
from datetime import datetime, time, timedelta
import traceback

# Setup logging
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('logs/consistency_engine.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# Constants for status determination
SCHEDULED_START_TIME = time(5, 0)  # 5:00 AM default start time if not specified
SCHEDULED_END_TIME = time(15, 30)  # 3:30 PM default end time if not specified
LATE_THRESHOLD_MINUTES = 15  # Minutes after scheduled start to be considered late
EARLY_END_THRESHOLD_MINUTES = 30  # Minutes before scheduled end to be considered early

def compute_driver_status(driver, assignment_time=None, telematics_data=None):
    """
    Compute the status of a driver based on assignment time and telematics data
    
    Args:
        driver (dict): Driver information with asset, name, etc.
        assignment_time (dict): Scheduled times for the driver
        telematics_data (dict): GPS and activity data from telematics
        
    Returns:
        dict: Driver record with computed status and relevant timestamps
    """
    try:
        # Start with a copy of the driver data
        result = driver.copy()
        
        # Default status is "Unknown" until determined
        result['status'] = "Unknown"
        result['status_reason'] = None
        
        # Get scheduled times (with defaults if not provided)
        scheduled_start = None
        scheduled_end = None
        
        if assignment_time:
            if 'start_time' in assignment_time and assignment_time['start_time']:
                # Parse scheduled start time
                if isinstance(assignment_time['start_time'], str):
                    try:
                        # Try different time formats
                        for fmt in ['%I:%M %p', '%H:%M', '%H:%M:%S']:
                            try:
                                scheduled_start = datetime.strptime(assignment_time['start_time'], fmt).time()
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logger.error(f"Error parsing scheduled start time: {e}")
                
                elif isinstance(assignment_time['start_time'], time):
                    scheduled_start = assignment_time['start_time']
                    
                elif isinstance(assignment_time['start_time'], datetime):
                    scheduled_start = assignment_time['start_time'].time()
            
            if 'end_time' in assignment_time and assignment_time['end_time']:
                # Parse scheduled end time
                if isinstance(assignment_time['end_time'], str):
                    try:
                        # Try different time formats
                        for fmt in ['%I:%M %p', '%H:%M', '%H:%M:%S']:
                            try:
                                scheduled_end = datetime.strptime(assignment_time['end_time'], fmt).time()
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logger.error(f"Error parsing scheduled end time: {e}")
                
                elif isinstance(assignment_time['end_time'], time):
                    scheduled_end = assignment_time['end_time']
                    
                elif isinstance(assignment_time['end_time'], datetime):
                    scheduled_end = assignment_time['end_time'].time()
        
        # Use defaults if not provided
        if not scheduled_start:
            scheduled_start = SCHEDULED_START_TIME
            logger.debug(f"Using default scheduled start time {scheduled_start} for driver {driver.get('name', 'Unknown')}")
            
        if not scheduled_end:
            scheduled_end = SCHEDULED_END_TIME
            logger.debug(f"Using default scheduled end time {scheduled_end} for driver {driver.get('name', 'Unknown')}")
        
        # Store scheduled times in result
        result['scheduled_start'] = scheduled_start.strftime('%I:%M %p')
        result['scheduled_end'] = scheduled_end.strftime('%I:%M %p')
        
        # Check telematics data
        if not telematics_data:
            result['status'] = "Not On Job"
            result['status_reason'] = "No telematics data available"
            logger.warning(f"No telematics data available for driver {driver.get('name', 'Unknown')}, marking as Not On Job")
            
            # Set arrival and departure to N/A
            result['arrival'] = "N/A"
            result['departure'] = "N/A"
            result['key_on_time'] = "N/A"
            result['key_off_time'] = "N/A"
            
            return result
        
        # Get actual start and end times from telematics
        actual_start = None
        actual_end = None
        
        # Process first_activity (key on) time
        if 'first_activity' in telematics_data and telematics_data['first_activity']:
            if isinstance(telematics_data['first_activity'], (int, float)) and telematics_data['first_activity'] > 1000000000000:
                # Unix timestamp in milliseconds
                actual_start = datetime.fromtimestamp(telematics_data['first_activity'] / 1000)
            elif isinstance(telematics_data['first_activity'], str):
                # Parse string timestamp
                try:
                    for fmt in ['%I:%M %p', '%H:%M', '%Y-%m-%d %H:%M:%S']:
                        try:
                            actual_start = datetime.strptime(telematics_data['first_activity'], fmt)
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    logger.error(f"Error parsing actual start time: {e}")
            elif isinstance(telematics_data['first_activity'], datetime):
                actual_start = telematics_data['first_activity']
        
        # Process last_activity (key off) time
        if 'last_activity' in telematics_data and telematics_data['last_activity']:
            if isinstance(telematics_data['last_activity'], (int, float)) and telematics_data['last_activity'] > 1000000000000:
                # Unix timestamp in milliseconds
                actual_end = datetime.fromtimestamp(telematics_data['last_activity'] / 1000)
            elif isinstance(telematics_data['last_activity'], str):
                # Parse string timestamp
                try:
                    for fmt in ['%I:%M %p', '%H:%M', '%Y-%m-%d %H:%M:%S']:
                        try:
                            actual_end = datetime.strptime(telematics_data['last_activity'], fmt)
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    logger.error(f"Error parsing actual end time: {e}")
            elif isinstance(telematics_data['last_activity'], datetime):
                actual_end = telematics_data['last_activity']
        
        # If no actual start/end times, mark as Not On Job
        if not actual_start and not actual_end:
            result['status'] = "Not On Job"
            result['status_reason'] = "No activity times recorded"
            logger.warning(f"No activity times recorded for driver {driver.get('name', 'Unknown')}, marking as Not On Job")
            
            # Set arrival and departure to N/A
            result['arrival'] = "N/A"
            result['departure'] = "N/A"
            result['key_on_time'] = "N/A"
            result['key_off_time'] = "N/A"
            
            return result
        
        # Store actual times in result
        if actual_start:
            result['arrival'] = actual_start.strftime('%I:%M %p')
            result['key_on_time'] = actual_start.strftime('%I:%M %p')
            
            # For comparison, convert actual start to the same date as scheduled start
            actual_start_time = actual_start.time()
        else:
            result['arrival'] = "N/A"
            result['key_on_time'] = "N/A"
            actual_start_time = None
        
        if actual_end:
            result['departure'] = actual_end.strftime('%I:%M %p')
            result['key_off_time'] = actual_end.strftime('%I:%M %p')
            
            # For comparison, convert actual end to the same date as scheduled end
            actual_end_time = actual_end.time()
        else:
            result['departure'] = "N/A"
            result['key_off_time'] = "N/A"
            actual_end_time = None
        
        # Calculate time on site if both start and end are available
        if actual_start and actual_end:
            time_diff = actual_end - actual_start
            hours, remainder = divmod(time_diff.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            result['time_on_site'] = f"{int(hours):02d}:{int(minutes):02d} hrs"
        else:
            result['time_on_site'] = "N/A"
        
        # Check job site mismatch (not on job)
        if 'job_site' in telematics_data and 'assigned_site' in assignment_time:
            if telematics_data.get('job_site') != assignment_time.get('assigned_site'):
                result['status'] = "NOJ"
                result['status_reason'] = "At incorrect job site"
                result['assigned_site'] = assignment_time.get('assigned_site', 'Unknown')
                result['actual_site'] = telematics_data.get('job_site', 'Unknown')
                logger.info(f"Driver {driver.get('name', 'Unknown')} at incorrect job site: "
                           f"Assigned={assignment_time.get('assigned_site', 'Unknown')}, "
                           f"Actual={telematics_data.get('job_site', 'Unknown')}")
                
                # Update issue type for reporting
                result['issue_type'] = "not_on_job"
                
                return result
        
        # Determine status based on arrival time (Late)
        if actual_start_time:
            # Convert times to comparable format (minutes since midnight)
            scheduled_minutes = scheduled_start.hour * 60 + scheduled_start.minute
            actual_minutes = actual_start_time.hour * 60 + actual_start_time.minute
            
            # Check if arrival is late
            if actual_minutes > scheduled_minutes + LATE_THRESHOLD_MINUTES:
                result['status'] = "Late"
                minutes_late = actual_minutes - scheduled_minutes
                result['minutes_late'] = minutes_late
                result['status_reason'] = f"{minutes_late} minutes late"
                logger.info(f"Driver {driver.get('name', 'Unknown')} arrived late: "
                           f"Scheduled={scheduled_start}, Actual={actual_start_time}, "
                           f"{minutes_late} minutes late")
                
                # Update issue type for reporting
                result['issue_type'] = "late_start"
                
                return result
        
        # Determine status based on departure time (Early End)
        if actual_end_time:
            # Convert times to comparable format (minutes since midnight)
            scheduled_minutes = scheduled_end.hour * 60 + scheduled_end.minute
            actual_minutes = actual_end_time.hour * 60 + actual_end_time.minute
            
            # Check if departure is early
            if actual_minutes < scheduled_minutes - EARLY_END_THRESHOLD_MINUTES:
                result['status'] = "Early End"
                minutes_early = scheduled_minutes - actual_minutes
                result['minutes_early'] = minutes_early
                result['status_reason'] = f"{minutes_early} minutes early"
                logger.info(f"Driver {driver.get('name', 'Unknown')} left early: "
                           f"Scheduled={scheduled_end}, Actual={actual_end_time}, "
                           f"{minutes_early} minutes early")
                
                # Update issue type for reporting
                result['issue_type'] = "early_end"
                
                return result
        
        # If no issues found, mark as On Time
        result['status'] = "On Time"
        logger.debug(f"Driver {driver.get('name', 'Unknown')} is on time")
        
        return result
    
    except Exception as e:
        logger.error(f"Error computing driver status: {e}")
        logger.error(traceback.format_exc())
        
        # Return driver with error status
        driver['status'] = "Error"
        driver['status_reason'] = str(e)
        return driver

def build_driver_summary(drivers, assignment_data, telematics_data):
    """
    Build a comprehensive driver summary with computed statuses
    
    Args:
        drivers (list): List of driver records
        assignment_data (dict): Dictionary of driver assignments by driver ID/name
        telematics_data (dict): Dictionary of telematics data by driver ID/name
        
    Returns:
        dict: Driver summary with computed statuses and counts
    """
    driver_summary = []
    
    for driver in drivers:
        driver_id = driver.get('employee_id') or driver.get('driver_id') or driver.get('id')
        driver_name = driver.get('name') or driver.get('driver_name')
        
        # Skip if no identifier is available
        if not driver_id and not driver_name:
            logger.warning(f"Skipping driver with no ID or name: {driver}")
            continue
        
        # Get assignment data for this driver
        driver_assignment = None
        if driver_id and driver_id in assignment_data:
            driver_assignment = assignment_data[driver_id]
        elif driver_name and driver_name in assignment_data:
            driver_assignment = assignment_data[driver_name]
        
        # Get telematics data for this driver
        driver_telematics = None
        if driver_id and driver_id in telematics_data:
            driver_telematics = telematics_data[driver_id]
        elif driver_name and driver_name in telematics_data:
            driver_telematics = telematics_data[driver_name]
        
        # Compute status
        driver_record = compute_driver_status(driver, driver_assignment, driver_telematics)
        
        # Add to summary
        driver_summary.append(driver_record)
    
    # Count summary statistics
    on_time_drivers = [d for d in driver_summary if d['status'] == 'On Time']
    late_drivers = [d for d in driver_summary if d['status'] == 'Late']
    early_end_drivers = [d for d in driver_summary if d['status'] == 'Early End']
    not_on_job_drivers = [d for d in driver_summary if d['status'] in ['Not On Job', 'NOJ']]
    
    # Calculate summary metrics
    total_drivers = len(driver_summary)
    total_morning_drivers = len(on_time_drivers) + len(late_drivers) + len(not_on_job_drivers)
    on_time_percent = 100 * len(on_time_drivers) / total_drivers if total_drivers > 0 else 0
    
    # Create summary dictionary
    summary = {
        'total_drivers': total_drivers,
        'total_morning_drivers': total_morning_drivers,
        'on_time_drivers': len(on_time_drivers),
        'late_drivers': len(late_drivers),
        'early_end_drivers': len(early_end_drivers),
        'not_on_job_drivers': len(not_on_job_drivers),
        'exception_drivers': len(late_drivers) + len(early_end_drivers) + len(not_on_job_drivers),
        'total_issues': len(late_drivers) + len(early_end_drivers) + len(not_on_job_drivers),
        'on_time_percent': round(on_time_percent, 1)
    }
    
    # Log summary
    logger.info(f"Driver summary: {summary}")
    
    # Create result
    result = {
        'driver_summary': driver_summary,
        'summary': summary,
        'late_drivers': late_drivers,
        'early_end_drivers': early_end_drivers,
        'not_on_job_drivers': not_on_job_drivers
    }
    
    return result

def generate_daily_report(date_str, driver_summary):
    """
    Generate a daily report from the driver summary
    
    Args:
        date_str (str): Report date in YYYY-MM-DD format
        driver_summary (dict): Driver summary with computed statuses
        
    Returns:
        dict: Daily report data
    """
    # Parse date string
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    report_date = date_obj.strftime('%A, %B %d, %Y')
    
    # Create report
    report = {
        'date': date_str,
        'report_date': report_date,
        'drivers': driver_summary['driver_summary'],
        'total_drivers': driver_summary['summary']['total_drivers'],
        'total_morning_drivers': driver_summary['summary']['total_morning_drivers'],
        'on_time_count': driver_summary['summary']['on_time_drivers'],
        'late_morning': driver_summary['late_drivers'],
        'early_departures': driver_summary['early_end_drivers'],
        'not_on_job_drivers': driver_summary['not_on_job_drivers'],
        'summary': driver_summary['summary']
    }
    
    # Save report
    exports_dir = 'exports/daily_reports'
    os.makedirs(exports_dir, exist_ok=True)
    report_file = f"{exports_dir}/daily_report_{date_str}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Daily report generated for {date_str} with {report['total_drivers']} drivers")
    
    return report