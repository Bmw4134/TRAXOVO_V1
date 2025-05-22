"""
TRAXORA GENIUS CORE | Geo Validator Module

This module validates GPS positions against known job site geofences,
determining if a driver is actually at their assigned location.
"""
import logging
import math
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points in km using the Haversine formula

    Args:
        lat1 (float): Latitude of point 1
        lon1 (float): Longitude of point 1
        lat2 (float): Latitude of point 2
        lon2 (float): Longitude of point 2

    Returns:
        float: Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert coordinates to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Difference in coordinates
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance


def is_point_in_geofence(lat, lon, geofence):
    """
    Check if a point is within a geofence

    Args:
        lat (float): Latitude of the point
        lon (float): Longitude of the point
        geofence (dict): Geofence data with center coordinates and radius

    Returns:
        bool: True if the point is within the geofence, False otherwise
    """
    if not geofence:
        logger.warning("No geofence data provided")
        return False
    
    # For circular geofence
    if 'center_lat' in geofence and 'center_lon' in geofence and 'radius_km' in geofence:
        distance = calculate_distance(lat, lon, geofence['center_lat'], geofence['center_lon'])
        return distance <= geofence['radius_km']
    
    # For polygon geofence (if we add support later)
    elif 'vertices' in geofence:
        # Implement point-in-polygon algorithm here if needed
        logger.warning("Polygon geofence not yet implemented")
        return False
    
    else:
        logger.warning("Invalid geofence format")
        return False


def validate_location(location_data, job_sites):
    """
    Validate if a location is within any known job site geofence

    Args:
        location_data (dict): Location data with lat/lon
        job_sites (list): List of job sites with geofence data

    Returns:
        dict: Validation results
    """
    results = {
        'timestamp': location_data.get('timestamp', datetime.now().isoformat()),
        'is_valid': False,
        'matching_job_site': None,
        'matching_job_number': None,
        'distance_to_job': None,
        'validation_details': {}
    }
    
    # Extract coordinates
    lat = location_data.get('latitude') 
    lon = location_data.get('longitude')
    
    if not lat or not lon:
        logger.warning("No coordinates in location data")
        return results
    
    # Check each job site
    closest_job_site = None
    closest_distance = float('inf')
    
    for job_site in job_sites:
        # Skip if no geofence data
        if not job_site.get('geofence'):
            continue
        
        # Get geofence data
        geofence = job_site['geofence']
        
        # Calculate distance to job site center
        distance = calculate_distance(
            lat, lon, 
            geofence.get('center_lat', 0), 
            geofence.get('center_lon', 0)
        )
        
        # Track closest job site
        if distance < closest_distance:
            closest_job_site = job_site
            closest_distance = distance
        
        # Check if in geofence
        if is_point_in_geofence(lat, lon, geofence):
            results['is_valid'] = True
            results['matching_job_site'] = job_site.get('name')
            results['matching_job_number'] = job_site.get('job_number')
            results['distance_to_job'] = distance
            results['validation_details'] = {
                'geofence_radius_km': geofence.get('radius_km'),
                'inside_geofence': True
            }
            return results
    
    # If no match found, return closest job site info
    if closest_job_site:
        results['matching_job_site'] = closest_job_site.get('name')
        results['matching_job_number'] = closest_job_site.get('job_number')
        results['distance_to_job'] = closest_distance
        results['validation_details'] = {
            'geofence_radius_km': closest_job_site['geofence'].get('radius_km'),
            'inside_geofence': False
        }
    
    return results


def validate_driver_locations(driver_locations, job_sites, assigned_job=None):
    """
    Validate all locations for a driver against job sites

    Args:
        driver_locations (list): List of location data for a driver
        job_sites (list): List of job sites with geofence data
        assigned_job (str, optional): Driver's assigned job number

    Returns:
        dict: Validation results
    """
    results = {
        'all_validations': [],
        'valid_locations_count': 0,
        'total_locations': len(driver_locations),
        'percent_at_job': 0,
        'assigned_job_match': False,
        'closest_job_site': None,
        'validation_score': 0  # 0-100 score
    }
    
    if not driver_locations:
        return results
    
    # Filter job sites to assigned job if provided
    target_job_sites = job_sites
    if assigned_job:
        target_job_sites = [js for js in job_sites if js.get('job_number') == assigned_job]
        
        # If no matching job sites, use all job sites
        if not target_job_sites:
            logger.warning(f"No job site found matching assigned job {assigned_job}")
            target_job_sites = job_sites
    
    # Validate each location
    matching_jobs = {}
    
    for location in driver_locations:
        validation = validate_location(location, target_job_sites)
        results['all_validations'].append(validation)
        
        if validation['is_valid']:
            results['valid_locations_count'] += 1
            
            # Track matching job sites
            job_number = validation.get('matching_job_number')
            if job_number:
                matching_jobs[job_number] = matching_jobs.get(job_number, 0) + 1
    
    # Calculate percentage at job
    if results['total_locations'] > 0:
        results['percent_at_job'] = (results['valid_locations_count'] / results['total_locations']) * 100
    
    # Determine most frequent job site
    most_frequent_job = None
    most_frequent_count = 0
    
    for job_number, count in matching_jobs.items():
        if count > most_frequent_count:
            most_frequent_job = job_number
            most_frequent_count = count
    
    # Check if most frequent job matches assigned job
    if most_frequent_job and assigned_job and most_frequent_job == assigned_job:
        results['assigned_job_match'] = True
    
    # Set closest job site based on most frequent
    if most_frequent_job:
        results['closest_job_site'] = most_frequent_job
    
    # Calculate validation score (0-100)
    score = results['percent_at_job']  # Base score is percentage at job
    
    # Bonus for assigned job match
    if results['assigned_job_match']:
        score += 20
    
    # Penalty for low location count
    if results['total_locations'] < 5:
        score -= (5 - results['total_locations']) * 5
    
    # Ensure score is between 0-100
    results['validation_score'] = max(0, min(100, score))
    
    return results


def get_job_site_geofence(job_number, address=None, lat=None, lon=None, radius_km=0.5):
    """
    Create a geofence for a job site using provided coordinates or by geocoding address

    Args:
        job_number (str): Job number
        address (str, optional): Job site address
        lat (float, optional): Latitude
        lon (float, optional): Longitude
        radius_km (float, optional): Radius in kilometers

    Returns:
        dict: Geofence data
    """
    # Create from direct coordinates
    if lat is not None and lon is not None:
        return {
            'job_number': job_number,
            'geofence': {
                'center_lat': lat,
                'center_lon': lon,
                'radius_km': radius_km
            }
        }
    
    # Create from address via geocoding if we implement later
    elif address:
        # Here we would add geocoding API integration
        logger.warning("Geocoding from address not yet implemented")
        return None
    
    else:
        logger.warning("No coordinates or address provided for job site geofence")
        return None