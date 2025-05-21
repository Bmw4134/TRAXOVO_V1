#!/usr/bin/env python
"""
Generate May 16, 2025 Daily Driver Report

This script generates the daily driver report for May 16, 2025,
using raw source files (DrivingHistory, ActivityDetail, and Start Time & Job),
and emails the report to specified recipients.
"""

import os
import logging
import argparse
from datetime import datetime
from utils.unified_data_processor import generate_daily_driver_report
from utils.report_generator import generate_pdf_report, generate_excel_report, email_report

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create log directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Create file handler for logging
file_handler = logging.FileHandler('logs/generate_may16_report.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate May 16, 2025 Daily Driver Report')
    parser.add_argument('--email', action='store_true', help='Send email with the report')
    parser.add_argument('--recipients', type=str, 
                      default='bm.watson34@gmail.com,bwatson@ragleinc.com',
                      help='Comma-separated list of email recipients')
    args = parser.parse_args()
    
    # Target date
    date_str = '2025-05-16'
    
    try:
        # Step 1: Generate the report data from raw source files
        logger.info(f"Generating daily driver report for {date_str}")
        report_data = generate_daily_driver_report(date_str)
        
        if not report_data:
            logger.error(f"Failed to generate report for {date_str}")
            return 1
        
        # Log summary statistics
        logger.info(f"Report summary: {report_data['summary']}")
        
        # Step 2: Generate PDF report
        logger.info(f"Generating PDF report for {date_str}")
        pdf_path = generate_pdf_report(date_str, report_data)
        
        if not pdf_path:
            logger.error(f"Failed to generate PDF report for {date_str}")
            return 1
        
        logger.info(f"PDF report generated: {pdf_path}")
        
        # Step 3: Generate Excel report
        logger.info(f"Generating Excel report for {date_str}")
        excel_path = generate_excel_report(date_str, report_data)
        
        if not excel_path:
            logger.error(f"Failed to generate Excel report for {date_str}")
            return 1
        
        logger.info(f"Excel report generated: {excel_path}")
        
        # Step 4: Email the report if requested
        if args.email:
            recipients = [email.strip() for email in args.recipients.split(',') if email.strip()]
            
            if not recipients:
                logger.error("No valid email recipients specified")
                return 1
            
            logger.info(f"Emailing report to: {', '.join(recipients)}")
            email_success = email_report(date_str, recipients, report_data)
            
            if not email_success:
                logger.error(f"Failed to email report for {date_str}")
                return 1
            
            logger.info(f"Report successfully emailed to {', '.join(recipients)}")
        
        return 0
    
    except Exception as e:
        logger.exception(f"Error generating report: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)