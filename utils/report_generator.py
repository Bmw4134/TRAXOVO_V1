"""
Report Generator

This module handles generating PDF and Excel reports from the daily driver report data,
as well as email delivery of these reports.
"""

import os
import pandas as pd
import logging
from datetime import datetime
import traceback
import json
from fpdf import FPDF
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
import base64

# Import the unified data processor
from utils.unified_data_processor import generate_daily_driver_report

# Set up logging
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('logs/report_generator.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# Set up email logging
email_logger = logging.getLogger('email_report_dispatch')
email_file_handler = logging.FileHandler('logs/email_report_dispatch.log')
email_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
email_logger.addHandler(email_file_handler)
email_logger.setLevel(logging.INFO)

def generate_pdf_report(date_str, report_data=None):
    """
    Generate a PDF report for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        report_data (dict): Report data (if None, will be generated)
        
    Returns:
        str: Path to generated PDF file
    """
    try:
        # Create export directory
        pdf_dir = os.path.join('exports', 'pdf_reports')
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Generate report data if not provided
        if not report_data:
            report_data = generate_daily_driver_report(date_str)
        
        # Parse date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Extract summary counts
        total_drivers = report_data['summary']['total_drivers']
        on_time_drivers = report_data['summary']['on_time_drivers']
        late_drivers = report_data['summary']['late_drivers']
        early_end_drivers = report_data['summary']['early_end_drivers']
        not_on_job_drivers = report_data['summary']['not_on_job_drivers']
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Set document properties
        pdf.set_title(f"Daily Driver Report - {formatted_date}")
        pdf.set_author("TRAXORA Fleet Management System")
        
        # Add header
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Daily Driver Report - {formatted_date}", 0, 1, "C")
        pdf.ln(5)
        
        # Add summary section
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Summary", 0, 1, "L")
        
        pdf.set_font("Arial", "", 11)
        
        # Summary table
        col_width = 95
        row_height = 8
        
        # Header row
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(col_width, row_height, "Metric", 1, 0, "L", True)
        pdf.cell(col_width, row_height, "Count", 1, 1, "C", True)
        
        # Data rows
        pdf.set_font("Arial", "", 10)
        
        # Total drivers
        pdf.cell(col_width, row_height, "Total Drivers", 1, 0, "L")
        pdf.cell(col_width, row_height, str(total_drivers), 1, 1, "C")
        
        # On time drivers
        pdf.cell(col_width, row_height, "On Time Drivers", 1, 0, "L")
        pdf.cell(col_width, row_height, str(on_time_drivers), 1, 1, "C")
        
        # Late drivers
        pdf.cell(col_width, row_height, "Late Drivers", 1, 0, "L")
        pdf.cell(col_width, row_height, str(late_drivers), 1, 1, "C")
        
        # Early end drivers
        pdf.cell(col_width, row_height, "Early End Drivers", 1, 0, "L")
        pdf.cell(col_width, row_height, str(early_end_drivers), 1, 1, "C")
        
        # Not on job drivers
        pdf.cell(col_width, row_height, "Not On Job Drivers", 1, 0, "L")
        pdf.cell(col_width, row_height, str(not_on_job_drivers), 1, 1, "C")
        
        # Calculate on-time percentage
        on_time_percent = round((on_time_drivers / total_drivers * 100) if total_drivers > 0 else 0, 1)
        
        # On time percentage
        pdf.cell(col_width, row_height, "On Time Percentage", 1, 0, "L")
        pdf.cell(col_width, row_height, f"{on_time_percent}%", 1, 1, "C")
        
        pdf.ln(5)
        
        # Add late drivers section if any
        if late_drivers > 0 and report_data.get('late_drivers'):
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Late Drivers", 0, 1, "L")
            
            # Column widths for late drivers
            col_widths = [40, 25, 35, 35, 30, 25]
            total_width = sum(col_widths)
            
            # Table header
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", "B", 8)
            pdf.cell(col_widths[0], row_height, "Driver", 1, 0, "L", True)
            pdf.cell(col_widths[1], row_height, "Asset", 1, 0, "L", True)
            pdf.cell(col_widths[2], row_height, "Scheduled Start", 1, 0, "C", True)
            pdf.cell(col_widths[3], row_height, "Actual Start", 1, 0, "C", True)
            pdf.cell(col_widths[4], row_height, "Minutes Late", 1, 0, "C", True)
            pdf.cell(col_widths[5], row_height, "Job Site", 1, 1, "L", True)
            
            # Table data
            pdf.set_font("Arial", "", 8)
            
            for driver in report_data['late_drivers']:
                pdf.cell(col_widths[0], row_height, str(driver.get('driver_name', 'N/A'))[:20], 1, 0, "L")
                pdf.cell(col_widths[1], row_height, str(driver.get('asset_id', 'N/A'))[:12], 1, 0, "L")
                pdf.cell(col_widths[2], row_height, str(driver.get('scheduled_start', 'N/A')), 1, 0, "C")
                pdf.cell(col_widths[3], row_height, str(driver.get('actual_start_display', 'N/A')), 1, 0, "C")
                pdf.cell(col_widths[4], row_height, str(driver.get('minutes_late', 'N/A')), 1, 0, "C")
                pdf.cell(col_widths[5], row_height, str(driver.get('assigned_job_site', 'N/A'))[:12], 1, 1, "L")
            
            pdf.ln(5)
        
        # Add early end drivers section if any
        if early_end_drivers > 0 and report_data.get('early_end_drivers'):
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Early End Drivers", 0, 1, "L")
            
            # Column widths for early end drivers
            col_widths = [40, 25, 35, 35, 30, 25]
            
            # Table header
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", "B", 8)
            pdf.cell(col_widths[0], row_height, "Driver", 1, 0, "L", True)
            pdf.cell(col_widths[1], row_height, "Asset", 1, 0, "L", True)
            pdf.cell(col_widths[2], row_height, "Scheduled End", 1, 0, "C", True)
            pdf.cell(col_widths[3], row_height, "Actual End", 1, 0, "C", True)
            pdf.cell(col_widths[4], row_height, "Minutes Early", 1, 0, "C", True)
            pdf.cell(col_widths[5], row_height, "Job Site", 1, 1, "L", True)
            
            # Table data
            pdf.set_font("Arial", "", 8)
            
            for driver in report_data['early_end_drivers']:
                pdf.cell(col_widths[0], row_height, str(driver.get('driver_name', 'N/A'))[:20], 1, 0, "L")
                pdf.cell(col_widths[1], row_height, str(driver.get('asset_id', 'N/A'))[:12], 1, 0, "L")
                pdf.cell(col_widths[2], row_height, str(driver.get('scheduled_end', 'N/A')), 1, 0, "C")
                pdf.cell(col_widths[3], row_height, str(driver.get('actual_end_display', 'N/A')), 1, 0, "C")
                pdf.cell(col_widths[4], row_height, str(driver.get('minutes_early', 'N/A')), 1, 0, "C")
                pdf.cell(col_widths[5], row_height, str(driver.get('assigned_job_site', 'N/A'))[:12], 1, 1, "L")
            
            pdf.ln(5)
        
        # Add not on job drivers section if any
        if not_on_job_drivers > 0 and report_data.get('not_on_job_drivers'):
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Not On Job Drivers", 0, 1, "L")
            
            # Column widths for not on job drivers
            col_widths = [45, 25, 45, 75]
            
            # Table header
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", "B", 8)
            pdf.cell(col_widths[0], row_height, "Driver", 1, 0, "L", True)
            pdf.cell(col_widths[1], row_height, "Asset", 1, 0, "L", True)
            pdf.cell(col_widths[2], row_height, "Job Site", 1, 0, "L", True)
            pdf.cell(col_widths[3], row_height, "Reason", 1, 1, "L", True)
            
            # Table data
            pdf.set_font("Arial", "", 8)
            
            for driver in report_data['not_on_job_drivers']:
                pdf.cell(col_widths[0], row_height, str(driver.get('driver_name', 'N/A'))[:20], 1, 0, "L")
                pdf.cell(col_widths[1], row_height, str(driver.get('asset_id', 'N/A'))[:12], 1, 0, "L")
                pdf.cell(col_widths[2], row_height, str(driver.get('assigned_job_site', 'N/A'))[:20], 1, 0, "L")
                pdf.cell(col_widths[3], row_height, str(driver.get('status_reason', 'Unknown'))[:35], 1, 1, "L")
        
        # Add footer
        pdf.set_y(-20)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, f"Generated by TRAXORA Fleet Management System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 0, "C")
        
        # Save PDF
        pdf_path = os.path.join(pdf_dir, f"daily_report_{date_str}.pdf")
        pdf.output(pdf_path)
        
        logger.info(f"Generated PDF report for {date_str}")
        
        # Update report data with PDF file path
        if 'files' not in report_data:
            report_data['files'] = {}
        
        report_data['files']['pdf_path'] = os.path.join('pdf_reports', f"daily_report_{date_str}.pdf")
        report_data['files']['pdf_exists'] = True
        
        # Update the JSON file
        json_dir = os.path.join('exports', 'daily_reports')
        json_path = os.path.join(json_dir, f"daily_report_{date_str}.json")
        
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return pdf_path
    
    except Exception as e:
        logger.error(f"Error generating PDF report for {date_str}: {e}")
        logger.error(traceback.format_exc())
        return None

def generate_excel_report(date_str, report_data=None):
    """
    Generate an Excel report for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        report_data (dict): Report data (if None, will be generated)
        
    Returns:
        str: Path to generated Excel file
    """
    try:
        # Create export directory
        excel_dir = os.path.join('exports', 'excel_reports')
        os.makedirs(excel_dir, exist_ok=True)
        
        # Generate report data if not provided
        if not report_data:
            report_data = generate_daily_driver_report(date_str)
        
        # Parse date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Create Excel writer
        excel_path = os.path.join(excel_dir, f"daily_report_{date_str}.xlsx")
        writer = pd.ExcelWriter(excel_path, engine='openpyxl')
        
        # Create summary sheet
        summary_data = {
            'Metric': [
                'Total Drivers',
                'On Time Drivers',
                'Late Drivers',
                'Early End Drivers',
                'Not On Job Drivers',
                'On Time Percentage'
            ],
            'Count': [
                report_data['summary']['total_drivers'],
                report_data['summary']['on_time_drivers'],
                report_data['summary']['late_drivers'],
                report_data['summary']['early_end_drivers'],
                report_data['summary']['not_on_job_drivers'],
                f"{round((report_data['summary']['on_time_drivers'] / report_data['summary']['total_drivers'] * 100) if report_data['summary']['total_drivers'] > 0 else 0, 1)}%"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Create late drivers sheet if any
        if report_data['summary']['late_drivers'] > 0 and report_data.get('late_drivers'):
            late_drivers_data = []
            
            for driver in report_data['late_drivers']:
                late_drivers_data.append({
                    'Driver': driver.get('driver_name', 'N/A'),
                    'Asset': driver.get('asset_id', 'N/A'),
                    'Scheduled Start': driver.get('scheduled_start', 'N/A'),
                    'Actual Start': driver.get('actual_start_display', 'N/A'),
                    'Minutes Late': driver.get('minutes_late', 'N/A'),
                    'Job Site': driver.get('assigned_job_site', 'N/A')
                })
            
            if late_drivers_data:
                late_drivers_df = pd.DataFrame(late_drivers_data)
                late_drivers_df.to_excel(writer, sheet_name='Late Drivers', index=False)
        
        # Create early end drivers sheet if any
        if report_data['summary']['early_end_drivers'] > 0 and report_data.get('early_end_drivers'):
            early_end_data = []
            
            for driver in report_data['early_end_drivers']:
                early_end_data.append({
                    'Driver': driver.get('driver_name', 'N/A'),
                    'Asset': driver.get('asset_id', 'N/A'),
                    'Scheduled End': driver.get('scheduled_end', 'N/A'),
                    'Actual End': driver.get('actual_end_display', 'N/A'),
                    'Minutes Early': driver.get('minutes_early', 'N/A'),
                    'Job Site': driver.get('assigned_job_site', 'N/A')
                })
            
            if early_end_data:
                early_end_df = pd.DataFrame(early_end_data)
                early_end_df.to_excel(writer, sheet_name='Early End Drivers', index=False)
        
        # Create not on job drivers sheet if any
        if report_data['summary']['not_on_job_drivers'] > 0 and report_data.get('not_on_job_drivers'):
            not_on_job_data = []
            
            for driver in report_data['not_on_job_drivers']:
                not_on_job_data.append({
                    'Driver': driver.get('driver_name', 'N/A'),
                    'Asset': driver.get('asset_id', 'N/A'),
                    'Job Site': driver.get('assigned_job_site', 'N/A'),
                    'Status': driver.get('status', 'Unknown'),
                    'Reason': driver.get('status_reason', 'Unknown')
                })
            
            if not_on_job_data:
                not_on_job_df = pd.DataFrame(not_on_job_data)
                not_on_job_df.to_excel(writer, sheet_name='Not On Job Drivers', index=False)
        
        # Create all drivers sheet
        all_drivers_data = []
        
        for driver in report_data.get('all_drivers', []):
            all_drivers_data.append({
                'Driver': driver.get('driver_name', 'N/A'),
                'Asset': driver.get('asset_id', 'N/A'),
                'Status': driver.get('status', 'Unknown'),
                'Scheduled Start': driver.get('scheduled_start', 'N/A'),
                'Actual Start': driver.get('actual_start_display', 'N/A'),
                'Scheduled End': driver.get('scheduled_end', 'N/A'),
                'Actual End': driver.get('actual_end_display', 'N/A'),
                'Job Site': driver.get('assigned_job_site', 'N/A'),
                'Reason': driver.get('status_reason', 'N/A')
            })
        
        if all_drivers_data:
            all_drivers_df = pd.DataFrame(all_drivers_data)
            all_drivers_df.to_excel(writer, sheet_name='All Drivers', index=False)
        
        # Save Excel file
        writer.close()
        
        logger.info(f"Generated Excel report for {date_str}")
        
        # Update report data with Excel file path
        if 'files' not in report_data:
            report_data['files'] = {}
        
        report_data['files']['excel_path'] = os.path.join('excel_reports', f"daily_report_{date_str}.xlsx")
        report_data['files']['excel_exists'] = True
        
        # Update the JSON file
        json_dir = os.path.join('exports', 'daily_reports')
        json_path = os.path.join(json_dir, f"daily_report_{date_str}.json")
        
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return excel_path
    
    except Exception as e:
        logger.error(f"Error generating Excel report for {date_str}: {e}")
        logger.error(traceback.format_exc())
        return None

def generate_email_html(report_data, date_str):
    """
    Generate HTML content for the daily report email
    
    Args:
        report_data (dict): Report data
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        str: HTML content
    """
    try:
        # Parse date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Extract summary counts
        total_drivers = report_data['summary']['total_drivers']
        on_time_drivers = report_data['summary']['on_time_drivers']
        late_drivers = report_data['summary']['late_drivers']
        early_end_drivers = report_data['summary']['early_end_drivers']
        not_on_job_drivers = report_data['summary']['not_on_job_drivers']
        
        # Calculate on-time percentage
        on_time_percent = round((on_time_drivers / total_drivers * 100) if total_drivers > 0 else 0, 1)
        
        # Generate summary HTML
        summary_html = f"""
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background-color: #f2f2f2;">
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Metric</th>
                <th style="text-align: right; padding: 8px; border: 1px solid #ddd;">Count</th>
            </tr>
            <tr>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">Total Drivers</td>
                <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{total_drivers}</td>
            </tr>
            <tr>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">On Time Drivers</td>
                <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{on_time_drivers}</td>
            </tr>
            <tr>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">Late Drivers</td>
                <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{late_drivers}</td>
            </tr>
            <tr>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">Early End Drivers</td>
                <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{early_end_drivers}</td>
            </tr>
            <tr>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">Not On Job Drivers</td>
                <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{not_on_job_drivers}</td>
            </tr>
            <tr>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">On Time Percentage</td>
                <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{on_time_percent}%</td>
            </tr>
        </table>
        """
        
        # Generate issue tables if there are issues
        issue_tables = ""
        
        # Late drivers table
        if late_drivers > 0 and 'late_drivers' in report_data:
            late_table = """
            <h3 style="color: #ff9900;">Late Drivers</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Driver</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Asset</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Scheduled Start</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Actual Start</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Minutes Late</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Job Site</th>
                </tr>
            """
            
            for driver in report_data['late_drivers']:
                late_table += f"""
                <tr>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('driver_name', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('asset_id', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('scheduled_start', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('actual_start_display', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('minutes_late', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('assigned_job_site', 'N/A')}</td>
                </tr>
                """
            
            late_table += "</table>"
            issue_tables += late_table
        
        # Early end drivers table
        if early_end_drivers > 0 and 'early_end_drivers' in report_data:
            early_table = """
            <h3 style="color: #3399ff;">Early End Drivers</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Driver</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Asset</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Scheduled End</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Actual End</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Minutes Early</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Job Site</th>
                </tr>
            """
            
            for driver in report_data['early_end_drivers']:
                early_table += f"""
                <tr>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('driver_name', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('asset_id', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('scheduled_end', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('actual_end_display', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('minutes_early', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('assigned_job_site', 'N/A')}</td>
                </tr>
                """
            
            early_table += "</table>"
            issue_tables += early_table
        
        # Not on job drivers table
        if not_on_job_drivers > 0 and 'not_on_job_drivers' in report_data:
            noj_table = """
            <h3 style="color: #ff3333;">Not On Job Drivers</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Driver</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Asset</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Job Site</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Reason</th>
                </tr>
            """
            
            for driver in report_data['not_on_job_drivers']:
                noj_table += f"""
                <tr>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('driver_name', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('asset_id', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('assigned_job_site', 'N/A')}</td>
                    <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('status_reason', 'Unknown')}</td>
                </tr>
                """
            
            noj_table += "</table>"
            issue_tables += noj_table
        
        # Build complete HTML
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    h1 {{ color: #0056b3; margin-bottom: 20px; }}
                    h2 {{ color: #0056b3; margin-top: 30px; margin-bottom: 10px; }}
                    h3 {{ margin-top: 20px; margin-bottom: 10px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; }}
                    th {{ background-color: #f2f2f2; text-align: left; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .summary {{ margin-bottom: 30px; }}
                    .note {{ color: #666; font-style: italic; }}
                </style>
            </head>
            <body>
                <h1>Daily Driver Report - {formatted_date}</h1>
                
                <div class="summary">
                    <h2>Summary</h2>
                    {summary_html}
                </div>
                
                {issue_tables}
                
                <div class="note">
                    <p>This report is generated automatically by the TRAXORA Fleet Management System.</p>
                    <p>For questions or assistance, please contact the Fleet Management team.</p>
                    <p>PDF and Excel reports are attached for detailed analysis.</p>
                </div>
            </body>
        </html>
        """
        
        return html_content
    
    except Exception as e:
        logger.error(f"Error generating email HTML: {e}")
        logger.error(traceback.format_exc())
        return f"<html><body><h1>Error generating report</h1><p>{str(e)}</p></body></html>"

def email_report(date_str, recipients, report_data=None):
    """
    Email the daily driver report to specified recipients
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        recipients (list or str): List of email addresses or comma-separated string
        report_data (dict): Report data (if None, will be generated)
        
    Returns:
        bool: Success status
    """
    try:
        # Get SendGrid API key from environment
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        
        if not sendgrid_api_key:
            email_logger.error("SendGrid API key not found in environment")
            return False
        
        # Generate report data if not provided
        if not report_data:
            report_data = generate_daily_driver_report(date_str)
        
        # Generate PDF and Excel reports if not already generated
        pdf_path = generate_pdf_report(date_str, report_data)
        excel_path = generate_excel_report(date_str, report_data)
        
        # Parse date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Generate email HTML
        html_content = generate_email_html(report_data, date_str)
        
        # Prepare recipient list
        if isinstance(recipients, str):
            recipients = [email.strip() for email in recipients.split(',') if email.strip()]
        
        # Initialize SendGrid client
        sg = SendGridAPIClient(sendgrid_api_key)
        
        # Prepare email
        from_email = Email("telematics@ragleinc.com", "Ragle Fleet Telematics")
        subject = f"Daily Driver Report - {formatted_date}"
        
        # Create mail for each recipient
        for recipient in recipients:
            mail = Mail(
                from_email=from_email,
                to_emails=To(recipient),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Attach PDF if available
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    pdf_data = base64.b64encode(f.read()).decode()
                    
                    pdf_attachment = Attachment()
                    pdf_attachment.file_content = FileContent(pdf_data)
                    pdf_attachment.file_name = FileName(f"daily_report_{date_str}.pdf")
                    pdf_attachment.file_type = FileType("application/pdf")
                    pdf_attachment.disposition = Disposition("attachment")
                    
                    mail.attachment = pdf_attachment
            
            # Attach Excel if available
            if excel_path and os.path.exists(excel_path):
                with open(excel_path, 'rb') as f:
                    excel_data = base64.b64encode(f.read()).decode()
                    
                    excel_attachment = Attachment()
                    excel_attachment.file_content = FileContent(excel_data)
                    excel_attachment.file_name = FileName(f"daily_report_{date_str}.xlsx")
                    excel_attachment.file_type = FileType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    excel_attachment.disposition = Disposition("attachment")
                    
                    mail.attachment = excel_attachment
            
            # Send email
            try:
                response = sg.send(mail)
                email_logger.info(f"Sent email to {recipient} for date {date_str}")
                email_logger.info(f"Status code: {response.status_code}")
            except Exception as e:
                email_logger.error(f"Error sending email to {recipient}: {e}")
                email_logger.error(traceback.format_exc())
        
        return True
    
    except Exception as e:
        email_logger.error(f"Error emailing report: {e}")
        email_logger.error(traceback.format_exc())
        return False

def process_date(date_str, email=False, recipients=None):
    """
    Process a specific date - generate report, PDF, Excel, and optionally email
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        email (bool): Whether to email the report
        recipients (str or list): Email recipients
        
    Returns:
        dict: Processing results
    """
    try:
        # Generate report data
        report_data = generate_daily_driver_report(date_str)
        
        if not report_data:
            logger.error(f"Failed to generate report data for {date_str}")
            return {
                'status': 'error',
                'message': 'Failed to generate report data'
            }
        
        # Generate PDF and Excel reports
        pdf_path = generate_pdf_report(date_str, report_data)
        excel_path = generate_excel_report(date_str, report_data)
        
        result = {
            'status': 'success',
            'date': date_str,
            'pdf_path': pdf_path,
            'excel_path': excel_path,
            'summary': report_data['summary']
        }
        
        # Email report if requested
        if email and recipients:
            email_success = email_report(date_str, recipients, report_data)
            result['email'] = {
                'status': 'success' if email_success else 'error',
                'recipients': recipients
            }
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing date {date_str}: {e}")
        logger.error(traceback.format_exc())
        return {
            'status': 'error',
            'message': str(e)
        }