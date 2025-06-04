"""
Attendance Import Utilities

This module provides functions for importing attendance data from various file formats
and processing it into the database.
"""
import os
import pandas as pd
import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from app import db
from models.driver_attendance import DriverAttendance, JobSiteAttendance, AttendanceRecord

# Set up logging
logger = logging.getLogger(__name__)

def process_excel_attendance(file_path):
    """
    Process attendance data from an Excel file
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        int: Number of records processed
    """
    try:
        logger.info(f"Processing Excel attendance file: {file_path}")
        
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Check which type of attendance file this is
        if 'Employee ID' in df.columns and 'Start Time' in df.columns:
            return process_activity_detail(df)
        elif 'Vehicle ID' in df.columns and 'Date' in df.columns:
            return process_driving_history(df)
        elif 'Asset ID' in df.columns and 'Site Name' in df.columns:
            return process_time_on_site(df)
        else:
            logger.warning(f"Unknown Excel format in file: {file_path}")
            raise ValueError("Unknown Excel format. File must contain expected columns for Activity Detail, Driving History, or Time on Site data.")
    
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise
        
def process_csv_attendance(file_path):
    """
    Process attendance data from a CSV file
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        int: Number of records processed
    """
    try:
        logger.info(f"Processing CSV attendance file: {file_path}")
        
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Check which type of attendance file this is
        if 'Employee ID' in df.columns and 'Start Time' in df.columns:
            return process_activity_detail(df)
        elif 'Vehicle ID' in df.columns and 'Date' in df.columns:
            return process_driving_history(df)
        elif 'Asset ID' in df.columns and 'Site Name' in df.columns:
            return process_time_on_site(df)
        else:
            logger.warning(f"Unknown CSV format in file: {file_path}")
            raise ValueError("Unknown CSV format. File must contain expected columns for Activity Detail, Driving History, or Time on Site data.")
    
    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}")
        raise

def process_activity_detail(df):
    """
    Process Activity Detail data
    
    Args:
        df (DataFrame): Pandas DataFrame containing activity detail data
        
    Returns:
        int: Number of records processed
    """
    records_processed = 0
    
    try:
        # Standardize column names
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        
        # Required columns
        required_cols = ['employee_id', 'date', 'start_time', 'end_time', 'job_number', 'asset_id']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns in Activity Detail data: {', '.join(missing_cols)}")
            
        # Process each row
        for _, row in df.iterrows():
            try:
                # Get or create driver
                employee_id = str(row['employee_id']).strip()
                driver = DriverAttendance.query.filter_by(employee_id=employee_id).first()
                
                if not driver:
                    # Create new driver record if doesn't exist
                    driver = DriverAttendance(
                        employee_id=employee_id,
                        first_name=row.get('first_name', 'Unknown'),
                        last_name=row.get('last_name', 'Unknown'),
                        division=row.get('division', 'Unknown')
                    )
                    db.session.add(driver)
                    db.session.flush()  # Get ID without committing
                
                # Get or create job site
                job_number = str(row['job_number']).strip()
                job_site = JobSiteAttendance.query.filter_by(job_number=job_number).first()
                
                if not job_site:
                    # Create new job site if doesn't exist
                    job_site = JobSiteAttendance(
                        job_number=job_number,
                        name=row.get('job_name', f'Job {job_number}'),
                        location=row.get('location', 'Unknown')
                    )
                    db.session.add(job_site)
                    db.session.flush()  # Get ID without committing
                
                # Parse date
                if isinstance(row['date'], str):
                    date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                else:
                    date = row['date'].date() if hasattr(row['date'], 'date') else row['date']
                
                # Parse times
                if isinstance(row['start_time'], str):
                    start_time = datetime.strptime(f"{date} {row['start_time']}", '%Y-%m-%d %H:%M:%S')
                else:
                    start_time = row['start_time']
                    
                if isinstance(row['end_time'], str):
                    end_time = datetime.strptime(f"{date} {row['end_time']}", '%Y-%m-%d %H:%M:%S')
                else:
                    end_time = row['end_time']
                
                # Expected start/end times (typical work day)
                expected_start = datetime.combine(date, datetime.strptime('07:00:00', '%H:%M:%S').time())
                expected_end = datetime.combine(date, datetime.strptime('17:00:00', '%H:%M:%S').time())
                
                # Determine late start/early end flags
                late_start = start_time > (expected_start + timedelta(minutes=5))
                early_end = end_time < (expected_end - timedelta(minutes=5))
                not_on_job = False  # Default to False, will be set by driving history
                
                # Create or update attendance record
                attendance = AttendanceRecord.query.filter_by(
                    driver_id=driver.id,
                    date=date
                ).first()
                
                if attendance:
                    # Update existing record
                    attendance.assigned_job_id = job_site.id
                    attendance.actual_job_id = job_site.id
                    attendance.expected_start_time = expected_start
                    attendance.actual_start_time = start_time
                    attendance.expected_end_time = expected_end
                    attendance.actual_end_time = end_time
                    attendance.late_start = late_start
                    attendance.early_end = early_end
                    attendance.asset_id = str(row['asset_id']).strip()
                else:
                    # Create new record
                    attendance = AttendanceRecord(
                        driver_id=driver.id,
                        date=date,
                        assigned_job_id=job_site.id,
                        actual_job_id=job_site.id,
                        expected_start_time=expected_start,
                        actual_start_time=start_time,
                        expected_end_time=expected_end,
                        actual_end_time=end_time,
                        late_start=late_start,
                        early_end=early_end,
                        not_on_job=not_on_job,
                        asset_id=str(row['asset_id']).strip()
                    )
                    db.session.add(attendance)
                
                records_processed += 1
                
                # Commit in batches to avoid large transactions
                if records_processed % 50 == 0:
                    db.session.commit()
                    
            except Exception as e:
                logger.error(f"Error processing Activity Detail row: {str(e)}")
                db.session.rollback()
                
        # Final commit
        db.session.commit()
        logger.info(f"Processed {records_processed} activity detail records")
        
        return records_processed
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in process_activity_detail: {str(e)}")
        raise

def process_driving_history(df):
    """
    Process Driving History data
    
    Args:
        df (DataFrame): Pandas DataFrame containing driving history data
        
    Returns:
        int: Number of records processed
    """
    records_updated = 0
    
    try:
        # Standardize column names
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        
        # Required columns
        required_cols = ['driver_id', 'date', 'vehicle_id', 'job_site']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns in Driving History data: {', '.join(missing_cols)}")
            
        # Process each row
        for _, row in df.iterrows():
            try:
                # Get driver
                employee_id = str(row['driver_id']).strip()
                driver = DriverAttendance.query.filter_by(employee_id=employee_id).first()
                
                if not driver:
                    logger.warning(f"Driver with ID {employee_id} not found, skipping driving history record")
                    continue
                
                # Parse date
                if isinstance(row['date'], str):
                    date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                else:
                    date = row['date'].date() if hasattr(row['date'], 'date') else row['date']
                
                # Determine not on job flag
                not_on_job = row.get('status', '').lower() == 'not_on_job'
                
                # Find and update existing attendance record
                attendance = AttendanceRecord.query.filter_by(
                    driver_id=driver.id,
                    date=date
                ).first()
                
                if attendance:
                    # Update not_on_job flag
                    attendance.not_on_job = not_on_job
                    
                    # Update asset ID if not already set
                    if not attendance.asset_id or attendance.asset_id == 'N/A':
                        attendance.asset_id = str(row['vehicle_id']).strip()
                        
                    # Update notes if available
                    if 'notes' in row and pd.notna(row['notes']):
                        attendance.notes = row['notes']
                        
                    records_updated += 1
                else:
                    logger.warning(f"No attendance record found for driver {employee_id} on {date}")
                
                # Commit in batches to avoid large transactions
                if records_updated % 50 == 0:
                    db.session.commit()
                    
            except Exception as e:
                logger.error(f"Error processing Driving History row: {str(e)}")
                db.session.rollback()
                
        # Final commit
        db.session.commit()
        logger.info(f"Updated {records_updated} records with driving history data")
        
        return records_updated
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in process_driving_history: {str(e)}")
        raise

def process_time_on_site(df):
    """
    Process Time on Site data
    
    Args:
        df (DataFrame): Pandas DataFrame containing time on site data
        
    Returns:
        int: Number of records processed
    """
    records_updated = 0
    
    try:
        # Standardize column names
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        
        # Required columns
        required_cols = ['asset_id', 'site_name', 'date', 'time_on_site']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns in Time on Site data: {', '.join(missing_cols)}")
            
        # Process each row to update efficiency metrics
        for _, row in df.iterrows():
            try:
                # Get the asset ID
                asset_id = str(row['asset_id']).strip()
                
                # Parse date
                if isinstance(row['date'], str):
                    date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                else:
                    date = row['date'].date() if hasattr(row['date'], 'date') else row['date']
                
                # Find all attendance records for this asset on this date
                attendance_records = AttendanceRecord.query.filter_by(
                    asset_id=asset_id,
                    date=date
                ).all()
                
                for attendance in attendance_records:
                    # Calculate time on site efficiency (if the column exists)
                    if 'time_on_site' in row and pd.notna(row['time_on_site']):
                        time_on_site_minutes = float(row['time_on_site'])
                        
                        # Calculate work day duration in minutes
                        if attendance.actual_start_time and attendance.actual_end_time:
                            work_duration = (attendance.actual_end_time - attendance.actual_start_time).total_seconds() / 60
                            
                            # Only update if we have valid data
                            if work_duration > 0:
                                # Update notes with efficiency data
                                efficiency_pct = round((time_on_site_minutes / work_duration) * 100, 1)
                                notes = attendance.notes or ""
                                notes += f" Time on site: {time_on_site_minutes} min ({efficiency_pct}% efficiency)."
                                attendance.notes = notes.strip()
                                
                                records_updated += 1
                
                # Commit in batches to avoid large transactions
                if records_updated % 50 == 0:
                    db.session.commit()
                    
            except Exception as e:
                logger.error(f"Error processing Time on Site row: {str(e)}")
                db.session.rollback()
                
        # Final commit
        db.session.commit()
        logger.info(f"Updated {records_updated} records with time on site data")
        
        return records_updated
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in process_time_on_site: {str(e)}")
        raise