"""
GENIUS CORE SMART MTD INGESTION MODULE

This module provides the interface for processing Month-to-Date (MTD) data files
and generating accurate daily driver reports with strict data validation.
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

class MTDProcessor:
    """
    Month-to-Date (MTD) data processor with GENIUS CORE validation
    """
    
    def __init__(self):
        """Initialize the processor"""
        self.target_date = None
        self.target_date_obj = None
        
        # Create necessary directories
        os.makedirs('processed/driving_history', exist_ok=True)
        os.makedirs('processed/activity_detail', exist_ok=True)
        os.makedirs('reports/trace', exist_ok=True)
        os.makedirs('exports/daily_reports', exist_ok=True)
    
    def process_date(self, date_str: str) -> Dict[str, Any]:
        """
        Process a specific date with MTD data
        
        Args:
            date_str: Target date in YYYY-MM-DD format
            
        Returns:
            Dictionary with processed data and file paths
        """
        logger.info(f"Processing MTD data for date: {date_str}")
        
        self.target_date = date_str
        self.target_date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Find available MTD data files
        driving_history_file = self._find_latest_file('attached_assets', 'DrivingHistory')
        activity_detail_file = self._find_latest_file('attached_assets', 'ActivityDetail')
        
        if not driving_history_file and not activity_detail_file:
            logger.error("No MTD data files found")
            return {'error': 'No MTD data files found in attached_assets directory'}
        
        # Process MTD files
        driving_history_output = None
        activity_detail_output = None
        
        if driving_history_file:
            driving_history_output = self._process_driving_history(driving_history_file, date_str)
        
        if activity_detail_file:
            activity_detail_output = self._process_activity_detail(activity_detail_file, date_str)
        
        # Generate report
        report_data = self._generate_report(date_str, driving_history_output, activity_detail_output)
        
        # Save output
        output_json_path = f'exports/daily_reports/attendance_data_{date_str}.json'
        with open(output_json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        trace_path = f'reports/trace/mtd_trace_{date_str}.json'
        with open(trace_path, 'w') as f:
            json.dump({
                'date': date_str,
                'driving_history': driving_history_output,
                'activity_detail': activity_detail_output,
                'processing_details': {
                    'timestamp': datetime.now().isoformat(),
                    'module': 'GENIUS CORE SMART MTD INGESTION'
                }
            }, f, indent=2)
        
        return {
            'date': date_str,
            'report_data': report_data,
            'output_json_path': output_json_path,
            'trace_path': trace_path,
            'driving_history_output': driving_history_output,
            'activity_detail_output': activity_detail_output
        }
    
    def _find_latest_file(self, directory: str, prefix: str) -> Optional[str]:
        """
        Find the latest file with the given prefix in the directory
        
        Args:
            directory: Directory to search
            prefix: File prefix to match
            
        Returns:
            Path to the latest file, or None if not found
        """
        if not os.path.exists(directory):
            return None
        
        matching_files = [
            os.path.join(directory, f) for f in os.listdir(directory)
            if f.startswith(prefix) and (f.endswith('.csv') or f.endswith('.xlsx'))
        ]
        
        if not matching_files:
            return None
        
        # Return the most recently modified file
        return max(matching_files, key=os.path.getmtime)
    
    def _process_driving_history(self, file_path: str, date_str: str) -> Dict[str, Any]:
        """
        Process driving history data file
        
        Args:
            file_path: Path to the driving history file
            date_str: Target date in YYYY-MM-DD format
            
        Returns:
            Dictionary with processed data
        """
        logger.info(f"Processing driving history file: {file_path}")
        
        try:
            # Handle different file formats
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                # Try different CSV parsing options
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except Exception as e:
                    logger.warning(f"Standard CSV parsing failed: {e}")
                    try:
                        # Try with more flexible engine
                        df = pd.read_csv(file_path, encoding='utf-8', engine='python', sep=None, on_bad_lines='skip')
                    except Exception as e:
                        logger.warning(f"Python engine parsing failed: {e}")
                        # Last resort - very permissive options
                        df = pd.read_csv(file_path, on_bad_lines='skip', encoding='latin1')
            
            # Normalize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Look for date column
            date_col = None
            for col in df.columns:
                if 'date' in col.lower():
                    date_col = col
                    break
            
            if not date_col:
                logger.error("No date column found in driving history file")
                return {'error': 'No date column found in driving history file'}
            
            # Convert date strings to datetime
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
            # Filter for target date
            target_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            df_filtered = df[df[date_col].dt.date == target_date_obj].copy()
            
            logger.info(f"Filtered {len(df_filtered)} driving history records for {date_str}")
            
            # Save filtered data
            output_path = f'processed/driving_history/driving_history_{date_str}.csv'
            df_filtered.to_csv(output_path, index=False)
            
            return {
                'input_file': file_path,
                'output_file': output_path,
                'records_count': len(df_filtered),
                'columns': list(df_filtered.columns)
            }
        except Exception as e:
            logger.error(f"Error processing driving history file: {e}")
            return {'error': str(e)}
    
    def _process_activity_detail(self, file_path: str, date_str: str) -> Dict[str, Any]:
        """
        Process activity detail data file
        
        Args:
            file_path: Path to the activity detail file
            date_str: Target date in YYYY-MM-DD format
            
        Returns:
            Dictionary with processed data
        """
        logger.info(f"Processing activity detail file: {file_path}")
        
        try:
            # Handle different file formats
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                # Try different CSV parsing options
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except Exception as e:
                    logger.warning(f"Standard CSV parsing failed: {e}")
                    try:
                        # Try with more flexible engine
                        df = pd.read_csv(file_path, encoding='utf-8', engine='python', sep=None, on_bad_lines='skip')
                    except Exception as e:
                        logger.warning(f"Python engine parsing failed: {e}")
                        # Last resort - very permissive options
                        df = pd.read_csv(file_path, on_bad_lines='skip', encoding='latin1')
            
            # Normalize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Look for date column
            date_col = None
            for col in df.columns:
                if 'date' in col.lower():
                    date_col = col
                    break
            
            if not date_col:
                logger.error("No date column found in activity detail file")
                return {'error': 'No date column found in activity detail file'}
            
            # Convert date strings to datetime
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
            # Filter for target date
            target_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            df_filtered = df[df[date_col].dt.date == target_date_obj].copy()
            
            logger.info(f"Filtered {len(df_filtered)} activity detail records for {date_str}")
            
            # Save filtered data
            output_path = f'processed/activity_detail/activity_detail_{date_str}.csv'
            df_filtered.to_csv(output_path, index=False)
            
            return {
                'input_file': file_path,
                'output_file': output_path,
                'records_count': len(df_filtered),
                'columns': list(df_filtered.columns)
            }
        except Exception as e:
            logger.error(f"Error processing activity detail file: {e}")
            return {'error': str(e)}
    
    def _generate_report(self, date_str: str, driving_history: Optional[Dict[str, Any]], 
                        activity_detail: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a consolidated report
        
        Args:
            date_str: Target date in YYYY-MM-DD format
            driving_history: Driving history processing results
            activity_detail: Activity detail processing results
            
        Returns:
            Dictionary with report data
        """
        logger.info(f"Generating report for {date_str}")
        
        # Initialize report structure
        report = {
            'date': date_str,
            'formatted_date': datetime.strptime(date_str, '%Y-%m-%d').strftime('%A, %B %d, %Y'),
            'drivers': [],
            'late_start_records': [],
            'early_end_records': [],
            'not_on_job_records': [],
            'on_time_drivers': 0,
            'total_drivers': 0,
            'on_time_percent': 0,
            'data_sources': []
        }
        
        # Process driving history data
        driver_data = {}
        
        if driving_history and 'output_file' in driving_history and not driving_history.get('error'):
            report['data_sources'].append({
                'name': 'driving_history',
                'file': os.path.basename(driving_history['input_file']),
                'records': driving_history['records_count']
            })
            
            try:
                df = pd.read_csv(driving_history['output_file'])
                
                # Extract driver data
                for _, row in df.iterrows():
                    # Look for driver name and event columns
                    driver_col = None
                    for col in df.columns:
                        if 'driver' in col.lower():
                            driver_col = col
                            break
                    
                    if not driver_col:
                        continue
                    
                    driver_name = str(row[driver_col])
                    
                    if driver_name not in driver_data:
                        driver_data[driver_name] = {
                            'driver_name': driver_name,
                            'key_on_times': [],
                            'key_off_times': [],
                            'asset_ids': set(),
                            'locations': set()
                        }
                    
                    # Look for event type
                    event_col = None
                    for col in df.columns:
                        if 'event' in col.lower():
                            event_col = col
                            break
                    
                    if event_col:
                        event = str(row[event_col]).lower()
                        time_col = None
                        
                        # Look for time column
                        for col in df.columns:
                            if 'time' in col.lower() and 'timestamp' not in col.lower():
                                time_col = col
                                break
                        
                        if time_col:
                            time_str = str(row[time_col])
                            
                            if 'on' in event or 'start' in event:
                                driver_data[driver_name]['key_on_times'].append(time_str)
                            elif 'off' in event or 'end' in event:
                                driver_data[driver_name]['key_off_times'].append(time_str)
                    
                    # Look for asset or equipment ID
                    asset_col = None
                    for col in df.columns:
                        if 'asset' in col.lower() or 'equipment' in col.lower() or 'vehicle' in col.lower():
                            asset_col = col
                            break
                    
                    if asset_col:
                        asset_id = str(row[asset_col])
                        driver_data[driver_name]['asset_ids'].add(asset_id)
            except Exception as e:
                logger.error(f"Error processing driving history data: {e}")
        
        # Process activity detail data
        if activity_detail and 'output_file' in activity_detail and not activity_detail.get('error'):
            report['data_sources'].append({
                'name': 'activity_detail',
                'file': os.path.basename(activity_detail['input_file']),
                'records': activity_detail['records_count']
            })
            
            try:
                df = pd.read_csv(activity_detail['output_file'])
                
                # Extract driver data
                for _, row in df.iterrows():
                    # Look for driver name column
                    driver_col = None
                    for col in df.columns:
                        if 'driver' in col.lower():
                            driver_col = col
                            break
                    
                    if not driver_col:
                        continue
                    
                    driver_name = str(row[driver_col])
                    
                    if driver_name not in driver_data:
                        driver_data[driver_name] = {
                            'driver_name': driver_name,
                            'key_on_times': [],
                            'key_off_times': [],
                            'asset_ids': set(),
                            'locations': set()
                        }
                    
                    # Look for location
                    location_col = None
                    for col in df.columns:
                        if 'location' in col.lower() or 'site' in col.lower() or 'job' in col.lower():
                            location_col = col
                            break
                    
                    if location_col:
                        location = str(row[location_col])
                        driver_data[driver_name]['locations'].add(location)
                    
                    # Look for start time
                    start_col = None
                    for col in df.columns:
                        if 'start' in col.lower():
                            start_col = col
                            break
                    
                    if start_col and pd.notna(row[start_col]):
                        start_time = str(row[start_col])
                        driver_data[driver_name]['key_on_times'].append(start_time)
                    
                    # Look for end time
                    end_col = None
                    for col in df.columns:
                        if 'end' in col.lower():
                            end_col = col
                            break
                    
                    if end_col and pd.notna(row[end_col]):
                        end_time = str(row[end_col])
                        driver_data[driver_name]['key_off_times'].append(end_time)
                    
                    # Look for asset or equipment ID
                    asset_col = None
                    for col in df.columns:
                        if 'asset' in col.lower() or 'equipment' in col.lower() or 'vehicle' in col.lower():
                            asset_col = col
                            break
                    
                    if asset_col and pd.notna(row[asset_col]):
                        asset_id = str(row[asset_col])
                        driver_data[driver_name]['asset_ids'].add(asset_id)
            except Exception as e:
                logger.error(f"Error processing activity detail data: {e}")
        
        # Generate driver records
        for driver_name, data in driver_data.items():
            # Create driver record
            driver_record = {
                'driver_name': driver_name,
                'asset_id': next(iter(data['asset_ids'])) if data['asset_ids'] else 'Unknown',
                'key_on_time': min(data['key_on_times']) if data['key_on_times'] else None,
                'key_off_time': max(data['key_off_times']) if data['key_off_times'] else None,
                'job_site': next(iter(data['locations'])) if data['locations'] else 'Unknown',
                'verified': True,
                'classification': 'Unknown',
                'scheduled_start': '07:00',  # Default values
                'scheduled_end': '17:30'
            }
            
            # Classify driver status
            if not driver_record['key_on_time']:
                # Not On Job
                driver_record['classification'] = 'Not On Job'
                driver_record['status_reason'] = 'No Key On time recorded'
                
                report['not_on_job_records'].append({
                    'driver_name': driver_name,
                    'asset_id': driver_record['asset_id'],
                    'job_site': driver_record['job_site'],
                    'current_location': 'Unknown',
                    'distance_from_job': 'N/A',
                    'last_update': 'N/A'
                })
            else:
                # Parse times
                try:
                    # Try different time formats
                    key_on_dt = None
                    scheduled_start_dt = datetime.strptime(driver_record['scheduled_start'], '%H:%M')
                    
                    try:
                        # Try time format with date
                        if ' ' in driver_record['key_on_time'] and ':' in driver_record['key_on_time']:
                            key_on_dt = datetime.strptime(driver_record['key_on_time'], '%Y-%m-%d %H:%M:%S')
                        # Try time-only format
                        elif ':' in driver_record['key_on_time'] and len(driver_record['key_on_time']) <= 8:
                            # Add date part
                            key_on_dt = datetime.strptime(driver_record['key_on_time'], '%H:%M:%S')
                    except ValueError:
                        try:
                            key_on_dt = datetime.strptime(driver_record['key_on_time'], '%H:%M')
                        except ValueError:
                            try:
                                # Try with AM/PM
                                if 'AM' in driver_record['key_on_time'].upper() or 'PM' in driver_record['key_on_time'].upper():
                                    key_on_dt = datetime.strptime(driver_record['key_on_time'], '%I:%M %p')
                            except ValueError:
                                pass
                    
                    if key_on_dt:
                        # Check if later than 15 minutes from scheduled start
                        key_on_minutes = key_on_dt.hour * 60 + key_on_dt.minute
                        scheduled_minutes = scheduled_start_dt.hour * 60 + scheduled_start_dt.minute
                        
                        if key_on_minutes > scheduled_minutes + 15:
                            # Late
                            driver_record['classification'] = 'Late'
                            driver_record['status_reason'] = f"{key_on_minutes - scheduled_minutes} minutes late"
                            
                            report['late_start_records'].append({
                                'driver_name': driver_name,
                                'asset_id': driver_record['asset_id'],
                                'scheduled_start': driver_record['scheduled_start'],
                                'actual_start': driver_record['key_on_time'],
                                'minutes_late': key_on_minutes - scheduled_minutes,
                                'job_site': driver_record['job_site']
                            })
                        else:
                            # On Time
                            driver_record['classification'] = 'On Time'
                            driver_record['status_reason'] = 'Within scheduled parameters'
                            report['on_time_drivers'] += 1
                    else:
                        # Could not parse time
                        driver_record['classification'] = 'Unknown'
                        driver_record['status_reason'] = 'Could not parse time'
                except Exception as e:
                    logger.error(f"Error classifying driver {driver_name}: {e}")
                    driver_record['classification'] = 'Unknown'
                    driver_record['status_reason'] = f'Error: {str(e)}'
            
            # Add to drivers list
            report['drivers'].append(driver_record)
        
        # Update summary metrics
        report['total_drivers'] = len(driver_data)
        if report['total_drivers'] > 0:
            report['on_time_percent'] = round(report['on_time_drivers'] / report['total_drivers'] * 100, 1)
        
        return report


# Standalone processor function
def process_date(date_str: str) -> Dict[str, Any]:
    """
    Process a specific date with MTD ingestion
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Dictionary with processing results
    """
    processor = MTDProcessor()
    return processor.process_date(date_str)