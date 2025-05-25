"""
TRAXORA Fleet Management System - Process Filtered Data

This utility script processes the filtered driving data JSON files
and generates attendance reports using the simplified attendance pipeline.
This is optimized for the specific TRAXORA data structure.
"""

import os
import json
import logging
import sys
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.attendance_pipeline_slim import process_attendance_data_v2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define constants
DATA_DIR = "data"
REPORTS_DIR = "reports"
LATE_START_TIME = "07:30:00"  # After this time is considered late
EARLY_END_TIME = "16:00:00"   # Before this time is considered early end

def format_time(time_str):
    """Format time string to AM/PM format for Excel report"""
    if not time_str:
        return ""
    try:
        # Parse time if in HH:MM:SS format
        if ":" in time_str:
            hours, minutes, seconds = map(int, time_str.split(':'))
            return f"{hours:02d}:{minutes:02d} {'AM' if hours < 12 else 'PM'}"
        return time_str
    except Exception:
        return time_str

def generate_excel_report(report_data, date_str):
    """Generate Excel report in the same format as the original workbook"""
    try:
        # Format date for report header
        formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%m.%d.%Y')
        
        # Create dataframe for Excel report
        data = []
        
        for record in report_data.get('driver_records', []):
            row = {
                'DRIVER': record.get('driver_name', ''),
                'JOB NO.': record.get('job_number', ''),
                'JOB NAME': record.get('job_name', ''),
                'STATUS': record.get('classification', '').replace('_', ' ').upper(),
                'START TIME': format_time(record.get('start_time', '')),
                'END TIME': format_time(record.get('end_time', '')),
                'HOURS ON SITE': record.get('hours', 0),
                'LATE (MIN)': record.get('late_minutes', '') if record.get('late_minutes', 0) > 0 else '',
                'EARLY END (MIN)': record.get('early_end_minutes', '') if record.get('early_end_minutes', 0) > 0 else '',
                'GPS VERIFIED': 'YES' if record.get('gps_verified', False) else 'NO',
                'NOTES': '',
                'CONTACT': record.get('contact', ''),
                'PHONE': record.get('phone', ''),
                'EMAIL': record.get('email', '')
            }
            data.append(row)
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Save Excel file with proper formatting
        os.makedirs(os.path.join(REPORTS_DIR, 'excel'), exist_ok=True)
        excel_file = os.path.join(REPORTS_DIR, 'excel', f"DAILY_DRIVER_REPORT_{date_str.replace('-', '_')}.xlsx")
        
        # Create Excel writer
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Sheet name
            sheet_name = f"DAILY REPORT {formatted_date}"
            
            # Create DataFrame with header row
            header_df = pd.DataFrame([
                {0: f"DAILY LATE START-EARLY END & NOJ REPORT_{date_str.replace('-', '_')}"},
                {0: ""},
            ])
            
            # Write header
            header_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
            
            # Write data starting at row 3
            df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)
            
        logger.info(f"Excel report generated: {excel_file}")
        return excel_file
    except Exception as e:
        logger.error(f"Error generating Excel report: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def process_filtered_data(date_str):
    """Process filtered data for a specific date
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        tuple: (json_path, excel_path) paths to the generated report files, or (None, None) if failed
    """
    try:
        # Find filtered data file
        filtered_file = os.path.join(DATA_DIR, f"filtered_driving_data_{date_str}.json")
        
        if not os.path.exists(filtered_file):
            logger.error(f"Filtered data file not found for {date_str}")
            return None, None
            
        # Load filtered data
        with open(filtered_file, 'r') as f:
            filtered_data = json.load(f)
            
        # Convert to expected format for attendance pipeline
        driving_history_data = []
        
        # Check if driver data file exists (for contact information)
        driver_data = {}
        driver_data_file = os.path.join(DATA_DIR, 'driver_contact_data.json')
        if os.path.exists(driver_data_file):
            try:
                with open(driver_data_file, 'r') as f:
                    driver_data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load driver contact data: {e}")
        
        for record in filtered_data:
            driver_name = record.get('Driver', '').strip()
            # Try to get contact info from driver data
            contact_info = driver_data.get(driver_name.lower(), {})
            
            # Use exact field names from TRAXORA data structure
            driving_record = {
                'driver_name': driver_name,
                'date': record.get('Date', date_str),
                'first_start': record.get('FirstSeen'),
                'last_end': record.get('LastSeen'),
                'job_site': record.get('JobSite', 'Unknown'),
                'employee_id': record.get('EmployeeID'),
                'status': record.get('Status'),
                'hours': record.get('Hours', 0),
                'source': record.get('Source', 'gps'),
                'event_datetime': record.get('EventDateTime'),
                'location': record.get('Location'),
                'contact': contact_info.get('contact', record.get('Contact', '')),
                'phone': contact_info.get('phone', record.get('Phone', '')),
                'email': contact_info.get('email', record.get('Email', ''))
            }
            driving_history_data.append(driving_record)
            
        # Get adaptive classification thresholds from iterative learning system
        try:
            from utils.iterative_learning import get_classification_thresholds, update_driver_patterns
            
            # Process attendance data with adaptive classification rules
            report = process_attendance_data_v2(
                driving_history_data=driving_history_data,
                date_str=date_str,
                late_start_time=get_classification_thresholds().get('late_start_time', LATE_START_TIME),
                early_end_time=get_classification_thresholds().get('early_end_time', EARLY_END_TIME)
            )
            
            # Update driver patterns after processing (this feeds the learning loop)
            update_driver_patterns()
        except ImportError:
            # Fallback to standard classification if iterative learning not available
            logger.warning("Iterative learning system not available, using default thresholds")
            report = process_attendance_data_v2(
                driving_history_data=driving_history_data,
                date_str=date_str,
                late_start_time=LATE_START_TIME,
                early_end_time=EARLY_END_TIME
            )
        
        # Save JSON report
        os.makedirs(REPORTS_DIR, exist_ok=True)
        json_report_file = os.path.join(REPORTS_DIR, f"attendance_report_{date_str}.json")
        with open(json_report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        logger.info(f"JSON attendance report saved to {json_report_file}")
        
        # Generate Excel report
        excel_report_file = generate_excel_report(report, date_str)
        
        # Create report folder structure for daily driver reports
        os.makedirs(os.path.join(REPORTS_DIR, 'daily_driver_reports'), exist_ok=True)
        
        # Copy Excel file to daily driver reports folder
        if excel_report_file:
            excel_report_dest = os.path.join(
                REPORTS_DIR, 
                'daily_driver_reports', 
                f"DAILY_DRIVER_REPORT_{date_str.replace('-', '_')}.xlsx"
            )
            
            # Copy the Excel file
            import shutil
            shutil.copy2(excel_report_file, excel_report_dest)
            
            # Also save JSON format in daily_driver_reports
            json_report_dest = os.path.join(
                REPORTS_DIR, 
                'daily_driver_reports', 
                f"driver_report_{date_str}.json"
            )
            with open(json_report_dest, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Reports also saved to daily_driver_reports folder")
        
        return json_report_file, excel_report_file
    
    except Exception as e:
        logger.error(f"Error processing filtered data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None

if __name__ == "__main__":
    import argparse
    from datetime import timedelta
    
    parser = argparse.ArgumentParser(description="Process filtered driving data")
    parser.add_argument('--date', help='Date to process (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if args.date:
        process_filtered_data(args.date)
    else:
        # Process yesterday's data by default
        yesterday = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
        process_filtered_data(yesterday)