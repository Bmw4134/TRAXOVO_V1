"""
MTD (Month-to-Date) Data Processor

This module processes month-to-date data files to extract all dates
and generate reports for the actual date range in the uploaded files.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from utils.attendance_pipeline_v2 import process_attendance_data

logger = logging.getLogger(__name__)

def extract_date_range_from_files(upload_dir):
    """
    Extract the actual date range from uploaded MTD files
    
    Args:
        upload_dir: Directory containing uploaded files
        
    Returns:
        tuple: (start_date, end_date) as strings in YYYY-MM-DD format
    """
    all_dates = set()
    
    # Process all files in upload directory
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        
        if not os.path.isfile(file_path):
            continue
            
        try:
            # Load file based on extension
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                continue
                
            # Look for date columns
            date_columns = []
            for col in df.columns:
                col_lower = str(col).lower()
                if any(date_word in col_lower for date_word in ['date', 'time', 'day']):
                    date_columns.append(col)
            
            # Extract dates from each date column
            for date_col in date_columns:
                for _, row in df.iterrows():
                    try:
                        date_val = row[date_col]
                        if pd.notna(date_val):
                            # Try to parse as date
                            parsed_date = pd.to_datetime(date_val)
                            date_str = parsed_date.strftime('%Y-%m-%d')
                            all_dates.add(date_str)
                    except:
                        continue
                        
        except Exception as e:
            logger.warning(f"Error processing file {filename}: {e}")
            continue
    
    if not all_dates:
        return None, None
        
    # Return min and max dates
    sorted_dates = sorted(all_dates)
    return sorted_dates[0], sorted_dates[-1]

def process_mtd_data_for_date_range(upload_dir, start_date, end_date):
    """
    Process MTD data for a specific date range
    
    Args:
        upload_dir: Directory containing uploaded files
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        dict: Processing results for each date
    """
    results = {}
    
    # Load all files once
    driving_history_data = []
    activity_detail_data = []
    time_on_site_data = []
    
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        
        if not os.path.isfile(file_path):
            continue
            
        try:
            # Load file
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                continue
                
            # Convert to records
            records = df.to_dict('records')
            
            # Categorize by file type
            filename_lower = filename.lower()
            if 'driving' in filename_lower or 'history' in filename_lower:
                driving_history_data.extend(records)
            elif 'activity' in filename_lower or 'detail' in filename_lower:
                activity_detail_data.extend(records)
            elif 'time' in filename_lower or 'site' in filename_lower:
                time_on_site_data.extend(records)
                
        except Exception as e:
            logger.error(f"Error loading file {filename}: {e}")
            continue
    
    # Process each date in range
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    while current_date <= end_date_obj:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Filter data for this specific date
        date_driving_history = []
        date_activity_detail = []
        date_time_on_site = []
        
        # Filter driving history for this date
        for record in driving_history_data:
            record_date = extract_date_from_record(record)
            if record_date == date_str:
                date_driving_history.append(record)
        
        # Filter activity detail for this date
        for record in activity_detail_data:
            record_date = extract_date_from_record(record)
            if record_date == date_str:
                date_activity_detail.append(record)
                
        # Filter time on site for this date
        for record in time_on_site_data:
            record_date = extract_date_from_record(record)
            if record_date == date_str:
                date_time_on_site.append(record)
        
        # Process attendance for this date if we have data
        if date_driving_history or date_activity_detail or date_time_on_site:
            try:
                # Convert to DataFrames
                driving_df = pd.DataFrame(date_driving_history) if date_driving_history else None
                activity_df = pd.DataFrame(date_activity_detail) if date_activity_detail else None
                time_df = pd.DataFrame(date_time_on_site) if date_time_on_site else None
                
                # Process attendance
                attendance_result = process_attendance_data(date_str, driving_df, activity_df, time_df)
                results[date_str] = attendance_result
                
            except Exception as e:
                logger.error(f"Error processing attendance for {date_str}: {e}")
                results[date_str] = {'error': str(e)}
        
        current_date += timedelta(days=1)
    
    return results

def extract_date_from_record(record):
    """
    Extract date from a single record
    
    Args:
        record: Dictionary record from CSV/Excel
        
    Returns:
        str: Date in YYYY-MM-DD format or None
    """
    # Try common date field names
    date_fields = ['Date', 'date', 'EVENT_DATE', 'EventDate', 'ActivityDate', 'TimeOnSiteDate']
    
    for field in date_fields:
        if field in record and record[field]:
            try:
                parsed_date = pd.to_datetime(record[field])
                return parsed_date.strftime('%Y-%m-%d')
            except:
                continue
    
    return None

def generate_mtd_summary_report(results):
    """
    Generate a summary report from MTD processing results
    
    Args:
        results: Dictionary of processing results by date
        
    Returns:
        dict: Summary report
    """
    total_days = len(results)
    total_drivers = 0
    total_on_time = 0
    total_late = 0
    total_early_end = 0
    total_not_on_job = 0
    
    daily_summaries = []
    
    for date_str, result in results.items():
        if 'error' in result:
            continue
            
        summary = result.get('summary', {})
        
        daily_summary = {
            'date': date_str,
            'total_drivers': summary.get('total_drivers', 0),
            'on_time': summary.get('on_time', 0),
            'late': summary.get('late', 0),
            'early_end': summary.get('early_end', 0),
            'not_on_job': summary.get('not_on_job', 0)
        }
        
        daily_summaries.append(daily_summary)
        
        # Add to totals
        total_drivers += daily_summary['total_drivers']
        total_on_time += daily_summary['on_time']
        total_late += daily_summary['late']
        total_early_end += daily_summary['early_end']
        total_not_on_job += daily_summary['not_on_job']
    
    return {
        'period': {
            'start_date': min(results.keys()) if results else None,
            'end_date': max(results.keys()) if results else None,
            'total_days': total_days
        },
        'totals': {
            'total_drivers': total_drivers,
            'on_time': total_on_time,
            'late': total_late,
            'early_end': total_early_end,
            'not_on_job': total_not_on_job
        },
        'daily_summaries': daily_summaries,
        'processed_dates': list(results.keys())
    }