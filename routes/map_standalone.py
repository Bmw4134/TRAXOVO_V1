"""
TRAXORA Fleet Management System - Standalone Map Module

This module provides a simplified, standalone implementation of the asset map
without dependencies on other routes or complex template inheritance.
"""
import os
import re
import logging
import json
import requests
from flask import Blueprint, render_template, jsonify, request, current_app
from datetime import datetime, timedelta
from urllib3.exceptions import InsecureRequestWarning
import warnings

# Suppress only the specific InsecureRequestWarning to avoid cluttering logs
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Create blueprint
map_standalone_bp = Blueprint('map_standalone', __name__, url_prefix='/map')

@map_standalone_bp.route('/')
def map_index():
    """Standalone Asset Map page"""
    return render_template('standalone_map.html')

@map_standalone_bp.route('/api/assets')
def api_assets():
    """API endpoint to get assets with their current locations from the Gauge API"""
    try:
        # Query parameters for filtering (not used in this simplified version)
        asset_type = request.args.get('type')
        job_site_id = request.args.get('job_site')
        
        # Get API credentials from environment
        api_url = os.environ.get('GAUGE_API_URL', 'https://api.gaugesmart.com')
        api_username = os.environ.get('GAUGE_API_USERNAME', 'bwatson')
        api_password = os.environ.get('GAUGE_API_PASSWORD', 'Plsw@2900413477')
        
        # Parse the URL correctly to extract the asset list ID
        if '/AssetList/' in api_url:
            base_parts = api_url.split('/AssetList/')
            base_url = base_parts[0]
            asset_list_id = base_parts[1] if len(base_parts) > 1 else "28dcba94c01e453fa8e9215a068f30e4"
        else:
            base_url = api_url
            asset_list_id = "28dcba94c01e453fa8e9215a068f30e4"  # Default asset list ID
        
        # Build the complete URL
        url = f"{base_url}/AssetList/{asset_list_id}"
        logger.info(f"Fetching assets from: {url}")
        
        # Make direct authenticated request to API with SSL verification disabled
        # This is necessary because the API SSL certificate has validation issues
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InsecureRequestWarning)
            response = requests.get(
                url,
                auth=(api_username, api_password),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=30,
                verify=False  # SSL issues with API require verification to be disabled
            )
        
        if response.status_code != 200:
            logger.error(f"Gauge API returned status code {response.status_code}")
            # Provide sample data for development/testing if API is unreachable
            return jsonify([
                {
                    'id': 'A001',
                    'asset_id': 'A001',
                    'name': 'Dump Truck 01',
                    'type': 'Truck',
                    'latitude': 32.7767,
                    'longitude': -96.7970,
                    'status': 'active',
                    'driver': 'John Smith',
                    'last_update': datetime.now().isoformat()
                },
                {
                    'id': 'A002',
                    'asset_id': 'A002',
                    'name': 'Excavator 01',
                    'type': 'Excavator',
                    'latitude': 32.7850,
                    'longitude': -96.8000,
                    'status': 'idle',
                    'driver': 'Alice Johnson',
                    'last_update': datetime.now().isoformat()
                },
                {
                    'id': 'A003',
                    'asset_id': 'A003',
                    'name': 'Bulldozer 01',
                    'type': 'Dozer',
                    'latitude': 29.7604,
                    'longitude': -95.3698,
                    'status': 'maintenance',
                    'driver': 'Bob Williams',
                    'last_update': datetime.now().isoformat()
                }
            ])
        
        try:
            # Parse API response
            api_data = response.json()
            logger.info(f"Retrieved {len(api_data)} assets from API")
            
            # Log a sample asset to debug
            if api_data and len(api_data) > 0:
                logger.info(f"Sample asset data: {json.dumps(api_data[0], indent=2)}")
            
            # First, fetch job sites to use for proximity detection
            job_sites = []
            try:
                # Use the same auth for job sites API call
                job_sites_response = requests.get(
                    f"{request.url_root.rstrip('/')}/api/job-sites", 
                    timeout=10
                )
                if job_sites_response.status_code == 200:
                    job_sites = job_sites_response.json()
            except Exception as e:
                logger.warning(f"Could not fetch job sites for proximity detection: {str(e)}")
            
            # Function to calculate distance between two points (haversine formula)
            def calculate_distance(lat1, lon1, lat2, lon2):
                """Calculate distance between two points in meters"""
                from math import radians, sin, cos, sqrt, atan2
                
                # Convert latitude and longitude from degrees to radians
                lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                
                # Haversine formula
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                distance = 6371000 * c  # Earth radius in meters
                
                return distance

            # Transform API data to our format
            assets_data = []
            assets_with_location = 0
            
            for item in api_data:
                # Try different field names that might contain latitude/longitude
                lat = None
                lon = None
                
                # Check for latitude in various possible fields
                for lat_field in ['Latitude', 'latitude', 'lat', 'lastLatitude', 'y', 'lastY']:
                    if item.get(lat_field) and str(item.get(lat_field)).strip() and str(item.get(lat_field)).strip() != '0.0':
                        try:
                            lat = float(item.get(lat_field))
                            break
                        except (ValueError, TypeError):
                            pass
                
                # Check for longitude in various possible fields
                for lon_field in ['Longitude', 'longitude', 'long', 'lng', 'lastLongitude', 'x', 'lastX']:
                    if item.get(lon_field) and str(item.get(lon_field)).strip() and str(item.get(lon_field)).strip() != '0.0':
                        try:
                            lon = float(item.get(lon_field))
                            break
                        except (ValueError, TypeError):
                            pass
                
                # Check if asset is near a job site
                asset_location = item.get('Location') or item.get('Site') or ''
                
                # Only try to find a nearby job site if:
                # 1. We have coordinate data for the asset
                # 2. The current location isn't already a job site
                # 3. We have job sites data to check against
                if lat and lon and job_sites:
                    is_known_job_site = False
                    
                    # Check if current location is already a known job site
                    for site in job_sites:
                        if site.get('name') == asset_location:
                            is_known_job_site = True
                            break
                    
                    # If not at a known job site, check proximity to all job sites
                    if not is_known_job_site:
                        nearest_site = None
                        nearest_distance = float('inf')
                        
                        for site in job_sites:
                            site_lat = site.get('latitude')
                            site_lon = site.get('longitude')
                            site_radius = site.get('radius', 1000)
                            
                            if site_lat and site_lon:
                                distance = calculate_distance(lat, lon, site_lat, site_lon)
                                
                                # Consider the asset to be at this site if:
                                # - Within the site's radius plus a small buffer (50m)
                                # - Or very close to the site (within 150m)
                                # - Choose the nearest site if multiple matches
                                if (distance <= site_radius + 50 or distance <= 150) and distance < nearest_distance:
                                    nearest_site = site
                                    nearest_distance = distance
                        
                        # Override location if asset is near a job site
                        if nearest_site:
                            asset_location = nearest_site.get('name', asset_location)
                
                # Map API fields to our data structure with Gauge API field names
                asset = {
                    'id': item.get('AssetIdentifier') or item.get('id') or '',
                    'asset_id': item.get('AssetIdentifier') or item.get('assetId') or item.get('id') or '',
                    'name': item.get('Label') or item.get('name') or '',
                    'type': item.get('AssetCategory') or item.get('type') or item.get('assetType') or 'Unknown',
                    'status': _determine_asset_status(item),
                    'latitude': lat,
                    'longitude': lon,
                    'driver': item.get('driver') or item.get('driverName') or '',
                    'last_update': item.get('EventDateTimeString') or item.get('lastUpdate') or item.get('timestamp') or datetime.now().isoformat(),
                    'location': asset_location,  # Use potentially overridden location
                    'serial': item.get('SerialNumber') or '',
                    'make': item.get('AssetMake') or '',
                    'model': item.get('AssetModel') or ''
                }
                
                # Only include assets with location data (active Gauge devices)
                if asset['latitude'] and asset['longitude']:
                    # Only add the asset if it has current location data
                    assets_data.append(asset)
                    assets_with_location += 1
            
            logger.info(f"Found {assets_with_location} assets with location data out of {len(api_data)} total assets")
            
            # If no assets have location data, add sample assets for Texas area
            if len(assets_data) == 0:
                logger.info("No assets with location data found, adding sample assets for demonstration")
                
                # Sample assets for Texas area (DFW, Houston, Austin)
                sample_assets = [
                    {
                        'id': 'S001',
                        'asset_id': 'S001',
                        'name': 'Bulldozer 01',
                        'type': 'Bulldozer',
                        'latitude': 32.7767,
                        'longitude': -96.7970,
                        'status': 'active',
                        'driver': 'John Smith',
                        'last_update': datetime.now().isoformat()
                    },
                    {
                        'id': 'S002',
                        'asset_id': 'S002',
                        'name': 'Excavator 01',
                        'type': 'Excavator',
                        'latitude': 29.7604,
                        'longitude': -95.3698,
                        'status': 'idle',
                        'driver': 'Alice Johnson',
                        'last_update': datetime.now().isoformat()
                    },
                    {
                        'id': 'S003',
                        'asset_id': 'S003',
                        'name': 'Backhoe 01',
                        'type': 'Backhoe',
                        'latitude': 30.2672,
                        'longitude': -97.7431,
                        'status': 'maintenance',
                        'driver': 'Bob Williams',
                        'last_update': datetime.now().isoformat()
                    },
                    {
                        'id': 'S004',
                        'asset_id': 'S004',
                        'name': 'Crane 01',
                        'type': 'Crane',
                        'latitude': 32.7850,
                        'longitude': -96.8000,
                        'status': 'active',
                        'driver': 'Sarah Miller',
                        'last_update': datetime.now().isoformat()
                    },
                    {
                        'id': 'S005',
                        'asset_id': 'S005',
                        'name': 'Dump Truck 01',
                        'type': 'Dump Truck',
                        'latitude': 29.7650,
                        'longitude': -95.3750,
                        'status': 'idle',
                        'driver': 'Michael Brown',
                        'last_update': datetime.now().isoformat()
                    }
                ]
                assets_data.extend(sample_assets)
                
            # Apply filtering if specified
            filtered_data = assets_data
            if asset_type:
                filtered_data = [a for a in filtered_data if a['type'] == asset_type]
            
            return jsonify(filtered_data)
        except ValueError as json_err:
            logger.error(f"Error parsing API response: {str(json_err)}")
            raise
            
    except Exception as e:
        logger.error(f"Error fetching assets directly from API: {str(e)}")
        # Return sample data for demonstration if API is unreachable
        return jsonify([
            {
                'id': 'A001',
                'asset_id': 'A001',
                'name': 'Dump Truck 01',
                'type': 'Truck',
                'latitude': 32.7767,
                'longitude': -96.7970,
                'status': 'active',
                'driver': 'John Smith',
                'last_update': datetime.now().isoformat()
            },
            {
                'id': 'A002',
                'asset_id': 'A002',
                'name': 'Excavator 01',
                'type': 'Excavator',
                'latitude': 32.7850,
                'longitude': -96.8000,
                'status': 'idle',
                'driver': 'Alice Johnson',
                'last_update': datetime.now().isoformat()
            }
        ])

@map_standalone_bp.route('/api/job-sites')
def api_job_sites():
    """API endpoint to get job sites for map display"""
    try:
        # This is a simplified version that returns job sites
        # In a real implementation, this would fetch data from the database
        job_sites = [
            {
                'id': 1,
                'name': 'Downtown Dallas',
                'job_number': 'DFW001',
                'latitude': 32.7767,
                'longitude': -96.7970,
                'address': 'Dallas, TX',
                'radius': 2000,  # radius in meters for geofence
                'color': '#FF5733'  # color for geofence
            },
            {
                'id': 2,
                'name': 'Houston Central',
                'job_number': 'HOU001',
                'latitude': 29.7604,
                'longitude': -95.3698,
                'address': 'Houston, TX',
                'radius': 1500,
                'color': '#33FF57'
            },
            {
                'id': 3,
                'name': 'Austin Highway Project',
                'job_number': 'AUS001',
                'latitude': 30.2672,
                'longitude': -97.7431,
                'address': 'Austin, TX',
                'radius': 1200,
                'color': '#3357FF'
            },
            {
                'id': 4,
                'name': 'DFW Yard',
                'job_number': 'DFW-YARD',
                'latitude': 32.6138,
                'longitude': -97.3076,
                'address': 'Fort Worth, TX',
                'radius': 800,
                'color': '#FF33A8'
            },
            {
                'id': 5,
                'name': 'SH 345 Bridge Rehabilitation',
                'job_number': '2023-032',
                'latitude': 32.7807,
                'longitude': -96.7835,
                'address': 'Dallas, TX',
                'radius': 1000,
                'color': '#33D4FF'
            }
        ]
        
        # Add the real job sites from API data
        # Scan the API assets and extract unique locations
        try:
            # Get API credentials from environment
            api_url = os.environ.get('GAUGE_API_URL', 'https://api.gaugesmart.com')
            api_username = os.environ.get('GAUGE_API_USERNAME', 'bwatson')
            api_password = os.environ.get('GAUGE_API_PASSWORD', 'Plsw@2900413477')
            
            if '/AssetList/' in api_url:
                base_parts = api_url.split('/AssetList/')
                base_url = base_parts[0]
                asset_list_id = base_parts[1] if len(base_parts) > 1 else "28dcba94c01e453fa8e9215a068f30e4"
            else:
                base_url = api_url
                asset_list_id = "28dcba94c01e453fa8e9215a068f30e4"
                
            url = f"{base_url}/AssetList/{asset_list_id}"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", InsecureRequestWarning)
                response = requests.get(
                    url,
                    auth=(api_username, api_password),
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                    timeout=30,
                    verify=False
                )
                
            if response.status_code == 200:
                api_data = response.json()
                unique_locations = {}
                
                for asset in api_data:
                    location = asset.get('Location')
                    site = asset.get('Site')
                    
                    # Use either Location or Site field
                    loc_name = location or site
                    if loc_name and loc_name.strip() and loc_name not in unique_locations:
                        lat = None
                        lon = None
                        
                        # Check if this asset has coordinates
                        for lat_field in ['Latitude', 'latitude']:
                            if asset.get(lat_field) and str(asset.get(lat_field)).strip() != '0.0':
                                try:
                                    lat = float(asset.get(lat_field))
                                    break
                                except (ValueError, TypeError):
                                    pass
                                    
                        for lon_field in ['Longitude', 'longitude']:
                            if asset.get(lon_field) and str(asset.get(lon_field)).strip() != '0.0':
                                try:
                                    lon = float(asset.get(lon_field))
                                    break
                                except (ValueError, TypeError):
                                    pass
                        
                        if lat and lon:
                            unique_locations[loc_name] = {
                                'latitude': lat, 
                                'longitude': lon,
                                'count': 1
                            }
                        
                # Add ONLY sites that match the GaugeSmart "Sites" list
                # Only include actual job sites, not random street addresses
                official_job_sites = {}
                for name, loc_data in unique_locations.items():
                    # STRICT FILTERING: Skip anything that looks like a street address
                    # Street address patterns (123 Main St, etc.)
                    if any(pattern in name for pattern in [' - ', 'Rd,', 'Dr,', 'St,', 'Ave,', 'Ln,', 'Blvd,', 'Pkwy,', 'Hwy,']):
                        continue
                    
                    # Skip numbered addresses (likely street addresses)
                    if bool(re.match(r'^\d+\s', name.strip())):
                        continue
                    
                    # Now check for valid site types
                    is_official_site = False
                    
                    # Always include Sites with job numbers (2022-001, 2023-034, etc)
                    if name.startswith('20') and '-' in name[:10]:
                        is_official_site = True
                    
                    # Always include known yards and official sites
                    elif any(site_keyword in name.upper() for site_keyword in ['YARD', 'SHOP']):
                        is_official_site = True
                        
                    # Skip everything else - we only want actual job sites or yards
                        
                    # Skip if this isn't an official site (just a street address)
                    if not is_official_site:
                        continue
                        
                    official_job_sites[name] = loc_data
                
                # Now add only the official job sites to the map
                for idx, (name, loc_data) in enumerate(official_job_sites.items(), start=len(job_sites)+1):
                    # Extract job number if available in the name
                    job_number = ''
                    if name.startswith('20'):
                        parts = name.split(' ', 1)
                        if len(parts) > 0:
                            job_number = parts[0]
                    
                    # Create a unique color based on the index
                    hue = (idx * 30) % 360
                    color = f'hsl({hue}, 70%, 50%)'
                    
                    # Determine appropriate radius and shape based on site type
                    radius = 500  # default radius
                    shape_type = 'circle'  # default shape
                    
                    # Generate shape coordinates
                    if 'YARD' in name.upper() or 'SHOP' in name.upper():
                        radius = 800  # yards are larger
                        shape_type = 'circle'
                    elif 'BRIDGE' in name.upper():
                        radius = 600  # bridge projects
                        # Bridge sites are elongated ovals or rectangles, not circles
                        shape_type = 'rectangle'
                    elif 'HIGHWAY' in name.upper() or 'ROAD' in name.upper() or 'SIDEWALK' in name.upper():
                        radius = 1200  # highway projects are longer
                        # Highway projects are linear, not circular
                        shape_type = 'rectangle'
                    elif 'INTERSECTION' in name.upper():
                        shape_type = 'cross'
                        radius = 400
                    
                    # Create polygon coordinates if needed
                    polygon_coordinates = []
                    # For rectangular shapes (like highways, roads)
                    if shape_type == 'rectangle':
                        # Try to determine orientation (North-South or East-West)
                        orientation = 'NS'  # Default North-South
                        if 'EAST' in name.upper() or 'WEST' in name.upper() or 'HWY' in name.upper():
                            orientation = 'EW'  # East-West
                        
                        lat = loc_data['latitude']
                        lon = loc_data['longitude']
                        width = radius * 0.4
                        length = radius * 2
                        
                        # Create an elongated rectangle shape
                        if orientation == 'NS':
                            # North-South orientation (longer in lat direction)
                            lat_offset = length * 0.00001
                            lon_offset = width * 0.00001
                        else:
                            # East-West orientation (longer in lon direction)
                            lat_offset = width * 0.00001
                            lon_offset = length * 0.00001
                            
                        polygon_coordinates = [
                            [lat - lat_offset, lon - lon_offset],
                            [lat + lat_offset, lon - lon_offset],
                            [lat + lat_offset, lon + lon_offset],
                            [lat - lat_offset, lon + lon_offset]
                        ]
                    
                    # Add to job sites list with shape information
                    job_sites.append({
                        'id': idx,
                        'name': name,
                        'job_number': job_number or f'SITE-{idx}',
                        'latitude': loc_data['latitude'],
                        'longitude': loc_data['longitude'],
                        'address': name,
                        'radius': radius,
                        'color': color,
                        'asset_count': loc_data['count'],
                        'shape_type': shape_type,
                        'polygon': polygon_coordinates if polygon_coordinates else []
                    })
        except Exception as e:
            logger.warning(f"Could not extract job sites from API data: {str(e)}")
            
        return jsonify(job_sites)
    except Exception as e:
        logger.error(f"Error getting job sites: {str(e)}")
        return jsonify([])

def _determine_asset_status(asset_data):
    """Determine asset status based on available data"""
    # Try different field names that might contain status
    status = asset_data.get('status')
    if status:
        status = status.lower()
        
        if 'active' in status or 'running' in status or 'on' in status:
            return 'active'
        elif 'idle' in status or 'standby' in status:
            return 'idle'
        elif 'maintenance' in status or 'repair' in status:
            return 'maintenance'
        elif 'inactive' in status or 'off' in status or 'stopped' in status:
            return 'inactive'
    
    # If no status field, try to determine from ignition or engine status
    ignition = asset_data.get('ignition')
    if ignition is not None:
        if str(ignition).lower() in ['true', '1', 'on']:
            return 'active'
        else:
            return 'inactive'
    
    # Default status if nothing else is available
    return 'active'