"""
Driver Utilities Module

This module contains utility functions for working with driver data,
particularly for extracting and formatting driver information from asset labels.
"""

import logging
import re

# Configure logging
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
        
    # Trim leading/trailing whitespace
    label = label.strip()
    
    # Common patterns for asset IDs
    asset_patterns = [
        r'^(ET-\d+)',      # Equipment truck (ET-01)
        r'^(PT-\d+)',      # Pickup truck (PT-01)
        r'^(RAM-\d+)',     # RAM truck
        r'^(FORD-\d+)',    # FORD truck
        r'^(LT-\d+)',      # Light truck
        r'^(HT-\d+)',      # Heavy truck
        r'^(A-\d+)',       # Asset with A prefix
        r'^(\d+-\w+)',     # Numeric asset ID
        r'^(RENTAL)',      # Rental vehicle
        r'^(YCO-\d+)'      # YCO-prefix assets
    ]
    
    # Try to match each pattern
    for pattern in asset_patterns:
        match = re.search(pattern, label)
        if match:
            # Extract the asset ID
            asset_id = match.group(1)
            
            # Get the driver name by removing the asset ID
            driver_name = label.replace(asset_id, '').strip()
            return driver_name
    
    # If no pattern matches, use a simple heuristic:
    # If there are digits followed by a space, take what comes after
    match = re.search(r'^\S+\s+(.+)$', label)
    if match:
        return match.group(1).strip()
    
    # No pattern matched, return original label
    # This is a fallback for when we can't identify the asset pattern
    return label

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
        
    # Trim leading/trailing whitespace
    label = label.strip()
    
    # Common patterns for asset IDs
    asset_patterns = [
        r'^(ET-\d+)',      # Equipment truck (ET-01)
        r'^(PT-\d+)',      # Pickup truck (PT-01)
        r'^(RAM-\d+)',     # RAM truck
        r'^(FORD-\d+)',    # FORD truck
        r'^(LT-\d+)',      # Light truck
        r'^(HT-\d+)',      # Heavy truck
        r'^(A-\d+)',       # Asset with A prefix
        r'^(\d+-\w+)',     # Numeric asset ID
        r'^(RENTAL)',      # Rental vehicle
        r'^(YCO-\d+)'      # YCO-prefix assets
    ]
    
    # Try to match each pattern
    for pattern in asset_patterns:
        match = re.search(pattern, label)
        if match:
            return match.group(1).strip()
    
    # If no pattern matches, use first "word" as asset ID
    parts = label.split(' ', 1)
    if len(parts) > 0:
        return parts[0].strip()
    
    # No asset ID found
    return ""

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
        
    # Convert to uppercase
    name = name.strip().upper()
    
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)
    
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
        return asset_id or "Unknown"
        
    if asset_id:
        return f"{driver_name} ({asset_id})"
    else:
        return driver_name