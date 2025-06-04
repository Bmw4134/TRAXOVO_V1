"""
Unified Data Processor

This module provides a unified interface for processing data from various sources
and generating attendance reports with proper validation and audit trails.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedDataProcessor:
    """
    Unified Data Processor for handling driver attendance data
    """
    
    def __init__(self, date_str: str):
        """
        Initialize the processor
        
        Args:
            date_str: Target date in YYYY-MM-DD format
        """
        self.date_str = date_str
        self.date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Data storage
        self.drivers = {}
        self.assets = {}
        self.driving_history = []
        self.activity_detail = []
        self.assets_onsite = []
        self.job_sites = {}
        self.employee_data = {}
        self.start_time_job = {}
        
        # Configuration
        self.config = {
            'late_minutes': 15,
            'early_minutes': 30,
            'scheduled_start': '07:00',
            'scheduled_end': '17:30'
        }
        
        # Create output directories
        os.makedirs('exports/daily_reports', exist_ok=True)
        
        # Initialize trace manifest
        self.trace_manifest = {
            'date': date_str,
            'data_sources': {},
            'processing_steps': [],
            'validation_results': {}
        }
    
    def process_driving_history(self, file_path: str) -> None:
        """
        Process driving history data
        
        Args:
            file_path: Path to the driving history CSV file
        """
        logger.info(f"Processing driving history from {file_path}")
        
        try:
            # Track data source
            source_info = {
                'file': os.path.basename(file_path),
                'timestamp': datetime.now().isoformat(),
                'records_loaded': 0
            }
            
            # Load data
            df = pd.read_csv(file_path)
            
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Find key columns
            driver_col = self._find_column(df, ['driver', 'driver_name', 'drivername'])
            date_col = self._find_column(df, ['date'])
            time_col = self._find_column(df, ['time'])
            event_col = self._find_column(df, ['event'])
            asset_col = self._find_column(df, ['asset', 'asset_id', 'equipment'])
            
            # Filter by date if possible
            if date_col:
                df['date'] = pd.to_datetime(df[date_col], errors='coerce')
                df = df[df['date'].dt.date == self.date_obj.date()]
            
            # Process records
            for idx, row in df.iterrows():
                if not all([driver_col, date_col, time_col, event_col, asset_col]):
                    continue
                    
                driver = str(row[driver_col]).strip()
                event = str(row[event_col]).strip()
                time_str = str(row[time_col]).strip()
                asset_id = str(row[asset_col]).strip()
                
                # Skip invalid entries
                if not all([driver, event, time_str, asset_id]):
                    continue
                
                # Add to driving history
                self.driving_history.append({
                    'driver': driver,
                    'event': event,
                    'time': time_str,
                    'asset_id': asset_id,
                    'source_file': os.path.basename(file_path),
                    'row_idx': idx
                })
                
                # Update driver-asset mapping
                if driver not in self.drivers:
                    self.drivers[driver] = {
                        'assets': set(),
                        'key_on_times': [],
                        'key_off_times': [],
                        'locations': set()
                    }
                
                self.drivers[driver]['assets'].add(asset_id)
                
                # Track key on/off events
                if event.lower() == 'keyon':
                    self.drivers[driver]['key_on_times'].append(time_str)
                elif event.lower() == 'keyoff':
                    self.drivers[driver]['key_off_times'].append(time_str)
            
            # Update source info
            source_info['records_loaded'] = len(self.driving_history)
            self.trace_manifest['data_sources']['driving_history'] = source_info
            
            logger.info(f"Processed {source_info['records_loaded']} driving history records")
        except Exception as e:
            logger.error(f"Error processing driving history: {e}")
    
    def process_activity_detail(self, file_path: str) -> None:
        """
        Process activity detail data
        
        Args:
            file_path: Path to the activity detail CSV file
        """
        logger.info(f"Processing activity detail from {file_path}")
        
        try:
            # Track data source
            source_info = {
                'file': os.path.basename(file_path),
                'timestamp': datetime.now().isoformat(),
                'records_loaded': 0
            }
            
            # Load data
            df = pd.read_csv(file_path)
            
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Find key columns
            driver_col = self._find_column(df, ['driver', 'driver_name', 'drivername'])
            date_col = self._find_column(df, ['date'])
            start_col = self._find_column(df, ['start', 'start_time', 'starttime'])
            end_col = self._find_column(df, ['end', 'end_time', 'endtime'])
            location_col = self._find_column(df, ['location', 'job_site', 'jobsite'])
            asset_col = self._find_column(df, ['asset', 'asset_id', 'equipment'])
            
            # Filter by date if possible
            if date_col:
                df['date'] = pd.to_datetime(df[date_col], errors='coerce')
                df = df[df['date'].dt.date == self.date_obj.date()]
            
            # Process records
            for idx, row in df.iterrows():
                if not all([driver_col, location_col]):
                    continue
                    
                driver = str(row[driver_col]).strip()
                location = str(row[location_col]).strip()
                
                # Get optional fields
                start_time = str(row[start_col]).strip() if start_col and not pd.isna(row[start_col]) else None
                end_time = str(row[end_col]).strip() if end_col and not pd.isna(row[end_col]) else None
                asset_id = str(row[asset_col]).strip() if asset_col and not pd.isna(row[asset_col]) else None
                
                # Skip invalid entries
                if not all([driver, location]):
                    continue
                
                # Add to activity detail
                self.activity_detail.append({
                    'driver': driver,
                    'location': location,
                    'start_time': start_time,
                    'end_time': end_time,
                    'asset_id': asset_id,
                    'source_file': os.path.basename(file_path),
                    'row_idx': idx
                })
                
                # Update driver-location mapping
                if driver not in self.drivers:
                    self.drivers[driver] = {
                        'assets': set(),
                        'key_on_times': [],
                        'key_off_times': [],
                        'locations': set()
                    }
                
                self.drivers[driver]['locations'].add(location)
                
                # Track job site
                if location not in self.job_sites:
                    self.job_sites[location] = {
                        'drivers': set(),
                        'asset_ids': set()
                    }
                
                self.job_sites[location]['drivers'].add(driver)
                
                if asset_id:
                    self.job_sites[location]['asset_ids'].add(asset_id)
                    
                    if driver in self.drivers:
                        self.drivers[driver]['assets'].add(asset_id)
            
            # Update source info
            source_info['records_loaded'] = len(self.activity_detail)
            self.trace_manifest['data_sources']['activity_detail'] = source_info
            
            logger.info(f"Processed {source_info['records_loaded']} activity detail records")
        except Exception as e:
            logger.error(f"Error processing activity detail: {e}")
    
    def process_asset_onsite(self, file_path: str) -> None:
        """
        Process assets time-on-site data
        
        Args:
            file_path: Path to the assets time-on-site CSV file
        """
        logger.info(f"Processing asset on-site data from {file_path}")
        
        try:
            # Track data source
            source_info = {
                'file': os.path.basename(file_path),
                'timestamp': datetime.now().isoformat(),
                'records_loaded': 0
            }
            
            # Load data
            df = pd.read_csv(file_path)
            
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Find key columns
            asset_col = self._find_column(df, ['asset', 'asset_id', 'equipment'])
            date_col = self._find_column(df, ['date'])
            site_col = self._find_column(df, ['site', 'job_site', 'jobsite', 'location'])
            hours_col = self._find_column(df, ['hours', 'time_on_site', 'timeonsite'])
            
            # Filter by date if possible
            if date_col:
                df['date'] = pd.to_datetime(df[date_col], errors='coerce')
                df = df[df['date'].dt.date == self.date_obj.date()]
            
            # Process records
            for idx, row in df.iterrows():
                if not all([asset_col, site_col]):
                    continue
                    
                asset_id = str(row[asset_col]).strip()
                site = str(row[site_col]).strip()
                hours = float(row[hours_col]) if hours_col and not pd.isna(row[hours_col]) else 0
                
                # Skip invalid entries
                if not all([asset_id, site]):
                    continue
                
                # Add to assets on-site
                self.assets_onsite.append({
                    'asset_id': asset_id,
                    'site': site,
                    'hours': hours,
                    'source_file': os.path.basename(file_path),
                    'row_idx': idx
                })
                
                # Update asset data
                if asset_id not in self.assets:
                    self.assets[asset_id] = {
                        'sites': set(),
                        'hours': {}
                    }
                
                self.assets[asset_id]['sites'].add(site)
                self.assets[asset_id]['hours'][site] = hours
                
                # Track job site
                if site not in self.job_sites:
                    self.job_sites[site] = {
                        'drivers': set(),
                        'asset_ids': set()
                    }
                
                self.job_sites[site]['asset_ids'].add(asset_id)
            
            # Update source info
            source_info['records_loaded'] = len(self.assets_onsite)
            self.trace_manifest['data_sources']['assets_onsite'] = source_info
            
            logger.info(f"Processed {source_info['records_loaded']} asset on-site records")
        except Exception as e:
            logger.error(f"Error processing asset on-site data: {e}")
    
    def process_employee_data(self, file_path: str) -> None:
        """
        Process employee data
        
        Args:
            file_path: Path to the employee data file
        """
        logger.info(f"Processing employee data from {file_path}")
        
        try:
            # Track data source
            source_info = {
                'file': os.path.basename(file_path),
                'timestamp': datetime.now().isoformat(),
                'records_loaded': 0
            }
            
            # Load data
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                logger.error(f"Unsupported file format: {file_path}")
                return
            
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Find key columns
            name_col = self._find_column(df, ['name', 'employee', 'employee_name', 'driver', 'driver_name'])
            
            # Process records
            for idx, row in df.iterrows():
                if not name_col:
                    continue
                    
                name = str(row[name_col]).strip()
                
                # Skip invalid entries
                if not name or name.lower() in ['nan', 'none', 'null', '']:
                    continue
                
                # Add to employee data
                self.employee_data[name] = {
                    'verified': True,
                    'source_file': os.path.basename(file_path),
                    'row_idx': idx
                }
            
            # Update source info
            source_info['records_loaded'] = len(self.employee_data)
            self.trace_manifest['data_sources']['employee_data'] = source_info
            
            logger.info(f"Processed {source_info['records_loaded']} employee records")
        except Exception as e:
            logger.error(f"Error processing employee data: {e}")
    
    def process_start_time_job_sheet(self, file_path: str) -> None:
        """
        Process start time and job sheet data
        
        Args:
            file_path: Path to the start time and job sheet file
        """
        logger.info(f"Processing start time and job sheet from {file_path}")
        
        try:
            # Track data source
            source_info = {
                'file': os.path.basename(file_path),
                'timestamp': datetime.now().isoformat(),
                'records_loaded': 0
            }
            
            # Load data
            df = pd.read_excel(file_path)
            
            # Standardize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Find key columns
            driver_col = self._find_column(df, ['driver', 'driver_name', 'drivername', 'name', 'employee'])
            job_col = self._find_column(df, ['job', 'job_site', 'jobsite', 'job_number', 'jobnumber'])
            start_col = self._find_column(df, ['start', 'start_time', 'starttime'])
            end_col = self._find_column(df, ['end', 'end_time', 'endtime'])
            
            # Process records
            for idx, row in df.iterrows():
                if not all([driver_col, job_col]):
                    continue
                    
                driver = str(row[driver_col]).strip()
                job = str(row[job_col]).strip()
                
                # Get optional fields
                start_time = str(row[start_col]).strip() if start_col and not pd.isna(row[start_col]) else self.config['scheduled_start']
                end_time = str(row[end_col]).strip() if end_col and not pd.isna(row[end_col]) else self.config['scheduled_end']
                
                # Skip invalid entries
                if not all([driver, job]):
                    continue
                
                # Add to start time job data
                self.start_time_job[driver] = {
                    'job': job,
                    'start_time': start_time,
                    'end_time': end_time,
                    'source_file': os.path.basename(file_path),
                    'row_idx': idx
                }
            
            # Update source info
            source_info['records_loaded'] = len(self.start_time_job)
            self.trace_manifest['data_sources']['start_time_job'] = source_info
            
            logger.info(f"Processed {source_info['records_loaded']} start time and job records")
        except Exception as e:
            logger.error(f"Error processing start time and job sheet: {e}")
    
    def generate_attendance_report(self) -> Dict[str, Any]:
        """
        Generate attendance report
        
        Returns:
            Dictionary with attendance report data
        """
        logger.info(f"Generating attendance report for {self.date_str}")
        
        try:
            # Initialize report
            report = {
                'date': self.date_str,
                'formatted_date': self.date_obj.strftime('%A, %B %d, %Y'),
                'total_drivers': len(self.drivers),
                'drivers': [],
                'late_start_records': [],
                'early_end_records': [],
                'not_on_job_records': [],
                'on_time_drivers': 0,
                'on_time_percent': 0,
                'trace_manifest': self.trace_manifest
            }
            
            # Process each driver
            for driver_name, driver_data in self.drivers.items():
                # Create driver record
                driver_record = {
                    'driver_name': driver_name,
                    'asset_id': next(iter(driver_data['assets'])) if driver_data['assets'] else 'Unknown',
                    'key_on_time': min(driver_data['key_on_times']) if driver_data['key_on_times'] else None,
                    'key_off_time': max(driver_data['key_off_times']) if driver_data['key_off_times'] else None,
                    'job_site': next(iter(driver_data['locations'])) if driver_data['locations'] else 'Unknown',
                    'verified': driver_name in self.employee_data,
                    'classification': 'Unknown'
                }
                
                # Get scheduled times
                scheduled_data = self.start_time_job.get(driver_name, {})
                scheduled_start = scheduled_data.get('start_time', self.config['scheduled_start'])
                scheduled_end = scheduled_data.get('end_time', self.config['scheduled_end'])
                job_site = scheduled_data.get('job', driver_record['job_site'])
                
                # Update driver record
                driver_record['scheduled_start'] = scheduled_start
                driver_record['scheduled_end'] = scheduled_end
                driver_record['job_site'] = job_site
                
                # Convert times to datetime for comparison
                scheduled_start_dt = self._parse_time(scheduled_start)
                scheduled_end_dt = self._parse_time(scheduled_end)
                actual_start_dt = self._parse_time(driver_record['key_on_time']) if driver_record['key_on_time'] else None
                actual_end_dt = self._parse_time(driver_record['key_off_time']) if driver_record['key_off_time'] else None
                
                # Classify driver
                late_threshold = scheduled_start_dt + timedelta(minutes=self.config['late_minutes'])
                early_threshold = scheduled_end_dt - timedelta(minutes=self.config['early_minutes'])
                
                if not actual_start_dt:
                    # Not On Job
                    driver_record['classification'] = 'Not On Job'
                    driver_record['status_reason'] = 'No Key On time recorded'
                    
                    report['not_on_job_records'].append({
                        'driver_name': driver_name,
                        'asset_id': driver_record['asset_id'],
                        'job_site': job_site,
                        'current_location': 'Unknown',
                        'distance_from_job': 'N/A',
                        'last_update': 'N/A'
                    })
                elif actual_start_dt > late_threshold:
                    # Late Start
                    driver_record['classification'] = 'Late'
                    minutes_late = int((actual_start_dt - scheduled_start_dt).total_seconds() / 60)
                    driver_record['status_reason'] = f"{minutes_late} minutes late"
                    
                    report['late_start_records'].append({
                        'driver_name': driver_name,
                        'asset_id': driver_record['asset_id'],
                        'scheduled_start': scheduled_start,
                        'actual_start': driver_record['key_on_time'],
                        'minutes_late': minutes_late,
                        'job_site': job_site
                    })
                elif actual_end_dt and actual_end_dt < early_threshold:
                    # Early End
                    driver_record['classification'] = 'Early End'
                    minutes_early = int((scheduled_end_dt - actual_end_dt).total_seconds() / 60)
                    driver_record['status_reason'] = f"{minutes_early} minutes early"
                    
                    report['early_end_records'].append({
                        'driver_name': driver_name,
                        'asset_id': driver_record['asset_id'],
                        'scheduled_end': scheduled_end,
                        'actual_end': driver_record['key_off_time'],
                        'minutes_early': minutes_early,
                        'job_site': job_site
                    })
                else:
                    # On Time
                    driver_record['classification'] = 'On Time'
                    driver_record['status_reason'] = 'Within scheduled parameters'
                    report['on_time_drivers'] += 1
                
                # Add to drivers list
                report['drivers'].append(driver_record)
            
            # Calculate on-time percentage
            total_drivers = len(self.drivers)
            on_time_drivers = report['on_time_drivers']
            report['on_time_percent'] = (on_time_drivers / total_drivers * 100) if total_drivers > 0 else 0
            
            # Save report to JSON
            output_path = f'exports/daily_reports/attendance_data_{self.date_str}.json'
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Attendance report saved to {output_path}")
            
            return report
        except Exception as e:
            logger.error(f"Error generating attendance report: {e}")
            return {'error': str(e)}
    
    def export_excel_report(self) -> str:
        """
        Export attendance report to Excel
        
        Returns:
            Path to the exported Excel file
        """
        logger.info(f"Exporting Excel report for {self.date_str}")
        
        try:
            # Load report data
            report_path = f'exports/daily_reports/attendance_data_{self.date_str}.json'
            
            if not os.path.exists(report_path):
                logger.error(f"Report data not found at {report_path}")
                return None
            
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            # Create Excel writer
            output_path = f'exports/daily_reports/{self.date_str}_DailyDriverReport.xlsx'
            writer = pd.ExcelWriter(output_path, engine='openpyxl')
            
            # Create summary sheet
            summary_data = {
                'Metric': [
                    'Total Drivers',
                    'On Time Drivers',
                    'Late Drivers',
                    'Early End Drivers',
                    'Not On Job Drivers',
                    'On Time Percentage'
                ],
                'Value': [
                    report['total_drivers'],
                    report['on_time_drivers'],
                    len(report['late_start_records']),
                    len(report['early_end_records']),
                    len(report['not_on_job_records']),
                    f"{report['on_time_percent']:.1f}%"
                ]
            }
            
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Create late drivers sheet
            if report['late_start_records']:
                pd.DataFrame(report['late_start_records']).to_excel(writer, sheet_name='Late Start', index=False)
            
            # Create early end drivers sheet
            if report['early_end_records']:
                pd.DataFrame(report['early_end_records']).to_excel(writer, sheet_name='Early End', index=False)
            
            # Create not on job drivers sheet
            if report['not_on_job_records']:
                pd.DataFrame(report['not_on_job_records']).to_excel(writer, sheet_name='Not On Job', index=False)
            
            # Create all drivers sheet
            pd.DataFrame(report['drivers']).to_excel(writer, sheet_name='All Drivers', index=False)
            
            # Save Excel file
            writer.close()
            
            logger.info(f"Excel report saved to {output_path}")
            
            return output_path
        except Exception as e:
            logger.error(f"Error exporting Excel report: {e}")
            return None
    
    def export_pdf_report(self) -> str:
        """
        Export attendance report to PDF
        
        Returns:
            Path to the exported PDF file
        """
        logger.info(f"Exporting PDF report for {self.date_str}")
        
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            # Load report data
            report_path = f'exports/daily_reports/attendance_data_{self.date_str}.json'
            
            if not os.path.exists(report_path):
                logger.error(f"Report data not found at {report_path}")
                return None
            
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            # Create PDF document
            output_path = f'exports/daily_reports/{self.date_str}_DailyDriverReport.pdf'
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Create content
            content = []
            
            # Add title
            title = Paragraph(f"Daily Driver Report - {report['formatted_date']}", title_style)
            content.append(title)
            content.append(Spacer(1, 12))
            
            # Add summary
            summary_heading = Paragraph("Summary", heading_style)
            content.append(summary_heading)
            content.append(Spacer(1, 6))
            
            summary_data = [
                ['Metric', 'Value'],
                ['Total Drivers', str(report['total_drivers'])],
                ['On Time Drivers', str(report['on_time_drivers'])],
                ['Late Drivers', str(len(report['late_start_records']))],
                ['Early End Drivers', str(len(report['early_end_records']))],
                ['Not On Job Drivers', str(len(report['not_on_job_records']))],
                ['On Time Percentage', f"{report['on_time_percent']:.1f}%"]
            ]
            
            summary_table = Table(summary_data, colWidths=[200, 100])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(summary_table)
            content.append(Spacer(1, 12))
            
            # Add late drivers
            if report['late_start_records']:
                late_heading = Paragraph("Late Start Drivers", heading_style)
                content.append(late_heading)
                content.append(Spacer(1, 6))
                
                late_data = [['Driver', 'Asset ID', 'Scheduled Start', 'Actual Start', 'Minutes Late', 'Job Site']]
                
                for record in report['late_start_records']:
                    late_data.append([
                        record['driver_name'],
                        record['asset_id'],
                        record['scheduled_start'],
                        record['actual_start'],
                        str(record['minutes_late']),
                        record['job_site']
                    ])
                
                late_table = Table(late_data, colWidths=[80, 60, 60, 60, 50, 150])
                late_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                content.append(late_table)
                content.append(Spacer(1, 12))
            
            # Add early end drivers
            if report['early_end_records']:
                early_heading = Paragraph("Early End Drivers", heading_style)
                content.append(early_heading)
                content.append(Spacer(1, 6))
                
                early_data = [['Driver', 'Asset ID', 'Scheduled End', 'Actual End', 'Minutes Early', 'Job Site']]
                
                for record in report['early_end_records']:
                    early_data.append([
                        record['driver_name'],
                        record['asset_id'],
                        record['scheduled_end'],
                        record['actual_end'],
                        str(record['minutes_early']),
                        record['job_site']
                    ])
                
                early_table = Table(early_data, colWidths=[80, 60, 60, 60, 50, 150])
                early_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                content.append(early_table)
                content.append(Spacer(1, 12))
            
            # Add not on job drivers
            if report['not_on_job_records']:
                not_on_job_heading = Paragraph("Not On Job Drivers", heading_style)
                content.append(not_on_job_heading)
                content.append(Spacer(1, 6))
                
                not_on_job_data = [['Driver', 'Asset ID', 'Job Site', 'Current Location', 'Distance', 'Last Update']]
                
                for record in report['not_on_job_records']:
                    not_on_job_data.append([
                        record['driver_name'],
                        record['asset_id'],
                        record['job_site'],
                        record.get('current_location', 'Unknown'),
                        record.get('distance_from_job', 'N/A'),
                        record.get('last_update', 'N/A')
                    ])
                
                not_on_job_table = Table(not_on_job_data, colWidths=[80, 60, 100, 100, 50, 60])
                not_on_job_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.pink),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                content.append(not_on_job_table)
            
            # Build the PDF
            doc.build(content)
            
            logger.info(f"PDF report saved to {output_path}")
            
            return output_path
        except Exception as e:
            logger.error(f"Error exporting PDF report: {e}")
            return None
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """
        Find a column in a DataFrame from a list of possible names
        
        Args:
            df: DataFrame to search
            possible_names: List of possible column names
            
        Returns:
            Column name if found, None otherwise
        """
        for name in possible_names:
            if name in df.columns:
                return name
        return None
    
    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """
        Parse a time string to a datetime object
        
        Args:
            time_str: Time string to parse
            
        Returns:
            Datetime object if successful, None otherwise
        """
        if not time_str:
            return None
            
        try:
            # Handle military time format
            if ':' in time_str and len(time_str) <= 5:
                # Add date part
                time_str = f"{self.date_str} {time_str}"
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M')
            
            # Handle AM/PM format
            if 'AM' in time_str.upper() or 'PM' in time_str.upper():
                time_str = f"{self.date_str} {time_str}"
                return datetime.strptime(time_str, '%Y-%m-%d %I:%M %p')
            
            # Try standard formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y %H:%M']:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            
            # Try Excel serial date format
            try:
                return datetime.fromordinal(int(float(time_str)) + 693594)
            except (ValueError, OverflowError):
                pass
            
            logger.warning(f"Could not parse time string: {time_str}")
            return None
        except Exception as e:
            logger.error(f"Error parsing time string {time_str}: {e}")
            return None