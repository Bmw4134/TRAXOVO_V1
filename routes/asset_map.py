import os
import json
import logging
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request
import equipment_lifecycle as lifecycle

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
asset_map_bp = Blueprint('asset_map', __name__, url_prefix='/asset-map')

# Cache directory for asset locations
ASSET_LOCATION_CACHE = 'data/cached/asset_locations'
os.makedirs(ASSET_LOCATION_CACHE, exist_ok=True)

@asset_map_bp.route('/')
def asset_map():
    """Render the asset map dashboard."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    return render_template('asset_map.html', date=current_date)

@asset_map_bp.route('/api/assets')
def api_assets():
    """API endpoint to get active assets with their locations."""
    # Get the date parameter or use current date
    date_param = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    
    # Get active assets for the specified date
    active_assets = lifecycle.get_active_assets(date_param)
    
    # Get locations for active assets
    asset_locations = get_asset_locations(active_assets, date_param)
    
    return jsonify(asset_locations)

def get_asset_locations(asset_ids, date_str=None):
    """
    Get locations for the specified assets.
    First check cached locations, then fall back to last known locations
    from DrivingHistory or ActivityDetail.
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    asset_locations = []
    date_formatted = date_str.replace('-', '')
    
    # Check cached locations first
    cache_file = os.path.join(ASSET_LOCATION_CACHE, f"locations_{date_formatted}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                
            # Filter to include only active assets
            asset_locations = [
                asset for asset in cached_data
                if asset.get('asset_id') in asset_ids
            ]
            
            if asset_locations:
                return asset_locations
        except Exception as e:
            logger.error(f"Error loading cached locations: {e}")
    
    # If cache doesn't exist or is empty, try to get data from DrivingHistory
    try:
        driving_history_file = find_latest_driving_history(date_str)
        if driving_history_file:
            driving_history_locations = extract_locations_from_driving_history(
                driving_history_file, asset_ids
            )
            if driving_history_locations:
                # Cache the results for future use
                cache_asset_locations(driving_history_locations, date_formatted)
                return driving_history_locations
    except Exception as e:
        logger.error(f"Error getting locations from DrivingHistory: {e}")
    
    # If DrivingHistory doesn't have data, try ActivityDetail
    try:
        activity_detail_file = find_latest_activity_detail(date_str)
        if activity_detail_file:
            activity_detail_locations = extract_locations_from_activity_detail(
                activity_detail_file, asset_ids
            )
            if activity_detail_locations:
                # Cache the results for future use
                cache_asset_locations(activity_detail_locations, date_formatted)
                return activity_detail_locations
    except Exception as e:
        logger.error(f"Error getting locations from ActivityDetail: {e}")
    
    # If no location data is available, return assets with default location
    for asset_id in asset_ids:
        asset_detail = lifecycle.get_asset_details(asset_id)
        driver_id = lifecycle.get_current_driver(asset_id, date_str)
        
        # Create a default asset entry with centerpoint of Dallas/Fort Worth
        asset_locations.append({
            'asset_id': asset_id,
            'driver_id': driver_id,
            'latitude': 32.7767,  # DFW area default
            'longitude': -96.7970,
            'location_source': 'default',
            'status': 'active',
            'last_updated': datetime.now().isoformat()
        })
    
    return asset_locations

def find_latest_driving_history(date_str):
    """Find the latest DrivingHistory file for a given date."""
    date_formatted = date_str.replace('-', '')
    
    # Search in data/driving_history directory
    search_paths = [
        f'data/driving_history/DrivingHistory_{date_formatted}.csv',
        f'data/DrivingHistory_{date_formatted}.csv',
        f'attached_assets/DrivingHistory_{date_formatted}.csv'
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            return path
    
    # If exact match not found, search for any file containing the date
    for directory in ['data/driving_history', 'data', 'attached_assets']:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.endswith('.csv') and ('driv' in filename.lower() or 'history' in filename.lower()) and date_formatted in filename:
                    return os.path.join(directory, filename)
    
    return None

def find_latest_activity_detail(date_str):
    """Find the latest ActivityDetail file for a given date."""
    date_formatted = date_str.replace('-', '')
    
    # Search in data/activity_detail directory
    search_paths = [
        f'data/activity_detail/ActivityDetail_{date_formatted}.csv',
        f'data/ActivityDetail_{date_formatted}.csv',
        f'attached_assets/ActivityDetail_{date_formatted}.csv'
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            return path
    
    # If exact match not found, search for any file containing the date
    for directory in ['data/activity_detail', 'data', 'attached_assets']:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.endswith('.csv') and ('activ' in filename.lower() or 'detail' in filename.lower()) and date_formatted in filename:
                    return os.path.join(directory, filename)
    
    return None

def extract_locations_from_driving_history(file_path, asset_ids):
    """Extract location data from DrivingHistory file."""
    import pandas as pd
    import re
    
    asset_locations = []
    
    try:
        # Determine delimiter
        with open(file_path, 'r') as f:
            header = f.readline().strip()
        
        delimiter = ',' if ',' in header else ';'
        
        # Read file
        df = pd.read_csv(file_path, delimiter=delimiter)
        
        # Normalize column names
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Find relevant columns
        asset_col = next((col for col in ['asset', 'asset_id', 'equipment', 'equipment_id'] if col in df.columns), None)
        driver_col = next((col for col in ['driver', 'driver_name', 'employee', 'employee_name'] if col in df.columns), None)
        location_col = next((col for col in ['location', 'site', 'job_site', 'place'] if col in df.columns), None)
        datetime_col = next((col for col in ['datetime', 'date_time', 'timestamp', 'time'] if col in df.columns), None)
        
        if not all([asset_col, location_col]):
            logger.warning(f"Missing required columns in {file_path}")
            return []
        
        # Extract coordinates from location string
        def extract_coordinates(location_str):
            if pd.isna(location_str):
                return None, None
            
            # Try to extract coordinates from location string
            # Common format: "Location Name (32.7767, -96.7970)"
            coord_match = re.search(r'\((-?\d+\.\d+),\s*(-?\d+\.\d+)\)', str(location_str))
            if coord_match:
                return float(coord_match.group(1)), float(coord_match.group(2))
            
            # If no coordinates in string, use default DFW coordinates
            return 32.7767, -96.7970
        
        # Process each asset
        for asset_id in asset_ids:
            # Filter to get rows for this asset
            asset_rows = df[df[asset_col].astype(str).str.upper() == asset_id.upper()]
            
            if not asset_rows.empty:
                # Sort by datetime if available to get the latest record
                if datetime_col and datetime_col in asset_rows.columns:
                    asset_rows = asset_rows.sort_values(by=datetime_col, ascending=False)
                
                # Get the latest record
                latest_row = asset_rows.iloc[0]
                
                # Get location data
                location_str = latest_row[location_col] if location_col and pd.notna(latest_row[location_col]) else "Unknown"
                latitude, longitude = extract_coordinates(location_str)
                
                # Get driver ID
                driver_id = str(latest_row[driver_col]) if driver_col and pd.notna(latest_row[driver_col]) else None
                
                # Add to results
                asset_locations.append({
                    'asset_id': asset_id,
                    'driver_id': driver_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'location': str(location_str),
                    'location_source': 'driving_history',
                    'status': 'active',
                    'last_updated': datetime.now().isoformat()
                })
    except Exception as e:
        logger.error(f"Error processing DrivingHistory file: {e}")
    
    return asset_locations

def extract_locations_from_activity_detail(file_path, asset_ids):
    """Extract location data from ActivityDetail file."""
    import pandas as pd
    import re
    
    asset_locations = []
    
    try:
        # Determine delimiter
        with open(file_path, 'r') as f:
            header = f.readline().strip()
        
        delimiter = ',' if ',' in header else ';'
        
        # Read file
        df = pd.read_csv(file_path, delimiter=delimiter)
        
        # Normalize column names
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Find relevant columns
        asset_col = next((col for col in ['asset', 'asset_id', 'equipment', 'equipment_id'] if col in df.columns), None)
        driver_col = next((col for col in ['driver', 'driver_name', 'employee', 'employee_name'] if col in df.columns), None)
        location_col = next((col for col in ['location', 'site', 'job_site', 'place'] if col in df.columns), None)
        datetime_col = next((col for col in ['datetime', 'date_time', 'timestamp', 'time', 'start_time'] if col in df.columns), None)
        
        if not all([asset_col, location_col]):
            logger.warning(f"Missing required columns in {file_path}")
            return []
        
        # Extract coordinates from location string
        def extract_coordinates(location_str):
            if pd.isna(location_str):
                return None, None
            
            # Try to extract coordinates from location string
            # Common format: "Location Name (32.7767, -96.7970)"
            coord_match = re.search(r'\((-?\d+\.\d+),\s*(-?\d+\.\d+)\)', str(location_str))
            if coord_match:
                return float(coord_match.group(1)), float(coord_match.group(2))
            
            # If no coordinates in string, use default DFW coordinates
            return 32.7767, -96.7970
        
        # Process each asset
        for asset_id in asset_ids:
            # Filter to get rows for this asset
            asset_rows = df[df[asset_col].astype(str).str.upper() == asset_id.upper()]
            
            if not asset_rows.empty:
                # Sort by datetime if available to get the latest record
                if datetime_col and datetime_col in asset_rows.columns:
                    asset_rows = asset_rows.sort_values(by=datetime_col, ascending=False)
                
                # Get the latest record
                latest_row = asset_rows.iloc[0]
                
                # Get location data
                location_str = latest_row[location_col] if location_col and pd.notna(latest_row[location_col]) else "Unknown"
                latitude, longitude = extract_coordinates(location_str)
                
                # Get driver ID
                driver_id = str(latest_row[driver_col]) if driver_col and pd.notna(latest_row[driver_col]) else None
                
                # Add to results
                asset_locations.append({
                    'asset_id': asset_id,
                    'driver_id': driver_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'location': str(location_str),
                    'location_source': 'activity_detail',
                    'status': 'active',
                    'last_updated': datetime.now().isoformat()
                })
    except Exception as e:
        logger.error(f"Error processing ActivityDetail file: {e}")
    
    return asset_locations

def cache_asset_locations(locations, date_formatted):
    """Cache asset locations for future use."""
    cache_file = os.path.join(ASSET_LOCATION_CACHE, f"locations_{date_formatted}.json")
    
    try:
        with open(cache_file, 'w') as f:
            json.dump(locations, f, indent=2)
    except Exception as e:
        logger.error(f"Error caching asset locations: {e}")