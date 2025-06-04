"""
TRAXORA | Jobsite Catalog Loader

This module loads and processes the jobsite catalog data,
providing functions for retrieving and validating job site information.
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

# Cache for jobsite catalog
_jobsite_catalog = None

def load_jobsite_catalog(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load the jobsite catalog from a JSON file.
    Uses cached data if available, unless force_reload is True.
    
    Args:
        file_path (str, optional): Path to the jobsite catalog file.
                                  If None, uses the default path.
                                  
    Returns:
        list: List of jobsite catalog entries
    """
    global _jobsite_catalog
    
    # Return cached catalog if available
    if _jobsite_catalog is not None:
        return _jobsite_catalog
    
    # Use default path if not specified
    if file_path is None:
        # Look in several possible locations
        possible_paths = [
            os.path.join(os.getcwd(), 'data', 'traxora_jobsite_catalog_v2.json'),
            os.path.join(os.getcwd(), 'traxora_jobsite_catalog_v2.json'),
            os.path.join(os.getcwd(), 'attached_assets', 'traxora_jobsite_catalog_v2.json')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break
                
        if file_path is None:
            logger.error("Jobsite catalog file not found in default locations")
            return []
    
    try:
        # Load jobsite catalog from file
        with open(file_path, 'r') as f:
            catalog = json.load(f)
        
        # Cache catalog for future use
        _jobsite_catalog = catalog
        
        logger.info(f"Loaded {len(catalog)} jobsite entries from catalog")
        return catalog
    
    except Exception as e:
        logger.error(f"Error loading jobsite catalog: {str(e)}")
        return []

def get_jobsite_by_number(job_number: str) -> Optional[Dict[str, Any]]:
    """
    Get a jobsite entry by job number
    
    Args:
        job_number (str): Job number to search for
        
    Returns:
        dict: Jobsite entry or None if not found
    """
    # Ensure catalog is loaded
    catalog = load_jobsite_catalog()
    
    # Normalize job number for comparison
    normalized_job_number = normalize_job_number(job_number)
    
    # Look for matching job number
    for jobsite in catalog:
        if normalize_job_number(jobsite['job_number']) == normalized_job_number:
            return jobsite
    
    return None

def get_jobsites_by_division(division: str) -> List[Dict[str, Any]]:
    """
    Get all jobsite entries for a specific division
    
    Args:
        division (str): Division to filter by
        
    Returns:
        list: List of matching jobsite entries
    """
    # Ensure catalog is loaded
    catalog = load_jobsite_catalog()
    
    # Filter by division (case insensitive)
    return [
        jobsite for jobsite in catalog 
        if jobsite.get('division', '').lower() == division.lower()
    ]

def normalize_job_number(job_number: str) -> str:
    """
    Normalize job number for consistent comparison
    
    Args:
        job_number (str): Job number to normalize
        
    Returns:
        str: Normalized job number
    """
    if not job_number:
        return ""
    
    # Convert to string, strip whitespace, and convert to lowercase
    job_number = str(job_number).strip().lower()
    
    # Remove any non-alphanumeric characters except dash
    job_number = ''.join(c for c in job_number if c.isalnum() or c == '-')
    
    return job_number

def validate_jobsite_reference(reference: str) -> Dict[str, Any]:
    """
    Validate a jobsite reference and return information about the jobsite
    
    Args:
        reference (str): Jobsite reference (job number, description, etc.)
        
    Returns:
        dict: Validation result containing:
            - valid (bool): Whether the jobsite is valid
            - jobsite (dict): Jobsite entry if valid, None otherwise
            - confidence (float): Confidence score for the match (0-1)
    """
    # Ensure catalog is loaded
    catalog = load_jobsite_catalog()
    
    # Try exact match by job number first
    jobsite = get_jobsite_by_number(reference)
    if jobsite:
        return {
            'valid': True,
            'jobsite': jobsite,
            'confidence': 1.0,
            'match_type': 'exact_job_number'
        }
    
    # Try fuzzy matching by description
    from fuzzywuzzy import process
    descriptions = {jobsite['description']: jobsite for jobsite in catalog}
    
    if descriptions:
        match, score = process.extractOne(reference, descriptions.keys())
        
        # Consider it a match if score is above threshold
        if score >= 70:
            return {
                'valid': True,
                'jobsite': descriptions[match],
                'confidence': score / 100.0,
                'match_type': 'fuzzy_description'
            }
    
    # No match found
    return {
        'valid': False,
        'jobsite': None,
        'confidence': 0.0,
        'match_type': 'no_match'
    }

def get_all_divisions() -> List[str]:
    """
    Get a list of all unique divisions in the jobsite catalog
    
    Returns:
        list: List of division names
    """
    # Ensure catalog is loaded
    catalog = load_jobsite_catalog()
    
    # Extract unique divisions
    divisions = set()
    for jobsite in catalog:
        if 'division' in jobsite and jobsite['division']:
            divisions.add(jobsite['division'])
    
    return sorted(list(divisions))

def get_all_categories() -> List[str]:
    """
    Get a list of all unique categories in the jobsite catalog
    
    Returns:
        list: List of category names
    """
    # Ensure catalog is loaded
    catalog = load_jobsite_catalog()
    
    # Extract unique categories
    categories = set()
    for jobsite in catalog:
        if 'category' in jobsite and jobsite['category']:
            categories.add(jobsite['category'])
    
    return sorted(list(categories))

# Initialize catalog on module import
load_jobsite_catalog()