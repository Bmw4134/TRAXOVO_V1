"""
Process Interval Reports Module

This module provides functions to process MTD files for multiple date ranges
and generate interval-based reports (daily, weekly, monthly).
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from process_mtd_files import process_mtd_files

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_interval_report(driving_history_paths, activity_detail_paths, start_date, end_date, interval_type='weekly'):
    """
    Process MTD files for a date range and generate interval-based reports.
    
    Args:
        driving_history_paths (list): List of paths to driving history CSV files
        activity_detail_paths (list): List of paths to activity detail CSV files
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        interval_type (str): Type of interval ('daily', 'weekly', or 'monthly')
        
    Returns:
        dict: Report data for the interval
    """
    logger.info(f"Processing interval report from {start_date} to {end_date} (type: {interval_type})")
    
    # Convert to datetime objects
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate date intervals based on interval type
    date_intervals = []
    
    if interval_type == 'daily':
        # One report per day
        current_date = start_dt
        while current_date <= end_dt:
            date_intervals.append({
                'label': current_date.strftime('%A, %B %d, %Y'),
                'start': current_date.strftime('%Y-%m-%d'),
                'end': current_date.strftime('%Y-%m-%d')
            })
            current_date += timedelta(days=1)
        
    elif interval_type == 'weekly':
        # One report per week
        current_date = start_dt
        while current_date <= end_dt:
            week_end = min(current_date + timedelta(days=6), end_dt)
            date_intervals.append({
                'label': f"{current_date.strftime('%b %d')} to {week_end.strftime('%b %d, %Y')}",
                'start': current_date.strftime('%Y-%m-%d'),
                'end': week_end.strftime('%Y-%m-%d')
            })
            current_date += timedelta(days=7)
        
    elif interval_type == 'monthly':
        # One report per month
        current_date = start_dt.replace(day=1)  # Start at first day of month
        while current_date <= end_dt:
            # Get last day of current month
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1)
            else:
                next_month = current_date.replace(month=current_date.month + 1)
            
            month_end = (next_month - timedelta(days=1))
            month_end = min(month_end, end_dt)
            
            date_intervals.append({
                'label': current_date.strftime('%B %Y'),
                'start': current_date.strftime('%Y-%m-%d'),
                'end': month_end.strftime('%Y-%m-%d')
            })
            
            current_date = next_month
    
    # Generate and process reports for intervals
    reports = []
    
    # Process up to 3 sample intervals if more than 3 (to prevent timeouts)
    if len(date_intervals) > 3:
        # Sample the first, middle, and last interval
        sample_indexes = [0, len(date_intervals) // 2, len(date_intervals) - 1]
        sample_intervals = [date_intervals[i] for i in sample_indexes]
        logger.info(f"Sampling {len(sample_intervals)} intervals from {len(date_intervals)} total")
    else:
        sample_intervals = date_intervals
    
    # Process each interval
    for interval in sample_intervals:
        interval_start = interval['start']
        interval_end = interval['end']
        
        # For daily intervals, just process the single date
        if interval_start == interval_end:
            try:
                day_report = process_mtd_files(
                    driving_history_paths=driving_history_paths,
                    activity_detail_paths=activity_detail_paths,
                    report_date=interval_start
                )
                
                reports.append({
                    'id': interval_start,
                    'label': interval['label'],
                    'start_date': interval_start,
                    'end_date': interval_end,
                    'type': 'daily',
                    'total_drivers': day_report.get('total_drivers', 0),
                    'on_time_count': day_report.get('on_time_count', 0),
                    'late_count': day_report.get('late_count', 0),
                    'early_end_count': day_report.get('early_end_count', 0),
                    'not_on_job_count': day_report.get('not_on_job_count', 0)
                })
            except Exception as e:
                logger.error(f"Error processing daily report for {interval_start}: {str(e)}")
        
        # For weekly/monthly intervals, sample days within the interval
        else:
            # Create interval report structure
            interval_id = f"{interval_start}_to_{interval_end}"
            interval_report = {
                'id': interval_id,
                'label': interval['label'],
                'start_date': interval_start,
                'end_date': interval_end,
                'interval_type': interval_type,
                'days': []
            }
            
            # Calculate sample days for the interval (max 3 days per interval)
            start_dt = datetime.strptime(interval_start, '%Y-%m-%d')
            end_dt = datetime.strptime(interval_end, '%Y-%m-%d')
            total_days = (end_dt - start_dt).days + 1
            
            sample_days = []
            if total_days > 3:
                # Sample start, middle, and end dates
                sample_days.append(start_dt)
                if total_days > 2:
                    sample_days.append(start_dt + timedelta(days=total_days // 2))
                if total_days > 1:
                    sample_days.append(end_dt)
            else:
                # Process all days if 3 or fewer
                current_dt = start_dt
                while current_dt <= end_dt:
                    sample_days.append(current_dt)
                    current_dt += timedelta(days=1)
            
            # Process each sample day
            for sample_day in sample_days:
                day_str = sample_day.strftime('%Y-%m-%d')
                
                try:
                    # Process individual day
                    day_report = process_mtd_files(
                        driving_history_paths=driving_history_paths,
                        activity_detail_paths=activity_detail_paths,
                        report_date=day_str
                    )
                    
                    # Add day to interval report
                    interval_report['days'].append({
                        'date': day_str,
                        'label': sample_day.strftime('%A, %B %d'),
                        'total_drivers': day_report.get('total_drivers', 0),
                        'on_time_count': day_report.get('on_time_count', 0),
                        'late_count': day_report.get('late_count', 0),
                        'early_end_count': day_report.get('early_end_count', 0),
                        'not_on_job_count': day_report.get('not_on_job_count', 0)
                    })
                except Exception as e:
                    logger.error(f"Error processing date {day_str}: {str(e)}")
            
            # Calculate interval summary
            total_drivers = sum(day.get('total_drivers', 0) for day in interval_report['days']) 
            on_time_count = sum(day.get('on_time_count', 0) for day in interval_report['days'])
            late_count = sum(day.get('late_count', 0) for day in interval_report['days'])
            early_end_count = sum(day.get('early_end_count', 0) for day in interval_report['days'])
            not_on_job_count = sum(day.get('not_on_job_count', 0) for day in interval_report['days'])
            
            if total_drivers > 0:
                on_time_percent = round(on_time_count / total_drivers * 100)
                late_percent = round(late_count / total_drivers * 100)
                early_end_percent = round(early_end_count / total_drivers * 100)
                not_on_job_percent = round(not_on_job_count / total_drivers * 100)
            else:
                on_time_percent = late_percent = early_end_percent = not_on_job_percent = 0
            
            interval_report['summary'] = {
                'total_drivers': total_drivers,
                'on_time_count': on_time_count,
                'late_count': late_count,
                'early_end_count': early_end_count,
                'not_on_job_count': not_on_job_count,
                'on_time_percent': on_time_percent,
                'late_percent': late_percent,
                'early_end_percent': early_end_percent,
                'not_on_job_percent': not_on_job_percent
            }
            
            # Save the full interval report to a file
            reports.append({
                'id': interval_id,
                'label': interval['label'],
                'start_date': interval_start,
                'end_date': interval_end,
                'type': interval_type,
                'total_drivers': total_drivers,
                'on_time_count': on_time_count,
                'late_count': late_count,
                'early_end_count': early_end_count,
                'not_on_job_count': not_on_job_count
            })
    
    # Return summary of all intervals
    return {
        'interval_type': interval_type,
        'start_date': start_date,
        'end_date': end_date,
        'reports': reports
    }