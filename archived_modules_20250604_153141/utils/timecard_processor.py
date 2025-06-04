"""
TRAXORA Fleet Management - Timecard Processor

This module processes GroundWorks timecard data and compares it with GPS data
to identify discrepancies between reported work times and actual GPS records.
"""
import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_groundworks_timecards(file_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Process GroundWorks timecard data
    
    Args:
        file_path: Path to the timecard Excel file
        start_date: Start date string (YYYY-MM-DD) for filtering
        end_date: End date string (YYYY-MM-DD) for filtering
    
    Returns:
        dict: Processed timecard data
    """
    try:
        logger.info(f"Processing GroundWorks timecard file: {file_path}")
        
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Try to identify relevant columns
        employee_col = None
        date_col = None
        start_time_col = None
        end_time_col = None
        job_col = None
        
        # Look for common column names
        for col in df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['employee', 'name', 'worker']):
                employee_col = col
            elif any(term in col_lower for term in ['date', 'day']):
                date_col = col
            elif any(term in col_lower for term in ['start', 'in', 'clock in']):
                start_time_col = col
            elif any(term in col_lower for term in ['end', 'out', 'clock out']):
                end_time_col = col
            elif any(term in col_lower for term in ['job', 'site', 'location']):
                job_col = col
        
        # Check if we found all required columns
        if not (employee_col and date_col and start_time_col and end_time_col):
            logger.warning("Could not identify all required columns in timecard file")
            # Try to use default column names
            if not employee_col:
                employee_col = "Employee Name"
            if not date_col:
                date_col = "Date"
            if not start_time_col:
                start_time_col = "Clock In"
            if not end_time_col:
                end_time_col = "Clock Out"
            if not job_col:
                job_col = "Job Number"
        
        # Parse date filters
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Invalid start date format: {start_date}")
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Invalid end date format: {end_date}")
        
        # Process data
        result = {
            'timecards': [],
            'employees': {},
            'jobs': {},
            'dates': {},
            'metadata': {
                'file_path': file_path,
                'processed_at': datetime.now().isoformat(),
                'total_records': len(df)
            }
        }
        
        # Process each row
        for _, row in df.iterrows():
            try:
                # Extract data
                employee = str(row.get(employee_col, '')).strip()
                date_val = row.get(date_col, None)
                start_time = row.get(start_time_col, None)
                end_time = row.get(end_time_col, None)
                job = str(row.get(job_col, '')).strip() if job_col else None
                
                # Skip rows with missing data
                if not employee or pd.isna(employee) or employee.lower() == 'nan':
                    continue
                
                # Parse date
                date_obj = None
                if isinstance(date_val, datetime):
                    date_obj = date_val.date()
                elif isinstance(date_val, str):
                    try:
                        date_obj = datetime.strptime(date_val, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(date_val, '%m/%d/%Y').date()
                        except ValueError:
                            logger.warning(f"Could not parse date: {date_val}")
                
                if not date_obj:
                    continue
                
                # Apply date filters
                if start_date_obj and date_obj < start_date_obj:
                    continue
                if end_date_obj and date_obj > end_date_obj:
                    continue
                
                # Parse times
                start_time_str = None
                end_time_str = None
                
                if isinstance(start_time, datetime):
                    start_time_str = start_time.strftime('%H:%M')
                elif isinstance(start_time, str):
                    # Try to parse time string
                    try:
                        start_time_obj = datetime.strptime(start_time, '%H:%M')
                        start_time_str = start_time_obj.strftime('%H:%M')
                    except ValueError:
                        try:
                            start_time_obj = datetime.strptime(start_time, '%I:%M %p')
                            start_time_str = start_time_obj.strftime('%H:%M')
                        except ValueError:
                            logger.warning(f"Could not parse start time: {start_time}")
                
                if isinstance(end_time, datetime):
                    end_time_str = end_time.strftime('%H:%M')
                elif isinstance(end_time, str):
                    # Try to parse time string
                    try:
                        end_time_obj = datetime.strptime(end_time, '%H:%M')
                        end_time_str = end_time_obj.strftime('%H:%M')
                    except ValueError:
                        try:
                            end_time_obj = datetime.strptime(end_time, '%I:%M %p')
                            end_time_str = end_time_obj.strftime('%H:%M')
                        except ValueError:
                            logger.warning(f"Could not parse end time: {end_time}")
                
                # Create timecard record
                timecard = {
                    'employee': employee,
                    'date': date_obj.isoformat(),
                    'start_time': start_time_str,
                    'end_time': end_time_str,
                    'job': job
                }
                
                # Add to result
                result['timecards'].append(timecard)
                
                # Update employee stats
                employee_key = employee.lower()
                if employee_key not in result['employees']:
                    result['employees'][employee_key] = {
                        'name': employee,
                        'days': [],
                        'jobs': set()
                    }
                
                result['employees'][employee_key]['days'].append(date_obj.isoformat())
                if job:
                    result['employees'][employee_key]['jobs'].add(job)
                
                # Update job stats
                if job:
                    if job not in result['jobs']:
                        result['jobs'][job] = {
                            'employees': set(),
                            'days': []
                        }
                    
                    result['jobs'][job]['employees'].add(employee_key)
                    result['jobs'][job]['days'].append(date_obj.isoformat())
                
                # Update date stats
                date_key = date_obj.isoformat()
                if date_key not in result['dates']:
                    result['dates'][date_key] = {
                        'employees': set(),
                        'jobs': set()
                    }
                
                result['dates'][date_key]['employees'].add(employee_key)
                if job:
                    result['dates'][date_key]['jobs'].add(job)
                
            except Exception as e:
                logger.error(f"Error processing timecard row: {e}")
        
        # Convert sets to lists for JSON serialization
        for employee_key in result['employees']:
            result['employees'][employee_key]['jobs'] = list(result['employees'][employee_key]['jobs'])
        
        for job_key in result['jobs']:
            result['jobs'][job_key]['employees'] = list(result['jobs'][job_key]['employees'])
        
        for date_key in result['dates']:
            result['dates'][date_key]['employees'] = list(result['dates'][date_key]['employees'])
            result['dates'][date_key]['jobs'] = list(result['dates'][date_key]['jobs'])
        
        # Update metadata
        result['metadata']['processed_records'] = len(result['timecards'])
        result['metadata']['employee_count'] = len(result['employees'])
        result['metadata']['job_count'] = len(result['jobs'])
        result['metadata']['date_count'] = len(result['dates'])
        
        logger.info(f"Successfully processed {len(result['timecards'])} timecard records")
        return result
        
    except Exception as e:
        logger.error(f"Error processing timecard file: {e}")
        return {
            'error': str(e),
            'timecards': [],
            'employees': {},
            'jobs': {},
            'dates': {},
            'metadata': {
                'file_path': file_path,
                'processed_at': datetime.now().isoformat(),
                'error': str(e)
            }
        }

def compare_timecards_with_gps(timecard_file: str, gps_data: Dict[str, Any], target_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Compare timecard data with GPS data to identify discrepancies
    
    Args:
        timecard_file: Path to timecard file
        gps_data: GPS data from driver reports
        target_date: Specific date to compare (YYYY-MM-DD)
    
    Returns:
        list: Comparison results
    """
    try:
        logger.info(f"Comparing timecards with GPS data")
        
        # Process timecard data
        timecard_data = process_groundworks_timecards(timecard_file, target_date, target_date)
        
        # Initialize results
        comparisons = []
        
        # For each employee in timecards
        for employee_key, employee_data in timecard_data['employees'].items():
            employee_name = employee_data['name']
            
            # Find matching driver in GPS data
            gps_driver_data = None
            normalized_key = employee_key.lower().replace(' ', '')
            
            # Try to find match in GPS data
            for driver_key, driver_data in gps_data.items():
                if normalized_key in driver_key.lower().replace(' ', ''):
                    gps_driver_data = driver_data
                    break
            
            if not gps_driver_data:
                # Try a more flexible match
                for driver_key, driver_data in gps_data.items():
                    driver_name = driver_data.get('driver_data', {}).get('name', '')
                    if employee_name.lower() in driver_name.lower() or driver_name.lower() in employee_name.lower():
                        gps_driver_data = driver_data
                        break
            
            if not gps_driver_data:
                continue
            
            # Now compare for each day
            for date_str in employee_data['days']:
                # Find timecard for this date
                timecard = None
                for tc in timecard_data['timecards']:
                    if tc['employee'].lower() == employee_name.lower() and tc['date'] == date_str:
                        timecard = tc
                        break
                
                if not timecard:
                    continue
                
                # Get GPS times for this date
                gps_start = None
                gps_end = None
                
                classification = gps_driver_data.get('classification', {})
                
                if classification.get('first_seen'):
                    gps_start = classification.get('first_seen')
                
                if classification.get('last_seen'):
                    gps_end = classification.get('last_seen')
                
                # Skip if no GPS data
                if not gps_start or not gps_end:
                    continue
                
                # Parse timecard times
                timecard_start = None
                timecard_end = None
                
                if timecard.get('start_time'):
                    try:
                        timecard_start = timecard['start_time']
                    except ValueError:
                        logger.warning(f"Could not parse timecard start time: {timecard['start_time']}")
                
                if timecard.get('end_time'):
                    try:
                        timecard_end = timecard['end_time']
                    except ValueError:
                        logger.warning(f"Could not parse timecard end time: {timecard['end_time']}")
                
                # Skip if no timecard data
                if not timecard_start or not timecard_end:
                    continue
                
                # Calculate differences
                start_diff_minutes = calculate_time_diff(timecard_start, gps_start)
                end_diff_minutes = calculate_time_diff(gps_end, timecard_end)
                total_variance = abs(start_diff_minutes) + abs(end_diff_minutes)
                
                # Add to comparisons
                comparison = {
                    'driver_name': employee_name,
                    'date': date_str,
                    'timecard_start': timecard_start,
                    'gps_start': gps_start,
                    'start_diff': start_diff_minutes,
                    'timecard_end': timecard_end,
                    'gps_end': gps_end,
                    'end_diff': end_diff_minutes,
                    'total_variance': total_variance,
                    'job': timecard.get('job', ''),
                    'flags': []
                }
                
                # Add flags for significant discrepancies
                if abs(start_diff_minutes) > 15:
                    if start_diff_minutes > 0:
                        comparison['flags'].append('TIMECARD_START_EARLIER')
                    else:
                        comparison['flags'].append('TIMECARD_START_LATER')
                
                if abs(end_diff_minutes) > 15:
                    if end_diff_minutes > 0:
                        comparison['flags'].append('TIMECARD_END_EARLIER')
                    else:
                        comparison['flags'].append('TIMECARD_END_LATER')
                
                if total_variance > 30:
                    comparison['flags'].append('SIGNIFICANT_VARIANCE')
                
                comparisons.append(comparison)
        
        # Sort by total variance descending
        comparisons.sort(key=lambda x: x['total_variance'], reverse=True)
        
        logger.info(f"Generated {len(comparisons)} timecard comparisons")
        return comparisons
        
    except Exception as e:
        logger.error(f"Error comparing timecards with GPS data: {e}")
        return []

def calculate_time_diff(time1_str: str, time2_str: str) -> int:
    """
    Calculate difference between two times in minutes
    
    Args:
        time1_str: First time string (HH:MM)
        time2_str: Second time string (HH:MM)
    
    Returns:
        int: Difference in minutes (time1 - time2)
    """
    try:
        # Parse times
        time1 = datetime.strptime(time1_str, '%H:%M')
        time2 = datetime.strptime(time2_str, '%H:%M')
        
        # Calculate difference in minutes
        diff = (time1.hour * 60 + time1.minute) - (time2.hour * 60 + time2.minute)
        
        return diff
        
    except Exception as e:
        logger.error(f"Error calculating time difference: {e}")
        return 0