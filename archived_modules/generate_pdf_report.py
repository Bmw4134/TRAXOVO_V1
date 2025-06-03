#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | PDF Report Generator

This module generates PDF reports from Daily Driver Report data with
identity verification status indicators and proper data validation.
"""

import os
import sys
import json
import logging
from datetime import datetime
import traceback
from typing import Dict, List, Any, Optional, Tuple
import tempfile
import base64

# PDF generation libraries
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Make sure logs directory exists
os.makedirs('logs', exist_ok=True)

# Add file handler for this script
file_handler = logging.FileHandler('logs/generate_pdf_report.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Create reports directory if it doesn't exist
os.makedirs('reports/pdf', exist_ok=True)

def create_status_pie_chart(report_data: Dict[str, Any], width=300, height=200) -> Drawing:
    """
    Create a pie chart showing the distribution of driver statuses
    
    Args:
        report_data (Dict[str, Any]): The report data
        width (int): Width of the chart
        height (int): Height of the chart
        
    Returns:
        Drawing: The pie chart drawing
    """
    # Create drawing
    drawing = Drawing(width, height)
    
    # Get counts from summary
    summary = report_data.get('summary', {})
    on_time = summary.get('on_time', 0)
    late = summary.get('late', 0)
    early_end = summary.get('early_end', 0)
    not_on_job = summary.get('not_on_job', 0)
    
    # Data for pie chart
    data = []
    labels = []
    
    if on_time > 0:
        data.append(on_time)
        labels.append('On Time')
        
    if late > 0:
        data.append(late)
        labels.append('Late')
        
    if early_end > 0:
        data.append(early_end)
        labels.append('Early End')
        
    if not_on_job > 0:
        data.append(not_on_job)
        labels.append('Not On Job')
    
    # Create pie chart
    pie = Pie()
    pie.x = width // 2
    pie.y = height // 2
    pie.width = min(width, height) * 0.8
    pie.height = min(width, height) * 0.8
    pie.data = data
    pie.labels = labels
    pie.slices.strokeWidth = 0.5
    
    # Colors for different statuses
    colors_list = [colors.green, colors.red, colors.orange, colors.purple]
    
    # Set colors for each slice
    for i, color in enumerate(colors_list[:len(data)]):
        pie.slices[i].fillColor = color
    
    drawing.add(pie)
    return drawing

def create_verification_pie_chart(report_data: Dict[str, Any], width=300, height=200) -> Drawing:
    """
    Create a pie chart showing the verification status of drivers
    
    Args:
        report_data (Dict[str, Any]): The report data
        width (int): Width of the chart
        height (int): Height of the chart
        
    Returns:
        Drawing: The pie chart drawing
    """
    # Create drawing
    drawing = Drawing(width, height)
    
    # Count verified and unverified drivers
    drivers = report_data.get('drivers', [])
    verified_count = sum(1 for d in drivers if d.get('identity_verified', False))
    unverified_count = len(drivers) - verified_count
    
    # Data for pie chart
    data = []
    labels = []
    
    if verified_count > 0:
        data.append(verified_count)
        labels.append('Verified')
        
    if unverified_count > 0:
        data.append(unverified_count)
        labels.append('Unverified')
    
    # Create pie chart
    pie = Pie()
    pie.x = width // 2
    pie.y = height // 2
    pie.width = min(width, height) * 0.8
    pie.height = min(width, height) * 0.8
    pie.data = data
    pie.labels = labels
    pie.slices.strokeWidth = 0.5
    
    # Colors for verification status
    colors_list = [colors.blue, colors.darkgray]
    
    # Set colors for each slice
    for i, color in enumerate(colors_list[:len(data)]):
        pie.slices[i].fillColor = color
    
    drawing.add(pie)
    return drawing

def generate_pdf_report(date_str: str, report_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Generate a PDF report for the Daily Driver Report
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        report_data (Dict[str, Any]): The report data
        output_path (Optional[str]): Output path for the PDF, defaults to reports/pdf/daily_report_{date_str}.pdf
        
    Returns:
        str: Path to the generated PDF
    """
    logger.info(f"Generating PDF report for {date_str}")
    
    # Determine output path
    if not output_path:
        output_path = f"reports/pdf/daily_report_{date_str}.pdf"
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(letter),
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    # Get sample stylesheet
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=4
    )
    
    # Create elements for PDF
    elements = []
    
    # Add title
    report_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')
    elements.append(Paragraph(f"DAILY DRIVER REPORT: {report_date}", title_style))
    
    # Add GENIUS CORE verification notice
    verification_status = report_data.get('metadata', {}).get('identity_verification', {})
    
    if verification_status:
        signature = verification_status.get('signature', '')
        if 'IDENTITY-VERIFIED' in signature:
            elements.append(Paragraph("GENIUS CORE: Identity Verification PASSED", subtitle_style))
        else:
            elements.append(Paragraph("GENIUS CORE: Identity Verification NOT VERIFIED", subtitle_style))
    
    elements.append(Spacer(1, 12))
    
    # Add summary
    summary = report_data.get('summary', {})
    total = summary.get('total', 0)
    on_time = summary.get('on_time', 0)
    late = summary.get('late', 0)
    early_end = summary.get('early_end', 0)
    not_on_job = summary.get('not_on_job', 0)
    
    summary_data = [
        ['Summary', 'Count', 'Percentage'],
        ['Total Drivers', str(total), '100%'],
        ['On Time', str(on_time), f"{on_time/total*100:.1f}%" if total > 0 else "0%"],
        ['Late', str(late), f"{late/total*100:.1f}%" if total > 0 else "0%"],
        ['Early End', str(early_end), f"{early_end/total*100:.1f}%" if total > 0 else "0%"],
        ['Not On Job', str(not_on_job), f"{not_on_job/total*100:.1f}%" if total > 0 else "0%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[100, 50, 80])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    # Add charts and summary side by side
    elements.append(Paragraph("Report Summary", header_style))
    
    # Create status chart
    status_chart = create_status_pie_chart(report_data)
    verification_chart = create_verification_pie_chart(report_data)
    
    # Table for summary and charts
    charts_table_data = [
        [summary_table, status_chart, verification_chart],
        ["", "Status Distribution", "Identity Verification"]
    ]
    
    charts_table = Table(charts_table_data, colWidths=[230, 300, 300])
    charts_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('TOPPADDING', (0, 1), (-1, 1), 5)
    ]))
    
    elements.append(charts_table)
    elements.append(Spacer(1, 20))
    
    # Add driver details
    elements.append(Paragraph("Driver Details", header_style))
    
    # Prepare driver data
    drivers = report_data.get('drivers', [])
    
    if drivers:
        # Define table headers
        driver_table_data = [
            ['Driver Name', 'Status', 'Asset ID', 'Job Site', 'Scheduled Start', 'Actual Start', 'Verified']
        ]
        
        # Add driver rows
        for driver in drivers:
            name = driver.get('driver_name', '')
            status = driver.get('status', '')
            asset_id = driver.get('asset_id', '')
            job_site = driver.get('assigned_job_site', '')
            scheduled_start = driver.get('scheduled_start_time', '')
            actual_start = driver.get('actual_start_time', '')
            verified = 'Yes' if driver.get('identity_verified', False) else 'No'
            
            driver_table_data.append([name, status, asset_id, job_site, scheduled_start, actual_start, verified])
        
        # Create driver table
        driver_table = Table(driver_table_data, repeatRows=1)
        
        # Style the table
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (6, 1), (6, -1), 'CENTER')
        ]
        
        # Color rows based on status
        for i, row in enumerate(driver_table_data[1:], 1):
            status = row[1]
            if status == 'Late':
                table_style.append(('BACKGROUND', (1, i), (1, i), colors.lightcoral))
            elif status == 'Early End':
                table_style.append(('BACKGROUND', (1, i), (1, i), colors.lightyellow))
            elif status == 'Not On Job':
                table_style.append(('BACKGROUND', (1, i), (1, i), colors.lightpink))
            elif status == 'On Time':
                table_style.append(('BACKGROUND', (1, i), (1, i), colors.lightgreen))
                
            # Add verification status color
            verified = row[6]
            if verified == 'Yes':
                table_style.append(('BACKGROUND', (6, i), (6, i), colors.lightblue))
            else:
                table_style.append(('BACKGROUND', (6, i), (6, i), colors.lightgrey))
        
        driver_table.setStyle(TableStyle(table_style))
        elements.append(driver_table)
    else:
        elements.append(Paragraph("No driver data available", normal_style))
    
    # Add notes and explanations
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Report Notes", header_style))
    
    notes = [
        "Late: Driver arrived more than 15 minutes after scheduled start time.",
        "Early End: Driver departed more than 30 minutes before scheduled end time.",
        "Not On Job: Driver not detected at assigned job site.",
        "Verified: Driver identity confirmed against employment records."
    ]
    
    for note in notes:
        elements.append(Paragraph(f"• {note}", small_style))
    
    # Add generated timestamp and verification information
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", small_style))
    
    if verification_status:
        timestamp = verification_status.get('timestamp', '')
        if timestamp:
            elements.append(Paragraph(f"Identity Verification: {timestamp}", small_style))
        
        verified_count = verification_status.get('verified_count', 0)
        unverified_count = verification_status.get('unverified_count', 0)
        if verified_count > 0 or unverified_count > 0:
            elements.append(Paragraph(f"Identity Statistics: {verified_count} verified, {unverified_count} unverified", small_style))
    
    # Build the PDF
    try:
        doc.build(elements)
        logger.info(f"PDF report saved to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error building PDF: {e}")
        logger.error(traceback.format_exc())
        raise

def generate_pdf_from_date(date_str: str, use_verified: bool = True) -> str:
    """
    Generate a PDF report for a specific date
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        use_verified (bool): Whether to use the verified report if available
        
    Returns:
        str: Path to the generated PDF
    """
    logger.info(f"Generating PDF report for {date_str} (use_verified={use_verified})")
    
    # Determine report path
    if use_verified:
        # Try identity verified report first
        report_path = f"reports/daily_drivers/daily_report_{date_str}_identity_verified.json"
        
        # If not available, try regular verified report
        if not os.path.exists(report_path):
            report_path = f"reports/daily_drivers/daily_report_{date_str}_verified.json"
            
        # If still not available, fall back to regular report
        if not os.path.exists(report_path):
            report_path = f"reports/daily_drivers/daily_report_{date_str}.json"
    else:
        # Use regular report
        report_path = f"reports/daily_drivers/daily_report_{date_str}.json"
    
    # Check if report exists
    if not os.path.exists(report_path):
        logger.error(f"Report not found: {report_path}")
        raise FileNotFoundError(f"Report not found: {report_path}")
    
    # Load report data
    with open(report_path, 'r') as f:
        report_data = json.load(f)
    
    # Determine output path
    if use_verified:
        output_path = f"reports/pdf/daily_report_{date_str}_verified.pdf"
    else:
        output_path = f"reports/pdf/daily_report_{date_str}.pdf"
    
    # Generate PDF
    return generate_pdf_report(date_str, report_data, output_path)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TRAXORA GENIUS CORE | PDF Report Generator')
    parser.add_argument('date', help='Date to process in YYYY-MM-DD format')
    parser.add_argument('--original', action='store_true', help='Use original (non-verified) report')
    
    args = parser.parse_args()
    
    try:
        pdf_path = generate_pdf_from_date(args.date, not args.original)
        print(f"PDF report generated successfully: {pdf_path}")
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()