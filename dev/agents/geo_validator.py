"""
Geo Validator Agent (Development Version)

This module handles GPS location validation and job site verification.
Development version with verbose logging and relaxed validation.
"""
import logging
import time

logger = logging.getLogger(__name__)

def validate_location(location_data, job_site_data, strict=False):
    """
    Validate a driver's GPS location against expected job site coordinates.
    
    Args:
        location_data (dict): Driver's GPS location data
        job_site_data (dict): Expected job site location data
        strict (bool): Whether to use strict validation rules
        
    Returns:
        dict: Validation results with status and confidence score
    """
    logger.debug(f"DEV MODE: Validating location with data: {location_data}")
    
    try:
        # Extract location coordinates
        driver_lat = location_data.get('latitude')
        driver_lon = location_data.get('longitude')
        job_lat = job_site_data.get('latitude')
        job_lon = job_site_data.get('longitude')
        job_radius = job_site_data.get('radius', 500)  # Default 500m radius
        
        # In development mode, we handle missing coordinates gracefully
        if not all([driver_lat, driver_lon, job_lat, job_lon]):
            logger.warning("DEV: Incomplete location coordinates, using relaxed validation")
            
            # If coordinates are missing but strict is False, make a best guess
            if not strict:
                is_valid = location_data.get('job_site') == job_site_data.get('name')
                confidence = 0.5  # Lower confidence due to missing data
            else:
                is_valid = False
                confidence = 0.0
        else:
            # Calculate distance between points (simplified)
            # In a real implementation, this would use the haversine formula
            distance = ((driver_lat - job_lat) ** 2 + (driver_lon - job_lon) ** 2) ** 0.5 * 111000  # Approx meters
            
            is_valid = distance <= job_radius
            # Scale confidence based on distance from perimeter
            if is_valid:
                confidence = 1.0 - (distance / job_radius) * 0.2  # At perimeter, confidence is 0.8
            else:
                confidence = max(0, 0.7 - (distance - job_radius) / 1000)  # Decay with distance
            
        validation_result = {
            'is_valid': is_valid,
            'confidence': confidence,
            'distance_meters': locals().get('distance', 'unknown'),
            'job_site': job_site_data.get('name', 'Unknown'),
            'location_description': location_data.get('description', ''),
            'source': 'dev_geo_validator',
            'metadata': {
                'processing_notes': 'Validated in development mode with relaxed rules',
                'missing_coordinates': not all([driver_lat, driver_lon, job_lat, job_lon]),
                'dev_mode': True
            }
        }
        
        logger.debug(f"DEV: Location validation result: {validation_result}")
        return validation_result
        
    except Exception as e:
        logger.error(f"DEV: Error validating location: {str(e)}")
        # In dev mode, return partial results on error
        return {
            'is_valid': False,
            'confidence': 0.0,
            'error': str(e),
            'source': 'dev_geo_validator',
            'metadata': {
                'processing_notes': f'Error in validation: {str(e)}',
                'dev_mode': True
            }
        }

def batch_validate_locations(locations_data, job_sites_data, strict=False):
    """
    Validate multiple locations in a batch.
    
    Args:
        locations_data (list): List of location data dictionaries
        job_sites_data (dict): Dictionary of job site data, keyed by job site name
        strict (bool): Whether to use strict validation rules
        
    Returns:
        list: List of validation results
    """
    logger.info(f"DEV: Batch validating {len(locations_data)} locations")
    
    results = []
    for location in locations_data:
        try:
            # Find matching job site
            job_site_name = location.get('job_site')
            job_site = job_sites_data.get(job_site_name, {})
            
            if not job_site and not strict:
                logger.warning(f"DEV: No job site data found for {job_site_name}, using default values")
                job_site = {
                    'name': job_site_name,
                    'latitude': 0.0,
                    'longitude': 0.0,
                    'radius': 1000  # Larger default radius for dev mode
                }
                
            # Add artificial delay in dev mode to simulate processing
            time.sleep(0.01)
            
            result = validate_location(location, job_site, strict)
            results.append(result)
        except Exception as e:
            logger.error(f"DEV: Error in batch validation for location: {str(e)}")
            # In dev mode, continue despite errors
            results.append({
                'job_site': location.get('job_site', 'Unknown'),
                'is_valid': False,
                'confidence': 0.0,
                'error': str(e),
                'source': 'dev_geo_validator',
                'skipped': True
            })
    
    logger.info(f"DEV: Completed batch validation of {len(results)} locations")
    return results