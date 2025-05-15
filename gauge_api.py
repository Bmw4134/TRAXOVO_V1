"""
Gauge API Integration Module

This module handles all interactions with the Gauge API to fetch asset data.
It automatically fetches and updates the data file used by the application.
"""
import os
import json
import logging
import requests
import traceback
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Configuration from environment variables
GAUGE_API_URL = os.environ.get('GAUGE_API_URL', 'https://api.gaugegps.com/v1/')
GAUGE_API_USERNAME = os.environ.get('GAUGE_API_USERNAME', '')
GAUGE_API_PASSWORD = os.environ.get('GAUGE_API_PASSWORD', '')

# Data file paths
DATA_DIR = 'data'
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)
    
DATA_FILE = os.path.join(DATA_DIR, 'gauge_api_data.json')
LAST_UPDATE_FILE = os.path.join(DATA_DIR, 'last_api_update.json')


def get_auth_token():
    """
    Get authentication token from Gauge API.
    
    Returns:
        str: Authentication token or None if authentication fails
    """
    if not GAUGE_API_KEY and (not GAUGE_API_USER or not GAUGE_API_PASSWORD):
        logger.error("No API authentication credentials provided")
        return None
    
    # Try API key authentication first if available
    if GAUGE_API_KEY:
        return GAUGE_API_KEY
    
    # Fall back to user/password authentication
    try:
        auth_url = f"{GAUGE_API_URL}auth/login"
        payload = {
            "username": GAUGE_API_USER,
            "password": GAUGE_API_PASSWORD
        }
        response = requests.post(auth_url, json=payload)
        response.raise_for_status()
        auth_data = response.json()
        return auth_data.get('token')
    except requests.exceptions.RequestException as e:
        logger.error(f"Authentication failed: {e}")
        return None


def fetch_asset_data():
    """
    Fetch asset data from Gauge API.
    
    Returns:
        list: List of asset dictionaries or empty list if fetch fails
    """
    token = get_auth_token()
    if not token:
        logger.error("Could not obtain authentication token")
        return []
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Endpoint for fetching all assets
        assets_url = f"{GAUGE_API_URL}assets"
        response = requests.get(assets_url, headers=headers)
        response.raise_for_status()
        
        assets = response.json()
        logger.info(f"Successfully fetched {len(assets)} assets from Gauge API")
        return assets
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch asset data: {e}")
        return []


def save_asset_data(assets):
    """
    Save asset data to a JSON file.
    
    Args:
        assets (list): List of asset dictionaries
    
    Returns:
        bool: True if save was successful, False otherwise
    """
    if not assets:
        logger.warning("No asset data to save")
        return False
    
    try:
        # Add a timestamp to the data
        data_with_timestamp = {
            "timestamp": datetime.now().isoformat(),
            "asset_count": len(assets),
            "assets": assets
        }
        
        with open(DATA_FILE, 'w') as f:
            json.dump(assets, f, indent=2)
        
        logger.info(f"Saved {len(assets)} assets to {DATA_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save asset data: {e}")
        return False


def load_cached_data():
    """
    Load asset data from the cached JSON file.
    
    Returns:
        list: List of asset dictionaries or empty list if load fails
    """
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                assets = json.load(f)
            logger.info(f"Loaded {len(assets)} assets from cache")
            return assets
        else:
            logger.warning("No cached data file found")
            return []
    except Exception as e:
        logger.error(f"Failed to load cached data: {e}")
        return []


def update_asset_data(force=False):
    """
    Update asset data by fetching from API and saving to file.
    Will only fetch if the cached data is older than 1 hour or force=True.
    
    Args:
        force (bool): Force update regardless of cache age
    
    Returns:
        list: Updated list of asset dictionaries
    """
    # Check if we need to update the cache
    update_needed = force
    
    if not update_needed and os.path.exists(DATA_FILE):
        # Check file modification time
        mtime = os.path.getmtime(DATA_FILE)
        file_age = datetime.now().timestamp() - mtime
        
        # Update if file is older than 1 hour (3600 seconds)
        if file_age > 3600:
            update_needed = True
    else:
        # No file exists, so we need to update
        update_needed = True
    
    if update_needed:
        logger.info("Fetching fresh data from Gauge API")
        assets = fetch_asset_data()
        if assets:
            save_asset_data(assets)
            return assets
    
    # Either we didn't need to update or the update failed
    return load_cached_data()


def get_asset_data(use_db=True):
    """
    Main function to get asset data, attempting to update from API first.
    
    Args:
        use_db (bool): Whether to try to get data from the database
    
    Returns:
        list: List of asset dictionaries
    """
    # Try to get from database if requested
    if use_db:
        try:
            from app import app
            from models import Asset
            
            with app.app_context():
                assets_from_db = Asset.query.all()
                if assets_from_db and len(assets_from_db) > 0:
                    logger.info(f"Loaded {len(assets_from_db)} assets from database")
                    # Convert DB models to dictionaries
                    assets = []
                    for asset in assets_from_db:
                        asset_dict = {
                            'AssetIdentifier': asset.asset_identifier,
                            'Label': asset.label,
                            'AssetCategory': asset.asset_category,
                            'AssetClass': asset.asset_class,
                            'AssetMake': asset.asset_make,
                            'AssetModel': asset.asset_model,
                            'SerialNumber': asset.serial_number,
                            'DeviceSerialNumber': asset.device_serial_number,
                            'Active': asset.active,
                            'DaysInactive': asset.days_inactive,
                            'Ignition': asset.ignition,
                            'Latitude': asset.latitude,
                            'Longitude': asset.longitude,
                            'Location': asset.location,
                            'Site': asset.site,
                            'District': asset.district,
                            'SubDistrict': asset.sub_district,
                            'Engine1Hours': asset.engine_hours,
                            'Odometer': asset.odometer,
                            'Speed': asset.speed,
                            'SpeedLimit': asset.speed_limit,
                            'Heading': asset.heading,
                            'BackupBatteryPct': asset.backup_battery_pct,
                            'Voltage': asset.voltage,
                            'IMEI': asset.imei,
                            'EventDateTimeString': asset.event_date_time_string,
                            'Reason': asset.reason,
                            'TimeZone': asset.time_zone,
                            'FormattedDateTime': asset.formatted_date_time
                        }
                        assets.append(asset_dict)
                    return assets
                else:
                    logger.info("No assets found in database, fetching from API")
        except Exception as e:
            logger.error(f"Failed to load data from database: {e}")
    
    # Try to update from API first
    assets = update_asset_data()
    
    # If API fetch failed and we have no cached data, use the attached assets file as fallback
    if not assets:
        logger.warning("Using attached assets file as fallback")
        try:
            with open('attached_assets/GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
                assets = json.load(f)
            logger.info(f"Loaded {len(assets)} assets from attached file")
            
            # Sync with database
            try:
                from app import app
                from utils import sync_assets_with_database
                
                with app.app_context():
                    success, errors, message = sync_assets_with_database(assets)
                    logger.info(message)
            except Exception as e:
                logger.error(f"Failed to sync with database: {e}")
                
        except Exception as e:
            logger.error(f"Failed to load attached assets file: {e}")
            assets = []
    else:
        # If we got assets from API, sync with database
        try:
            from app import app
            from utils import sync_assets_with_database
            
            with app.app_context():
                success, errors, message = sync_assets_with_database(assets)
                logger.info(message)
        except Exception as e:
            logger.error(f"Failed to sync with database: {e}")
    
    return assets


# Execute this if the script is run directly
if __name__ == "__main__":
    print(f"Gauge API URL: {GAUGE_API_URL}")
    print("Updating asset data...")
    assets = update_asset_data(force=True)
    print(f"Retrieved {len(assets)} assets")