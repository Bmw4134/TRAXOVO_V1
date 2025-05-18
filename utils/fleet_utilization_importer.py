"""
Fleet Utilization Importer

This module provides utilities for importing and processing fleet utilization data
from Excel reports.
"""
import os
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app import db
from models.driver_attendance import Driver, JobSite, AttendanceRecord

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_fleet_utilization(file_path):
    """
    Import fleet utilization data from Excel file
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        bool: True if import was successful, False otherwise
    """
    try:
        logger.info(f"Importing fleet utilization data from {file_path}")
        
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Log columns and shape for debugging
        logger.info(f"Excel file columns: {df.columns.tolist()}")
        logger.info(f"Excel file shape: {df.shape}")
        
        # Process data based on column structure
        # Since we can't preview the Excel file, we'll try various common column names
        
        # Track processed records
        records_processed = 0
        records_skipped = 0
        
        # Try to identify relevant columns
        asset_col = None
        for col in df.columns:
            if 'asset' in str(col).lower() or 'equipment' in str(col).lower() or 'vehicle' in str(col).lower():
                asset_col = col
                break
        
        driver_col = None
        for col in df.columns:
            if 'driver' in str(col).lower() or 'operator' in str(col).lower() or 'employee' in str(col).lower():
                driver_col = col
                break
        
        job_col = None
        for col in df.columns:
            if 'job' in str(col).lower() or 'site' in str(col).lower() or 'location' in str(col).lower() or 'project' in str(col).lower():
                job_col = col
                break
        
        date_col = None
        for col in df.columns:
            if 'date' in str(col).lower() or 'day' in str(col).lower() or 'time' in str(col).lower():
                date_col = col
                break
        
        utilization_col = None
        for col in df.columns:
            if 'util' in str(col).lower() or 'usage' in str(col).lower() or 'hours' in str(col).lower() or 'time' in str(col).lower():
                utilization_col = col
                break
        
        # Log which columns were identified
        logger.info(f"Identified columns - Asset: {asset_col}, Driver: {driver_col}, Job: {job_col}, Date: {date_col}, Utilization: {utilization_col}")
        
        # Check if we found enough columns to process
        if not asset_col or not date_col:
            logger.error("Could not identify required columns (asset and date)")
            return False
        
        # Process rows
        for idx, row in df.iterrows():
            # Skip rows with missing essential data
            if pd.isna(row[asset_col]) or (date_col and pd.isna(row[date_col])):
                records_skipped += 1
                continue
            
            # Extract asset info
            asset = str(row[asset_col]).strip()
            
            # Extract driver info if available
            driver_id = None
            driver_name = None
            if driver_col and pd.notna(row[driver_col]):
                driver_name = str(row[driver_col]).strip()
                # Try to extract employee ID if it's in the format "Name (ID)"
                if "(" in driver_name and ")" in driver_name:
                    parts = driver_name.split("(")
                    if len(parts) > 1:
                        possible_id = parts[1].split(")")[0].strip()
                        if possible_id.isalnum():
                            driver_id = possible_id
                
                # If no ID was found but we have a name, use a placeholder ID
                if not driver_id and driver_name:
                    driver_id = f"FU-{driver_name.replace(' ', '')[:8]}"
            
            # Extract job site info if available
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
            
            # Extract date info
            record_date = None
            if date_col:
                try:
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
                    
                    # If still no date, try extracting from a string
                    if not record_date and isinstance(row[date_col], str):
                        date_str = row[date_col]
                        # Try to extract date in MM/DD/YYYY format
                        import re
                        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
                        if date_match:
                            month, day, year = date_match.groups()
                            if len(year) == 2:
                                year = f"20{year}"
                            try:
                                record_date = datetime(int(year), int(month), int(day))
                            except ValueError:
                                pass
                except Exception as e:
                    logger.error(f"Error parsing date {row[date_col]}: {str(e)}")
            
            # If still no date, use today's date
            if not record_date:
                record_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Skip if we don't have essential information
            if not asset or not record_date:
                records_skipped += 1
                continue
            
            # Create/update database entries
            try:
                # If we have a driver, create or get the driver
                db_driver = None
                if driver_id:
                    db_driver = Driver.query.filter_by(employee_id=driver_id).first()
                    if not db_driver:
                        if driver_name:
                            first_name = driver_name.split()[0] if len(driver_name.split()) > 0 else "Unknown"
                            last_name = " ".join(driver_name.split()[1:]) if len(driver_name.split()) > 1 else "Unknown"
                        else:
                            first_name = "Unknown"
                            last_name = "Unknown"
                        
                        db_driver = Driver(
                            employee_id=driver_id,
                            first_name=first_name,
                            last_name=last_name,
                            is_active=True
                        )
                        db.session.add(db_driver)
                        db.session.flush()  # Get ID without committing
                
                # If we have a job site, create or get it
                db_job_site = None
                if job_number:
                    db_job_site = JobSite.query.filter_by(job_number=job_number).first()
                    if not db_job_site:
                        db_job_site = JobSite(
                            job_number=job_number,
                            name=job_number,
                            is_active=True
                        )
                        db.session.add(db_job_site)
                        db.session.flush()  # Get ID without committing
                
                # Only create attendance record if we have both driver and job site
                if db_driver and db_job_site:
                    # Check if a record already exists for this date/driver
                    existing_record = AttendanceRecord.query.filter_by(
                        driver_id=db_driver.id,
                        date=record_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    ).first()
                    
                    if not existing_record:
                        # Create new record
                        new_record = AttendanceRecord(
                            driver_id=db_driver.id,
                            date=record_date.replace(hour=0, minute=0, second=0, microsecond=0),
                            asset_id=asset.split(" - ")[0].strip() if " - " in asset else asset,
                            assigned_job_id=db_job_site.id,
                            actual_job_id=db_job_site.id
                        )
                        
                        # Set expected times based on typical work day
                        new_record.expected_start_time = record_date.replace(hour=7, minute=0, second=0)
                        new_record.expected_end_time = record_date.replace(hour=16, minute=30, second=0)
                        
                        # If utilization column exists, calculate times
                        hours_worked = None
                        if utilization_col and pd.notna(row[utilization_col]):
                            try:
                                hours_worked = float(row[utilization_col])
                            except (ValueError, TypeError):
                                # Try to extract numeric part
                                import re
                                hours_match = re.search(r'(\d+(\.\d+)?)', str(row[utilization_col]))
                                if hours_match:
                                    try:
                                        hours_worked = float(hours_match.group(1))
                                    except ValueError:
                                        pass
                        
                        if hours_worked:
                            # Assume start at 7am and calculate end time based on hours worked
                            new_record.actual_start_time = record_date.replace(hour=7, minute=0, second=0)
                            
                            # Calculate end time (start + hours worked)
                            hours = int(hours_worked)
                            minutes = int((hours_worked - hours) * 60)
                            end_time = new_record.actual_start_time.replace(
                                hour=new_record.actual_start_time.hour + hours,
                                minute=new_record.actual_start_time.minute + minutes
                            )
                            new_record.actual_end_time = end_time
                            
                            # Check for late start or early end
                            new_record.late_start = new_record.actual_start_time > new_record.expected_start_time
                            new_record.early_end = new_record.actual_end_time < new_record.expected_end_time
                        
                        db.session.add(new_record)
                        records_processed += 1
                        
                        # Commit every 100 records to avoid memory issues
                        if records_processed % 100 == 0:
                            db.session.commit()
                            logger.info(f"Processed {records_processed} records")
                    else:
                        # Update existing record if needed
                        updated = False
                        
                        # Update asset ID if not already set
                        if not existing_record.asset_id:
                            existing_record.asset_id = asset.split(" - ")[0].strip() if " - " in asset else asset
                            updated = True
                        
                        # If utilization column exists, update times if not already set
                        hours_worked = None
                        if utilization_col and pd.notna(row[utilization_col]):
                            try:
                                hours_worked = float(row[utilization_col])
                            except (ValueError, TypeError):
                                # Try to extract numeric part
                                import re
                                hours_match = re.search(r'(\d+(\.\d+)?)', str(row[utilization_col]))
                                if hours_match:
                                    try:
                                        hours_worked = float(hours_match.group(1))
                                    except ValueError:
                                        pass
                        
                        if hours_worked and (not existing_record.actual_start_time or not existing_record.actual_end_time):
                            # Assume start at 7am and calculate end time based on hours worked
                            if not existing_record.actual_start_time:
                                existing_record.actual_start_time = record_date.replace(hour=7, minute=0, second=0)
                                updated = True
                            
                            # Calculate end time (start + hours worked)
                            if not existing_record.actual_end_time:
                                hours = int(hours_worked)
                                minutes = int((hours_worked - hours) * 60)
                                end_time = existing_record.actual_start_time.replace(
                                    hour=existing_record.actual_start_time.hour + hours,
                                    minute=existing_record.actual_start_time.minute + minutes
                                )
                                existing_record.actual_end_time = end_time
                                updated = True
                            
                            # Check for late start or early end
                            if updated:
                                existing_record.late_start = existing_record.actual_start_time > existing_record.expected_start_time
                                existing_record.early_end = existing_record.actual_end_time < existing_record.expected_end_time
                        
                        if updated:
                            records_processed += 1
                            
                            # Commit every 100 records to avoid memory issues
                            if records_processed % 100 == 0:
                                db.session.commit()
                                logger.info(f"Processed {records_processed} records")
            
            except Exception as e:
                logger.error(f"Error processing row {idx}: {str(e)}")
                records_skipped += 1
        
        # Final commit
        db.session.commit()
        
        logger.info(f"Fleet utilization import complete. Processed {records_processed} records, skipped {records_skipped} records.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error importing fleet utilization data: {str(e)}")
        db.session.rollback()
        return False