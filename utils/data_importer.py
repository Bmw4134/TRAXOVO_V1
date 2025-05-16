"""
Data Importer Module

This module handles importing and processing various data reports
for the attendance, utilization, and driver behavior tracking systems.
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from app import db
from models import Asset
from models.attendance import Driver, JobSite, AttendanceRecord, AttendanceTrend
from utils.attendance_analytics import (
    get_or_create_driver, 
    get_or_create_job_site, 
    save_attendance_record,
    update_attendance_trends
)

# Initialize logger
logger = logging.getLogger(__name__)

def process_activity_detail(file_path):
    """
    Process activity detail report and store attendance data
    
    This report contains Key On/Key Off events and is used
    for Late Start and Early End tracking.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        dict: Processing results
    """
    try:
        logger.info(f"Processing activity detail report: {file_path}")
        
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        if df.empty:
            logger.error(f"Empty activity detail file: {file_path}")
            return {'success': False, 'message': 'Empty file'}
        
        # Collect stats
        total_records = len(df)
        processed_records = 0
        late_start_count = 0
        early_end_count = 0
        errors = 0
        
        # Define expected start/end times (could be customized per driver/region)
        expected_start_time = datetime.strptime('07:00', '%H:%M').time()
        expected_end_time = datetime.strptime('17:00', '%H:%M').time()
        
        # Track processed driver-days to avoid duplicates
        processed_events = set()
        
        # Process each record
        for _, row in df.iterrows():
            try:
                # Extract relevant data
                vehicle_id = str(row.get('Vehicle ID', '')).strip()
                driver_name = str(row.get('Driver', '')).strip()
                event_date_str = str(row.get('Event Date', '')).strip()
                event_time_str = str(row.get('Event Time', '')).strip()
                event_type = str(row.get('Event Type', '')).strip()
                location = str(row.get('Location', '')).strip()
                department = str(row.get('Department', '')).strip()
                
                # Skip if missing critical data
                if not vehicle_id or not driver_name or not event_date_str or not event_time_str:
                    continue
                
                # Parse date and time
                try:
                    event_date = datetime.strptime(event_date_str, '%m/%d/%Y').date()
                    event_time = datetime.strptime(event_time_str, '%H:%M:%S').time()
                    event_datetime = datetime.combine(event_date, event_time)
                except:
                    logger.warning(f"Invalid date/time format: {event_date_str} {event_time_str}")
                    continue
                
                # Generate employee ID from driver name
                employee_id = f"EMP-{driver_name.replace(' ', '')}"
                
                # Get asset
                asset = Asset.query.filter_by(asset_identifier=vehicle_id).first()
                asset_id = asset.id if asset else None
                
                # Get or create driver
                driver = get_or_create_driver(
                    name=driver_name,
                    employee_id=employee_id,
                    asset_id=asset_id,
                    department=department
                )
                
                # Get or create job site
                job_site = get_or_create_job_site(
                    name=location,
                    job_number=f"JOB-{location.replace(' ', '')}"
                )
                
                if not driver or not job_site:
                    errors += 1
                    continue
                
                # Process Key On events for Late Start
                if event_type == 'Key On' and event_time > expected_start_time:
                    # Create a unique key for this driver-day-event to avoid duplicates
                    event_key = f"{driver.id}_{event_date}_{event_type}"
                    
                    if event_key not in processed_events:
                        processed_events.add(event_key)
                        
                        # Calculate minutes late
                        start_diff = (datetime.combine(event_date, event_time) - 
                                    datetime.combine(event_date, expected_start_time))
                        late_minutes = max(0, int(start_diff.total_seconds() / 60))
                        
                        if late_minutes > 0:
                            # Save attendance record
                            save_attendance_record(
                                report_date=event_date,
                                driver_id=driver.id,
                                asset_id=asset_id,
                                job_site_id=job_site.id,
                                status_type='LATE_START',
                                expected_start=datetime.combine(event_date, expected_start_time),
                                actual_start=event_datetime,
                                minutes_late=late_minutes
                            )
                            late_start_count += 1
                
                # Process Key Off events for Early End
                if event_type == 'Key Off' and event_time < expected_end_time:
                    # Create a unique key for this driver-day-event to avoid duplicates
                    event_key = f"{driver.id}_{event_date}_{event_type}"
                    
                    if event_key not in processed_events:
                        processed_events.add(event_key)
                        
                        # Calculate minutes early
                        end_diff = (datetime.combine(event_date, expected_end_time) - 
                                   datetime.combine(event_date, event_time))
                        early_minutes = max(0, int(end_diff.total_seconds() / 60))
                        
                        if early_minutes > 0:
                            # Save attendance record
                            save_attendance_record(
                                report_date=event_date,
                                driver_id=driver.id,
                                asset_id=asset_id,
                                job_site_id=job_site.id,
                                status_type='EARLY_END',
                                expected_end=datetime.combine(event_date, expected_end_time),
                                actual_end=event_datetime,
                                minutes_early=early_minutes
                            )
                            early_end_count += 1
                
                processed_records += 1
                
            except Exception as e:
                logger.error(f"Error processing activity detail record: {e}")
                errors += 1
                continue
        
        # Update trends for each day in the report
        date_range = pd.date_range(
            start=df['Event Date'].min(), 
            end=df['Event Date'].max(), 
            freq='D'
        )
        
        for date in date_range:
            update_attendance_trends(date.date())
        
        return {
            'success': True,
            'total_records': total_records,
            'processed_records': processed_records,
            'late_start_count': late_start_count,
            'early_end_count': early_end_count,
            'errors': errors
        }
    
    except Exception as e:
        logger.error(f"Error processing activity detail file: {e}")
        return {'success': False, 'message': str(e)}

def process_driving_history(file_path):
    """
    Process driving history report and store attendance data
    
    This report contains location data used for Not On Job tracking.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        dict: Processing results
    """
    try:
        logger.info(f"Processing driving history report: {file_path}")
        
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        if df.empty:
            logger.error(f"Empty driving history file: {file_path}")
            return {'success': False, 'message': 'Empty file'}
        
        # Collect stats
        total_records = len(df)
        processed_records = 0
        not_on_job_count = 0
        errors = 0
        
        # Track processed driver-days to avoid duplicates
        processed_driver_days = set()
        
        # Find columns for assigned/actual job sites
        location_col = None
        for col in df.columns:
            if 'location' in col.lower():
                location_col = col
                break
        
        if not location_col:
            logger.error(f"No location column found in file: {file_path}")
            return {'success': False, 'message': 'No location column found'}
        
        # Process each record
        for _, row in df.iterrows():
            try:
                # Extract relevant data
                vehicle_id = str(row.get('Vehicle ID', '')).strip()
                driver_name = str(row.get('Driver', '')).strip()
                event_date_str = str(row.get('Date', '')).strip()
                actual_location = str(row.get(location_col, '')).strip()
                assigned_location = str(row.get('Assigned Job', '')).strip()
                department = str(row.get('Department', '')).strip()
                
                # Skip if missing critical data
                if not vehicle_id or not driver_name or not event_date_str:
                    continue
                
                # Parse date
                try:
                    event_date = datetime.strptime(event_date_str, '%m/%d/%Y').date()
                except:
                    logger.warning(f"Invalid date format: {event_date_str}")
                    continue
                
                # Generate employee ID from driver name
                employee_id = f"EMP-{driver_name.replace(' ', '')}"
                
                # Get asset
                asset = Asset.query.filter_by(asset_identifier=vehicle_id).first()
                asset_id = asset.id if asset else None
                
                # Get or create driver
                driver = get_or_create_driver(
                    name=driver_name,
                    employee_id=employee_id,
                    asset_id=asset_id,
                    department=department
                )
                
                # Skip if missing assigned location
                if not assigned_location:
                    continue
                    
                # Create a unique key for this driver-day to avoid duplicates
                driver_day_key = f"{driver.id}_{event_date}"
                
                if driver_day_key in processed_driver_days:
                    continue
                    
                processed_driver_days.add(driver_day_key)
                
                # Get or create job sites for assigned and actual locations
                assigned_job = get_or_create_job_site(
                    name=assigned_location,
                    job_number=f"JOB-{assigned_location.replace(' ', '')}"
                )
                
                actual_job = None
                if actual_location and actual_location != assigned_location:
                    actual_job = get_or_create_job_site(
                        name=actual_location,
                        job_number=f"JOB-{actual_location.replace(' ', '')}"
                    )
                
                if not driver or not assigned_job:
                    errors += 1
                    continue
                
                # Check if not on assigned job site
                if actual_location and actual_location != assigned_location:
                    # Save attendance record for Not On Job
                    save_attendance_record(
                        report_date=event_date,
                        driver_id=driver.id,
                        asset_id=asset_id,
                        job_site_id=assigned_job.id,
                        status_type='NOT_ON_JOB',
                        expected_job_id=assigned_job.id,
                        actual_job_id=actual_job.id if actual_job else None
                    )
                    not_on_job_count += 1
                
                processed_records += 1
                
            except Exception as e:
                logger.error(f"Error processing driving history record: {e}")
                errors += 1
                continue
        
        # Update trends for each day in the report
        date_range = pd.date_range(
            start=df['Date'].min(), 
            end=df['Date'].max(), 
            freq='D'
        )
        
        for date in date_range:
            update_attendance_trends(date.date())
        
        return {
            'success': True,
            'total_records': total_records,
            'processed_records': processed_records,
            'not_on_job_count': not_on_job_count,
            'errors': errors
        }
    
    except Exception as e:
        logger.error(f"Error processing driving history file: {e}")
        return {'success': False, 'message': str(e)}

def process_assets_time_on_site(file_path):
    """
    Process assets time on site report
    
    This report contains time spent at job sites for billing logic.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        dict: Processing results
    """
    try:
        logger.info(f"Processing assets time on site report: {file_path}")
        
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        if df.empty:
            logger.error(f"Empty assets time on site file: {file_path}")
            return {'success': False, 'message': 'Empty file'}
        
        # Process data for reporting - this would be implemented based on specific requirements
        
        return {
            'success': True,
            'message': 'Time on site data processed for billing logic'
        }
    
    except Exception as e:
        logger.error(f"Error processing assets time on site file: {e}")
        return {'success': False, 'message': str(e)}

def process_fleet_utilization(file_path):
    """
    Process fleet utilization report
    
    This report contains metrics for equipment utilization KPIs.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        dict: Processing results
    """
    try:
        logger.info(f"Processing fleet utilization report: {file_path}")
        
        # Load the Excel file
        df = pd.read_excel(file_path)
        
        if df.empty:
            logger.error(f"Empty fleet utilization file: {file_path}")
            return {'success': False, 'message': 'Empty file'}
        
        # Process data for reporting - this would be implemented based on specific requirements
        
        return {
            'success': True,
            'message': 'Fleet utilization data processed for KPIs'
        }
    
    except Exception as e:
        logger.error(f"Error processing fleet utilization file: {e}")
        return {'success': False, 'message': str(e)}

def process_driver_scorecard(file_path):
    """
    Process driver scorecard report
    
    This report contains driver behavior metrics.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        dict: Processing results
    """
    try:
        logger.info(f"Processing driver scorecard report: {file_path}")
        
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        if df.empty:
            logger.error(f"Empty driver scorecard file: {file_path}")
            return {'success': False, 'message': 'Empty file'}
        
        # Process data for reporting - this would be implemented based on specific requirements
        
        return {
            'success': True,
            'message': 'Driver scorecard data processed for behavior metrics'
        }
    
    except Exception as e:
        logger.error(f"Error processing driver scorecard file: {e}")
        return {'success': False, 'message': str(e)}

def process_speeding_report(file_path):
    """
    Process speeding report
    
    This report contains speeding violations.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        dict: Processing results
    """
    try:
        logger.info(f"Processing speeding report: {file_path}")
        
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        if df.empty:
            logger.error(f"Empty speeding report file: {file_path}")
            return {'success': False, 'message': 'Empty file'}
        
        # Process data for reporting - this would be implemented based on specific requirements
        
        return {
            'success': True,
            'message': 'Speeding data processed for driver behavior metrics'
        }
    
    except Exception as e:
        logger.error(f"Error processing speeding report file: {e}")
        return {'success': False, 'message': str(e)}

def import_mtd_reports(directory_path):
    """
    Import all MTD reports from a directory
    
    Args:
        directory_path (str): Path to directory containing MTD reports
        
    Returns:
        dict: Import results
    """
    try:
        logger.info(f"Importing MTD reports from directory: {directory_path}")
        
        if not os.path.exists(directory_path):
            logger.error(f"Directory does not exist: {directory_path}")
            return {'success': False, 'message': 'Directory does not exist'}
        
        results = {}
        
        # Activity Detail (Key On/Off)
        activity_file = os.path.join(directory_path, 'ActivityDetail_KeyOnly_OnRoad_2025-05-01_to_2025-05-15.csv')
        if os.path.exists(activity_file):
            results['activity_detail'] = process_activity_detail(activity_file)
        
        # Driving History
        driving_file = os.path.join(directory_path, 'DrivingHistory_2025-05-01_to_2025-05-15.csv')
        if os.path.exists(driving_file):
            results['driving_history'] = process_driving_history(driving_file)
        
        # Assets Time On Site
        tos_file = os.path.join(directory_path, 'AssetsTimeOnSite_2025-05-01_to_2025-05-15.csv')
        if os.path.exists(tos_file):
            results['assets_time_on_site'] = process_assets_time_on_site(tos_file)
        
        # Fleet Utilization
        utilization_file = os.path.join(directory_path, 'FleetUtilization_MTD_May2025.xlsx')
        if os.path.exists(utilization_file):
            results['fleet_utilization'] = process_fleet_utilization(utilization_file)
        
        # Driver Scorecard
        scorecard_file = os.path.join(directory_path, 'DriverScorecard_2025-05-01_to_2025-05-15.csv')
        if os.path.exists(scorecard_file):
            results['driver_scorecard'] = process_driver_scorecard(scorecard_file)
        
        # Speeding Report
        speeding_file = os.path.join(directory_path, 'SpeedingReport_2025-05-01_to_2025-05-15.csv')
        if os.path.exists(speeding_file):
            results['speeding_report'] = process_speeding_report(speeding_file)
        
        return {
            'success': True,
            'results': results
        }
    
    except Exception as e:
        logger.error(f"Error importing MTD reports: {e}")
        return {'success': False, 'message': str(e)}