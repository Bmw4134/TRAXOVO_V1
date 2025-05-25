"""
TRAXORA Fleet Management System - Automatic Attendance Processor

This module automates the daily driver attendance report generation by:
1. Detecting and processing newly uploaded data files
2. Running the attendance pipeline with intelligent fallbacks
3. Generating reports in multiple formats (JSON, Excel, PDF)
4. Maintaining a processing log for traceability

Designed to run either on-demand or via scheduler to eliminate manual work.
"""

import os
import json
import logging
import pandas as pd
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Import pipeline modules
from utils.attendance_pipeline_v2 import (
    process_attendance_data, 
    generate_attendance_report,
    classify_attendance,
    normalize_driver_name,
    parse_datetime
)

# Configure logging
logger = logging.getLogger(__name__)

class AutoAttendanceProcessor:
    """
    Automated attendance processing system for daily driver reports
    
    Features:
    - Auto-detection of required data files
    - Intelligent file type recognition
    - Cross-validation between multiple data sources
    - Graceful fallbacks when data is incomplete
    - Comprehensive audit trail
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the auto attendance processor
        
        Args:
            base_dir: Base directory for data files (default: app root/data)
        """
        self.base_dir = base_dir or os.path.join(os.getcwd(), 'data')
        self.uploads_dir = os.path.join(self.base_dir, 'uploads')
        self.results_dir = os.path.join(self.base_dir, 'results')
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        
        # Create directories if they don't exist
        for directory in [self.base_dir, self.uploads_dir, self.results_dir, self.logs_dir]:
            os.makedirs(directory, exist_ok=True)
            
        # File type patterns for auto-detection
        self.file_patterns = {
            'driving_history': ['driving', 'history', 'drive'],
            'activity_detail': ['activity', 'detail', 'activities'],
            'time_on_site': ['time', 'site', 'assets', 'onsite']
        }
        
        # Processing status tracking
        self.processing_log = []
        
    def detect_file_type(self, filename: str) -> Optional[str]:
        """
        Auto-detect file type based on filename
        
        Args:
            filename: Name of the file to detect
            
        Returns:
            str: Detected file type or None if unknown
        """
        filename_lower = filename.lower()
        
        for file_type, patterns in self.file_patterns.items():
            if any(pattern in filename_lower for pattern in patterns):
                return file_type
                
        return None
        
    def find_latest_files(self, date_str: Optional[str] = None) -> Dict[str, str]:
        """
        Find the latest available files for each required type
        
        Args:
            date_str: Optional specific date to find files for (YYYY-MM-DD)
            
        Returns:
            Dict: Dictionary of file types and their paths
        """
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            # Default to yesterday if no date specified
            target_date = (datetime.now() - timedelta(days=1)).date()
            date_str = target_date.strftime('%Y-%m-%d')
            
        # Look in date-specific directory first
        date_dir = os.path.join(self.uploads_dir, date_str)
        
        # Fall back to main uploads directory if date directory doesn't exist
        if not os.path.exists(date_dir):
            date_dir = self.uploads_dir
            
        # Find files for each type
        latest_files = {
            'driving_history': None,
            'activity_detail': None,
            'time_on_site': None
        }
        
        # First pass: check exact date directory
        if os.path.exists(os.path.join(self.uploads_dir, date_str)):
            for filename in os.listdir(os.path.join(self.uploads_dir, date_str)):
                file_path = os.path.join(self.uploads_dir, date_str, filename)
                if not os.path.isfile(file_path):
                    continue
                    
                file_type = self.detect_file_type(filename)
                if file_type and file_type in latest_files and not latest_files[file_type]:
                    latest_files[file_type] = file_path
        
        # Second pass: check main uploads directory if we're still missing files
        if None in latest_files.values():
            for filename in os.listdir(self.uploads_dir):
                file_path = os.path.join(self.uploads_dir, filename)
                if not os.path.isfile(file_path):
                    continue
                    
                file_type = self.detect_file_type(filename)
                if file_type and file_type in latest_files and not latest_files[file_type]:
                    # Check if file is within acceptable date range (±7 days)
                    file_stat = os.stat(file_path)
                    file_date = datetime.fromtimestamp(file_stat.st_mtime).date()
                    date_diff = abs((target_date - file_date).days)
                    
                    if date_diff <= 7:  # Within a week of target date
                        latest_files[file_type] = file_path
                        
        # Check if we found at least one file
        if all(v is None for v in latest_files.values()):
            logger.warning(f"No data files found for date {date_str}")
            
        return latest_files
    
    def process_date(self, date_str: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """
        Process attendance data for a specific date
        
        Args:
            date_str: Date to process (YYYY-MM-DD) or None for yesterday
            force: Force processing even if some data is missing
            
        Returns:
            Dict: Processing results and metadata
        """
        start_time = datetime.now()
        
        if not date_str:
            # Default to yesterday
            date_str = (datetime.now() - timedelta(days=1)).date().strftime('%Y-%m-%d')
            
        logger.info(f"Processing attendance data for date: {date_str}")
        
        # Find data files
        data_files = self.find_latest_files(date_str)
        logger.info(f"Found data files: {data_files}")
        
        # Check if we have enough data
        missing_files = [k for k, v in data_files.items() if v is None]
        if missing_files and not force:
            logger.warning(f"Missing required files: {missing_files}. Use force=True to process anyway.")
            return {
                'success': False,
                'date': date_str,
                'error': f"Missing required files: {', '.join(missing_files)}",
                'files_found': data_files,
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Load and process data
            attendance_data = self._process_files(date_str, data_files)
            
            # Generate report
            report_path = os.path.join(self.results_dir, f"attendance_report_{date_str}.json")
            with open(report_path, 'w') as f:
                json.dump(attendance_data, f, indent=2)
                
            # Generate Excel report
            excel_path = os.path.join(self.results_dir, f"attendance_report_{date_str}.xlsx")
            self._generate_excel_report(attendance_data, excel_path)
            
            # Update processing log
            processing_duration = (datetime.now() - start_time).total_seconds()
            log_entry = {
                'date': date_str,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'files_used': {k: os.path.basename(v) if v else None for k, v in data_files.items()},
                'records_processed': len(attendance_data.get('driver_records', [])),
                'processing_time_seconds': processing_duration,
                'report_path': report_path
            }
            self.processing_log.append(log_entry)
            
            # Save processing log
            log_path = os.path.join(self.logs_dir, f"processing_log_{date_str}.json")
            with open(log_path, 'w') as f:
                json.dump(log_entry, f, indent=2)
                
            return {
                'success': True,
                'date': date_str,
                'records_processed': len(attendance_data.get('driver_records', [])),
                'report_path': report_path,
                'excel_path': excel_path,
                'processing_time_seconds': processing_duration,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing attendance data: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Update processing log
            log_entry = {
                'date': date_str,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'files_used': {k: os.path.basename(v) if v else None for k, v in data_files.items()},
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            self.processing_log.append(log_entry)
            
            # Save processing log
            log_path = os.path.join(self.logs_dir, f"processing_log_{date_str}.json")
            with open(log_path, 'w') as f:
                json.dump(log_entry, f, indent=2)
                
            return {
                'success': False,
                'date': date_str,
                'error': str(e),
                'files_found': data_files,
                'timestamp': datetime.now().isoformat()
            }
    
    def _process_files(self, date_str: str, data_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Process the data files to generate attendance data
        
        Args:
            date_str: Date string (YYYY-MM-DD)
            data_files: Dictionary of file types and paths
            
        Returns:
            Dict: Processed attendance data
        """
        # Load data files
        driving_history_df = None
        activity_detail_df = None
        time_on_site_df = None
        
        if data_files.get('driving_history'):
            try:
                driving_history_df = pd.read_csv(data_files['driving_history'])
                logger.info(f"Loaded driving history data: {len(driving_history_df)} records")
            except Exception as e:
                logger.error(f"Error loading driving history data: {str(e)}")
                
        if data_files.get('activity_detail'):
            try:
                activity_detail_df = pd.read_csv(data_files['activity_detail'])
                logger.info(f"Loaded activity detail data: {len(activity_detail_df)} records")
            except Exception as e:
                logger.error(f"Error loading activity detail data: {str(e)}")
                
        if data_files.get('time_on_site'):
            try:
                time_on_site_df = pd.read_csv(data_files['time_on_site'])
                logger.info(f"Loaded time on site data: {len(time_on_site_df)} records")
            except Exception as e:
                logger.error(f"Error loading time on site data: {str(e)}")
        
        # Process attendance data
        # Use the attendance_pipeline_v2 module for the core processing logic
        processed_data = process_attendance_data(
            date_str=date_str,
            driving_history_df=driving_history_df,
            activity_detail_df=activity_detail_df,
            time_on_site_df=time_on_site_df
        )
        
        return processed_data
    
    def _generate_excel_report(self, attendance_data: Dict[str, Any], output_path: str) -> None:
        """
        Generate Excel report from attendance data
        
        Args:
            attendance_data: Processed attendance data
            output_path: Path to save Excel report
        """
        try:
            # Extract driver records
            driver_records = attendance_data.get('driver_records', [])
            if not driver_records:
                logger.warning("No driver records found to generate Excel report")
                return
                
            # Create DataFrame from driver records
            df = pd.DataFrame(driver_records)
            
            # Ensure all required columns exist
            required_columns = [
                'driver_name', 'normalized_name', 'status', 'job_site',
                'start_time', 'end_time', 'total_hours'
            ]
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Create Excel writer
            with pd.ExcelWriter(output_path) as writer:
                # Summary sheet
                summary_data = {
                    'Date': attendance_data.get('date'),
                    'Total Drivers': len(driver_records),
                    'On Time': sum(1 for r in driver_records if r.get('status') == 'on_time'),
                    'Late Start': sum(1 for r in driver_records if r.get('status') == 'late'),
                    'Early End': sum(1 for r in driver_records if r.get('status') == 'early_end'),
                    'Not On Job': sum(1 for r in driver_records if r.get('status') == 'not_on_job'),
                    'Generated At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                summary_df = pd.DataFrame([summary_data])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Driver details sheet
                driver_df = df[['driver_name', 'status', 'job_site', 'start_time', 'end_time', 'total_hours']]
                driver_df.to_excel(writer, sheet_name='Driver Details', index=False)
                
                # Status sheets
                for status in ['on_time', 'late', 'early_end', 'not_on_job']:
                    status_df = df[df['status'] == status]
                    if not status_df.empty:
                        status_title = status.replace('_', ' ').title()
                        status_df.to_excel(writer, sheet_name=status_title, index=False)
                        
                # Job site sheet
                job_sites = df['job_site'].dropna().unique()
                for job_site in job_sites:
                    job_df = df[df['job_site'] == job_site]
                    if not job_df.empty and len(job_df) > 1:  # Only if we have multiple drivers
                        job_site_name = str(job_site)[:31]  # Excel sheet name length limit
                        job_df.to_excel(writer, sheet_name=job_site_name, index=False)
                        
            logger.info(f"Excel report generated: {output_path}")
            
        except Exception as e:
            logger.error(f"Error generating Excel report: {str(e)}")
            logger.error(traceback.format_exc())

# Standalone functions for direct use
def process_specific_date(date_str: str, force: bool = False) -> Dict[str, Any]:
    """
    Process attendance data for a specific date
    
    Args:
        date_str: Date to process (YYYY-MM-DD)
        force: Force processing even if some data is missing
        
    Returns:
        Dict: Processing results
    """
    processor = AutoAttendanceProcessor()
    return processor.process_date(date_str, force)
    
def process_yesterday() -> Dict[str, Any]:
    """
    Process attendance data for yesterday
    
    Returns:
        Dict: Processing results
    """
    yesterday = (datetime.now() - timedelta(days=1)).date().strftime('%Y-%m-%d')
    return process_specific_date(yesterday, force=True)
    
def process_date_range(start_date: str, end_date: str, force: bool = False) -> List[Dict[str, Any]]:
    """
    Process attendance data for a range of dates
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        force: Force processing even if some data is missing
        
    Returns:
        List: List of processing results for each date
    """
    processor = AutoAttendanceProcessor()
    
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    results = []
    current = start
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        result = processor.process_date(date_str, force)
        results.append(result)
        current += timedelta(days=1)
        
    return results

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Process yesterday's data when run directly
    result = process_yesterday()
    print(json.dumps(result, indent=2))