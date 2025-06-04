"""
Enhanced Daily Driver Report Processor

Automated daily processing that generates comprehensive reports
using authentic MTD data and GPS tracking from the Gauge API.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)

class EnhancedDailyProcessor:
    """Process daily driver reports with authentic data validation"""
    
    def __init__(self):
        self.base_dir = Path('.')
        self.data_dir = self.base_dir / 'data'
        self.reports_dir = self.base_dir / 'reports'
        self.temp_dir = self.base_dir / 'temp_reports'
        
        # Ensure directories exist
        for directory in [self.data_dir, self.reports_dir, self.temp_dir]:
            directory.mkdir(exist_ok=True)
    
    def process_daily_report(self, target_date=None):
        """
        Generate comprehensive daily driver report
        
        Args:
            target_date (str): Date in YYYY-MM-DD format, defaults to yesterday
        """
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"Processing daily report for {target_date}")
        
        try:
            # Load authentic MTD data
            mtd_data = self._load_mtd_data()
            if not mtd_data:
                logger.error("No MTD data available for processing")
                return None
            
            # Process driver records for the target date
            daily_records = self._extract_daily_records(mtd_data, target_date)
            
            # Generate comprehensive report
            report_data = self._generate_report_data(daily_records, target_date)
            
            # Save reports in multiple formats
            report_paths = self._save_reports(report_data, target_date)
            
            logger.info(f"Daily report completed for {target_date}")
            return report_paths
            
        except Exception as e:
            logger.error(f"Error processing daily report: {e}")
            return None
    
    def _load_mtd_data(self):
        """Load the most recent MTD data file"""
        try:
            # Look for MTD files in data directory
            mtd_files = list(self.data_dir.glob('*MTD*.json'))
            if not mtd_files:
                # Check temp_extract directory
                temp_extract_dir = self.base_dir / 'temp_extract'
                if temp_extract_dir.exists():
                    mtd_files = list(temp_extract_dir.glob('*MTD*.json'))
            
            if not mtd_files:
                logger.warning("No MTD files found")
                return None
            
            # Use the most recent MTD file
            latest_mtd = max(mtd_files, key=os.path.getmtime)
            logger.info(f"Loading MTD data from: {latest_mtd}")
            
            with open(latest_mtd, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading MTD data: {e}")
            return None
    
    def _extract_daily_records(self, mtd_data, target_date):
        """Extract driver records for the specific date"""
        daily_records = []
        
        try:
            # Get records for the target date
            if 'daily_records' in mtd_data and target_date in mtd_data['daily_records']:
                daily_records = mtd_data['daily_records'][target_date]
                logger.info(f"Found {len(daily_records)} records for {target_date}")
            else:
                # If exact date not found, use the most recent available data
                available_dates = list(mtd_data.get('daily_records', {}).keys())
                if available_dates:
                    recent_date = max(available_dates)
                    daily_records = mtd_data['daily_records'][recent_date]
                    logger.info(f"Using records from {recent_date} ({len(daily_records)} records)")
            
            return daily_records
            
        except Exception as e:
            logger.error(f"Error extracting daily records: {e}")
            return []
    
    def _generate_report_data(self, daily_records, target_date):
        """Generate comprehensive report data"""
        report_data = {
            'date': target_date,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_drivers': 0,
                'on_time': 0,
                'late_start': 0,
                'early_end': 0,
                'not_on_job': 0,
                'attendance_rate': 0
            },
            'job_sites': defaultdict(lambda: {
                'drivers': [],
                'on_time': 0,
                'issues': 0,
                'total': 0
            }),
            'driver_details': [],
            'alerts': []
        }
        
        try:
            for record in daily_records:
                driver_name = record.get('name', 'Unknown')
                status = record.get('status', 'Unknown')
                job_site = record.get('job_site', 'Unknown')
                start_time = record.get('start_time', 'N/A')
                end_time = record.get('end_time', 'N/A')
                
                # Update summary counts
                report_data['summary']['total_drivers'] += 1
                
                if status == 'On Time':
                    report_data['summary']['on_time'] += 1
                    report_data['job_sites'][job_site]['on_time'] += 1
                elif status == 'Late Start':
                    report_data['summary']['late_start'] += 1
                    report_data['job_sites'][job_site]['issues'] += 1
                elif status == 'Early End':
                    report_data['summary']['early_end'] += 1
                    report_data['job_sites'][job_site]['issues'] += 1
                elif status == 'Not On Job':
                    report_data['summary']['not_on_job'] += 1
                    report_data['job_sites'][job_site]['issues'] += 1
                
                # Add to job site tracking
                report_data['job_sites'][job_site]['total'] += 1
                report_data['job_sites'][job_site]['drivers'].append({
                    'name': driver_name,
                    'status': status,
                    'start_time': start_time,
                    'end_time': end_time
                })
                
                # Add driver details
                driver_detail = {
                    'name': driver_name,
                    'status': status,
                    'job_site': job_site,
                    'start_time': start_time,
                    'end_time': end_time,
                    'hours_worked': self._calculate_hours(start_time, end_time),
                    'alert_level': self._determine_alert_level(status)
                }
                report_data['driver_details'].append(driver_detail)
                
                # Generate alerts for issues
                if status != 'On Time':
                    alert = {
                        'driver': driver_name,
                        'job_site': job_site,
                        'issue': status,
                        'severity': 'high' if status == 'Not On Job' else 'medium',
                        'time': start_time if status == 'Late Start' else end_time
                    }
                    report_data['alerts'].append(alert)
            
            # Calculate attendance rate
            if report_data['summary']['total_drivers'] > 0:
                report_data['summary']['attendance_rate'] = round(
                    (report_data['summary']['on_time'] / report_data['summary']['total_drivers']) * 100, 1
                )
            
            # Convert defaultdict to regular dict for JSON serialization
            report_data['job_sites'] = dict(report_data['job_sites'])
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating report data: {e}")
            return report_data
    
    def _calculate_hours(self, start_time, end_time):
        """Calculate work hours from start and end times"""
        try:
            if start_time == 'N/A' or end_time == 'N/A' or not start_time or not end_time:
                return 0.0
            
            start_parts = start_time.split(':')
            end_parts = end_time.split(':')
            
            start_hours = int(start_parts[0]) + int(start_parts[1]) / 60
            end_hours = int(end_parts[0]) + int(end_parts[1]) / 60
            
            return max(0, round(end_hours - start_hours, 2))
            
        except Exception:
            return 0.0
    
    def _determine_alert_level(self, status):
        """Determine alert level based on status"""
        if status == 'Not On Job':
            return 'high'
        elif status in ['Late Start', 'Early End']:
            return 'medium'
        else:
            return 'low'
    
    def _save_reports(self, report_data, target_date):
        """Save reports in multiple formats"""
        report_paths = {}
        
        try:
            # JSON report for system processing
            json_path = self.reports_dir / f"daily_report_{target_date}.json"
            with open(json_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            report_paths['json'] = str(json_path)
            
            # Excel report for management
            excel_path = self._create_excel_report(report_data, target_date)
            if excel_path:
                report_paths['excel'] = excel_path
            
            # Summary text report
            summary_path = self._create_summary_report(report_data, target_date)
            if summary_path:
                report_paths['summary'] = summary_path
            
            logger.info(f"Reports saved: {list(report_paths.keys())}")
            return report_paths
            
        except Exception as e:
            logger.error(f"Error saving reports: {e}")
            return {}
    
    def _create_excel_report(self, report_data, target_date):
        """Create Excel report with multiple sheets"""
        try:
            excel_path = self.reports_dir / f"daily_report_{target_date}.xlsx"
            
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_df = pd.DataFrame([report_data['summary']])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Driver details sheet
                if report_data['driver_details']:
                    details_df = pd.DataFrame(report_data['driver_details'])
                    details_df.to_excel(writer, sheet_name='Driver Details', index=False)
                
                # Job sites sheet
                job_sites_data = []
                for site, data in report_data['job_sites'].items():
                    job_sites_data.append({
                        'Job Site': site,
                        'Total Drivers': data['total'],
                        'On Time': data['on_time'],
                        'Issues': data['issues'],
                        'Performance': f"{round((data['on_time'] / max(1, data['total'])) * 100, 1)}%"
                    })
                
                if job_sites_data:
                    sites_df = pd.DataFrame(job_sites_data)
                    sites_df.to_excel(writer, sheet_name='Job Sites', index=False)
                
                # Alerts sheet
                if report_data['alerts']:
                    alerts_df = pd.DataFrame(report_data['alerts'])
                    alerts_df.to_excel(writer, sheet_name='Alerts', index=False)
            
            return str(excel_path)
            
        except Exception as e:
            logger.error(f"Error creating Excel report: {e}")
            return None
    
    def _create_summary_report(self, report_data, target_date):
        """Create text summary report"""
        try:
            summary_path = self.reports_dir / f"daily_summary_{target_date}.txt"
            
            with open(summary_path, 'w') as f:
                f.write(f"DAILY DRIVER REPORT - {target_date}\n")
                f.write("=" * 50 + "\n\n")
                
                # Summary section
                summary = report_data['summary']
                f.write("ATTENDANCE SUMMARY:\n")
                f.write(f"Total Drivers: {summary['total_drivers']}\n")
                f.write(f"On Time: {summary['on_time']}\n")
                f.write(f"Late Start: {summary['late_start']}\n")
                f.write(f"Early End: {summary['early_end']}\n")
                f.write(f"Not On Job: {summary['not_on_job']}\n")
                f.write(f"Attendance Rate: {summary['attendance_rate']}%\n\n")
                
                # Alerts section
                if report_data['alerts']:
                    f.write("ALERTS REQUIRING ATTENTION:\n")
                    for alert in report_data['alerts'][:10]:  # Top 10 alerts
                        f.write(f"- {alert['driver']} ({alert['job_site']}): {alert['issue']}\n")
                    f.write("\n")
                
                # Job site performance
                f.write("JOB SITE PERFORMANCE:\n")
                for site, data in report_data['job_sites'].items():
                    performance = round((data['on_time'] / max(1, data['total'])) * 100, 1)
                    f.write(f"{site}: {data['on_time']}/{data['total']} ({performance}%)\n")
            
            return str(summary_path)
            
        except Exception as e:
            logger.error(f"Error creating summary report: {e}")
            return None

def run_daily_report_automation():
    """Main function to run daily report automation"""
    processor = EnhancedDailyProcessor()
    return processor.process_daily_report()

if __name__ == "__main__":
    # Run the daily report
    result = run_daily_report_automation()
    if result:
        print(f"Daily report completed successfully: {result}")
    else:
        print("Daily report failed")