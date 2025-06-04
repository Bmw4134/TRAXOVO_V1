"""
Attendance Trends API

This module provides the API for accessing the multi-day attendance trend data
and integrates with the main attendance processor.
"""

import json
import logging
from datetime import datetime, timedelta

from trend_report import generate_trend_report
from utils.attendance_processor import process_attendance_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_driver_trends(start_date=None, end_date=None, days=5):
    """
    Get attendance trends for drivers across multiple days.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        days (int): Number of days to analyze if dates not provided
        
    Returns:
        dict: Driver trend data with flags
    """
    # Determine date range
    if not start_date or not end_date:
        # Default to last N days
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_dt = datetime.now() - timedelta(days=days-1)
        start_date = start_dt.strftime('%Y-%m-%d')
    
    dates = []
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Generate list of dates
    current_dt = start_dt
    while current_dt <= end_dt:
        dates.append(current_dt.strftime('%Y-%m-%d'))
        current_dt += timedelta(days=1)
    
    # Generate trend report
    report = generate_trend_report(dates=dates)
    
    # Format trends for API response
    driver_trends = {}
    for driver in report.get('drivers', []):
        driver_id = driver.get('name', '')  # In a real system, this would be the driver ID
        if driver_id:
            driver_trends[driver_id] = {
                'flags': driver.get('flags', []),
                'days_analyzed': driver.get('days_analyzed', 0),
                'late_count': driver.get('late_count', 0),
                'absence_count': driver.get('absence_count', 0), 
                'early_end_count': driver.get('early_end_count', 0)
            }
    
    # Add summary counts
    summary = {
        'total_drivers': report.get('summary', {}).get('total_drivers', 0),
        'chronic_late_count': report.get('summary', {}).get('chronic_late_count', 0),
        'repeated_absence_count': report.get('summary', {}).get('repeated_absence_count', 0),
        'unstable_shift_count': report.get('summary', {}).get('unstable_shift_count', 0),
        'date_range': {
            'start': start_date,
            'end': end_date
        },
        'days_analyzed': len(dates)
    }
    
    return {
        'driver_trends': driver_trends,
        'summary': summary
    }

def enrich_attendance_data_with_trends(attendance_data, days=5):
    """
    Enrich a single day's attendance data with trend information.
    
    Args:
        attendance_data (dict): Single day attendance data
        days (int): Number of days to include in trend analysis
        
    Returns:
        dict: Attendance data enriched with trend information
    """
    # Get the date from attendance data
    date = attendance_data.get('date')
    if not date:
        # Default to today
        date = datetime.now().strftime('%Y-%m-%d')
    
    # Calculate date range for trend analysis
    end_date = date
    start_dt = datetime.strptime(date, '%Y-%m-%d') - timedelta(days=days-1)
    start_date = start_dt.strftime('%Y-%m-%d')
    
    # Get trend data
    trend_data = get_driver_trends(start_date, end_date)
    
    # Add trend data to attendance data
    enriched_data = attendance_data.copy()
    enriched_data['driver_trends'] = trend_data.get('driver_trends', {})
    enriched_data['trend_summary'] = trend_data.get('summary', {})
    
    return enriched_data

def save_trend_report(output_path=None, days=5):
    """
    Generate and save a trend report for the specified number of days.
    
    Args:
        output_path (str): Path to save JSON report
        days (int): Number of days to include
        
    Returns:
        dict: Trend report data
    """
    if not output_path:
        today = datetime.now().strftime('%Y-%m-%d')
        output_path = f'trend_report_{today}.json'
    
    # Get trend data
    trend_data = get_driver_trends(days=days)
    
    # Save to file
    with open(output_path, 'w') as f:
        json.dump(trend_data, f, indent=2, default=str)
    
    logger.info(f"Trend report saved to {output_path}")
    return trend_data