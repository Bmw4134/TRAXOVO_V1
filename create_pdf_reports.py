#!/usr/bin/env python3
"""
Create PDF Reports

This script generates PDF reports for the Daily Driver Report module
for the dates specified on the command line.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger()

# Ensure exports directory exists
os.makedirs('exports/daily_reports', exist_ok=True)

def create_pdf_report(date_str, attendance_data=None):
    """
    Create a PDF report for a specific date
    """
    # If no attendance data provided, try to get it
    if attendance_data is None:
        try:
            from utils.attendance_pipeline_connector import get_attendance_data
            attendance_data = get_attendance_data(date_str, force_refresh=False)
            if not attendance_data:
                logger.error(f"No attendance data found for {date_str}")
                return False
        except Exception as e:
            logger.error(f"Error getting attendance data: {e}")
            return False
    
    # Setup output path
    pdf_path = f'exports/daily_reports/{date_str}_DailyDriverReport.pdf'
    
    try:
        # Create a PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,  # Center
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12
        )
        
        # Elements to add to the PDF
        elements = []
        
        # Title
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        elements.append(Paragraph(f"Daily Driver Report - {formatted_date}", title_style))
        
        # Summary section
        elements.append(Paragraph("Summary", heading_style))
        
        summary_data = [
            ["Total Drivers", "On Time", "Late", "Early End", "Not On Job", "Issues"],
            [
                str(attendance_data.get('total_drivers', 0)),
                str(attendance_data.get('total_drivers', 0) - attendance_data.get('late_count', 0) - attendance_data.get('missing_count', 0)),
                str(attendance_data.get('late_count', 0)),
                str(attendance_data.get('early_count', 0)),
                str(attendance_data.get('missing_count', 0)),
                str(attendance_data.get('late_count', 0) + attendance_data.get('early_count', 0) + attendance_data.get('missing_count', 0))
            ]
        ]
        
        summary_table = Table(summary_data, colWidths=[100, 80, 80, 80, 80, 80])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Late drivers section
        late_drivers = attendance_data.get('late_start_records', [])
        if late_drivers:
            elements.append(Paragraph("Late Arrivals", heading_style))
            
            late_data = [["Driver", "Asset ID", "Scheduled", "Actual", "Minutes Late", "Job Site", "Contact"]]
            
            for driver in late_drivers:
                late_data.append([
                    driver.get('driver_name', ''),
                    driver.get('asset_id', ''),
                    driver.get('scheduled_start', ''),
                    driver.get('actual_start', ''),
                    str(driver.get('minutes_late', 0)),
                    driver.get('job_site', ''),
                    driver.get('contact_info', '')
                ])
            
            late_table = Table(late_data, colWidths=[80, 60, 60, 60, 60, 60, 100])
            late_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(late_table)
            elements.append(Spacer(1, 20))
        
        # Early end section
        early_end = attendance_data.get('early_end_records', [])
        if early_end:
            elements.append(Paragraph("Early Departures", heading_style))
            
            early_data = [["Driver", "Asset ID", "Scheduled End", "Actual End", "Minutes Early", "Job Site", "Contact"]]
            
            for driver in early_end:
                early_data.append([
                    driver.get('driver_name', ''),
                    driver.get('asset_id', ''),
                    driver.get('scheduled_end', ''),
                    driver.get('actual_end', ''),
                    str(driver.get('minutes_early', 0)),
                    driver.get('job_site', ''),
                    driver.get('contact_info', '')
                ])
            
            early_table = Table(early_data, colWidths=[80, 60, 60, 60, 60, 60, 100])
            early_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(early_table)
            elements.append(Spacer(1, 20))
        
        # Not on job section
        not_on_job = attendance_data.get('not_on_job_records', [])
        if not_on_job:
            elements.append(Paragraph("Not On Job", heading_style))
            
            not_on_job_data = [["Driver", "Asset ID", "Last Seen", "Job Site", "Status", "Contact"]]
            
            for driver in not_on_job:
                not_on_job_data.append([
                    driver.get('driver_name', ''),
                    driver.get('asset_id', ''),
                    driver.get('last_seen', ''),
                    driver.get('job_site', ''),
                    'Not On Job',
                    driver.get('contact_info', '')
                ])
            
            not_on_job_table = Table(not_on_job_data, colWidths=[80, 60, 60, 60, 60, 100])
            not_on_job_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(not_on_job_table)
            elements.append(Spacer(1, 20))
        
        # Sources section
        elements.append(Paragraph("Data Sources", heading_style))
        
        source_data = [
            ["Source Type", "File"],
            ["Activity Detail", attendance_data.get('sources', {}).get('activity_file', 'N/A')],
            ["Driving History", attendance_data.get('sources', {}).get('driving_file', 'N/A')],
            ["Fleet Utilization", attendance_data.get('sources', {}).get('utilization_file', 'N/A')]
        ]
        
        source_table = Table(source_data, colWidths=[100, 400])
        source_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(source_table)
        
        # Build the document
        doc.build(elements)
        
        logger.info(f"Successfully created PDF report: {pdf_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error creating PDF report: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_pipeline_for_tomorrow():
    """
    Create automatic pipeline for tomorrow's report
    """
    # Create the script to process tomorrow's report
    script_path = 'auto_process_tomorrow.py'
    
    with open(script_path, 'w') as f:
        f.write('''#!/usr/bin/env python3
"""
Auto Process Report for Tomorrow (2025-05-20)

This script automatically processes the daily driver report
for tomorrow when the data becomes available.
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_process.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

def main():
    """Main function to process tomorrow's report"""
    logger.info("Starting auto processing for 2025-05-20")
    
    # Target date
    target_date = '2025-05-20'
    
    try:
        # Import necessary modules
        from utils.attendance_pipeline_connector import get_attendance_data
        
        # Process attendance data
        logger.info(f"Processing attendance data for {target_date}")
        attendance_data = get_attendance_data(target_date, force_refresh=True)
        
        if attendance_data:
            logger.info(f"Successfully retrieved attendance data for {target_date}")
            logger.info(f"Total drivers: {attendance_data.get('total_drivers', 0)}")
            logger.info(f"Late drivers: {attendance_data.get('late_count', 0)}")
            logger.info(f"Early departure drivers: {attendance_data.get('early_count', 0)}")
            logger.info(f"Not on job drivers: {attendance_data.get('missing_count', 0)}")
            
            # Export reports
            from create_pdf_reports import create_pdf_report
            
            # Ensure the exports directory exists
            os.makedirs('exports/daily_reports', exist_ok=True)
            
            # Create PDF reports
            logger.info(f"Creating PDF report for {target_date}")
            create_pdf_report(target_date, attendance_data)
            
            # Copy the standard report to the required format
            if os.path.exists(f'exports/daily_reports/daily_report_{target_date}.xlsx'):
                import shutil
                shutil.copy2(
                    f'exports/daily_reports/daily_report_{target_date}.xlsx',
                    f'exports/daily_reports/{target_date}_DailyDriverReport.xlsx'
                )
                logger.info(f"Created {target_date}_DailyDriverReport.xlsx")
            
            # Log any unmapped entities
            logger.info("Logging unmapped entities")
            unmapped_dir = 'logs/unmapped_entities'
            os.makedirs(unmapped_dir, exist_ok=True)
            
            # Find unmapped drivers
            unmapped_drivers = []
            all_drivers = attendance_data.get('all_drivers', [])
            
            try:
                # Check against employee data
                import pandas as pd
                employee_file = 'attached_assets/Consolidated_Employee_And_Job_Lists_Corrected.xlsx'
                if os.path.exists(employee_file):
                    employee_data = pd.read_excel(employee_file, sheet_name='Employee_Contacts')
                    employee_names = employee_data['Employee Name'].tolist()
                    
                    for driver in all_drivers:
                        driver_name = driver.get('driver_name', '')
                        if driver_name and driver_name not in employee_names:
                            unmapped_drivers.append(driver_name)
            except Exception as e:
                logger.error(f"Error finding unmapped drivers: {e}")
            
            # Write unmapped drivers to log
            with open(f'{unmapped_dir}/unmapped_drivers_{target_date}.txt', 'w') as f:
                f.write(f"# Unmapped Drivers - {target_date}\\n")
                f.write(f"# Total: {len(unmapped_drivers)}\\n\\n")
                for driver in unmapped_drivers:
                    f.write(f"{driver}\\n")
            
            logger.info(f"Logged {len(unmapped_drivers)} unmapped drivers")
            logger.info(f"Auto processing complete for {target_date}")
        else:
            logger.error(f"No attendance data available for {target_date}")
    
    except Exception as e:
        logger.error(f"Error in auto processing: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
''')
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    
    logger.info(f"Created pipeline script for tomorrow: {script_path}")
    return True

def export_april_billing():
    """
    Export the full mock April Billing
    """
    logger.info("Exporting April Billing")
    
    # Ensure billing directory exists
    os.makedirs('exports/billing', exist_ok=True)
    
    # Run the billing processor directly
    try:
        from final_billing_processor import process_and_generate_deliverables
        process_and_generate_deliverables()
        
        # Copy the exports to the required location
        source_files = ['exports/dfw_april_2025.xlsx', 'exports/hou_april_2025.xlsx', 'exports/wt_april_2025.xlsx']
        target_file = 'exports/billing/April_MockBilling_Complete.xlsx'
        
        # Create consolidated file
        with pd.ExcelWriter(target_file, engine='openpyxl') as writer:
            for source_file in source_files:
                if os.path.exists(source_file):
                    # Get division name from filename
                    division = os.path.basename(source_file).split('_')[0].upper()
                    
                    # Load data
                    df = pd.read_excel(source_file)
                    
                    # Write to consolidated file
                    df.to_excel(writer, sheet_name=division, index=False)
                    
                    logger.info(f"Added {division} data with {len(df)} rows")
        
        if os.path.exists(target_file):
            logger.info(f"Successfully created consolidated billing file: {target_file}")
            return True
        else:
            logger.error(f"Failed to create consolidated billing file: {target_file}")
            return False
    
    except Exception as e:
        logger.error(f"Error exporting April billing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Main function to process all reports
    """
    logger.info("Starting PDF report generation")
    
    # Get dates from command line
    dates = sys.argv[1:] if len(sys.argv) > 1 else ['2025-05-15', '2025-05-16', '2025-05-19']
    
    logger.info(f"Processing dates: {dates}")
    
    for date_str in dates:
        logger.info(f"Processing {date_str}")
        create_pdf_report(date_str)
    
    # Create pipeline for tomorrow
    create_pipeline_for_tomorrow()
    
    # Export April billing
    export_april_billing()
    
    logger.info("PDF report generation complete")

if __name__ == "__main__":
    main()