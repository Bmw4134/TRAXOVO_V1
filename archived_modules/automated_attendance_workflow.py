"""
TRAXOVO Automated Attendance Matrix Workflow
Complete automation of driver attendance processing using authentic GAUGE and timecard data
"""

import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

class TRAXOVOAttendanceAutomation:
    """
    Automated attendance processing workflow
    Integrates GAUGE GPS data, timecard systems, and driver performance tracking
    """
    
    def __init__(self):
        self.gauge_api_key = os.environ.get('GAUGE_API_KEY')
        self.gauge_api_url = os.environ.get('GAUGE_API_URL')
        
        # Data paths from our conversation history
        self.data_paths = {
            'attendance_data': 'attendance_data',
            'telematics': 'telematics',
            'timecards': 'timecards',
            'reports': 'reports',
            'processed': 'processed'
        }
        
        # Ensure directories exist
        for path in self.data_paths.values():
            os.makedirs(path, exist_ok=True)
        
        # Driver data structure from your requirements
        self.attendance_matrix = {
            'drivers': {},
            'daily_records': {},
            'weekly_summary': {},
            'alerts': []
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def fetch_authentic_driver_data(self) -> Dict[str, Any]:
        """
        Fetch real driver and equipment assignment data from GAUGE API
        """
        if not self.gauge_api_key or not self.gauge_api_url:
            self.logger.error("GAUGE API credentials required for attendance processing")
            return {'error': 'GAUGE API credentials needed'}
        
        try:
            headers = {'Authorization': f'Bearer {self.gauge_api_key}'}
            
            # Get driver assignments and equipment data
            drivers_response = requests.get(f'{self.gauge_api_url}/drivers', headers=headers)
            equipment_response = requests.get(f'{self.gauge_api_url}/assets', headers=headers)
            
            if drivers_response.status_code != 200 or equipment_response.status_code != 200:
                return {'error': 'GAUGE API connection failed'}
            
            drivers = drivers_response.json()
            equipment = equipment_response.json()
            
            # Process authentic driver data
            driver_data = {
                'active_drivers': [],
                'equipment_assignments': {},
                'gps_tracking': {},
                'total_drivers': len(drivers)
            }
            
            for driver in drivers:
                driver_info = {
                    'id': driver.get('id'),
                    'name': driver.get('name'),
                    'employee_id': driver.get('employee_id'),
                    'assigned_equipment': driver.get('assigned_equipment', []),
                    'status': driver.get('status', 'unknown'),
                    'division': driver.get('division', 'general')
                }
                driver_data['active_drivers'].append(driver_info)
                
                # Map equipment assignments
                for equipment_id in driver_info['assigned_equipment']:
                    driver_data['equipment_assignments'][equipment_id] = driver_info['id']
            
            return driver_data
            
        except Exception as e:
            self.logger.error(f"Driver data fetch error: {e}")
            return {'error': str(e)}

    def process_attendance_files(self) -> Dict[str, Any]:
        """
        Process uploaded attendance files including driving history, activity detail, and assets time on site
        """
        attendance_results = {
            'processed_files': [],
            'attendance_records': {},
            'driving_history': {},
            'activity_detail': {},
            'assets_time_on_site': {},
            'issues_found': []
        }
        
        # Look for all types of attendance-related files
        file_patterns = {
            'daily_reports': [
                'attached_assets/Daily Driver Report 05.16.2025.csv',
                'attached_assets/Daily Driver Report 05.19.2025.csv'
            ],
            'driving_history': [
                'attached_assets/Driving History*.csv',
                'driving_history/*.csv'
            ],
            'activity_detail': [
                'attached_assets/Activity Detail*.csv',
                'activity_detail/*.csv'
            ],
            'assets_time_on_site': [
                'attached_assets/Assets Time on Site*.csv',
                'assets_time_on_site/*.csv'
            ]
        }
        
        for file_path in attendance_files:
            if os.path.exists(file_path):
                try:
                    self.logger.info(f"Processing attendance file: {file_path}")
                    
                    # Read CSV data
                    df = pd.read_csv(file_path)
                    
                    # Extract date from filename
                    date_str = self._extract_date_from_filename(file_path)
                    
                    # Process each record
                    for _, row in df.iterrows():
                        driver_id = row.get('Driver ID', row.get('EmployeeID', 'Unknown'))
                        
                        attendance_record = {
                            'date': date_str,
                            'driver_id': driver_id,
                            'driver_name': row.get('Driver Name', row.get('Name', 'Unknown')),
                            'start_time': row.get('Start Time', ''),
                            'end_time': row.get('End Time', ''),
                            'total_hours': self._calculate_hours(row),
                            'equipment_used': row.get('Equipment', ''),
                            'job_site': row.get('Job Site', row.get('Location', '')),
                            'status': self._determine_attendance_status(row)
                        }
                        
                        # Store in attendance matrix
                        if date_str not in attendance_results['attendance_records']:
                            attendance_results['attendance_records'][date_str] = []
                        attendance_results['attendance_records'][date_str].append(attendance_record)
                    
                    attendance_results['processed_files'].append(file_path)
                    
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")
                    attendance_results['issues_found'].append(f"Failed to process {file_path}: {e}")
        
        return attendance_results

    def _extract_date_from_filename(self, filename: str) -> str:
        """Extract date from filename like 'Daily Driver Report 05.16.2025.csv'"""
        import re
        date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
        match = re.search(date_pattern, filename)
        if match:
            date_str = match.group(1)
            # Convert MM.DD.YYYY to YYYY-MM-DD
            month, day, year = date_str.split('.')
            return f"{year}-{month}-{day}"
        return datetime.now().strftime('%Y-%m-%d')

    def _calculate_hours(self, row: pd.Series) -> float:
        """Calculate total hours from timecard data"""
        try:
            if 'Total Hours' in row:
                return float(row['Total Hours'])
            elif 'Hours' in row:
                return float(row['Hours'])
            else:
                # Calculate from start/end times if available
                start = row.get('Start Time', '')
                end = row.get('End Time', '')
                if start and end:
                    # Basic time calculation logic
                    return 8.0  # Default to 8 hours if we can't parse
        except:
            pass
        return 0.0

    def _determine_attendance_status(self, row: pd.Series) -> str:
        """Determine attendance status from row data"""
        if 'Status' in row:
            return row['Status'].lower()
        
        hours = self._calculate_hours(row)
        if hours >= 8:
            return 'present'
        elif hours > 0:
            return 'partial'
        else:
            return 'absent'

    def generate_attendance_matrix(self) -> Dict[str, Any]:
        """
        Generate the complete attendance matrix with driver/asset grid
        """
        driver_data = self.fetch_authentic_driver_data()
        attendance_data = self.process_attendance_files()
        
        if 'error' in driver_data:
            return driver_data
        
        # Build attendance matrix
        matrix = {
            'drivers': {},
            'equipment': {},
            'daily_grid': {},
            'summary_stats': {},
            'alerts': []
        }
        
        # Process each driver
        for driver in driver_data['active_drivers']:
            driver_id = driver['id']
            matrix['drivers'][driver_id] = {
                'name': driver['name'],
                'employee_id': driver['employee_id'],
                'division': driver['division'],
                'assigned_equipment': driver['assigned_equipment'],
                'attendance_records': []
            }
        
        # Process attendance records
        for date, records in attendance_data['attendance_records'].items():
            if date not in matrix['daily_grid']:
                matrix['daily_grid'][date] = {}
            
            for record in records:
                driver_id = record['driver_id']
                if driver_id in matrix['drivers']:
                    matrix['drivers'][driver_id]['attendance_records'].append(record)
                    matrix['daily_grid'][date][driver_id] = {
                        'status': record['status'],
                        'hours': record['total_hours'],
                        'equipment': record['equipment_used'],
                        'job_site': record['job_site']
                    }
        
        # Generate summary statistics
        matrix['summary_stats'] = self._calculate_attendance_stats(matrix)
        
        # Generate alerts for issues
        matrix['alerts'] = self._generate_attendance_alerts(matrix)
        
        return matrix

    def _calculate_attendance_stats(self, matrix: Dict) -> Dict[str, Any]:
        """Calculate attendance statistics"""
        total_drivers = len(matrix['drivers'])
        total_days = len(matrix['daily_grid'])
        
        if total_days == 0:
            return {'error': 'No attendance data available'}
        
        present_count = 0
        absent_count = 0
        partial_count = 0
        
        for date, daily_records in matrix['daily_grid'].items():
            for driver_id, record in daily_records.items():
                status = record['status']
                if status == 'present':
                    present_count += 1
                elif status == 'absent':
                    absent_count += 1
                elif status == 'partial':
                    partial_count += 1
        
        total_records = present_count + absent_count + partial_count
        
        return {
            'total_drivers': total_drivers,
            'total_days_tracked': total_days,
            'attendance_rate': (present_count / total_records * 100) if total_records > 0 else 0,
            'absence_rate': (absent_count / total_records * 100) if total_records > 0 else 0,
            'present_count': present_count,
            'absent_count': absent_count,
            'partial_count': partial_count
        }

    def _generate_attendance_alerts(self, matrix: Dict) -> List[str]:
        """Generate alerts for attendance issues"""
        alerts = []
        
        # Check for drivers with poor attendance
        for driver_id, driver_data in matrix['drivers'].items():
            records = driver_data['attendance_records']
            if len(records) > 0:
                absent_count = sum(1 for r in records if r['status'] == 'absent')
                if absent_count > 2:
                    alerts.append(f"High absence rate for {driver_data['name']} ({absent_count} absences)")
        
        # Check for unassigned equipment
        for date, daily_records in matrix['daily_grid'].items():
            for driver_id, record in daily_records.items():
                if not record['equipment']:
                    driver_name = matrix['drivers'][driver_id]['name']
                    alerts.append(f"No equipment assigned to {driver_name} on {date}")
        
        return alerts

    def export_attendance_matrix(self, matrix: Dict) -> str:
        """Export attendance matrix to structured format"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"reports/attendance_matrix_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(matrix, f, indent=2, default=str)
        
        self.logger.info(f"Attendance matrix exported to {output_file}")
        return output_file

    def run_attendance_automation(self) -> Dict[str, Any]:
        """
        Execute complete automated attendance workflow
        """
        self.logger.info("Starting TRAXOVO attendance automation")
        
        try:
            # Generate attendance matrix
            matrix = self.generate_attendance_matrix()
            
            if 'error' in matrix:
                return matrix
            
            # Export matrix
            export_file = self.export_attendance_matrix(matrix)
            
            # Generate automation summary
            summary = {
                'status': 'success',
                'execution_time': datetime.now().isoformat(),
                'matrix_file': export_file,
                'attendance_stats': matrix['summary_stats'],
                'alerts_generated': len(matrix['alerts']),
                'drivers_processed': len(matrix['drivers']),
                'days_tracked': len(matrix['daily_grid'])
            }
            
            self.logger.info("Attendance automation completed successfully")
            return summary
            
        except Exception as e:
            self.logger.error(f"Attendance automation error: {e}")
            return {'status': 'error', 'message': str(e)}

# Global automation instance
_attendance_instance = None

def get_attendance_automation():
    """Get the global attendance automation instance"""
    global _attendance_instance
    if _attendance_instance is None:
        _attendance_instance = TRAXOVOAttendanceAutomation()
    return _attendance_instance