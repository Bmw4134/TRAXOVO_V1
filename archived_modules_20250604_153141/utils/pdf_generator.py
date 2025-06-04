"""
PDF Generator for Daily Driver Reports

This module handles the generation of PDF reports for daily driver attendance data.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Set up logging
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('logs/pdf_generator.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

def generate_driver_report_pdf(date_str, output_path=None):
    """
    Generate a PDF report for daily driver data
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        output_path (str): Optional custom output path
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        # Determine file paths
        if output_path is None:
            # Use both paths to ensure compatibility with the web interface
            report_dir = Path('reports/daily_drivers')
            export_dir = Path('exports/daily_reports')
            
            # Ensure directories exist
            report_dir.mkdir(parents=True, exist_ok=True)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = export_dir / f"{date_str}_DailyDriverReport.pdf"
            
            # Create a copy in the expected report path
            alt_output_path = export_dir / f"daily_report_{date_str}.pdf"
            
            # Also put a copy in our reports directory
            report_output_path = report_dir / f"daily_report_{date_str}.pdf"
        else:
            output_path = Path(output_path)
            alt_output_path = None
            report_output_path = None
            
        # Check for JSON data
        json_path = report_dir / f"daily_report_{date_str}.json"
        if not json_path.exists():
            json_path = export_dir / f"daily_report_{date_str}.json"
            
        if not json_path.exists():
            json_path = export_dir / f"attendance_data_{date_str}.json"
            
        if not json_path.exists():
            logger.error(f"No report data found for {date_str}")
            return None
            
        # Load report data
        with open(json_path, 'r') as f:
            report_data = json.load(f)
            
        # Format date for display
        display_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%A, %B %d, %Y')
            
        # Extract driver data
        drivers = []
        if 'drivers' in report_data:
            drivers = report_data['drivers']
        
        # Extract summary
        summary = {}
        if 'summary' in report_data:
            summary = report_data['summary']
        elif 'total' in report_data:
            summary = {
                'total': report_data.get('total', 0),
                'late': report_data.get('late', 0),
                'early_end': report_data.get('early_end', 0),
                'not_on_job': report_data.get('not_on_job', 0),
                'on_time': report_data.get('on_time', 0)
            }
            
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Set up styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Customize title style
        title_style.fontName = 'Helvetica-Bold'
        title_style.fontSize = 16
        title_style.spaceAfter = 0.3 * inch
        
        # Create custom styles
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Heading4'],
            textColor=colors.white,
            backColor=colors.darkblue,
            alignment=1
        )
        
        # Create PDF elements
        elements = []
        
        # Add title
        elements.append(Paragraph(f"Daily Driver Report: {display_date}", title_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add summary
        elements.append(Paragraph("Summary", heading_style))
        
        # Create summary table
        summary_data = [
            ["Total Drivers", "Late", "Early End", "Not On Job", "On Time"],
            [
                summary.get('total', 0),
                f"{summary.get('late', 0)} ({summary.get('late', 0)/summary.get('total', 1)*100:.1f}%)" if summary.get('total', 0) > 0 else "0 (0.0%)",
                f"{summary.get('early_end', 0)} ({summary.get('early_end', 0)/summary.get('total', 1)*100:.1f}%)" if summary.get('total', 0) > 0 else "0 (0.0%)",
                f"{summary.get('not_on_job', 0)} ({summary.get('not_on_job', 0)/summary.get('total', 1)*100:.1f}%)" if summary.get('total', 0) > 0 else "0 (0.0%)",
                f"{summary.get('on_time', 0)} ({summary.get('on_time', 0)/summary.get('total', 1)*100:.1f}%)" if summary.get('total', 0) > 0 else "0 (0.0%)"
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
        
        logger.info(f"Generated PDF report at {output_path}")
        
        # Create duplicates if needed for compatibility
        if alt_output_path:
            import shutil
            shutil.copy(output_path, alt_output_path)
            logger.info(f"Created alternate PDF at {alt_output_path}")
            
        if report_output_path:
            import shutil
            shutil.copy(output_path, report_output_path)
            logger.info(f"Created report PDF at {report_output_path}")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# Remove unused function since we're using getSampleStyleSheet directly