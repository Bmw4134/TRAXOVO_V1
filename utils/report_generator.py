"""
Report Generator Module

This module provides utilities to generate PDF and CSV reports from various data sources.
It handles formatting, layout, and export options with preview capabilities.
"""

import os
import csv
import json
import datetime
import logging
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure export directories exist
EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)
PREVIEW_DIR = EXPORTS_DIR / "previews"
PREVIEW_DIR.mkdir(exist_ok=True)
PDF_DIR = EXPORTS_DIR / "pdf"
PDF_DIR.mkdir(exist_ok=True)
CSV_DIR = EXPORTS_DIR / "csv"
CSV_DIR.mkdir(exist_ok=True)


class ReportGenerator:
    """Report generator for PDF and CSV formats with preview capabilities"""
    
    def __init__(self, report_type=None, data=None):
        """
        Initialize the report generator
        
        Args:
            report_type (str): Type of report ('daily_driver', 'pm_allocation', etc.)
            data (dict): Data to include in the report
        """
        self.report_type = report_type
        self.data = data or {}
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename_base = f"{self.report_type}_{self.timestamp}" if self.report_type else f"report_{self.timestamp}"
        
        # Set up styles
        self.styles = getSampleStyleSheet()
        self.title_style = self.styles['Heading1']
        self.subtitle_style = self.styles['Heading2']
        self.normal_style = self.styles['Normal']
        
        # Create custom styles
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Heading3'],
            textColor=colors.darkblue,
            spaceAfter=10
        )
        
        self.table_header_style = ParagraphStyle(
            'TableHeaderStyle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.black
        )

    def generate_pdf(self, title="Report", subtitle=None, columns=None, data_rows=None):
        """
        Generate a PDF report
        
        Args:
            title (str): Report title
            subtitle (str): Report subtitle
            columns (list): Column headers
            data_rows (list): Rows of data
            
        Returns:
            tuple: (filepath, preview_path)
        """
        columns = columns or self._get_columns()
        data_rows = data_rows or self._get_data_rows()
        pdf_buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=landscape(letter),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Build the story
        story = []
        
        # Add title
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 0.25*inch))
        
        # Add subtitle if provided
        if subtitle:
            story.append(Paragraph(subtitle, self.subtitle_style))
            story.append(Spacer(1, 0.15*inch))
        
        # Add timestamp
        timestamp_text = f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(timestamp_text, self.normal_style))
        story.append(Spacer(1, 0.25*inch))
        
        # Format table data
        table_data = [columns]  # First row is column headers
        for row in data_rows:
            table_data.append(row)
            
        # Create the table
        table = Table(table_data, repeatRows=1)
        
        # Style the table
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            # Zebra striping for readability
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
        ])
        table.setStyle(table_style)
        
        # Add the table to the story
        story.append(table)
        
        # Build the PDF
        doc.build(story)
        
        # Save the PDF to a file
        pdf_content = pdf_buffer.getvalue()
        pdf_filename = f"{self.filename_base}.pdf"
        pdf_path = PDF_DIR / pdf_filename
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
            
        # Generate a preview image
        preview_path = self._generate_preview(pdf_path)
        
        logger.info(f"Generated PDF report: {pdf_path}")
        return str(pdf_path), str(preview_path)

    def generate_csv(self, columns=None, data_rows=None):
        """
        Generate a CSV report
        
        Args:
            columns (list): Column headers
            data_rows (list): Rows of data
            
        Returns:
            tuple: (filepath, preview_path)
        """
        columns = columns or self._get_columns()
        data_rows = data_rows or self._get_data_rows()
        
        csv_filename = f"{self.filename_base}.csv"
        csv_path = CSV_DIR / csv_filename
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(data_rows)
            
        # Generate a preview of the CSV
        preview_path = self._generate_csv_preview(csv_path, columns, data_rows)
        
        logger.info(f"Generated CSV report: {csv_path}")
        return str(csv_path), str(preview_path)

    def _generate_preview(self, pdf_path):
        """
        Generate a preview image of the first page of a PDF
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            str: Path to the preview image
        """
        # For a real implementation, you would use a library like pdf2image or PyMuPDF
        # For simplicity, we'll create a placeholder image with matplotlib
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, f"PDF Preview\n{os.path.basename(pdf_path)}", 
                ha='center', va='center', fontsize=14)
        ax.axis('off')
        
        preview_filename = f"{self.filename_base}_preview.png"
        preview_path = PREVIEW_DIR / preview_filename
        
        plt.savefig(preview_path, dpi=72, bbox_inches='tight')
        plt.close(fig)
        
        return preview_path
        
    def _generate_csv_preview(self, csv_path, columns, data_rows):
        """
        Generate a preview image of a CSV file
        
        Args:
            csv_path (str): Path to the CSV file
            columns (list): Column headers
            data_rows (list): Rows of data
            
        Returns:
            str: Path to the preview image
        """
        # Create a visual preview of the CSV data
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Limit to first 10 rows for preview
        preview_rows = data_rows[:10]
        
        # Create a table
        table_data = [columns] + preview_rows
        table = ax.table(
            cellText=table_data,
            cellLoc='center',
            loc='center',
            colWidths=[0.15] * len(columns)
        )
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)
        
        # Color the header row
        for j, cell in enumerate(table._cells[(0, j)] for j in range(len(columns))):
            cell.set_facecolor('#4682B4')
            cell.set_text_props(weight='bold', color='white')
        
        ax.axis('off')
        
        preview_filename = f"{self.filename_base}_preview.png"
        preview_path = PREVIEW_DIR / preview_filename
        
        plt.savefig(preview_path, dpi=72, bbox_inches='tight')
        plt.close(fig)
        
        return preview_path

    def _get_columns(self):
        """
        Get columns based on report type
        
        Returns:
            list: Column headers
        """
        if not self.data:
            return ["Column 1", "Column 2", "Column 3"]
            
        if self.report_type == 'daily_driver':
            return ["Driver", "Asset", "Late Starts", "Early Ends", "Not On Job", "Notes"]
        elif self.report_type == 'pm_allocation':
            return ["Asset ID", "Description", "Original", "Updated", "Difference", "Notes"]
        elif self.report_type == 'asset_status':
            return ["Asset ID", "Name", "Status", "Location", "Last Updated", "Driver"]
        elif self.report_type == 'maintenance':
            return ["Asset ID", "Description", "Service Due", "Last Service", "Status", "Assigned To"]
        else:
            # Default columns based on data keys
            if isinstance(self.data, list) and self.data:
                return list(self.data[0].keys())
            elif isinstance(self.data, dict):
                return list(self.data.keys())
            else:
                return ["Column 1", "Column 2", "Column 3"]

    def _get_data_rows(self):
        """
        Get data rows based on report type
        
        Returns:
            list: Rows of data
        """
        if not self.data:
            # Return sample data if no data provided
            return [
                ["Sample Data 1", "Sample Data 2", "Sample Data 3"] for _ in range(5)
            ]
            
        if isinstance(self.data, list):
            # If data is a list of dicts
            if all(isinstance(item, dict) for item in self.data):
                columns = self._get_columns()
                return [[str(item.get(col, "")) for col in columns] for item in self.data]
            # If data is a list of lists
            elif all(isinstance(item, (list, tuple)) for item in self.data):
                return self.data
        elif isinstance(self.data, dict):
            # If data is a dictionary
            columns = self._get_columns()
            return [[str(self.data.get(col, ""))] for col in columns]
        
        # Default empty data
        return [["No Data"] * len(self._get_columns())]


# Convenience functions to generate reports
def generate_pdf_report(report_type, data, title=None, subtitle=None):
    """
    Generate a PDF report
    
    Args:
        report_type (str): Type of report
        data (dict): Data for the report
        title (str): Report title
        subtitle (str): Report subtitle
        
    Returns:
        tuple: (filepath, preview_path)
    """
    generator = ReportGenerator(report_type, data)
    return generator.generate_pdf(
        title=title or f"{report_type.replace('_', ' ').title()} Report",
        subtitle=subtitle
    )

def generate_csv_report(report_type, data):
    """
    Generate a CSV report
    
    Args:
        report_type (str): Type of report
        data (dict): Data for the report
        
    Returns:
        tuple: (filepath, preview_path)
    """
    generator = ReportGenerator(report_type, data)
    return generator.generate_csv()