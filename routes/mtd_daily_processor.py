"""
MTD Daily Processor

This module processes your MTD data to generate daily attendance reports
for any specific date within the 26-day period (May 1-26, 2025).
"""

from flask import Blueprint, render_template, request, jsonify
import pandas as pd
import os
import logging
from datetime import datetime, time
from utils.jobsite_extractor import JobSiteExtractor

logger = logging.getLogger(__name__)

mtd_daily_bp = Blueprint('mtd_daily', __name__, url_prefix='/mtd-daily')

def process_daily_from_mtd(target_date):
    """Process a specific day from your MTD data to create daily attendance report"""
    try:
        mtd_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
        
        if not os.path.exists(mtd_file):
            return None
        
        # Load your MTD data
        df = pd.read_csv(mtd_file, skiprows=8, low_memory=False)
        
        # Convert EventDateTime to datetime
        df['EventDateTime'] = pd.to_datetime(df['EventDateTime'], errors='coerce')
        df['Date'] = df['EventDateTime'].dt.date
        
        # Filter for the specific target date
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        daily_data = df[df['Date'] == target_date_obj]
        
        if daily_data.empty:
            return {
                'date': target_date,
                'total_drivers': 0,
                'on_time': 0,
                'late': 0,
                'early_end': 0,
                'not_on_job': 0,
                'drivers': []
            }
        
        # Process each driver's attendance for this specific day
        driver_attendance = {}
        
        for _, row in daily_data.iterrows():
            if pd.isna(row['Textbox53']):
                continue
                
            assignment = str(row['Textbox53'])
            driver_name = extract_driver_name_from_assignment(assignment)
            
            if not driver_name:
                continue
            
            if driver_name not in driver_attendance:
                driver_attendance[driver_name] = {
                    'name': driver_name,
                    'assignment': assignment,
                    'events': [],
                    'locations': [],
                    'start_time': None,
                    'end_time': None
                }
            
            # Track events and locations
            event_time = row['EventDateTime']
            msg_type = str(row.get('MsgType', ''))
            location = str(row.get('Location', ''))
            
            driver_attendance[driver_name]['events'].append({
                'time': event_time,
                'type': msg_type,
                'location': location
            })
            
            if location and location != 'nan':
                driver_attendance[driver_name]['locations'].append(location)
        
        # Analyze each driver's daily performance
        daily_report = {
            'date': target_date,
            'total_drivers': len(driver_attendance),
            'on_time': 0,
            'late': 0,
            'early_end': 0,
            'not_on_job': 0,
            'drivers': []
        }
        
        for driver_name, data in driver_attendance.items():
            # Determine start and end times from events
            events = sorted(data['events'], key=lambda x: x['time'])
            
            # Find first "Key On" or work-related event
            work_start = None
            work_end = None
            
            for event in events:
                if event['type'] in ['Key On', 'Arrived'] and not work_start:
                    # Skip if this is at a residential location
                    if not is_residential_location(event['location']):
                        work_start = event['time']
                
                if event['type'] in ['Key Off', 'Departed']:
                    if not is_residential_location(event['location']):
                        work_end = event['time']
            
            # Determine job site from locations
            job_site_info = get_job_site_from_locations(data['locations'])
            
            # Calculate performance category
            category = categorize_daily_performance(work_start, work_end, job_site_info)
            
            driver_record = {
                'name': driver_name,
                'assignment': data['assignment'],
                'start_time': work_start.strftime('%H:%M:%S') if work_start else 'No Start',
                'end_time': work_end.strftime('%H:%M:%S') if work_end else 'No End',
                'job_site': job_site_info['display_name'],
                'zone': job_site_info['zone'],
                'working_hours': job_site_info['working_hours'],
                'category': category,
                'total_events': len(data['events'])
            }
            
            daily_report['drivers'].append(driver_record)
            daily_report[category] += 1
        
        logger.info(f"Daily report for {target_date}: {daily_report['total_drivers']} drivers processed")
        return daily_report
        
    except Exception as e:
        logger.error(f"Error processing daily MTD data for {target_date}: {e}")
        return None

def extract_driver_name_from_assignment(assignment_str):
    """Extract driver name from asset assignment string"""
    try:
        assignment = str(assignment_str)
        
        # Format 1: "#210003 - AMMAR I. ELHAMAD FORD F150 2024"
        if ' - ' in assignment and assignment.startswith('#'):
            parts = assignment.split(' - ', 1)
            if len(parts) > 1:
                name_and_vehicle = parts[1]
                vehicle_patterns = ['FORD', 'CHEVY', 'RAM', 'TOYOTA', 'NISSAN', 'GMC', 'HONDA']
                
                for pattern in vehicle_patterns:
                    if pattern in name_and_vehicle.upper():
                        name_part = name_and_vehicle[:name_and_vehicle.upper().find(pattern)].strip()
                        if name_part:
                            return name_part
                
                return name_and_vehicle
        
        # Format 2: "ET-01 (SAUL MARTINEZ ALVAREZ) RAM 1500 2022"
        elif '(' in assignment and ')' in assignment:
            start = assignment.find('(') + 1
            end = assignment.find(')')
            if start > 0 and end > start:
                return assignment[start:end].strip()
        
        return None
        
    except Exception:
        return None

def is_residential_location(location):
    """Check if location is residential/personal"""
    if not location or location == 'nan':
        return False
    
    residential_keywords = [
        'sunflower dr', 'mansfield', 'residential', 'home',
        'apartment', 'house', 'drive', 'street', 'lane'
    ]
    
    location_lower = location.lower()
    return any(keyword in location_lower for keyword in residential_keywords)

def get_job_site_from_locations(locations):
    """Extract job site from list of locations for the day"""
    if not locations:
        return {
            'job_number': 'NO_LOCATION',
            'zone': None,
            'display_name': 'No Location Data',
            'working_hours': 0.0
        }
    
    # Find the most common work location (excluding residential)
    work_locations = [loc for loc in locations if not is_residential_location(loc)]
    
    if not work_locations:
        return {
            'job_number': 'PERSONAL',
            'zone': 'Residential',
            'display_name': 'Personal Vehicle Use',
            'working_hours': 0.0
        }
    
    # Use the first work location found
    location = work_locations[0]
    
    # Extract job site using your location patterns
    if 'TEXDIST' in location.upper():
        if 'North Richland Hills' in location:
            return {
                'job_number': 'TEXDIST-NRH',
                'zone': 'North Richland Hills',
                'display_name': 'TEXDIST (North Richland Hills)',
                'working_hours': 8.0
            }
        elif 'Hurst' in location:
            return {
                'job_number': 'TEXDIST-HUR',
                'zone': 'Hurst',
                'display_name': 'TEXDIST (Hurst)',
                'working_hours': 8.0
            }
        else:
            return {
                'job_number': 'TEXDIST',
                'zone': None,
                'display_name': 'TEXDIST Operations',
                'working_hours': 8.0
            }
    
    # Extract city from location
    if ',' in location:
        parts = location.split(',')
        if len(parts) >= 2:
            area = parts[-1].strip()
            if 'TX' in area:
                city = area.replace('TX', '').strip()
                return {
                    'job_number': f'TX-{city.upper()[:3]}',
                    'zone': city,
                    'display_name': f'Texas Operations ({city})',
                    'working_hours': 8.0
                }
    
    return {
        'job_number': 'UNKNOWN',
        'zone': None,
        'display_name': 'Unknown Job Site',
        'working_hours': 8.0
    }

def categorize_daily_performance(start_time, end_time, job_site_info):
    """Categorize driver performance for a specific day"""
    if not start_time:
        return 'not_on_job'
    
    # Expected start time (7:00 AM)
    expected_start = time(7, 0)
    actual_start = start_time.time()
    
    # Expected working hours
    expected_hours = job_site_info['working_hours']
    
    if expected_hours == 0.0:  # Personal vehicle use
        return 'not_on_job'
    
    # Check if late start (more than 15 minutes after 7:00 AM)
    late_threshold = time(7, 15)
    if actual_start > late_threshold:
        return 'late'
    
    # Check if early end (if we have end time)
    if end_time and expected_hours > 0:
        work_duration = (end_time - start_time).total_seconds() / 3600  # hours
        if work_duration < (expected_hours - 1.0):  # More than 1 hour short
            return 'early_end'
    
    # Otherwise, on time
    return 'on_time'

@mtd_daily_bp.route('/')
def daily_selector():
    """Daily report selector page"""
    # Available dates from your MTD period (May 1-26, 2025)
    available_dates = []
    start_date = datetime(2025, 5, 1)
    end_date = datetime(2025, 5, 26)
    
    current = start_date
    while current <= end_date:
        available_dates.append(current.strftime('%Y-%m-%d'))
        current += pd.Timedelta(days=1)
    
    available_dates.reverse()  # Most recent first
    
    return render_template('mtd_daily/selector.html', available_dates=available_dates)

@mtd_daily_bp.route('/report/<date>')
def daily_report(date):
    """Display daily report for specific date"""
    report_data = process_daily_from_mtd(date)
    
    if not report_data:
        return f"No data available for {date}", 404
    
    return render_template('mtd_daily/report.html', report=report_data)

@mtd_daily_bp.route('/api/daily/<date>')
def api_daily_report(date):
    """API endpoint for daily report data"""
    report_data = process_daily_from_mtd(date)
    return jsonify(report_data) if report_data else jsonify({'error': 'No data available'})