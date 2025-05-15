"""
Gauge API Integration Module

This module handles all interactions with the Gauge API to fetch asset data.
It automatically fetches and updates the data file used by the application.
"""
import os
import json
import time
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
    # Check if we have the required credentials
    if not GAUGE_API_USERNAME or not GAUGE_API_PASSWORD:
        logger.error("No API authentication credentials provided")
        return None
    
    try:
        # GaugeSmart API may have different access patterns
        # Let's first check if direct access to assets is possible with the API key
        
        # Try direct access first if we have a simple API key
        if GAUGE_API_URL.lower().find('assetlist') > -1:
            logger.info(f"API URL contains 'AssetList', attempting direct asset access with API key")
            # This appears to be a direct asset feed URL, return the API key/username as the "token"
            return GAUGE_API_USERNAME
            
        # Fall back to standard auth flow if direct access pattern isn't detected
        
        # Clean up and standardize API URL
        api_url = GAUGE_API_URL
        if api_url.endswith('/'):
            api_url = api_url[:-1]
            
        # Add protocol if missing
        if not api_url.startswith('http'):
            api_url = 'https://' + api_url
        
        # Try various common authentication endpoint patterns
        auth_endpoints = [
            f"{api_url}/auth/login",
            f"{api_url}/api/auth/login",
            f"{api_url}/api/authenticate",
            f"{api_url}/authenticate"
        ]
        
        # Try each potential auth endpoint
        for auth_endpoint in auth_endpoints:
            logger.info(f"Attempting authentication at: {auth_endpoint}")
            
            try:
                payload = {
                    "username": GAUGE_API_USERNAME,
                    "password": GAUGE_API_PASSWORD
                }
                
                # Disable SSL verification to handle self-signed certificates
                # Note: In production, proper SSL certificates should be used
                response = requests.post(auth_endpoint, json=payload, timeout=30, verify=False)
                
                if response.status_code == 200:
                    try:
                        auth_data = response.json()
                        token = auth_data.get('token')
                        if token:
                            logger.info("Successfully obtained authentication token")
                            return token
                        else:
                            logger.warning(f"Token not found in response from {auth_endpoint}")
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON response from {auth_endpoint}: {response.text[:100]}...")
                else:
                    logger.warning(f"Auth failed at {auth_endpoint}: {response.status_code}")
            except requests.RequestException as e:
                logger.warning(f"Request error with {auth_endpoint}: {e}")
            
            # Continue to next endpoint if this one failed
        
        # If we got here, all endpoints failed
        logger.error("All authentication endpoints failed")
        return None
            
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        logger.debug(traceback.format_exc())
        return None


def fetch_asset_data(retries=3, retry_delay=5):
    """
    Fetch asset data from Gauge API with retry logic.
    
    Args:
        retries (int): Number of retry attempts
        retry_delay (int): Delay in seconds between retries
    
    Returns:
        list: List of asset dictionaries or empty list if fetch fails
    """
    # Get authentication token or API key 
    token = get_auth_token()
    if not token:
        logger.error("Could not obtain authentication token or API key")
        return []
    
    # Check if we're dealing with a direct AssetList URL
    if GAUGE_API_URL.lower().find('assetlist') > -1:
        # This is a direct data feed URL, use it as is
        api_url = GAUGE_API_URL
        
        # Clean up URL if needed
        if api_url.endswith('/'):
            api_url = api_url[:-1]
            
        # Add protocol if missing
        if not api_url.startswith('http'):
            api_url = 'https://' + api_url
            
        logger.info(f"Using direct asset feed URL: {api_url}")
        
        # Attempt to fetch with retries
        attempt = 0
        while attempt < retries:
            try:
                # For direct asset feed, we may not need headers
                response = requests.get(api_url, timeout=60, verify=False)
                
                if response.status_code == 200:
                    try:
                        assets = response.json()
                        if isinstance(assets, list):
                            logger.info(f"Successfully fetched {len(assets)} assets from direct feed")
                            return assets
                        elif isinstance(assets, dict) and 'assets' in assets:
                            # Some APIs nest the assets array in an object
                            asset_list = assets['assets']
                            logger.info(f"Successfully fetched {len(asset_list)} assets from direct feed (nested format)")
                            return asset_list
                        else:
                            logger.error(f"Unexpected response format from direct feed: {type(assets)}")
                            logger.debug(f"Response content: {response.text[:500]}...")
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON response from direct feed: {response.text[:500]}...")
                else:
                    logger.error(f"Failed to fetch from direct feed: {response.status_code}")
            except requests.RequestException as e:
                logger.error(f"Request error from direct feed: {e}")
            except Exception as e:
                logger.error(f"Unexpected error fetching from direct feed: {e}")
                logger.debug(traceback.format_exc())
            
            # Increment attempt counter and delay before retry
            attempt += 1
            if attempt < retries:
                logger.info(f"Retrying direct feed fetch in {retry_delay} seconds (attempt {attempt+1}/{retries})")
                time.sleep(retry_delay)
        
        logger.error(f"Failed to fetch assets from direct feed after {retries} attempts")
        return []
        
    # Standard API flow for non-direct URLs
    # Clean up and standardize API URL
    api_url = GAUGE_API_URL
    if api_url.endswith('/'):
        api_url = api_url[:-1]
        
    # Add protocol if missing
    if not api_url.startswith('http'):
        api_url = 'https://' + api_url
    
    # Try various common asset endpoints
    asset_endpoints = [
        f"{api_url}/assets",
        f"{api_url}/api/assets",
        f"{api_url}/api/v1/assets",
        f"{api_url}/v1/assets"
    ]
    
    # Attempt to fetch with retries from each endpoint
    for assets_endpoint in asset_endpoints:
        logger.info(f"Trying to fetch assets from: {assets_endpoint}")
        
        attempt = 0
        while attempt < retries:
            try:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                response = requests.get(assets_endpoint, headers=headers, timeout=60, verify=False)
                
                if response.status_code == 200:
                    try:
                        assets = response.json()
                        if isinstance(assets, list):
                            logger.info(f"Successfully fetched {len(assets)} assets from Gauge API")
                            return assets
                        elif isinstance(assets, dict) and 'assets' in assets:
                            # Some APIs nest the assets array in an object
                            asset_list = assets['assets']
                            logger.info(f"Successfully fetched {len(asset_list)} assets from Gauge API (nested format)")
                            return asset_list
                        else:
                            logger.warning(f"Unexpected response format from {assets_endpoint}: {type(assets)}")
                            logger.debug(f"Response content: {response.text[:500]}...")
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON response from {assets_endpoint}: {response.text[:500]}...")
                else:
                    logger.warning(f"Failed to fetch assets from {assets_endpoint}: {response.status_code}")
                    # If unauthorized, try to get a new token
                    if response.status_code == 401:
                        logger.info("Auth token expired, attempting to get a new one")
                        token = get_auth_token()
                        if not token:
                            logger.error("Could not obtain new authentication token")
                            break  # Try next endpoint
                        # Continue to next attempt with new token
                
            except requests.RequestException as e:
                logger.warning(f"Request error when fetching from {assets_endpoint}: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error when fetching from {assets_endpoint}: {e}")
                logger.debug(traceback.format_exc())
            
            # Increment attempt counter and delay before retry
            attempt += 1
            if attempt < retries:
                logger.info(f"Retrying {assets_endpoint} fetch in {retry_delay}s (attempt {attempt+1}/{retries})")
                time.sleep(retry_delay)
        
        # If we reach here, this endpoint failed - try the next one
    
    # If we get here, all endpoints failed
    logger.error("Failed to fetch assets from any API endpoint")
    return []


def save_asset_data(assets, create_backup=True):
    """
    Save asset data to a JSON file and optionally create a backup.
    
    Args:
        assets (list): List of asset dictionaries
        create_backup (bool): Whether to create a backup of the previous data
    
    Returns:
        bool: True if save was successful, False otherwise
    """
    if not assets:
        logger.warning("No asset data to save")
        return False
    
    try:
        # Create backup of existing file if requested
        if create_backup and os.path.exists(DATA_FILE):
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = os.path.join(BACKUP_DIR, f'gauge_data_backup_{timestamp}.json')
                
                with open(DATA_FILE, 'r') as src, open(backup_file, 'w') as dst:
                    data = json.load(src)
                    json.dump(data, dst, indent=2)
                
                logger.info(f"Created backup of previous data at {backup_file}")
                
                # Keep only the 10 most recent backups
                backups = sorted([os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) 
                                 if f.startswith('gauge_data_backup_')])
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        os.remove(old_backup)
                        logger.info(f"Removed old backup: {old_backup}")
                
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
                # Continue with saving new data even if backup fails
        
        # Add a timestamp and metadata to the data
        data_with_timestamp = {
            "timestamp": datetime.now().isoformat(),
            "asset_count": len(assets),
            "data_source": "Gauge API",
            "source_url": GAUGE_API_URL,
            "assets": assets
        }
        
        # First save to a temporary file to avoid corruption
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(data_with_timestamp, f, indent=2)
        
        # If temporary save was successful, replace the main file
        os.replace(temp_file, DATA_FILE)
        
        # Record the update time separately
        update_info = {
            "last_update": datetime.now().isoformat(),
            "asset_count": len(assets),
            "status": "success"
        }
        with open(LAST_UPDATE_FILE, 'w') as f:
            json.dump(update_info, f, indent=2)
        
        logger.info(f"Successfully saved {len(assets)} assets to {DATA_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save asset data: {e}")
        logger.debug(traceback.format_exc())
        
        # Record the failed update
        try:
            update_info = {
                "last_attempt": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            }
            with open(LAST_UPDATE_FILE, 'w') as f:
                json.dump(update_info, f, indent=2)
        except Exception:
            pass  # Ignore errors when saving error info
            
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
                data = json.load(f)
            
            # Check if the data is in the new format (with metadata)
            if isinstance(data, dict) and 'assets' in data:
                assets = data['assets']
                timestamp = data.get('timestamp', 'unknown')
                logger.info(f"Loaded {len(assets)} assets from cache (timestamp: {timestamp})")
                return assets
            # Old format (direct list of assets)
            elif isinstance(data, list):
                logger.info(f"Loaded {len(data)} assets from cache (old format)")
                return data
            else:
                logger.warning(f"Unexpected data format in cache file: {type(data)}")
                return []
                
        else:
            logger.warning("No cached data file found")
            
            # Try to find a backup file if no primary file
            backups = sorted([os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) 
                             if f.startswith('gauge_data_backup_')], reverse=True)
            
            if backups:
                latest_backup = backups[0]
                logger.info(f"Attempting to load from latest backup: {latest_backup}")
                
                try:
                    with open(latest_backup, 'r') as f:
                        backup_data = json.load(f)
                    
                    if isinstance(backup_data, dict) and 'assets' in backup_data:
                        assets = backup_data['assets']
                        logger.info(f"Loaded {len(assets)} assets from backup file")
                        return assets
                    elif isinstance(backup_data, list):
                        logger.info(f"Loaded {len(backup_data)} assets from backup file (old format)")
                        return backup_data
                    else:
                        logger.warning(f"Unexpected data format in backup file: {type(backup_data)}")
                except Exception as e:
                    logger.error(f"Failed to load from backup: {e}")
            
            return []
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in cached data file: {e}")
        
        # Try to recover from a backup
        try:
            backups = sorted([os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) 
                             if f.startswith('gauge_data_backup_')], reverse=True)
            
            if backups:
                latest_backup = backups[0]
                logger.info(f"Attempting to recover from backup: {latest_backup}")
                
                with open(latest_backup, 'r') as f:
                    backup_data = json.load(f)
                
                if isinstance(backup_data, dict) and 'assets' in backup_data:
                    assets = backup_data['assets']
                    logger.info(f"Recovered {len(assets)} assets from backup file")
                    return assets
                elif isinstance(backup_data, list):
                    logger.info(f"Recovered {len(backup_data)} assets from backup file (old format)")
                    return backup_data
        except Exception as recover_e:
            logger.error(f"Failed to recover from backup: {recover_e}")
            
        return []
        
    except Exception as e:
        logger.error(f"Failed to load cached data: {e}")
        logger.debug(traceback.format_exc())
        return []


def update_asset_data(force=False, max_age_hours=1):
    """
    Update asset data by fetching from API and saving to file.
    Will only fetch if the cached data is older than max_age_hours or force=True.
    
    Args:
        force (bool): Force update regardless of cache age
        max_age_hours (int): Maximum age of cached data in hours before update is needed
    
    Returns:
        list: Updated list of asset dictionaries
    """
    # Check if we need to update the cache
    update_needed = force
    last_update_time = None
    
    # Check the last update file first (more reliable)
    if not update_needed and os.path.exists(LAST_UPDATE_FILE):
        try:
            with open(LAST_UPDATE_FILE, 'r') as f:
                update_info = json.load(f)
                if 'last_update' in update_info:
                    last_update_time = datetime.fromisoformat(update_info['last_update'])
                    time_since_update = (datetime.now() - last_update_time).total_seconds() / 3600
                    logger.info(f"Last update was {time_since_update:.2f} hours ago")
                    if time_since_update > max_age_hours:
                        update_needed = True
                        logger.info(f"Cache is older than {max_age_hours} hours, update needed")
                else:
                    update_needed = True
                    logger.info("Last update time not found in update info, update needed")
        except Exception as e:
            logger.warning(f"Error reading last update file: {e}")
            update_needed = True
    
    # Fall back to checking file modification time
    if not update_needed and not last_update_time and os.path.exists(DATA_FILE):
        try:
            mtime = os.path.getmtime(DATA_FILE)
            file_age_seconds = datetime.now().timestamp() - mtime
            file_age_hours = file_age_seconds / 3600
            
            logger.info(f"Cache file is {file_age_hours:.2f} hours old")
            
            # Update if file is older than specified hours
            if file_age_hours > max_age_hours:
                update_needed = True
                logger.info(f"Cache file is older than {max_age_hours} hours, update needed")
        except Exception as e:
            logger.warning(f"Error checking file modification time: {e}")
            update_needed = True
    
    # If no cache exists, we need to update
    if not update_needed and not os.path.exists(DATA_FILE):
        logger.info("No cache file exists, update needed")
        update_needed = True
    
    # Perform the update if needed
    if update_needed:
        logger.info("Fetching fresh data from Gauge API")
        assets = fetch_asset_data()
        if assets:
            logger.info(f"Successfully retrieved {len(assets)} assets from API")
            if save_asset_data(assets):
                logger.info("Successfully saved updated asset data")
                
                # Sync with database
                try:
                    from app import app
                    from utils import sync_assets_with_database
                    
                    with app.app_context():
                        success, errors, message = sync_assets_with_database(assets)
                        logger.info(message)
                except Exception as e:
                    logger.error(f"Failed to sync with database: {e}")
                    logger.debug(traceback.format_exc())
                
                return assets
            else:
                logger.error("Failed to save asset data")
        else:
            logger.error("Failed to fetch asset data from API")
    else:
        logger.info("Cache is fresh, no update needed")
    
    # Either we didn't need to update or the update failed
    return load_cached_data()


def get_asset_data(use_db=True, force_update=False):
    """
    Main function to get asset data, using the most reliable source.
    
    This function attempts to get data in the following order:
    1. From database if use_db=True (most reliable)
    2. By updating from API if cache is outdated or force_update=True
    3. From cached file if API update fails
    4. From backup file if cache doesn't exist
    5. From attached assets file as a last resort
    
    Args:
        use_db (bool): Whether to try to get data from the database first
        force_update (bool): Whether to force an API update regardless of cache age
    
    Returns:
        list: List of asset dictionaries
    """
    assets = []
    
    # Try to get from database if requested (most reliable source)
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
                            'FormattedDateTime': asset.formatted_date_time() if hasattr(asset, 'formatted_date_time') and callable(asset.formatted_date_time) else None
                        }
                        assets.append(asset_dict)
                    return assets
                else:
                    logger.info("No assets found in database, trying API")
        except Exception as e:
            logger.error(f"Failed to load data from database: {e}")
            logger.debug(traceback.format_exc())
    
    # Try to update from API or get from cache
    assets = update_asset_data(force=force_update)
    
    # If we still don't have assets, try to use the attached assets file as fallback
    if not assets:
        logger.warning("No assets from API or cache, trying attached assets file as fallback")
        try:
            asset_file_path = 'attached_assets/GAUGE API PULL 1045AM_05.15.2025.json'
            if os.path.exists(asset_file_path):
                with open(asset_file_path, 'r') as f:
                    assets = json.load(f)
                logger.info(f"Loaded {len(assets)} assets from attached file")
                
                # Backup the attached file to the data directory
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_file = os.path.join(BACKUP_DIR, f'attached_gauge_data_{timestamp}.json')
                    with open(asset_file_path, 'r') as src, open(backup_file, 'w') as dst:
                        json.dump(assets, dst, indent=2)
                    logger.info(f"Backed up attached file to {backup_file}")
                except Exception as e:
                    logger.warning(f"Failed to backup attached file: {e}")
                
                # Sync with database
                try:
                    from app import app
                    from utils import sync_assets_with_database
                    
                    with app.app_context():
                        success, errors, message = sync_assets_with_database(assets)
                        logger.info(message)
                except Exception as e:
                    logger.error(f"Failed to sync attached assets with database: {e}")
                    logger.debug(traceback.format_exc())
            else:
                logger.error(f"Attached assets file not found at {asset_file_path}")
                assets = []
                
        except Exception as e:
            logger.error(f"Failed to load attached assets file: {e}")
            logger.debug(traceback.format_exc())
            assets = []
    
    return assets


# Execute this if the script is run directly
if __name__ == "__main__":
    print(f"Gauge API URL: {GAUGE_API_URL}")
    print("Updating asset data...")
    assets = update_asset_data(force=True)
    print(f"Retrieved {len(assets)} assets")