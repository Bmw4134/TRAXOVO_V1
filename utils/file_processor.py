"""
File Upload and Processing Module

This module handles the parsing and processing of uploaded files including:
- Activity Detail (CSV/JSON)
- Work Zone Hours reports
- Equipment billing worksheets
- AL sheet (asset ↔ driver mapping)
"""
import os
import csv
import json
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename
from app import app, db
from models.reports import (
    Driver, DriverAttendance, Jobsite, WorkZoneHours, 
    EquipmentBilling, AssetDriverMapping, FileUpload
)
from models import Asset, User

# Configure file upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, file_type, user_id=None):
    """
    Save an uploaded file and create a database record
    
    Args:
        file: The file object from request.files
        file_type: Type of file being uploaded (activity, workzone, billing, al)
        user_id: ID of the user uploading the file
        
    Returns:
        FileUpload object
    """
    if file and allowed_file(file.filename):
        # Secure the filename
        original_filename = file.filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(f"{timestamp}_{original_filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save the file
        file.save(filepath)
        
        # Create database record
        file_upload = FileUpload(
            filename=filename,
            file_type=file_type,
            original_filename=original_filename,
            file_size=os.path.getsize(filepath),
            uploaded_by_id=user_id,
            process_status="Pending"
        )
        
        db.session.add(file_upload)
        db.session.commit()
        
        return file_upload
    
    return None

def get_file_extension(filename):
    """Get the file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def process_activity_detail(file_upload_id):
    """
    Process Activity Detail file
    
    Args:
        file_upload_id: ID of the FileUpload record
        
    Returns:
        tuple: (success, message, records_added)
    """
    file_upload = FileUpload.query.get(file_upload_id)
    if not file_upload:
        return False, "File upload record not found", 0
    
    filepath = os.path.join(UPLOAD_FOLDER, file_upload.filename)
    if not os.path.exists(filepath):
        return False, "File not found", 0
    
    extension = get_file_extension(file_upload.filename)
    records_added = 0
    
    try:
        # Load data based on file type
        if extension == 'csv':
            df = pd.read_csv(filepath)
        elif extension == 'json':
            with open(filepath, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        elif extension in ['xlsx', 'xls']:
            df = pd.read_excel(filepath)
        else:
            return False, f"Unsupported file extension: {extension}", 0
        
        # Process each row
        for _, row in df.iterrows():
            # Try to find driver by employee ID or create new
            employee_id = str(row.get('EmployeeID', '')).strip()
            if not employee_id:
                continue
                
            driver = Driver.query.filter_by(employee_id=employee_id).first()
            if not driver:
                driver = Driver(
                    employee_id=employee_id,
                    name=row.get('EmployeeName', ''),
                    department=row.get('Department', ''),
                    status='Active'
                )
                db.session.add(driver)
                db.session.flush()
            
            # Try to find or create jobsite
            jobsite_code = str(row.get('JobsiteCode', '')).strip()
            jobsite = None
            if jobsite_code:
                jobsite = Jobsite.query.filter_by(code=jobsite_code).first()
                if not jobsite:
                    jobsite = Jobsite(
                        code=jobsite_code,
                        name=row.get('JobsiteName', jobsite_code),
                        latitude=row.get('Latitude'),
                        longitude=row.get('Longitude')
                    )
                    db.session.add(jobsite)
                    db.session.flush()
            
            # Parse date
            try:
                date_str = row.get('Date')
                if isinstance(date_str, str):
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                elif isinstance(date_str, datetime):
                    date_obj = date_str.date()
                else:
                    continue
            except (ValueError, TypeError):
                continue
            
            # Check if attendance record already exists
            existing = DriverAttendance.query.filter_by(
                driver_id=driver.id,
                date=date_obj
            ).first()
            
            if existing:
                continue
            
            # Create attendance record
            attendance = DriverAttendance(
                driver_id=driver.id,
                date=date_obj,
                late_start=row.get('LateStart', False),
                early_end=row.get('EarlyEnd', False),
                no_jobsite=row.get('NoJobsite', False),
                total_hours=row.get('TotalHours', 0),
                billable_hours=row.get('BillableHours', 0),
                notes=row.get('Notes', '')
            )
            
            # Add jobsite if found
            if jobsite:
                attendance.jobsite_id = jobsite.id
            
            # Parse start/end times if available
            start_time = row.get('StartTime')
            if start_time:
                try:
                    if isinstance(start_time, str):
                        attendance.start_time = datetime.strptime(f"{date_str} {start_time}", '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    pass
            
            end_time = row.get('EndTime')
            if end_time:
                try:
                    if isinstance(end_time, str):
                        attendance.end_time = datetime.strptime(f"{date_str} {end_time}", '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    pass
            
            db.session.add(attendance)
            records_added += 1
            
            # Commit in batches to avoid large transactions
            if records_added % 50 == 0:
                db.session.commit()
        
        # Final commit
        db.session.commit()
        
        # Update file upload record
        file_upload.processed = True
        file_upload.process_status = "Success"
        file_upload.records_added = records_added
        db.session.commit()
        
        return True, f"Successfully processed {records_added} records", records_added
        
    except Exception as e:
        db.session.rollback()
        file_upload.process_status = f"Failed: {str(e)}"
        db.session.commit()
        return False, f"Error processing file: {str(e)}", 0

def process_workzone_hours(file_upload_id):
    """
    Process Work Zone Hours file
    
    Args:
        file_upload_id: ID of the FileUpload record
        
    Returns:
        tuple: (success, message, records_added)
    """
    file_upload = FileUpload.query.get(file_upload_id)
    if not file_upload:
        return False, "File upload record not found", 0
    
    filepath = os.path.join(UPLOAD_FOLDER, file_upload.filename)
    if not os.path.exists(filepath):
        return False, "File not found", 0
    
    extension = get_file_extension(file_upload.filename)
    records_added = 0
    
    try:
        # Load data based on file type
        if extension == 'csv':
            df = pd.read_csv(filepath)
        elif extension == 'json':
            with open(filepath, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        elif extension in ['xlsx', 'xls']:
            df = pd.read_excel(filepath)
        else:
            return False, f"Unsupported file extension: {extension}", 0
        
        # Process each row
        for _, row in df.iterrows():
            # Try to find or create jobsite
            jobsite_code = str(row.get('JobsiteCode', '')).strip()
            if not jobsite_code:
                continue
                
            jobsite = Jobsite.query.filter_by(code=jobsite_code).first()
            if not jobsite:
                jobsite = Jobsite(
                    code=jobsite_code,
                    name=row.get('JobsiteName', jobsite_code),
                    latitude=row.get('Latitude'),
                    longitude=row.get('Longitude')
                )
                db.session.add(jobsite)
                db.session.flush()
            
            # Parse date
            try:
                date_str = row.get('Date')
                if isinstance(date_str, str):
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                elif isinstance(date_str, datetime):
                    date_obj = date_str.date()
                else:
                    continue
            except (ValueError, TypeError):
                continue
            
            # Check if work zone record already exists
            existing = WorkZoneHours.query.filter_by(
                jobsite_id=jobsite.id,
                date=date_obj
            ).first()
            
            if existing:
                # Update existing record
                existing.total_hours = row.get('TotalHours', existing.total_hours)
                existing.equipment_hours = row.get('EquipmentHours', existing.equipment_hours)
                existing.labor_hours = row.get('LaborHours', existing.labor_hours)
                existing.expected_hours = row.get('ExpectedHours', existing.expected_hours)
                
                # Calculate efficiency if both values are present
                if existing.total_hours and existing.expected_hours and existing.expected_hours > 0:
                    existing.efficiency_percentage = (existing.total_hours / existing.expected_hours) * 100
            else:
                # Create new work zone hours record
                work_hours = WorkZoneHours(
                    jobsite_id=jobsite.id,
                    date=date_obj,
                    total_hours=row.get('TotalHours', 0),
                    equipment_hours=row.get('EquipmentHours', 0),
                    labor_hours=row.get('LaborHours', 0),
                    expected_hours=row.get('ExpectedHours', 0)
                )
                
                # Calculate efficiency if both values are present
                if work_hours.total_hours and work_hours.expected_hours and work_hours.expected_hours > 0:
                    work_hours.efficiency_percentage = (work_hours.total_hours / work_hours.expected_hours) * 100
                
                db.session.add(work_hours)
                records_added += 1
            
            # Commit in batches to avoid large transactions
            if records_added % 50 == 0:
                db.session.commit()
        
        # Final commit
        db.session.commit()
        
        # Update file upload record
        file_upload.processed = True
        file_upload.process_status = "Success"
        file_upload.records_added = records_added
        db.session.commit()
        
        return True, f"Successfully processed {records_added} records", records_added
        
    except Exception as e:
        db.session.rollback()
        file_upload.process_status = f"Failed: {str(e)}"
        db.session.commit()
        return False, f"Error processing file: {str(e)}", 0

def process_equipment_billing(file_upload_id):
    """
    Process Equipment Billing Worksheet
    
    Args:
        file_upload_id: ID of the FileUpload record
        
    Returns:
        tuple: (success, message, records_added)
    """
    file_upload = FileUpload.query.get(file_upload_id)
    if not file_upload:
        return False, "File upload record not found", 0
    
    filepath = os.path.join(UPLOAD_FOLDER, file_upload.filename)
    if not os.path.exists(filepath):
        return False, "File not found", 0
    
    extension = get_file_extension(file_upload.filename)
    records_added = 0
    
    try:
        # Load data based on file type
        if extension == 'csv':
            df = pd.read_csv(filepath)
        elif extension == 'json':
            with open(filepath, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        elif extension in ['xlsx', 'xls']:
            df = pd.read_excel(filepath)
        else:
            return False, f"Unsupported file extension: {extension}", 0
        
        # Process each row
        for _, row in df.iterrows():
            # Try to find asset
            asset_identifier = str(row.get('AssetIdentifier', '')).strip()
            if not asset_identifier:
                continue
                
            asset = Asset.query.filter_by(asset_identifier=asset_identifier).first()
            if not asset:
                continue  # Skip if asset not found
            
            # Parse month and year
            try:
                month = int(row.get('Month', 0))
                year = int(row.get('Year', 0))
                if month < 1 or month > 12 or year < 2000:
                    continue
            except (ValueError, TypeError):
                continue
            
            # Check if billing record already exists
            existing = EquipmentBilling.query.filter_by(
                asset_id=asset.id,
                month=month,
                year=year
            ).first()
            
            if existing:
                # Update existing record
                existing.category = row.get('Category', existing.category)
                existing.hours_used = row.get('HoursUsed', existing.hours_used)
                existing.rate = row.get('Rate', existing.rate)
                existing.total_amount = row.get('TotalAmount', existing.total_amount)
                existing.notes = row.get('Notes', existing.notes)
            else:
                # Create new billing record
                billing = EquipmentBilling(
                    asset_id=asset.id,
                    month=month,
                    year=year,
                    category=row.get('Category', ''),
                    hours_used=row.get('HoursUsed', 0),
                    rate=row.get('Rate', 0),
                    total_amount=row.get('TotalAmount', 0),
                    notes=row.get('Notes', '')
                )
                
                # Try to find jobsite if specified
                jobsite_code = str(row.get('JobsiteCode', '')).strip()
                if jobsite_code:
                    jobsite = Jobsite.query.filter_by(code=jobsite_code).first()
                    if jobsite:
                        billing.jobsite_id = jobsite.id
                
                db.session.add(billing)
                records_added += 1
            
            # Commit in batches to avoid large transactions
            if records_added % 50 == 0:
                db.session.commit()
        
        # Final commit
        db.session.commit()
        
        # Update file upload record
        file_upload.processed = True
        file_upload.process_status = "Success"
        file_upload.records_added = records_added
        db.session.commit()
        
        return True, f"Successfully processed {records_added} records", records_added
        
    except Exception as e:
        db.session.rollback()
        file_upload.process_status = f"Failed: {str(e)}"
        db.session.commit()
        return False, f"Error processing file: {str(e)}", 0

def process_asset_driver_mapping(file_upload_id):
    """
    Process Asset-Driver Mapping (AL Sheet)
    
    Args:
        file_upload_id: ID of the FileUpload record
        
    Returns:
        tuple: (success, message, records_added)
    """
    file_upload = FileUpload.query.get(file_upload_id)
    if not file_upload:
        return False, "File upload record not found", 0
    
    filepath = os.path.join(UPLOAD_FOLDER, file_upload.filename)
    if not os.path.exists(filepath):
        return False, "File not found", 0
    
    extension = get_file_extension(file_upload.filename)
    records_added = 0
    
    try:
        # Load data based on file type
        if extension == 'csv':
            df = pd.read_csv(filepath)
        elif extension == 'json':
            with open(filepath, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        elif extension in ['xlsx', 'xls']:
            df = pd.read_excel(filepath)
        else:
            return False, f"Unsupported file extension: {extension}", 0
        
        # Process each row
        for _, row in df.iterrows():
            # Try to find asset
            asset_identifier = str(row.get('AssetIdentifier', '')).strip()
            if not asset_identifier:
                continue
                
            asset = Asset.query.filter_by(asset_identifier=asset_identifier).first()
            if not asset:
                continue  # Skip if asset not found
            
            # Try to find driver
            employee_id = str(row.get('EmployeeID', '')).strip()
            if not employee_id:
                continue
                
            driver = Driver.query.filter_by(employee_id=employee_id).first()
            if not driver:
                # Create new driver if not found
                driver = Driver(
                    employee_id=employee_id,
                    name=row.get('EmployeeName', ''),
                    status='Active'
                )
                db.session.add(driver)
                db.session.flush()
            
            # Parse dates
            start_date = None
            if row.get('StartDate'):
                try:
                    start_date_str = row.get('StartDate')
                    if isinstance(start_date_str, str):
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    elif isinstance(start_date_str, datetime):
                        start_date = start_date_str.date()
                except (ValueError, TypeError):
                    pass
            
            end_date = None
            if row.get('EndDate'):
                try:
                    end_date_str = row.get('EndDate')
                    if isinstance(end_date_str, str):
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    elif isinstance(end_date_str, datetime):
                        end_date = end_date_str.date()
                except (ValueError, TypeError):
                    pass
            
            # Determine if this is current assignment
            is_current = row.get('IsCurrent', True)
            if isinstance(is_current, str):
                is_current = is_current.lower() in ['true', 'yes', '1', 'y']
            
            # If this is a current assignment, end previous assignments
            if is_current:
                previous_assignments = AssetDriverMapping.query.filter_by(
                    asset_id=asset.id,
                    is_current=True
                ).all()
                
                for prev in previous_assignments:
                    prev.is_current = False
                    if not prev.end_date:
                        prev.end_date = datetime.now().date()
            
            # Create new mapping
            mapping = AssetDriverMapping(
                asset_id=asset.id,
                driver_id=driver.id,
                start_date=start_date,
                end_date=end_date,
                is_current=is_current
            )
            
            db.session.add(mapping)
            records_added += 1
            
            # Commit in batches to avoid large transactions
            if records_added % 50 == 0:
                db.session.commit()
        
        # Final commit
        db.session.commit()
        
        # Update file upload record
        file_upload.processed = True
        file_upload.process_status = "Success"
        file_upload.records_added = records_added
        db.session.commit()
        
        return True, f"Successfully processed {records_added} records", records_added
        
    except Exception as e:
        db.session.rollback()
        file_upload.process_status = f"Failed: {str(e)}"
        db.session.commit()
        return False, f"Error processing file: {str(e)}", 0

def process_uploaded_file(file_upload_id):
    """
    Process an uploaded file based on its type
    
    Args:
        file_upload_id: ID of the FileUpload record
        
    Returns:
        tuple: (success, message, records_added)
    """
    file_upload = FileUpload.query.get(file_upload_id)
    if not file_upload:
        return False, "File upload record not found", 0
    
    # Process based on file type
    file_type = file_upload.file_type.lower() if file_upload.file_type else ""
    
    if "activity" in file_type:
        return process_activity_detail(file_upload_id)
    elif "workzone" in file_type or "work zone" in file_type:
        return process_workzone_hours(file_upload_id)
    elif "billing" in file_type or "equipment" in file_type:
        return process_equipment_billing(file_upload_id)
    elif "al" in file_type or "mapping" in file_type:
        return process_asset_driver_mapping(file_upload_id)
    else:
        file_upload.process_status = "Failed: Unknown file type"
        db.session.commit()
        return False, f"Unknown file type: {file_type}", 0