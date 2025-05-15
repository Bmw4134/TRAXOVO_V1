import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def load_data(file_path):
    """
    Load asset data from a JSON file
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        list: List of asset dictionaries
    """
    try:
        # Try to get data from our API module first
        try:
            from gauge_api import get_asset_data
            logger.info("Attempting to load data from Gauge API")
            api_data = get_asset_data()
            if api_data:
                logger.info(f"Successfully loaded {len(api_data)} assets from Gauge API")
                data = api_data
                # Generate reports from the fresh data
                try:
                    from reports_processor import generate_reports
                    generate_reports(data)
                except Exception as report_error:
                    logger.warning(f"Could not generate reports: {report_error}")
            else:
                # Fallback to file if API fails
                logger.warning("API data fetch failed, falling back to file")
                with open(file_path, 'r') as f:
                    data = json.load(f)
        except Exception as api_error:
            # Fallback to file if API module fails
            logger.warning(f"API module error: {api_error}. Falling back to file.")
            with open(file_path, 'r') as f:
                data = json.load(f)
        
        # Clean and pre-process data
        for asset in data:
            # Ensure all required fields exist
            if 'AssetIdentifier' not in asset:
                asset['AssetIdentifier'] = asset.get('Label', 'Unknown').split(' ')[0]
            
            # Format event datetime if available
            if 'EventDateTimeString' in asset:
                try:
                    dt_str = asset['EventDateTimeString']
                    if dt_str:
                        # Parse datetime in the format "MM/DD/YYYY HH:MM:SS AM/PM CT"
                        dt_parts = dt_str.split(' ')
                        date_part = dt_parts[0]
                        time_part = dt_parts[1]
                        am_pm = dt_parts[2]
                        
                        # Create a more standardized format for the template
                        if len(dt_parts) >= 3:
                            date_obj = datetime.strptime(f"{date_part} {time_part} {am_pm}", "%m/%d/%Y %I:%M:%S %p")
                            asset['FormattedDateTime'] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        asset['FormattedDateTime'] = "No date available"
                except Exception as e:
                    logger.warning(f"Could not parse datetime for asset {asset.get('AssetIdentifier', 'Unknown')}: {e}")
                    asset['FormattedDateTime'] = asset.get('EventDateTimeString', 'No date available')
        
        # Save the processed data to a cache file for quick loading
        # Create data directory if it doesn't exist
        data_dir = 'data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Save to cache file
        cache_file = os.path.join(data_dir, 'processed_data.json')
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved processed data to cache file: {cache_file}")
        except Exception as e:
            logger.warning(f"Could not save to cache file: {e}")
        
        return data
    except Exception as e:
        logger.error(f"Error loading data file {file_path}: {e}")
        raise

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
    filtered = assets.copy()
    
    # Filter by status
    if status == 'active':
        filtered = [asset for asset in filtered if asset.get('Active', False)]
    elif status == 'inactive':
        filtered = [asset for asset in filtered if not asset.get('Active', False)]
    
    # Filter by category
    if category != 'all':
        filtered = [asset for asset in filtered if asset.get('AssetCategory') == category]
    
    # Filter by location
    if location != 'all':
        filtered = [asset for asset in filtered if asset.get('Location') == location]
    
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
        if 'AssetCategory' in asset and asset['AssetCategory']:
            categories.add(asset['AssetCategory'])
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
        if 'Location' in asset and asset['Location']:
            locations.add(asset['Location'])
    return sorted(list(locations))

def get_asset_status(assets):
    """
    Get counts of active and inactive assets
    
    Args:
        assets (list): List of asset dictionaries
        
    Returns:
        dict: Dictionary with active and inactive counts
    """
    active = len([a for a in assets if a.get('Active', False)])
    inactive = len([a for a in assets if not a.get('Active', False)])
    return {'active': active, 'inactive': inactive}
