"""
TRAXORA GENIUS CORE | Report Generator Module

This module builds categorized outputs like:
- PMR (NOJ) - Not On Job reports
- PMR (LATE) - Late reports
- PMR (EARLY) - Early End reports
- Full Daily Driver Report with summary metrics

All reports include detailed traceability, validation info, and confidence scores.

Also includes enhanced Activity Detail metrics for full visibility.
"""
import os
import logging
import json
from datetime import datetime, date, time
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

# Status constants
STATUS_ON_TIME = 'On Time'
STATUS_LATE = 'Late'
STATUS_EARLY_END = 'Early End'
STATUS_NOT_ON_JOB = 'Not On Job'
STATUS_UNKNOWN = 'Unknown'

class ReportGenerator:
    """Report generator for driver reporting pipeline"""
    
    def __init__(self, date_str=None, output_dir=None):
        """
        Initialize report generator

        Args:
            date_str (str, optional): Date string in YYYY-MM-DD format
            output_dir (str, optional): Output directory for reports
        """
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
        
        # Initialize report data
        self.report_data = {
            'date': self.date_str,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_drivers': 0,
                'on_time': 0,
                'late': 0,
                'early_end': 0,
                'not_on_job': 0,
                'unknown': 0,
                'avg_minutes_late': 0,
                'avg_minutes_early_end': 0
            },
            'drivers': [],
            'job_sites': {},
            'activity_metrics': {
                'activity_types': {},
                'activity_counts': {}
            }
        }
    
    def add_driver_data(self, driver_data, classification):
        """
        Add driver data to report

        Args:
            driver_data (dict): Driver data
            classification (dict): Classification results for the driver

        Returns:
            None
        """
        # Extract driver info
        driver_info = {
            'driver_name': driver_data.get('name', 'Unknown'),
            'normalized_name': driver_data.get('normalized_name', ''),
            'asset_id': next(iter(driver_data.get('assets', [])), None),
            'assets': list(driver_data.get('assets', [])),
            'status': classification.get('status', STATUS_UNKNOWN),
            'minutes_late': classification.get('minutes_late', 0),
            'minutes_early_end': classification.get('minutes_early_end', 0),
            'data_sources': list(driver_data.get('sources', {}).keys()),
            'validation_score': classification.get('validation_score', 0),
            'reasons': classification.get('reasons', []),
            'first_seen': driver_data.get('first_seen', '').isoformat() if driver_data.get('first_seen') else None,
            'last_seen': driver_data.get('last_seen', '').isoformat() if driver_data.get('last_seen') else None,
            'scheduled_start': driver_data.get('scheduled_start', '').isoformat() if driver_data.get('scheduled_start') else None,
            'scheduled_end': driver_data.get('scheduled_end', '').isoformat() if driver_data.get('scheduled_end') else None,
            'assigned_job': driver_data.get('assigned_job', None),
            'actual_job': driver_data.get('actual_job', None),
            'locations': [],
            'activity_metrics': {}
        }
        
        # Add locations from driving records
        for record in driver_data.get('driving_records', []):
            if record.get('latitude') and record.get('longitude'):
                driver_info['locations'].append({
                    'timestamp': record.get('timestamp', '').isoformat() if record.get('timestamp') else None,
                    'latitude': record.get('latitude'),
                    'longitude': record.get('longitude'),
                    'event': record.get('event', '')
                })
        
        # Add activity metrics
        if 'Activity Detail' in driver_data.get('sources', {}):
            activity_source = driver_data['sources']['Activity Detail']
            driver_info['activity_metrics'] = {
                'total_activities': activity_source.get('records', 0),
                'activity_types': activity_source.get('activity_types', {}),
                'files': list(activity_source.get('files', set()))
            }
            
            # Track activity types for summary
            for activity_type, count in activity_source.get('activity_types', {}).items():
                if activity_type not in self.report_data['activity_metrics']['activity_types']:
                    self.report_data['activity_metrics']['activity_types'][activity_type] = 0
                self.report_data['activity_metrics']['activity_types'][activity_type] += count
        
        # Add to report data
        self.report_data['drivers'].append(driver_info)
        
        # Update summary counts
        self.report_data['summary']['total_drivers'] += 1
        status_key = classification.get('status', STATUS_UNKNOWN).lower().replace(' ', '_')
        if status_key in self.report_data['summary']:
            self.report_data['summary'][status_key] += 1
        
        # Track job sites
        if driver_data.get('assigned_job'):
            job_number = driver_data['assigned_job']
            if job_number not in self.report_data['job_sites']:
                self.report_data['job_sites'][job_number] = {
                    'job_number': job_number,
                    'drivers': [],
                    'statuses': {
                        'on_time': 0,
                        'late': 0,
                        'early_end': 0,
                        'not_on_job': 0,
                        'unknown': 0
                    }
                }
            
            # Add driver to job site
            self.report_data['job_sites'][job_number]['drivers'].append(driver_info['driver_name'])
            
            # Update job site status counts
            status_key = classification.get('status', STATUS_UNKNOWN).lower().replace(' ', '_')
            if status_key in self.report_data['job_sites'][job_number]['statuses']:
                self.report_data['job_sites'][job_number]['statuses'][status_key] += 1
    
    def generate_summary(self):
        """
        Generate summary statistics for the report

        Returns:
            dict: Summary statistics
        """
        # Calculate averages
        total_late = sum(driver.get('minutes_late', 0) for driver in self.report_data['drivers'] if driver.get('status') == STATUS_LATE)
        late_count = self.report_data['summary'].get('late', 0)
        
        total_early = sum(driver.get('minutes_early_end', 0) for driver in self.report_data['drivers'] if driver.get('status') == STATUS_EARLY_END)
        early_count = self.report_data['summary'].get('early_end', 0)
        
        if late_count > 0:
            self.report_data['summary']['avg_minutes_late'] = total_late / late_count
        
        if early_count > 0:
            self.report_data['summary']['avg_minutes_early_end'] = total_early / early_count
        
        # Add additional activity metrics
        self.report_data['summary']['activity_metrics'] = {
            'total_activities': sum(driver.get('activity_metrics', {}).get('total_activities', 0) for driver in self.report_data['drivers']),
            'unique_activity_types': len(self.report_data['activity_metrics']['activity_types'])
        }
        
        # Add job site stats
        self.report_data['summary']['job_sites'] = {
            'total': len(self.report_data['job_sites']),
            'with_late_drivers': sum(1 for job in self.report_data['job_sites'].values() if job['statuses']['late'] > 0),
            'with_not_on_job': sum(1 for job in self.report_data['job_sites'].values() if job['statuses']['not_on_job'] > 0)
        }
        
        return self.report_data['summary']
    
    def save_json_report(self, filename=None):
        """
        Save report data as JSON

        Args:
            filename (str, optional): Output filename

        Returns:
            str: Path to saved file
        """
        # Generate summary first
        self.generate_summary()
        
        # Default filename
        if not filename:
            filename = f"driver_report_{self.date_str}.json"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Full output path
        output_path = os.path.join(self.output_dir, filename)
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(self.report_data, f, indent=2)
        
        logger.info(f"Saved JSON report to {output_path}")
        return output_path
    
    def save_excel_report(self, filename=None):
        """
        Save report data as Excel

        Args:
            filename (str, optional): Output filename

        Returns:
            str: Path to saved file
        """
        # Generate summary first
        self.generate_summary()
        
        # Default filename
        if not filename:
            filename = f"driver_report_{self.date_str}.xlsx"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Full output path
        output_path = os.path.join(self.output_dir, filename)
        
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet
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
                    'Avg Minutes Early End',
                    'Total Activities',
                    'Unique Activity Types',
                    'Total Job Sites',
                    'Job Sites with Late Drivers',
                    'Job Sites with Not On Job'
                ],
                'Value': [
                    self.report_data['date'],
                    self.report_data['generated_at'],
                    self.report_data['summary']['total_drivers'],
                    self.report_data['summary']['on_time'],
                    self.report_data['summary']['late'],
                    self.report_data['summary']['early_end'],
                    self.report_data['summary']['not_on_job'],
                    self.report_data['summary']['unknown'],
                    round(self.report_data['summary']['avg_minutes_late'], 1),
                    round(self.report_data['summary']['avg_minutes_early_end'], 1),
                    self.report_data['summary']['activity_metrics']['total_activities'],
                    self.report_data['summary']['activity_metrics']['unique_activity_types'],
                    self.report_data['summary']['job_sites']['total'],
                    self.report_data['summary']['job_sites']['with_late_drivers'],
                    self.report_data['summary']['job_sites']['with_not_on_job']
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Driver data sheet
            driver_data = []
            for driver in self.report_data['drivers']:
                driver_data.append({
                    'Driver Name': driver['driver_name'],
                    'Status': driver['status'],
                    'Asset ID': driver['asset_id'],
                    'Minutes Late': driver['minutes_late'],
                    'Minutes Early End': driver['minutes_early_end'],
                    'First Seen': driver['first_seen'],
                    'Last Seen': driver['last_seen'],
                    'Assigned Job': driver['assigned_job'],
                    'Actual Job': driver['actual_job'],
                    'Validation Score': driver['validation_score'],
                    'Data Sources': ', '.join(driver['data_sources']),
                    'Activity Count': driver.get('activity_metrics', {}).get('total_activities', 0)
                })
            
            if driver_data:
                driver_df = pd.DataFrame(driver_data)
                driver_df.to_excel(writer, sheet_name='Driver Data', index=False)
            
            # Late drivers sheet
            late_drivers = [driver for driver in self.report_data['drivers'] if driver['status'] == STATUS_LATE]
            if late_drivers:
                late_data = [{
                    'Driver Name': driver['driver_name'],
                    'Minutes Late': driver['minutes_late'],
                    'Asset ID': driver['asset_id'],
                    'Assigned Job': driver['assigned_job'],
                    'First Seen': driver['first_seen'],
                    'Scheduled Start': driver['scheduled_start'],
                    'Validation Score': driver['validation_score'],
                    'Reasons': ', '.join(driver['reasons'])
                } for driver in late_drivers]
                
                late_df = pd.DataFrame(late_data)
                late_df.to_excel(writer, sheet_name='Late Drivers', index=False)
            
            # Early end drivers sheet
            early_drivers = [driver for driver in self.report_data['drivers'] if driver['status'] == STATUS_EARLY_END]
            if early_drivers:
                early_data = [{
                    'Driver Name': driver['driver_name'],
                    'Minutes Early': driver['minutes_early_end'],
                    'Asset ID': driver['asset_id'],
                    'Assigned Job': driver['assigned_job'],
                    'Last Seen': driver['last_seen'],
                    'Scheduled End': driver['scheduled_end'],
                    'Validation Score': driver['validation_score'],
                    'Reasons': ', '.join(driver['reasons'])
                } for driver in early_drivers]
                
                early_df = pd.DataFrame(early_data)
                early_df.to_excel(writer, sheet_name='Early End Drivers', index=False)
            
            # Not on job drivers sheet
            noj_drivers = [driver for driver in self.report_data['drivers'] if driver['status'] == STATUS_NOT_ON_JOB]
            if noj_drivers:
                noj_data = [{
                    'Driver Name': driver['driver_name'],
                    'Asset ID': driver['asset_id'],
                    'Assigned Job': driver['assigned_job'],
                    'Actual Job': driver['actual_job'],
                    'First Seen': driver['first_seen'],
                    'Last Seen': driver['last_seen'],
                    'Validation Score': driver['validation_score'],
                    'Reasons': ', '.join(driver['reasons'])
                } for driver in noj_drivers]
                
                noj_df = pd.DataFrame(noj_data)
                noj_df.to_excel(writer, sheet_name='Not On Job Drivers', index=False)
            
            # Job sites sheet
            job_sites_data = []
            for job_number, job_data in self.report_data['job_sites'].items():
                job_sites_data.append({
                    'Job Number': job_number,
                    'Total Drivers': len(job_data['drivers']),
                    'On Time': job_data['statuses']['on_time'],
                    'Late': job_data['statuses']['late'],
                    'Early End': job_data['statuses']['early_end'],
                    'Not On Job': job_data['statuses']['not_on_job'],
                    'Unknown': job_data['statuses']['unknown']
                })
            
            if job_sites_data:
                job_sites_df = pd.DataFrame(job_sites_data)
                job_sites_df.to_excel(writer, sheet_name='Job Sites', index=False)
            
            # Activity types sheet
            activity_types_data = []
            for activity_type, count in self.report_data['activity_metrics']['activity_types'].items():
                activity_types_data.append({
                    'Activity Type': activity_type,
                    'Count': count
                })
            
            if activity_types_data:
                activity_types_df = pd.DataFrame(activity_types_data)
                activity_types_df.to_excel(writer, sheet_name='Activity Types', index=False)
        
        logger.info(f"Saved Excel report to {output_path}")
        return output_path
    
    def generate_categorized_reports(self):
        """
        Generate categorized reports for different driver statuses

        Returns:
            dict: Paths to generated report files
        """
        # Generate summary first
        self.generate_summary()
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        report_paths = {}
        
        # PMR (LATE) report
        late_drivers = [driver for driver in self.report_data['drivers'] if driver['status'] == STATUS_LATE]
        if late_drivers:
            late_report = {
                'date': self.date_str,
                'generated_at': datetime.now().isoformat(),
                'report_type': 'PMR (LATE)',
                'total_drivers': len(late_drivers),
                'avg_minutes_late': sum(driver['minutes_late'] for driver in late_drivers) / len(late_drivers),
                'drivers': late_drivers
            }
            
            late_report_path = os.path.join(self.output_dir, f"pmr_late_{self.date_str}.json")
            with open(late_report_path, 'w') as f:
                json.dump(late_report, f, indent=2)
            
            report_paths['late'] = late_report_path
        
        # PMR (EARLY) report
        early_drivers = [driver for driver in self.report_data['drivers'] if driver['status'] == STATUS_EARLY_END]
        if early_drivers:
            early_report = {
                'date': self.date_str,
                'generated_at': datetime.now().isoformat(),
                'report_type': 'PMR (EARLY)',
                'total_drivers': len(early_drivers),
                'avg_minutes_early': sum(driver['minutes_early_end'] for driver in early_drivers) / len(early_drivers),
                'drivers': early_drivers
            }
            
            early_report_path = os.path.join(self.output_dir, f"pmr_early_{self.date_str}.json")
            with open(early_report_path, 'w') as f:
                json.dump(early_report, f, indent=2)
            
            report_paths['early'] = early_report_path
        
        # PMR (NOJ) report
        noj_drivers = [driver for driver in self.report_data['drivers'] if driver['status'] == STATUS_NOT_ON_JOB]
        if noj_drivers:
            noj_report = {
                'date': self.date_str,
                'generated_at': datetime.now().isoformat(),
                'report_type': 'PMR (NOJ)',
                'total_drivers': len(noj_drivers),
                'drivers': noj_drivers
            }
            
            noj_report_path = os.path.join(self.output_dir, f"pmr_noj_{self.date_str}.json")
            with open(noj_report_path, 'w') as f:
                json.dump(noj_report, f, indent=2)
            
            report_paths['not_on_job'] = noj_report_path
        
        # Activity Detail Summary
        activity_summary = {
            'date': self.date_str,
            'generated_at': datetime.now().isoformat(),
            'report_type': 'Activity Detail Summary',
            'total_activities': self.report_data['summary']['activity_metrics']['total_activities'],
            'unique_activity_types': self.report_data['summary']['activity_metrics']['unique_activity_types'],
            'activity_types': self.report_data['activity_metrics']['activity_types'],
            'driver_activities': {
                driver['driver_name']: driver.get('activity_metrics', {})
                for driver in self.report_data['drivers']
                if driver.get('activity_metrics', {}).get('total_activities', 0) > 0
            }
        }
        
        activity_report_path = os.path.join(self.output_dir, f"activity_summary_{self.date_str}.json")
        with open(activity_report_path, 'w') as f:
            json.dump(activity_summary, f, indent=2)
        
        report_paths['activity'] = activity_report_path
        
        logger.info(f"Generated categorized reports: {', '.join(report_paths.keys())}")
        return report_paths
    
    def generate_all_reports(self):
        """
        Generate all report formats

        Returns:
            dict: Paths to all generated report files
        """
        report_paths = {}
        
        # Save JSON report
        json_path = self.save_json_report()
        report_paths['json'] = json_path
        
        # Save Excel report
        excel_path = self.save_excel_report()
        report_paths['excel'] = excel_path
        
        # Generate categorized reports
        categorized_paths = self.generate_categorized_reports()
        report_paths.update(categorized_paths)
        
        return report_paths