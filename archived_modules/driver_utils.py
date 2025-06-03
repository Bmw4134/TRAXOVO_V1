"""
Driver Utilities Module

This module contains utility functions for working with driver data,
particularly for extracting and formatting driver information from asset labels.
"""

import os
import re
import sys
import logging
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
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
    if not label:
        return ""
    
    # Convert to string if needed
    label = str(label).strip()
    
    # Try to match common vehicle/equipment ID patterns
    for pattern in config.EQUIPMENT_PATTERNS + config.VEHICLE_PATTERNS:
        match = re.search(pattern, label, re.IGNORECASE)
        if match:
            # Extract everything after the match
            start_idx = match.end()
            driver_name = label[start_idx:].strip()
            
            # Remove any leading separators
            driver_name = re.sub(r'^[\s\-_]+', '', driver_name)
            
            return driver_name
    
    # If no pattern matched, try some heuristics
    # Look for pattern of letters followed by digits, then assume driver name follows
    match = re.search(r'[A-Za-z]+[\-\s]?\d+', label)
    if match:
        start_idx = match.end()
        driver_name = label[start_idx:].strip()
        driver_name = re.sub(r'^[\s\-_]+', '', driver_name)
        return driver_name
    
    # If all else fails, and there's a space, assume first part is asset and rest is driver
    if ' ' in label:
        parts = label.split(' ', 1)
        return parts[1].strip()
    
    return ""

def clean_asset_info(label):
    """
    Extract just the asset ID from a label
    
    Args:
        label (str): Asset label string
        
    Returns:
        str: Asset ID or empty string if not found
    """
    if not label:
        return ""
    
    # Convert to string if needed
    label = str(label).strip()
    
    # Try to match common vehicle/equipment ID patterns
    for pattern in config.EQUIPMENT_PATTERNS + config.VEHICLE_PATTERNS:
        match = re.search(pattern, label, re.IGNORECASE)
        if match:
            asset_id = match.group(0).strip()
            return asset_id
    
    # If no pattern matched, try some heuristics
    # Look for pattern of letters followed by digits
    match = re.search(r'[A-Za-z]+[\-\s]?\d+', label)
    if match:
        return match.group(0).strip()
    
    # If all else fails, and there's a space, assume first part is asset
    if ' ' in label:
        parts = label.split(' ', 1)
        return parts[0].strip()
    
    # If we couldn't extract anything, just return the original
    return label

def normalize_driver_name(name):
    """
    Normalize a driver name to a standard format
    
    Args:
        name (str): Driver name string
        
    Returns:
        str: Normalized driver name
    """
    if not name:
        return ""
    
    # Convert to string and strip whitespace
    name = str(name).strip()
    
    # Remove any employee IDs in parentheses
    name = re.sub(r'\s*\([^)]*\)\s*', ' ', name)
    
    # Remove any employee IDs after dash
    name = re.sub(r'\s*-\s*[A-Z0-9]+\s*$', '', name)
    
    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Convert to title case
    name = name.title()
    
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
        return ""
    
    # Normalize the driver name
    driver_name = normalize_driver_name(driver_name)
    
    # If asset ID is provided, include it
    if asset_id:
        return f"{driver_name} ({asset_id})"
    
    return driver_name

def is_vehicle_id(text):
    """
    Check if the given text matches a vehicle ID pattern
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text matches vehicle ID pattern, False otherwise
    """
    if not text:
        return False
    
    # Check against vehicle patterns
    for pattern in config.VEHICLE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
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
    
    # If pattern ends with a wildcard, do a prefix match
    if pattern.endswith('*'):
        prefix = pattern[:-1]
        return asset_id.upper().startswith(prefix.upper())
    
    # Otherwise, do an exact match
    return asset_id.upper() == pattern.upper()