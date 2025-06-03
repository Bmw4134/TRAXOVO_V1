"""
Process Authentic Employee Report

This script rebuilds the Daily Driver Reports for May 16th, 2025 using only verified employee data
from the official ELIST and JLIST sources, eliminating all synthetic or test employee entries.
"""
import logging
import sys
import os
from employee_data_validator import employee_validator
from reports_processor import process_report_for_date
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')

# Add a file handler for unmatched driver logs
unmatched_handler = logging.FileHandler('logs/unmatched_drivers.log')
unmatched_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
unmatched_logger = logging.getLogger('unmatched_drivers')
unmatched_logger.addHandler(unmatched_handler)
unmatched_logger.setLevel(logging.WARNING)

def process_authentic_report(date_str=None):
    """
    Process a report with only authentic employee data for the specified date
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format, defaults to May 16th, 2025
        
    Returns:
        bool: True if successful, False otherwise
    """
    if date_str is None:
        date_str = '2025-05-16'
    
    logger.info(f"Processing authentic report for {date_str}")
    
    # First make sure employee validator is loaded
    if not employee_validator.loaded:
        logger.info("Loading employee data from official sources")
        if not employee_validator.load_employee_data():
            logger.error("Failed to load employee data")
            return False
    
    # Process the report for the specified date
    try:
        success = process_report_for_date(date_str)
        
        if success:
            logger.info(f"Successfully processed authentic report for {date_str}")
            # Verify the output
            report_path = f"exports/daily_reports/daily_report_{date_str}.json"
            pdf_path = f"exports/daily_reports/{date_str}_DailyDriverReport.pdf"
            
            if os.path.exists(report_path) and os.path.exists(pdf_path):
                logger.info(f"Report files generated successfully:")
                logger.info(f"  - JSON: {report_path}")
                logger.info(f"  - PDF: {pdf_path}")
            else:
                logger.warning("Report files not found at expected locations")
                
            return True
        else:
            logger.error(f"Failed to process report for {date_str}")
            return False
    
    except Exception as e:
        logger.error(f"Error processing report: {e}")
        return False

def process_all_required_dates():
    """Process all required dates (May 15, 16, 19, 20, 2025)"""
    dates = ['2025-05-15', '2025-05-16', '2025-05-19', '2025-05-20']
    
    results = {}
    for date_str in dates:
        success = process_authentic_report(date_str)
        results[date_str] = "Success" if success else "Failed"
    
    # Print summary
    logger.info("-" * 40)
    logger.info("Report Processing Summary:")
    for date, result in results.items():
        logger.info(f"  - {date}: {result}")
    logger.info("-" * 40)

if __name__ == "__main__":
    # Process May 16th report or specific date if provided
    if len(sys.argv) > 1:
        date_arg = sys.argv[1]
        if date_arg == "all":
            process_all_required_dates()
        else:
            process_authentic_report(date_arg)
    else:
        # Default to May 16th
        process_authentic_report('2025-05-16')