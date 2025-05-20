#!/usr/bin/env python3
"""
Fix Daily Driver Reports

This script diagnoses and fixes the Daily Driver Reports for all required dates
and prepares for the next workday report (2025-05-20).
"""

import os
import sys
import logging
import traceback
import pandas as pd
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure the exports directory exists
os.makedirs('exports/daily_reports', exist_ok=True)

def create_pdf_report(date_str):
    """
    Create a PDF report for a specific date using ReportLab directly
    """
    try:
        # Import needed modules
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from utils.attendance_pipeline_connector import get_attendance_data
        
        # Get attendance data for the date
        attendance_data = get_attendance_data(date_str, force_refresh=False)
        
        if not attendance_data:
            logger.error(f"No attendance data found for {date_str}")
            return False
            
        # Setup PDF path
        pdf_path = f'exports/daily_reports/daily_report_{date_str}.pdf'
        
        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,  # Center alignment
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12
        )
        
        # Elements for the PDF
        elements = []
        
        # Add title
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        report_title = f"Daily Driver Attendance Report - {formatted_date}"
        elements.append(Paragraph(report_title, title_style))
        
        # Summary section
        elements.append(Paragraph("Summary", heading_style))
        
        # Summary table
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
        
        summary_table = Table(summary_data, colWidths=[100, 70, 70, 70, 70, 70])
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
        
        # Late arrivals section
        late_records = attendance_data.get('late_start_records', [])
        if late_records:
            elements.append(Paragraph("Late Arrivals", heading_style))
            
            # Create late arrivals table
            late_headers = ["Driver", "Asset", "Scheduled", "Actual", "Minutes Late", "Job Site"]
            late_data = [late_headers]
            
            for record in late_records:
                late_data.append([
                    record.get('driver_name', ''),
                    record.get('asset_id', ''),
                    record.get('scheduled_start', ''),
                    record.get('actual_start', ''),
                    str(record.get('minutes_late', 0)),
                    record.get('job_site', '')
                ])
            
            late_table = Table(late_data, colWidths=[120, 80, 80, 80, 80, 80])
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
        
        # Early departures section
        early_records = attendance_data.get('early_end_records', [])
        if early_records:
            elements.append(Paragraph("Early Departures", heading_style))
            
            # Create early departures table
            early_headers = ["Driver", "Asset", "Scheduled End", "Actual End", "Minutes Early", "Job Site"]
            early_data = [early_headers]
            
            for record in early_records:
                early_data.append([
                    record.get('driver_name', ''),
                    record.get('asset_id', ''),
                    record.get('scheduled_end', ''),
                    record.get('actual_end', ''),
                    str(record.get('minutes_early', 0)),
                    record.get('job_site', '')
                ])
            
            early_table = Table(early_data, colWidths=[120, 80, 80, 80, 80, 80])
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
        not_on_job_records = attendance_data.get('not_on_job_records', [])
        if not_on_job_records:
            elements.append(Paragraph("Not On Job", heading_style))
            
            # Create not on job table
            not_on_job_headers = ["Driver", "Asset", "Last Seen", "Location", "Status"]
            not_on_job_data = [not_on_job_headers]
            
            for record in not_on_job_records:
                not_on_job_data.append([
                    record.get('driver_name', ''),
                    record.get('asset_id', ''),
                    record.get('last_seen', ''),
                    record.get('location', ''),
                    'Not On Job'
                ])
            
            not_on_job_table = Table(not_on_job_data, colWidths=[120, 80, 100, 150, 80])
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
        
        # Source information
        elements.append(Paragraph("Data Sources", heading_style))
        sources = attendance_data.get('sources', {})
        
        source_data = [
            ["Source Type", "File"],
            ["Activity Detail", sources.get('activity_file', 'Not specified')],
            ["Driving History", sources.get('driving_file', 'Not specified')],
            ["Fleet Utilization", sources.get('utilization_file', 'Not specified')]
        ]
        
        source_table = Table(source_data, colWidths=[150, 350])
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
        
        # Build the PDF document
        doc.build(elements)
        logger.info(f"Successfully created PDF report for {date_str}: {pdf_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating PDF report for {date_str}: {e}")
        traceback.print_exc()
        return False

def process_all_required_dates():
    """
    Process all required dates for the Daily Driver Reports
    """
    # Define all dates that need processing
    dates = ['2025-05-15', '2025-05-16', '2025-05-19', '2025-05-20']
    results = {}
    
    for date_str in dates:
        logger.info(f"Processing Daily Driver Report for {date_str}")
        
        try:
            # Import the attendance pipeline connector
            from utils.attendance_pipeline_connector import get_attendance_data
            
            # Get attendance data for this date, force refresh to ensure latest data
            attendance_data = get_attendance_data(date_str, force_refresh=True)
            
            if attendance_data:
                # Data was successfully retrieved
                logger.info(f"Successfully retrieved attendance data for {date_str}")
                logger.info(f"Total drivers: {attendance_data.get('total_drivers', 0)}")
                logger.info(f"Late drivers: {attendance_data.get('late_count', 0)}")
                logger.info(f"Early departure drivers: {attendance_data.get('early_count', 0)}")
                logger.info(f"Not on job drivers: {attendance_data.get('missing_count', 0)}")
                
                # Create PDF report
                pdf_success = create_pdf_report(date_str)
                
                # Store results
                results[date_str] = {
                    'status': 'Success',
                    'total_drivers': attendance_data.get('total_drivers', 0),
                    'late_count': attendance_data.get('late_count', 0),
                    'early_count': attendance_data.get('early_count', 0),
                    'missing_count': attendance_data.get('missing_count', 0),
                    'pdf_created': pdf_success
                }
            else:
                logger.error(f"Failed to retrieve attendance data for {date_str}")
                results[date_str] = {'status': 'Failed', 'error': 'No data returned'}
                
        except Exception as e:
            logger.error(f"Error processing {date_str}: {e}")
            traceback.print_exc()
            results[date_str] = {'status': 'Error', 'error': str(e)}
    
    # Print summary of results
    logger.info("==== Daily Driver Report Processing Summary ====")
    for date_str, result in results.items():
        logger.info(f"{date_str}: {result}")
    
    return results

if __name__ == "__main__":
    logger.info("Starting Daily Driver Reports fix")
    process_all_required_dates()
    logger.info("Completed Daily Driver Reports processing")