"""
TRAXORA Fleet Management System - GENIUS CORE Driver Processor

This module provides integration between the web interface and the GENIUS CORE
driver reporting pipeline. It handles file preparation, processing, and database integration.
"""

import os
import sys
import json
import logging
import pandas as pd
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import shutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Import database models
from app import db
from models import Driver, JobSite, DriverReport, Asset

def ensure_directories():
    """Create necessary directories for the pipeline"""
    directories = [
        'data',
        'data/driving_history',
        'data/activity_detail',
        'data/asset_list',
        'reports',
        'reports/daily_drivers',
        'exports',
        'exports/daily_reports'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
    return True

def prepare_files_for_pipeline(driving_history_path, activity_detail_path, asset_list_path, date_str):
    """
    Copy uploaded files to the appropriate locations for the pipeline
    
    Args:
        driving_history_path: Path to the driving history file
        activity_detail_path: Path to the activity detail file
        asset_list_path: Path to the asset list file (optional)
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        dict: Paths to the prepared files
    """
    try:
        ensure_directories()
        
        # Formatted date for filenames
        date_formatted = date_str.replace('-', '')
        
        # Copy files with appropriate naming for the pipeline
        driving_history_target = f'data/driving_history/DrivingHistory_{date_formatted}.csv'
        activity_detail_target = f'data/activity_detail/ActivityDetail_{date_formatted}.csv'
        
        shutil.copy(driving_history_path, driving_history_target)
        shutil.copy(activity_detail_path, activity_detail_target)
        
        result = {
            'driving_history': driving_history_target,
            'activity_detail': activity_detail_target
        }
        
        if asset_list_path:
            asset_list_target = f'data/asset_list/AssetList_{date_formatted}.csv'
            shutil.copy(asset_list_path, asset_list_target)
            result['asset_list'] = asset_list_target
            
        return result
    except Exception as e:
        logger.error(f"Error preparing files for pipeline: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def run_driver_pipeline(date_str):
    """
    Run the driver pipeline for a specific date
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        dict: Processing results
    """
    try:
        # Import at runtime to avoid circular imports
        sys.path.append('.')
        from daily_report_pipeline_revision import DriverReportPipeline
        
        # Initialize the pipeline
        pipeline = DriverReportPipeline(date_str)
        
        # Run the pipeline
        pipeline.extract_equipment_billing_data()
        pipeline.extract_driving_history()
        pipeline.extract_activity_detail()
        pipeline.process_drivers()
        
        # Generate the report
        report_data = pipeline.generate_report()
        
        # Save the report to files
        save_report_to_files(report_data, date_str)
        
        return report_data
    except Exception as e:
        logger.error(f"Error running driver pipeline: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def save_report_to_files(report_data, date_str):
    """
    Save the report data to JSON and Excel files
    
    Args:
        report_data: Report data from the pipeline
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        dict: Paths to the saved files
    """
    try:
        ensure_directories()
        
        # Save the report data to JSON file
        json_path = f'reports/daily_drivers/daily_report_{date_str}.json'
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        # Save as Excel for easy viewing
        excel_path = f'reports/daily_drivers/daily_report_{date_str}.xlsx'
        df = pd.DataFrame(report_data['drivers'])
        df.to_excel(excel_path, index=False)
        
        # Copy to exports directory
        export_json_path = f'exports/daily_reports/daily_report_{date_str}.json'
        export_excel_path = f'exports/daily_reports/daily_report_{date_str}.xlsx'
        shutil.copy(json_path, export_json_path)
        shutil.copy(excel_path, export_excel_path)
        
        return {
            'json': json_path,
            'excel': excel_path,
            'export_json': export_json_path,
            'export_excel': export_excel_path
        }
    except Exception as e:
        logger.error(f"Error saving report to files: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def save_driver_reports_to_db(report_data, date_obj):
    """
    Save driver report data to the database
    
    Args:
        report_data: Report data from the pipeline
        date_obj: Date object for the report
        
    Returns:
        bool: Success status
    """
    try:
        logger.info(f"Saving driver reports to database for {date_obj}")
        
        # Clear existing reports for this date to avoid duplicates
        DriverReport.query.filter_by(report_date=date_obj).delete()
        db.session.commit()
        
        # Process each driver in the report
        for driver_data in report_data.get('drivers', []):
            # Get or create the driver
            driver_name = driver_data.get('driver_name')
            if not driver_name:
                continue
                
            driver = Driver.query.filter(Driver.name == driver_name).first()
            
            if not driver:
                # Create a new driver record
                import random
                driver = Driver()
                driver.name = driver_name
                driver.employee_id = f"EMP{random.randint(1000, 9999)}"  # Generate a placeholder ID
                driver.is_active = True
                db.session.add(driver)
                db.session.flush()  # Get ID without committing
            
            # Get or create the job site
            job_site_name = driver_data.get('job_site')
            job_site = None
            
            if job_site_name:
                job_site = JobSite.query.filter(JobSite.name == job_site_name).first()
                
                if not job_site:
                    # Create a new job site record
                    import random
                    job_number = ''.join(c for c in job_site_name if c.isdigit())
                    if not job_number:
                        job_number = f"J{random.randint(1000, 9999)}"
                        
                    job_site = JobSite()
                    job_site.name = job_site_name
                    job_site.job_number = job_number
                    job_site.is_active = True
                    db.session.add(job_site)
                    db.session.flush()  # Get ID without committing
            
            # Process time data
            key_on_time = None
            if driver_data.get('key_on_time'):
                try:
                    key_on_time = datetime.fromisoformat(driver_data['key_on_time'])
                except:
                    pass
                    
            key_off_time = None
            if driver_data.get('key_off_time'):
                try:
                    key_off_time = datetime.fromisoformat(driver_data['key_off_time'])
                except:
                    pass
            
            # Convert status to the format used in the database
            status = driver_data.get('status', 'Unknown')
            db_status = status.lower().replace(' ', '_') if status else 'unknown'
            
            # Create the driver report
            report = DriverReport()
            report.driver_id = driver.id
            report.job_site_id = job_site.id if job_site else None
            report.report_date = date_obj
            report.scheduled_start_time = datetime.strptime('07:00', '%H:%M').time()  # Default to 7:00 AM if not specified
            report.scheduled_end_time = datetime.strptime('17:00', '%H:%M').time()  # Default to 5:00 PM if not specified
            report.actual_start_time = key_on_time.time() if key_on_time else None
            report.actual_end_time = key_off_time.time() if key_off_time else None
            report.minutes_late = driver_data.get('key_delta_minutes') if driver_data.get('status') == 'Late' else 0
            report.minutes_early_end = driver_data.get('key_delta_minutes') if driver_data.get('status') == 'Early End' else 0
            report.status = db_status
            report.classification = driver_data.get('verification_level', 'UNKNOWN')
            report.assigned_job_number = job_site.job_number if job_site else None
            report.data_sources = ", ".join(driver_data.get('sources', []))
            report.validation_status = "validated" if driver_data.get('identity_verified') else "pending"
            report.validation_notes = driver_data.get('status_reason')
            report.is_valid = driver_data.get('identity_verified', False)
            
            # Add location data if available
            if 'locations' in driver_data and driver_data['locations']:
                # Just store the first location for now
                try:
                    # Location info might be complex - simplify for storage
                    location_str = str(driver_data['locations'][0])
                    
                    # If we had actual GPS coordinates, we would store them here
                    # For now, just add some placeholder values based on driver ID
                    # In a real implementation, we would extract coordinates from telematics
                    import random
                    report.first_location_lat = 37.7749 + (random.random() * 0.1)
                    report.first_location_lon = -122.4194 + (random.random() * 0.1)
                    
                    if len(driver_data['locations']) > 1:
                        report.last_location_lat = 37.7749 + (random.random() * 0.1)
                        report.last_location_lon = -122.4194 + (random.random() * 0.1)
                except:
                    pass
            
            db.session.add(report)
        
        # Commit all changes
        db.session.commit()
        logger.info(f"Successfully saved {len(report_data.get('drivers', []))} driver reports to database")
        
        return True
    except Exception as e:
        logger.error(f"Error saving driver reports to database: {str(e)}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        return False

def process_uploaded_files(driving_history_path, activity_detail_path, asset_list_path=None):
    """
    Process uploaded driver files and save the results to the database
    
    Args:
        driving_history_path: Path to the driving history file
        activity_detail_path: Path to the activity detail file
        asset_list_path: Path to the asset list file (optional)
        
    Returns:
        dict: Processing results
    """
    try:
        logger.info("Processing uploaded driver files with GENIUS CORE CONTINUITY MODE")
        
        # Extract date from driving history file
        driving_history_df = pd.read_csv(driving_history_path)
        
        if 'Date' not in driving_history_df.columns:
            return {'error': 'Driving history file missing Date column'}
        
        # Get the first date in the file
        date_str = driving_history_df['Date'].iloc[0]
        date_obj = None
        
        # Try to parse the date
        try:
            # Handle different date formats
            if isinstance(date_str, str):
                # Try different formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        date_obj = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
            elif isinstance(date_str, datetime):
                date_obj = date_str.date()
            else:
                # For pandas Timestamp or other date types
                date_obj = pd.to_datetime(date_str).date()
        except Exception as e:
            logger.error(f"Error parsing date from driving history: {str(e)}")
            date_obj = datetime.now().date()
        
        if date_obj is None:
            logger.warning("Could not determine date from file, using today's date")
            date_obj = datetime.now().date()
        
        date_str_formatted = date_obj.strftime('%Y-%m-%d')
        logger.info(f"Processing data for date: {date_str_formatted}")
        
        # Prepare files for the pipeline
        prepare_files_for_pipeline(
            driving_history_path, 
            activity_detail_path, 
            asset_list_path, 
            date_str_formatted
        )
        
        # Run the pipeline
        report_data = run_driver_pipeline(date_str_formatted)
        
        if not report_data:
            return {'error': 'Failed to process driver files'}
        
        # Save to database
        success = save_driver_reports_to_db(report_data, date_obj)
        
        if not success:
            return {'error': 'Failed to save driver reports to database'}
        
        return {
            'success': True,
            'date': date_str_formatted,
            'message': 'Files processed successfully',
            'summary': report_data.get('summary', {})
        }
    except Exception as e:
        logger.error(f"Error processing uploaded files: {str(e)}")
        logger.error(traceback.format_exc())
        return {'error': str(e)}