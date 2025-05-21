"""
TRAXORA Fleet Management System - Asset Data Provider

This module provides a unified interface for accessing asset data from various sources,
with intelligent fallback mechanisms to ensure data availability.
"""
import os
import csv
import logging
import json
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func
from flask import current_app

from models import Asset, AssetLocation, Driver, JobSite, db
from gauge_api import GaugeAPI

logger = logging.getLogger(__name__)

class AssetDataProvider:
    """
    Unified asset data provider with intelligent fallback mechanisms.
    Attempts to fetch data from primary sources first, then falls back
    to secondary sources when needed.
    """
    
    def __init__(self):
        """Initialize the asset data provider"""
        self.gauge_api = GaugeAPI()
        self.data_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create cache directory
        self.cache_dir = os.path.join(self.data_dir, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_assets(self, use_cache=True):
        """
        Get all assets, attempting to use the API first, then falling back to database,
        and finally to local files.
        
        Args:
            use_cache: Whether to use cached data when API is unavailable
            
        Returns:
            List of asset dictionaries
        """
        # First, try to get assets from the Gauge API
        if self.gauge_api.check_connection():
            try:
                api_assets = self.gauge_api.get_assets()
                if api_assets:
                    # Cache the API response for fallback
                    self._cache_data('assets.json', api_assets)
                    return api_assets
            except Exception as e:
                logger.warning(f"Failed to get assets from API: {str(e)}")
        
        # Second, try to get assets from the database
        try:
            db_assets = Asset.query.all()
            if db_assets:
                assets_list = []
                for asset in db_assets:
                    assets_list.append({
                        'id': asset.id,
                        'asset_id': asset.asset_id,
                        'name': asset.name,
                        'type': asset.type,
                        'status': asset.status,
                        'last_latitude': asset.last_latitude,
                        'last_longitude': asset.last_longitude,
                        'last_location_update': asset.last_location_update.isoformat() if asset.last_location_update else None
                    })
                return assets_list
        except Exception as e:
            logger.warning(f"Failed to get assets from database: {str(e)}")
        
        # Finally, try to get assets from cached file
        if use_cache:
            try:
                cached_assets = self._load_cached_data('assets.json')
                if cached_assets:
                    logger.info(f"Using {len(cached_assets)} cached assets")
                    return cached_assets
            except Exception as e:
                logger.warning(f"Failed to load cached assets: {str(e)}")
        
        # If all else fails, try to parse CSV files from attached_assets directory
        try:
            assets_from_csv = self._parse_assets_from_csv()
            if assets_from_csv:
                logger.info(f"Using {len(assets_from_csv)} assets from CSV files")
                return assets_from_csv
        except Exception as e:
            logger.warning(f"Failed to parse assets from CSV: {str(e)}")
        
        # If everything failed, return an empty list
        logger.error("All asset data sources failed, returning empty list")
        return []
    
    def get_asset_location(self, asset_id, start_date=None, end_date=None):
        """
        Get location history for an asset, with fallback mechanisms.
        
        Args:
            asset_id: The asset ID to get locations for
            start_date: Start date for history (default: 7 days ago)
            end_date: End date for history (default: now)
            
        Returns:
            List of location dictionaries
        """
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # First, try to get location from the Gauge API
        if self.gauge_api.check_connection():
            try:
                api_locations = self.gauge_api.get_asset_locations(asset_id, start_date, end_date)
                if api_locations:
                    # Cache the API response for fallback
                    cache_key = f'locations_{asset_id}_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.json'
                    self._cache_data(cache_key, api_locations)
                    return api_locations
            except Exception as e:
                logger.warning(f"Failed to get locations from API for asset {asset_id}: {str(e)}")
        
        # Second, try to get locations from the database
        try:
            # Use the location_timestamp attribute correctly
            from sqlalchemy import column
            location_timestamp = getattr(AssetLocation, 'timestamp')
            
            db_locations = AssetLocation.query.filter(
                AssetLocation.asset_id == asset_id,
                location_timestamp >= start_date,
                location_timestamp <= end_date
            ).order_by(location_timestamp).all()
            
            if db_locations:
                locations_list = []
                for location in db_locations:
                    locations_list.append({
                        'id': location.id,
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'timestamp': location.timestamp.isoformat(),
                        'speed': location.speed,
                        'heading': location.heading,
                        'altitude': location.altitude,
                        'accuracy': location.accuracy,
                        'job_site_id': location.job_site_id
                    })
                return locations_list
        except Exception as e:
            logger.warning(f"Failed to get locations from database for asset {asset_id}: {str(e)}")
        
        # Finally, try to get locations from cached file
        try:
            cache_key = f'locations_{asset_id}_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.json'
            cached_locations = self._load_cached_data(cache_key)
            if cached_locations:
                logger.info(f"Using {len(cached_locations)} cached locations for asset {asset_id}")
                return cached_locations
        except Exception as e:
            logger.warning(f"Failed to load cached locations for asset {asset_id}: {str(e)}")
        
        # If all else fails, try to parse CSV files for location data
        try:
            locations_from_csv = self._parse_locations_from_csv(asset_id, start_date, end_date)
            if locations_from_csv:
                logger.info(f"Using {len(locations_from_csv)} locations from CSV for asset {asset_id}")
                return locations_from_csv
        except Exception as e:
            logger.warning(f"Failed to parse locations from CSV for asset {asset_id}: {str(e)}")
        
        # If everything failed, return an empty list
        logger.error(f"All location data sources failed for asset {asset_id}, returning empty list")
        return []
    
    def get_job_sites(self, active_only=True):
        """
        Get all job sites, with fallback mechanisms.
        
        Args:
            active_only: Whether to get only active job sites
            
        Returns:
            List of job site dictionaries
        """
        # First, try to get job sites from the database
        try:
            query = JobSite.query
            if active_only:
                query = query.filter_by(active=True)
            
            db_job_sites = query.all()
            if db_job_sites:
                job_sites_list = []
                for site in db_job_sites:
                    job_sites_list.append({
                        'id': site.id,
                        'job_number': site.job_number,
                        'name': site.name,
                        'latitude': site.latitude,
                        'longitude': site.longitude,
                        'radius': site.radius,
                        'address': site.address,
                        'city': site.city,
                        'state': site.state,
                        'zipcode': site.zipcode,
                        'active': site.is_active
                    })
                return job_sites_list
        except Exception as e:
            logger.warning(f"Failed to get job sites from database: {str(e)}")
        
        # Try to get job sites from cached file
        try:
            cached_job_sites = self._load_cached_data('job_sites.json')
            if cached_job_sites:
                if active_only:
                    cached_job_sites = [site for site in cached_job_sites if site.get('active', True)]
                logger.info(f"Using {len(cached_job_sites)} cached job sites")
                return cached_job_sites
        except Exception as e:
            logger.warning(f"Failed to load cached job sites: {str(e)}")
        
        # Try to parse job sites from CSV files
        try:
            job_sites_from_csv = self._parse_job_sites_from_csv()
            if job_sites_from_csv:
                if active_only:
                    job_sites_from_csv = [site for site in job_sites_from_csv if site.get('active', True)]
                logger.info(f"Using {len(job_sites_from_csv)} job sites from CSV")
                self._cache_data('job_sites.json', job_sites_from_csv)
                return job_sites_from_csv
        except Exception as e:
            logger.warning(f"Failed to parse job sites from CSV: {str(e)}")
        
        # If everything failed, return an empty list
        logger.error("All job site data sources failed, returning empty list")
        return []
    
    def get_heatmap_data(self, start_date=None, end_date=None):
        """
        Get heatmap data for asset activity, with fallback mechanisms.
        
        Args:
            start_date: Start date for heatmap (default: 7 days ago)
            end_date: End date for heatmap (default: now)
            
        Returns:
            List of heatmap point dictionaries
        """
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Try to get heatmap data from the database
        try:
            # Use the location_timestamp attribute correctly
            from sqlalchemy import column
            location_timestamp = getattr(AssetLocation, 'timestamp')
            
            # Get the asset locations aggregated by geographic grid
            heatmap_data = db.session.query(
                func.round(AssetLocation.latitude, 3).label('lat_grid'),
                func.round(AssetLocation.longitude, 3).label('lng_grid'),
                func.count().label('count')
            ).filter(
                location_timestamp >= start_date,
                location_timestamp <= end_date
            ).group_by('lat_grid', 'lng_grid').all()
            
            if heatmap_data:
                result = []
                for lat_grid, lng_grid, count in heatmap_data:
                    point = {
                        'latitude': float(lat_grid),
                        'longitude': float(lng_grid),
                        'weight': min(count / 10, 1.0)  # Normalize weight between 0 and 1
                    }
                    result.append(point)
                return result
        except Exception as e:
            logger.warning(f"Failed to get heatmap data from database: {str(e)}")
        
        # Try to get heatmap data from cached file
        try:
            cache_key = f'heatmap_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.json'
            cached_heatmap = self._load_cached_data(cache_key)
            if cached_heatmap:
                logger.info(f"Using {len(cached_heatmap)} cached heatmap points")
                return cached_heatmap
        except Exception as e:
            logger.warning(f"Failed to load cached heatmap: {str(e)}")
        
        # If all else fails, generate a heatmap from CSV files
        try:
            all_locations = self._parse_all_locations_from_csv(start_date, end_date)
            if all_locations:
                # Generate a heatmap from CSV location data
                heatmap_data = self._generate_heatmap_from_locations(all_locations)
                if heatmap_data:
                    # Cache the heatmap data
                    cache_key = f'heatmap_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.json'
                    self._cache_data(cache_key, heatmap_data)
                    logger.info(f"Generated {len(heatmap_data)} heatmap points from CSV locations")
                    return heatmap_data
        except Exception as e:
            logger.warning(f"Failed to generate heatmap from CSV: {str(e)}")
        
        # If everything failed, return an empty list
        logger.error("All heatmap data sources failed, returning empty list")
        return []
    
    def _cache_data(self, filename, data):
        """
        Cache data to a JSON file for fallback.
        
        Args:
            filename: Name of the cache file
            data: Data to cache
        """
        try:
            cache_path = os.path.join(self.cache_dir, filename)
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            logger.debug(f"Cached data to {cache_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cache data to {filename}: {str(e)}")
            return False
    
    def _load_cached_data(self, filename):
        """
        Load cached data from a JSON file.
        
        Args:
            filename: Name of the cache file
            
        Returns:
            The cached data or None if not found
        """
        cache_path = os.path.join(self.cache_dir, filename)
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            logger.debug(f"Loaded cached data from {cache_path}")
            return data
        except Exception as e:
            logger.warning(f"Failed to load cached data from {filename}: {str(e)}")
            return None
    
    def _parse_assets_from_csv(self):
        """
        Parse assets from CSV files in the attached_assets directory.
        
        Returns:
            List of asset dictionaries
        """
        assets = []
        asset_ids = set()
        
        # Check for common CSV file names that might contain asset data
        attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
        
        for filename in os.listdir(attached_assets_dir):
            if not filename.endswith('.csv'):
                continue
            
            if 'ActivityDetail' in filename or 'DrivingHistory' in filename or 'AssetTimeOnSite' in filename:
                file_path = os.path.join(attached_assets_dir, filename)
                
                try:
                    # Use pandas to read the CSV file
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    
                    # Look for asset columns with common names
                    asset_column = None
                    for col in ['Asset', 'AssetId', 'Asset ID', 'Vehicle', 'VehicleId', 'Vehicle ID']:
                        if col in df.columns:
                            asset_column = col
                            break
                    
                    if asset_column:
                        # Extract unique assets
                        unique_assets = df[asset_column].dropna().unique()
                        
                        for asset_name in unique_assets:
                            if asset_name and str(asset_name) not in asset_ids:
                                asset_ids.add(str(asset_name))
                                
                                # Get latitude and longitude if available
                                lat, lng = None, None
                                if 'Latitude' in df.columns and 'Longitude' in df.columns:
                                    asset_rows = df[df[asset_column] == asset_name]
                                    if not asset_rows.empty:
                                        lat = asset_rows['Latitude'].iloc[0]
                                        lng = asset_rows['Longitude'].iloc[0]
                                
                                assets.append({
                                    'id': len(assets) + 1,
                                    'asset_id': str(asset_name),
                                    'name': str(asset_name),
                                    'type': 'Vehicle',
                                    'status': 'active',
                                    'last_latitude': lat,
                                    'last_longitude': lng,
                                    'last_location_update': datetime.now().isoformat()
                                })
                except Exception as e:
                    logger.warning(f"Error parsing assets from {filename}: {str(e)}")
                    continue
        
        return assets
    
    def _parse_locations_from_csv(self, asset_id, start_date, end_date):
        """
        Parse location data for a specific asset from CSV files.
        
        Args:
            asset_id: The asset ID to find locations for
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of location dictionaries
        """
        locations = []
        attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
        
        for filename in os.listdir(attached_assets_dir):
            if not filename.endswith('.csv'):
                continue
            
            if 'DrivingHistory' in filename or 'AssetTimeOnSite' in filename or 'ActivityDetail' in filename:
                file_path = os.path.join(attached_assets_dir, filename)
                
                try:
                    # Use pandas to read the CSV file
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    
                    # Look for asset and location columns
                    asset_column = None
                    for col in ['Asset', 'AssetId', 'Asset ID', 'Vehicle', 'VehicleId', 'Vehicle ID']:
                        if col in df.columns:
                            asset_column = col
                            break
                    
                    lat_column = None
                    lng_column = None
                    time_column = None
                    
                    for col in ['Latitude', 'Lat']:
                        if col in df.columns:
                            lat_column = col
                            break
                    
                    for col in ['Longitude', 'Long', 'Lng']:
                        if col in df.columns:
                            lng_column = col
                            break
                    
                    for col in ['Timestamp', 'Time', 'Date', 'DateTime']:
                        if col in df.columns:
                            time_column = col
                            break
                    
                    if asset_column and lat_column and lng_column:
                        # Filter for the specific asset
                        asset_df = df[df[asset_column].astype(str) == str(asset_id)]
                        
                        if not asset_df.empty:
                            # Process each row as a location
                            for _, row in asset_df.iterrows():
                                lat = row[lat_column]
                                lng = row[lng_column]
                                
                                # Skip if latitude or longitude is missing
                                if pd.isna(lat) or pd.isna(lng):
                                    continue
                                
                                # Parse timestamp if available
                                timestamp = datetime.now()
                                if time_column and not pd.isna(row[time_column]):
                                    try:
                                        # Try different date formats
                                        timestamp_str = str(row[time_column])
                                        for fmt in [
                                            '%m/%d/%Y %H:%M:%S',
                                            '%Y-%m-%d %H:%M:%S',
                                            '%m/%d/%Y',
                                            '%Y-%m-%d'
                                        ]:
                                            try:
                                                timestamp = datetime.strptime(timestamp_str, fmt)
                                                break
                                            except ValueError:
                                                continue
                                    except Exception:
                                        pass
                                
                                # Skip if outside date range
                                if timestamp < start_date or timestamp > end_date:
                                    continue
                                
                                # Add location to list
                                locations.append({
                                    'id': len(locations) + 1,
                                    'latitude': float(lat),
                                    'longitude': float(lng),
                                    'timestamp': timestamp.isoformat(),
                                    'speed': float(row['Speed']) if 'Speed' in row and not pd.isna(row['Speed']) else 0,
                                    'heading': float(row['Heading']) if 'Heading' in row and not pd.isna(row['Heading']) else 0,
                                    'altitude': float(row['Altitude']) if 'Altitude' in row and not pd.isna(row['Altitude']) else 0,
                                    'accuracy': float(row['Accuracy']) if 'Accuracy' in row and not pd.isna(row['Accuracy']) else 0,
                                    'job_site_id': None
                                })
                except Exception as e:
                    logger.warning(f"Error parsing locations from {filename} for asset {asset_id}: {str(e)}")
                    continue
        
        # Sort locations by timestamp
        locations.sort(key=lambda x: x['timestamp'])
        return locations
    
    def _parse_job_sites_from_csv(self):
        """
        Parse job sites from CSV files.
        
        Returns:
            List of job site dictionaries
        """
        job_sites = []
        site_names = set()
        attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
        
        for filename in os.listdir(attached_assets_dir):
            if not filename.endswith('.csv'):
                continue
            
            if 'ActivityDetail' in filename or 'AssetTimeOnSite' in filename:
                file_path = os.path.join(attached_assets_dir, filename)
                
                try:
                    # Use pandas to read the CSV file
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    
                    # Look for job site columns
                    site_column = None
                    for col in ['Job', 'JobSite', 'Job Site', 'Location', 'Site']:
                        if col in df.columns:
                            site_column = col
                            break
                    
                    if site_column:
                        # Extract unique job sites
                        unique_sites = df[site_column].dropna().unique()
                        
                        for site_name in unique_sites:
                            if site_name and str(site_name) not in site_names:
                                site_names.add(str(site_name))
                                
                                # Get latitude and longitude if available
                                lat, lng = None, None
                                if 'Latitude' in df.columns and 'Longitude' in df.columns:
                                    site_rows = df[df[site_column] == site_name]
                                    if not site_rows.empty:
                                        # Use the most common lat/lng for this site
                                        lat = site_rows['Latitude'].mode().iloc[0] if not site_rows['Latitude'].mode().empty else None
                                        lng = site_rows['Longitude'].mode().iloc[0] if not site_rows['Longitude'].mode().empty else None
                                
                                # Extract job number if available
                                job_number = None
                                if 'JobNumber' in df.columns or 'Job Number' in df.columns:
                                    job_num_col = 'JobNumber' if 'JobNumber' in df.columns else 'Job Number'
                                    site_rows = df[df[site_column] == site_name]
                                    if not site_rows.empty and not site_rows[job_num_col].empty:
                                        job_number = site_rows[job_num_col].mode().iloc[0] if not site_rows[job_num_col].mode().empty else None
                                
                                job_sites.append({
                                    'id': len(job_sites) + 1,
                                    'job_number': job_number or f"JOB{len(job_sites) + 1:03d}",
                                    'name': str(site_name),
                                    'latitude': lat,
                                    'longitude': lng,
                                    'radius': 500,  # Default radius in meters
                                    'address': None,
                                    'city': None,
                                    'state': None,
                                    'zipcode': None,
                                    'active': True
                                })
                except Exception as e:
                    logger.warning(f"Error parsing job sites from {filename}: {str(e)}")
                    continue
        
        return job_sites
    
    def _parse_all_locations_from_csv(self, start_date, end_date):
        """
        Parse all location data from CSV files within the date range.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of location dictionaries
        """
        all_locations = []
        attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
        
        for filename in os.listdir(attached_assets_dir):
            if not filename.endswith('.csv'):
                continue
            
            if 'DrivingHistory' in filename or 'AssetTimeOnSite' in filename or 'ActivityDetail' in filename:
                file_path = os.path.join(attached_assets_dir, filename)
                
                try:
                    # Use pandas to read the CSV file
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    
                    # Look for location columns
                    lat_column = None
                    lng_column = None
                    time_column = None
                    
                    for col in ['Latitude', 'Lat']:
                        if col in df.columns:
                            lat_column = col
                            break
                    
                    for col in ['Longitude', 'Long', 'Lng']:
                        if col in df.columns:
                            lng_column = col
                            break
                    
                    for col in ['Timestamp', 'Time', 'Date', 'DateTime']:
                        if col in df.columns:
                            time_column = col
                            break
                    
                    if lat_column and lng_column:
                        # Process rows with lat/lng data
                        for _, row in df.iterrows():
                            lat = row[lat_column]
                            lng = row[lng_column]
                            
                            # Skip if latitude or longitude is missing
                            if pd.isna(lat) or pd.isna(lng):
                                continue
                            
                            # Parse timestamp if available
                            timestamp = datetime.now()
                            if time_column and not pd.isna(row[time_column]):
                                try:
                                    # Try different date formats
                                    timestamp_str = str(row[time_column])
                                    for fmt in [
                                        '%m/%d/%Y %H:%M:%S',
                                        '%Y-%m-%d %H:%M:%S',
                                        '%m/%d/%Y',
                                        '%Y-%m-%d'
                                    ]:
                                        try:
                                            timestamp = datetime.strptime(timestamp_str, fmt)
                                            break
                                        except ValueError:
                                            continue
                                except Exception:
                                    pass
                            
                            # Skip if outside date range
                            if timestamp < start_date or timestamp > end_date:
                                continue
                            
                            # Add to all locations
                            all_locations.append({
                                'latitude': float(lat),
                                'longitude': float(lng),
                                'timestamp': timestamp.isoformat()
                            })
                except Exception as e:
                    logger.warning(f"Error parsing all locations from {filename}: {str(e)}")
                    continue
        
        return all_locations
    
    def _generate_heatmap_from_locations(self, locations):
        """
        Generate heatmap data from a list of locations.
        
        Args:
            locations: List of location dictionaries with lat/lng
            
        Returns:
            List of heatmap point dictionaries
        """
        if not locations:
            return []
        
        # Create a DataFrame from the locations
        df = pd.DataFrame(locations)
        
        # Round coordinates to create grid points
        df['lat_grid'] = df['latitude'].apply(lambda x: round(x, 3))
        df['lng_grid'] = df['longitude'].apply(lambda x: round(x, 3))
        
        # Group by grid points and count occurrences
        grid_counts = df.groupby(['lat_grid', 'lng_grid']).size().reset_index(name='count')
        
        # Convert to heatmap format
        result = []
        max_count = grid_counts['count'].max() if not grid_counts.empty else 10
        
        for _, row in grid_counts.iterrows():
            point = {
                'latitude': float(row['lat_grid']),
                'longitude': float(row['lng_grid']),
                'weight': min(row['count'] / max_count, 1.0)  # Normalize weight between 0 and 1
            }
            result.append(point)
        
        return result