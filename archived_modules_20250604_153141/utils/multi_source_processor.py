"""
Multi-Source Processor Module

This module provides functionality for processing and combining data from multiple sources
to create a unified dataset for the driver attendance report.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz, process

# Configure logging
logger = logging.getLogger(__name__)

def combine_attendance_sources(driving_history=None, time_on_site=None, activity_detail=None):
    """
    Combine data from multiple sources.
    
    Args:
        driving_history: Driving history data
        time_on_site: Time on site data
        activity_detail: Activity detail data
        
    Returns:
        list: Combined data
    """
    combined_data = []
    
    # Process driving history
    if driving_history:
        for record in driving_history:
            processed_record = process_driving_history_record(record)
            if processed_record:
                combined_data.append(processed_record)
    
    # Process time on site
    if time_on_site:
        for record in time_on_site:
            processed_record = process_time_on_site_record(record)
            if processed_record:
                combined_data.append(processed_record)
    
    # Process activity detail
    if activity_detail:
        for record in activity_detail:
            processed_record = process_activity_detail_record(record)
            if processed_record:
                combined_data.append(processed_record)
    
    # Merge records for the same driver
    merged_data = merge_driver_records(combined_data)
    
    return merged_data

def process_driving_history_record(record):
    """
    Process a driving history record.
    
    Args:
        record: The record to process
        
    Returns:
        dict: Processed record or None if invalid
    """
    try:
        # Check if this is a valid record
        required_fields = []
        
        # For Gauge API data
        if ('Driver' in record or 'driver' in record or 'driver_name' in record or 'DriverName' in record):
            # Extract driver name
            driver_name = None
            for field in ['Driver', 'driver', 'driver_name', 'DriverName']:
                if field in record and record[field]:
                    driver_name = record[field]
                    break
            
            if not driver_name:
                return None
            
            # Extract timestamp
            timestamp = None
            for field in ['timestamp', 'Timestamp', 'event_time', 'EventTime', 'time', 'Time']:
                if field in record and record[field]:
                    timestamp = record[field]
                    break
            
            if not timestamp:
                return None
            
            # Parse timestamp
            if isinstance(timestamp, str):
                try:
                    # Try different formats
                    formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%m/%d/%Y %H:%M:%S',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%dT%H:%M:%S.%f'
                    ]
                    
                    parsed_time = None
                    for fmt in formats:
                        try:
                            parsed_time = datetime.strptime(timestamp, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if not parsed_time:
                        return None
                    
                    timestamp = parsed_time
                except Exception:
                    return None
            elif not isinstance(timestamp, datetime):
                return None
            
            # Extract location
            location = None
            for field in ['location', 'Location', 'address', 'Address', 'place', 'Place']:
                if field in record and record[field]:
                    location = record[field]
                    break
            
            # Extract event type
            event_type = None
            for field in ['event_type', 'EventType', 'event', 'Event', 'action', 'Action']:
                if field in record and record[field]:
                    event_type = record[field]
                    break
            
            # Create processed record
            processed_record = {
                'source': 'driving_history',
                'driver_name': driver_name,
                'timestamp': timestamp,
                'location': location,
                'event_type': event_type
            }
            
            # Extract additional fields
            for field in record:
                if field not in processed_record and record[field] is not None:
                    processed_record[field] = record[field]
            
            return processed_record
        
        return None
    
    except Exception as e:
        logger.error(f"Error processing driving history record: {str(e)}")
        return None

def process_time_on_site_record(record):
    """
    Process a time on site record.
    
    Args:
        record: The record to process
        
    Returns:
        dict: Processed record or None if invalid
    """
    try:
        # Check if this is a valid record
        required_fields = []
        
        # For Gauge API data
        if ('Asset' in record or 'asset' in record or 'asset_id' in record or 'AssetID' in record):
            # Extract asset information
            asset_id = None
            for field in ['Asset', 'asset', 'asset_id', 'AssetID', 'id', 'ID']:
                if field in record and record[field]:
                    asset_id = record[field]
                    break
            
            if not asset_id:
                return None
            
            # Extract asset name
            asset_name = None
            for field in ['asset_name', 'AssetName', 'name', 'Name', 'asset_description', 'AssetDescription']:
                if field in record and record[field]:
                    asset_name = record[field]
                    break
            
            # Extract driver information
            driver_name = None
            for field in ['driver', 'Driver', 'operator', 'Operator', 'driver_name', 'DriverName']:
                if field in record and record[field]:
                    driver_name = record[field]
                    break
            
            # Extract on time and off time
            on_time = None
            off_time = None
            
            for field in ['on_time', 'OnTime', 'start_time', 'StartTime', 'arrival_time', 'ArrivalTime']:
                if field in record and record[field]:
                    on_time = record[field]
                    break
            
            for field in ['off_time', 'OffTime', 'end_time', 'EndTime', 'departure_time', 'DepartureTime']:
                if field in record and record[field]:
                    off_time = record[field]
                    break
            
            # Extract job site information
            job_site = None
            for field in ['job_site', 'JobSite', 'site', 'Site', 'location', 'Location']:
                if field in record and record[field]:
                    job_site = record[field]
                    break
            
            # Extract job number
            job_number = None
            for field in ['job_number', 'JobNumber', 'job_id', 'JobID', 'job', 'Job']:
                if field in record and record[field]:
                    job_number = record[field]
                    break
            
            # Create processed record
            processed_record = {
                'source': 'time_on_site',
                'asset_id': asset_id,
                'asset_name': asset_name,
                'driver_name': driver_name,
                'start_time': on_time,
                'end_time': off_time,
                'job_site': job_site,
                'job_number': job_number,
                'location': job_site
            }
            
            # Extract additional fields
            for field in record:
                if field not in processed_record and record[field] is not None:
                    processed_record[field] = record[field]
            
            return processed_record
        
        return None
    
    except Exception as e:
        logger.error(f"Error processing time on site record: {str(e)}")
        return None

def process_activity_detail_record(record):
    """
    Process an activity detail record.
    
    Args:
        record: The record to process
        
    Returns:
        dict: Processed record or None if invalid
    """
    try:
        # Check if this is a valid record
        required_fields = []
        
        # For Gauge API data
        if ('Activity' in record or 'activity' in record or 'activity_id' in record or 'ActivityID' in record):
            # Extract activity information
            activity_id = None
            for field in ['Activity', 'activity', 'activity_id', 'ActivityID', 'id', 'ID']:
                if field in record and record[field]:
                    activity_id = record[field]
                    break
            
            if not activity_id:
                return None
            
            # Extract asset information
            asset_id = None
            for field in ['asset_id', 'AssetID', 'asset', 'Asset']:
                if field in record and record[field]:
                    asset_id = record[field]
                    break
            
            # Extract driver information
            driver_name = None
            for field in ['driver', 'Driver', 'operator', 'Operator', 'driver_name', 'DriverName']:
                if field in record and record[field]:
                    driver_name = record[field]
                    break
            
            # Extract timestamp
            timestamp = None
            for field in ['timestamp', 'Timestamp', 'time', 'Time', 'date', 'Date']:
                if field in record and record[field]:
                    timestamp = record[field]
                    break
            
            # Extract location
            location = None
            for field in ['location', 'Location', 'address', 'Address', 'place', 'Place']:
                if field in record and record[field]:
                    location = record[field]
                    break
            
            # Extract job site information
            job_site = None
            for field in ['job_site', 'JobSite', 'site', 'Site']:
                if field in record and record[field]:
                    job_site = record[field]
                    break
            
            # Create processed record
            processed_record = {
                'source': 'activity_detail',
                'activity_id': activity_id,
                'asset_id': asset_id,
                'driver_name': driver_name,
                'timestamp': timestamp,
                'location': location or job_site
            }
            
            # Extract additional fields
            for field in record:
                if field not in processed_record and record[field] is not None:
                    processed_record[field] = record[field]
            
            return processed_record
        
        return None
    
    except Exception as e:
        logger.error(f"Error processing activity detail record: {str(e)}")
        return None

def merge_driver_records(records):
    """
    Merge records for the same driver.
    
    Args:
        records: List of records
        
    Returns:
        list: Merged records
    """
    # Create a map of driver names to records
    driver_records = {}
    
    for record in records:
        # Skip records without driver name
        if not record.get('driver_name'):
            continue
        
        # Normalize driver name for consistent matching
        driver_name = normalize_driver_name(record['driver_name'])
        
        # If this driver already has records, merge the new record
        if driver_name in driver_records:
            driver_records[driver_name].append(record)
        else:
            driver_records[driver_name] = [record]
    
    # Process each driver's records
    merged_records = []
    
    for driver_name, driver_data in driver_records.items():
        # Sort records by timestamp
        driver_data.sort(key=lambda x: x.get('timestamp') if isinstance(x.get('timestamp'), datetime) else datetime.min)
        
        # Create a merged record
        merged_record = {
            'driver_name': driver_name,
            'sources': [record.get('source') for record in driver_data],
            'locations': []
        }
        
        # Process time-related fields
        start_times = []
        end_times = []
        timestamps = []
        
        for record in driver_data:
            # Collect start times
            if record.get('start_time'):
                if isinstance(record['start_time'], datetime):
                    start_times.append(record['start_time'])
                elif isinstance(record['start_time'], str):
                    try:
                        # Try to parse the time string
                        parsed_time = datetime.strptime(record['start_time'], '%H:%M:%S')
                        start_times.append(parsed_time)
                    except ValueError:
                        try:
                            parsed_time = datetime.strptime(record['start_time'], '%H:%M')
                            start_times.append(parsed_time)
                        except ValueError:
                            pass
            
            # Collect end times
            if record.get('end_time'):
                if isinstance(record['end_time'], datetime):
                    end_times.append(record['end_time'])
                elif isinstance(record['end_time'], str):
                    try:
                        # Try to parse the time string
                        parsed_time = datetime.strptime(record['end_time'], '%H:%M:%S')
                        end_times.append(parsed_time)
                    except ValueError:
                        try:
                            parsed_time = datetime.strptime(record['end_time'], '%H:%M')
                            end_times.append(parsed_time)
                        except ValueError:
                            pass
            
            # Collect timestamps
            if record.get('timestamp') and isinstance(record['timestamp'], datetime):
                timestamps.append(record['timestamp'])
            
            # Collect locations
            if record.get('location') and record['location'] not in merged_record['locations']:
                merged_record['locations'].append(record['location'])
            
            # Copy other fields if not already set
            for field, value in record.items():
                if field not in ['driver_name', 'source', 'sources', 'timestamp', 'start_time', 'end_time', 'location', 'locations'] and value is not None:
                    if field not in merged_record:
                        merged_record[field] = value
        
        # Determine start and end times
        if start_times:
            # Use the earliest start time
            merged_record['start_time'] = min(start_times).strftime('%H:%M:%S')
        elif timestamps:
            # Use the earliest timestamp as start time
            merged_record['start_time'] = min(timestamps).strftime('%H:%M:%S')
        
        if end_times:
            # Use the latest end time
            merged_record['end_time'] = max(end_times).strftime('%H:%M:%S')
        elif timestamps:
            # Use the latest timestamp as end time
            merged_record['end_time'] = max(timestamps).strftime('%H:%M:%S')
        
        # Add the merged record
        merged_records.append(merged_record)
    
    return merged_records

def normalize_driver_name(name):
    """
    Normalize driver name for consistent matching.
    
    Args:
        name: Driver name
        
    Returns:
        str: Normalized name
    """
    if not name:
        return ''
    
    # Convert to string
    name = str(name).strip()
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove common titles
    titles = ['mr.', 'mrs.', 'ms.', 'miss', 'dr.', 'prof.']
    for title in titles:
        if name.startswith(title + ' '):
            name = name[len(title) + 1:]
    
    # Remove special characters and double spaces
    name = ''.join(c for c in name if c.isalnum() or c.isspace())
    name = ' '.join(name.split())
    
    return name.strip()

def get_closest_driver_match(target_name, driver_list, threshold=80):
    """
    Get the closest driver name match from a list.
    
    Args:
        target_name: Target driver name
        driver_list: List of driver names
        threshold: Matching threshold (0-100)
        
    Returns:
        str: Closest match or None if no match above threshold
    """
    if not target_name or not driver_list:
        return None
    
    # Normalize target name
    target_name = normalize_driver_name(target_name)
    
    # Normalize driver list
    normalized_list = [normalize_driver_name(name) for name in driver_list]
    
    # Find the closest match
    if target_name in normalized_list:
        # Exact match
        index = normalized_list.index(target_name)
        return driver_list[index]
    else:
        # Fuzzy match
        match, score = process.extractOne(target_name, normalized_list)
        
        if score >= threshold:
            index = normalized_list.index(match)
            return driver_list[index]
    
    return None

def get_closest_location_match(target_location, location_list, threshold=80):
    """
    Get the closest location match from a list.
    
    Args:
        target_location: Target location
        location_list: List of locations
        threshold: Matching threshold (0-100)
        
    Returns:
        str: Closest match or None if no match above threshold
    """
    if not target_location or not location_list:
        return None
    
    # Normalize target location
    target_location = str(target_location).lower().strip()
    
    # Normalize location list
    normalized_list = [str(loc).lower().strip() for loc in location_list]
    
    # Find the closest match
    if target_location in normalized_list:
        # Exact match
        index = normalized_list.index(target_location)
        return location_list[index]
    else:
        # Fuzzy match
        match, score = process.extractOne(target_location, normalized_list)
        
        if score >= threshold:
            index = normalized_list.index(match)
            return location_list[index]
    
    return None