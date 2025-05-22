"""
TRAXORA GENIUS CORE | Geographic Validator Agent

This agent validates job site references and geographic coordinates,
ensuring data integrity for location-based reporting.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from utils.jobsite_catalog_loader import validate_jobsite_reference, get_jobsite_by_number

# Configure logging
logger = logging.getLogger(__name__)

def validate_coordinates(lat: float, lng: float) -> Dict[str, Any]:
    """
    Validate if coordinates are within expected ranges for project areas
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        
    Returns:
        dict: Validation result containing valid status and metadata
    """
    # Basic bounds check for Texas region (approximate)
    TEXAS_LAT_MIN, TEXAS_LAT_MAX = 25.8, 36.5
    TEXAS_LNG_MIN, TEXAS_LNG_MAX = -106.6, -93.5
    
    # Check if coordinates are within Texas bounds
    is_in_texas = (
        TEXAS_LAT_MIN <= lat <= TEXAS_LAT_MAX and
        TEXAS_LNG_MIN <= lng <= TEXAS_LNG_MAX
    )
    
    # More precise checks could be added for specific work zones
    
    return {
        'valid': is_in_texas,
        'region': 'Texas' if is_in_texas else 'Out of Region',
        'confidence': 1.0 if is_in_texas else 0.0
    }

def validate_jobsite(jobsite_reference: str) -> Dict[str, Any]:
    """
    Validate a job site reference against the catalog
    
    Args:
        jobsite_reference (str): Job site reference (job number, description)
        
    Returns:
        dict: Validation result with job site metadata
    """
    # Use the jobsite catalog to validate the reference
    validation_result = validate_jobsite_reference(jobsite_reference)
    
    if validation_result['valid']:
        jobsite = validation_result['jobsite']
        return {
            'valid': True,
            'job_number': jobsite['job_number'],
            'description': jobsite['description'],
            'zone': jobsite.get('zone'),
            'division': jobsite.get('division'),
            'category': jobsite.get('category'),
            'confidence': validation_result['confidence'],
            'match_type': validation_result['match_type']
        }
    else:
        return {
            'valid': False,
            'reference': jobsite_reference,
            'reason': 'Job site not found in catalog',
            'confidence': 0.0
        }

def enrich_record_with_jobsite(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a record with job site metadata
    
    Args:
        record (dict): Record to enrich
        
    Returns:
        dict: Enriched record with job site metadata
    """
    # Copy the record to avoid modifying the original
    enriched = record.copy()
    
    # Try different fields that might contain jobsite references
    reference_fields = ['JobSite', 'jobsite', 'job_site', 'JobNumber', 'job_number', 'JobID']
    jobsite_reference = None
    
    # Find the first non-empty reference field
    for field in reference_fields:
        if field in record and record[field]:
            jobsite_reference = record[field]
            break
    
    if not jobsite_reference:
        # No job site reference found
        enriched['jobsite_validation'] = {
            'valid': False,
            'reason': 'No job site reference found'
        }
        return enriched
    
    # Validate the job site reference
    validation = validate_jobsite(jobsite_reference)
    
    # Add validation results to the record
    enriched['jobsite_validation'] = validation
    
    # If valid, add additional metadata
    if validation['valid']:
        enriched['normalized_job_number'] = validation['job_number']
        enriched['job_description'] = validation['description']
        enriched['division'] = validation.get('division')
        enriched['zone'] = validation.get('zone')
        enriched['category'] = validation.get('category')
    
    return enriched

def handle(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process a batch of records for geographic validation
    
    Args:
        data (list): List of records to validate
        
    Returns:
        dict: Processing results with validated records
    """
    validated_records = []
    invalid_records = []
    
    for record in data:
        # Enrich with jobsite information
        enriched = enrich_record_with_jobsite(record)
        
        # Check for coordinates if available
        lat = record.get('Latitude') or record.get('latitude')
        lng = record.get('Longitude') or record.get('longitude')
        
        if lat and lng:
            try:
                lat_float = float(lat)
                lng_float = float(lng)
                coord_validation = validate_coordinates(lat_float, lng_float)
                enriched['coordinate_validation'] = coord_validation
            except (ValueError, TypeError):
                enriched['coordinate_validation'] = {
                    'valid': False,
                    'reason': 'Invalid coordinate format'
                }
        
        # Determine if the record is valid overall
        is_valid = (
            enriched.get('jobsite_validation', {}).get('valid', False) or
            enriched.get('coordinate_validation', {}).get('valid', False)
        )
        
        if is_valid:
            validated_records.append(enriched)
        else:
            invalid_records.append(enriched)
    
    return {
        'validated_records': validated_records,
        'invalid_records': invalid_records,
        'total_records': len(data),
        'valid_count': len(validated_records),
        'invalid_count': len(invalid_records),
        'validation_rate': len(validated_records) / len(data) if data else 0
    }