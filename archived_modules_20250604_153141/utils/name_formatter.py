"""
Name and Data Formatting Utilities for TRAXOVO

This module cleans up raw data display for field crews,
converting technical JSON data into user-friendly formats.
"""
import re
import logging

logger = logging.getLogger(__name__)

def clean_driver_name(raw_name):
    """
    Clean up driver names from technical formats to user-friendly display
    
    Examples:
    'MATTHEW C. SHAYLOR JEEP WRANGLER 2024 Pickup Truck' -> 'Matthew Shaylor'
    'AMMAR I. ELHAMAD FORD F150 2024 Personal Vehicle' -> 'Ammar Elhamad'
    """
    if not raw_name:
        return "Unknown Driver"
    
    # Remove vehicle information and clean up
    name = raw_name.upper()
    
    # Common vehicle types to remove
    vehicle_types = [
        'JEEP WRANGLER', 'FORD F150', 'PICKUP TRUCK', 'PERSONAL VEHICLE',
        'COMPANY VEHICLE', 'WORK TRUCK', 'SERVICE VEHICLE', 'UTILITY TRUCK',
        'JEEP', 'FORD', 'CHEVY', 'TOYOTA', 'DODGE', 'RAM', 'GMC'
    ]
    
    # Remove years (2020-2030)
    name = re.sub(r'\b20[2-3][0-9]\b', '', name)
    
    # Remove vehicle types
    for vehicle_type in vehicle_types:
        name = name.replace(vehicle_type, '')
    
    # Remove extra descriptors
    descriptors = ['PICKUP', 'TRUCK', 'VEHICLE', 'CAR', 'VAN', 'SUV']
    for desc in descriptors:
        name = name.replace(desc, '')
    
    # Clean up multiple spaces and strip
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Convert to title case and handle middle initials
    parts = name.split()
    clean_parts = []
    
    for part in parts:
        if len(part) == 2 and part.endswith('.'):
            # Skip middle initials for cleaner display
            continue
        elif len(part) > 1:
            clean_parts.append(part.capitalize())
    
    # Return first and last name only
    if len(clean_parts) >= 2:
        return f"{clean_parts[0]} {clean_parts[-1]}"
    elif len(clean_parts) == 1:
        return clean_parts[0].capitalize()
    else:
        return "Unknown Driver"

def clean_asset_name(raw_asset_name):
    """
    Clean up asset names for mobile display
    
    Examples:
    '#210003 - MATTHEW C. SHAYLOR JEEP' -> 'Jeep #210003'
    '#210013 - Asset Description' -> 'Asset #210013'
    """
    if not raw_asset_name:
        return "Unknown Asset"
    
    # Extract asset number
    asset_match = re.search(r'#?(\d+)', raw_asset_name)
    asset_num = asset_match.group(1) if asset_match else "???"
    
    # Extract vehicle type
    upper_name = raw_asset_name.upper()
    
    vehicle_types = {
        'JEEP': 'Jeep',
        'FORD': 'Ford',
        'F150': 'F-150',
        'WRANGLER': 'Wrangler',
        'PICKUP': 'Pickup',
        'TRUCK': 'Truck',
        'CRANE': 'Crane',
        'EXCAVATOR': 'Excavator',
        'DOZER': 'Dozer',
        'LOADER': 'Loader'
    }
    
    for key, display_name in vehicle_types.items():
        if key in upper_name:
            return f"{display_name} #{asset_num}"
    
    return f"Asset #{asset_num}"

def format_attendance_status(status_data):
    """
    Convert raw attendance JSON to clean status display
    """
    if not status_data or not isinstance(status_data, dict):
        return {
            'status': 'unknown',
            'display': 'Unknown',
            'icon': '❓',
            'color': '#6c757d'
        }
    
    # Map technical status to user-friendly display
    status_map = {
        'present': {'display': 'On Site', 'icon': '✅', 'color': '#28a745'},
        'late': {'display': 'Late', 'icon': '⏰', 'color': '#ffc107'},
        'absent': {'display': 'Absent', 'icon': '❌', 'color': '#dc3545'},
        'early_departure': {'display': 'Left Early', 'icon': '🏃', 'color': '#fd7e14'},
        'not_on_job': {'display': 'Not on Job', 'icon': '📍', 'color': '#6f42c1'},
        'timecard_only': {'display': 'Timecard Only', 'icon': '📝', 'color': '#17a2b8'},
        'gps_only': {'display': 'GPS Only', 'icon': '🛰️', 'color': '#20c997'}
    }
    
    raw_status = status_data.get('status', 'unknown').lower()
    
    if raw_status in status_map:
        result = status_map[raw_status].copy()
        result['status'] = raw_status
        return result
    else:
        return {
            'status': 'unknown',
            'display': 'Unknown',
            'icon': '❓',
            'color': '#6c757d'
        }

def format_time_readable(time_str):
    """
    Convert technical time formats to readable display
    """
    if not time_str:
        return "Not recorded"
    
    try:
        from datetime import datetime
        # Handle various time formats
        if 'T' in time_str:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(time_str, '%H:%M:%S')
        
        return dt.strftime('%I:%M %p')
    except:
        return str(time_str)

def simplify_job_description(raw_description):
    """
    Simplify job descriptions for mobile display
    """
    if not raw_description:
        return "General Work"
    
    # Remove excessive technical details
    desc = raw_description.strip()
    
    # Common job type mappings
    job_types = {
        'CONSTRUCTION': 'Construction',
        'EXCAVATION': 'Excavation', 
        'ROAD WORK': 'Road Work',
        'SITE PREP': 'Site Prep',
        'UTILITY': 'Utility Work',
        'MAINTENANCE': 'Maintenance',
        'TRANSPORT': 'Transport'
    }
    
    upper_desc = desc.upper()
    for key, display in job_types.items():
        if key in upper_desc:
            return display
    
    # Truncate if too long
    if len(desc) > 30:
        return desc[:27] + "..."
    
    return desc.title()