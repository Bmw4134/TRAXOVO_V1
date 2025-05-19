"""
Driver Utilities Module

This module contains utility functions for working with driver data,
particularly for extracting and formatting driver information from asset labels.
"""

import re
import logging
from config import VEHICLE_PREFIXES, EQUIPMENT_PREFIXES

# Configure logger
logger = logging.getLogger(__name__)

def extract_driver_from_label(label):
    """
    Extract driver name from an asset label
    
    Asset labels are typically in format: 
    "ET-01 MATTHEW C. SHAYLOR" or "RAM-2500 JOHN DOE"
    This function extracts just the driver name portion.
    
    Args:
        label (str): Asset label string
        
    Returns:
        str: Driver name or empty string if not found
    """
    if not label or not isinstance(label, str):
        return ""
    
    # Clean up the label
    label = label.strip().upper()
    
    # Try to find pattern with vehicle prefix (e.g., "ET-01 DRIVER NAME")
    for prefix in VEHICLE_PREFIXES:
        if prefix in label:
            parts = label.split(prefix, 1)
            if len(parts) > 1:
                # Find the ID part (number after prefix)
                id_part_match = re.search(r'^\d+', parts[1].strip())
                if id_part_match:
                    id_part = id_part_match.group(0)
                    # Everything after the ID is the driver name
                    driver_part = parts[1][len(id_part):].strip()
                    return driver_part
    
    # Try standard pattern (vehicle identifier followed by driver name)
    # Look for common separators between vehicle ID and driver name
    separators = [' ', '-', '_', ':', '|']
    for separator in separators:
        if separator in label:
            parts = label.split(separator, 1)
            # Check if first part looks like a vehicle ID (contains number or is short)
            if (any(c.isdigit() for c in parts[0]) or len(parts[0]) <= 8) and len(parts[1].strip()) > 0:
                return parts[1].strip()
    
    # If no clear separator found, try to split on the first whitespace after a number
    match = re.search(r'\d+\s+([A-Z\s\.]+)$', label)
    if match:
        return match.group(1).strip()
    
    # If all else fails and the label is long enough, assume the whole thing is a driver name
    if len(label) > 10 and ' ' in label:
        return label
    
    # No driver name found
    return ""

def clean_asset_info(label):
    """
    Extract just the asset ID from a label
    
    Args:
        label (str): Asset label string
        
    Returns:
        str: Asset ID or empty string if not found
    """
    if not label or not isinstance(label, str):
        return ""
    
    # Clean up the label
    label = label.strip().upper()
    
    # Look for standard vehicle prefixes
    for prefix in VEHICLE_PREFIXES + EQUIPMENT_PREFIXES:
        if prefix in label:
            # Extract the part with the prefix and any numbers that follow
            match = re.search(f'{prefix}\\d+', label)
            if match:
                return match.group(0)
    
    # Look for common vehicle patterns like "RAM-2500" or "F-150"
    vehicle_patterns = [
        r'RAM-\d+',
        r'F-\d+',
        r'FORD\s+F\d+',
        r'CHEVY\s+\w+',
        r'GMC\s+\w+',
        r'DODGE\s+\w+'
    ]
    
    for pattern in vehicle_patterns:
        match = re.search(pattern, label)
        if match:
            return match.group(0)
    
    # If no standard pattern found, take everything before the first space
    # (assuming the format is "ASSET_ID DRIVER_NAME")
    if ' ' in label:
        return label.split(' ', 1)[0]
    
    # If all else fails, return the whole label as the asset ID
    return label

def normalize_driver_name(name):
    """
    Normalize a driver name to a standard format
    
    Args:
        name (str): Driver name string
        
    Returns:
        str: Normalized driver name
    """
    if not name or not isinstance(name, str):
        return ""
    
    # Remove excess whitespace
    name = " ".join(name.strip().split())
    
    # Convert to title case (first letter of each word capitalized)
    name = name.title()
    
    # Fix common name formatting issues
    
    # Properly handle "Mc" and "Mac" prefixes in last names
    name = re.sub(r'Mc(\w)', lambda x: f'Mc{x.group(1).upper()}', name)
    name = re.sub(r'Mac(\w)', lambda x: f'Mac{x.group(1).upper()}', name)
    
    # Properly handle hyphenated names
    name = re.sub(r'-(\w)', lambda x: f'-{x.group(1).upper()}', name)
    
    # Properly handle apostrophes in names like O'Brien
    name = re.sub(r'\'(\w)', lambda x: f"'{x.group(1).lower()}", name)
    
    # Handle name suffixes (Jr, Sr, III)
    suffixes = ['Jr', 'Sr', 'Ii', 'Iii', 'Iv', 'V']
    for suffix in suffixes:
        if f' {suffix}' in name:
            name = name.replace(f' {suffix}', f' {suffix.upper()}')
            if f' {suffix.upper()}.' not in name and f' {suffix.upper()}' in name:
                name = name.replace(f' {suffix.upper()}', f' {suffix.upper()}.')
    
    return name

def format_driver_display(driver_name, asset_id=None):
    """
    Format driver info for display
    
    Args:
        driver_name (str): Driver name
        asset_id (str): Asset ID
        
    Returns:
        str: Formatted driver display string
    """
    if not driver_name:
        if asset_id:
            return f"{asset_id} (No Driver)"
        else:
            return "Unknown Driver"
    
    driver_name = normalize_driver_name(driver_name)
    
    if asset_id:
        return f"{driver_name} ({asset_id})"
    else:
        return driver_name

def is_vehicle_id(text):
    """
    Check if the given text matches a vehicle ID pattern
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text matches vehicle ID pattern, False otherwise
    """
    if not text or not isinstance(text, str):
        return False
    
    text = text.strip().upper()
    
    # Check for standard vehicle prefixes
    for prefix in VEHICLE_PREFIXES:
        if text.startswith(prefix) and len(text) > len(prefix) and text[len(prefix):].strip().isdigit():
            return True
    
    # Check for common vehicle patterns
    vehicle_patterns = [
        r'^RAM-\d+$',
        r'^F-\d+$',
        r'^FORD\s+F\d+$',
        r'^[A-Z]+-\d+$',  # Generic pattern for things like "CT-01"
    ]
    
    for pattern in vehicle_patterns:
        if re.match(pattern, text):
            return True
    
    return False

def match_asset_pattern(asset_id, pattern):
    """
    Check if an asset ID matches a pattern (for filtering)
    
    Args:
        asset_id (str): Asset ID to check
        pattern (str): Pattern to match against
        
    Returns:
        bool: True if asset_id matches pattern, False otherwise
    """
    if not asset_id or not pattern:
        return False
    
    # Clean and normalize
    asset_id = asset_id.strip().upper()
    pattern = pattern.strip().upper()
    
    # Exact match
    if asset_id == pattern:
        return True
    
    # Prefix match (e.g., "ET-" matches all ET vehicles)
    if pattern.endswith('-') and asset_id.startswith(pattern):
        return True
    
    # Pattern with wildcard (e.g., "ET-*" matches all ET vehicles)
    if pattern.endswith('*'):
        base_pattern = pattern[:-1]
        return asset_id.startswith(base_pattern)
    
    # Check if asset ID contains the pattern
    return pattern in asset_id