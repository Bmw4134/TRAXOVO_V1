#!/usr/bin/env python3
"""
Generate PDF Report for Daily Driver Data

This script generates a PDF report for the May 16, 2025 driver attendance data
using ReportLab.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def generate_pdf_report(date_str='2025-05-16'):
    """Generate PDF report for the specified date"""
    logger.info(f"Generating PDF report for {date_str}")
    
    try:
        # Ensure output directories exist
        reports_dir = Path('reports/daily_drivers')
        exports_dir = Path('exports/daily_reports')
        reports_dir.mkdir(parents=True, exist_ok=True)
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for JSON data
        json_path = reports_dir / f"daily_report_{date_str}.json"
        if not json_path.exists():
            logger.error(f"JSON data file not found: {json_path}")
            return False
            
        # Load report data
        with open(json_path, 'r') as f:
            report_data = json.load(f)
            
        # Output file paths
        pdf_path = reports_dir / f"daily_report_{date_str}.pdf"
        export_pdf = exports_dir / f"{date_str}_DailyDriverReport.pdf"
        legacy_pdf = exports_dir / f"daily_report_{date_str}.pdf"
        
        # Format date for display
        display_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%A, %B %d, %Y')
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Customize title style
        title_style.fontName = 'Helvetica-Bold'
        title_style.fontSize = 16
        title_style.spaceAfter = 0.3 * inch
        
        # Create PDF elements
        elements = []
        
        # Add title
        elements.append(Paragraph(f"Daily Driver Report: {display_date}", title_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add summary
        elements.append(Paragraph("Summary", heading_style))
        
        # Extract summary data
        summary = report_data.get('summary', {})
        total = summary.get('total', 0)
        late = summary.get('late', 0)
        early_end = summary.get('early_end', 0)
        not_on_job = summary.get('not_on_job', 0)
        on_time = summary.get('on_time', 0)
        
        # Create summary table
        summary_data = [
            ["Total Drivers", "Late", "Early End", "Not On Job", "On Time"],
            [
                total,
                f"{late} ({late/total*100:.1f}%)" if total > 0 else "0 (0.0%)",
                f"{early_end} ({early_end/total*100:.1f}%)" if total > 0 else "0 (0.0%)",
                f"{not_on_job} ({not_on_job/total*100:.1f}%)" if total > 0 else "0 (0.0%)",
                f"{on_time} ({on_time/total*100:.1f}%)" if total > 0 else "0 (0.0%)"
            ]
        ]
        
        summary_table = Table(summary_data, colWidths=[1.6*inch, 1.6*inch, 1.6*inch, 1.6*inch, 1.6*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add driver details
        elements.append(Paragraph("Driver Details", heading_style))
        
        # Get driver data
        drivers = report_data.get('drivers', [])
        
        if drivers:
            # Create driver table data
            driver_data = [
                ["Driver Name", "Asset", "Job Site", "Scheduled Start", "Scheduled End", "Actual Start", "Actual End", "Status", "Reason"]
            ]
            
            for driver in drivers:
                driver_data.append([
                    driver.get('driver_name', ''),
                    driver.get('asset_id', ''),
                    driver.get('job_site', ''),
                    driver.get('scheduled_start', ''),
                    driver.get('scheduled_end', ''),
                    driver.get('actual_start', ''),
                    driver.get('actual_end', ''),
                    driver.get('status', ''),
                    driver.get('status_reason', '')
                ])
            
            # Create driver table
            driver_table = Table(driver_data, colWidths=[1.1*inch, 0.8*inch, 1.0*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.8*inch, 1.5*inch])
            
            # Set table style
            driver_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (8, 1), (8, -1), 'LEFT')  # Left-align the reason column
            ]))
            
            # Add conditional formatting for status
            for i, driver in enumerate(drivers, 1):
                status = driver.get('status', '')
                if status == 'Late':
                    driver_table.setStyle(TableStyle([
                        ('BACKGROUND', (7, i), (7, i), colors.lightcoral)
                    ]))
                elif status == 'Early End':
                    driver_table.setStyle(TableStyle([
                        ('BACKGROUND', (7, i), (7, i), colors.lightgoldenrodyellow)
                    ]))
                elif status == 'Not On Job':
                    driver_table.setStyle(TableStyle([
                        ('BACKGROUND', (7, i), (7, i), colors.lightcoral)
                    ]))
                elif status == 'On Time':
                    driver_table.setStyle(TableStyle([
                        ('BACKGROUND', (7, i), (7, i), colors.lightgreen)
                    ]))
            
            elements.append(driver_table)
        else:
            elements.append(Paragraph("No driver data available for this date.", normal_style))
        
        # Build the PDF
        doc.build(elements)
        logger.info(f"PDF report generated at {pdf_path}")
        
        # Create copies for web interface
        import shutil
        shutil.copy(pdf_path, export_pdf)
        shutil.copy(pdf_path, legacy_pdf)
        logger.info(f"PDF copies created at {export_pdf} and {legacy_pdf}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    generate_pdf_report()