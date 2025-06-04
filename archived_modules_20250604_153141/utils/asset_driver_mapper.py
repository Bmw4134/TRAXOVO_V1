"""
Asset Driver Mapper Utility

This utility provides functions to map asset identifiers to drivers using 
the Secondary Asset Identifier from the asset list report. This ensures
consistent driver identification across all reports and data sources.
"""

import os
import pandas as pd
import re
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Cache for holding asset-driver mappings to avoid repeated file loading
_asset_driver_cache = None
_last_file_timestamp = None

def _extract_employee_id(secondary_id):
    """
    Extract employee ID from Secondary Asset Identifier format.
    Example: "210013 - Shaylor, Matthew C" -> "210013"
    
    Args:
        secondary_id (str): Secondary Asset Identifier
        
    Returns:
        str: Employee ID or None if not found
    """
    if not secondary_id or pd.isna(secondary_id):
        return None
        
    # Look for pattern: numbers followed by space, dash, space
    match = re.match(r'^(\d+)\s*-\s*', str(secondary_id))
    if match:
        return match.group(1)
    
    return None

def _extract_employee_name(secondary_id):
    """
    Extract employee name from Secondary Asset Identifier format.
    Example: "210013 - Shaylor, Matthew C" -> "Shaylor, Matthew C"
    
    Args:
        secondary_id (str): Secondary Asset Identifier
        
    Returns:
        str: Employee name or None if not found
    """
    if not secondary_id or pd.isna(secondary_id):
        return None
        
    # Look for pattern: numbers, dash, then capture the name
    match = re.match(r'^\d+\s*-\s*(.*)', str(secondary_id))
    if match:
        return match.group(1).strip()
    
    return None

def _load_asset_driver_mapping(force_reload=False):
    """
    Load the asset to driver mapping from the asset list export file.
    
    Args:
        force_reload (bool): Force reload from file even if cached
        
    Returns:
        dict: Dictionary mapping asset identifiers to driver information
    """
    global _asset_driver_cache, _last_file_timestamp
    
    # Try to find the latest assets list export file
    assets_dir = os.path.join(os.getcwd(), 'attached_assets')
    assets_file = os.path.join(assets_dir, 'AssetsListExport.xlsx')
    
    if not os.path.exists(assets_file):
        logger.warning(f"Assets list file not found: {assets_file}")
        return {}
    
    # Check if we need to reload the file
    current_timestamp = os.path.getmtime(assets_file)
    if (_asset_driver_cache is None or force_reload or 
            _last_file_timestamp is None or current_timestamp > _last_file_timestamp):
        try:
            logger.info(f"Loading asset-driver mapping from {assets_file}")
            df = pd.read_excel(assets_file)
            
            # Create mapping dictionary
            mapping = {}
            for _, row in df.iterrows():
                asset_id = row.get('Asset Identifier')
                secondary_id = row.get('Secondary Asset Identifier')
                
                if not asset_id or pd.isna(asset_id):
                    continue
                    
                # Extract employee ID and name
                employee_id = _extract_employee_id(secondary_id)
                employee_name = _extract_employee_name(secondary_id)
                
                mapping[str(asset_id).strip()] = {
                    'employee_id': employee_id,
                    'employee_name': employee_name,
                    'secondary_id': secondary_id,
                    'asset_type': row.get('Type'),
                    'asset_make': row.get('Make'),
                    'asset_model': row.get('Model')
                }
            
            _asset_driver_cache = mapping
            _last_file_timestamp = current_timestamp
            logger.info(f"Loaded {len(mapping)} asset-driver mappings")
            
        except Exception as e:
            logger.error(f"Error loading asset driver mapping: {str(e)}")
            return {}
    
    return _asset_driver_cache

def get_driver_for_asset(asset_id):
    """
    Get driver information for a given asset ID.
    
    Args:
        asset_id (str): Asset identifier
        
    Returns:
        dict: Dictionary with driver information or None if not found
    """
    mapping = _load_asset_driver_mapping()
    
    if not asset_id:
        return None
        
    # Try different formats of the asset ID
    cleaned_id = str(asset_id).strip()
    if cleaned_id.startswith('#'):
        alt_id = cleaned_id[1:]
    else:
        alt_id = f"#{cleaned_id}"
        
    # Check both formats
    for id_format in [cleaned_id, alt_id]:
        if id_format in mapping:
            return mapping[id_format]
    
    # If not found by direct lookup, try fuzzy matching
    for mapped_id, info in mapping.items():
        if cleaned_id in mapped_id or mapped_id in cleaned_id:
            return info
            
    return None

def get_asset_for_driver(employee_id):
    """
    Get asset information for a given employee ID.
    
    Args:
        employee_id (str): Employee ID
        
    Returns:
        dict: Dictionary with asset information or None if not found
    """
    mapping = _load_asset_driver_mapping()
    
    # Look for the employee ID in the mapping values
    for asset_id, info in mapping.items():
        if info.get('employee_id') == str(employee_id).strip():
            return {
                'asset_id': asset_id,
                'asset_type': info.get('asset_type'),
                'asset_make': info.get('asset_make'),
                'asset_model': info.get('asset_model')
            }
            
    return None

def get_all_mapped_drivers():
    """
    Get a list of all drivers that have mapped assets.
    
    Returns:
        list: List of dictionaries with driver information
    """
    mapping = _load_asset_driver_mapping()
    
    drivers = []
    for asset_id, info in mapping.items():
        if info.get('employee_id'):
            drivers.append({
                'asset_id': asset_id,
                'employee_id': info.get('employee_id'),
                'employee_name': info.get('employee_name'),
                'asset_type': info.get('asset_type'),
                'asset_make': info.get('asset_make'),
                'asset_model': info.get('asset_model')
            })
            
    return drivers

def refresh_mapping():
    """
    Force refresh the asset-driver mapping from the file.
    
    Returns:
        int: Number of mappings loaded
    """
    mapping = _load_asset_driver_mapping(force_reload=True)
    return len(mapping)