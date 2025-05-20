"""
Unified Data Processor

This module provides a unified interface for processing all source data types,
ensuring consistent parsing and output regardless of file format or source.
"""

import os
import csv
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# Import attendance audit module
from utils.attendance_audit import (
    create_audit_record,
    add_source_file,
    update_stats,
    log_error,
    complete_audit
)

# Set up logging
logger = logging.getLogger(__name__)

# Constants
DRIVING_HISTORY_COLUMNS = [
    'EventDateTime', 'Contact', 'MsgType', 'Location', 'Latitude', 'Longitude'
]
ACTIVITY_DETAIL_COLUMNS = [
    'DateTime', 'Activity', 'Driver', 'Asset', 'Location'
]
ASSET_ONSITE_COLUMNS = [
    'Asset', 'StartDateTime', 'EndDateTime', 'Location', 'Duration'
]

class UnifiedDataProcessor:
    """
    Unified data processor for all source data types
    """
    
    def __init__(self, date_str):
        """
        Initialize processor for a specific date
        
        Args:
            date_str (str): Date in YYYY-MM-DD format
        """
        self.date_str = date_str
        self.date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Create audit record
        self.audit_record = create_audit_record(date_str)
        
        # Initialize data containers
        self.driving_history_data = []
        self.activity_detail_data = []
        self.asset_onsite_data = []
        self.start_time_job_data = []
        self.employee_data = []
        
        # Output path
        self.output_dir = Path('processed')
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized unified data processor for {date_str}")
    
    def process_driving_history(self, file_path):
        """
        Process driving history file
        
        Args:
            file_path (str): Path to the driving history file
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Processing driving history file: {file_path}")
            
            # Add file to audit record
            add_source_file(self.date_str, file_path, 'driving_history')
            
            # Read file manually due to custom format
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find header line
            header_line = 0
            for i, line in enumerate(lines):
                if ('EventDateTime' in line and 'MsgType' in line) or i > 20:
                    header_line = i
                    break
            
            # Extract header
            headers = lines[header_line].strip().split(',')
            
            # Process data rows using CSV reader to handle quoted values
            data = []
            for line in lines[header_line+1:]:
                if not line.strip():
                    continue
                
                # Use CSV reader to handle quoted values
                reader = csv.reader([line])
                row = next(reader)
                
                # Skip rows with insufficient fields
                if len(row) < 7:
                    continue
                
                # Ensure row matches header length
                if len(row) > len(headers):
                    row = row[:len(headers)]
                elif len(row) < len(headers):
                    row += [''] * (len(headers) - len(row))
                
                # Create record
                record = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        record[header] = row[i]
                    else:
                        record[header] = ''
                
                # Parse date and time
                if 'EventDateTime' in record and record['EventDateTime']:
                    try:
                        dt = pd.to_datetime(record['EventDateTime'])
                        record_date = dt.date()
                        
                        # Only include records for the target date
                        if record_date == self.date_obj:
                            data.append(record)
                    except:
                        pass
            
            logger.info(f"Found {len(data)} driving history records for {self.date_str}")
            
            # Store data
            self.driving_history_data = data
            
            # Extract driver info
            drivers = {}
            for record in data:
                driver_name = record.get('Contact', '')
                if not driver_name:
                    continue
                
                # Extract employee ID if available
                employee_id = None
                if '(' in driver_name and ')' in driver_name:
                    id_part = driver_name.split('(')[1].split(')')[0]
                    if id_part.isdigit():
                        employee_id = id_part
                
                # Clean up driver name
                clean_name = driver_name.split('(')[0].strip() if '(' in driver_name else driver_name
                
                # Initialize driver record
                if clean_name not in drivers:
                    drivers[clean_name] = {
                        'name': clean_name,
                        'employee_id': employee_id,
                        'events': [],
                        'key_on_count': 0,
                        'key_off_count': 0,
                        'first_activity': None,
                        'last_activity': None,
                        'locations': set()
                    }
                
                # Process event
                if 'EventDateTime' in record and record['EventDateTime']:
                    try:
                        dt = pd.to_datetime(record['EventDateTime'])
                        
                        # Add event
                        event_type = record.get('MsgType', '')
                        event = {
                            'time': dt,
                            'type': event_type,
                            'location': record.get('Location', '')
                        }
                        drivers[clean_name]['events'].append(event)
                        
                        # Count key events
                        if event_type == 'Key On':
                            drivers[clean_name]['key_on_count'] += 1
                        elif event_type == 'Key Off':
                            drivers[clean_name]['key_off_count'] += 1
                        
                        # Update activity timestamps
                        if drivers[clean_name]['first_activity'] is None or dt < drivers[clean_name]['first_activity']:
                            drivers[clean_name]['first_activity'] = dt
                        
                        if drivers[clean_name]['last_activity'] is None or dt > drivers[clean_name]['last_activity']:
                            drivers[clean_name]['last_activity'] = dt
                        
                        # Add location
                        if 'Location' in record and record['Location']:
                            drivers[clean_name]['locations'].add(record['Location'])
                    except:
                        pass
            
            # Convert to list
            driver_list = []
            for driver_name, driver_data in drivers.items():
                # Convert sets to lists
                driver_data['locations'] = list(driver_data['locations'])
                
                # Add source
                driver_data['source'] = 'driving_history'
                
                # Add date
                driver_data['date'] = self.date_str
                
                driver_list.append(driver_data)
            
            # Save processed drivers
            output_file = self.output_dir / f"drivers_{self.date_str}.json"
            with open(output_file, 'w') as f:
                json.dump(driver_list, f, indent=2, default=str)
            
            logger.info(f"Processed {len(driver_list)} drivers from driving history")
            
            # Update stats
            update_stats(self.date_str, {
                'total_drivers': len(driver_list),
                'driving_history_records': len(data)
            })
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing driving history: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Log error in audit record
            log_error(self.date_str, str(e), f"driving_history:{file_path}")
            
            return False
    
    def process_activity_detail(self, file_path):
        """
        Process activity detail file
        
        Args:
            file_path (str): Path to the activity detail file
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Processing activity detail file: {file_path}")
            
            # Add file to audit record
            add_source_file(self.date_str, file_path, 'activity_detail')
            
            # Try different encoding options
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    # For CSV files
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
                        break
                    # For Excel files
                    elif file_path.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(file_path)
                        break
                except Exception as e:
                    logger.warning(f"Failed to read with {encoding} encoding: {e}")
            
            if df is None:
                logger.error(f"Could not read file with any encoding: {file_path}")
                log_error(self.date_str, "Could not read file with any encoding", f"activity_detail:{file_path}")
                return False
            
            # Filter by date
            if 'DateTime' in df.columns:
                df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
                df['Date'] = df['DateTime'].dt.date
                df = df[df['Date'] == self.date_obj]
            
            logger.info(f"Found {len(df)} activity detail records for {self.date_str}")
            
            # Store data
            self.activity_detail_data = df.to_dict('records')
            
            # Extract driver info
            drivers = {}
            for record in self.activity_detail_data:
                driver_name = record.get('Driver', '')
                if not driver_name or pd.isna(driver_name):
                    continue
                
                # Clean up driver name
                driver_name = str(driver_name).strip()
                
                # Initialize driver record
                if driver_name not in drivers:
                    drivers[driver_name] = {
                        'name': driver_name,
                        'activities': [],
                        'asset_id': None,
                        'locations': set()
                    }
                
                # Process activity
                if 'DateTime' in record and record['DateTime'] and not pd.isna(record['DateTime']):
                    # Add activity
                    activity_type = record.get('Activity', '')
                    activity = {
                        'time': record['DateTime'],
                        'type': activity_type,
                        'location': record.get('Location', '') if not pd.isna(record.get('Location', '')) else ''
                    }
                    drivers[driver_name]['activities'].append(activity)
                    
                    # Add location
                    if 'Location' in record and record['Location'] and not pd.isna(record['Location']):
                        drivers[driver_name]['locations'].add(str(record['Location']))
                
                # Capture asset ID
                if 'Asset' in record and record['Asset'] and not pd.isna(record['Asset']):
                    drivers[driver_name]['asset_id'] = str(record['Asset'])
            
            # Merge with existing driver list
            self._merge_driver_data(drivers, 'activity_detail')
            
            # Update stats
            update_stats(self.date_str, {
                'activity_detail_records': len(self.activity_detail_data)
            })
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing activity detail: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Log error in audit record
            log_error(self.date_str, str(e), f"activity_detail:{file_path}")
            
            return False
    
    def process_asset_onsite(self, file_path):
        """
        Process assets time on site file
        
        Args:
            file_path (str): Path to the assets time on site file
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Processing assets time on site file: {file_path}")
            
            # Add file to audit record
            add_source_file(self.date_str, file_path, 'asset_onsite')
            
            # Try different encoding options
            encodings = ['utf-8', 'latin-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    # For CSV files
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
                        break
                    # For Excel files
                    elif file_path.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(file_path)
                        break
                except Exception as e:
                    logger.warning(f"Failed to read with {encoding} encoding: {e}")
            
            if df is None:
                logger.error(f"Could not read file with any encoding: {file_path}")
                log_error(self.date_str, "Could not read file with any encoding", f"asset_onsite:{file_path}")
                return False
            
            # Filter by date
            if 'StartDateTime' in df.columns:
                df['StartDateTime'] = pd.to_datetime(df['StartDateTime'], errors='coerce')
                df['Date'] = df['StartDateTime'].dt.date
                df = df[df['Date'] == self.date_obj]
            
            logger.info(f"Found {len(df)} asset onsite records for {self.date_str}")
            
            # Store data
            self.asset_onsite_data = df.to_dict('records')
            
            # Extract asset info
            assets = {}
            for record in self.asset_onsite_data:
                asset_id = record.get('Asset', '')
                if not asset_id or pd.isna(asset_id):
                    continue
                
                # Clean up asset ID
                asset_id = str(asset_id).strip()
                
                # Initialize asset record
                if asset_id not in assets:
                    assets[asset_id] = {
                        'asset_id': asset_id,
                        'time_onsite': [],
                        'locations': set(),
                        'total_duration': 0
                    }
                
                # Process on-site time
                if ('StartDateTime' in record and record['StartDateTime'] and 
                    'EndDateTime' in record and record['EndDateTime'] and 
                    not pd.isna(record['StartDateTime']) and not pd.isna(record['EndDateTime'])):
                    
                    # Calculate duration
                    duration = 0
                    if 'Duration' in record and record['Duration'] and not pd.isna(record['Duration']):
                        try:
                            duration = float(record['Duration'])
                        except:
                            pass
                    
                    # Add on-site time
                    onsite = {
                        'start_time': record['StartDateTime'],
                        'end_time': record['EndDateTime'],
                        'duration': duration,
                        'location': record.get('Location', '') if not pd.isna(record.get('Location', '')) else ''
                    }
                    assets[asset_id]['time_onsite'].append(onsite)
                    assets[asset_id]['total_duration'] += duration
                    
                    # Add location
                    if 'Location' in record and record['Location'] and not pd.isna(record['Location']):
                        assets[asset_id]['locations'].add(str(record['Location']))
            
            # Convert to list
            asset_list = []
            for asset_id, asset_data in assets.items():
                # Convert sets to lists
                asset_data['locations'] = list(asset_data['locations'])
                
                # Add source
                asset_data['source'] = 'asset_onsite'
                
                # Add date
                asset_data['date'] = self.date_str
                
                asset_list.append(asset_data)
            
            # Save processed assets
            output_file = self.output_dir / f"assets_{self.date_str}.json"
            with open(output_file, 'w') as f:
                json.dump(asset_list, f, indent=2, default=str)
            
            logger.info(f"Processed {len(asset_list)} assets from time on site data")
            
            # Update stats
            update_stats(self.date_str, {
                'assets_count': len(asset_list),
                'asset_onsite_records': len(self.asset_onsite_data)
            })
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing asset onsite data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Log error in audit record
            log_error(self.date_str, str(e), f"asset_onsite:{file_path}")
            
            return False
    
    def process_start_time_job_sheet(self, file_path, sheet_name='Start Time & Job'):
        """
        Process Start Time & Job sheet from Excel file
        
        Args:
            file_path (str): Path to the Excel file
            sheet_name (str): Name of the start time and job sheet
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Processing Start Time & Job sheet from {file_path}")
            
            # Add file to audit record
            add_source_file(self.date_str, file_path, 'start_time_job')
            
            # Try to find the correct sheet name
            xl = pd.ExcelFile(file_path)
            sheet_names = xl.sheet_names
            
            # Look for the Start Time & Job sheet
            found_sheet = None
            potential_sheet_names = [
                'Start Time & Job', 'Start Time', 'Start Times', 'Start Time and Job',
                # Add variations
                'START TIME & JOB', 'START TIME', 'START TIMES'
            ]
            
            for name in potential_sheet_names:
                if name in sheet_names:
                    found_sheet = name
                    break
            
            # If not found, look for any sheet with "Start" and "Time" in the name
            if found_sheet is None:
                for name in sheet_names:
                    if 'START' in name.upper() and 'TIME' in name.upper():
                        found_sheet = name
                        break
            
            if found_sheet is None:
                logger.error(f"Could not find Start Time & Job sheet in {file_path}")
                log_error(self.date_str, "Could not find Start Time & Job sheet", f"start_time_job:{file_path}")
                return False
            
            logger.info(f"Found sheet: {found_sheet}")
            
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=found_sheet)
            
            # Clean up and normalize the DataFrame
            df = df.dropna(how='all')  # Remove empty rows
            
            # Convert column names to strings and normalize
            df.columns = [str(col).strip() if col is not None else f'col_{i}' 
                         for i, col in enumerate(df.columns)]
            
            # Find the key column names (case-insensitive)
            asset_col = None
            driver_col = None
            job_col = None
            emp_id_col = None
            
            for col in df.columns:
                col_upper = col.upper()
                if 'ASSET' in col_upper:
                    asset_col = col
                elif 'DRIVER' in col_upper:
                    driver_col = col
                elif 'JOB' in col_upper and 'SR' not in col_upper:
                    job_col = col
                elif 'EMP' in col_upper and 'ID' in col_upper:
                    emp_id_col = col
            
            # Create standardized columns
            if asset_col:
                df['Asset ID'] = df[asset_col]
            if driver_col:
                df['Driver'] = df[driver_col]
            if job_col:
                df['Job'] = df[job_col]
            if emp_id_col:
                df['Employee ID'] = df[emp_id_col]
            
            # Filter out rows without asset ID or driver
            if 'Asset ID' in df.columns:
                df = df[df['Asset ID'].notna()]
            if 'Driver' in df.columns:
                df = df[df['Driver'].notna()]
            
            # Add report date
            df['Report Date'] = self.date_str
            
            logger.info(f"Processed {len(df)} rows from Start Time & Job sheet")
            
            # Store data
            self.start_time_job_data = df.to_dict('records')
            
            # Extract driver and job assignment info
            drivers = {}
            for record in self.start_time_job_data:
                asset_id = record.get('Asset ID', '')
                driver_name = record.get('Driver', '')
                job_number = record.get('Job', '')
                employee_id = record.get('Employee ID', '')
                
                if not asset_id or pd.isna(asset_id) or not driver_name or pd.isna(driver_name):
                    continue
                
                # Clean up values
                asset_id = str(asset_id).strip()
                driver_name = str(driver_name).strip()
                job_number = str(job_number).strip() if job_number and not pd.isna(job_number) else ''
                employee_id = str(employee_id).strip() if employee_id and not pd.isna(employee_id) else ''
                
                # Initialize driver record
                if driver_name not in drivers:
                    drivers[driver_name] = {
                        'name': driver_name,
                        'asset_id': asset_id,
                        'job_number': job_number,
                        'employee_id': employee_id,
                        'source': 'start_time_job'
                    }
            
            # Merge with existing driver list
            self._merge_driver_data(drivers, 'start_time_job')
            
            # Update stats
            update_stats(self.date_str, {
                'start_time_job_records': len(self.start_time_job_data)
            })
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing Start Time & Job sheet: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Log error in audit record
            log_error(self.date_str, str(e), f"start_time_job:{file_path}")
            
            return False
    
    def process_employee_data(self, file_path, sheet_name=None):
        """
        Process employee data from Excel file
        
        Args:
            file_path (str): Path to the employee data file
            sheet_name (str): Name of the sheet to read
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Processing employee data from {file_path}")
            
            # Add file to audit record
            add_source_file(self.date_str, file_path, 'employee_data')
            
            # Try to read the file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                # Try to find the right sheet
                xl = pd.ExcelFile(file_path)
                sheet_names = xl.sheet_names
                
                # Look for employee data sheet
                potential_sheets = [
                    'Employee_Contacts', 'Employees', 'Employee List', 'ELIST',
                    'Employee_List', 'Employee_Data'
                ]
                
                found_sheet = None
                for name in potential_sheets:
                    if name in sheet_names:
                        found_sheet = name
                        break
                
                if found_sheet:
                    logger.info(f"Found employee sheet: {found_sheet}")
                    df = pd.read_excel(file_path, sheet_name=found_sheet)
                else:
                    # Default to first sheet
                    logger.warning(f"Could not find employee sheet, using first sheet")
                    df = pd.read_excel(file_path)
            
            # Clean up and normalize the DataFrame
            df = df.dropna(how='all')  # Remove empty rows
            
            # Store the data
            self.employee_data = df.to_dict('records')
            
            logger.info(f"Processed {len(self.employee_data)} employee records")
            
            # Update stats
            update_stats(self.date_str, {
                'employee_records': len(self.employee_data)
            })
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing employee data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Log error in audit record
            log_error(self.date_str, str(e), f"employee_data:{file_path}")
            
            return False
    
    def _merge_driver_data(self, new_drivers, source):
        """
        Merge new driver data with existing driver data
        
        Args:
            new_drivers (dict): Dictionary of new driver data
            source (str): Source of the data
        """
        # Load existing driver data
        driver_file = self.output_dir / f"drivers_{self.date_str}.json"
        
        if os.path.exists(driver_file):
            try:
                with open(driver_file, 'r') as f:
                    driver_list = json.load(f)
                
                # Convert to dictionary for easier merging
                existing_drivers = {}
                for driver in driver_list:
                    existing_drivers[driver['name']] = driver
                
                # Merge with new drivers
                for driver_name, driver_data in new_drivers.items():
                    if driver_name in existing_drivers:
                        # Update existing driver
                        for key, value in driver_data.items():
                            # For complex data types, preserve existing data
                            if key in ('events', 'activities', 'locations') and key in existing_drivers[driver_name]:
                                if isinstance(value, list):
                                    existing_drivers[driver_name][key].extend(value)
                                elif isinstance(value, set):
                                    existing_drivers[driver_name][key].update(value)
                            else:
                                # For simple types, only overwrite if not already set
                                if key not in existing_drivers[driver_name] or not existing_drivers[driver_name][key]:
                                    existing_drivers[driver_name][key] = value
                        
                        # Update sources
                        if 'sources' not in existing_drivers[driver_name]:
                            existing_drivers[driver_name]['sources'] = []
                        if source not in existing_drivers[driver_name]['sources']:
                            existing_drivers[driver_name]['sources'].append(source)
                    else:
                        # Add new driver
                        driver_data['sources'] = [source]
                        driver_data['date'] = self.date_str
                        existing_drivers[driver_name] = driver_data
                
                # Convert back to list
                driver_list = list(existing_drivers.values())
            except Exception as e:
                logger.error(f"Error merging driver data: {e}")
                
                # If error, create new list
                driver_list = []
                for driver_name, driver_data in new_drivers.items():
                    driver_data['sources'] = [source]
                    driver_data['date'] = self.date_str
                    driver_list.append(driver_data)
        else:
            # Create new list
            driver_list = []
            for driver_name, driver_data in new_drivers.items():
                driver_data['sources'] = [source]
                driver_data['date'] = self.date_str
                driver_list.append(driver_data)
        
        # Save updated driver list
        with open(driver_file, 'w') as f:
            json.dump(driver_list, f, indent=2, default=str)
        
        logger.info(f"Merged {len(new_drivers)} drivers from {source}, total drivers: {len(driver_list)}")
    
    def generate_attendance_report(self):
        """
        Generate attendance report for the processed data
        
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Generating attendance report for {self.date_str}")
            
            # Load processed driver data
            driver_file = self.output_dir / f"drivers_{self.date_str}.json"
            
            if not os.path.exists(driver_file):
                logger.error(f"No driver data found for {self.date_str}")
                log_error(self.date_str, "No driver data found", "generate_attendance_report")
                return False
            
            with open(driver_file, 'r') as f:
                drivers = json.load(f)
            
            # Create attendance report structure
            attendance_data = {
                'date': self.date_str,
                'total_drivers': len(drivers),
                'late_start_records': [],
                'early_end_records': [],
                'not_on_job_records': [],
                'drivers': drivers
            }
            
            # Standard work hours
            work_start = datetime.strptime(f"{self.date_str} 07:00:00", '%Y-%m-%d %H:%M:%S')
            work_end = datetime.strptime(f"{self.date_str} 17:00:00", '%Y-%m-%d %H:%M:%S')
            
            # Process each driver
            for driver in drivers:
                # Check for late start
                if 'first_activity' in driver and driver['first_activity']:
                    first_activity = pd.to_datetime(driver['first_activity'])
                    
                    if first_activity > work_start:
                        # Calculate late minutes
                        late_minutes = int((first_activity - work_start).total_seconds() / 60)
                        
                        if late_minutes > 10:  # Only count if more than 10 minutes late
                            # Add late record
                            late_record = {
                                'driver_name': driver['name'],
                                'job_site': driver.get('locations', ['Unknown'])[0] if driver.get('locations') else 'Unknown',
                                'scheduled_start': '07:00',
                                'actual_start': first_activity.strftime('%H:%M'),
                                'late_minutes': late_minutes,
                                'asset_id': driver.get('asset_id', '')
                            }
                            attendance_data['late_start_records'].append(late_record)
                
                # Check for early end
                if 'last_activity' in driver and driver['last_activity'] and 'first_activity' in driver and driver['first_activity']:
                    first_activity = pd.to_datetime(driver['first_activity'])
                    last_activity = pd.to_datetime(driver['last_activity'])
                    
                    # Calculate work duration
                    work_duration = int((last_activity - first_activity).total_seconds() / 60)
                    
                    # Check if they worked at least 2 hours (120 minutes) and ended before standard end time
                    if work_duration >= 120 and last_activity < work_end:
                        # Calculate early minutes
                        early_minutes = int((work_end - last_activity).total_seconds() / 60)
                        
                        if early_minutes > 10:  # Only count if more than 10 minutes early
                            # Add early record
                            early_record = {
                                'driver_name': driver['name'],
                                'job_site': driver.get('locations', ['Unknown'])[0] if driver.get('locations') else 'Unknown',
                                'scheduled_end': '17:00',
                                'actual_end': last_activity.strftime('%H:%M'),
                                'early_minutes': early_minutes,
                                'asset_id': driver.get('asset_id', '')
                            }
                            attendance_data['early_end_records'].append(early_record)
            
            # Sort records
            attendance_data['late_start_records'] = sorted(
                attendance_data['late_start_records'],
                key=lambda x: x.get('late_minutes', 0),
                reverse=True
            )
            
            attendance_data['early_end_records'] = sorted(
                attendance_data['early_end_records'],
                key=lambda x: x.get('early_minutes', 0),
                reverse=True
            )
            
            # Add stat counts
            attendance_data['late_count'] = len(attendance_data['late_start_records'])
            attendance_data['early_count'] = len(attendance_data['early_end_records'])
            attendance_data['missing_count'] = len(attendance_data['not_on_job_records'])
            
            # Calculate on-time percentage
            on_time = attendance_data['total_drivers'] - attendance_data['late_count'] - attendance_data['missing_count']
            attendance_data['on_time_percent'] = round(100 * on_time / max(1, attendance_data['total_drivers']), 1)
            
            # Save attendance report
            reports_dir = Path('exports/daily_reports')
            reports_dir.mkdir(exist_ok=True, parents=True)
            
            report_file = reports_dir / f"attendance_data_{self.date_str}.json"
            with open(report_file, 'w') as f:
                json.dump(attendance_data, f, indent=2, default=str)
            
            logger.info(f"Saved attendance report to {report_file}")
            
            # Update stats
            update_stats(self.date_str, {
                'total_drivers': attendance_data['total_drivers'],
                'late_drivers': attendance_data['late_count'],
                'early_end_drivers': attendance_data['early_count'],
                'missing_drivers': attendance_data['missing_count'],
                'on_time_percent': attendance_data['on_time_percent']
            })
            
            # Mark audit as complete
            complete_audit(self.date_str, success=True)
            
            return True
        
        except Exception as e:
            logger.error(f"Error generating attendance report: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Log error in audit record
            log_error(self.date_str, str(e), "generate_attendance_report")
            
            return False
            
    def export_excel_report(self):
        """
        Export attendance report to Excel
        
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Exporting Excel report for {self.date_str}")
            
            # Load attendance data
            reports_dir = Path('exports/daily_reports')
            report_file = reports_dir / f"attendance_data_{self.date_str}.json"
            
            if not os.path.exists(report_file):
                logger.error(f"No attendance report found at {report_file}")
                return False
            
            with open(report_file, 'r') as f:
                attendance_data = json.load(f)
            
            # Create Excel report
            report_path = reports_dir / f"daily_report_{self.date_str}.xlsx"
            standard_path = reports_dir / f"{self.date_str}_DailyDriverReport.xlsx"
            
            # Create DataFrames for each section
            drivers_df = pd.DataFrame(attendance_data['drivers'])
            late_df = pd.DataFrame(attendance_data['late_start_records']) if attendance_data['late_start_records'] else pd.DataFrame()
            early_df = pd.DataFrame(attendance_data['early_end_records']) if attendance_data['early_end_records'] else pd.DataFrame()
            
            # Add summary sheet data
            summary_data = {
                'Metric': [
                    'Date', 'Total Drivers', 'On-Time Drivers', 'Late Drivers',
                    'Early End Drivers', 'Not on Job Drivers', 'On-Time Percentage'
                ],
                'Value': [
                    self.date_str,
                    attendance_data['total_drivers'],
                    attendance_data['total_drivers'] - attendance_data['late_count'] - attendance_data['missing_count'],
                    attendance_data['late_count'],
                    attendance_data['early_count'],
                    attendance_data['missing_count'],
                    f"{attendance_data['on_time_percent']}%"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            
            # Write to Excel
            with pd.ExcelWriter(report_path) as writer:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                drivers_df.to_excel(writer, sheet_name='All Drivers', index=False)
                late_df.to_excel(writer, sheet_name='Late Drivers', index=False)
                early_df.to_excel(writer, sheet_name='Early End', index=False)
            
            # Copy to standardized name
            import shutil
            shutil.copy2(report_path, standard_path)
            
            logger.info(f"Exported Excel report to {report_path} and {standard_path}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error exporting Excel report: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return False
    
    def export_pdf_report(self):
        """
        Export attendance report to PDF
        
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Exporting PDF report for {self.date_str}")
            
            # Load attendance data
            reports_dir = Path('exports/daily_reports')
            report_file = reports_dir / f"attendance_data_{self.date_str}.json"
            
            if not os.path.exists(report_file):
                logger.error(f"No attendance report found at {report_file}")
                return False
            
            with open(report_file, 'r') as f:
                attendance_data = json.load(f)
            
            # Create PDF report
            from fpdf import FPDF
            
            report_path = reports_dir / f"daily_report_{self.date_str}.pdf"
            standard_path = reports_dir / f"{self.date_str}_DailyDriverReport.pdf"
            
            # Create PDF
            pdf = FPDF()
            pdf.add_page()
            
            # Set up fonts
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, f'Daily Driver Report: {self.date_str}', 0, 1, 'C')
            pdf.ln(5)
            
            # Summary section
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f"Total Drivers: {attendance_data['total_drivers']}", 0, 1)
            pdf.cell(0, 10, f"Late Drivers: {attendance_data['late_count']}", 0, 1)
            pdf.cell(0, 10, f"Early End Drivers: {attendance_data['early_count']}", 0, 1)
            pdf.cell(0, 10, f"Not on Job Drivers: {attendance_data['missing_count']}", 0, 1)
            pdf.cell(0, 10, f"On-Time Percentage: {attendance_data['on_time_percent']}%", 0, 1)
            pdf.ln(5)
            
            # Late drivers section
            if attendance_data['late_start_records']:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Late Drivers', 0, 1)
                
                # Column headers
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(60, 7, 'Driver Name', 1)
                pdf.cell(30, 7, 'Late (min)', 1)
                pdf.cell(25, 7, 'Actual Start', 1)
                pdf.cell(75, 7, 'Job Site', 1)
                pdf.ln()
                
                # Late driver rows
                pdf.set_font('Arial', '', 10)
                for late in attendance_data['late_start_records'][:15]:  # Show first 15
                    pdf.cell(60, 7, late['driver_name'][:28], 1)
                    pdf.cell(30, 7, str(late['late_minutes']), 1)
                    pdf.cell(25, 7, late['actual_start'], 1)
                    pdf.cell(75, 7, (late['job_site'] or 'Unknown')[:35], 1)
                    pdf.ln()
                
                pdf.ln(5)
            
            # Early end drivers section
            if attendance_data['early_end_records']:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Early End Drivers', 0, 1)
                
                # Column headers
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(60, 7, 'Driver Name', 1)
                pdf.cell(30, 7, 'Early (min)', 1)
                pdf.cell(25, 7, 'Actual End', 1)
                pdf.cell(75, 7, 'Job Site', 1)
                pdf.ln()
                
                # Early end driver rows
                pdf.set_font('Arial', '', 10)
                for early in attendance_data['early_end_records'][:15]:  # Show first 15
                    pdf.cell(60, 7, early['driver_name'][:28], 1)
                    pdf.cell(30, 7, str(early['early_minutes']), 1)
                    pdf.cell(25, 7, early['actual_end'], 1)
                    pdf.cell(75, 7, (early['job_site'] or 'Unknown')[:35], 1)
                    pdf.ln()
            
            # Output PDF
            pdf.output(report_path)
            
            # Copy to standardized name
            import shutil
            shutil.copy2(report_path, standard_path)
            
            logger.info(f"Exported PDF report to {report_path} and {standard_path}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error exporting PDF report: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return False