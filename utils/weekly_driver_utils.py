"""
Weekly Driver Report Utilities

This module provides common utility functions for processing weekly driver report data
and generating reports. It consolidates the functionality from other utility modules
to ensure consistent operation.
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta

import pandas as pd

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_weekly_driver_data(files, start_date, end_date):
    """
    Process weekly driver data from uploaded files
    
    Args:
        files (list): List of file paths to process
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        dict: Processed driver data report
    """
    logger.info(f"Processing weekly driver data for {start_date} to {end_date}")
    
    # Process files based on type
    driving_history_files = [f for f in files if "DrivingHistory" in f]
    activity_detail_files = [f for f in files if "ActivityDetail" in f]
    time_on_site_files = [f for f in files if "TimeOnSite" in f]
    timecard_files = [f for f in files if "Timecard" in f]
    
    # Extract driver data from files
    drivers = extract_driver_data(
        driving_history_files, 
        activity_detail_files, 
        time_on_site_files, 
        timecard_files
    )
    
    # Generate report file
    report = {
        "start_date": start_date,
        "end_date": end_date,
        "generated_at": datetime.now().isoformat(),
        "drivers": drivers
    }
    
    # Save report to JSON file
    reports_dir = os.path.join(os.getcwd(), 'reports', 'weekly_driver_reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    report_filename = f"weekly_driver_report_{start_date}_to_{end_date}.json"
    report_path = os.path.join(reports_dir, report_filename)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Weekly driver report saved to {report_path}")
    return report

def extract_driver_data(driving_history_files, activity_detail_files, time_on_site_files, timecard_files):
    """
    Extract driver data from various files
    
    Args:
        driving_history_files (list): List of DrivingHistory file paths
        activity_detail_files (list): List of ActivityDetail file paths
        time_on_site_files (list): List of TimeOnSite file paths
        timecard_files (list): List of Timecard file paths
        
    Returns:
        list: List of driver data records
    """
    # Placeholder for driver data
    drivers = []
    
    # Sample driver data structure
    # This would normally be replaced with real data from files
    sample_driver = {
        "name": "John Doe",
        "employee_id": "E123456",
        "attendance": {
            "2025-05-18": "On Time",
            "2025-05-19": "Late Start (15 min)",
            "2025-05-20": "On Time",
            "2025-05-21": "Early End (30 min)",
            "2025-05-22": "On Time",
            "2025-05-23": "On Time",
            "2025-05-24": "Not On Job"
        },
        "job_sites": {
            "2025-05-18": "Site A",
            "2025-05-19": "Site B",
            "2025-05-20": "Site B",
            "2025-05-21": "Site C",
            "2025-05-22": "Site A",
            "2025-05-23": "Site A",
            "2025-05-24": ""
        },
        "log_on_times": {
            "2025-05-18": "07:00",
            "2025-05-19": "07:15",
            "2025-05-20": "06:55",
            "2025-05-21": "07:05",
            "2025-05-22": "07:00",
            "2025-05-23": "06:50",
            "2025-05-24": ""
        },
        "log_off_times": {
            "2025-05-18": "17:00",
            "2025-05-19": "17:00",
            "2025-05-20": "17:00",
            "2025-05-21": "16:30",
            "2025-05-22": "17:00",
            "2025-05-23": "17:00",
            "2025-05-24": ""
        },
        "timecard_hours": {
            "2025-05-18": "",
            "2025-05-19": "9.75",
            "2025-05-20": "10.0",
            "2025-05-21": "9.5",
            "2025-05-22": "10.0",
            "2025-05-23": "10.0",
            "2025-05-24": ""
        }
    }
    
    # In a real implementation, this would be replaced with actual data processing
    # For now, using a placeholder
    drivers.append(sample_driver)
    
    return drivers

def process_may_timecard_data(timecard_file, start_date, end_date):
    """
    Process May timecard data for weekly report
    
    Args:
        timecard_file (str): Path to timecard Excel file
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        dict: Processed report data
    """
    logger.info(f"Processing May timecard data for {start_date} to {end_date}")
    
    attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
    
    # Load DrivingHistory files
    driving_history_files = [
        os.path.join(attached_assets_dir, f) for f in os.listdir(attached_assets_dir) 
        if "DrivingHistory" in f and f.endswith(".csv")
    ]
    
    # Load ActivityDetail files
    activity_detail_files = [
        os.path.join(attached_assets_dir, f) for f in os.listdir(attached_assets_dir) 
        if "ActivityDetail" in f and f.endswith(".csv")
    ]
    
    # Generate a list of dates in the range
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    date_range = []
    current_date = start_date_obj
    while current_date <= end_date_obj:
        date_range.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Extract real driver names and data
    driver_data = extract_may_driver_data(driving_history_files, activity_detail_files, timecard_file, date_range)
    
    # Generate report
    report = {
        "start_date": start_date,
        "end_date": end_date,
        "generated_at": datetime.now().isoformat(),
        "drivers": driver_data
    }
    
    # Save report to JSON file
    reports_dir = os.path.join(os.getcwd(), 'reports', 'weekly_driver_reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    report_filename = f"weekly_driver_report_{start_date}_to_{end_date}.json"
    report_path = os.path.join(reports_dir, report_filename)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"May weekly driver report saved to {report_path}")
    return report

def extract_may_driver_data(driving_history_files, activity_detail_files, timecard_file, date_range):
    """
    Extract driver data for May report
    
    Args:
        driving_history_files (list): List of DrivingHistory file paths
        activity_detail_files (list): List of ActivityDetail file paths
        timecard_file (str): Path to timecard Excel file
        date_range (list): List of dates in YYYY-MM-DD format
        
    Returns:
        list: List of driver data records
    """
    # Extract data from all files
    driving_data = extract_driving_history(driving_history_files, date_range)
    activity_data = extract_activity_detail(activity_detail_files, date_range)
    timecard_data = extract_timecard_data(timecard_file, date_range)
    
    # Combine data by driver name
    all_drivers = set(list(driving_data.keys()) + list(activity_data.keys()) + list(timecard_data.keys()))
    logger.info(f"Found {len(all_drivers)} unique drivers across all data sources")
    
    # Create driver records
    driver_records = []
    for driver_name in all_drivers:
        # Skip empty driver names
        if not driver_name or driver_name.lower() == 'nan':
            continue
            
        # Create record structure
        record = {
            "name": driver_name,
            "employee_id": get_employee_id(driver_name, timecard_data),
            "attendance": {},
            "job_sites": {},
            "log_on_times": {},
            "log_off_times": {},
            "timecard_hours": {}
        }
        
        # Fill in data for each day
        for date in date_range:
            # Get driving data for this driver and date
            driver_driving = driving_data.get(driver_name, {}).get(date, {})
            driver_activity = activity_data.get(driver_name, {}).get(date, {})
            driver_timecard = timecard_data.get(driver_name, {}).get(date, {})
            
            # Determine status based on data
            status = determine_status(driver_driving, driver_activity, driver_timecard)
            
            # Fill in record for this day
            record["attendance"][date] = status
            record["job_sites"][date] = driver_driving.get("job_site", "") or driver_activity.get("job_site", "")
            record["log_on_times"][date] = driver_driving.get("log_on_time", "") or driver_activity.get("start_time", "")
            record["log_off_times"][date] = driver_driving.get("log_off_time", "") or driver_activity.get("end_time", "")
            record["timecard_hours"][date] = driver_timecard.get("hours", "")
        
        # Add timecard and GPS comparison data
        if driver_name in timecard_data:
            record["timecard_data"] = True
            record["timecard_comparison"] = compare_timecard_gps(record)
        
        driver_records.append(record)
    
    # Sort by driver name
    driver_records.sort(key=lambda x: x["name"])
    
    return driver_records

def extract_driving_history(files, date_range):
    """Extract data from DrivingHistory files"""
    driving_data = {}
    
    for file in files:
        try:
            df = pd.read_csv(file, encoding='utf-8')
            
            # Filter data in the date range
            for _, row in df.iterrows():
                try:
                    # Skip rows with missing driver or date
                    if pd.isna(row.get('Driver')) or pd.isna(row.get('Date')):
                        continue
                    
                    # Parse date
                    try:
                        date_obj = pd.to_datetime(row['Date'])
                        date_str = date_obj.strftime('%Y-%m-%d')
                        
                        # Skip if not in date range
                        if date_str not in date_range:
                            continue
                    except:
                        continue
                    
                    # Get driver name
                    driver_name = str(row['Driver']).strip()
                    
                    # Initialize data structures if needed
                    if driver_name not in driving_data:
                        driving_data[driver_name] = {}
                    
                    if date_str not in driving_data[driver_name]:
                        driving_data[driver_name][date_str] = {}
                    
                    # Extract job site if available
                    job_site = str(row.get('Job Number', '')) if not pd.isna(row.get('Job Number', '')) else ""
                    
                    # Extract times if available
                    log_on_time = ""
                    log_off_time = ""
                    
                    if 'First Key On' in row and not pd.isna(row['First Key On']):
                        try:
                            first_key = pd.to_datetime(row['First Key On'])
                            log_on_time = first_key.strftime('%H:%M')
                        except:
                            pass
                    
                    if 'Last Key Off' in row and not pd.isna(row['Last Key Off']):
                        try:
                            last_key = pd.to_datetime(row['Last Key Off'])
                            log_off_time = last_key.strftime('%H:%M')
                        except:
                            pass
                    
                    # Update record
                    driving_data[driver_name][date_str] = {
                        "job_site": job_site,
                        "log_on_time": log_on_time,
                        "log_off_time": log_off_time
                    }
                    
                except Exception as e:
                    logger.error(f"Error processing driving history row: {str(e)}")
                    continue
                
        except Exception as e:
            logger.error(f"Error processing driving history file {file}: {str(e)}")
            continue
    
    return driving_data

def extract_activity_detail(files, date_range):
    """Extract data from ActivityDetail files"""
    activity_data = {}
    
    for file in files:
        try:
            df = pd.read_csv(file, encoding='utf-8')
            
            # Filter data in the date range
            for _, row in df.iterrows():
                try:
                    # Skip rows with missing driver or date
                    if pd.isna(row.get('Driver')) or pd.isna(row.get('Date')):
                        continue
                    
                    # Parse date
                    try:
                        date_obj = pd.to_datetime(row['Date'])
                        date_str = date_obj.strftime('%Y-%m-%d')
                        
                        # Skip if not in date range
                        if date_str not in date_range:
                            continue
                    except:
                        continue
                    
                    # Get driver name
                    driver_name = str(row['Driver']).strip()
                    
                    # Initialize data structures if needed
                    if driver_name not in activity_data:
                        activity_data[driver_name] = {}
                    
                    if date_str not in activity_data[driver_name]:
                        activity_data[driver_name][date_str] = {}
                    
                    # Extract job site if available
                    job_site = str(row.get('Job Site', '')) if not pd.isna(row.get('Job Site', '')) else ""
                    
                    # Extract times if available
                    start_time = ""
                    end_time = ""
                    
                    if 'Start Time' in row and not pd.isna(row['Start Time']):
                        try:
                            start = pd.to_datetime(row['Start Time'])
                            start_time = start.strftime('%H:%M')
                        except:
                            pass
                    
                    if 'End Time' in row and not pd.isna(row['End Time']):
                        try:
                            end = pd.to_datetime(row['End Time'])
                            end_time = end.strftime('%H:%M')
                        except:
                            pass
                    
                    # Update record
                    activity_data[driver_name][date_str] = {
                        "job_site": job_site,
                        "start_time": start_time,
                        "end_time": end_time
                    }
                    
                except Exception as e:
                    logger.error(f"Error processing activity detail row: {str(e)}")
                    continue
                
        except Exception as e:
            logger.error(f"Error processing activity detail file {file}: {str(e)}")
            continue
    
    return activity_data

def extract_timecard_data(timecard_file, date_range):
    """Extract data from timecard Excel file"""
    timecard_data = {}
    
    try:
        # Load Excel file
        df = pd.read_excel(timecard_file)
        
        # Extract employee IDs and names
        employee_ids = {}
        name_pattern = re.compile(r'^(.+?),\s*(.+?)(?:\s+\((\d+)\))?$')
        
        for _, row in df.iterrows():
            try:
                # Skip rows with missing name
                if pd.isna(row.get('Employee')):
                    continue
                
                # Parse employee name and ID
                employee = str(row['Employee']).strip()
                match = name_pattern.match(employee)
                
                if match:
                    last_name = match.group(1).strip()
                    first_name = match.group(2).strip()
                    employee_id = match.group(3) if match.group(3) else ""
                    
                    full_name = f"{first_name} {last_name}"
                    employee_ids[full_name] = employee_id
                    
                    # Initialize timecard data
                    if full_name not in timecard_data:
                        timecard_data[full_name] = {}
                    
                    # Extract hours for each date
                    for date_str in date_range:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        col_name = date_obj.strftime('%-m/%-d/%Y')  # Format to match Excel column
                        
                        if col_name in row and not pd.isna(row[col_name]):
                            hours = str(row[col_name])
                            
                            if date_str not in timecard_data[full_name]:
                                timecard_data[full_name][date_str] = {}
                            
                            timecard_data[full_name][date_str]["hours"] = hours
            
            except Exception as e:
                logger.error(f"Error processing timecard row: {str(e)}")
                continue
        
    except Exception as e:
        logger.error(f"Error processing timecard file {timecard_file}: {str(e)}")
    
    return timecard_data

def get_employee_id(driver_name, timecard_data):
    """Get employee ID for a driver"""
    if driver_name in timecard_data:
        # Employee IDs are stored at the timecard_data[driver_name]["employee_id"] level
        return timecard_data.get(driver_name, {}).get("employee_id", "")
    return ""

def determine_status(driving_data, activity_data, timecard_data):
    """Determine driver status based on available data"""
    # If no data for this day, driver was not on job
    if not driving_data and not activity_data and not timecard_data:
        return "Not On Job"
    
    # Check if we have times from driving or activity data
    log_on_time = driving_data.get("log_on_time", "") or activity_data.get("start_time", "")
    log_off_time = driving_data.get("log_off_time", "") or activity_data.get("end_time", "")
    
    # If we have timecard hours but no GPS data
    if timecard_data and not (log_on_time or log_off_time):
        return "Timecard Only - No GPS"
    
    # If we have no times, driver was not on job
    if not log_on_time and not log_off_time:
        return "Not On Job"
    
    # Check for late start (after 7:00 AM)
    if log_on_time:
        try:
            on_time = datetime.strptime(log_on_time, '%H:%M')
            target_time = datetime.strptime('07:00', '%H:%M')
            
            if on_time > target_time:
                minutes_late = (on_time - target_time).seconds // 60
                return f"Late Start ({minutes_late} min)"
        except:
            pass
    
    # Check for early end (before 5:00 PM)
    if log_off_time:
        try:
            off_time = datetime.strptime(log_off_time, '%H:%M')
            target_time = datetime.strptime('17:00', '%H:%M')
            
            if off_time < target_time:
                minutes_early = (target_time - off_time).seconds // 60
                return f"Early End ({minutes_early} min)"
        except:
            pass
    
    # If passed all checks, driver was on time
    return "On Time"

def compare_timecard_gps(driver_record):
    """Compare timecard hours with GPS log times"""
    comparison = {"matches": 0, "discrepancies": 0, "dates": {}}
    
    for date, hours in driver_record.get("timecard_hours", {}).items():
        if not hours:
            continue
        
        log_on = driver_record.get("log_on_times", {}).get(date, "")
        log_off = driver_record.get("log_off_times", {}).get(date, "")
        
        if not log_on or not log_off:
            comparison["dates"][date] = "No GPS data for comparison"
            comparison["discrepancies"] += 1
            continue
        
        try:
            timecard_hours = float(hours)
            
            on_time = datetime.strptime(log_on, '%H:%M')
            off_time = datetime.strptime(log_off, '%H:%M')
            
            gps_hours = (off_time - on_time).seconds / 3600
            
            difference = abs(timecard_hours - gps_hours)
            
            if difference <= 0.25:  # Within 15 minutes
                comparison["dates"][date] = "Matches"
                comparison["matches"] += 1
            else:
                comparison["dates"][date] = f"Discrepancy of {difference:.1f} hours"
                comparison["discrepancies"] += 1
        except:
            comparison["dates"][date] = "Could not compare"
            comparison["discrepancies"] += 1
    
    return comparison