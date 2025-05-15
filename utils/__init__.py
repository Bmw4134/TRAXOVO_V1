"""
Utility functions for the application
"""

import os
import json
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

def load_data(file_path):
    """
    Load asset data from a JSON file
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        list: List of asset dictionaries
    """
    logger.info(f"Loading data from {file_path}")
    
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Successfully loaded {len(data)} items from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {e}")
        return []

def filter_assets(assets, status='all', category='all', location='all'):
    """
    Filter assets based on status, category, and location
    
    Args:
        assets (list): List of asset dictionaries
        status (str): 'active', 'inactive', or 'all'
        category (str): Asset category or 'all'
        location (str): Asset location or 'all'
        
    Returns:
        list: Filtered list of asset dictionaries
    """
    filtered = assets
    
    # Filter by status
    if status != 'all':
        is_active = status == 'active'
        filtered = [a for a in filtered if a.get('Active', False) == is_active]
    
    # Filter by category
    if category != 'all':
        filtered = [a for a in filtered if a.get('AssetCategory') == category]
    
    # Filter by location
    if location != 'all':
        filtered = [a for a in filtered if a.get('Location') == location]
    
    return filtered

def get_asset_by_id(assets, asset_id):
    """
    Get a specific asset by its identifier
    
    Args:
        assets (list): List of asset dictionaries
        asset_id (str): Asset identifier to find
        
    Returns:
        dict: Asset dictionary or None if not found
    """
    for asset in assets:
        if asset.get('AssetIdentifier') == asset_id:
            return asset
    return None

def get_asset_categories(assets):
    """
    Get a unique list of asset categories
    
    Args:
        assets (list): List of asset dictionaries
        
    Returns:
        list: Unique list of asset categories
    """
    categories = set()
    for asset in assets:
        category = asset.get('AssetCategory')
        if category:
            categories.add(category)
    return sorted(list(categories))

def get_asset_locations(assets):
    """
    Get a unique list of asset locations
    
    Args:
        assets (list): List of asset dictionaries
        
    Returns:
        list: Unique list of asset locations
    """
    locations = set()
    for asset in assets:
        location = asset.get('Location')
        if location:
            locations.add(location)
    return sorted(list(locations))

def get_asset_status(assets):
    """
    Get counts of active and inactive assets
    
    Args:
        assets (list): List of asset dictionaries
        
    Returns:
        dict: Dictionary with active and inactive counts
    """
    active = sum(1 for a in assets if a.get('Active', False))
    inactive = len(assets) - active
    return {
        'active': active,
        'inactive': inactive
    }

def sync_assets_with_database(assets_data):
    """
    Synchronize assets data with the database
    
    Args:
        assets_data (list): List of asset dictionaries
        
    Returns:
        tuple: (success_count, error_count, message)
    """
    if not assets_data:
        return 0, 0, "No assets data provided"
    
    try:
        from models import db, Asset
        
        success_count = 0
        error_count = 0
        
        # Process in batches of 50 to avoid memory issues
        batch_size = 50
        total_batches = (len(assets_data) + batch_size - 1) // batch_size
        
        for batch_index in range(total_batches):
            start_idx = batch_index * batch_size
            end_idx = min(start_idx + batch_size, len(assets_data))
            batch = assets_data[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_index + 1} of {total_batches}")
            
            for asset_data in batch:
                try:
                    Asset.from_json(asset_data)
                    success_count += 1
                    logger.info(f"Updated asset: {asset_data.get('AssetIdentifier', 'Unknown')}")
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error updating asset {asset_data.get('AssetIdentifier', 'Unknown')}: {e}")
            
            # Commit batch
            db.session.commit()
            logger.info(f"Batch {batch_index + 1} processed: {success_count} successes, {error_count} errors")
        
        return success_count, error_count, f"Synchronized {success_count} assets with {error_count} errors"
    except Exception as e:
        logger.error(f"Error synchronizing assets with database: {e}")
        return 0, 0, f"Error: {str(e)}"