"""
TRAXORA GENIUS CORE | Output Formatter Module

This module produces formatted outputs in various formats:
- PDF reports with detailed analytics
- Excel workbooks with categorized sheets
- JSON data files for system integration

It creates professional reports with company branding, charts, and 
enhanced Activity Detail metrics for comprehensive visibility.
"""
import os
import logging
import json
import pandas as pd
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart

# Configure logging
logger = logging.getLogger(__name__)

# Define constants
COMPANY_NAME = "TRAXORA Fleet Management"
REPORT_TITLE = "Daily Driver Report"
COMPANY_LOGO = None  # Path to logo if available

class OutputFormatter:
    """Output formatter for driver reporting pipeline"""
    
    def __init__(self, report_data=None, date_str=None, output_dir=None):
        """
        Initialize output formatter

        Args:
            report_data (dict, optional): Report data from ReportGenerator
            date_str (str, optional): Date string in YYYY-MM-DD format
            output_dir (str, optional): Output directory for reports
        """
        self.report_data = report_data or {}
        
        self.target_date = datetime.now().date()
        if date_str:
            try:
                self.target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Invalid date format: {date_str}, using current date")
        
        self.date_str = self.target_date.strftime('%Y-%m-%d')
        self.output_dir = output_dir or os.path.join('reports', self.date_str)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self.title_style = self.styles['Heading1']
        self.heading_style = self.styles['Heading2']
        self.subheading_style = self.styles['Heading3']
        self.normal_style = self.styles['Normal']
        
        # Custom styles
        self.header_style = ParagraphStyle(
            name='HeaderStyle',
            parent=self.styles['Heading2'],
            textColor=colors.darkblue,
            spaceAfter=10
        )
        
        self.metric_style = ParagraphStyle(
            name='MetricStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            backColor=colors.lightgrey,
            borderWidth=1,
            borderColor=colors.black,
            borderPadding=5,
            borderRadius=5,
            alignment=1  # Center
        )
    
    def load_report_data(self, report_data):
        """
        Load report data from ReportGenerator

        Args:
            report_data (dict): Report data

        Returns:
            bool: True if successful, False otherwise
        """
        if not report_data:
            logger.error("No report data provided")
            return False
        
        self.report_data = report_data
        return True
    
    def load_report_from_file(self, file_path):
        """
        Load report data from JSON file

        Args:
            file_path (str): Path to JSON file

        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r') as f:
                self.report_data = json.load(f)
            
            return True
        except Exception as e:
            logger.error(f"Error loading report data: {e}")
            return False
    
    def create_pdf_report(self, filename=None):
        """
        Create PDF report from report data

        Args:
            filename (str, optional): Output filename

        Returns:
            str: Path to saved file
        """
        if not self.report_data:
            logger.error("No report data loaded")
            return None
        
        # Default filename
        if not filename:
            filename = f"driver_report_{self.date_str}.pdf"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Full output path
        output_path = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Build PDF content
        story = []
        
        # Add title
        title = Paragraph(f"{REPORT_TITLE} - {self.report_data.get('date', self.date_str)}", self.title_style)
        story.append(title)
        story.append(Spacer(1, 0.25*inch))
        
        # Add summary section
        summary = self.report_data.get('summary', {})
        story.append(Paragraph("Summary", self.heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Create summary table
        summary_data = [
            ["Metric", "Value"],
            ["Total Drivers", summary.get('total_drivers', 0)],
            ["On Time", summary.get('on_time', 0)],
            ["Late", summary.get('late', 0)],
            ["Early End", summary.get('early_end', 0)],
            ["Not On Job", summary.get('not_on_job', 0)],
            ["Unknown", summary.get('unknown', 0)],
            ["Avg Minutes Late", round(summary.get('avg_minutes_late', 0), 1)],
            ["Avg Minutes Early End", round(summary.get('avg_minutes_early_end', 0), 1)]
        ]
        
        # Add activity metrics if available
        if 'activity_metrics' in summary:
            summary_data.extend([
                ["Total Activities", summary['activity_metrics'].get('total_activities', 0)],
                ["Unique Activity Types", summary['activity_metrics'].get('unique_activity_types', 0)]
            ])
        
        # Add job site stats if available
        if 'job_sites' in summary:
            summary_data.extend([
                ["Total Job Sites", summary['job_sites'].get('total', 0)],
                ["Job Sites with Late Drivers", summary['job_sites'].get('with_late_drivers', 0)],
                ["Job Sites with Not On Job", summary['job_sites'].get('with_not_on_job', 0)]
            ])
        
        summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.25*inch))
        
        # Add summary chart
        story.append(Paragraph("Driver Status Distribution", self.subheading_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Create pie chart
        pie_data = [
            summary.get('on_time', 0),
            summary.get('late', 0),
            summary.get('early_end', 0),
            summary.get('not_on_job', 0),
            summary.get('unknown', 0)
        ]
        
        if sum(pie_data) > 0:
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 150
            pie.y = 50
            pie.width = 100
            pie.height = 100
            pie.data = pie_data
            pie.labels = ['On Time', 'Late', 'Early End', 'Not On Job', 'Unknown']
            pie.slices.strokeWidth = 0.5
            pie.slices[0].fillColor = colors.green
            pie.slices[1].fillColor = colors.red
            pie.slices[2].fillColor = colors.orange
            pie.slices[3].fillColor = colors.purple
            pie.slices[4].fillColor = colors.grey
            drawing.add(pie)
            story.append(drawing)
            
        story.append(Spacer(1, 0.25*inch))
        story.append(PageBreak())
        
        # Add Activity Detail Metrics section if available
        if 'activity_metrics' in self.report_data:
            story.append(Paragraph("Activity Detail Metrics", self.heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            activity_types = self.report_data['activity_metrics'].get('activity_types', {})
            if activity_types:
                activity_data = [["Activity Type", "Count"]]
                for activity_type, count in activity_types.items():
                    activity_data.append([activity_type, count])
                
                activity_table = Table(activity_data, colWidths=[4*inch, 1*inch])
                activity_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                    ('BACKGROUND', (0, 1), (1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ]))
                
                story.append(activity_table)
                story.append(Spacer(1, 0.25*inch))
                
                # Add activity chart if we have data
                if len(activity_types) > 0:
                    drawing = Drawing(500, 200)
                    chart = VerticalBarChart()
                    chart.x = 50
                    chart.y = 50
                    chart.height = 125
                    chart.width = 400
                    chart.data = [list(activity_types.values())]
                    chart.categoryAxis.categoryNames = list(activity_types.keys())
                    chart.valueAxis.valueMin = 0
                    chart.valueAxis.valueMax = max(activity_types.values()) * 1.1
                    chart.bars[0].fillColor = colors.lightblue
                    drawing.add(chart)
                    story.append(drawing)
                    story.append(Spacer(1, 0.25*inch))
            
            story.append(PageBreak())
        
        # Add Driver Status sections
        status_sections = [
            ("Late Drivers", "late", colors.red),
            ("Early End Drivers", "early_end", colors.orange),
            ("Not On Job Drivers", "not_on_job", colors.purple)
        ]
        
        for title, status_key, color in status_sections:
            drivers = [d for d in self.report_data.get('drivers', []) if d.get('status', '').lower().replace(' ', '_') == status_key]
            
            if drivers:
                story.append(Paragraph(title, self.heading_style))
                story.append(Spacer(1, 0.1*inch))
                
                # Column headers based on status
                if status_key == 'late':
                    headers = ["Driver Name", "Minutes Late", "Asset ID", "Validation Score"]
                    data = [headers]
                    for driver in drivers:
                        data.append([
                            driver.get('driver_name', 'Unknown'),
                            driver.get('minutes_late', 0),
                            driver.get('asset_id', ''),
                            driver.get('validation_score', 0)
                        ])
                elif status_key == 'early_end':
                    headers = ["Driver Name", "Minutes Early", "Asset ID", "Validation Score"]
                    data = [headers]
                    for driver in drivers:
                        data.append([
                            driver.get('driver_name', 'Unknown'),
                            driver.get('minutes_early_end', 0),
                            driver.get('asset_id', ''),
                            driver.get('validation_score', 0)
                        ])
                else:  # not_on_job
                    headers = ["Driver Name", "Asset ID", "Assigned Job", "Actual Job", "Validation Score"]
                    data = [headers]
                    for driver in drivers:
                        data.append([
                            driver.get('driver_name', 'Unknown'),
                            driver.get('asset_id', ''),
                            driver.get('assigned_job', ''),
                            driver.get('actual_job', ''),
                            driver.get('validation_score', 0)
                        ])
                
                # Create table with appropriate widths
                col_widths = [2*inch] * len(headers)
                table = Table(data, colWidths=col_widths)
                
                # Style the table
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ]))
                
                story.append(table)
                story.append(Spacer(1, 0.25*inch))
                
                # Add explanatory text
                if status_key == 'late':
                    story.append(Paragraph(f"Total {len(drivers)} drivers late by an average of {round(summary.get('avg_minutes_late', 0), 1)} minutes", self.normal_style))
                elif status_key == 'early_end':
                    story.append(Paragraph(f"Total {len(drivers)} drivers ended early by an average of {round(summary.get('avg_minutes_early_end', 0), 1)} minutes", self.normal_style))
                else:  # not_on_job
                    story.append(Paragraph(f"Total {len(drivers)} drivers not at their assigned job site", self.normal_style))
                
                story.append(PageBreak())
        
        # Add Job Sites section
        job_sites = self.report_data.get('job_sites', {})
        if job_sites:
            story.append(Paragraph("Job Sites", self.heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            headers = ["Job Number", "Total Drivers", "On Time", "Late", "Early End", "Not On Job"]
            data = [headers]
            
            for job_number, job_data in job_sites.items():
                data.append([
                    job_number,
                    len(job_data.get('drivers', [])),
                    job_data.get('statuses', {}).get('on_time', 0),
                    job_data.get('statuses', {}).get('late', 0),
                    job_data.get('statuses', {}).get('early_end', 0),
                    job_data.get('statuses', {}).get('not_on_job', 0)
                ])
            
            # Create table
            col_widths = [1.5*inch] + [1*inch] * (len(headers) - 1)
            table = Table(data, colWidths=col_widths)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ]))
            
            story.append(table)
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Created PDF report: {output_path}")
        return output_path
    
    def create_comprehensive_excel(self, filename=None):
        """
        Create comprehensive Excel report with multiple sheets
        including detailed Activity Detail metrics

        Args:
            filename (str, optional): Output filename

        Returns:
            str: Path to saved file
        """
        if not self.report_data:
            logger.error("No report data loaded")
            return None
        
        # Default filename
        if not filename:
            filename = f"comprehensive_report_{self.date_str}.xlsx"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Full output path
        output_path = os.path.join(self.output_dir, filename)
        
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet
            summary = self.report_data.get('summary', {})
            summary_data = {
                'Metric': [
                    'Date',
                    'Generated At',
                    'Total Drivers',
                    'On Time',
                    'Late',
                    'Early End',
                    'Not On Job',
                    'Unknown',
                    'Avg Minutes Late',
                    'Avg Minutes Early End'
                ],
                'Value': [
                    self.report_data.get('date', self.date_str),
                    self.report_data.get('generated_at', datetime.now().isoformat()),
                    summary.get('total_drivers', 0),
                    summary.get('on_time', 0),
                    summary.get('late', 0),
                    summary.get('early_end', 0),
                    summary.get('not_on_job', 0),
                    summary.get('unknown', 0),
                    round(summary.get('avg_minutes_late', 0), 1),
                    round(summary.get('avg_minutes_early_end', 0), 1)
                ]
            }
            
            # Add activity metrics if available
            if 'activity_metrics' in summary:
                summary_data['Metric'].extend([
                    'Total Activities',
                    'Unique Activity Types'
                ])
                summary_data['Value'].extend([
                    summary['activity_metrics'].get('total_activities', 0),
                    summary['activity_metrics'].get('unique_activity_types', 0)
                ])
            
            # Add job site stats if available
            if 'job_sites' in summary:
                summary_data['Metric'].extend([
                    'Total Job Sites',
                    'Job Sites with Late Drivers',
                    'Job Sites with Not On Job'
                ])
                summary_data['Value'].extend([
                    summary['job_sites'].get('total', 0),
                    summary['job_sites'].get('with_late_drivers', 0),
                    summary['job_sites'].get('with_not_on_job', 0)
                ])
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # All Drivers sheet
            all_drivers = self.report_data.get('drivers', [])
            if all_drivers:
                all_drivers_data = []
                for driver in all_drivers:
                    all_drivers_data.append({
                        'Driver Name': driver.get('driver_name', 'Unknown'),
                        'Status': driver.get('status', 'Unknown'),
                        'Asset ID': driver.get('asset_id', ''),
                        'Minutes Late': driver.get('minutes_late', 0),
                        'Minutes Early End': driver.get('minutes_early_end', 0),
                        'Assigned Job': driver.get('assigned_job', ''),
                        'Actual Job': driver.get('actual_job', ''),
                        'First Seen': driver.get('first_seen', ''),
                        'Last Seen': driver.get('last_seen', ''),
                        'Validation Score': driver.get('validation_score', 0),
                        'Data Sources': ', '.join(driver.get('data_sources', [])),
                        'Activity Count': driver.get('activity_metrics', {}).get('total_activities', 0)
                    })
                
                all_drivers_df = pd.DataFrame(all_drivers_data)
                all_drivers_df.to_excel(writer, sheet_name='All Drivers', index=False)
            
            # Status-specific sheets
            status_sheets = [
                ('Late', 'Late'),
                ('Early End', 'Early End'),
                ('Not On Job', 'Not On Job')
            ]
            
            for sheet_name, status in status_sheets:
                status_drivers = [d for d in all_drivers if d.get('status') == status]
                if status_drivers:
                    status_data = []
                    for driver in status_drivers:
                        driver_dict = {
                            'Driver Name': driver.get('driver_name', 'Unknown'),
                            'Asset ID': driver.get('asset_id', ''),
                            'Validation Score': driver.get('validation_score', 0),
                            'Assigned Job': driver.get('assigned_job', ''),
                            'Data Sources': ', '.join(driver.get('data_sources', []))
                        }
                        
                        # Add status-specific fields
                        if status == 'Late':
                            driver_dict['Minutes Late'] = driver.get('minutes_late', 0)
                            driver_dict['Scheduled Start'] = driver.get('scheduled_start', '')
                            driver_dict['First Seen'] = driver.get('first_seen', '')
                        elif status == 'Early End':
                            driver_dict['Minutes Early End'] = driver.get('minutes_early_end', 0)
                            driver_dict['Scheduled End'] = driver.get('scheduled_end', '')
                            driver_dict['Last Seen'] = driver.get('last_seen', '')
                        elif status == 'Not On Job':
                            driver_dict['Actual Job'] = driver.get('actual_job', '')
                            driver_dict['Locations'] = len(driver.get('locations', []))
                        
                        driver_dict['Reasons'] = ', '.join(driver.get('reasons', []))
                        status_data.append(driver_dict)
                    
                    status_df = pd.DataFrame(status_data)
                    status_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Activity Types sheet
            activity_types = self.report_data.get('activity_metrics', {}).get('activity_types', {})
            if activity_types:
                activity_types_data = []
                for activity_type, count in activity_types.items():
                    activity_types_data.append({
                        'Activity Type': activity_type,
                        'Count': count
                    })
                
                activity_types_df = pd.DataFrame(activity_types_data)
                activity_types_df.to_excel(writer, sheet_name='Activity Types', index=False)
            
            # Activity by Driver sheet
            driver_activity = []
            for driver in all_drivers:
                if 'activity_metrics' in driver and driver['activity_metrics'].get('total_activities', 0) > 0:
                    activity_types_dict = driver['activity_metrics'].get('activity_types', {})
                    
                    driver_row = {
                        'Driver Name': driver.get('driver_name', 'Unknown'),
                        'Total Activities': driver['activity_metrics'].get('total_activities', 0),
                        'Asset ID': driver.get('asset_id', ''),
                        'Status': driver.get('status', 'Unknown')
                    }
                    
                    # Add each activity type as a column
                    for activity_type in activity_types:
                        driver_row[activity_type] = activity_types_dict.get(activity_type, 0)
                    
                    driver_activity.append(driver_row)
            
            if driver_activity:
                driver_activity_df = pd.DataFrame(driver_activity)
                driver_activity_df.to_excel(writer, sheet_name='Activity by Driver', index=False)
            
            # Job Sites sheet
            job_sites = self.report_data.get('job_sites', {})
            if job_sites:
                job_sites_data = []
                for job_number, job_data in job_sites.items():
                    job_sites_data.append({
                        'Job Number': job_number,
                        'Total Drivers': len(job_data.get('drivers', [])),
                        'On Time': job_data.get('statuses', {}).get('on_time', 0),
                        'Late': job_data.get('statuses', {}).get('late', 0),
                        'Early End': job_data.get('statuses', {}).get('early_end', 0),
                        'Not On Job': job_data.get('statuses', {}).get('not_on_job', 0),
                        'Unknown': job_data.get('statuses', {}).get('unknown', 0),
                        'Drivers': ', '.join(job_data.get('drivers', []))
                    })
                
                job_sites_df = pd.DataFrame(job_sites_data)
                job_sites_df.to_excel(writer, sheet_name='Job Sites', index=False)
        
        logger.info(f"Created comprehensive Excel report: {output_path}")
        return output_path
    
    def create_pmr_reports(self):
        """
        Create PMR reports for Late, Early End, and Not On Job drivers

        Returns:
            dict: Paths to saved files
        """
        if not self.report_data:
            logger.error("No report data loaded")
            return {}
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate PDFs for each status
        report_paths = {}
        
        all_drivers = self.report_data.get('drivers', [])
        
        # PMR (LATE)
        late_drivers = [d for d in all_drivers if d.get('status') == 'Late']
        if late_drivers:
            late_path = os.path.join(self.output_dir, f"PMR_LATE_{self.date_str}.pdf")
            doc = SimpleDocTemplate(
                late_path,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            story = []
            
            # Add title
            title = Paragraph(f"PMR (LATE) Report - {self.date_str}", self.title_style)
            story.append(title)
            story.append(Spacer(1, 0.25*inch))
            
            # Add summary
            summary = self.report_data.get('summary', {})
            late_count = summary.get('late', 0)
            avg_minutes_late = summary.get('avg_minutes_late', 0)
            
            summary_text = Paragraph(f"Total {late_count} drivers late by an average of {round(avg_minutes_late, 1)} minutes", self.header_style)
            story.append(summary_text)
            story.append(Spacer(1, 0.25*inch))
            
            # Add driver table
            headers = ["Driver Name", "Minutes Late", "Asset ID", "Assigned Job", "Validation Score", "Reasons"]
            data = [headers]
            
            for driver in late_drivers:
                data.append([
                    driver.get('driver_name', 'Unknown'),
                    driver.get('minutes_late', 0),
                    driver.get('asset_id', ''),
                    driver.get('assigned_job', ''),
                    driver.get('validation_score', 0),
                    ', '.join(driver.get('reasons', []))
                ])
            
            # Create table
            col_widths = [2*inch, 1*inch, 1*inch, 1.5*inch, 1*inch, 2*inch]
            table = Table(data, colWidths=col_widths)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (4, -1), 'CENTER'),
            ]))
            
            story.append(table)
            
            # Build PDF
            doc.build(story)
            report_paths['late'] = late_path
        
        # PMR (EARLY END)
        early_drivers = [d for d in all_drivers if d.get('status') == 'Early End']
        if early_drivers:
            early_path = os.path.join(self.output_dir, f"PMR_EARLY_END_{self.date_str}.pdf")
            doc = SimpleDocTemplate(
                early_path,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            story = []
            
            # Add title
            title = Paragraph(f"PMR (EARLY END) Report - {self.date_str}", self.title_style)
            story.append(title)
            story.append(Spacer(1, 0.25*inch))
            
            # Add summary
            summary = self.report_data.get('summary', {})
            early_count = summary.get('early_end', 0)
            avg_minutes_early = summary.get('avg_minutes_early_end', 0)
            
            summary_text = Paragraph(f"Total {early_count} drivers ended early by an average of {round(avg_minutes_early, 1)} minutes", self.header_style)
            story.append(summary_text)
            story.append(Spacer(1, 0.25*inch))
            
            # Add driver table
            headers = ["Driver Name", "Minutes Early", "Asset ID", "Assigned Job", "Validation Score", "Reasons"]
            data = [headers]
            
            for driver in early_drivers:
                data.append([
                    driver.get('driver_name', 'Unknown'),
                    driver.get('minutes_early_end', 0),
                    driver.get('asset_id', ''),
                    driver.get('assigned_job', ''),
                    driver.get('validation_score', 0),
                    ', '.join(driver.get('reasons', []))
                ])
            
            # Create table
            col_widths = [2*inch, 1*inch, 1*inch, 1.5*inch, 1*inch, 2*inch]
            table = Table(data, colWidths=col_widths)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkorange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (4, -1), 'CENTER'),
            ]))
            
            story.append(table)
            
            # Build PDF
            doc.build(story)
            report_paths['early_end'] = early_path
        
        # PMR (NOT ON JOB)
        noj_drivers = [d for d in all_drivers if d.get('status') == 'Not On Job']
        if noj_drivers:
            noj_path = os.path.join(self.output_dir, f"PMR_NOT_ON_JOB_{self.date_str}.pdf")
            doc = SimpleDocTemplate(
                noj_path,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            story = []
            
            # Add title
            title = Paragraph(f"PMR (NOT ON JOB) Report - {self.date_str}", self.title_style)
            story.append(title)
            story.append(Spacer(1, 0.25*inch))
            
            # Add summary
            summary = self.report_data.get('summary', {})
            noj_count = summary.get('not_on_job', 0)
            
            summary_text = Paragraph(f"Total {noj_count} drivers not at their assigned job site", self.header_style)
            story.append(summary_text)
            story.append(Spacer(1, 0.25*inch))
            
            # Add driver table
            headers = ["Driver Name", "Asset ID", "Assigned Job", "Actual Job", "Validation Score", "Reasons"]
            data = [headers]
            
            for driver in noj_drivers:
                data.append([
                    driver.get('driver_name', 'Unknown'),
                    driver.get('asset_id', ''),
                    driver.get('assigned_job', ''),
                    driver.get('actual_job', ''),
                    driver.get('validation_score', 0),
                    ', '.join(driver.get('reasons', []))
                ])
            
            # Create table
            col_widths = [2*inch, 1*inch, 1.5*inch, 1.5*inch, 1*inch, 1.5*inch]
            table = Table(data, colWidths=col_widths)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkviolet),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (4, -1), 'CENTER'),
            ]))
            
            story.append(table)
            
            # Build PDF
            doc.build(story)
            report_paths['not_on_job'] = noj_path
        
        # Create Activity Detail Summary PDF
        if 'activity_metrics' in self.report_data:
            activity_path = os.path.join(self.output_dir, f"ACTIVITY_DETAIL_SUMMARY_{self.date_str}.pdf")
            doc = SimpleDocTemplate(
                activity_path,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            story = []
            
            # Add title
            title = Paragraph(f"Activity Detail Summary - {self.date_str}", self.title_style)
            story.append(title)
            story.append(Spacer(1, 0.25*inch))
            
            # Add summary
            summary = self.report_data.get('summary', {})
            activity_metrics = summary.get('activity_metrics', {})
            total_activities = activity_metrics.get('total_activities', 0)
            unique_types = activity_metrics.get('unique_activity_types', 0)
            
            summary_text = Paragraph(f"Total {total_activities} activities across {unique_types} unique activity types", self.header_style)
            story.append(summary_text)
            story.append(Spacer(1, 0.25*inch))
            
            # Add activity types table
            activity_types = self.report_data.get('activity_metrics', {}).get('activity_types', {})
            if activity_types:
                # Add activity types table
                story.append(Paragraph("Activity Types", self.subheading_style))
                story.append(Spacer(1, 0.1*inch))
                
                headers = ["Activity Type", "Count", "Percentage"]
                data = [headers]
                
                total = sum(activity_types.values())
                for activity_type, count in activity_types.items():
                    percentage = (count / total * 100) if total > 0 else 0
                    data.append([
                        activity_type,
                        count,
                        f"{percentage:.1f}%"
                    ])
                
                # Create table
                col_widths = [3*inch, 1*inch, 1*inch]
                table = Table(data, colWidths=col_widths)
                
                # Style the table
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (2, -1), 'CENTER'),
                ]))
                
                story.append(table)
                story.append(Spacer(1, 0.25*inch))
                
                # Add chart if we have data
                if len(activity_types) > 0:
                    drawing = Drawing(500, 200)
                    chart = VerticalBarChart()
                    chart.x = 50
                    chart.y = 50
                    chart.height = 125
                    chart.width = 400
                    chart.data = [list(activity_types.values())]
                    chart.categoryAxis.categoryNames = list(activity_types.keys())
                    chart.valueAxis.valueMin = 0
                    chart.valueAxis.valueMax = max(activity_types.values()) * 1.1
                    chart.bars[0].fillColor = colors.lightblue
                    drawing.add(chart)
                    story.append(drawing)
                    story.append(Spacer(1, 0.25*inch))
            
            # Add top drivers by activity
            story.append(PageBreak())
            story.append(Paragraph("Top Drivers by Activity", self.subheading_style))
            story.append(Spacer(1, 0.1*inch))
            
            # Collect driver activity data
            driver_activities = []
            for driver in all_drivers:
                if 'activity_metrics' in driver and driver['activity_metrics'].get('total_activities', 0) > 0:
                    driver_activities.append({
                        'driver_name': driver.get('driver_name', 'Unknown'),
                        'total_activities': driver['activity_metrics'].get('total_activities', 0),
                        'activity_types': driver['activity_metrics'].get('activity_types', {})
                    })
            
            # Sort by total activities
            driver_activities.sort(key=lambda x: x['total_activities'], reverse=True)
            
            # Take top 10
            top_drivers = driver_activities[:10]
            
            # Create table
            if top_drivers:
                headers = ["Driver Name", "Total Activities", "Most Common Activity"]
                data = [headers]
                
                for driver in top_drivers:
                    most_common = ""
                    if driver['activity_types']:
                        most_common = max(driver['activity_types'].items(), key=lambda x: x[1])[0]
                    
                    data.append([
                        driver['driver_name'],
                        driver['total_activities'],
                        most_common
                    ])
                
                # Create table
                col_widths = [2.5*inch, 1.5*inch, 2.5*inch]
                table = Table(data, colWidths=col_widths)
                
                # Style the table
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ]))
                
                story.append(table)
            
            # Build PDF
            doc.build(story)
            report_paths['activity'] = activity_path
        
        logger.info(f"Created PMR reports: {', '.join(report_paths.keys())}")
        return report_paths
    
    def generate_all_formats(self):
        """
        Generate all report formats

        Returns:
            dict: Paths to all generated report files
        """
        if not self.report_data:
            logger.error("No report data loaded")
            return {}
        
        report_paths = {}
        
        # Create PDF report
        pdf_path = self.create_pdf_report()
        if pdf_path:
            report_paths['pdf'] = pdf_path
        
        # Create comprehensive Excel
        excel_path = self.create_comprehensive_excel()
        if excel_path:
            report_paths['excel'] = excel_path
        
        # Create PMR reports
        pmr_paths = self.create_pmr_reports()
        if pmr_paths:
            report_paths.update(pmr_paths)
        
        return report_paths