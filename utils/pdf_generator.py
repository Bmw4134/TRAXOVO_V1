"""
PDF and CSV Report Generator Module

This module provides utilities for generating PDF and CSV reports from
driver attendance data and other report types.
"""

import os
import csv
import logging
from datetime import datetime
from io import BytesIO
import base64
from pathlib import Path

from fpdf import FPDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Configure logging
logger = logging.getLogger(__name__)

# Create directories if they don't exist
REPORTS_DIR = os.path.join(os.getcwd(), 'static', 'reports')
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

def generate_daily_driver_pdf(report_data):
    """
    Generate a PDF report for daily driver attendance
    
    Args:
        report_data (dict): Dictionary containing report data
        
    Returns:
        BytesIO: PDF file as BytesIO object
    """
    # Get current date for the report
    report_date = report_data.get('report_date', datetime.now())
    date_str = report_date.strftime('%Y-%m-%d')
    
    # Create PDF using ReportLab
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,  # Center alignment
        spaceAfter=0.3*inch
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=0.2*inch,
        spaceAfter=0.1*inch
    )
    
    # Create elements list for the PDF
    elements = []
    
    # Add title
    elements.append(Paragraph(f"TRAXORA Daily Driver Report", title_style))
    elements.append(Paragraph(f"Date: {date_str}", styles['Italic']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add summary section
    elements.append(Paragraph("Attendance Summary", subtitle_style))
    
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
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add late start details if available
    late_start_records = report_data.get('late_start_records', [])
    if late_start_records:
        elements.append(Paragraph("Late Start Details", subtitle_style))
        
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
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
        elements.append(Paragraph("Early End Details", subtitle_style))
        
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
        elements.append(Spacer(1, 0.25*inch))
    
    # Add not on job details if available
    not_on_job_records = report_data.get('not_on_job_records', [])
    if not_on_job_records:
        elements.append(Paragraph("Not On Job Details", subtitle_style))
        
        noj_data = [['Driver', 'Expected Job', 'Actual Job', 'Time']]
        for record in not_on_job_records:
            noj_data.append([
                record.get('driver_name', 'Unknown'),
                record.get('expected_job', 'Unknown'),
                record.get('actual_job', 'Unknown'),
                record.get('time', '').strftime('%H:%M') if hasattr(record.get('time', ''), 'strftime') else ''
            ])
        
        noj_table = Table(noj_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 0.5*inch])
        noj_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(noj_table)
    
    # Add footer with timestamp
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Italic']))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Save to file
    report_filename = f"daily_driver_report_{date_str}.pdf"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    
    with open(report_path, 'wb') as f:
        f.write(pdf_data)
    
    logger.info(f"Generated PDF report: {report_path}")
    return report_path, BytesIO(pdf_data)

def generate_daily_driver_csv(report_data):
    """
    Generate a CSV report for daily driver attendance
    
    Args:
        report_data (dict): Dictionary containing report data
        
    Returns:
        str: Path to CSV file
    """
    # Get current date for the report
    report_date = report_data.get('report_date', datetime.now())
    date_str = report_date.strftime('%Y-%m-%d')
    
    # Create filename
    report_filename = f"daily_driver_report_{date_str}.csv"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    
    with open(report_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['TRAXORA Daily Driver Report', date_str])
        writer.writerow([])
        
        # Write summary
        writer.writerow(['Attendance Summary'])
        writer.writerow(['Metric', 'Count'])
        writer.writerow(['Late Starts', report_data.get('late_starts', 0)])
        writer.writerow(['Early Ends', report_data.get('early_ends', 0)])
        writer.writerow(['Not On Job', report_data.get('not_on_job', 0)])
        writer.writerow(['On Time', report_data.get('on_time', 0)])
        writer.writerow(['Total Records', report_data.get('total_records', 0)])
        writer.writerow([])
        
        # Write late start details
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
        
        # Write early end details
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
        
        # Write not on job details
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

def create_simple_pdf_thumbnail(width=200, height=258):
    """Create a simple thumbnail for PDF reports"""
    pdf = FPDF()
    pdf.add_page()
    
    # Set font and colors
    pdf.set_font("Arial", size=16)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(52, 58, 64)  # Dark background
    
    # Add title
    pdf.rect(0, 0, 210, 40, 'F')  # Header background
    pdf.set_xy(10, 15)
    pdf.cell(190, 10, "TRAXORA Daily Driver Report", 0, 1, 'C')
    
    # Summary table placeholder
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=12)
    pdf.set_xy(20, 50)
    pdf.cell(170, 10, "Attendance Summary", 0, 1, 'L')
    
    # Draw table
    pdf.set_draw_color(0, 0, 0)
    pdf.set_fill_color(200, 200, 200)
    pdf.rect(20, 65, 80, 8, 'F')
    pdf.rect(100, 65, 40, 8, 'F')
    pdf.set_xy(20, 65)
    pdf.cell(80, 8, "Metric", 1, 0, 'C')
    pdf.cell(40, 8, "Count", 1, 1, 'C')
    
    pdf.set_xy(20, 73)
    pdf.cell(80, 8, "Late Starts", 1, 0, 'L')
    pdf.cell(40, 8, "3", 1, 1, 'C')
    
    pdf.set_xy(20, 81)
    pdf.cell(80, 8, "Early Ends", 1, 0, 'L')
    pdf.cell(40, 8, "2", 1, 1, 'C')
    
    # Save to memory
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    
    # Create thumbnail
    thumbnail_path = os.path.join(REPORTS_DIR, "pdf_preview_thumbnail.png")
    
    # For a real implementation, you would convert PDF to PNG
    # Here we'll create a simple placeholder
    with open(thumbnail_path, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    return thumbnail_path

def init_reports_folder():
    """Initialize the reports folder structure"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # Create a sample thumbnail if it doesn't exist
    thumbnail_path = os.path.join(REPORTS_DIR, "pdf_preview_thumbnail.png")
    if not os.path.exists(thumbnail_path):
        create_simple_pdf_thumbnail()
    
    return True