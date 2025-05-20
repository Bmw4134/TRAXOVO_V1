"""
PDF Export Utilities for Daily Driver Reports

This module handles the creation of PDF reports from attendance data
"""

import os
import logging
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = logging.getLogger(__name__)

def export_daily_report_to_pdf(attendance_data, output_path):
    """
    Export daily attendance report to PDF
    
    Args:
        attendance_data (dict): Attendance data dictionary
        output_path (str): Output file path
        
    Returns:
        bool: Success status
    """
    # Ensure exports directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Create the PDF document
        doc = SimpleDocTemplate(
            output_path, 
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Get the sample style sheet
        styles = getSampleStyleSheet()
        
        # Create a title style
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
        
        normal_style = styles['Normal']
        
        # Elements to add to the PDF
        elements = []
        
        # Report title
        date_obj = datetime.strptime(attendance_data['date'], '%Y-%m-%d')
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
        
        # Late Arrivals section
        late_arrivals = attendance_data.get('late_start_records', [])
        if late_arrivals:
            elements.append(Paragraph("Late Arrivals", heading_style))
            
            late_data = [["Driver", "Asset", "Scheduled", "Actual", "Minutes Late", "Job Site"]]
            
            for driver in late_arrivals:
                late_data.append([
                    driver.get('driver_name', 'Unknown'),
                    driver.get('asset_id', ''),
                    driver.get('scheduled_start', ''),
                    driver.get('actual_start', ''),
                    str(driver.get('minutes_late', 0)),
                    driver.get('job_site', '')
                ])
            
            late_table = Table(late_data, colWidths=[100, 70, 90, 90, 70, 70])
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
            
        # Early Departures section
        early_departures = attendance_data.get('early_end_records', [])
        if early_departures:
            elements.append(Paragraph("Early Departures", heading_style))
            
            early_data = [["Driver", "Asset", "Scheduled End", "Actual End", "Minutes Early", "Job Site"]]
            
            for driver in early_departures:
                early_data.append([
                    driver.get('driver_name', 'Unknown'),
                    driver.get('asset_id', ''),
                    driver.get('scheduled_end', ''),
                    driver.get('actual_end', ''),
                    str(driver.get('minutes_early', 0)),
                    driver.get('job_site', '')
                ])
            
            early_table = Table(early_data, colWidths=[100, 70, 90, 90, 70, 70])
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
            
        # Not On Job section
        not_on_job = attendance_data.get('not_on_job_records', [])
        if not_on_job:
            elements.append(Paragraph("Not On Job", heading_style))
            
            not_on_job_data = [["Driver", "Asset", "Last Seen", "Job Site", "Status"]]
            
            for driver in not_on_job:
                not_on_job_data.append([
                    driver.get('driver_name', 'Unknown'),
                    driver.get('asset_id', ''),
                    driver.get('last_seen', ''),
                    driver.get('job_site', ''),
                    driver.get('status', 'Not On Job')
                ])
            
            not_on_job_table = Table(not_on_job_data, colWidths=[100, 70, 90, 70, 70])
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
            
        # File information
        elements.append(Paragraph("Report Sources", heading_style))
        
        source_data = [
            ["Source", "File"],
            ["Activity File", attendance_data.get('sources', {}).get('activity_file', 'N/A')],
            ["Driving History File", attendance_data.get('sources', {}).get('driving_file', 'N/A')],
            ["Fleet Utilization File", attendance_data.get('sources', {}).get('utilization_file', 'N/A')]
        ]
        
        source_table = Table(source_data, colWidths=[200, 300])
        source_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(source_table)
        
        # Build the document
        doc.build(elements)
        logger.info(f"Successfully exported daily report to PDF: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting daily report to PDF: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False