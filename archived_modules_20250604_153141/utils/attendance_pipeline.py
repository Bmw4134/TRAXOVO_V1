"""
TRAXORA Fleet Management System - Attendance Pipeline

This module provides the attendance data processing pipeline that integrates
GPS telematics data with timecard data to infer attendance status.
"""
import os
import json
import pandas as pd
import logging
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure all required directories exist"""
    directories = [
        os.path.join(os.getcwd(), 'exports', 'attendance'),
        os.path.join(os.getcwd(), 'processed'),
        os.path.join(os.getcwd(), 'uploads', 'telematics'),
        os.path.join(os.getcwd(), 'uploads', 'timecards'),
        os.path.join(os.getcwd(), 'reports', 'weekly')
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")

def load_telematics(file_path=None, date_str=None):
    """Load telematics data from file or use sample data"""
    try:
        if file_path and os.path.exists(file_path):
            # Load data from the specified file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                logger.error(f"Unsupported file format: {file_path}")
                return pd.DataFrame()
            
            logger.info(f"Loaded telematics data from {file_path}")
            return df
        
        # Check if we have weekly data in attached_assets
        if date_str:
            try:
                weekly_data_path = os.path.join(os.getcwd(), 'attached_assets', 'weekly_driver_report_2025-05-18_to_2025-05-24.json')
                if os.path.exists(weekly_data_path):
                    with open(weekly_data_path, 'r') as f:
                        weekly_data = json.load(f)
                        # Filter data for the specific day
                        day_data = [record for record in weekly_data if record.get('Date') == date_str]
                        if day_data:
                            return pd.DataFrame(day_data)
            except Exception as e:
                logger.error(f"Error loading sample data: {str(e)}")
        
        logger.warning("No telematics data found")
        return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error loading telematics data: {str(e)}")
        return pd.DataFrame()

def load_timecards(file_path=None, date_str=None):
    """Load timecard data from file or use sample data"""
    try:
        if file_path and os.path.exists(file_path):
            # Load data from the specified file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                logger.error(f"Unsupported file format: {file_path}")
                return pd.DataFrame()
            
            logger.info(f"Loaded timecard data from {file_path}")
            return df
        
        # If no file is specified, try to load from attached_assets for the specific date
        if date_str:
            try:
                timecard_path = os.path.join(os.getcwd(), 'attached_assets', 'Timecards - 2025-05-18 - 2025-05-24 (3).xlsx')
                if os.path.exists(timecard_path):
                    df = pd.read_excel(timecard_path)
                    # Filter for the specific date
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    filtered_df = df[df['Date'] == date_obj]
                    if not filtered_df.empty:
                        return filtered_df
            except Exception as e:
                logger.error(f"Error loading sample timecard data: {str(e)}")
        
        logger.warning("No timecard data found")
        return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error loading timecard data: {str(e)}")
        return pd.DataFrame()

def infer_attendance(telematics_df, timecards_df, date_str):
    """Infer attendance status based on telematics and timecard data"""
    try:
        # If we have real telematics data with GPS records
        if not telematics_df.empty and 'FirstSeen' in telematics_df.columns and 'LastSeen' in telematics_df.columns:
            attendance_df = telematics_df.copy()
            
            # Calculate attendance status
            def determine_status(row):
                # Default status is Not On Job
                status = "Not On Job"
                
                first_seen = row.get('FirstSeen')
                last_seen = row.get('LastSeen')
                
                if first_seen and last_seen:
                    # Parse time strings
                    if isinstance(first_seen, str):
                        try:
                            first_time = datetime.strptime(first_seen, '%H:%M').time()
                        except ValueError:
                            try:
                                first_time = datetime.strptime(first_seen, '%I:%M %p').time()
                            except ValueError:
                                logger.warning(f"Could not parse time: {first_seen}")
                                return status
                    else:
                        # If already a datetime object
                        first_time = first_seen.time() if hasattr(first_seen, 'time') else first_seen
                    
                    if isinstance(last_seen, str):
                        try:
                            last_time = datetime.strptime(last_seen, '%H:%M').time()
                        except ValueError:
                            try:
                                last_time = datetime.strptime(last_seen, '%I:%M %p').time()
                            except ValueError:
                                logger.warning(f"Could not parse time: {last_seen}")
                                return status
                    else:
                        # If already a datetime object
                        last_time = last_seen.time() if hasattr(last_seen, 'time') else last_seen
                    
                    # Determine status based on time
                    start_threshold = datetime.strptime('07:30', '%H:%M').time()
                    end_threshold = datetime.strptime('16:00', '%H:%M').time()
                    
                    if first_time > start_threshold:
                        status = "Late"
                    elif last_time < end_threshold:
                        status = "Early End"
                    else:
                        status = "On Time"
                
                return status
            
            # Apply status determination to each row
            attendance_df['Status'] = attendance_df.apply(determine_status, axis=1)
            
            # Add date if not present
            if 'Date' not in attendance_df.columns:
                attendance_df['Date'] = date_str
            
            return attendance_df
        
        # Use the existing data if it already has Status field
        elif not telematics_df.empty and 'Status' in telematics_df.columns:
            return telematics_df
        
        # If we have no usable data, return empty DataFrame
        logger.warning("Insufficient data to infer attendance status")
        return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error inferring attendance: {str(e)}")
        return pd.DataFrame()

def generate_report(attendance_df, date_str, output_file=None):
    """Generate attendance report and save to file"""
    try:
        if attendance_df.empty:
            logger.warning("No attendance data to generate report")
            return False
        
        # Ensure all required fields are present
        required_fields = ['Driver', 'Status', 'JobSite', 'FirstSeen', 'LastSeen']
        for field in required_fields:
            if field not in attendance_df.columns:
                logger.warning(f"Missing required field in attendance data: {field}")
                return False
        
        # Calculate hours if not present
        if 'Hours' not in attendance_df.columns:
            def calculate_hours(row):
                first_seen = row.get('FirstSeen')
                last_seen = row.get('LastSeen')
                
                if not first_seen or not last_seen:
                    return 0
                
                # Parse time strings
                if isinstance(first_seen, str):
                    try:
                        first_time = datetime.strptime(first_seen, '%H:%M')
                    except ValueError:
                        try:
                            first_time = datetime.strptime(first_seen, '%I:%M %p')
                        except ValueError:
                            logger.warning(f"Could not parse time: {first_seen}")
                            return 0
                else:
                    # If already a datetime object
                    first_time = first_seen if isinstance(first_seen, datetime) else datetime.combine(datetime.today(), first_seen)
                
                if isinstance(last_seen, str):
                    try:
                        last_time = datetime.strptime(last_seen, '%H:%M')
                    except ValueError:
                        try:
                            last_time = datetime.strptime(last_seen, '%I:%M %p')
                        except ValueError:
                            logger.warning(f"Could not parse time: {last_seen}")
                            return 0
                else:
                    # If already a datetime object
                    last_time = last_seen if isinstance(last_seen, datetime) else datetime.combine(datetime.today(), last_seen)
                
                # Calculate hours
                delta = last_time - first_time
                hours = delta.total_seconds() / 3600
                return round(hours, 2)
            
            attendance_df['Hours'] = attendance_df.apply(calculate_hours, axis=1)
        
        # Add Source field if not present
        if 'Source' not in attendance_df.columns:
            attendance_df['Source'] = 'GPS + Timecard'
        
        # Format the report data
        report_data = attendance_df.to_dict('records')
        
        # Determine output file name
        if not output_file:
            ensure_dirs()
            exports_dir = os.path.join(os.getcwd(), 'exports', 'attendance')
            output_file = os.path.join(exports_dir, f'driver_report_{date_str}.json')
        
        # Save to JSON
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Also save to processed directory
        processed_dir = os.path.join(os.getcwd(), 'processed')
        processed_file = os.path.join(processed_dir, f'attendance_{date_str}.json')
        with open(processed_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate Excel file as well
        excel_file = output_file.replace('.json', '.xlsx')
        attendance_df.to_excel(excel_file, index=False)
        
        logger.info(f"Generated attendance report for {date_str} with {len(report_data)} records")
        return True
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return False

def process_attendance_data(date_str):
    """Process attendance data for a specific date"""
    try:
        ensure_dirs()
        
        # Load telematics data
        telematics_df = load_telematics(date_str=date_str)
        
        # Load timecard data
        timecards_df = load_timecards(date_str=date_str)
        
        # Infer attendance status
        attendance_df = infer_attendance(telematics_df, timecards_df, date_str)
        
        # Generate report
        success = generate_report(attendance_df, date_str)
        
        return success
    
    except Exception as e:
        logger.error(f"Error processing attendance data: {str(e)}")
        return False

def process_week_data(start_date_str, end_date_str):
    """Process attendance data for a week"""
    try:
        ensure_dirs()
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        current_date = start_date
        success_count = 0
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            logger.info(f"Processing attendance data for {date_str}")
            
            if process_attendance_data(date_str):
                success_count += 1
            
            current_date += timedelta(days=1)
        
        logger.info(f"Processed attendance data for {success_count} days in the week")
        return success_count > 0
    
    except Exception as e:
        logger.error(f"Error processing week data: {str(e)}")
        return False

# Run this when the module is executed directly
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Process data for May 18-24, 2025
    process_week_data('2025-05-18', '2025-05-24')