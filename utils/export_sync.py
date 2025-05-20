"""
Export Sync Module

This module ensures that all export formats (PDF, Excel, HTML) consistently
use the same driver data from the attendance pipeline.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import traceback

# Set up logging
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('logs/export_sync.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# Define directories
EXPORTS_DIR = "exports"
DAILY_REPORTS_DIR = os.path.join(EXPORTS_DIR, "daily_reports")
PDF_REPORTS_DIR = os.path.join(EXPORTS_DIR, "pdf_reports")
EXCEL_REPORTS_DIR = os.path.join(EXPORTS_DIR, "excel_reports")

# Ensure directories exist
for directory in [EXPORTS_DIR, DAILY_REPORTS_DIR, PDF_REPORTS_DIR, EXCEL_REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

def generate_pdf_report(date_str, driver_summary):
    """
    Generate a PDF report for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        driver_summary (dict): Driver summary with computed statuses
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Set up styles
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f"Daily Driver Report - {formatted_date}", 0, 1, 'C')
        pdf.ln(5)
        
        # Summary section
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "Summary", 0, 1, 'L')
        
        pdf.set_font('Arial', '', 12)
        pdf.cell(60, 8, "Total Drivers:", 0, 0, 'L')
        pdf.cell(30, 8, str(driver_summary['summary']['total_drivers']), 0, 1, 'L')
        
        pdf.cell(60, 8, "On Time Drivers:", 0, 0, 'L')
        pdf.cell(30, 8, str(driver_summary['summary']['on_time_drivers']), 0, 1, 'L')
        
        pdf.cell(60, 8, "Late Drivers:", 0, 0, 'L')
        pdf.cell(30, 8, str(driver_summary['summary']['late_drivers']), 0, 1, 'L')
        
        pdf.cell(60, 8, "Early End Drivers:", 0, 0, 'L')
        pdf.cell(30, 8, str(driver_summary['summary']['early_end_drivers']), 0, 1, 'L')
        
        pdf.cell(60, 8, "Not On Job Drivers:", 0, 0, 'L')
        pdf.cell(30, 8, str(driver_summary['summary']['not_on_job_drivers']), 0, 1, 'L')
        
        pdf.ln(5)
        
        # Late drivers section
        if driver_summary['late_drivers']:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "Late Drivers", 0, 1, 'L')
            
            # Table header
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(50, 8, "Driver", 1, 0, 'L')
            pdf.cell(30, 8, "Asset", 1, 0, 'L')
            pdf.cell(35, 8, "Scheduled Start", 1, 0, 'L')
            pdf.cell(35, 8, "Actual Start", 1, 0, 'L')
            pdf.cell(30, 8, "Minutes Late", 1, 1, 'L')
            
            # Table data
            pdf.set_font('Arial', '', 10)
            for driver in driver_summary['late_drivers']:
                pdf.cell(50, 8, driver.get('name', 'N/A')[:25], 1, 0, 'L')
                pdf.cell(30, 8, driver.get('asset', 'N/A')[:15], 1, 0, 'L')
                pdf.cell(35, 8, driver.get('scheduled_start', 'N/A'), 1, 0, 'L')
                pdf.cell(35, 8, driver.get('arrival', 'N/A'), 1, 0, 'L')
                pdf.cell(30, 8, str(driver.get('minutes_late', 'N/A')), 1, 1, 'L')
            
            pdf.ln(5)
        
        # Early end drivers section
        if driver_summary['early_end_drivers']:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "Early End Drivers", 0, 1, 'L')
            
            # Table header
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(50, 8, "Driver", 1, 0, 'L')
            pdf.cell(30, 8, "Asset", 1, 0, 'L')
            pdf.cell(35, 8, "Scheduled End", 1, 0, 'L')
            pdf.cell(35, 8, "Actual End", 1, 0, 'L')
            pdf.cell(30, 8, "Minutes Early", 1, 1, 'L')
            
            # Table data
            pdf.set_font('Arial', '', 10)
            for driver in driver_summary['early_end_drivers']:
                pdf.cell(50, 8, driver.get('name', 'N/A')[:25], 1, 0, 'L')
                pdf.cell(30, 8, driver.get('asset', 'N/A')[:15], 1, 0, 'L')
                pdf.cell(35, 8, driver.get('scheduled_end', 'N/A'), 1, 0, 'L')
                pdf.cell(35, 8, driver.get('departure', 'N/A'), 1, 0, 'L')
                pdf.cell(30, 8, str(driver.get('minutes_early', 'N/A')), 1, 1, 'L')
            
            pdf.ln(5)
        
        # Not on job drivers section
        if driver_summary['not_on_job_drivers']:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "Not On Job Drivers", 0, 1, 'L')
            
            # Table header
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(50, 8, "Driver", 1, 0, 'L')
            pdf.cell(30, 8, "Asset", 1, 0, 'L')
            pdf.cell(60, 8, "Job Site", 1, 0, 'L')
            pdf.cell(50, 8, "Reason", 1, 1, 'L')
            
            # Table data
            pdf.set_font('Arial', '', 10)
            for driver in driver_summary['not_on_job_drivers']:
                pdf.cell(50, 8, driver.get('name', 'N/A')[:25], 1, 0, 'L')
                pdf.cell(30, 8, driver.get('asset', 'N/A')[:15], 1, 0, 'L')
                pdf.cell(60, 8, driver.get('job_site', 'N/A')[:30], 1, 0, 'L')
                pdf.cell(50, 8, driver.get('status_reason', 'Unknown')[:25], 1, 1, 'L')
        
        # Save PDF
        pdf_path = os.path.join(PDF_REPORTS_DIR, f"daily_report_{date_str}.pdf")
        pdf.output(pdf_path)
        
        logger.info(f"Generated PDF report for {date_str}: {pdf_path}")
        return pdf_path
    
    except Exception as e:
        logger.error(f"Error generating PDF report for {date_str}: {e}")
        logger.error(traceback.format_exc())
        return None

def generate_excel_report(date_str, driver_summary):
    """
    Generate an Excel report for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        driver_summary (dict): Driver summary with computed statuses
        
    Returns:
        str: Path to the generated Excel file
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Create Excel writer
        excel_path = os.path.join(EXCEL_REPORTS_DIR, f"daily_report_{date_str}.xlsx")
        writer = pd.ExcelWriter(excel_path, engine='openpyxl')
        
        # Create summary sheet
        summary_data = {
            'Metric': ['Total Drivers', 'On Time Drivers', 'Late Drivers', 
                      'Early End Drivers', 'Not On Job Drivers'],
            'Count': [
                driver_summary['summary']['total_drivers'],
                driver_summary['summary']['on_time_drivers'],
                driver_summary['summary']['late_drivers'],
                driver_summary['summary']['early_end_drivers'],
                driver_summary['summary']['not_on_job_drivers']
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Create late drivers sheet
        if driver_summary['late_drivers']:
            late_drivers_data = []
            for driver in driver_summary['late_drivers']:
                late_drivers_data.append({
                    'Driver': driver.get('name', 'N/A'),
                    'Asset': driver.get('asset', 'N/A'),
                    'Scheduled Start': driver.get('scheduled_start', 'N/A'),
                    'Actual Start': driver.get('arrival', 'N/A'),
                    'Minutes Late': driver.get('minutes_late', 'N/A'),
                    'Job Site': driver.get('job_site', 'N/A')
                })
            
            if late_drivers_data:
                late_drivers_df = pd.DataFrame(late_drivers_data)
                late_drivers_df.to_excel(writer, sheet_name='Late Drivers', index=False)
        
        # Create early end drivers sheet
        if driver_summary['early_end_drivers']:
            early_end_data = []
            for driver in driver_summary['early_end_drivers']:
                early_end_data.append({
                    'Driver': driver.get('name', 'N/A'),
                    'Asset': driver.get('asset', 'N/A'),
                    'Scheduled End': driver.get('scheduled_end', 'N/A'),
                    'Actual End': driver.get('departure', 'N/A'),
                    'Minutes Early': driver.get('minutes_early', 'N/A'),
                    'Job Site': driver.get('job_site', 'N/A')
                })
            
            if early_end_data:
                early_end_df = pd.DataFrame(early_end_data)
                early_end_df.to_excel(writer, sheet_name='Early End Drivers', index=False)
        
        # Create not on job drivers sheet
        if driver_summary['not_on_job_drivers']:
            not_on_job_data = []
            for driver in driver_summary['not_on_job_drivers']:
                not_on_job_data.append({
                    'Driver': driver.get('name', 'N/A'),
                    'Asset': driver.get('asset', 'N/A'),
                    'Job Site': driver.get('job_site', 'N/A'),
                    'Reason': driver.get('status_reason', 'Unknown')
                })
            
            if not_on_job_data:
                not_on_job_df = pd.DataFrame(not_on_job_data)
                not_on_job_df.to_excel(writer, sheet_name='Not On Job Drivers', index=False)
        
        # Create all drivers sheet
        all_drivers_data = []
        for driver in driver_summary['driver_summary']:
            all_drivers_data.append({
                'Driver': driver.get('name', 'N/A'),
                'Asset': driver.get('asset', 'N/A'),
                'Status': driver.get('status', 'Unknown'),
                'Scheduled Start': driver.get('scheduled_start', 'N/A'),
                'Actual Start': driver.get('arrival', 'N/A'),
                'Scheduled End': driver.get('scheduled_end', 'N/A'),
                'Actual End': driver.get('departure', 'N/A'),
                'Job Site': driver.get('job_site', 'N/A')
            })
        
        all_drivers_df = pd.DataFrame(all_drivers_data)
        all_drivers_df.to_excel(writer, sheet_name='All Drivers', index=False)
        
        # Save Excel file
        writer.close()
        
        logger.info(f"Generated Excel report for {date_str}: {excel_path}")
        return excel_path
    
    except Exception as e:
        logger.error(f"Error generating Excel report for {date_str}: {e}")
        logger.error(traceback.format_exc())
        return None

def sync_exports(date_str, driver_summary=None):
    """
    Sync all export formats for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        driver_summary (dict): Driver summary with computed statuses
        
    Returns:
        dict: Export file paths
    """
    try:
        # If driver_summary is not provided, load it from cache
        if not driver_summary:
            json_path = os.path.join(DAILY_REPORTS_DIR, f"daily_report_{date_str}.json")
            
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    driver_summary = json.load(f)
            else:
                # Get attendance data
                from utils.attendance_pipeline_connector import process_attendance_data
                driver_summary = process_attendance_data(date_str)
        
        if not driver_summary:
            logger.error(f"No driver summary available for {date_str}")
            return None
        
        # Assert that driver summary is consistent
        assert driver_summary['summary']['total_drivers'] == len(driver_summary['driver_summary']), \
            f"Driver count mismatch: summary={driver_summary['summary']['total_drivers']}, actual={len(driver_summary['driver_summary'])}"
        
        assert driver_summary['summary']['late_drivers'] == len(driver_summary['late_drivers']), \
            f"Late driver count mismatch: summary={driver_summary['summary']['late_drivers']}, actual={len(driver_summary['late_drivers'])}"
        
        assert driver_summary['summary']['early_end_drivers'] == len(driver_summary['early_end_drivers']), \
            f"Early end driver count mismatch: summary={driver_summary['summary']['early_end_drivers']}, actual={len(driver_summary['early_end_drivers'])}"
        
        assert driver_summary['summary']['not_on_job_drivers'] == len(driver_summary['not_on_job_drivers']), \
            f"Not on job driver count mismatch: summary={driver_summary['summary']['not_on_job_drivers']}, actual={len(driver_summary['not_on_job_drivers'])}"
        
        # Generate exports
        json_path = os.path.join(DAILY_REPORTS_DIR, f"daily_report_{date_str}.json")
        
        # Save/update JSON file (primary source of truth)
        with open(json_path, 'w') as f:
            json.dump(driver_summary, f, indent=2, default=str)
        
        # Generate PDF
        pdf_path = generate_pdf_report(date_str, driver_summary)
        
        # Generate Excel
        excel_path = generate_excel_report(date_str, driver_summary)
        
        # Return export paths
        export_paths = {
            'json': json_path,
            'pdf': pdf_path,
            'excel': excel_path
        }
        
        logger.info(f"Exports synced for {date_str}: {export_paths}")
        return export_paths
    
    except Exception as e:
        logger.error(f"Error syncing exports for {date_str}: {e}")
        logger.error(traceback.format_exc())
        return None

def update_report_links(date_str, export_paths=None):
    """
    Update the report links in the JSON file
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        export_paths (dict): Export file paths
        
    Returns:
        bool: Success status
    """
    try:
        # If export_paths is not provided, regenerate them
        if not export_paths:
            export_paths = sync_exports(date_str)
        
        if not export_paths:
            logger.error(f"No export paths available for {date_str}")
            return False
        
        # Load the JSON report
        json_path = export_paths['json']
        
        with open(json_path, 'r') as f:
            report_data = json.load(f)
        
        # Update file paths
        if 'files' not in report_data:
            report_data['files'] = {}
        
        # Set relative paths
        report_data['files']['json_path'] = os.path.relpath(export_paths['json'], EXPORTS_DIR)
        report_data['files']['json_exists'] = True
        
        if export_paths['pdf']:
            report_data['files']['pdf_path'] = os.path.relpath(export_paths['pdf'], EXPORTS_DIR)
            report_data['files']['pdf_exists'] = True
        else:
            report_data['files']['pdf_exists'] = False
        
        if export_paths['excel']:
            report_data['files']['excel_path'] = os.path.relpath(export_paths['excel'], EXPORTS_DIR)
            report_data['files']['excel_exists'] = True
        else:
            report_data['files']['excel_exists'] = False
        
        # Save updated JSON
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Updated report links for {date_str}")
        return True
    
    except Exception as e:
        logger.error(f"Error updating report links for {date_str}: {e}")
        logger.error(traceback.format_exc())
        return False

def process_date_range(start_date, end_date):
    """
    Process a range of dates to sync all exports
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        dict: Processing results by date
    """
    results = {}
    
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    current_date = start_date_obj
    while current_date <= end_date_obj:
        date_str = current_date.strftime('%Y-%m-%d')
        
        try:
            # Sync exports
            export_paths = sync_exports(date_str)
            
            if export_paths:
                # Update report links
                update_report_links(date_str, export_paths)
                
                results[date_str] = {
                    'status': 'success',
                    'export_paths': export_paths
                }
            else:
                results[date_str] = {
                    'status': 'error',
                    'message': 'Failed to sync exports'
                }
        
        except Exception as e:
            logger.error(f"Error processing {date_str}: {e}")
            logger.error(traceback.format_exc())
            
            results[date_str] = {
                'status': 'error',
                'message': str(e)
            }
        
        current_date = current_date + timedelta(days=1)
    
    return results

def process_specific_date(date_str):
    """
    Process a specific date to sync all exports
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Processing results
    """
    try:
        # Sync exports
        export_paths = sync_exports(date_str)
        
        if export_paths:
            # Update report links
            update_report_links(date_str, export_paths)
            
            return {
                'status': 'success',
                'export_paths': export_paths
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to sync exports'
            }
    
    except Exception as e:
        logger.error(f"Error processing {date_str}: {e}")
        logger.error(traceback.format_exc())
        
        return {
            'status': 'error',
            'message': str(e)
        }