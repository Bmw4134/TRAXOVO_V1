"""
Geo Validator Agent (Production Version)

This module handles GPS location validation and job site verification.
Production version with strict validation and optimized performance.
"""
import logging
import math

logger = logging.getLogger(__name__)

def validate_location(location_data, job_site_data, strict=True):
    """
    Validate a driver's GPS location against expected job site coordinates.
    
    Args:
        location_data (dict): Driver's GPS location data
        job_site_data (dict): Expected job site location data
        strict (bool): Whether to use strict validation rules
        
    Returns:
        dict: Validation results with status and confidence score
    """
    logger.debug(f"PROD: Validating location")
    
    try:
        # In production, we require complete coordinates for validation
        required_fields = ['latitude', 'longitude']
        
        # Validate required location fields
        for field in required_fields:
            if field not in location_data or location_data[field] is None:
                if strict:
                    raise ValueError(f"Missing required location field: {field}")
                else:
                    logger.warning(f"PROD: Missing location field: {field}")
                    
        # Validate required job site fields
        for field in required_fields + ['radius']:
            if field not in job_site_data or job_site_data[field] is None:
                if strict:
                    raise ValueError(f"Missing required job site field: {field}")
                else:
                    logger.warning(f"PROD: Missing job site field: {field}")
                    
        # Extract location coordinates
        driver_lat = location_data.get('latitude')
        driver_lon = location_data.get('longitude')
        job_lat = job_site_data.get('latitude')
        job_lon = job_site_data.get('longitude')
        job_radius = job_site_data.get('radius', 200)  # Default 200m radius (stricter in prod)
        
        if all([driver_lat, driver_lon, job_lat, job_lon]):
            # Calculate distance using haversine formula for more accuracy in production
            R = 6371000  # Earth radius in meters
            lat1, lon1 = math.radians(driver_lat), math.radians(driver_lon)
            lat2, lon2 = math.radians(job_lat), math.radians(job_lon)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            
            is_valid = distance <= job_radius
            
            # Scale confidence based on distance from perimeter
            if is_valid:
                confidence = 1.0 - (distance / job_radius) * 0.1  # At perimeter, confidence is 0.9
            else:
                confidence = max(0, 0.5 - (distance - job_radius) / 2000)  # Faster decay with distance
        else:
            # In production, missing coordinates with non-strict mode means low confidence
            is_valid = False
            confidence = 0.0
            distance = None
            
        validation_result = {
            'is_valid': is_valid,
            'confidence': confidence,
            'distance_meters': distance,
            'job_site': job_site_data.get('name', 'Unknown'),
            'location_description': location_data.get('description', ''),
            'source': 'prod_geo_validator',
            'metadata': {
                'processing_notes': 'Validated in production mode with strict rules',
                'validation_method': 'haversine' if all([driver_lat, driver_lon, job_lat, job_lon]) else 'fallback',
                'dev_mode': False
            }
        }
        
        return validation_result
        
    except Exception as e:
        logger.error(f"PROD: Error validating location: {str(e)}")
        if strict:
            # In strict mode, propagate errors
            raise
        else:
            # In non-strict mode, return error result
            return {
                'is_valid': False,
                'confidence': 0.0,
                'error': str(e),
                'source': 'prod_geo_validator',
                'metadata': {
                    'processing_notes': f'Error in validation: {str(e)}',
                    'dev_mode': False
                }
            }

def batch_validate_locations(locations_data, job_sites_data, strict=True):
    """
    Validate multiple locations in a batch.
    
    Args:
        locations_data (list): List of location data dictionaries
        job_sites_data (dict): Dictionary of job site data, keyed by job site name
        strict (bool): Whether to use strict validation rules
        
    Returns:
        list: List of validation results
    """
    logger.info(f"PROD: Batch validating {len(locations_data)} locations")
    
    results = []
    error_count = 0
    max_errors = 5  # In production, limit errors before failing
    
    for location in locations_data:
        try:
            # Find matching job site
            job_site_name = location.get('job_site')
            
            if not job_site_name:
                if strict:
                    raise ValueError("Missing job site name in location data")
                else:
                    logger.warning("PROD: Missing job site name, using default")
                    job_site_name = "Unknown"
                    
            job_site = job_sites_data.get(job_site_name)
            
            if not job_site:
                if strict:
                    raise ValueError(f"No job site data found for {job_site_name}")
                else:
                    logger.warning(f"PROD: No job site data found for {job_site_name}, using default values")
                    job_site = {
                        'name': job_site_name,
                        'latitude': 0.0,
                        'longitude': 0.0,
                        'radius': 200  # Smaller default radius for prod mode
                    }
            
            result = validate_location(location, job_site, strict)
            results.append(result)
        except Exception as e:
            error_count += 1
            logger.error(f"PROD: Error in batch validation for location: {str(e)}")
            
            # In production strict mode, fail after too many errors
            if strict and error_count > max_errors:
                logger.critical(f"PROD: Exceeded maximum error threshold ({max_errors}), aborting batch")
                raise RuntimeError(f"Exceeded maximum error threshold: {error_count} errors")
            
            # Add error entry
            results.append({
                'job_site': location.get('job_site', 'Unknown'),
                'is_valid': False,
                'confidence': 0.0,
                'error': str(e),
                'source': 'prod_geo_validator',
                'skipped': True
            })
    
    logger.info(f"PROD: Completed batch validation of {len(results)} locations with {error_count} errors")
    return results