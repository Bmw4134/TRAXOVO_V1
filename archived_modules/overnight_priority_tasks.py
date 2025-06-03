#!/usr/bin/env python3
"""
Overnight Priority Tasks

This script executes all critical overnight priorities:
1. Finalize Daily Driver Report for 2025-05-19
2. Prepare the 2025-05-20 pipeline
3. Export full April Billing
4. Log unmapped entities

EXECUTION INSTRUCTIONS:
Run this script directly:
python overnight_priority_tasks.py
"""

import os
import sys
import logging
import traceback
import pandas as pd
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'overnight_priority_tasks.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure critical directories exist
os.makedirs('exports/daily_reports', exist_ok=True)
os.makedirs('exports/billing', exist_ok=True)
os.makedirs('logs/unmapped_entities', exist_ok=True)

def finalize_daily_report(date_str='2025-05-19'):
    """
    Finalize Daily Driver Report for the specified date
    """
    logger.info(f"TASK 1: Finalizing Daily Driver Report for {date_str}")
    
    try:
        # Import needed modules
        from utils.attendance_pipeline_connector import get_attendance_data
        
        # Get attendance data with force refresh to ensure latest
        logger.info(f"Retrieving attendance data for {date_str}")
        attendance_data = get_attendance_data(date_str, force_refresh=True)
        
        if not attendance_data:
            logger.error(f"Failed to retrieve attendance data for {date_str}")
            return False
        
        logger.info(f"Successfully retrieved attendance data for {date_str}")
        logger.info(f"Total drivers: {attendance_data.get('total_drivers', 0)}")
        logger.info(f"Late drivers: {attendance_data.get('late_count', 0)}")
        logger.info(f"Early departure drivers: {attendance_data.get('early_count', 0)}")
        logger.info(f"Not on job drivers: {attendance_data.get('missing_count', 0)}")
        
        # Load employee and job data for enrichment
        employee_file = 'attached_assets/Consolidated_Employee_And_Job_Lists_Corrected.xlsx'
        
        if not os.path.exists(employee_file):
            logger.error(f"Employee file not found: {employee_file}")
            return False
        
        logger.info(f"Loading employee and job data from: {employee_file}")
        try:
            employee_data = pd.read_excel(employee_file, sheet_name='Employee_Contacts')
            job_data = pd.read_excel(employee_file, sheet_name='Job_Lists')
            logger.info(f"Loaded {len(employee_data)} employee records and {len(job_data)} job records")
        except Exception as e:
            logger.error(f"Error loading employee/job data: {e}")
            return False
        
        # Process the report using rebuild_attendance_data.py
        logger.info("Rebuilding attendance data to generate reports")
        
        # Create a backup of argv
        original_argv = sys.argv.copy()
        
        try:
            from rebuild_attendance_data import main as rebuild_attendance
            # Set command line arguments
            sys.argv = ['rebuild_attendance_data.py', date_str]
            # Run rebuild
            rebuild_attendance()
            # Restore original argv
            sys.argv = original_argv
            
            logger.info(f"Successfully rebuilt attendance data for {date_str}")
        except Exception as e:
            logger.error(f"Error rebuilding attendance data: {e}")
            traceback.print_exc()
            # Restore original argv
            sys.argv = original_argv
            return False
        
        # Verify outputs exist and rename if needed
        source_xlsx = f'exports/daily_reports/daily_report_{date_str}.xlsx'
        source_pdf = f'exports/daily_reports/daily_report_{date_str}.pdf'
        
        target_xlsx = f'exports/daily_reports/{date_str}_DailyDriverReport.xlsx'
        target_pdf = f'exports/daily_reports/{date_str}_DailyDriverReport.pdf'
        
        if os.path.exists(source_xlsx):
            logger.info(f"Excel report exists: {source_xlsx} ({os.path.getsize(source_xlsx)} bytes)")
            # Copy to the required filename format
            shutil.copy2(source_xlsx, target_xlsx)
            logger.info(f"Copied to required format: {target_xlsx}")
        else:
            logger.error(f"Excel report not found: {source_xlsx}")
            return False
        
        if os.path.exists(source_pdf):
            logger.info(f"PDF report exists: {source_pdf} ({os.path.getsize(source_pdf)} bytes)")
            # Copy to the required filename format
            shutil.copy2(source_pdf, target_pdf)
            logger.info(f"Copied to required format: {target_pdf}")
        else:
            logger.warning(f"PDF report not found: {source_pdf}")
            logger.info("Attempting to create PDF report directly")
            
            try:
                # Import PDF export module
                from utils.pdf_export import export_daily_report_to_pdf
                
                # Create PDF directly
                export_daily_report_to_pdf(attendance_data, target_pdf)
                
                if os.path.exists(target_pdf):
                    logger.info(f"Successfully created PDF report: {target_pdf} ({os.path.getsize(target_pdf)} bytes)")
                else:
                    logger.error(f"Failed to create PDF report: {target_pdf}")
            except Exception as e:
                logger.error(f"Error creating PDF directly: {e}")
                traceback.print_exc()
        
        logger.info("Task 1 completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error in Task 1: {e}")
        traceback.print_exc()
        return False

def prepare_tomorrow_pipeline():
    """
    Prepare pipeline for tomorrow (2025-05-20)
    """
    logger.info("TASK 2: Preparing pipeline for 2025-05-20")
    
    try:
        # Create scheduled task script
        scheduler_script = 'auto_daily_report.py'
        
        with open(scheduler_script, 'w') as f:
            f.write('''#!/usr/bin/env python3
"""
Auto Daily Report

This script automatically processes the Daily Driver Report for the current day.
It checks for input files and processes the report when all required files are available.
If files are not available by 7 PM, it will process with whatever data is available.
"""

import os
import sys
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'auto_daily_report.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_input_files(date_str=None):
    """
    Check if input files are available for the specified date
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"Checking input files for {date_str}")
    
    # Check for required files
    activity_files = [f for f in os.listdir('attached_assets') if f.startswith('ActivityDetail')]
    driving_files = [f for f in os.listdir('attached_assets') if f.startswith('DrivingHistory')]
    asset_files = [f for f in os.listdir('attached_assets') if f.startswith('AssetsTimeOnSite') or f.startswith('FleetUtilization')]
    timecard_files = [f for f in os.listdir('attached_assets') if f.startswith('Timecards')]
    
    logger.info(f"Found {len(activity_files)} activity files")
    logger.info(f"Found {len(driving_files)} driving history files")
    logger.info(f"Found {len(asset_files)} asset/fleet files")
    logger.info(f"Found {len(timecard_files)} timecard files")
    
    # Check if all required files are available
    if len(activity_files) > 0 and len(driving_files) > 0:
        logger.info("All critical files are available")
        return True
    else:
        logger.warning("Not all critical files are available")
        if len(activity_files) == 0:
            logger.warning("Missing activity files")
        if len(driving_files) == 0:
            logger.warning("Missing driving history files")
        return False

def process_report(date_str=None, force=False):
    """
    Process the Daily Driver Report for the specified date
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    logger.info(f"Processing Daily Driver Report for {date_str}")
    
    # Check if files are available
    files_ready = check_input_files(date_str)
    
    if not files_ready and not force:
        logger.warning(f"Cannot process report for {date_str} - required files not available")
        return False
    
    try:
        # Run the rebuild script
        from rebuild_attendance_data import main as rebuild_attendance
        
        # Save original argv
        original_argv = sys.argv.copy()
        
        # Set new argv
        sys.argv = ['rebuild_attendance_data.py', date_str]
        
        # Run rebuild
        rebuild_attendance()
        
        # Restore original argv
        sys.argv = original_argv
        
        logger.info(f"Successfully processed report for {date_str}")
        
        # Verify outputs
        source_xlsx = f'exports/daily_reports/daily_report_{date_str}.xlsx'
        source_pdf = f'exports/daily_reports/daily_report_{date_str}.pdf'
        
        target_xlsx = f'exports/daily_reports/{date_str}_DailyDriverReport.xlsx'
        target_pdf = f'exports/daily_reports/{date_str}_DailyDriverReport.pdf'
        
        # Copy files to required format if they exist
        if os.path.exists(source_xlsx):
            import shutil
            shutil.copy2(source_xlsx, target_xlsx)
            logger.info(f"Copied Excel report to {target_xlsx}")
        else:
            logger.error(f"Excel report not found: {source_xlsx}")
        
        if os.path.exists(source_pdf):
            import shutil
            shutil.copy2(source_pdf, target_pdf)
            logger.info(f"Copied PDF report to {target_pdf}")
        else:
            logger.warning(f"PDF report not found: {source_pdf}")
            
            # Try to create PDF directly
            try:
                from utils.attendance_pipeline_connector import get_attendance_data
                from utils.pdf_export import export_daily_report_to_pdf
                
                attendance_data = get_attendance_data(date_str, force_refresh=False)
                if attendance_data:
                    export_daily_report_to_pdf(attendance_data, target_pdf)
                    logger.info(f"Created PDF report directly: {target_pdf}")
                else:
                    logger.error(f"No attendance data available for {date_str}")
            except Exception as e:
                logger.error(f"Error creating PDF directly: {e}")
                traceback.print_exc()
        
        logger.info(f"Report processing complete for {date_str}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing report: {e}")
        traceback.print_exc()
        return False

def main():
    """
    Main function
    """
    logger.info("Starting Auto Daily Report")
    
    # Set target date
    target_date = '2025-05-20'
    
    # Check for arguments
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    
    logger.info(f"Target date: {target_date}")
    
    # Get current time
    current_time = datetime.now()
    current_hour = current_time.hour
    
    logger.info(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Current hour: {current_hour}")
    
    # Check file availability
    file_check_result = check_input_files(target_date)
    
    # Process based on time and file availability
    if current_hour >= 19 or file_check_result:
        # Either it's past 7 PM or all files are available
        force_mode = current_hour >= 19
        logger.info(f"Processing report with force={force_mode}")
        process_report(target_date, force=force_mode)
    else:
        logger.info("Files not available and it's before 7 PM, not processing report yet")
        logger.info("Will check again at 7 PM")
    
    logger.info("Auto Daily Report completed")

if __name__ == "__main__":
    main()
''')
        
        logger.info(f"Created auto daily report script: {scheduler_script}")
        
        # Create cron-like entry in scheduled_tasks.py
        scheduled_tasks_script = 'scheduled_tasks.py'
        
        with open(scheduled_tasks_script, 'w') as f:
            f.write('''#!/usr/bin/env python3
"""
Scheduled Tasks for TRAXORA

This script runs scheduled tasks for the TRAXORA system.
It checks for input files hourly and processes the daily report at 7 PM.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'scheduled_tasks.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_auto_daily_report():
    """
    Run the auto daily report script
    """
    logger.info("Running auto daily report script")
    
    try:
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Run the script
        os.system(f"python auto_daily_report.py {today}")
        
        logger.info("Auto daily report script completed")
    except Exception as e:
        logger.error(f"Error running auto daily report script: {e}")
        import traceback
        logger.error(traceback.format_exc())

def check_hourly():
    """
    Check for input files hourly
    """
    logger.info("Running hourly check for input files")
    
    try:
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Check current hour
        current_hour = datetime.now().hour
        
        # Import the check function directly
        from auto_daily_report import check_input_files
        
        # Check for files
        files_available = check_input_files(today)
        
        logger.info(f"Files available: {files_available}")
        
        # If files are available, process the report
        if files_available:
            logger.info("All required files are available, processing report")
            from auto_daily_report import process_report
            process_report(today)
        else:
            logger.info("Not all required files are available")
            
            # If it's 7 PM or later, process anyway
            if current_hour >= 19:
                logger.info("It's 7 PM or later, processing report anyway")
                from auto_daily_report import process_report
                process_report(today, force=True)
    
    except Exception as e:
        logger.error(f"Error in hourly check: {e}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    """
    Main function - runs scheduled tasks
    """
    logger.info("Starting scheduled tasks")
    
    # Get current time
    current_time = datetime.now()
    logger.info(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run initial check
    check_hourly()
    
    # Schedule tasks to run at specific times
    while True:
        # Get current time
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        # Check if it's time to run hourly check (at the top of each hour)
        if current_minute == 0:
            logger.info(f"Running hourly check at {current_hour}:00")
            check_hourly()
        
        # Check if it's 7 PM
        if current_hour == 19 and current_minute == 0:
            logger.info("It's 7 PM, running daily report")
            run_auto_daily_report()
        
        # Sleep for a minute
        time.sleep(60)

if __name__ == "__main__":
    main()
''')
        
        logger.info(f"Created scheduled tasks script: {scheduled_tasks_script}")
        
        # Create first-time execution for tomorrow
        one_time_script = 'process_may20_report.py'
        
        with open(one_time_script, 'w') as f:
            f.write('''#!/usr/bin/env python3
"""
Process May 20 Report

This script is a one-time execution script to process the May 20 report.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function
    """
    logger.info("Starting process for May 20 report")
    
    # Target date
    target_date = '2025-05-20'
    
    # Run auto daily report script
    logger.info(f"Running auto daily report for {target_date}")
    os.system(f"python auto_daily_report.py {target_date}")
    
    logger.info("Process completed")

if __name__ == "__main__":
    main()
''')
        
        logger.info(f"Created one-time execution script: {one_time_script}")
        
        # Make scripts executable
        os.system(f"chmod +x {scheduler_script}")
        os.system(f"chmod +x {scheduled_tasks_script}")
        os.system(f"chmod +x {one_time_script}")
        
        logger.info("Task 2 completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error in Task 2: {e}")
        traceback.print_exc()
        return False

def export_april_billing():
    """
    Export the full mock April Billing
    """
    logger.info("TASK 3: Exporting full mock April Billing")
    
    try:
        # Check if the April billing files exist
        ragle_file = [f for f in os.listdir('attached_assets') if 'RAGLE EQ BILLINGS - APRIL 2025' in f]
        pm_files = [f for f in os.listdir('attached_assets') if 'EQMO. BILLING ALLOCATIONS - APRIL 2025' in f]
        
        if not ragle_file:
            logger.error("RAGLE EQ BILLINGS file not found")
            return False
        
        logger.info(f"Found RAGLE file: {ragle_file[0]}")
        logger.info(f"Found {len(pm_files)} PM allocation files")
        
        # Call the billing processing module
        logger.info("Running final billing processor")
        
        # Create a backup of argv
        original_argv = sys.argv.copy()
        
        try:
            from final_billing_processor import process_and_generate_deliverables
            
            # Process billings
            process_and_generate_deliverables()
            
            # Restore original argv
            sys.argv = original_argv
            
            logger.info("Successfully processed April billing")
        except Exception as e:
            logger.error(f"Error processing April billing: {e}")
            traceback.print_exc()
            # Restore original argv
            sys.argv = original_argv
            return False
        
        # Check if exports were created
        billing_dir = 'exports/billing'
        os.makedirs(billing_dir, exist_ok=True)
        
        # Copy the processed files to the required location
        source_files = ['exports/dfw_april_2025.xlsx', 'exports/hou_april_2025.xlsx', 'exports/wt_april_2025.xlsx']
        
        # Combine into a single consolidated file
        try:
            logger.info("Creating consolidated April billing file")
            
            # Create a new Excel file with multiple sheets
            consolidated_path = f'{billing_dir}/April_MockBilling_Complete.xlsx'
            
            with pd.ExcelWriter(consolidated_path, engine='openpyxl') as writer:
                # Load each division file
                for source_file in source_files:
                    if os.path.exists(source_file):
                        # Get division name from filename
                        division = os.path.basename(source_file).split('_')[0].upper()
                        
                        # Read data
                        df = pd.read_excel(source_file)
                        
                        # Write to consolidated file
                        df.to_excel(writer, sheet_name=division, index=False)
                        
                        logger.info(f"Added {division} data with {len(df)} rows")
                    else:
                        logger.warning(f"Source file not found: {source_file}")
            
            if os.path.exists(consolidated_path):
                logger.info(f"Successfully created consolidated billing file: {consolidated_path} ({os.path.getsize(consolidated_path)} bytes)")
            else:
                logger.error(f"Failed to create consolidated billing file: {consolidated_path}")
                return False
            
            # Attempt to create PDF version
            try:
                from fpdf import FPDF
                
                pdf_path = f'{billing_dir}/April_MockBilling_Complete.pdf'
                
                # Create PDF
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                
                # Load each division file for PDF
                for source_file in source_files:
                    if os.path.exists(source_file):
                        # Get division name from filename
                        division = os.path.basename(source_file).split('_')[0].upper()
                        
                        # Read data
                        df = pd.read_excel(source_file)
                        
                        # Add page
                        pdf.add_page()
                        
                        # Add title
                        pdf.set_font('Arial', 'B', 16)
                        pdf.cell(0, 10, f"{division} - April 2025 Billing", 0, 1, 'C')
                        
                        # Add table headers
                        pdf.set_font('Arial', 'B', 10)
                        pdf.cell(0, 5, '', 0, 1, 'C')  # Spacing
                        
                        # Get column widths based on dataframe columns
                        col_width = 280 / len(df.columns)
                        
                        # Add headers
                        for col in df.columns:
                            pdf.cell(col_width, 7, str(col), 1, 0, 'C')
                        pdf.ln()
                        
                        # Add data
                        pdf.set_font('Arial', '', 8)
                        for i, row in df.head(40).iterrows():  # Limit to 40 rows for demo
                            for col in df.columns:
                                pdf.cell(col_width, 6, str(row[col])[:20], 1, 0, 'L')
                            pdf.ln()
                        
                        # Add note if truncated
                        if len(df) > 40:
                            pdf.cell(0, 10, f"Note: Showing 40 of {len(df)} rows", 0, 1, 'C')
                
                # Save PDF
                pdf.output(pdf_path)
                
                if os.path.exists(pdf_path):
                    logger.info(f"Successfully created PDF billing file: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
                else:
                    logger.error(f"Failed to create PDF billing file: {pdf_path}")
            
            except Exception as e:
                logger.error(f"Error creating PDF billing file: {e}")
                traceback.print_exc()
            
        except Exception as e:
            logger.error(f"Error creating consolidated billing file: {e}")
            traceback.print_exc()
            return False
        
        logger.info("Task 3 completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error in Task 3: {e}")
        traceback.print_exc()
        return False

def log_unmapped_entities():
    """
    Log unmapped drivers, job sites, or cost codes
    """
    logger.info("TASK 4: Logging unmapped entities")
    
    try:
        # Create log files
        unmapped_dir = 'logs/unmapped_entities'
        os.makedirs(unmapped_dir, exist_ok=True)
        
        # Functions to extract unmapped entities
        def find_unmapped_drivers():
            """Find drivers without proper matching"""
            unmapped_drivers = []
            
            # Check attendance pipeline logs for unmapped drivers
            try:
                from utils.attendance_pipeline_connector import get_attendance_data
                
                # Get data for a sample date
                sample_date = '2025-05-19'
                attendance_data = get_attendance_data(sample_date, force_refresh=False)
                
                if attendance_data:
                    # Get all driver records
                    all_drivers = attendance_data.get('all_drivers', [])
                    
                    # Check employee matches
                    employee_file = 'attached_assets/Consolidated_Employee_And_Job_Lists_Corrected.xlsx'
                    if os.path.exists(employee_file):
                        employee_data = pd.read_excel(employee_file, sheet_name='Employee_Contacts')
                        employee_names = employee_data['Employee Name'].tolist()
                        
                        # Find drivers without matches
                        for driver in all_drivers:
                            driver_name = driver.get('driver_name', '')
                            if driver_name and driver_name not in employee_names:
                                # Check if any employee name contains this driver name as substring
                                if not any(driver_name in emp_name for emp_name in employee_names):
                                    unmapped_drivers.append(driver_name)
            except Exception as e:
                logger.error(f"Error finding unmapped drivers: {e}")
            
            return list(set(unmapped_drivers))  # Return unique list
        
        def find_unmapped_jobs():
            """Find job sites without proper matching"""
            unmapped_jobs = []
            
            # Check attendance pipeline logs for unmapped jobs
            try:
                from utils.attendance_pipeline_connector import get_attendance_data
                
                # Get data for a sample date
                sample_date = '2025-05-19'
                attendance_data = get_attendance_data(sample_date, force_refresh=False)
                
                if attendance_data:
                    # Get all driver records
                    all_drivers = attendance_data.get('all_drivers', [])
                    
                    # Check job matches
                    job_file = 'attached_assets/Consolidated_Employee_And_Job_Lists_Corrected.xlsx'
                    if os.path.exists(job_file):
                        job_data = pd.read_excel(job_file, sheet_name='Job_Lists')
                        job_numbers = job_data['Job Number'].astype(str).tolist()
                        
                        # Find jobs without matches
                        for driver in all_drivers:
                            job_site = driver.get('job_site', '')
                            if job_site and job_site not in job_numbers:
                                unmapped_jobs.append(job_site)
            except Exception as e:
                logger.error(f"Error finding unmapped jobs: {e}")
            
            return list(set(unmapped_jobs))  # Return unique list
        
        def find_unmapped_cost_codes():
            """Find cost codes without proper matching"""
            unmapped_cost_codes = []
            
            # Check billing module for unmapped cost codes
            try:
                # Look at PM allocation files
                pm_files = [f for f in os.listdir('attached_assets') if 'EQMO. BILLING ALLOCATIONS - APRIL 2025' in f]
                
                for pm_file in pm_files:
                    try:
                        file_path = os.path.join('attached_assets', pm_file)
                        
                        # Read the Excel file
                        xls = pd.ExcelFile(file_path)
                        
                        # Look for sheets with allocation data
                        for sheet in xls.sheet_names:
                            if 'EQ ALLOCATIONS' in sheet.upper() or 'ALLOCATION' in sheet.upper():
                                try:
                                    df = pd.read_excel(file_path, sheet_name=sheet)
                                    
                                    # Find cost code column
                                    cost_code_col = None
                                    for col in df.columns:
                                        if 'COST CODE' in str(col).upper() or 'COSTCODE' in str(col).upper():
                                            cost_code_col = col
                                            break
                                    
                                    if cost_code_col:
                                        # Get cost codes
                                        cost_codes = df[cost_code_col].dropna().astype(str).tolist()
                                        
                                        # Check if cost codes match known formats
                                        for code in cost_codes:
                                            # Check if code matches expected format (e.g., 02-220-3210)
                                            import re
                                            if not re.match(r'\d{2}-\d{3}-\d{4}', code):
                                                unmapped_cost_codes.append(code)
                                except Exception as e:
                                    logger.warning(f"Error reading sheet {sheet} in {pm_file}: {e}")
                    except Exception as e:
                        logger.warning(f"Error reading PM file {pm_file}: {e}")
            except Exception as e:
                logger.error(f"Error finding unmapped cost codes: {e}")
            
            return list(set(unmapped_cost_codes))  # Return unique list
        
        # Find all unmapped entities
        unmapped_drivers = find_unmapped_drivers()
        unmapped_jobs = find_unmapped_jobs()
        unmapped_cost_codes = find_unmapped_cost_codes()
        
        # Log to files
        drivers_file = os.path.join(unmapped_dir, 'unmapped_drivers.txt')
        jobs_file = os.path.join(unmapped_dir, 'unmapped_jobs.txt')
        cost_codes_file = os.path.join(unmapped_dir, 'unmapped_cost_codes.txt')
        
        with open(drivers_file, 'w') as f:
            f.write(f"# Unmapped Drivers Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total: {len(unmapped_drivers)}\n\n")
            for driver in unmapped_drivers:
                f.write(f"{driver}\n")
        
        with open(jobs_file, 'w') as f:
            f.write(f"# Unmapped Job Sites Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total: {len(unmapped_jobs)}\n\n")
            for job in unmapped_jobs:
                f.write(f"{job}\n")
        
        with open(cost_codes_file, 'w') as f:
            f.write(f"# Unmapped Cost Codes Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total: {len(unmapped_cost_codes)}\n\n")
            for code in unmapped_cost_codes:
                f.write(f"{code}\n")
        
        logger.info(f"Found {len(unmapped_drivers)} unmapped drivers")
        logger.info(f"Found {len(unmapped_jobs)} unmapped job sites")
        logger.info(f"Found {len(unmapped_cost_codes)} unmapped cost codes")
        
        logger.info(f"Saved unmapped drivers to: {drivers_file}")
        logger.info(f"Saved unmapped jobs to: {jobs_file}")
        logger.info(f"Saved unmapped cost codes to: {cost_codes_file}")
        
        # Create summary file
        summary_file = os.path.join(unmapped_dir, 'unmapped_summary.txt')
        
        with open(summary_file, 'w') as f:
            f.write(f"# Unmapped Entities Summary Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Unmapped Drivers\n")
            f.write(f"Total: {len(unmapped_drivers)}\n")
            for driver in unmapped_drivers[:10]:  # First 10 for summary
                f.write(f"- {driver}\n")
            if len(unmapped_drivers) > 10:
                f.write(f"... and {len(unmapped_drivers) - 10} more\n")
            
            f.write("\n## Unmapped Job Sites\n")
            f.write(f"Total: {len(unmapped_jobs)}\n")
            for job in unmapped_jobs[:10]:  # First 10 for summary
                f.write(f"- {job}\n")
            if len(unmapped_jobs) > 10:
                f.write(f"... and {len(unmapped_jobs) - 10} more\n")
            
            f.write("\n## Unmapped Cost Codes\n")
            f.write(f"Total: {len(unmapped_cost_codes)}\n")
            for code in unmapped_cost_codes[:10]:  # First 10 for summary
                f.write(f"- {code}\n")
            if len(unmapped_cost_codes) > 10:
                f.write(f"... and {len(unmapped_cost_codes) - 10} more\n")
        
        logger.info(f"Saved summary report to: {summary_file}")
        
        logger.info("Task 4 completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error in Task 4: {e}")
        traceback.print_exc()
        return False

def main():
    """
    Main function to execute all tasks
    """
    logger.info("======== STARTING OVERNIGHT PRIORITY TASKS ========")
    logger.info(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track overall status
    overall_status = True
    
    # Execute tasks in sequence
    tasks = [
        ("Finalize 2025-05-19 Daily Driver Report", finalize_daily_report),
        ("Prepare 2025-05-20 pipeline", prepare_tomorrow_pipeline),
        ("Export April Billing", export_april_billing),
        ("Log unmapped entities", log_unmapped_entities)
    ]
    
    for task_name, task_function in tasks:
        logger.info(f"\n======== EXECUTING: {task_name} ========")
        try:
            task_success = task_function()
            if task_success:
                logger.info(f"SUCCESS: {task_name}")
            else:
                logger.error(f"FAILED: {task_name}")
                overall_status = False
        except Exception as e:
            logger.error(f"CRITICAL ERROR in {task_name}: {e}")
            traceback.print_exc()
            overall_status = False
    
    # Final status report
    logger.info("\n======== OVERNIGHT TASKS SUMMARY ========")
    if overall_status:
        logger.info("ALL TASKS COMPLETED SUCCESSFULLY")
    else:
        logger.warning("SOME TASKS FAILED - See log for details")
    
    logger.info(f"Completion time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("======== END OF OVERNIGHT TASKS ========")

if __name__ == "__main__":
    main()