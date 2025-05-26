"""
TRAXORA Comprehensive Driver Reports

Provides daily, weekly, and monthly driver attendance reports with drill-down capabilities,
tally counts, and detailed analysis using authentic MTD data.
"""

from flask import Blueprint, render_template, request, jsonify
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# Initialize blueprint
comprehensive_reports_bp = Blueprint('comprehensive_reports', __name__)

logger = logging.getLogger(__name__)

def load_mtd_data():
    """Load and process MTD data from attached assets"""
    mtd_data = {
        'drivers': [],
        'locations': [],
        'daily_records': defaultdict(list)
    }
    
    try:
        # Load driving history data
        driving_files = [
            'attached_assets/DrivingHistory.csv',
            'attached_assets/DrivingHistory (13).csv',
            'attached_assets/DrivingHistory (14).csv',
            'attached_assets/DrivingHistory (19).csv'
        ]
        
        all_driving_data = []
        
        for file_path in driving_files:
            if os.path.exists(file_path):
                try:
                    # Try different CSV parsing approaches for your MTD files
                    df = pd.read_csv(file_path, encoding='utf-8', error_bad_lines=False, warn_bad_lines=False)
                    if len(df) > 0:
                        all_driving_data.append(df)
                        logger.info(f"Loaded {len(df)} records from {file_path}")
                except:
                    try:
                        # Try with different encoding
                        df = pd.read_csv(file_path, encoding='latin-1', error_bad_lines=False, warn_bad_lines=False)
                        if len(df) > 0:
                            all_driving_data.append(df)
                            logger.info(f"Loaded {len(df)} records from {file_path} with latin-1")
                    except Exception as e:
                        logger.warning(f"Could not load {file_path}: {e}")
        
        if all_driving_data:
            combined_df = pd.concat(all_driving_data, ignore_index=True)
            
            # Process driver data
            for _, row in combined_df.iterrows():
                driver_field = row.get('Driver')
                if pd.notna(driver_field):
                    driver_name = str(driver_field).strip()
                    if driver_name and driver_name != 'nan':
                        # Extract date from record
                        date_str = None
                        date_field = row.get('Date')
                        start_time_field = row.get('Start Time')
                        
                        if pd.notna(date_field):
                            date_str = str(date_field)
                        elif pd.notna(start_time_field):
                            date_str = str(start_time_field).split()[0]
                        
                        if date_str:
                            # Create driver record
                            driver_record = {
                                'name': driver_name,
                                'date': date_str,
                                'start_time': row.get('Start Time', ''),
                                'end_time': row.get('End Time', ''),
                                'location': row.get('Location', ''),
                                'asset': row.get('Asset', ''),
                                'job_site': extract_job_site(row),
                                'status': classify_attendance(row)
                            }
                            
                            mtd_data['daily_records'][date_str].append(driver_record)
                            
                            if driver_name not in mtd_data['drivers']:
                                mtd_data['drivers'].append(driver_name)
        
        logger.info(f"Processed {len(mtd_data['drivers'])} unique drivers")
        return mtd_data
        
    except Exception as e:
        logger.error(f"Error loading MTD data: {e}")
        return mtd_data

def extract_job_site(row):
    """Extract job site from MTD record"""
    # Look for job site patterns in various fields
    fields_to_check = ['Location', 'Asset', 'Description', 'Job']
    
    for field in fields_to_check:
        if field in row and pd.notna(row[field]):
            value = str(row[field])
            # Look for job patterns like 2024-004, TEXDIST, etc.
            import re
            patterns = [
                r'(\d{4}-\d{3})',  # 2024-004
                r'(\d{2}-\d{2})',   # 24-04
                r'(TEXDIST)',
                r'(HOUOH-HH)',
                r'(DALOH-HH)',
                r'(WTOH-HH)',
                r'(EQUIP\s+\w+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, value, re.IGNORECASE)
                if match:
                    return match.group(1)
    
    return 'Unknown'

def classify_attendance(row):
    """Classify driver attendance status"""
    start_time = row.get('Start Time', '')
    end_time = row.get('End Time', '')
    
    if not start_time or pd.isna(start_time):
        return 'Not On Job'
    
    try:
        # Parse start time
        if isinstance(start_time, str) and ':' in start_time:
            time_part = start_time.split()[-1] if ' ' in start_time else start_time
            hour = int(time_part.split(':')[0])
            
            # Classification rules
            if hour >= 8:  # Late start (after 8 AM)
                return 'Late Start'
            elif end_time and isinstance(end_time, str) and ':' in end_time:
                end_hour = int(end_time.split(':')[0])
                if end_hour < 16:  # Early end (before 4 PM)
                    return 'Early End'
            
            return 'On Time'
    except:
        pass
    
    return 'Unknown'

@comprehensive_reports_bp.route('/reports-dashboard')
def reports_dashboard():
    """Main reports dashboard"""
    mtd_data = load_mtd_data()
    
    # Get available dates
    available_dates = sorted(mtd_data['daily_records'].keys(), reverse=True)
    
    # Generate summary statistics
    total_drivers = len(mtd_data['drivers'])
    total_days = len(available_dates)
    
    # Calculate overall attendance stats
    attendance_summary = {
        'on_time': 0,
        'late_start': 0,
        'early_end': 0,
        'not_on_job': 0
    }
    
    for date_records in mtd_data['daily_records'].values():
        for record in date_records:
            status = record['status'].lower().replace(' ', '_')
            if status in attendance_summary:
                attendance_summary[status] += 1
    
    return render_template('comprehensive_reports_dashboard.html',
                         available_dates=available_dates,
                         total_drivers=total_drivers,
                         total_days=total_days,
                         attendance_summary=attendance_summary,
                         mtd_data=mtd_data)

@comprehensive_reports_bp.route('/daily-report/<date>')
def daily_report(date):
    """Individual daily report"""
    mtd_data = load_mtd_data()
    
    daily_records = mtd_data['daily_records'].get(date, [])
    
    # Calculate daily statistics
    daily_stats = {
        'total_drivers': len(daily_records),
        'on_time': len([r for r in daily_records if r['status'] == 'On Time']),
        'late_start': len([r for r in daily_records if r['status'] == 'Late Start']),
        'early_end': len([r for r in daily_records if r['status'] == 'Early End']),
        'not_on_job': len([r for r in daily_records if r['status'] == 'Not On Job'])
    }
    
    # Group by job site
    by_job_site = defaultdict(list)
    for record in daily_records:
        by_job_site[record['job_site']].append(record)
    
    return render_template('daily_report_detail.html',
                         date=date,
                         daily_records=daily_records,
                         daily_stats=daily_stats,
                         by_job_site=dict(by_job_site))

@comprehensive_reports_bp.route('/weekly-report')
def weekly_report():
    """Weekly compiled report"""
    start_date = request.args.get('start_date')
    
    if not start_date:
        # Default to current week
        today = datetime.now().date()
        start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
    
    mtd_data = load_mtd_data()
    
    # Calculate week range
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    week_dates = [(start_dt + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    # Compile weekly data
    weekly_data = {}
    weekly_totals = {
        'on_time': 0,
        'late_start': 0,
        'early_end': 0,
        'not_on_job': 0
    }
    
    for date in week_dates:
        daily_records = mtd_data['daily_records'].get(date, [])
        daily_stats = {
            'total': len(daily_records),
            'on_time': len([r for r in daily_records if r['status'] == 'On Time']),
            'late_start': len([r for r in daily_records if r['status'] == 'Late Start']),
            'early_end': len([r for r in daily_records if r['status'] == 'Early End']),
            'not_on_job': len([r for r in daily_records if r['status'] == 'Not On Job'])
        }
        
        weekly_data[date] = daily_stats
        
        # Add to weekly totals
        for key in weekly_totals:
            weekly_totals[key] += daily_stats.get(key, 0)
    
    return render_template('weekly_report_detail.html',
                         start_date=start_date,
                         week_dates=week_dates,
                         weekly_data=weekly_data,
                         weekly_totals=weekly_totals)

@comprehensive_reports_bp.route('/monthly-report')
def monthly_report():
    """Monthly compiled report"""
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    mtd_data = load_mtd_data()
    
    # Filter records for the month
    monthly_records = {}
    monthly_totals = {
        'on_time': 0,
        'late_start': 0,
        'early_end': 0,
        'not_on_job': 0
    }
    
    for date, records in mtd_data['daily_records'].items():
        if date.startswith(month):
            daily_stats = {
                'total': len(records),
                'on_time': len([r for r in records if r['status'] == 'On Time']),
                'late_start': len([r for r in records if r['status'] == 'Late Start']),
                'early_end': len([r for r in records if r['status'] == 'Early End']),
                'not_on_job': len([r for r in records if r['status'] == 'Not On Job'])
            }
            
            monthly_records[date] = daily_stats
            
            # Add to monthly totals
            for key in monthly_totals:
                monthly_totals[key] += daily_stats.get(key, 0)
    
    # Driver performance analysis
    driver_performance = defaultdict(lambda: {'days': 0, 'on_time': 0, 'late': 0, 'early': 0})
    
    for date, records in mtd_data['daily_records'].items():
        if date.startswith(month):
            for record in records:
                driver = record['name']
                driver_performance[driver]['days'] += 1
                if record['status'] == 'On Time':
                    driver_performance[driver]['on_time'] += 1
                elif record['status'] == 'Late Start':
                    driver_performance[driver]['late'] += 1
                elif record['status'] == 'Early End':
                    driver_performance[driver]['early'] += 1
    
    return render_template('monthly_report_detail.html',
                         month=month,
                         monthly_records=monthly_records,
                         monthly_totals=monthly_totals,
                         driver_performance=dict(driver_performance))

@comprehensive_reports_bp.route('/api/drill-down/<report_type>')
def drill_down_api(report_type):
    """API endpoint for drill-down data"""
    date = request.args.get('date')
    job_site = request.args.get('job_site')
    status = request.args.get('status')
    
    mtd_data = load_mtd_data()
    
    if report_type == 'daily' and date:
        records = mtd_data['daily_records'].get(date, [])
        
        # Filter by job site if specified
        if job_site:
            records = [r for r in records if r['job_site'] == job_site]
        
        # Filter by status if specified
        if status:
            records = [r for r in records if r['status'].lower().replace(' ', '_') == status]
        
        return jsonify(records)
    
    return jsonify([])