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
from sqlalchemy import func, desc, and_
from app import db
from models.attendance import AttendanceRecord, Driver, JobSite, AttendanceTrend
from models import Asset
from utils.file_processor import read_excel_file

# Initialize logger
logger = logging.getLogger(__name__)

def get_or_create_driver(name, employee_id, asset_id=None, department=None):
    """
    Get or create a driver record
    
    Args:
        name (str): Driver name
        employee_id (str): Employee ID
        asset_id (int, optional): Associated asset ID
        department (str, optional): Department
        
    Returns:
        Driver: Driver object
    """
    try:
        driver = Driver.query.filter_by(employee_id=employee_id).first()
        
        if not driver:
            driver = Driver(
                name=name,
                employee_id=employee_id,
                asset_id=asset_id,
                department=department,
                is_active=True
            )
            db.session.add(driver)
            db.session.commit()
            logger.info(f"Created new driver: {name} ({employee_id})")
        elif asset_id and driver.asset_id != asset_id:
            # Update asset if different
            driver.asset_id = asset_id
            db.session.commit()
            logger.info(f"Updated asset for driver {name} to {asset_id}")
            
        return driver
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error getting/creating driver: {e}")
        return None

def get_or_create_job_site(name, job_number, location=None):
    """
    Get or create a job site record
    
    Args:
        name (str): Job site name
        job_number (str): Job number
        location (dict, optional): Location data with lat/long
        
    Returns:
        JobSite: JobSite object
    """
    try:
        job_site = JobSite.query.filter_by(job_number=job_number).first()
        
        if not job_site:
            job_site = JobSite(
                name=name,
                job_number=job_number,
                is_active=True
            )
            
            if location:
                job_site.latitude = location.get('latitude')
                job_site.longitude = location.get('longitude')
                
            db.session.add(job_site)
            db.session.commit()
            logger.info(f"Created new job site: {name} ({job_number})")
            
        return job_site
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error getting/creating job site: {e}")
        return None

def save_attendance_record(report_date, driver_id, asset_id, job_site_id, status_type, 
                          expected_start=None, actual_start=None, expected_end=None, 
                          actual_end=None, minutes_late=None, minutes_early=None, 
                          expected_job_id=None, actual_job_id=None, notes=None):
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
        notes (str, optional): Additional notes
        
    Returns:
        AttendanceRecord: Saved attendance record
    """
    try:
        # Check if record already exists for this driver & date & status_type
        existing = AttendanceRecord.query.filter_by(
            report_date=report_date,
            driver_id=driver_id,
            status_type=status_type
        ).first()
        
        if existing:
            # Update existing record
            existing.asset_id = asset_id
            existing.job_site_id = job_site_id
            existing.expected_start = expected_start
            existing.actual_start = actual_start
            existing.expected_end = expected_end
            existing.actual_end = actual_end
            existing.minutes_late = minutes_late
            existing.minutes_early = minutes_early
            existing.expected_job_id = expected_job_id
            existing.actual_job_id = actual_job_id
            existing.notes = notes
            
            db.session.commit()
            logger.info(f"Updated attendance record for driver {driver_id} on {report_date}")
            return existing
        else:
            # Create new record
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
                actual_job_id=actual_job_id,
                notes=notes
            )
            
            db.session.add(record)
            db.session.commit()
            logger.info(f"Saved new attendance record for driver {driver_id} on {report_date}")
            return record
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving attendance record: {e}")
        return None

def process_attendance_report(report_file_path, report_date=None, report_type=None):
    """
    Process attendance report and save records to database
    
    Args:
        report_file_path (str): Path to report Excel file
        report_date (datetime, optional): Report date, defaults to file date or today
        report_type (str, optional): Report type (PRIOR_DAY or CURRENT_DAY)
        
    Returns:
        dict: Processing results
    """
    try:
        logger.info(f"Processing attendance report: {report_file_path}")
        
        # Extract report date from filename if not provided
        if not report_date:
            filename = os.path.basename(report_file_path)
            date_parts = filename.split('_')
            if len(date_parts) > 1:
                try:
                    date_str = date_parts[1].split('.')[0]  # Format: YYYY-MM-DD
                    report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except:
                    report_date = datetime.now().date()
            else:
                report_date = datetime.now().date()
        
        # Read the Excel file
        df = read_excel_file(report_file_path)
        
        if df is None or df.empty:
            logger.error(f"Failed to read report file or file is empty: {report_file_path}")
            return {'success': False, 'error': 'Failed to read report file or file is empty'}
        
        # Define required columns based on report format
        if 'Driver' not in df.columns or 'Asset' not in df.columns:
            logger.error(f"Report file does not have required columns: {report_file_path}")
            return {'success': False, 'error': 'Report file does not have required columns'}
        
        # Process each row in the report
        records_processed = 0
        late_start_count = 0
        early_end_count = 0
        not_on_job_count = 0
        
        for _, row in df.iterrows():
            try:
                # Extract driver info - format might be "Name (ID)" or just "Name"
                driver_name = row.get('Driver', '').strip()
                employee_id = None
                
                # Try to extract employee ID from driver name
                if '(' in driver_name and ')' in driver_name:
                    parts = driver_name.split('(')
                    driver_name = parts[0].strip()
                    employee_id = parts[1].split(')')[0].strip()
                
                # If no employee ID, use name as ID
                if not employee_id:
                    employee_id = f"EMP-{driver_name.replace(' ', '')}"
                
                # Get asset info
                asset_identifier = str(row.get('Asset', '')).strip()
                
                # Try to get asset from database
                asset = Asset.query.filter_by(asset_identifier=asset_identifier).first()
                asset_id = asset.id if asset else None
                
                # Get or create job site
                job_site_name = str(row.get('Job Site', '')).strip()
                job_number = str(row.get('Job Number', '')).strip()
                
                if not job_number and 'Job #' in df.columns:
                    job_number = str(row.get('Job #', '')).strip()
                
                # If still no job number, generate one
                if not job_number:
                    job_number = f"JOB-{job_site_name.replace(' ', '')}"
                
                job_site = get_or_create_job_site(job_site_name, job_number)
                job_site_id = job_site.id if job_site else None
                
                # Get driver record
                department = str(row.get('Department', '')).strip()
                driver = get_or_create_driver(driver_name, employee_id, asset_id, department)
                driver_id = driver.id if driver else None
                
                if not driver_id or not job_site_id:
                    logger.warning(f"Missing driver or job site for row: {row}")
                    continue
                
                # Process status types
                # LATE START
                if 'Late Start' in df.columns and row.get('Late Start', '').strip().upper() in ['YES', 'Y', 'TRUE', '1']:
                    expected_start = None
                    actual_start = None
                    minutes_late = None
                    
                    # Try to parse time values
                    if 'Expected Start' in df.columns:
                        try:
                            expected_start_str = str(row.get('Expected Start', '')).strip()
                            expected_start = datetime.strptime(f"{report_date.strftime('%Y-%m-%d')} {expected_start_str}", "%Y-%m-%d %H:%M")
                        except:
                            pass
                            
                    if 'Actual Start' in df.columns:
                        try:
                            actual_start_str = str(row.get('Actual Start', '')).strip()
                            actual_start = datetime.strptime(f"{report_date.strftime('%Y-%m-%d')} {actual_start_str}", "%Y-%m-%d %H:%M")
                        except:
                            pass
                    
                    if 'Minutes Late' in df.columns:
                        try:
                            minutes_late = int(row.get('Minutes Late', 0))
                        except:
                            pass
                    
                    # Save record
                    save_attendance_record(
                        report_date=report_date,
                        driver_id=driver_id,
                        asset_id=asset_id,
                        job_site_id=job_site_id,
                        status_type='LATE_START',
                        expected_start=expected_start,
                        actual_start=actual_start,
                        minutes_late=minutes_late
                    )
                    late_start_count += 1
                
                # EARLY END
                if 'Early End' in df.columns and row.get('Early End', '').strip().upper() in ['YES', 'Y', 'TRUE', '1']:
                    expected_end = None
                    actual_end = None
                    minutes_early = None
                    
                    # Try to parse time values
                    if 'Expected End' in df.columns:
                        try:
                            expected_end_str = str(row.get('Expected End', '')).strip()
                            expected_end = datetime.strptime(f"{report_date.strftime('%Y-%m-%d')} {expected_end_str}", "%Y-%m-%d %H:%M")
                        except:
                            pass
                            
                    if 'Actual End' in df.columns:
                        try:
                            actual_end_str = str(row.get('Actual End', '')).strip()
                            actual_end = datetime.strptime(f"{report_date.strftime('%Y-%m-%d')} {actual_end_str}", "%Y-%m-%d %H:%M")
                        except:
                            pass
                    
                    if 'Minutes Early' in df.columns:
                        try:
                            minutes_early = int(row.get('Minutes Early', 0))
                        except:
                            pass
                    
                    # Save record
                    save_attendance_record(
                        report_date=report_date,
                        driver_id=driver_id,
                        asset_id=asset_id,
                        job_site_id=job_site_id,
                        status_type='EARLY_END',
                        expected_end=expected_end,
                        actual_end=actual_end,
                        minutes_early=minutes_early
                    )
                    early_end_count += 1
                
                # NOT ON JOB
                if 'Not On Job' in df.columns and row.get('Not On Job', '').strip().upper() in ['YES', 'Y', 'TRUE', '1']:
                    expected_job_id = None
                    actual_job_id = None
                    
                    # Try to get expected job site
                    if 'Expected Job' in df.columns:
                        expected_job_name = str(row.get('Expected Job', '')).strip()
                        expected_job_number = f"JOB-{expected_job_name.replace(' ', '')}"
                        expected_job = get_or_create_job_site(expected_job_name, expected_job_number)
                        expected_job_id = expected_job.id if expected_job else None
                    
                    # Try to get actual job site
                    if 'Actual Job' in df.columns:
                        actual_job_name = str(row.get('Actual Job', '')).strip()
                        actual_job_number = f"JOB-{actual_job_name.replace(' ', '')}"
                        actual_job = get_or_create_job_site(actual_job_name, actual_job_number)
                        actual_job_id = actual_job.id if actual_job else None
                    
                    # Save record
                    save_attendance_record(
                        report_date=report_date,
                        driver_id=driver_id,
                        asset_id=asset_id,
                        job_site_id=job_site_id,
                        status_type='NOT_ON_JOB',
                        expected_job_id=expected_job_id,
                        actual_job_id=actual_job_id
                    )
                    not_on_job_count += 1
                
                records_processed += 1
                
            except Exception as e:
                logger.error(f"Error processing row: {e}")
                continue
        
        # Update trend summaries
        update_attendance_trends(report_date)
        
        return {
            'success': True,
            'records_processed': records_processed,
            'late_start_count': late_start_count,
            'early_end_count': early_end_count,
            'not_on_job_count': not_on_job_count,
            'report_date': report_date
        }
    
    except Exception as e:
        logger.error(f"Error processing attendance report: {e}")
        return {'success': False, 'error': str(e)}

def update_attendance_trends(report_date):
    """
    Update attendance trend summary data for a given date
    
    Args:
        report_date (datetime): Report date
        
    Returns:
        bool: Success or failure
    """
    try:
        # Calculate counts for each status type
        late_start_count = AttendanceRecord.query.filter(
            AttendanceRecord.report_date == report_date,
            AttendanceRecord.status_type == 'LATE_START'
        ).count()
        
        early_end_count = AttendanceRecord.query.filter(
            AttendanceRecord.report_date == report_date,
            AttendanceRecord.status_type == 'EARLY_END'
        ).count()
        
        not_on_job_count = AttendanceRecord.query.filter(
            AttendanceRecord.report_date == report_date,
            AttendanceRecord.status_type == 'NOT_ON_JOB'
        ).count()
        
        # Update or create trend records
        for status_type, count in [
            ('LATE_START', late_start_count),
            ('EARLY_END', early_end_count),
            ('NOT_ON_JOB', not_on_job_count)
        ]:
            # Check if trend record exists
            trend = AttendanceTrend.query.filter_by(
                trend_date=report_date,
                trend_type='DAILY',
                status_type=status_type
            ).first()
            
            if trend:
                trend.count = count
                db.session.commit()
            else:
                trend = AttendanceTrend(
                    trend_date=report_date,
                    trend_type='DAILY',
                    status_type=status_type,
                    count=count
                )
                db.session.add(trend)
                db.session.commit()
        
        # Calculate and update weekly trends if this is the last day of the week
        if report_date.weekday() == 6:  # Sunday (0=Monday, 6=Sunday)
            week_start = report_date - timedelta(days=6)
            
            for status_type in ['LATE_START', 'EARLY_END', 'NOT_ON_JOB']:
                weekly_count = AttendanceRecord.query.filter(
                    AttendanceRecord.report_date.between(week_start, report_date),
                    AttendanceRecord.status_type == status_type
                ).count()
                
                # Create or update weekly trend
                weekly_trend = AttendanceTrend.query.filter_by(
                    trend_date=report_date,
                    trend_type='WEEKLY',
                    status_type=status_type
                ).first()
                
                if weekly_trend:
                    weekly_trend.count = weekly_count
                    db.session.commit()
                else:
                    weekly_trend = AttendanceTrend(
                        trend_date=report_date,
                        trend_type='WEEKLY',
                        status_type=status_type,
                        count=weekly_count
                    )
                    db.session.add(weekly_trend)
                    db.session.commit()
        
        # Calculate and update monthly trends if this is the last day of the month
        last_day_of_month = (report_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        if report_date.day == last_day_of_month.day:
            month_start = report_date.replace(day=1)
            
            for status_type in ['LATE_START', 'EARLY_END', 'NOT_ON_JOB']:
                monthly_count = AttendanceRecord.query.filter(
                    AttendanceRecord.report_date.between(month_start, report_date),
                    AttendanceRecord.status_type == status_type
                ).count()
                
                # Create or update monthly trend
                monthly_trend = AttendanceTrend.query.filter_by(
                    trend_date=report_date,
                    trend_type='MONTHLY',
                    status_type=status_type
                ).first()
                
                if monthly_trend:
                    monthly_trend.count = monthly_count
                    db.session.commit()
                else:
                    monthly_trend = AttendanceTrend(
                        trend_date=report_date,
                        trend_type='MONTHLY',
                        status_type=status_type,
                        count=monthly_count
                    )
                    db.session.add(monthly_trend)
                    db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating attendance trends: {e}")
        return False

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
        
        if status_type and status_type != 'all':
            query = query.filter(AttendanceRecord.status_type == status_type)
        
        if driver_id and driver_id != 'all':
            query = query.filter(AttendanceRecord.driver_id == driver_id)
            
        if job_site_id and job_site_id != 'all':
            query = query.filter(AttendanceRecord.job_site_id == job_site_id)
            
        results = query.all()
        
        dates = [r.date for r in results]
        counts = [r.count for r in results]
        
        # Fill in missing dates with zero counts
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date.date() if isinstance(current_date, datetime) else current_date)
            current_date += timedelta(days=1)
        
        filled_counts = []
        for date in all_dates:
            if date in dates:
                idx = dates.index(date)
                filled_counts.append(counts[idx])
            else:
                filled_counts.append(0)
        
        return {
            'dates': all_dates,
            'counts': filled_counts,
            'total': sum(filled_counts),
            'average': round(sum(filled_counts) / len(filled_counts), 2) if filled_counts else 0
        }
    except Exception as e:
        logger.error(f"Error getting attendance trends: {e}")
        return {
            'dates': [],
            'counts': [],
            'total': 0,
            'average': 0
        }

def get_top_drivers_with_issues(start_date, end_date, status_type='LATE_START', limit=10):
    """
    Get top drivers with attendance issues of a specific type
    
    Args:
        start_date (datetime): Start date
        end_date (datetime): End date
        status_type (str): Status type (LATE_START, EARLY_END, NOT_ON_JOB)
        limit (int, optional): Limit number of results
        
    Returns:
        list: List of drivers with issue counts and trends
    """
    try:
        # Get current period counts
        current_results = db.session.query(
            AttendanceRecord.driver_id,
            func.count(AttendanceRecord.id).label('issue_count')
        ).filter(
            AttendanceRecord.report_date.between(start_date, end_date),
            AttendanceRecord.status_type == status_type
        ).group_by(
            AttendanceRecord.driver_id
        ).order_by(
            desc('issue_count')
        ).limit(limit).all()
        
        # Calculate previous period for trend comparison
        period_length = (end_date - start_date).days + 1
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=period_length)
        
        # Get driver details and calculate trends
        driver_data = []
        for r in current_results:
            driver = Driver.query.get(r.driver_id)
            
            if not driver:
                continue
                
            # Get asset details
            asset = Asset.query.get(driver.asset_id) if driver.asset_id else None
            asset_identifier = asset.asset_identifier if asset else 'Unknown'
            
            # Get previous period count for this driver
            prev_count = db.session.query(
                func.count(AttendanceRecord.id)
            ).filter(
                AttendanceRecord.report_date.between(prev_start_date, prev_end_date),
                AttendanceRecord.status_type == status_type,
                AttendanceRecord.driver_id == r.driver_id
            ).scalar() or 0
            
            # Calculate trend percentage
            if prev_count == 0:
                trend = 100 if r.issue_count > 0 else 0
            else:
                trend = round(((r.issue_count - prev_count) / prev_count) * 100, 1)
            
            # Get last incident date
            last_incident = db.session.query(
                AttendanceRecord.report_date
            ).filter(
                AttendanceRecord.driver_id == r.driver_id,
                AttendanceRecord.status_type == status_type
            ).order_by(
                AttendanceRecord.report_date.desc()
            ).first()
            
            last_incident_date = last_incident.report_date.strftime('%Y-%m-%d') if last_incident else 'Unknown'
            
            driver_data.append({
                'id': r.driver_id,
                'name': driver.name,
                'asset': {'asset_identifier': asset_identifier},
                'department': driver.department or 'Unknown',
                'incident_count': r.issue_count,
                'last_incident': last_incident_date,
                'trend': trend
            })
        
        return driver_data
    except Exception as e:
        logger.error(f"Error getting top drivers with issues: {e}")
        return []

def get_attendance_by_job_site(start_date, end_date, limit=5):
    """
    Get attendance issues grouped by job site
    
    Args:
        start_date (datetime): Start date
        end_date (datetime): End date
        limit (int): Maximum number of job sites to return
        
    Returns:
        dict: Dictionary with job site attendance data
    """
    try:
        # Get counts by job site and status type
        results = db.session.query(
            AttendanceRecord.job_site_id,
            AttendanceRecord.status_type,
            func.count(AttendanceRecord.id).label('count')
        ).filter(
            AttendanceRecord.report_date.between(start_date, end_date)
        ).group_by(
            AttendanceRecord.job_site_id,
            AttendanceRecord.status_type
        ).all()
        
        # Group by job site
        job_site_data = {}
        for r in results:
            job_site = JobSite.query.get(r.job_site_id)
            
            if not job_site:
                continue
                
            job_site_name = job_site.name
            
            if job_site_name not in job_site_data:
                job_site_data[job_site_name] = {
                    'job_site_id': r.job_site_id,
                    'job_site_name': job_site_name,
                    'LATE_START': 0,
                    'EARLY_END': 0,
                    'NOT_ON_JOB': 0,
                    'total': 0
                }
            
            job_site_data[job_site_name][r.status_type] = r.count
            job_site_data[job_site_name]['total'] += r.count
        
        # Convert to list and sort by total
        job_sites_list = list(job_site_data.values())
        job_sites_list.sort(key=lambda x: x['total'], reverse=True)
        
        # Limit to top N job sites
        top_job_sites = job_sites_list[:limit]
        
        # Prepare data for chart
        labels = [site['job_site_name'] for site in top_job_sites]
        late_start_data = [site['LATE_START'] for site in top_job_sites]
        early_end_data = [site['EARLY_END'] for site in top_job_sites]
        not_on_job_data = [site['NOT_ON_JOB'] for site in top_job_sites]
        
        return {
            'labels': labels,
            'late_start_data': late_start_data,
            'early_end_data': early_end_data,
            'not_on_job_data': not_on_job_data,
            'job_sites': top_job_sites
        }
    except Exception as e:
        logger.error(f"Error getting attendance by job site: {e}")
        return {
            'labels': [],
            'late_start_data': [],
            'early_end_data': [],
            'not_on_job_data': [],
            'job_sites': []
        }

def get_weekly_comparison_data(status_type, weeks=4):
    """
    Get weekly comparison data for a specific status type
    
    Args:
        status_type (str): Status type (LATE_START, EARLY_END, NOT_ON_JOB)
        weeks (int): Number of weeks to compare
        
    Returns:
        dict: Dictionary with weekly comparison data
    """
    try:
        end_date = datetime.now().date()
        
        # Get data for each week
        weekly_data = []
        labels = []
        counts = []
        
        for i in range(weeks):
            week_end = end_date - timedelta(days=(7 * i + end_date.weekday()))
            week_start = week_end - timedelta(days=6)
            
            # Format week label
            week_label = f"Week {weeks-i}"
            
            # Try to get from pre-aggregated weekly trends first
            weekly_trend = AttendanceTrend.query.filter_by(
                trend_date=week_end,
                trend_type='WEEKLY',
                status_type=status_type
            ).first()
            
            if weekly_trend:
                count = weekly_trend.count
            else:
                # Calculate on-the-fly if not pre-aggregated
                count = AttendanceRecord.query.filter(
                    AttendanceRecord.report_date.between(week_start, week_end),
                    AttendanceRecord.status_type == status_type
                ).count()
            
            weekly_data.append({
                'week': week_label,
                'start_date': week_start.strftime('%Y-%m-%d'),
                'end_date': week_end.strftime('%Y-%m-%d'),
                'count': count
            })
            
            labels.append(week_label)
            counts.append(count)
        
        return {
            'weekly_data': weekly_data,
            'labels': labels,
            'counts': counts
        }
    except Exception as e:
        logger.error(f"Error getting weekly comparison data: {e}")
        return {
            'weekly_data': [],
            'labels': [],
            'counts': []
        }

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