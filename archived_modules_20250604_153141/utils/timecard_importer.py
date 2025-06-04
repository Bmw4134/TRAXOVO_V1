"""
Timecard Importer

This module provides utilities for importing and processing timecard data
from Excel reports.
"""
import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from app import db
from models.driver_attendance import Driver, JobSite, AttendanceRecord

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_timecards(file_path):
    """
    Import timecard data from Excel file
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        bool: True if import was successful, False otherwise
    """
    try:
        logger.info(f"Importing timecard data from {file_path}")
        
        # Extract date range from filename
        import re
        date_range = re.search(r'(\d{4}-\d{2}-\d{2})\s*-\s*(\d{4}-\d{2}-\d{2})', os.path.basename(file_path))
        start_date_str = None
        end_date_str = None
        
        if date_range:
            start_date_str = date_range.group(1)
            end_date_str = date_range.group(2)
            logger.info(f"Detected date range: {start_date_str} to {end_date_str}")
        
        # Read Excel file
        xl = pd.ExcelFile(file_path)
        logger.info(f"Excel sheets: {xl.sheet_names}")
        
        # Process each sheet
        records_processed = 0
        records_skipped = 0
        
        for sheet_name in xl.sheet_names:
            logger.info(f"Processing sheet: {sheet_name}")
            
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Log the columns
            logger.info(f"Sheet columns: {df.columns.tolist()}")
            
            # Try to identify important columns
            employee_col = None
            for col in df.columns:
                if 'employee' in str(col).lower() or 'name' in str(col).lower() or 'worker' in str(col).lower():
                    employee_col = col
                    break
            
            date_col = None
            for col in df.columns:
                if 'date' in str(col).lower() or 'day' in str(col).lower():
                    date_col = col
                    break
            
            job_col = None
            for col in df.columns:
                if 'job' in str(col).lower() or 'project' in str(col).lower() or 'site' in str(col).lower():
                    job_col = col
                    break
            
            hours_col = None
            for col in df.columns:
                if 'hours' in str(col).lower() or 'time' in str(col).lower() or 'duration' in str(col).lower():
                    hours_col = col
                    break
            
            start_time_col = None
            for col in df.columns:
                if 'start' in str(col).lower() or 'in' in str(col).lower() or 'clock in' in str(col).lower():
                    start_time_col = col
                    break
            
            end_time_col = None
            for col in df.columns:
                if 'end' in str(col).lower() or 'out' in str(col).lower() or 'clock out' in str(col).lower():
                    end_time_col = col
                    break
            
            # Log identified columns
            logger.info(f"Identified columns - Employee: {employee_col}, Date: {date_col}, Job: {job_col}, " +
                     f"Hours: {hours_col}, Start Time: {start_time_col}, End Time: {end_time_col}")
            
            # Skip sheet if we can't identify key columns
            if not employee_col or not date_col:
                logger.warning(f"Missing key columns in sheet {sheet_name}, skipping")
                continue
            
            # Process rows
            for idx, row in df.iterrows():
                # Skip rows with missing essential data
                if pd.isna(row[employee_col]) or pd.isna(row[date_col]):
                    records_skipped += 1
                    continue
                
                # Extract employee info
                employee_name = str(row[employee_col]).strip()
                employee_id = None
                
                # Try to extract employee ID if it's in the format "Name (ID)"
                if "(" in employee_name and ")" in employee_name:
                    parts = employee_name.split("(")
                    if len(parts) > 1:
                        possible_id = parts[1].split(")")[0].strip()
                        if possible_id.isalnum():
                            employee_id = possible_id
                
                # If no ID was found but we have a name, use a placeholder ID
                if not employee_id and employee_name:
                    # Generate a consistent ID based on the name
                    employee_id = f"TC-{employee_name.replace(' ', '')[:8]}"
                
                # Extract job info
                job_number = None
                if job_col and pd.notna(row[job_col]):
                    job_site = str(row[job_col]).strip()
                    # Try to extract job number in format YYYY-NNN
                    import re
                    job_match = re.search(r'(\d{4}-\d{3})', job_site)
                    if job_match:
                        job_number = job_match.group(1)
                    else:
                        # Use the job site name as the "number"
                        job_number = job_site
                else:
                    # Default job site if not specified
                    job_number = "UNKNOWN"
                
                # Extract date
                record_date = None
                if isinstance(row[date_col], datetime):
                    record_date = row[date_col]
                elif isinstance(row[date_col], str):
                    # Try common date formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y']:
                        try:
                            record_date = datetime.strptime(row[date_col], fmt)
                            break
                        except ValueError:
                            continue
                
                # If still no date but we have date range from filename, use start date
                if not record_date and start_date_str:
                    try:
                        record_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    except ValueError:
                        pass
                
                # If still no date, skip this row
                if not record_date:
                    records_skipped += 1
                    continue
                
                # Extract start/end times
                start_time = None
                end_time = None
                
                # Try to get start time
                if start_time_col and pd.notna(row[start_time_col]):
                    if isinstance(row[start_time_col], datetime):
                        start_time = row[start_time_col]
                    elif isinstance(row[start_time_col], str):
                        # Try to parse time string (format might be HH:MM or HH:MM AM/PM)
                        try:
                            # Check if it's a time-only string
                            if ":" in row[start_time_col]:
                                if "AM" in row[start_time_col].upper() or "PM" in row[start_time_col].upper():
                                    time_obj = datetime.strptime(row[start_time_col].strip(), '%I:%M %p')
                                else:
                                    time_obj = datetime.strptime(row[start_time_col].strip(), '%H:%M')
                                
                                # Combine date and time
                                start_time = record_date.replace(
                                    hour=time_obj.hour,
                                    minute=time_obj.minute,
                                    second=0
                                )
                        except ValueError:
                            pass
                
                # Try to get end time
                if end_time_col and pd.notna(row[end_time_col]):
                    if isinstance(row[end_time_col], datetime):
                        end_time = row[end_time_col]
                    elif isinstance(row[end_time_col], str):
                        # Try to parse time string
                        try:
                            if ":" in row[end_time_col]:
                                if "AM" in row[end_time_col].upper() or "PM" in row[end_time_col].upper():
                                    time_obj = datetime.strptime(row[end_time_col].strip(), '%I:%M %p')
                                else:
                                    time_obj = datetime.strptime(row[end_time_col].strip(), '%H:%M')
                                
                                # Combine date and time
                                end_time = record_date.replace(
                                    hour=time_obj.hour,
                                    minute=time_obj.minute,
                                    second=0
                                )
                        except ValueError:
                            pass
                
                # If we don't have start/end times but have hours, estimate them
                if not start_time or not end_time:
                    hours_worked = None
                    
                    if hours_col and pd.notna(row[hours_col]):
                        try:
                            hours_worked = float(row[hours_col])
                        except (ValueError, TypeError):
                            # Try to extract numeric part
                            import re
                            hours_match = re.search(r'(\d+(\.\d+)?)', str(row[hours_col]))
                            if hours_match:
                                try:
                                    hours_worked = float(hours_match.group(1))
                                except ValueError:
                                    pass
                    
                    if hours_worked:
                        # If we don't have start time, assume 7am
                        if not start_time:
                            start_time = record_date.replace(hour=7, minute=0, second=0)
                        
                        # If we don't have end time, calculate from start and hours
                        if not end_time:
                            hours = int(hours_worked)
                            minutes = int((hours_worked - hours) * 60)
                            
                            end_time = start_time + timedelta(hours=hours, minutes=minutes)
                
                # Skip if we still don't have enough info
                if not start_time or not end_time:
                    # Default to standard work hours if we have nothing else
                    start_time = record_date.replace(hour=7, minute=0, second=0)
                    end_time = record_date.replace(hour=16, minute=30, second=0)
                
                # Create or get the driver
                db_driver = Driver.query.filter_by(employee_id=employee_id).first()
                if not db_driver:
                    # Parse name
                    name_parts = employee_name.split()
                    first_name = name_parts[0] if len(name_parts) > 0 else "Unknown"
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "Unknown"
                    
                    db_driver = Driver(
                        employee_id=employee_id,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True
                    )
                    db.session.add(db_driver)
                    db.session.flush()
                
                # Create or get the job site
                db_job_site = JobSite.query.filter_by(job_number=job_number).first()
                if not db_job_site:
                    db_job_site = JobSite(
                        job_number=job_number,
                        name=job_number,
                        is_active=True
                    )
                    db.session.add(db_job_site)
                    db.session.flush()
                
                # Find or create attendance record
                existing_record = AttendanceRecord.query.filter_by(
                    driver_id=db_driver.id,
                    date=record_date.replace(hour=0, minute=0, second=0, microsecond=0)
                ).first()
                
                if not existing_record:
                    # Create new record
                    new_record = AttendanceRecord(
                        driver_id=db_driver.id,
                        date=record_date.replace(hour=0, minute=0, second=0, microsecond=0),
                        assigned_job_id=db_job_site.id,
                        actual_job_id=db_job_site.id,
                        expected_start_time=record_date.replace(hour=7, minute=0, second=0),
                        expected_end_time=record_date.replace(hour=16, minute=30, second=0),
                        actual_start_time=start_time,
                        actual_end_time=end_time
                    )
                    
                    # Check for late start or early end
                    new_record.late_start = start_time > new_record.expected_start_time
                    new_record.early_end = end_time < new_record.expected_end_time
                    
                    db.session.add(new_record)
                    records_processed += 1
                else:
                    # Update existing record if our times are better
                    if not existing_record.actual_start_time or (
                            existing_record.actual_start_time and start_time and 
                            start_time < existing_record.actual_start_time):
                        existing_record.actual_start_time = start_time
                        existing_record.late_start = start_time > existing_record.expected_start_time
                    
                    if not existing_record.actual_end_time or (
                            existing_record.actual_end_time and end_time and 
                            end_time > existing_record.actual_end_time):
                        existing_record.actual_end_time = end_time
                        existing_record.early_end = end_time < existing_record.expected_end_time
                    
                    records_processed += 1
                
                # Commit every 100 records
                if records_processed % 100 == 0:
                    db.session.commit()
                    logger.info(f"Processed {records_processed} records")
        
        # Final commit
        db.session.commit()
        logger.info(f"Timecard import complete. Processed {records_processed} records, skipped {records_skipped} records.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error importing timecard data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return False


def import_all_timecards():
    """Import all timecard data from available files"""
    imported_count = 0
    
    # Look for timecard files
    timecard_files = []
    for file in os.listdir('attached_assets'):
        if 'timecard' in file.lower() or 'time card' in file.lower() or ('2025' in file and '.xls' in file.lower()):
            timecard_files.append(os.path.join('attached_assets', file))
    
    logger.info(f"Found {len(timecard_files)} potential timecard files")
    
    # Import each file
    for file_path in timecard_files:
        logger.info(f"Importing timecard file: {file_path}")
        if import_timecards(file_path):
            imported_count += 1
    
    logger.info(f"Imported {imported_count} timecard files")
    
    return imported_count > 0


if __name__ == '__main__':
    import_all_timecards()