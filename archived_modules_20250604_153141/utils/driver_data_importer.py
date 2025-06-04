"""
Driver Data Importer

This module provides utilities for importing driver data from various report formats
including driving history reports and assets time on site reports.
"""
import os
import csv
import re
import logging
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from app import db
from models.driver_attendance import Driver, JobSite, AttendanceRecord

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
LOCATION_PATTERN = re.compile(r'([0-9]{4}-[0-9]{3})')  # Pattern for job site numbers like 2024-004
TIME_FORMATS = [
    '%m/%d/%Y %I:%M:%S %p',
    '%m/%d/%Y %I:%M:%S %p CT',
    '%m/%d/%Y %I:%M %p',
    '%m/%d/%Y %I:%M %p CT'
]


def parse_datetime(date_str):
    """Parse datetime string in various formats"""
    if not date_str or date_str.strip() in ['—', '–', 'Asset On Site', 'Began Day On Site']:
        return None
    
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse datetime: {date_str}")
    return None


def extract_job_number(location_str):
    """Extract job number from location string"""
    if not location_str:
        return None
    
    matches = LOCATION_PATTERN.search(location_str)
    if matches:
        return matches.group(1)
    
    return None


def ensure_driver_exists(employee_id, name=None):
    """Ensure driver exists in database, create if not"""
    driver = Driver.query.filter_by(employee_id=employee_id).first()
    
    if not driver:
        # Extract first and last name
        first_name = name.split()[0] if name else "Unknown"
        last_name = " ".join(name.split()[1:]) if name and len(name.split()) > 1 else "Unknown"
        
        driver = Driver(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        db.session.add(driver)
        db.session.commit()
        logger.info(f"Created new driver: {driver.full_name} ({driver.employee_id})")
    
    return driver


def ensure_job_site_exists(job_number, location=None):
    """Ensure job site exists in database, create if not"""
    job_site = JobSite.query.filter_by(job_number=job_number).first()
    
    if not job_site:
        job_site = JobSite(
            job_number=job_number,
            name=location if location else job_number,
            is_active=True
        )
        db.session.add(job_site)
        db.session.commit()
        logger.info(f"Created new job site: {job_site.job_number}")
    
    return job_site


def import_driving_history(file_path):
    """Import driving history data from CSV file"""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # Skip header rows
        start_row = None
        for i, row in df.iterrows():
            if 'Textbox53' in str(row) and 'Textbox61' in str(row) and 'Distance' in str(row):
                start_row = i + 1
                break
        
        if start_row is None:
            logger.error(f"Could not find data start row in {file_path}")
            return False
        
        data = df.iloc[start_row:].reset_index(drop=True)
        
        # Rename columns
        columns = ['asset', 'distance', 'days', 'driver', 'phone', 'event_time', 'event_type', 'latitude', 'longitude', 'location']
        if len(data.columns) > len(columns):
            data = data.iloc[:, :len(columns)]
        data.columns = columns
        
        # Process records
        current_asset = None
        current_driver = None
        current_driver_name = None
        current_phone = None
        records_processed = 0
        records_skipped = 0
        
        for _, row in data.iterrows():
            # Skip empty rows
            if pd.isna(row['event_time']) or pd.isna(row['location']):
                records_skipped += 1
                continue
            
            # Store driver/asset info when encountered
            if pd.notna(row['asset']) and str(row['asset']).strip():
                current_asset = str(row['asset']).strip()
                if " - " in current_asset:
                    asset_parts = current_asset.split(" - ", 1)
                    employee_id = asset_parts[0].strip().replace('#', '')
                    current_driver_name = asset_parts[1].split(" ", 1)[0] + " " + asset_parts[1].split(" ", 2)[1] if len(asset_parts[1].split(" ")) > 2 else asset_parts[1]
                    current_driver = employee_id
            
            if pd.notna(row['driver']) and str(row['driver']).strip():
                current_driver_name = str(row['driver']).strip()
                if "(" in current_driver_name and ")" in current_driver_name:
                    employee_id = current_driver_name.split("(")[1].split(")")[0].strip()
                    current_driver = employee_id
            
            if pd.notna(row['phone']) and str(row['phone']).strip():
                current_phone = str(row['phone']).strip()
            
            # Skip if no driver or event time
            if not current_driver or not row['event_time']:
                records_skipped += 1
                continue
            
            # Parse event time and location
            event_time = parse_datetime(str(row['event_time']))
            location = str(row['location']).strip()
            event_type = str(row['event_type']).strip() if pd.notna(row['event_type']) else None
            
            if not event_time:
                records_skipped += 1
                continue
            
            # Extract job number from location
            job_number = extract_job_number(location)
            
            # If no job number, use a default
            if not job_number:
                job_number = "UNKNOWN"
            
            # Create driver and job site if they don't exist
            driver = ensure_driver_exists(current_driver, current_driver_name)
            job_site = ensure_job_site_exists(job_number, location)
            
            # Determine if this is a start or end event
            is_start = event_type in ['Key On', 'Arrived']
            is_end = event_type in ['Key Off', 'Departed']
            
            # Find existing record for this driver and date
            record_date = event_time.replace(hour=0, minute=0, second=0, microsecond=0)
            existing_record = AttendanceRecord.query.filter_by(
                driver_id=driver.id,
                date=record_date
            ).first()
            
            # Create or update attendance record
            if not existing_record:
                existing_record = AttendanceRecord(
                    driver_id=driver.id,
                    date=record_date,
                    asset_id=current_asset.split(" - ")[0].strip() if " - " in current_asset else current_asset,
                    assigned_job_id=job_site.id,
                    actual_job_id=job_site.id
                )
                db.session.add(existing_record)
            
            # Update start/end times
            if is_start:
                if not existing_record.actual_start_time or event_time < existing_record.actual_start_time:
                    existing_record.actual_start_time = event_time
                    existing_record.expected_start_time = event_time.replace(hour=7, minute=0, second=0)
                    existing_record.late_start = event_time > existing_record.expected_start_time
            elif is_end:
                if not existing_record.actual_end_time or event_time > existing_record.actual_end_time:
                    existing_record.actual_end_time = event_time
                    existing_record.expected_end_time = event_time.replace(hour=16, minute=30, second=0)
                    existing_record.early_end = event_time < existing_record.expected_end_time
            
            records_processed += 1
            
            # Commit every 100 records to avoid memory issues
            if records_processed % 100 == 0:
                db.session.commit()
                logger.info(f"Processed {records_processed} records")
        
        # Final commit
        db.session.commit()
        logger.info(f"Processed {records_processed} records, skipped {records_skipped} records")
        
        return True
        
    except Exception as e:
        logger.error(f"Error importing driving history: {str(e)}")
        db.session.rollback()
        return False


def import_assets_time_on_site(file_path):
    """Import assets time on site data from CSV file"""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # Skip header rows
        start_row = None
        for i, row in df.iterrows():
            if 'Location' in str(row) and 'Asset' in str(row) and 'Date' in str(row):
                start_row = i + 1
                break
        
        if start_row is None:
            logger.error(f"Could not find data start row in {file_path}")
            return False
        
        data = df.iloc[start_row:].reset_index(drop=True)
        
        # Rename columns
        columns = ['location', 'asset', 'date', 'day', 'start_time', 'end_time', 'time_on_site', 'company', 'total_time']
        if len(data.columns) > len(columns):
            data = data.iloc[:, :len(columns)]
        data.columns = columns
        
        # Process records
        records_processed = 0
        records_skipped = 0
        
        for _, row in data.iterrows():
            # Skip empty rows
            if pd.isna(row['location']) or pd.isna(row['asset']) or pd.isna(row['date']):
                records_skipped += 1
                continue
            
            # Parse location, asset, date
            location = str(row['location']).strip()
            asset = str(row['asset']).strip()
            date_str = str(row['date']).strip()
            
            # Parse driver/asset info
            if "#" in asset and " - " in asset:
                asset_parts = asset.split(" - ", 1)
                employee_id = asset_parts[0].replace('#', '').strip()
                driver_name = asset_parts[1].split(" ", 2)
                driver_name = driver_name[0] + " " + driver_name[1] if len(driver_name) > 1 else asset_parts[1]
            else:
                employee_id = "UNKNOWN"
                driver_name = "Unknown Driver"
            
            # Extract job number from location
            job_number = extract_job_number(location)
            if not job_number:
                job_number = "UNKNOWN"
            
            # Parse time
            try:
                record_date = datetime.strptime(date_str, '%m/%d/%Y')
            except ValueError:
                records_skipped += 1
                continue
            
            # Parse start/end times
            start_time_str = str(row['start_time']).strip() if pd.notna(row['start_time']) else None
            end_time_str = str(row['end_time']).strip() if pd.notna(row['end_time']) else None
            
            start_time = None
            end_time = None
            
            if start_time_str and start_time_str != '—' and start_time_str != 'Began Day On Site':
                try:
                    if 'CT' in start_time_str:
                        start_time_str = start_time_str.replace(' CT', '')
                    time_parts = start_time_str.split(' ')
                    hour, minute = time_parts[0].split(':')
                    am_pm = time_parts[1]
                    
                    hour = int(hour)
                    minute = int(minute)
                    
                    if am_pm.upper() == 'PM' and hour < 12:
                        hour += 12
                    elif am_pm.upper() == 'AM' and hour == 12:
                        hour = 0
                    
                    start_time = record_date.replace(hour=hour, minute=minute, second=0)
                except:
                    pass
            
            if end_time_str and end_time_str != '—' and end_time_str != 'Asset On Site':
                try:
                    if 'CT' in end_time_str:
                        end_time_str = end_time_str.replace(' CT', '')
                    time_parts = end_time_str.split(' ')
                    hour, minute = time_parts[0].split(':')
                    am_pm = time_parts[1]
                    
                    hour = int(hour)
                    minute = int(minute)
                    
                    if am_pm.upper() == 'PM' and hour < 12:
                        hour += 12
                    elif am_pm.upper() == 'AM' and hour == 12:
                        hour = 0
                    
                    end_time = record_date.replace(hour=hour, minute=minute, second=0)
                except:
                    pass
            
            # Create driver and job site if they don't exist
            driver = ensure_driver_exists(employee_id, driver_name)
            job_site = ensure_job_site_exists(job_number, location)
            
            # Find existing record for this driver and date
            existing_record = AttendanceRecord.query.filter_by(
                driver_id=driver.id,
                date=record_date
            ).first()
            
            # Create or update attendance record
            if not existing_record:
                existing_record = AttendanceRecord(
                    driver_id=driver.id,
                    date=record_date,
                    asset_id=asset.split(" - ")[0].strip() if " - " in asset else asset,
                    assigned_job_id=job_site.id,
                    actual_job_id=job_site.id
                )
                db.session.add(existing_record)
            
            # Update times if not already set
            if start_time:
                if not existing_record.actual_start_time or start_time < existing_record.actual_start_time:
                    existing_record.actual_start_time = start_time
                    existing_record.expected_start_time = start_time.replace(hour=7, minute=0, second=0)
                    existing_record.late_start = start_time > existing_record.expected_start_time
            
            if end_time:
                if not existing_record.actual_end_time or end_time > existing_record.actual_end_time:
                    existing_record.actual_end_time = end_time
                    existing_record.expected_end_time = end_time.replace(hour=16, minute=30, second=0)
                    existing_record.early_end = end_time < existing_record.expected_end_time
            
            records_processed += 1
            
            # Commit every 100 records to avoid memory issues
            if records_processed % 100 == 0:
                db.session.commit()
                logger.info(f"Processed {records_processed} records")
        
        # Final commit
        db.session.commit()
        logger.info(f"Processed {records_processed} records, skipped {records_skipped} records")
        
        return True
        
    except Exception as e:
        logger.error(f"Error importing assets time on site: {str(e)}")
        db.session.rollback()
        return False


def import_all_driver_data():
    """Import all driver data from available sources"""
    # Import driving history
    driving_history_path = os.path.join('attached_assets', 'DrivingHistory.csv')
    if os.path.exists(driving_history_path):
        logger.info(f"Importing driving history from {driving_history_path}")
        import_driving_history(driving_history_path)
    
    # Import assets time on site
    time_on_site_path = os.path.join('attached_assets', 'AssetsTimeOnSite (3).csv')
    if os.path.exists(time_on_site_path):
        logger.info(f"Importing assets time on site from {time_on_site_path}")
        import_assets_time_on_site(time_on_site_path)
    
    # Calculate not_on_job flag for all records
    logger.info("Calculating not_on_job flag for all records")
    try:
        records = AttendanceRecord.query.all()
        for record in records:
            # If actual_job_id is different from assigned_job_id, set not_on_job flag
            if record.actual_job_id and record.assigned_job_id and record.actual_job_id != record.assigned_job_id:
                record.not_on_job = True
        
        db.session.commit()
        logger.info("Completed not_on_job calculations")
    except Exception as e:
        logger.error(f"Error calculating not_on_job flags: {str(e)}")
        db.session.rollback()
    
    return True


if __name__ == '__main__':
    import_all_driver_data()