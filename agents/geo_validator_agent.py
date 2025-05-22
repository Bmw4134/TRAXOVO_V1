"""
Geo Validator Agent

This agent validates driver and asset locations against job site boundaries
to determine if they are within the expected work areas.
"""
import logging
import json
import time
import math
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle(data, job_sites=None):
    """
    Validate locations of drivers/assets against job site boundaries
    
    Args:
        data (list/dict): Driver or asset location data to validate
        job_sites (list/dict): Job site data with boundaries
        
    Returns:
        dict: Validation results for each location
    """
    start_time = time.time()
    input_count = len(data) if isinstance(data, list) else 1
    logger.info(f"Geo Validator Agent processing {input_count} locations")
    
    # Process input data
    if not job_sites:
        logger.warning("No job site data provided for validation")
        return {"validated_locations": [], "validation_status": "error", "reason": "No job site data"}
    
    results = []
    if isinstance(data, list):
        for item in data:
            try:
                result = validate_location(item, job_sites)
                results.append(result)
            except Exception as e:
                logger.error(f"Error validating location: {e}")
                results.append({
                    "id": item.get("id", "unknown"),
                    "validated": False,
                    "error": str(e)
                })
    else:
        # Single item
        try:
            result = validate_location(data, job_sites)
            results.append(result)
        except Exception as e:
            logger.error(f"Error validating location: {e}")
            results.append({
                "id": data.get("id", "unknown"),
                "validated": False,
                "error": str(e)
            })
    
    processing_time = time.time() - start_time
    
    # Log usage
    log_usage(input_count, len(results), processing_time)
    
    return {
        "validated_locations": results,
        "validation_summary": {
            "total": len(results),
            "validated": sum(1 for r in results if r.get("validated", False)),
            "failed": sum(1 for r in results if not r.get("validated", False))
        }
    }

def run(data, job_sites=None):
    """Alias for handle() function"""
    return handle(data, job_sites)

def validate_location(location_data, job_sites):
    """
    Validate a single location against job sites
    
    Args:
        location_data (dict): Location data with lat/long
        job_sites (list/dict): Job site reference data
        
    Returns:
        dict: Validation result
    """
    result = {
        "id": location_data.get("id", "unknown"),
        "driver_id": location_data.get("driver_id"),
        "asset_id": location_data.get("asset_id"),
        "job_site_id": location_data.get("job_site_id"),
        "validated": False,
        "distance": None,
        "validation_time": datetime.now().isoformat()
    }
    
    # Extract location coordinates
    lat = location_data.get("latitude") or location_data.get("lat")
    lng = location_data.get("longitude") or location_data.get("lng") or location_data.get("lon")
    
    if not lat or not lng:
        result["reason"] = "Missing latitude/longitude"
        return result
        
    # Format job sites for processing
    job_site_list = []
    if isinstance(job_sites, dict):
        job_site_list = list(job_sites.values())
    elif isinstance(job_sites, list):
        job_site_list = job_sites
    else:
        result["reason"] = "Invalid job site data format"
        return result
        
    # Find the nearest job site for validation
    target_job_site = None
    min_distance = float('inf')
    
    for site in job_site_list:
        site_lat = site.get("latitude") or site.get("lat")
        site_lng = site.get("longitude") or site.get("lng") or site.get("lon")
        site_id = site.get("id") or site.get("job_site_id")
        
        if not site_lat or not site_lng:
            continue
            
        # If job_site_id is specified, only validate against that site
        if result["job_site_id"] and str(result["job_site_id"]) != str(site_id):
            continue
            
        distance = calculate_distance(float(lat), float(lng), float(site_lat), float(site_lng))
        
        if distance < min_distance:
            min_distance = distance
            target_job_site = site
    
    if not target_job_site:
        result["reason"] = "No matching job site found"
        return result
        
    # Get validation radius (default to 200 meters if not specified)
    radius = target_job_site.get("radius", 200)
    
    # Validate if within radius
    if min_distance <= radius:
        result["validated"] = True
        result["matched_job_site"] = target_job_site.get("name") or target_job_site.get("id")
        result["matched_job_site_id"] = target_job_site.get("id")
        result["distance"] = round(min_distance, 2)
    else:
        result["reason"] = f"Outside job site radius by {round(min_distance - radius, 2)} meters"
        result["matched_job_site"] = target_job_site.get("name") or target_job_site.get("id")
        result["matched_job_site_id"] = target_job_site.get("id") 
        result["distance"] = round(min_distance, 2)
        
    return result

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points in meters using the Haversine formula
    
    Args:
        lat1 (float): Latitude of point 1
        lon1 (float): Longitude of point 1
        lat2 (float): Latitude of point 2
        lon2 (float): Longitude of point 2
        
    Returns:
        float: Distance in meters
    """
    # Earth radius in meters
    R = 6371000
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

def log_usage(input_count, output_count, processing_time):
    """
    Log agent usage statistics
    
    Args:
        input_count (int): Number of input records
        output_count (int): Number of output records
        processing_time (float): Processing time in seconds
    """
    usage_log = {
        "agent": "geo_validator",
        "timestamp": datetime.now().isoformat(),
        "input_count": input_count,
        "output_count": output_count,
        "processing_time": round(processing_time, 3),
        "records_per_second": round(input_count / processing_time, 2) if processing_time > 0 else 0
    }
    
    logger.info(f"Agent usage: {json.dumps(usage_log)}")
    
    # In a production environment, this could write to a database or external logging system
    try:
        with open("logs/agent_usage.log", "a") as f:
            f.write(json.dumps(usage_log) + "\n")
    except Exception as e:
        logger.warning(f"Could not write to agent usage log: {e}")

if __name__ == "__main__":
    # Example usage
    test_locations = [
        {"id": 1, "driver_id": 1, "latitude": 32.7767, "longitude": -96.7970, "job_site_id": 101},
        {"id": 2, "driver_id": 2, "latitude": 32.7957, "longitude": -96.8089, "job_site_id": 102}
    ]
    
    test_job_sites = [
        {"id": 101, "name": "Downtown Project", "latitude": 32.7767, "longitude": -96.7970, "radius": 300},
        {"id": 102, "name": "Uptown Project", "latitude": 32.8000, "longitude": -96.8000, "radius": 200}
    ]
    
    result = handle(test_locations, test_job_sites)
    print(json.dumps(result, indent=2))