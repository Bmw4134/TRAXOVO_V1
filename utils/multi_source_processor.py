"""
TRAXORA | Multi-Source Processor Utility

This module combines data from multiple report sources (TimeOnSite, ActivityDetail, DrivingHistory)
using driver ID and date as join keys to create comprehensive attendance records.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

def combine_attendance_sources(
    time_on_site_data: List[Dict[str, Any]], 
    activity_detail_data: List[Dict[str, Any]], 
    driving_history_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Combine data from multiple sources using driver ID + date as the join key.
    
    Args:
        time_on_site_data: List of processed TimeOnSite records
        activity_detail_data: List of processed ActivityDetail records
        driving_history_data: List of processed DrivingHistory records
        
    Returns:
        List of combined attendance records with data from all sources
    """
    logger.info("Combining attendance data from multiple sources")
    
    # Create a dictionary to store combined records by driver+date key
    combined_records = {}
    
    # Process TimeOnSite data (site presence windows)
    for record in time_on_site_data:
        # Extract driver info and date
        driver_id = normalize_driver_id(record.get('driver_id') or record.get('employee_id') or record.get('driver_name'))
        record_date = extract_date(record)
        
        if not driver_id or not record_date:
            continue
            
        # Create join key
        join_key = f"{driver_id}_{record_date}"
        
        # Initialize combined record if not exists
        if join_key not in combined_records:
            combined_records[join_key] = {
                'driver_id': driver_id,
                'driver_name': record.get('driver_name', ''),
                'date': record_date,
                'job_site': record.get('job_site', ''),
                'job_number': record.get('job_number', ''),
                'time_on_site': {},
                'activity_detail': {},
                'driving_history': {},
                'source_count': 0
            }
            
        # Add TimeOnSite data
        combined_records[join_key]['time_on_site'] = {
            'arrival_time': record.get('arrival_time'),
            'departure_time': record.get('departure_time'),
            'duration': record.get('duration'),
            'site_name': record.get('site_name') or record.get('job_site')
        }
        combined_records[join_key]['source_count'] += 1
    
    # Process ActivityDetail data (movement/activity context)
    for record in activity_detail_data:
        # Extract driver info and date
        driver_id = normalize_driver_id(record.get('driver_id') or record.get('employee_id') or record.get('driver_name'))
        record_date = extract_date(record)
        
        if not driver_id or not record_date:
            continue
            
        # Create join key
        join_key = f"{driver_id}_{record_date}"
        
        # Initialize combined record if not exists
        if join_key not in combined_records:
            combined_records[join_key] = {
                'driver_id': driver_id, 
                'driver_name': record.get('driver_name', ''),
                'date': record_date,
                'job_site': record.get('job_site', ''),
                'job_number': record.get('job_number', ''),
                'time_on_site': {},
                'activity_detail': {},
                'driving_history': {},
                'source_count': 0
            }
            
        # Add ActivityDetail data
        combined_records[join_key]['activity_detail'] = {
            'event_type': record.get('event_type'),
            'activity': record.get('activity'),
            'start_time': record.get('start_time'),
            'end_time': record.get('end_time'),
            'location': record.get('location') or record.get('job_site')
        }
        combined_records[join_key]['source_count'] += 1
    
    # Process DrivingHistory data (arrive/depart sequence)
    for record in driving_history_data:
        # Extract driver info and date
        driver_id = normalize_driver_id(record.get('driver_id') or record.get('employee_id') or record.get('driver_name'))
        record_date = extract_date(record)
        
        if not driver_id or not record_date:
            continue
            
        # Create join key
        join_key = f"{driver_id}_{record_date}"
        
        # Initialize combined record if not exists
        if join_key not in combined_records:
            combined_records[join_key] = {
                'driver_id': driver_id,
                'driver_name': record.get('driver_name', ''),
                'date': record_date,
                'job_site': record.get('job_site', ''),
                'job_number': record.get('job_number', ''),
                'time_on_site': {},
                'activity_detail': {},
                'driving_history': {},
                'source_count': 0
            }
            
        # Add DrivingHistory data
        combined_records[join_key]['driving_history'] = {
            'first_start': record.get('first_start'),
            'last_stop': record.get('last_stop'),
            'total_driving': record.get('total_driving'),
            'trip_count': record.get('trip_count'),
            'start_location': record.get('start_location'),
            'end_location': record.get('end_location')
        }
        combined_records[join_key]['source_count'] += 1
    
    # Consolidate and enhance records with cross-validation
    consolidated_records = []
    for join_key, record in combined_records.items():
        # Get the most accurate job site name across sources
        job_site = get_best_job_site_name(record)
        if job_site:
            record['job_site'] = job_site
            
        # Get the most accurate driver name across sources
        driver_name = get_best_driver_name(record)
        if driver_name:
            record['driver_name'] = driver_name
            
        # Add classification based on combined data
        record['classification'] = classify_attendance(record)
        
        # Add additional flags for verification
        record['has_time_on_site'] = bool(record['time_on_site'].get('arrival_time'))
        record['has_activity'] = bool(record['activity_detail'].get('event_type'))
        record['has_driving'] = bool(record['driving_history'].get('first_start'))
        
        # Add record to consolidated list
        consolidated_records.append(record)
    
    logger.info(f"Combined {len(consolidated_records)} attendance records from multiple sources")
    return consolidated_records

def normalize_driver_id(driver_id: Optional[str]) -> Optional[str]:
    """Normalize driver ID for consistent matching"""
    if not driver_id:
        return None
        
    # Strip whitespace and convert to lowercase
    driver_id = str(driver_id).strip().lower()
    
    # Remove common prefixes/suffixes
    driver_id = driver_id.replace('driver:', '').replace('id:', '')
    
    return driver_id

def extract_date(record: Dict[str, Any]) -> Optional[str]:
    """Extract date string from record in YYYY-MM-DD format"""
    # Check for explicit date field
    if 'date' in record:
        date_val = record['date']
        if isinstance(date_val, str):
            # Try to parse and standardize the date
            try:
                date_obj = datetime.strptime(date_val, '%Y-%m-%d')
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                try:
                    # Try alternate format MM/DD/YYYY
                    date_obj = datetime.strptime(date_val, '%m/%d/%Y')
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    pass
    
    # Try to extract from timestamp fields
    for field in ['arrival_time', 'start_time', 'timestamp', 'first_start']:
        if field in record and record[field]:
            try:
                date_str = str(record[field])
                if 'T' in date_str:
                    # ISO format with time
                    date_obj = datetime.fromisoformat(date_str.split('T')[0])
                    return date_obj.strftime('%Y-%m-%d')
                elif ' ' in date_str:
                    # Date with time
                    date_part = date_str.split(' ')[0]
                    if '-' in date_part:
                        # YYYY-MM-DD
                        return date_part
                    elif '/' in date_part:
                        # MM/DD/YYYY
                        date_obj = datetime.strptime(date_part, '%m/%d/%Y')
                        return date_obj.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                continue
    
    return None

def get_best_job_site_name(record: Dict[str, Any]) -> Optional[str]:
    """Get the most accurate job site name from all sources"""
    # Collect all possible job site names from different sources
    job_sites = []
    
    # From the main record
    if record.get('job_site'):
        job_sites.append(record['job_site'])
    
    # From time_on_site data
    if record['time_on_site'].get('site_name'):
        job_sites.append(record['time_on_site']['site_name'])
    
    # From activity_detail data
    if record['activity_detail'].get('location'):
        job_sites.append(record['activity_detail']['location'])
    
    # From driving_history data
    if record['driving_history'].get('end_location'):
        job_sites.append(record['driving_history']['end_location'])
    
    # Return the longest non-empty job site name (likely the most specific)
    valid_sites = [site for site in job_sites if site and len(str(site)) > 0]
    if valid_sites:
        return max(valid_sites, key=len)
    
    return None

def get_best_driver_name(record: Dict[str, Any]) -> Optional[str]:
    """Get the most accurate driver name from all sources"""
    # Use the existing driver name if available
    if record.get('driver_name'):
        return record['driver_name']
    
    # No other source has better driver name information
    return None

def classify_attendance(record: Dict[str, Any]) -> str:
    """
    Classify attendance based on combined data from all sources
    Uses strict rules for classification with verification across sources
    """
    # No data from any source
    if record['source_count'] == 0:
        return 'Unknown'
    
    # Check for time on site data (most reliable for attendance)
    if record['has_time_on_site']:
        arrival_time = record['time_on_site'].get('arrival_time')
        departure_time = record['time_on_site'].get('departure_time')
        
        # Validate with driving history if available
        if record['has_driving']:
            first_start = record['driving_history'].get('first_start')
            
            # Late arrival (arrived after 7:00 AM)
            if arrival_time and isinstance(arrival_time, str) and 'T' in arrival_time:
                time_part = arrival_time.split('T')[1]
                if time_part > '07:00:00':
                    return 'Late'
        
        # Early departure (left before 3:30 PM)
        if departure_time and isinstance(departure_time, str) and 'T' in departure_time:
            time_part = departure_time.split('T')[1]
            if time_part < '15:30:00':
                return 'Early End'
        
        # On time (has time on site and no late/early flags)
        return 'On Time'
    
    # No time on site data but has driving history
    elif record['has_driving']:
        # Check driving times for attendance classification
        first_start = record['driving_history'].get('first_start')
        last_stop = record['driving_history'].get('last_stop')
        
        # No actual driving detected
        if not first_start or not last_stop:
            return 'No Show'
        
        # Some driving but incomplete day
        return 'Partial'
    
    # Has activity but no time on site or driving
    elif record['has_activity']:
        event_type = record['activity_detail'].get('event_type')
        
        # Check if any meaningful activity was recorded
        if event_type and event_type.lower() not in ['idle', 'inactive', 'off duty']:
            return 'Activity Only'
        
        return 'Inactive'
    
    # No meaningful data found
    return 'Unknown'