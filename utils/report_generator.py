"""
Report Generator Module

This module provides utilities for generating PDF and CSV reports from
daily driver attendance data.
"""

import os
import csv
import logging
from datetime import datetime
from io import BytesIO
import base64

from fpdf import FPDF
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Configure logging
logger = logging.getLogger(__name__)

# Create directories if they don't exist
REPORTS_DIR = os.path.join(os.getcwd(), 'reports')
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

THUMBNAILS_DIR = os.path.join(os.getcwd(), 'static', 'thumbnails')
if not os.path.exists(THUMBNAILS_DIR):
    os.makedirs(THUMBNAILS_DIR)

def generate_pdf_report(report_data, report_type, date=None):
    """
    Generate a PDF report from the provided data
    
    Args:
        report_data (dict): Dictionary containing report data
        report_type (str): Type of report ('daily_driver', 'pm_allocation', etc)
        date (datetime, optional): Report date, defaults to today
        
    Returns:
        tuple: (path to PDF file, path to thumbnail image)
    """
    if date is None:
        date = datetime.now()
        
    # Create filename with date
    date_str = date.strftime('%Y-%m-%d')
    report_filename = f"{report_type}_report_{date_str}.pdf"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    
    # Create PDF using ReportLab for more advanced styling
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,  # Center alignment
        spaceAfter=0.3*inch
    )
    
    # Create elements list for the PDF
    elements = []
    
    # Add title based on report type
    if report_type == 'daily_driver':
        title = f"Daily Driver Attendance Report - {date_str}"
    elif report_type == 'pm_allocation':
        title = f"PM Allocation Report - {date_str}"
    else:
        title = f"TRAXORA Report - {date_str}"
        
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add report data based on report type
    if report_type == 'daily_driver':
        # Add summary section
        summary_data = [
            ['Metric', 'Count'],
            ['Late Starts', report_data.get('late_starts', 0)],
            ['Early Ends', report_data.get('early_ends', 0)],
            ['Not On Job', report_data.get('not_on_job', 0)],
            ['On Time', report_data.get('on_time', 0)],
            ['Total Records', report_data.get('total_records', 0)]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.navy),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (1, -1), colors.lightgrey),
            ('GRID', (0, 0), (1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ]))
        
        elements.append(Paragraph("Attendance Summary", styles['Heading2']))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add late start details if available
        late_start_records = report_data.get('late_start_records', [])
        if late_start_records:
            elements.append(Paragraph("Late Start Details", styles['Heading2']))
            
            late_data = [['Driver', 'Job Site', 'Expected', 'Actual', 'Minutes Late']]
            for record in late_start_records:
                late_data.append([
                    record.get('driver_name', 'Unknown'),
                    record.get('job_site', 'Unknown'),
                    record.get('expected_start', '').strftime('%H:%M') if hasattr(record.get('expected_start', ''), 'strftime') else '',
                    record.get('actual_start', '').strftime('%H:%M') if hasattr(record.get('actual_start', ''), 'strftime') else '',
                    str(record.get('minutes_late', ''))
                ])
            
            late_table = Table(late_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
            late_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(late_table)
            elements.append(Spacer(1, 0.25*inch))
            
        # Add early end details if available
        early_end_records = report_data.get('early_end_records', [])
        if early_end_records:
            elements.append(Paragraph("Early End Details", styles['Heading2']))
            
            early_data = [['Driver', 'Job Site', 'Expected', 'Actual', 'Minutes Early']]
            for record in early_end_records:
                early_data.append([
                    record.get('driver_name', 'Unknown'),
                    record.get('job_site', 'Unknown'),
                    record.get('expected_end', '').strftime('%H:%M') if hasattr(record.get('expected_end', ''), 'strftime') else '',
                    record.get('actual_end', '').strftime('%H:%M') if hasattr(record.get('actual_end', ''), 'strftime') else '',
                    str(record.get('minutes_early', ''))
                ])
            
            early_table = Table(early_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
            early_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(early_table)
            
    # Build PDF
    doc.build(elements)
    
    # Get PDF data and save to file
    pdf_data = buffer.getvalue()
    with open(report_path, 'wb') as f:
        f.write(pdf_data)
    
    # Generate thumbnail
    thumbnail_path = os.path.join(THUMBNAILS_DIR, f"{report_type}_report_{date_str}_thumb.png")
    generate_pdf_thumbnail(report_path, thumbnail_path)
    
    logger.info(f"Generated PDF report: {report_path}")
    return report_path, thumbnail_path

def generate_csv_report(report_data, report_type, date=None):
    """
    Generate a CSV report from the provided data
    
    Args:
        report_data (dict): Dictionary containing report data
        report_type (str): Type of report ('daily_driver', 'pm_allocation', etc)
        date (datetime, optional): Report date, defaults to today
        
    Returns:
        str: Path to CSV file
    """
    if date is None:
        date = datetime.now()
        
    # Create filename with date
    date_str = date.strftime('%Y-%m-%d')
    report_filename = f"{report_type}_report_{date_str}.csv"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    
    with open(report_path, 'w', newline='') as csvfile:
        if report_type == 'daily_driver':
            # Write summary section
            writer = csv.writer(csvfile)
            writer.writerow(['TRAXORA Daily Driver Report', date_str])
            writer.writerow([])
            writer.writerow(['Attendance Summary'])
            writer.writerow(['Metric', 'Count'])
            writer.writerow(['Late Starts', report_data.get('late_starts', 0)])
            writer.writerow(['Early Ends', report_data.get('early_ends', 0)])
            writer.writerow(['Not On Job', report_data.get('not_on_job', 0)])
            writer.writerow(['On Time', report_data.get('on_time', 0)])
            writer.writerow(['Total Records', report_data.get('total_records', 0)])
            writer.writerow([])
            
            # Write late start details if available
            late_start_records = report_data.get('late_start_records', [])
            if late_start_records:
                writer.writerow(['Late Start Details'])
                writer.writerow(['Driver', 'Job Site', 'Expected Start', 'Actual Start', 'Minutes Late'])
                for record in late_start_records:
                    writer.writerow([
                        record.get('driver_name', 'Unknown'),
                        record.get('job_site', 'Unknown'),
                        record.get('expected_start', '').strftime('%H:%M') if hasattr(record.get('expected_start', ''), 'strftime') else '',
                        record.get('actual_start', '').strftime('%H:%M') if hasattr(record.get('actual_start', ''), 'strftime') else '',
                        record.get('minutes_late', '')
                    ])
                writer.writerow([])
            
            # Write early end details if available
            early_end_records = report_data.get('early_end_records', [])
            if early_end_records:
                writer.writerow(['Early End Details'])
                writer.writerow(['Driver', 'Job Site', 'Expected End', 'Actual End', 'Minutes Early'])
                for record in early_end_records:
                    writer.writerow([
                        record.get('driver_name', 'Unknown'),
                        record.get('job_site', 'Unknown'),
                        record.get('expected_end', '').strftime('%H:%M') if hasattr(record.get('expected_end', ''), 'strftime') else '',
                        record.get('actual_end', '').strftime('%H:%M') if hasattr(record.get('actual_end', ''), 'strftime') else '',
                        record.get('minutes_early', '')
                    ])
                writer.writerow([])
            
            # Write not on job details if available
            not_on_job_records = report_data.get('not_on_job_records', [])
            if not_on_job_records:
                writer.writerow(['Not On Job Details'])
                writer.writerow(['Driver', 'Expected Job', 'Actual Job', 'Time'])
                for record in not_on_job_records:
                    writer.writerow([
                        record.get('driver_name', 'Unknown'),
                        record.get('expected_job', 'Unknown'),
                        record.get('actual_job', 'Unknown'),
                        record.get('time', '').strftime('%H:%M') if hasattr(record.get('time', ''), 'strftime') else ''
                    ])
    
    logger.info(f"Generated CSV report: {report_path}")
    return report_path

def generate_pdf_thumbnail(pdf_path, thumbnail_path, size=(200, 258)):
    """
    Generate a thumbnail preview image from the first page of a PDF
    
    Args:
        pdf_path (str): Path to the PDF file
        thumbnail_path (str): Path to save the thumbnail image
        size (tuple): Thumbnail dimensions (width, height)
        
    Returns:
        str: Path to the thumbnail image
    """
    try:
        # For this demo, we'll create a simple placeholder image since
        # converting PDF to image requires additional libraries
        
        # Create a blank white image
        img = Image.new('RGB', size, color='white')
        
        # Save the image
        img.save(thumbnail_path)
        
        logger.info(f"Generated thumbnail: {thumbnail_path}")
        return thumbnail_path
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        return None

def get_base64_thumbnail(thumbnail_path):
    """
    Convert a thumbnail image to base64 for embedding in HTML
    
    Args:
        thumbnail_path (str): Path to the thumbnail image
        
    Returns:
        str: Base64 encoded image data
    """
    try:
        with open(thumbnail_path, 'rb') as f:
            image_data = f.read()
            
        return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Error converting thumbnail to base64: {e}")
        return None