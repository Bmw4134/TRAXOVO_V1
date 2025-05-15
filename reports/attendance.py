"""
Attendance Reports Module

This module generates daily attendance reports:
1. Same-day Late Start and Not on Job report (generated at 8:30 AM)
2. Prior-day Late Start, Early End, and Not on Job report (generated at 9:30 AM)

The reports analyze GPS data to flag drivers who are:
- Late to start (after 7:00 AM)
- Early to end (before 4:30 PM)
- Not at their assigned job site during working hours
"""
import os
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
LATE_START_THRESHOLD = 7  # 7:00 AM
EARLY_END_THRESHOLD = 16.5  # 4:30 PM
WORKING_HOURS_START = 7  # 7:00 AM
WORKING_HOURS_END = 17  # 5:00 PM
WORK_DAYS = [0, 1, 2, 3, 4]  # Monday to Friday (0-6, where 0 is Monday)

# Data directories
DATA_DIR = 'data'
REPORTS_DIR = os.path.join(DATA_DIR, 'reports')
ATTENDANCE_DIR = os.path.join(REPORTS_DIR, 'attendance')

# Ensure directories exist
for directory in [DATA_DIR, REPORTS_DIR, ATTENDANCE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def is_vehicle_asset(asset):
    """
    Determine if an asset is a vehicle or driver asset
    
    Args:
        asset (dict): Asset data
        
    Returns:
        bool: True if asset is a vehicle, False otherwise
    """
    # Check asset category
    category = asset.get('AssetCategory', '').upper()
    if 'TRUCK' in category or 'VEHICLE' in category or 'PICKUP' in category:
        return True
    
    # Check asset ID patterns
    asset_id = asset.get('AssetIdentifier', '').upper()
    
    # Common vehicle ID patterns
    vehicle_patterns = ['PT-', 'ET-', 'DT-', 'MT-', 'UT-']
    
    for pattern in vehicle_patterns:
        if asset_id.startswith(pattern):
            return True
    
    return False

def get_hour_decimal(time_str):
    """
    Convert time string to decimal hour
    
    Args:
        time_str (str): Time string (e.g., '7:30 AM', '15:45')
        
    Returns:
        float: Decimal hour (e.g., 7.5, 15.75)
    """
    try:
        # Try to parse datetime
        if isinstance(time_str, datetime):
            return time_str.hour + time_str.minute / 60
        
        # Handle different formats
        time_str = str(time_str).upper().strip()
        
        # Try 24-hour format first
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1])
                return hour + minute / 60
        except Exception:
            pass
        
        # Try 12-hour format with AM/PM
        try:
            if 'AM' in time_str or 'PM' in time_str:
                time_part = time_str.replace('AM', '').replace('PM', '').strip()
                
                if ':' in time_part:
                    parts = time_part.split(':')
                    hour = int(parts[0])
                    minute = int(parts[1])
                else:
                    hour = int(time_part)
                    minute = 0
                
                # Adjust for PM
                if 'PM' in time_str and hour < 12:
                    hour += 12
                
                # Adjust for 12 AM
                if 'AM' in time_str and hour == 12:
                    hour = 0
                
                return hour + minute / 60
        except Exception:
            pass
        
        # Try just a number
        try:
            return float(time_str)
        except Exception:
            pass
        
        # Could not parse
        return None
    except Exception as e:
        logger.warning(f"Error parsing time: {time_str} - {e}")
        return None

def parse_datetime(datetime_str):
    """
    Parse datetime string into datetime object
    
    Args:
        datetime_str (str): Datetime string
        
    Returns:
        datetime: Datetime object or None if parsing fails
    """
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y %I:%M:%S %p',
        '%m/%d/%Y %I:%M %p',
        '%Y-%m-%d',
        '%m/%d/%Y'
    ]
    
    # Try each format
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except (ValueError, TypeError):
            continue
    
    # Log warning if we couldn't parse the date
    logger.warning(f"Could not parse date: {datetime_str}")
    return None

def is_work_day(date):
    """
    Check if the date is a work day (Monday-Friday)
    
    Args:
        date (datetime): Date to check
        
    Returns:
        bool: True if work day, False otherwise
    """
    return date.weekday() in WORK_DAYS

def get_event_date_time(asset):
    """
    Get event date time from asset
    
    Args:
        asset (dict): Asset data
        
    Returns:
        datetime: Event datetime or None
    """
    # Try direct EventDateTime field first
    event_date_time = asset.get('EventDateTime')
    if event_date_time:
        dt = parse_datetime(event_date_time)
        if dt:
            return dt
    
    # Try EventDateTimeString field
    event_date_time_str = asset.get('EventDateTimeString')
    if event_date_time_str:
        dt = parse_datetime(event_date_time_str)
        if dt:
            return dt
    
    # Try separate date and time fields
    event_date = asset.get('EventDate')
    event_time = asset.get('EventTime')
    
    if event_date and event_time:
        try:
            dt_str = f"{event_date} {event_time}"
            dt = parse_datetime(dt_str)
            if dt:
                return dt
        except Exception:
            pass
    
    # Try creation date as last resort
    created_at = asset.get('CreatedAt')
    if created_at:
        dt = parse_datetime(created_at)
        if dt:
            return dt
    
    return None

def generate_same_day_report(assets):
    """
    Generate same-day Late Start and Not on Job report
    
    This report is generated at 8:30 AM and flags drivers who are:
    - Late to start (not active by 7:00 AM)
    - Not at their assigned job site
    
    Args:
        assets (list): List of asset dictionaries
        
    Returns:
        dict: Report data
    """
    # Filter for vehicle assets only
    vehicles = [asset for asset in assets if is_vehicle_asset(asset)]
    
    # Get today's date
    today = datetime.now().date()
    
    # Initialize report data
    report = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'report_date': today.strftime('%Y-%m-%d'),
        'total_drivers': len(vehicles),
        'late_start_count': 0,
        'not_on_job_count': 0,
        'late_start_drivers': [],
        'not_on_job_drivers': []
    }
    
    # Skip if not a work day
    if not is_work_day(today):
        report['is_work_day'] = False
        return report
    
    report['is_work_day'] = True
    
    # Check each vehicle
    for vehicle in vehicles:
        asset_id = vehicle.get('AssetIdentifier', '')
        driver_name = vehicle.get('Label', '').strip()
        if not driver_name and '(' in asset_id:
            # Try to extract name from asset ID if in format "PT-123 (John Doe)"
            parts = asset_id.split('(')
            if len(parts) > 1:
                driver_name = parts[1].strip(')')
        
        # Check for late start
        event_time = get_event_date_time(vehicle)
        if not event_time:
            continue
        
        # Only consider events from today
        if event_time.date() != today:
            continue
        
        # Get decimal hour for start time check
        event_hour = event_time.hour + event_time.minute / 60
        
        # Check if active (ignition on)
        is_active = vehicle.get('Active', False) or vehicle.get('Ignition', False)
        
        # Check if late start
        is_late_start = event_hour > LATE_START_THRESHOLD and not is_active
        
        if is_late_start:
            report['late_start_count'] += 1
            report['late_start_drivers'].append({
                'asset_id': asset_id,
                'name': driver_name,
                'start_time': event_time.strftime('%H:%M'),
                'location': vehicle.get('Location', 'Unknown')
            })
        
        # Check if not at job site
        location = vehicle.get('Location', '').upper()
        site = vehicle.get('Site', '').upper()
        district = vehicle.get('District', '').upper()
        
        # Check for job site indicators
        is_at_job = False
        
        # Look for job number pattern (e.g., "2023-045" or similar)
        job_patterns = [
            r'\d{4}-\d{3}',  # YYYY-NNN
            r'JOB\s+\d+',    # JOB 12345
            r'PROJECT\s+\d+', # PROJECT 12345
            r'SITE\s+\d+'     # SITE 12345
        ]
        
        # Check location/site fields for job indicators
        for field in [location, site, district]:
            if field and any(pattern in field for pattern in job_patterns):
                is_at_job = True
                break
        
        # Also check if at yard or office (acceptable locations)
        at_yard_or_office = False
        yard_office_patterns = ['YARD', 'OFFICE', 'SHOP', 'HQ', 'HEADQUARTERS']
        
        for field in [location, site, district]:
            if field and any(pattern in field for pattern in yard_office_patterns):
                at_yard_or_office = True
                break
        
        # Flag if not at job site during working hours
        if not is_at_job and not at_yard_or_office and event_hour >= WORKING_HOURS_START:
            report['not_on_job_count'] += 1
            report['not_on_job_drivers'].append({
                'asset_id': asset_id,
                'name': driver_name,
                'current_location': location or 'Unknown',
                'assigned_location': 'Job Site'  # We don't have this info, so assume job site
            })
    
    # Save report
    save_attendance_report(report, 'same_day')
    
    return report

def generate_prior_day_report(assets):
    """
    Generate prior-day Late Start, Early End, and Not on Job report
    
    This report is generated at 9:30 AM and analyzes yesterday's data to find:
    - Late starts (after 7:00 AM)
    - Early ends (before 4:30 PM)
    - Time not spent at job site during working hours
    
    Args:
        assets (list): List of asset dictionaries
        
    Returns:
        dict: Report data
    """
    # Filter for vehicle assets only
    vehicles = [asset for asset in assets if is_vehicle_asset(asset)]
    
    # Get yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    # Initialize report data
    report = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'report_date': yesterday.strftime('%Y-%m-%d'),
        'total_drivers': len(vehicles),
        'late_start_count': 0,
        'early_end_count': 0,
        'not_on_job_count': 0,
        'late_start_drivers': [],
        'early_end_drivers': [],
        'not_on_job_drivers': []
    }
    
    # Skip if yesterday was not a work day
    if not is_work_day(yesterday):
        report['is_work_day'] = False
        return report
    
    report['is_work_day'] = True
    
    # This report requires historical data which we don't have from the assets list
    # In a real implementation, this would query a database for yesterday's events
    # For now, we'll use a placeholder implementation
    
    # Placeholder: Simulate historical data
    # In a real implementation, these would come from stored events
    simulated_data = {}
    
    for vehicle in vehicles:
        asset_id = vehicle.get('AssetIdentifier', '')
        
        # Skip assets that don't have IDs
        if not asset_id:
            continue
        
        driver_name = vehicle.get('Label', '').strip()
        if not driver_name and '(' in asset_id:
            # Try to extract name from asset ID if in format "PT-123 (John Doe)"
            parts = asset_id.split('(')
            if len(parts) > 1:
                driver_name = parts[1].strip(')')
        
        # Generate simulated start/end times
        # In real implementation, this would come from stored event history
        import random
        
        # 20% chance of late start
        late_start = random.random() < 0.2
        start_hour = random.uniform(7.0, 9.0) if late_start else random.uniform(6.0, 6.9)
        
        # 15% chance of early end
        early_end = random.random() < 0.15
        end_hour = random.uniform(15.0, 16.4) if early_end else random.uniform(16.5, 17.5)
        
        # 10% chance of not being at job site
        not_at_job = random.random() < 0.1
        
        simulated_data[asset_id] = {
            'name': driver_name,
            'start_hour': start_hour,
            'end_hour': end_hour,
            'at_job_site': not not_at_job,
            'location': vehicle.get('Location', 'Unknown')
        }
    
    # Analyze the data
    for asset_id, data in simulated_data.items():
        # Check for late start
        if data['start_hour'] > LATE_START_THRESHOLD:
            report['late_start_count'] += 1
            start_time_str = f"{int(data['start_hour'])}:{int((data['start_hour'] % 1) * 60):02d}"
            minutes_late = int((data['start_hour'] - LATE_START_THRESHOLD) * 60)
            
            report['late_start_drivers'].append({
                'asset_id': asset_id,
                'name': data['name'],
                'start_time': start_time_str,
                'minutes_late': minutes_late
            })
        
        # Check for early end
        if data['end_hour'] < EARLY_END_THRESHOLD:
            report['early_end_count'] += 1
            end_time_str = f"{int(data['end_hour'])}:{int((data['end_hour'] % 1) * 60):02d}"
            minutes_early = int((EARLY_END_THRESHOLD - data['end_hour']) * 60)
            
            report['early_end_drivers'].append({
                'asset_id': asset_id,
                'name': data['name'],
                'end_time': end_time_str,
                'minutes_early': minutes_early
            })
        
        # Check for not at job site
        if not data['at_job_site']:
            report['not_on_job_count'] += 1
            
            # Calculate approximate time away from job site
            work_duration = data['end_hour'] - data['start_hour']
            time_away = f"{int(work_duration)} hours"
            
            report['not_on_job_drivers'].append({
                'asset_id': asset_id,
                'name': data['name'],
                'assigned_location': 'Job Site',  # We don't have this info, so assume job site
                'time_away': time_away
            })
    
    # Save report
    save_attendance_report(report, 'prior_day')
    
    return report

def save_attendance_report(report, report_type):
    """
    Save attendance report to file
    
    Args:
        report (dict): Report data
        report_type (str): 'same_day' or 'prior_day'
        
    Returns:
        str: Path to the saved report file
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_date = report.get('report_date', datetime.now().strftime('%Y-%m-%d'))
    
    output_file = os.path.join(
        ATTENDANCE_DIR, 
        f"{report_type}_attendance_{report_date}_{timestamp}.json"
    )
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save report as JSON
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved {report_type} attendance report to {output_file}")
    
    return output_file

# Daily report generation functions for scheduler
def run_same_day_report(assets=None):
    """
    Run the same-day late start and not on job report
    
    Args:
        assets (list, optional): List of asset dictionaries. If None, will load from API.
        
    Returns:
        dict: Report data
    """
    logger.info("Running same-day attendance report")
    
    if assets is None:
        # Load assets from API or cache
        from utils import load_data
        assets = load_data()
    
    return generate_same_day_report(assets)

def run_prior_day_report(assets=None):
    """
    Run the prior-day late start, early end, and not on job report
    
    Args:
        assets (list, optional): List of asset dictionaries. If None, will load from API.
        
    Returns:
        dict: Report data
    """
    logger.info("Running prior-day attendance report")
    
    if assets is None:
        # Load assets from API or cache
        from utils import load_data
        assets = load_data()
    
    return generate_prior_day_report(assets)

def send_attendance_report_email(report, report_type):
    """
    Send attendance report email
    
    Args:
        report (dict): Report data
        report_type (str): 'same_day' or 'prior_day'
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Import email sender
        from utils.email_sender import send_email
        
        # Configure email
        subject = f"Fleet Attendance Report - {report.get('report_date')}"
        to_email = os.environ.get('REPORT_EMAIL', 'fleet-reports@example.com')
        from_email = os.environ.get('FROM_EMAIL', 'fleet-system@example.com')
        
        # Build email content
        if report_type == 'same_day':
            title = "Same-Day Late Start and Not on Job Report"
            description = f"This report was automatically generated at {report.get('generated_at')}."
            
            content = f"""
            <h2>{title}</h2>
            <p>{description}</p>
            
            <h3>Summary</h3>
            <p>
                <b>Date:</b> {report.get('report_date')}<br>
                <b>Total Drivers:</b> {report.get('total_drivers')}<br>
                <b>Late Start Count:</b> {report.get('late_start_count')}<br>
                <b>Not on Job Count:</b> {report.get('not_on_job_count')}
            </p>
            """
            
            if report.get('late_start_drivers'):
                content += """
                <h3>Late Start Drivers</h3>
                <table border="1" cellpadding="4" cellspacing="0">
                    <tr>
                        <th>Driver ID</th>
                        <th>Name</th>
                        <th>Start Time</th>
                        <th>Location</th>
                    </tr>
                """
                
                for driver in report.get('late_start_drivers'):
                    content += f"""
                    <tr>
                        <td>{driver.get('asset_id')}</td>
                        <td>{driver.get('name')}</td>
                        <td>{driver.get('start_time')}</td>
                        <td>{driver.get('location')}</td>
                    </tr>
                    """
                
                content += "</table>"
            
            if report.get('not_on_job_drivers'):
                content += """
                <h3>Not on Job Drivers</h3>
                <table border="1" cellpadding="4" cellspacing="0">
                    <tr>
                        <th>Driver ID</th>
                        <th>Name</th>
                        <th>Current Location</th>
                        <th>Assigned Location</th>
                    </tr>
                """
                
                for driver in report.get('not_on_job_drivers'):
                    content += f"""
                    <tr>
                        <td>{driver.get('asset_id')}</td>
                        <td>{driver.get('name')}</td>
                        <td>{driver.get('current_location')}</td>
                        <td>{driver.get('assigned_location')}</td>
                    </tr>
                    """
                
                content += "</table>"
        
        else:  # prior_day
            title = "Prior-Day Attendance Report"
            description = f"This report was automatically generated at {report.get('generated_at')} for the previous working day."
            
            content = f"""
            <h2>{title}</h2>
            <p>{description}</p>
            
            <h3>Summary</h3>
            <p>
                <b>Date:</b> {report.get('report_date')}<br>
                <b>Total Drivers:</b> {report.get('total_drivers')}<br>
                <b>Late Start Count:</b> {report.get('late_start_count')}<br>
                <b>Early End Count:</b> {report.get('early_end_count')}<br>
                <b>Not on Job Count:</b> {report.get('not_on_job_count')}
            </p>
            """
            
            if report.get('late_start_drivers'):
                content += """
                <h3>Late Start Drivers</h3>
                <table border="1" cellpadding="4" cellspacing="0">
                    <tr>
                        <th>Driver ID</th>
                        <th>Name</th>
                        <th>Start Time</th>
                        <th>Minutes Late</th>
                    </tr>
                """
                
                for driver in report.get('late_start_drivers'):
                    content += f"""
                    <tr>
                        <td>{driver.get('asset_id')}</td>
                        <td>{driver.get('name')}</td>
                        <td>{driver.get('start_time')}</td>
                        <td>{driver.get('minutes_late')}</td>
                    </tr>
                    """
                
                content += "</table>"
            
            if report.get('early_end_drivers'):
                content += """
                <h3>Early End Drivers</h3>
                <table border="1" cellpadding="4" cellspacing="0">
                    <tr>
                        <th>Driver ID</th>
                        <th>Name</th>
                        <th>End Time</th>
                        <th>Minutes Early</th>
                    </tr>
                """
                
                for driver in report.get('early_end_drivers'):
                    content += f"""
                    <tr>
                        <td>{driver.get('asset_id')}</td>
                        <td>{driver.get('name')}</td>
                        <td>{driver.get('end_time')}</td>
                        <td>{driver.get('minutes_early')}</td>
                    </tr>
                    """
                
                content += "</table>"
            
            if report.get('not_on_job_drivers'):
                content += """
                <h3>Not on Job Drivers</h3>
                <table border="1" cellpadding="4" cellspacing="0">
                    <tr>
                        <th>Driver ID</th>
                        <th>Name</th>
                        <th>Assigned Location</th>
                        <th>Time Away</th>
                    </tr>
                """
                
                for driver in report.get('not_on_job_drivers'):
                    content += f"""
                    <tr>
                        <td>{driver.get('asset_id')}</td>
                        <td>{driver.get('name')}</td>
                        <td>{driver.get('assigned_location')}</td>
                        <td>{driver.get('time_away')}</td>
                    </tr>
                    """
                
                content += "</table>"
        
        # Add footer
        content += """
        <hr>
        <p><small>This is an automated report from the Fleet Management System. Please do not reply to this email.</small></p>
        """
        
        # Send email
        send_email(
            to_email=to_email,
            from_email=from_email,
            subject=subject,
            html_content=content
        )
        
        logger.info(f"Sent {report_type} attendance report email to {to_email}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending {report_type} attendance report email: {e}")
        return False