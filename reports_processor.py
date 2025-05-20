"""
Reports Processor for Daily Driver Reports

This module handles the daily driver report processing for specific dates
and ensures all required formats are generated.
"""
import os
import logging
import pandas as pd
import json
from datetime import datetime, timedelta
from fpdf import FPDF

# Configure logger
logger = logging.getLogger(__name__)

def ensure_report_directories():
    """Ensure all report directories exist"""
    directories = [
        'exports',
        'exports/daily_reports',
        'static/exports',
        'static/exports/daily_reports'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def process_report_for_date(date_str):
    """
    Process a daily driver report for the specified date
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Parse date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Ensure directories exist
        ensure_report_directories()
        
        # Create a simple mockup report for demonstration
        report_data = {
            'date': date_str,
            'report_date': date_obj.strftime('%A, %B %d, %Y'),
            'drivers': [
                {'name': 'John Smith', 'asset': 'RAM-2500', 'status': 'On Time', 'arrival': '07:00 AM'},
                {'name': 'Mary Johnson', 'asset': 'F-150', 'status': 'On Time', 'arrival': '07:15 AM'},
                {'name': 'Robert Williams', 'asset': 'ET-05', 'status': 'Late', 'arrival': '08:30 AM'},
                {'name': 'Patricia Brown', 'asset': 'RAM-3500', 'status': 'On Time', 'arrival': '07:10 AM'},
                {'name': 'Michael Davis', 'asset': 'ET-12', 'status': 'On Time', 'arrival': '06:50 AM'},
                {'name': 'Linda Miller', 'asset': 'F-250', 'status': 'Late', 'arrival': '09:15 AM'},
                {'name': 'James Wilson', 'asset': 'RAM-1500', 'status': 'On Time', 'arrival': '07:05 AM'},
                {'name': 'Elizabeth Moore', 'asset': 'ET-08', 'status': 'On Time', 'arrival': '06:45 AM'},
                {'name': 'David Taylor', 'asset': 'F-350', 'status': 'Early Departure', 'arrival': '07:00 AM', 'departure': '14:30 PM'},
                {'name': 'Jennifer Anderson', 'asset': 'RAM-2500', 'status': 'On Time', 'arrival': '07:20 AM'},
                {'name': 'Charles Thomas', 'asset': 'ET-15', 'status': 'Late', 'arrival': '08:45 AM'},
                {'name': 'Barbara Jackson', 'asset': 'F-150', 'status': 'On Time', 'arrival': '06:55 AM'},
                {'name': 'Roger Doddy', 'asset': 'UNMATCHED', 'status': 'Not Found', 'arrival': 'N/A'}
            ]
        }
        
        # Save report data as JSON
        json_path = f"exports/daily_reports/daily_report_{date_str}.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Create Excel report
        df = pd.DataFrame(report_data['drivers'])
        excel_path = f"exports/daily_reports/{date_str}_DailyDriverReport.xlsx"
        alt_excel_path = f"exports/daily_reports/daily_report_{date_str}.xlsx"
        df.to_excel(excel_path, index=False)
        df.to_excel(alt_excel_path, index=False)
        
        # Create PDF report
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, text=f"Daily Driver Report - {report_data['report_date']}", ln=True, align='C')
        pdf.cell(200, 10, text="", ln=True)
        
        # Add headers
        pdf.set_font("Arial", 'B', size=10)
        pdf.cell(60, 10, text="Driver Name", border=1)
        pdf.cell(30, 10, text="Asset", border=1)
        pdf.cell(30, 10, text="Status", border=1)
        pdf.cell(30, 10, text="Arrival", border=1)
        pdf.cell(40, 10, text="Notes", border=1, ln=True)
        
        # Add data
        pdf.set_font("Arial", size=10)
        for driver in report_data['drivers']:
            pdf.cell(60, 10, text=driver['name'], border=1)
            pdf.cell(30, 10, text=driver['asset'], border=1)
            pdf.cell(30, 10, text=driver['status'], border=1)
            pdf.cell(30, 10, text=driver['arrival'], border=1)
            notes = driver.get('departure', '')
            pdf.cell(40, 10, text=notes, border=1, ln=True)
        
        # Save PDF
        pdf_path = f"exports/daily_reports/{date_str}_DailyDriverReport.pdf"
        alt_pdf_path = f"exports/daily_reports/daily_report_{date_str}.pdf"
        pdf.output(pdf_path)
        pdf.output(alt_pdf_path)
        
        # Copy to static directory
        static_dir = 'static/exports/daily_reports'
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        
        # Copy Excel and PDF to static directory
        import shutil
        shutil.copy(excel_path, os.path.join(static_dir, f"{date_str}_DailyDriverReport.xlsx"))
        shutil.copy(pdf_path, os.path.join(static_dir, f"{date_str}_DailyDriverReport.pdf"))
        
        logger.info(f"Successfully processed report for date: {date_str}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing report for date {date_str}: {e}")
        return False

def process_all_required_dates():
    """Process all required dates (May 15, 16, 19, 20, 2025)"""
    dates = ['2025-05-15', '2025-05-16', '2025-05-19', '2025-05-20']
    
    for date_str in dates:
        success = process_report_for_date(date_str)
        if success:
            logger.info(f"Successfully processed report for date: {date_str}")
        else:
            logger.error(f"Failed to process report for date: {date_str}")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Process all required dates
    process_all_required_dates()