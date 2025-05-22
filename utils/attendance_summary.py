"""
TRAXORA | Attendance Summary Utilities

This module provides functions for classifying and summarizing driver attendance data.
"""
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# Configure logging
logger = logging.getLogger(__name__)

def classify_day(row):
    """
    Classify a driver's day based on TimeOnSite data
    
    Args:
        row (dict): Data row containing attendance information
        
    Returns:
        str: Classification as "On Time", "Late", "Early End", or "No Show"
    """
    try:
        time_on = row.get("TimeOnSite")
        if not time_on or time_on == "#Error":
            return "No Show"
        
        # Parse minutes from format like "120 Minutes"
        parts = time_on.split()
        if len(parts) >= 1:
            try:
                minutes = float(parts[0])
                if minutes < 15:
                    return "Early End"
                if minutes < 60:
                    return "Late"
                return "On Time"
            except ValueError:
                logger.warning(f"Could not parse TimeOnSite value: {time_on}")
                return "Unknown"
        return "Unknown"
    except Exception as e:
        logger.error(f"Error classifying day: {str(e)}")
        return "Unknown"

def summarize_week(data, start_date=None):
    """
    Summarize weekly attendance for all drivers
    
    Args:
        data (list): List of attendance data records
        start_date (datetime.date, optional): Start date to filter records
        
    Returns:
        list: List of driver attendance summaries
    """
    # Convert dates and organize by driver and date
    summary = defaultdict(lambda: defaultdict(list))
    all_dates = set()

    for row in data:
        try:
            # Get driver identifier (handle different field names)
            driver = row.get("Asset") or row.get("Driver") or row.get("DriverName") or "Unknown"
            
            # Parse date
            raw_date = row.get("Date")
            if not raw_date:
                continue
                
            # Try different date formats
            try:
                date = datetime.strptime(raw_date, "%m/%d/%Y").date()
            except ValueError:
                try:
                    date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                except ValueError:
                    logger.warning(f"Could not parse date: {raw_date}")
                    continue
            
            # Skip if before start date
            if start_date and date < start_date:
                continue

            # Classify the day
            classification = classify_day(row)
            
            # Add to summary
            summary[driver]["daily"].append({
                "date": str(date),
                "status": classification,
                "row": row
            })
            
            # Increment classification counter
            summary[driver][classification] = summary[driver].get(classification, 0) + 1
            
            # Track all dates
            all_dates.add(date)
        except Exception as e:
            logger.error(f"Error processing row: {str(e)}")
            continue

    # Create report
    report = []
    for driver, record in summary.items():
        total_days = len(record["daily"])
        
        # Skip drivers with no data
        if total_days == 0:
            continue
            
        report.append({
            "driver": driver,
            "total_days": total_days,
            "on_time": record.get("On Time", 0),
            "late": record.get("Late", 0),
            "early_end": record.get("Early End", 0),
            "no_show": record.get("No Show", 0),
            "unknown": record.get("Unknown", 0),
            "attendance_rate": round((record.get("On Time", 0) / total_days) * 100 if total_days > 0 else 0, 1),
            "daily_breakdown": record["daily"]
        })

    # Sort by driver name
    return sorted(report, key=lambda x: x["driver"])

def get_date_range(data, weeks=1):
    """
    Determine the date range for the report
    
    Args:
        data (list): List of attendance data records
        weeks (int): Number of weeks to include
        
    Returns:
        tuple: (start_date, end_date)
    """
    dates = []
    for row in data:
        raw_date = row.get("Date")
        if not raw_date:
            continue
            
        try:
            date = datetime.strptime(raw_date, "%m/%d/%Y").date()
            dates.append(date)
        except ValueError:
            try:
                date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                dates.append(date)
            except ValueError:
                continue
    
    if not dates:
        # Default to current week
        today = datetime.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        return start_date, end_date
    
    # Find max date and calculate start date
    max_date = max(dates)
    start_date = max_date - timedelta(days=7 * weeks - 1)
    
    return start_date, max_date