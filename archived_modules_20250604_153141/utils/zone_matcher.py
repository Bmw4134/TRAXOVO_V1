"""
Zone Matcher Utility - GPS Geofence Validation
Compares GPS coordinates against job site geofences using haversine distance
"""

import math
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class JobSiteZone:
    """Job site geofence definition"""
    job_id: str
    name: str
    center_lat: float
    center_lng: float
    radius_meters: float = 500  # Default 500m radius

# Predefined job site zones (would come from database)
JOB_ZONES = [
    JobSiteZone("2019-044", "E Long Avenue Project", 30.2672, -97.7431, 500),
    JobSiteZone("2021-017", "Plaza Development", 30.2850, -97.7550, 750),
    JobSiteZone("2024-003", "Highway 183 Bridge", 30.3100, -97.7200, 300),
]

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth
    Returns distance in meters
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2)
    
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in meters
    earth_radius = 6371000
    
    return earth_radius * c

def is_asset_in_zone(asset_lat: float, asset_lng: float, zone: JobSiteZone) -> Dict:
    """
    Check if asset is within job site geofence
    Returns dict with match status and distance
    """
    if not asset_lat or not asset_lng:
        return {
            'in_zone': False,
            'distance_meters': None,
            'zone_id': zone.job_id,
            'zone_name': zone.name,
            'reason': 'invalid_gps'
        }
    
    distance = haversine_distance(asset_lat, asset_lng, zone.center_lat, zone.center_lng)
    in_zone = distance <= zone.radius_meters
    
    return {
        'in_zone': in_zone,
        'distance_meters': round(distance, 2),
        'zone_id': zone.job_id,
        'zone_name': zone.name,
        'radius_meters': zone.radius_meters,
        'reason': 'in_geofence' if in_zone else 'outside_geofence'
    }

def match_asset_to_zones(asset: Dict) -> List[Dict]:
    """
    Match a single asset against all job site zones
    Returns list of zone matches ordered by distance
    """
    matches = []
    
    for zone in JOB_ZONES:
        match_result = is_asset_in_zone(
            asset.get('latitude'),
            asset.get('longitude'),
            zone
        )
        match_result['asset_id'] = asset.get('asset_id')
        match_result['asset_name'] = asset.get('asset_name')
        matches.append(match_result)
    
    # Sort by distance (closest first)
    matches.sort(key=lambda x: x['distance_meters'] or float('inf'))
    return matches

def match_assets_to_zones(assets: List[Dict]) -> List[Dict]:
    """
    Match multiple assets to job site zones
    Returns list of assets with their best zone match
    """
    results = []
    
    for asset in assets:
        zone_matches = match_asset_to_zones(asset)
        
        # Find best match (closest zone that asset is within)
        best_match = None
        for match in zone_matches:
            if match['in_zone']:
                best_match = match
                break
        
        # If no zone contains the asset, use closest zone
        if not best_match and zone_matches:
            best_match = zone_matches[0]
            best_match['in_zone'] = False
        
        if best_match:
            results.append({
                **asset,
                'zone_match': best_match,
                'in_zone': best_match.get('in_zone', False),
                'matched_job_id': best_match.get('zone_id'),
                'distance_to_zone': best_match.get('distance_meters')
            })
        else:
            results.append({
                **asset,
                'zone_match': None,
                'in_zone': False,
                'matched_job_id': None,
                'distance_to_zone': None
            })
    
    return results

def get_zone_by_job_id(job_id: str) -> JobSiteZone:
    """Get job site zone by job ID"""
    for zone in JOB_ZONES:
        if zone.job_id == job_id:
            return zone
    return None

def validate_employee_location(employee_data: Dict, expected_job_id: str) -> Dict:
    """
    Validate if employee's asset is at expected job site
    Used for attendance validation
    """
    asset_lat = employee_data.get('latitude')
    asset_lng = employee_data.get('longitude')
    
    expected_zone = get_zone_by_job_id(expected_job_id)
    if not expected_zone:
        return {
            'valid': False,
            'reason': 'unknown_job_site',
            'status_icon': '❓'
        }
    
    if not asset_lat or not asset_lng:
        return {
            'valid': False,
            'reason': 'no_gps_signal',
            'status_icon': '🟡',
            'zone_name': expected_zone.name
        }
    
    zone_check = is_asset_in_zone(asset_lat, asset_lng, expected_zone)
    
    if zone_check['in_zone']:
        return {
            'valid': True,
            'reason': 'on_site',
            'status_icon': '🟢',
            'distance_meters': zone_check['distance_meters'],
            'zone_name': expected_zone.name
        }
    else:
        return {
            'valid': False,
            'reason': 'off_site',
            'status_icon': '🔴',
            'distance_meters': zone_check['distance_meters'],
            'zone_name': expected_zone.name
        }

def add_job_zone(job_id: str, name: str, lat: float, lng: float, radius: int = 500):
    """Add new job site zone (would save to database in production)"""
    new_zone = JobSiteZone(job_id, name, lat, lng, radius)
    JOB_ZONES.append(new_zone)
    return new_zone