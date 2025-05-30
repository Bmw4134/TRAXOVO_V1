"""
GroundWorks Parser - Excel Timecard Processing
Processes uploaded GroundWorks timecard Excel files for attendance matrix
"""

import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class GroundWorksParser:
    """Parser for GroundWorks timecard Excel files"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
        self.employee_columns = ['employee_name', 'name', 'driver', 'operator', 'employee']
        self.time_columns = ['clock_in', 'start_time', 'time_in', 'punch_in']
        self.hours_columns = ['hours_worked', 'total_hours', 'hours', 'daily_hours']
        
    def parse_timecard_file(self, file_path: str) -> Dict:
        """Parse a single timecard file and extract attendance records"""
        try:
            # Determine file type and read accordingly
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Normalize column names
            df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]
            
            # Extract attendance records
            records = []
            
            for _, row in df.iterrows():
                record = self._extract_employee_record(row, df.columns)
                if record:
                    records.append(record)
            
            return {
                'success': True,
                'records': records,
                'source_file': os.path.basename(file_path),
                'record_count': len(records)
            }
            
        except Exception as e:
            logger.error(f"Error parsing timecard file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'source_file': os.path.basename(file_path),
                'record_count': 0
            }
    
    def _extract_employee_record(self, row: pd.Series, columns: List[str]) -> Optional[Dict]:
        """Extract individual employee attendance record from row"""
        try:
            # Find employee name
            employee_name = None
            for col in self.employee_columns:
                if col in columns and pd.notna(row.get(col)):
                    employee_name = str(row[col]).strip()
                    break
            
            if not employee_name:
                return None
            
            # Extract time information
            clock_in = self._find_value(row, self.time_columns, default='07:00')
            hours_worked = self._find_numeric_value(row, self.hours_columns, default=0.0)
            
            # Determine status based on hours and timing
            status_icon, gps_status = self._determine_status(clock_in, hours_worked)
            
            return {
                'employee_name': employee_name,
                'employee_id': row.get('employee_id', f"EMP{hash(employee_name) % 1000:03d}"),
                'asset_id': row.get('asset_id', row.get('equipment_id', 'TBD')),
                'job_id': row.get('job_id', row.get('job_code', '2019-044')),
                'clock_in': str(clock_in),
                'clock_out': str(row.get('clock_out', row.get('end_time', '17:00'))),
                'hours_worked': float(hours_worked),
                'status_icon': status_icon,
                'gps_status': gps_status,
                'division': row.get('division', row.get('dept', 'Ground Works')),
                'date': row.get('date', datetime.now().strftime('%Y-%m-%d'))
            }
            
        except Exception as e:
            logger.warning(f"Error extracting record: {e}")
            return None
    
    def _find_value(self, row: pd.Series, possible_columns: List[str], default: str = '') -> str:
        """Find value from row using possible column names"""
        for col in possible_columns:
            if col in row.index and pd.notna(row.get(col)):
                return str(row[col])
        return default
    
    def _find_numeric_value(self, row: pd.Series, possible_columns: List[str], default: float = 0.0) -> float:
        """Find numeric value from row using possible column names"""
        for col in possible_columns:
            if col in row.index and pd.notna(row.get(col)):
                try:
                    return float(row[col])
                except (ValueError, TypeError):
                    continue
        return default
    
    def _determine_status(self, clock_in: str, hours_worked: float) -> tuple:
        """Determine status icon and GPS status based on timecard data"""
        try:
            if hours_worked == 0:
                return '❌', 'not_on_job'
            
            if isinstance(clock_in, str) and ':' in clock_in:
                hour = int(clock_in.split(':')[0])
                if hour > 7:  # Late start (after 7 AM)
                    return '🕒', 'late_start'
                elif hour <= 6:  # Very early start
                    return '✅', 'early_start'
                else:  # Normal start time
                    return '✅', 'on_time'
            
            # Default for valid hours
            return '✅', 'on_time'
            
        except Exception:
            return '❓', 'unknown'

def process_groundworks_files(file_paths: List[str]) -> Dict:
    """Process multiple GroundWorks timecard files"""
    parser = GroundWorksParser()
    all_records = []
    processing_results = []
    
    for file_path in file_paths:
        result = parser.parse_timecard_file(file_path)
        processing_results.append(result)
        
        if result['success']:
            all_records.extend(result['records'])
    
    return {
        'success': len(processing_results) > 0,
        'total_records': len(all_records),
        'records': all_records,
        'file_results': processing_results,
        'files_processed': len([r for r in processing_results if r['success']])
    }

def find_timecard_files(search_paths: List[str] = None) -> List[str]:
    """Find GroundWorks timecard files in specified directories"""
    if search_paths is None:
        search_paths = ['uploads', 'attached_assets', '.']
    
    timecard_files = []
    keywords = ['timecard', 'attendance', 'daily', 'report', 'hours']
    
    for path in search_paths:
        if not os.path.exists(path):
            continue
            
        for file in os.listdir(path):
            if any(keyword.lower() in file.lower() for keyword in keywords):
                if any(file.lower().endswith(ext) for ext in ['.xlsx', '.xls', '.csv']):
                    timecard_files.append(os.path.join(path, file))
    
    return sorted(timecard_files, key=os.path.getmtime, reverse=True)