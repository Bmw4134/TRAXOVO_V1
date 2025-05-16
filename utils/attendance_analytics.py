"""
Attendance Analytics Module

This module handles historical data tracking and trend analysis for attendance reports.
It provides functions to:
1. Store attendance report results in the database
2. Calculate week-over-week and month-over-month trends
3. Generate charts and visualizations for attendance metrics
4. Identify pattern anomalies and top drivers with issues
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sqlalchemy import func, desc
from app import db
from models import AttendanceRecord, Driver, Asset, JobSite

# Initialize logger
logger = logging.getLogger(__name__)

def save_attendance_record(report_date, driver_id, asset_id, job_site_id, status_type, 
                          expected_start=None, actual_start=None, expected_end=None, 
                          actual_end=None, minutes_late=None, minutes_early=None, 
                          expected_job_id=None, actual_job_id=None):
    """
    Save attendance record to database for historical tracking
    
    Args:
        report_date (datetime): Date of the report
        driver_id (int): Driver ID
        asset_id (int): Asset ID
        job_site_id (int): Job site ID
        status_type (str): Status type (LATE_START, EARLY_END, NOT_ON_JOB)
        expected_start (datetime, optional): Expected start time
        actual_start (datetime, optional): Actual start time
        expected_end (datetime, optional): Expected end time
        actual_end (datetime, optional): Actual end time
        minutes_late (int, optional): Minutes late
        minutes_early (int, optional): Minutes early
        expected_job_id (int, optional): Expected job site ID
        actual_job_id (int, optional): Actual job site ID
        
    Returns:
        AttendanceRecord: Saved attendance record
    """
    try:
        record = AttendanceRecord(
            report_date=report_date,
            driver_id=driver_id,
            asset_id=asset_id,
            job_site_id=job_site_id,
            status_type=status_type,
            expected_start=expected_start,
            actual_start=actual_start,
            expected_end=expected_end,
            actual_end=actual_end,
            minutes_late=minutes_late,
            minutes_early=minutes_early,
            expected_job_id=expected_job_id,
            actual_job_id=actual_job_id
        )
        
        db.session.add(record)
        db.session.commit()
        logger.info(f"Saved attendance record for driver {driver_id} on {report_date}")
        return record
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving attendance record: {e}")
        return None

def get_attendance_trends(start_date, end_date, status_type=None, driver_id=None, job_site_id=None):
    """
    Get attendance trends for a date range
    
    Args:
        start_date (datetime): Start date
        end_date (datetime): End date
        status_type (str, optional): Filter by status type
        driver_id (int, optional): Filter by driver ID
        job_site_id (int, optional): Filter by job site ID
        
    Returns:
        dict: Dictionary with trend data
    """
    try:
        query = db.session.query(
            func.date(AttendanceRecord.report_date).label('date'),
            func.count(AttendanceRecord.id).label('count')
        ).filter(
            AttendanceRecord.report_date.between(start_date, end_date)
        ).group_by(
            func.date(AttendanceRecord.report_date)
        )
        
        if status_type:
            query = query.filter(AttendanceRecord.status_type == status_type)
        
        if driver_id:
            query = query.filter(AttendanceRecord.driver_id == driver_id)
            
        if job_site_id:
            query = query.filter(AttendanceRecord.job_site_id == job_site_id)
            
        results = query.all()
        
        dates = [r.date for r in results]
        counts = [r.count for r in results]
        
        return {
            'dates': dates,
            'counts': counts,
            'total': sum(counts),
            'average': round(sum(counts) / len(counts), 2) if counts else 0
        }
    except Exception as e:
        logger.error(f"Error getting attendance trends: {e}")
        return {
            'dates': [],
            'counts': [],
            'total': 0,
            'average': 0
        }

def get_top_late_drivers(start_date, end_date, limit=10):
    """
    Get top drivers with late starts
    
    Args:
        start_date (datetime): Start date
        end_date (datetime): End date
        limit (int, optional): Limit number of results
        
    Returns:
        list: List of drivers with late start counts
    """
    try:
        results = db.session.query(
            AttendanceRecord.driver_id,
            func.count(AttendanceRecord.id).label('late_count')
        ).filter(
            AttendanceRecord.report_date.between(start_date, end_date),
            AttendanceRecord.status_type == 'LATE_START'
        ).group_by(
            AttendanceRecord.driver_id
        ).order_by(
            desc('late_count')
        ).limit(limit).all()
        
        # Get driver details
        driver_data = []
        for r in results:
            driver = Driver.query.get(r.driver_id)
            if driver:
                driver_data.append({
                    'driver_id': r.driver_id,
                    'name': driver.name,
                    'late_count': r.late_count
                })
        
        return driver_data
    except Exception as e:
        logger.error(f"Error getting top late drivers: {e}")
        return []

def generate_weekly_comparison_chart(status_type, weeks=4):
    """
    Generate a weekly comparison chart for a specific status type
    
    Args:
        status_type (str): Status type (LATE_START, EARLY_END, NOT_ON_JOB)
        weeks (int): Number of weeks to compare
        
    Returns:
        str: Path to saved chart image
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=weeks*7)
        
        # Get data for each week
        weekly_data = []
        for i in range(weeks):
            week_end = end_date - timedelta(days=i*7)
            week_start = week_end - timedelta(days=7)
            
            trends = get_attendance_trends(
                week_start, 
                week_end,
                status_type=status_type
            )
            
            weekly_data.append({
                'week': f"Week {weeks-i}",
                'start_date': week_start.strftime('%Y-%m-%d'),
                'end_date': week_end.strftime('%Y-%m-%d'),
                'count': trends['total']
            })
        
        # Create DataFrame
        df = pd.DataFrame(weekly_data)
        
        # Generate chart
        plt.figure(figsize=(10, 6))
        bars = plt.bar(df['week'], df['count'], color='skyblue')
        plt.title(f"{status_type} - Weekly Comparison")
        plt.xlabel('Week')
        plt.ylabel('Count')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f"{height}", ha='center', va='bottom')
        
        # Save chart
        charts_dir = os.path.join('static', 'charts')
        os.makedirs(charts_dir, exist_ok=True)
        
        chart_path = os.path.join(charts_dir, f"weekly_{status_type.lower()}.png")
        plt.savefig(chart_path)
        plt.close()
        
        return chart_path
    except Exception as e:
        logger.error(f"Error generating weekly comparison chart: {e}")
        return None

def calculate_trend_percentage(current_count, previous_count):
    """
    Calculate trend percentage change
    
    Args:
        current_count (int): Current count
        previous_count (int): Previous count
        
    Returns:
        float: Percentage change
    """
    if previous_count == 0:
        return 100 if current_count > 0 else 0
    
    return round(((current_count - previous_count) / previous_count) * 100, 1)

def get_trend_summary():
    """
    Get summary of attendance trends
    
    Returns:
        dict: Dictionary with trend summary
    """
    try:
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        
        # Get counts for different periods
        yesterday_data = {
            'late_start': get_attendance_trends(yesterday, yesterday, status_type='LATE_START')['total'],
            'early_end': get_attendance_trends(yesterday, yesterday, status_type='EARLY_END')['total'],
            'not_on_job': get_attendance_trends(yesterday, yesterday, status_type='NOT_ON_JOB')['total']
        }
        
        last_week_data = {
            'late_start': get_attendance_trends(last_week, yesterday, status_type='LATE_START')['total'],
            'early_end': get_attendance_trends(last_week, yesterday, status_type='EARLY_END')['total'],
            'not_on_job': get_attendance_trends(last_week, yesterday, status_type='NOT_ON_JOB')['total']
        }
        
        last_month_data = {
            'late_start': get_attendance_trends(last_month, yesterday, status_type='LATE_START')['total'],
            'early_end': get_attendance_trends(last_month, yesterday, status_type='EARLY_END')['total'],
            'not_on_job': get_attendance_trends(last_month, yesterday, status_type='NOT_ON_JOB')['total']
        }
        
        # Get previous periods for comparison
        previous_week = last_week - timedelta(days=7)
        previous_week_data = {
            'late_start': get_attendance_trends(previous_week, last_week, status_type='LATE_START')['total'],
            'early_end': get_attendance_trends(previous_week, last_week, status_type='EARLY_END')['total'],
            'not_on_job': get_attendance_trends(previous_week, last_week, status_type='NOT_ON_JOB')['total']
        }
        
        previous_month = last_month - timedelta(days=30)
        previous_month_data = {
            'late_start': get_attendance_trends(previous_month, last_month, status_type='LATE_START')['total'],
            'early_end': get_attendance_trends(previous_month, last_month, status_type='EARLY_END')['total'],
            'not_on_job': get_attendance_trends(previous_month, last_month, status_type='NOT_ON_JOB')['total']
        }
        
        # Calculate week-over-week and month-over-month trends
        wow_trends = {
            'late_start': calculate_trend_percentage(last_week_data['late_start'], previous_week_data['late_start']),
            'early_end': calculate_trend_percentage(last_week_data['early_end'], previous_week_data['early_end']),
            'not_on_job': calculate_trend_percentage(last_week_data['not_on_job'], previous_week_data['not_on_job'])
        }
        
        mom_trends = {
            'late_start': calculate_trend_percentage(last_month_data['late_start'], previous_month_data['late_start']),
            'early_end': calculate_trend_percentage(last_month_data['early_end'], previous_month_data['early_end']),
            'not_on_job': calculate_trend_percentage(last_month_data['not_on_job'], previous_month_data['not_on_job'])
        }
        
        return {
            'yesterday': yesterday_data,
            'last_week': last_week_data,
            'last_month': last_month_data,
            'wow_trends': wow_trends,
            'mom_trends': mom_trends
        }
    except Exception as e:
        logger.error(f"Error getting trend summary: {e}")
        return {
            'yesterday': {'late_start': 0, 'early_end': 0, 'not_on_job': 0},
            'last_week': {'late_start': 0, 'early_end': 0, 'not_on_job': 0},
            'last_month': {'late_start': 0, 'early_end': 0, 'not_on_job': 0},
            'wow_trends': {'late_start': 0, 'early_end': 0, 'not_on_job': 0},
            'mom_trends': {'late_start': 0, 'early_end': 0, 'not_on_job': 0}
        }