"""
Attendance Analytics Module

This module provides functions for analyzing attendance data
and generating trend reports for historical pattern identification.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from models import Asset
from models.attendance import Driver, JobSite, AttendanceRecord, AttendanceTrend

# Initialize logger
logger = logging.getLogger(__name__)

def get_or_create_driver(name, employee_id, asset_id=None, department=None):
    """
    Get an existing driver or create a new one
    
    Args:
        name (str): Driver name
        employee_id (str): Unique employee ID
        asset_id (int, optional): Asset ID associated with the driver
        department (str, optional): Department/region the driver belongs to
        
    Returns:
        Driver: Driver object
    """
    try:
        # Try to find existing driver
        driver = Driver.query.filter_by(employee_id=employee_id).first()
        
        if driver:
            # Update existing driver if needed
            updated = False
            if asset_id and driver.asset_id != asset_id:
                driver.asset_id = asset_id
                updated = True
            if department and driver.department != department:
                driver.department = department
                updated = True
            
            if updated:
                driver.updated_at = datetime.utcnow()
                db.session.commit()
            
            return driver
        else:
            # Create new driver
            new_driver = Driver(
                name=name,
                employee_id=employee_id,
                asset_id=asset_id,
                department=department,
                active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(new_driver)
            db.session.commit()
            return new_driver
    
    except Exception as e:
        logger.error(f"Error getting or creating driver: {e}")
        db.session.rollback()
        return None

def get_or_create_job_site(name, job_number, address=None, city=None, state=None, latitude=None, longitude=None):
    """
    Get an existing job site or create a new one
    
    Args:
        name (str): Job site name
        job_number (str): Unique job number
        address (str, optional): Job site address
        city (str, optional): Job site city
        state (str, optional): Job site state
        latitude (float, optional): Job site latitude
        longitude (float, optional): Job site longitude
        
    Returns:
        JobSite: JobSite object
    """
    try:
        # Try to find existing job site
        job_site = JobSite.query.filter_by(job_number=job_number).first()
        
        if job_site:
            # Update existing job site if needed
            updated = False
            if name and job_site.name != name:
                job_site.name = name
                updated = True
                
            if updated:
                job_site.updated_at = datetime.utcnow()
                db.session.commit()
            
            return job_site
        else:
            # Create new job site
            new_job_site = JobSite(
                name=name,
                job_number=job_number,
                address=address,
                city=city,
                state=state,
                latitude=latitude,
                longitude=longitude,
                active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(new_job_site)
            db.session.commit()
            return new_job_site
    
    except Exception as e:
        logger.error(f"Error getting or creating job site: {e}")
        db.session.rollback()
        return None

def save_attendance_record(report_date, driver_id, job_site_id, status_type, 
                          asset_id=None, expected_start=None, actual_start=None, 
                          expected_end=None, actual_end=None, minutes_late=None, 
                          minutes_early=None, expected_job_id=None, actual_job_id=None, 
                          notes=None):
    """
    Save an attendance record
    
    Args:
        report_date (date): Date of the attendance record
        driver_id (int): Driver ID
        job_site_id (int): Job site ID
        status_type (str): Status type ('LATE_START', 'EARLY_END', 'NOT_ON_JOB')
        asset_id (int, optional): Asset ID
        expected_start (datetime, optional): Expected start time
        actual_start (datetime, optional): Actual start time
        expected_end (datetime, optional): Expected end time
        actual_end (datetime, optional): Actual end time
        minutes_late (int, optional): Minutes late
        minutes_early (int, optional): Minutes early
        expected_job_id (int, optional): Expected job site ID
        actual_job_id (int, optional): Actual job site ID
        notes (str, optional): Notes
        
    Returns:
        AttendanceRecord: AttendanceRecord object
    """
    try:
        # Check if record already exists for this driver, date, and status type
        existing_record = AttendanceRecord.query.filter_by(
            report_date=report_date,
            driver_id=driver_id,
            status_type=status_type
        ).first()
        
        if existing_record:
            # Update existing record if needed
            updated = False
            
            if job_site_id and existing_record.job_site_id != job_site_id:
                existing_record.job_site_id = job_site_id
                updated = True
                
            if asset_id and existing_record.asset_id != asset_id:
                existing_record.asset_id = asset_id
                updated = True
                
            if expected_start and existing_record.expected_start != expected_start:
                existing_record.expected_start = expected_start
                updated = True
                
            if actual_start and existing_record.actual_start != actual_start:
                existing_record.actual_start = actual_start
                updated = True
                
            if expected_end and existing_record.expected_end != expected_end:
                existing_record.expected_end = expected_end
                updated = True
                
            if actual_end and existing_record.actual_end != actual_end:
                existing_record.actual_end = actual_end
                updated = True
                
            if minutes_late is not None and existing_record.minutes_late != minutes_late:
                existing_record.minutes_late = minutes_late
                updated = True
                
            if minutes_early is not None and existing_record.minutes_early != minutes_early:
                existing_record.minutes_early = minutes_early
                updated = True
                
            if expected_job_id and existing_record.expected_job_id != expected_job_id:
                existing_record.expected_job_id = expected_job_id
                updated = True
                
            if actual_job_id and existing_record.actual_job_id != actual_job_id:
                existing_record.actual_job_id = actual_job_id
                updated = True
                
            if notes and existing_record.notes != notes:
                existing_record.notes = notes
                updated = True
                
            if updated:
                existing_record.updated_at = datetime.utcnow()
                db.session.commit()
                
            return existing_record
        else:
            # Create new record
            new_record = AttendanceRecord(
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
                actual_job_id=actual_job_id,
                notes=notes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(new_record)
            db.session.commit()
            return new_record
    
    except Exception as e:
        logger.error(f"Error saving attendance record: {e}")
        db.session.rollback()
        return None

def get_attendance_records(start_date=None, end_date=None, driver_id=None, 
                          job_site_id=None, status_type=None, department=None):
    """
    Get attendance records based on filters
    
    Args:
        start_date (date, optional): Start date for filter
        end_date (date, optional): End date for filter
        driver_id (int, optional): Filter by driver ID
        job_site_id (int, optional): Filter by job site ID
        status_type (str, optional): Filter by status type
        department (str, optional): Filter by department
        
    Returns:
        list: List of AttendanceRecord objects
    """
    try:
        # Start with base query
        query = AttendanceRecord.query
        
        # Apply filters
        if start_date:
            query = query.filter(AttendanceRecord.report_date >= start_date)
        
        if end_date:
            query = query.filter(AttendanceRecord.report_date <= end_date)
        
        if driver_id:
            query = query.filter(AttendanceRecord.driver_id == driver_id)
        
        if job_site_id:
            query = query.filter(AttendanceRecord.job_site_id == job_site_id)
        
        if status_type:
            query = query.filter(AttendanceRecord.status_type == status_type)
        
        if department:
            query = query.join(Driver).filter(Driver.department == department)
        
        # Order by date (newest first)
        query = query.order_by(AttendanceRecord.report_date.desc())
        
        return query.all()
    
    except Exception as e:
        logger.error(f"Error getting attendance records: {e}")
        return []

def get_driver_stats(driver_id, start_date=None, end_date=None):
    """
    Get attendance statistics for a specific driver
    
    Args:
        driver_id (int): Driver ID
        start_date (date, optional): Start date for filter
        end_date (date, optional): End date for filter
        
    Returns:
        dict: Statistics for the driver
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().date()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get driver details
        driver = Driver.query.get(driver_id)
        if not driver:
            return None
        
        # Get attendance records for the driver
        records = get_attendance_records(
            start_date=start_date,
            end_date=end_date,
            driver_id=driver_id
        )
        
        # Count incidents by type
        late_starts = sum(1 for r in records if r.status_type == 'LATE_START')
        early_ends = sum(1 for r in records if r.status_type == 'EARLY_END')
        not_on_job = sum(1 for r in records if r.status_type == 'NOT_ON_JOB')
        total_incidents = late_starts + early_ends + not_on_job
        
        # Get average times
        late_minutes = [r.minutes_late for r in records if r.status_type == 'LATE_START' and r.minutes_late is not None]
        avg_late_minutes = sum(late_minutes) / len(late_minutes) if late_minutes else 0
        
        early_minutes = [r.minutes_early for r in records if r.status_type == 'EARLY_END' and r.minutes_early is not None]
        avg_early_minutes = sum(early_minutes) / len(early_minutes) if early_minutes else 0
        
        # Get job sites with issues
        problem_sites = {}
        for record in records:
            site_name = record.job_site.name if record.job_site else 'Unknown'
            if site_name not in problem_sites:
                problem_sites[site_name] = 0
            problem_sites[site_name] += 1
        
        # Sort job sites by incident count
        problem_sites = dict(sorted(problem_sites.items(), key=lambda x: x[1], reverse=True))
        
        # Calculate recent trend
        recent_date = end_date - timedelta(days=7)
        recent_records = [r for r in records if r.report_date >= recent_date]
        recent_incidents = len(recent_records)
        
        return {
            'driver': {
                'id': driver.id,
                'name': driver.name,
                'employee_id': driver.employee_id,
                'department': driver.department
            },
            'stats': {
                'total_incidents': total_incidents,
                'late_starts': late_starts,
                'early_ends': early_ends,
                'not_on_job': not_on_job,
                'avg_late_minutes': avg_late_minutes,
                'avg_early_minutes': avg_early_minutes,
                'recent_incidents': recent_incidents,
                'problem_sites': problem_sites,
                'start_date': start_date,
                'end_date': end_date
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting driver stats: {e}")
        return None

def get_job_site_stats(job_site_id, start_date=None, end_date=None):
    """
    Get attendance statistics for a specific job site
    
    Args:
        job_site_id (int): Job site ID
        start_date (date, optional): Start date for filter
        end_date (date, optional): End date for filter
        
    Returns:
        dict: Statistics for the job site
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().date()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get job site details
        job_site = JobSite.query.get(job_site_id)
        if not job_site:
            return None
        
        # Get attendance records for the job site
        records = get_attendance_records(
            start_date=start_date,
            end_date=end_date,
            job_site_id=job_site_id
        )
        
        # Count incidents by type
        late_starts = sum(1 for r in records if r.status_type == 'LATE_START')
        early_ends = sum(1 for r in records if r.status_type == 'EARLY_END')
        not_on_job = sum(1 for r in records if r.status_type == 'NOT_ON_JOB')
        total_incidents = late_starts + early_ends + not_on_job
        
        # Get problem drivers
        problem_drivers = {}
        for record in records:
            driver_name = record.driver.name if record.driver else 'Unknown'
            if driver_name not in problem_drivers:
                problem_drivers[driver_name] = 0
            problem_drivers[driver_name] += 1
        
        # Sort drivers by incident count
        problem_drivers = dict(sorted(problem_drivers.items(), key=lambda x: x[1], reverse=True))
        
        # Calculate recent trend
        recent_date = end_date - timedelta(days=7)
        recent_records = [r for r in records if r.report_date >= recent_date]
        recent_incidents = len(recent_records)
        
        return {
            'job_site': {
                'id': job_site.id,
                'name': job_site.name,
                'job_number': job_site.job_number,
                'address': job_site.address,
                'city': job_site.city,
                'state': job_site.state
            },
            'stats': {
                'total_incidents': total_incidents,
                'late_starts': late_starts,
                'early_ends': early_ends,
                'not_on_job': not_on_job,
                'recent_incidents': recent_incidents,
                'problem_drivers': problem_drivers,
                'start_date': start_date,
                'end_date': end_date
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting job site stats: {e}")
        return None

def get_department_stats(department, start_date=None, end_date=None):
    """
    Get attendance statistics for a specific department
    
    Args:
        department (str): Department name
        start_date (date, optional): Start date for filter
        end_date (date, optional): End date for filter
        
    Returns:
        dict: Statistics for the department
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().date()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get attendance records for the department
        records = get_attendance_records(
            start_date=start_date,
            end_date=end_date,
            department=department
        )
        
        # Count incidents by type
        late_starts = sum(1 for r in records if r.status_type == 'LATE_START')
        early_ends = sum(1 for r in records if r.status_type == 'EARLY_END')
        not_on_job = sum(1 for r in records if r.status_type == 'NOT_ON_JOB')
        total_incidents = late_starts + early_ends + not_on_job
        
        # Get problem drivers
        problem_drivers = {}
        for record in records:
            driver_name = record.driver.name if record.driver else 'Unknown'
            if driver_name not in problem_drivers:
                problem_drivers[driver_name] = 0
            problem_drivers[driver_name] += 1
        
        # Sort drivers by incident count
        problem_drivers = dict(sorted(problem_drivers.items(), key=lambda x: x[1], reverse=True))
        
        # Get problem job sites
        problem_sites = {}
        for record in records:
            site_name = record.job_site.name if record.job_site else 'Unknown'
            if site_name not in problem_sites:
                problem_sites[site_name] = 0
            problem_sites[site_name] += 1
        
        # Sort job sites by incident count
        problem_sites = dict(sorted(problem_sites.items(), key=lambda x: x[1], reverse=True))
        
        # Calculate recent trend
        recent_date = end_date - timedelta(days=7)
        recent_records = [r for r in records if r.report_date >= recent_date]
        recent_incidents = len(recent_records)
        
        return {
            'department': department,
            'stats': {
                'total_incidents': total_incidents,
                'late_starts': late_starts,
                'early_ends': early_ends,
                'not_on_job': not_on_job,
                'recent_incidents': recent_incidents,
                'problem_drivers': problem_drivers,
                'problem_sites': problem_sites,
                'start_date': start_date,
                'end_date': end_date
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting department stats: {e}")
        return None

def update_attendance_trends(report_date):
    """
    Update attendance trends for a specific date
    
    This function calculates and updates trend data for:
    - Individual drivers
    - Job sites
    - Departments
    - Overall system
    
    Args:
        report_date (date): Report date
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        logger.info(f"Updating attendance trends for {report_date}")
        
        # Get attendance records for the date
        records = get_attendance_records(
            start_date=report_date,
            end_date=report_date
        )
        
        # Initialize counters
        overall_late_start = 0
        overall_early_end = 0
        overall_not_on_job = 0
        
        # Process driver trends
        drivers_processed = set()
        for record in records:
            # Skip if driver already processed for this date
            if record.driver_id in drivers_processed:
                continue
                
            drivers_processed.add(record.driver_id)
            
            # Get all records for this driver on this date
            driver_records = [r for r in records if r.driver_id == record.driver_id]
            
            # Count incident types
            late_starts = sum(1 for r in driver_records if r.status_type == 'LATE_START')
            early_ends = sum(1 for r in driver_records if r.status_type == 'EARLY_END')
            not_on_job = sum(1 for r in driver_records if r.status_type == 'NOT_ON_JOB')
            total = late_starts + early_ends + not_on_job
            
            # Add to overall counts
            overall_late_start += late_starts
            overall_early_end += early_ends
            overall_not_on_job += not_on_job
            
            # Get driver for department info
            driver = Driver.query.get(record.driver_id)
            department = driver.department if driver else None
            
            # Get previous week data for comparison
            prev_week_date = report_date - timedelta(days=7)
            prev_week_trend = AttendanceTrend.query.filter_by(
                trend_date=prev_week_date,
                trend_type='DRIVER',
                driver_id=record.driver_id
            ).first()
            
            # Get previous month data for comparison
            prev_month_date = report_date - timedelta(days=30)
            prev_month_trend = AttendanceTrend.query.filter_by(
                trend_date=prev_month_date,
                trend_type='DRIVER',
                driver_id=record.driver_id
            ).first()
            
            # Calculate week-over-week and month-over-month changes
            wow_change = None
            if prev_week_trend and prev_week_trend.total_incidents > 0:
                wow_change = (total - prev_week_trend.total_incidents) / prev_week_trend.total_incidents
                
            mom_change = None
            if prev_month_trend and prev_month_trend.total_incidents > 0:
                mom_change = (total - prev_month_trend.total_incidents) / prev_month_trend.total_incidents
            
            # Detect recurring patterns
            recurring_pattern = False
            pattern_description = None
            
            # Check for consistent issues on same day of week
            day_of_week = report_date.weekday()
            last_4_weeks = [report_date - timedelta(days=7*i) for i in range(1, 5)]
            
            same_day_trends = []
            for past_date in last_4_weeks:
                past_trend = AttendanceTrend.query.filter_by(
                    trend_type='DRIVER',
                    driver_id=record.driver_id
                ).filter(
                    AttendanceTrend.trend_date >= past_date,
                    AttendanceTrend.trend_date < past_date + timedelta(days=1)
                ).first()
                
                if past_trend:
                    same_day_trends.append(past_trend)
            
            # Check if there are incidents for at least 3 of the past 4 same days of week
            if len(same_day_trends) >= 3 and all(t.total_incidents > 0 for t in same_day_trends):
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                recurring_pattern = True
                pattern_description = f"Recurring issues on {day_names[day_of_week]}"
            
            # Update or create trend record
            trend = AttendanceTrend.query.filter_by(
                trend_date=report_date,
                trend_type='DRIVER',
                driver_id=record.driver_id
            ).first()
            
            if trend:
                # Update existing trend
                trend.late_start_count = late_starts
                trend.early_end_count = early_ends
                trend.not_on_job_count = not_on_job
                trend.total_incidents = total
                trend.week_over_week_change = wow_change
                trend.month_over_month_change = mom_change
                trend.recurring_pattern = recurring_pattern
                trend.pattern_description = pattern_description
                trend.department = department
                trend.updated_at = datetime.utcnow()
            else:
                # Create new trend
                trend = AttendanceTrend(
                    trend_date=report_date,
                    trend_type='DRIVER',
                    driver_id=record.driver_id,
                    late_start_count=late_starts,
                    early_end_count=early_ends,
                    not_on_job_count=not_on_job,
                    total_incidents=total,
                    week_over_week_change=wow_change,
                    month_over_month_change=mom_change,
                    recurring_pattern=recurring_pattern,
                    pattern_description=pattern_description,
                    department=department,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(trend)
            
            db.session.commit()
        
        # Process job site trends
        sites_processed = set()
        for record in records:
            # Skip if job site already processed for this date
            if record.job_site_id in sites_processed:
                continue
                
            sites_processed.add(record.job_site_id)
            
            # Get all records for this job site on this date
            site_records = [r for r in records if r.job_site_id == record.job_site_id]
            
            # Count incident types
            late_starts = sum(1 for r in site_records if r.status_type == 'LATE_START')
            early_ends = sum(1 for r in site_records if r.status_type == 'EARLY_END')
            not_on_job = sum(1 for r in site_records if r.status_type == 'NOT_ON_JOB')
            total = late_starts + early_ends + not_on_job
            
            # Get previous week data for comparison
            prev_week_date = report_date - timedelta(days=7)
            prev_week_trend = AttendanceTrend.query.filter_by(
                trend_date=prev_week_date,
                trend_type='JOB_SITE',
                job_site_id=record.job_site_id
            ).first()
            
            # Get previous month data for comparison
            prev_month_date = report_date - timedelta(days=30)
            prev_month_trend = AttendanceTrend.query.filter_by(
                trend_date=prev_month_date,
                trend_type='JOB_SITE',
                job_site_id=record.job_site_id
            ).first()
            
            # Calculate week-over-week and month-over-month changes
            wow_change = None
            if prev_week_trend and prev_week_trend.total_incidents > 0:
                wow_change = (total - prev_week_trend.total_incidents) / prev_week_trend.total_incidents
                
            mom_change = None
            if prev_month_trend and prev_month_trend.total_incidents > 0:
                mom_change = (total - prev_month_trend.total_incidents) / prev_month_trend.total_incidents
            
            # Update or create trend record
            trend = AttendanceTrend.query.filter_by(
                trend_date=report_date,
                trend_type='JOB_SITE',
                job_site_id=record.job_site_id
            ).first()
            
            if trend:
                # Update existing trend
                trend.late_start_count = late_starts
                trend.early_end_count = early_ends
                trend.not_on_job_count = not_on_job
                trend.total_incidents = total
                trend.week_over_week_change = wow_change
                trend.month_over_month_change = mom_change
                trend.updated_at = datetime.utcnow()
            else:
                # Create new trend
                trend = AttendanceTrend(
                    trend_date=report_date,
                    trend_type='JOB_SITE',
                    job_site_id=record.job_site_id,
                    late_start_count=late_starts,
                    early_end_count=early_ends,
                    not_on_job_count=not_on_job,
                    total_incidents=total,
                    week_over_week_change=wow_change,
                    month_over_month_change=mom_change,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(trend)
            
            db.session.commit()
        
        # Process department trends
        departments = set()
        for record in records:
            driver = Driver.query.get(record.driver_id)
            if driver and driver.department:
                departments.add(driver.department)
        
        for department in departments:
            # Get all records for this department on this date
            dept_records = []
            for record in records:
                driver = Driver.query.get(record.driver_id)
                if driver and driver.department == department:
                    dept_records.append(record)
            
            # Count incident types
            late_starts = sum(1 for r in dept_records if r.status_type == 'LATE_START')
            early_ends = sum(1 for r in dept_records if r.status_type == 'EARLY_END')
            not_on_job = sum(1 for r in dept_records if r.status_type == 'NOT_ON_JOB')
            total = late_starts + early_ends + not_on_job
            
            # Get previous week data for comparison
            prev_week_date = report_date - timedelta(days=7)
            prev_week_trend = AttendanceTrend.query.filter_by(
                trend_date=prev_week_date,
                trend_type='DEPARTMENT',
                department=department
            ).first()
            
            # Get previous month data for comparison
            prev_month_date = report_date - timedelta(days=30)
            prev_month_trend = AttendanceTrend.query.filter_by(
                trend_date=prev_month_date,
                trend_type='DEPARTMENT',
                department=department
            ).first()
            
            # Calculate week-over-week and month-over-month changes
            wow_change = None
            if prev_week_trend and prev_week_trend.total_incidents > 0:
                wow_change = (total - prev_week_trend.total_incidents) / prev_week_trend.total_incidents
                
            mom_change = None
            if prev_month_trend and prev_month_trend.total_incidents > 0:
                mom_change = (total - prev_month_trend.total_incidents) / prev_month_trend.total_incidents
            
            # Update or create trend record
            trend = AttendanceTrend.query.filter_by(
                trend_date=report_date,
                trend_type='DEPARTMENT',
                department=department
            ).first()
            
            if trend:
                # Update existing trend
                trend.late_start_count = late_starts
                trend.early_end_count = early_ends
                trend.not_on_job_count = not_on_job
                trend.total_incidents = total
                trend.week_over_week_change = wow_change
                trend.month_over_month_change = mom_change
                trend.updated_at = datetime.utcnow()
            else:
                # Create new trend
                trend = AttendanceTrend(
                    trend_date=report_date,
                    trend_type='DEPARTMENT',
                    department=department,
                    late_start_count=late_starts,
                    early_end_count=early_ends,
                    not_on_job_count=not_on_job,
                    total_incidents=total,
                    week_over_week_change=wow_change,
                    month_over_month_change=mom_change,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(trend)
            
            db.session.commit()
        
        # Process overall trends
        total_incidents = overall_late_start + overall_early_end + overall_not_on_job
        
        # Get previous week data for comparison
        prev_week_date = report_date - timedelta(days=7)
        prev_week_trend = AttendanceTrend.query.filter_by(
            trend_date=prev_week_date,
            trend_type='OVERALL'
        ).first()
        
        # Get previous month data for comparison
        prev_month_date = report_date - timedelta(days=30)
        prev_month_trend = AttendanceTrend.query.filter_by(
            trend_date=prev_month_date,
            trend_type='OVERALL'
        ).first()
        
        # Calculate week-over-week and month-over-month changes
        wow_change = None
        if prev_week_trend and prev_week_trend.total_incidents > 0:
            wow_change = (total_incidents - prev_week_trend.total_incidents) / prev_week_trend.total_incidents
            
        mom_change = None
        if prev_month_trend and prev_month_trend.total_incidents > 0:
            mom_change = (total_incidents - prev_month_trend.total_incidents) / prev_month_trend.total_incidents
        
        # Update or create overall trend record
        trend = AttendanceTrend.query.filter_by(
            trend_date=report_date,
            trend_type='OVERALL'
        ).first()
        
        if trend:
            # Update existing trend
            trend.late_start_count = overall_late_start
            trend.early_end_count = overall_early_end
            trend.not_on_job_count = overall_not_on_job
            trend.total_incidents = total_incidents
            trend.week_over_week_change = wow_change
            trend.month_over_month_change = mom_change
            trend.updated_at = datetime.utcnow()
        else:
            # Create new trend
            trend = AttendanceTrend(
                trend_date=report_date,
                trend_type='OVERALL',
                late_start_count=overall_late_start,
                early_end_count=overall_early_end,
                not_on_job_count=overall_not_on_job,
                total_incidents=total_incidents,
                week_over_week_change=wow_change,
                month_over_month_change=mom_change,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(trend)
        
        db.session.commit()
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating attendance trends: {e}")
        db.session.rollback()
        return False

def get_attendance_trends(trend_type='OVERALL', entity_id=None, department=None, 
                        start_date=None, end_date=None):
    """
    Get attendance trends
    
    Args:
        trend_type (str, optional): Trend type ('OVERALL', 'DRIVER', 'JOB_SITE', 'DEPARTMENT')
        entity_id (int, optional): Entity ID (driver_id or job_site_id)
        department (str, optional): Department name
        start_date (date, optional): Start date for filter
        end_date (date, optional): End date for filter
        
    Returns:
        list: List of AttendanceTrend objects
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().date()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Start with base query
        query = AttendanceTrend.query.filter_by(trend_type=trend_type)
        
        # Apply entity filters
        if trend_type == 'DRIVER' and entity_id:
            query = query.filter_by(driver_id=entity_id)
        elif trend_type == 'JOB_SITE' and entity_id:
            query = query.filter_by(job_site_id=entity_id)
        elif trend_type == 'DEPARTMENT' and department:
            query = query.filter_by(department=department)
        
        # Apply date range filter
        query = query.filter(
            AttendanceTrend.trend_date >= start_date,
            AttendanceTrend.trend_date <= end_date
        )
        
        # Order by date (oldest first for charting)
        query = query.order_by(AttendanceTrend.trend_date.asc())
        
        return query.all()
    
    except Exception as e:
        logger.error(f"Error getting attendance trends: {e}")
        return []

def get_problem_entities(trend_type='DRIVER', min_incidents=5, period_days=30):
    """
    Get entities with recurring attendance issues
    
    Args:
        trend_type (str, optional): Entity type ('DRIVER', 'JOB_SITE', 'DEPARTMENT')
        min_incidents (int, optional): Minimum number of incidents to be considered a problem
        period_days (int, optional): Number of days to look back
        
    Returns:
        list: List of problem entities with statistics
    """
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period_days)
        
        # Get trends for the period
        trends = get_attendance_trends(
            trend_type=trend_type,
            start_date=start_date,
            end_date=end_date
        )
        
        # Group by entity
        entities = {}
        
        for trend in trends:
            # Get entity ID based on trend type
            entity_id = None
            entity_name = None
            
            if trend_type == 'DRIVER':
                entity_id = trend.driver_id
                driver = Driver.query.get(entity_id)
                entity_name = driver.name if driver else f"Driver {entity_id}"
            elif trend_type == 'JOB_SITE':
                entity_id = trend.job_site_id
                job_site = JobSite.query.get(entity_id)
                entity_name = job_site.name if job_site else f"Job Site {entity_id}"
            elif trend_type == 'DEPARTMENT':
                entity_id = trend.department
                entity_name = trend.department
            
            if not entity_id:
                continue
            
            # Initialize entity data
            if entity_id not in entities:
                entities[entity_id] = {
                    'id': entity_id,
                    'name': entity_name,
                    'total_incidents': 0,
                    'late_starts': 0,
                    'early_ends': 0,
                    'not_on_job': 0,
                    'days_with_incidents': 0,
                    'recurring_pattern': False,
                    'pattern_description': None,
                    'recent_trend': 0  # positive = improving, negative = worsening
                }
            
            # Add trend data
            entities[entity_id]['total_incidents'] += trend.total_incidents
            entities[entity_id]['late_starts'] += trend.late_start_count
            entities[entity_id]['early_ends'] += trend.early_end_count
            entities[entity_id]['not_on_job'] += trend.not_on_job_count
            
            if trend.total_incidents > 0:
                entities[entity_id]['days_with_incidents'] += 1
            
            if trend.recurring_pattern:
                entities[entity_id]['recurring_pattern'] = True
                entities[entity_id]['pattern_description'] = trend.pattern_description
            
            # Track most recent trend change
            if trend.week_over_week_change is not None:
                entities[entity_id]['recent_trend'] = trend.week_over_week_change
        
        # Filter to entities with minimum incidents
        problem_entities = [e for e in entities.values() if e['total_incidents'] >= min_incidents]
        
        # Sort by total incidents (most problematic first)
        problem_entities.sort(key=lambda x: x['total_incidents'], reverse=True)
        
        return problem_entities
    
    except Exception as e:
        logger.error(f"Error getting problem entities: {e}")
        return []

def generate_attendance_report(start_date=None, end_date=None):
    """
    Generate a comprehensive attendance report
    
    Args:
        start_date (date, optional): Start date for report
        end_date (date, optional): End date for report
        
    Returns:
        dict: Report data
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().date()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get overall trends
        overall_trends = get_attendance_trends(
            trend_type='OVERALL',
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate overall statistics
        total_late_starts = sum(t.late_start_count for t in overall_trends)
        total_early_ends = sum(t.early_end_count for t in overall_trends)
        total_not_on_job = sum(t.not_on_job_count for t in overall_trends)
        total_incidents = sum(t.total_incidents for t in overall_trends)
        
        # Get department trends
        department_trends = {}
        departments = db.session.query(Driver.department).distinct().all()
        
        for dept in departments:
            department = dept[0]
            if not department:
                continue
                
            dept_trends = get_attendance_trends(
                trend_type='DEPARTMENT',
                department=department,
                start_date=start_date,
                end_date=end_date
            )
            
            if dept_trends:
                department_trends[department] = {
                    'trends': dept_trends,
                    'total_incidents': sum(t.total_incidents for t in dept_trends),
                    'late_starts': sum(t.late_start_count for t in dept_trends),
                    'early_ends': sum(t.early_end_count for t in dept_trends),
                    'not_on_job': sum(t.not_on_job_count for t in dept_trends)
                }
        
        # Get problem drivers
        problem_drivers = get_problem_entities(
            trend_type='DRIVER',
            min_incidents=3,
            period_days=(end_date - start_date).days
        )
        
        # Get problem job sites
        problem_sites = get_problem_entities(
            trend_type='JOB_SITE',
            min_incidents=3,
            period_days=(end_date - start_date).days
        )
        
        # Prepare chart data
        dates = [t.trend_date.strftime('%Y-%m-%d') for t in overall_trends]
        late_start_data = [t.late_start_count for t in overall_trends]
        early_end_data = [t.early_end_count for t in overall_trends]
        not_on_job_data = [t.not_on_job_count for t in overall_trends]
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': (end_date - start_date).days + 1
            },
            'overall': {
                'total_incidents': total_incidents,
                'late_starts': total_late_starts,
                'early_ends': total_early_ends,
                'not_on_job': total_not_on_job,
                'avg_per_day': total_incidents / len(overall_trends) if overall_trends else 0
            },
            'departments': department_trends,
            'problem_drivers': problem_drivers[:10],  # Top 10
            'problem_sites': problem_sites[:10],      # Top 10
            'chart_data': {
                'dates': dates,
                'late_starts': late_start_data,
                'early_ends': early_end_data,
                'not_on_job': not_on_job_data
            }
        }
    
    except Exception as e:
        logger.error(f"Error generating attendance report: {e}")
        return None