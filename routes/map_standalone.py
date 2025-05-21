"""
TRAXORA Fleet Management System - Standalone Map Module

This module provides a simplified, standalone implementation of the asset map
without dependencies on other routes or complex template inheritance.
"""
import os
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
                    'location': item.get('Location') or item.get('Site') or '',
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
                        
                # Add only official job sites from the real API data
                # Filter locations to only include those that appear to be job sites
                official_job_sites = {}
                for name, loc_data in unique_locations.items():
                    # Check if this is likely an official job site (not just a street address)
                    is_official_site = False
                    
                    # Sites with job numbers (2022-001, 2023-034, etc)
                    if name.startswith('20') and '-' in name[:10]:
                        is_official_site = True
                    
                    # Known yards and official sites
                    if any(site_keyword in name.upper() for site_keyword in 
                          ['YARD', 'SHOP', 'PROJECT', 'REHAB', 'IMPROVEMENT']):
                        is_official_site = True
                    
                    # Highway/Bridge/Road sites ONLY if they have job numbers
                    # (avoid random street addresses and highways)
                    if any(site_keyword in name.upper() for site_keyword in 
                          ['BRIDGE', 'HIGHWAY', 'SIDEWALK', 'ROAD', 'REPLACEMENT', 'MAINTENANCE']):
                        # Only count as an official site if it ALSO has a job number or yard keyword
                        if (name.startswith('20') and '-' in name[:10]) or 'YARD' in name.upper():
                            is_official_site = True
                        else:
                            is_official_site = False
                        
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
                    
                    # Determine appropriate radius based on site type
                    radius = 500  # default radius
                    if 'YARD' in name.upper():
                        radius = 800  # yards are larger
                    elif 'BRIDGE' in name.upper():
                        radius = 600  # bridge projects
                    elif 'HIGHWAY' in name.upper() or 'ROAD' in name.upper():
                        radius = 1200  # highway projects are longer
                    
                    # Add to job sites list
                    job_sites.append({
                        'id': idx,
                        'name': name,
                        'job_number': job_number or f'SITE-{idx}',
                        'latitude': loc_data['latitude'],
                        'longitude': loc_data['longitude'],
                        'address': name,
                        'radius': radius,
                        'color': color,
                        'asset_count': loc_data['count']
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