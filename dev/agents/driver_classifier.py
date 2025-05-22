"""
Driver Classifier Agent (Development Version)

This module handles driver classification based on their activity patterns.
Development version with verbose logging and relaxed validation.
"""
import logging

logger = logging.getLogger(__name__)

def classify_driver(driver_data, strict=False):
    """
    Classify a driver based on their activity data.
    
    Args:
        driver_data (dict): Driver activity data
        strict (bool): Whether to use strict validation rules
        
    Returns:
        dict: Classification results with status and metadata
    """
    logger.debug(f"DEV MODE: Classifying driver with data: {driver_data}")
    
    # Development mode has more detailed logging and more permissive parsing
    try:
        driver_name = driver_data.get('name', 'Unknown Driver')
        start_time = driver_data.get('start_time', 'Unknown')
        end_time = driver_data.get('end_time', 'Unknown')
        job_site = driver_data.get('job_site', 'Unknown')
        
        logger.info(f"DEV: Classifying driver '{driver_name}' with times {start_time}-{end_time} at {job_site}")
        
        # In dev mode, we allow partial data and make best effort classifications
        if not all([start_time, end_time, job_site]) and not strict:
            logger.warning(f"DEV: Incomplete driver data for {driver_name}, attempting classification anyway")
            
        # Simplified classification logic for development
        if start_time == 'Unknown' or end_time == 'Unknown':
            status = 'unknown'
        elif start_time > '08:00:00':
            status = 'late'
        elif end_time < '16:00:00':
            status = 'early_end'
        elif job_site == 'Unknown' or 'incorrect' in str(job_site).lower():
            status = 'not_on_job'
        else:
            status = 'on_time'
            
        result = {
            'name': driver_name,
            'status': status,
            'start_time': start_time,
            'end_time': end_time,
            'job_site': job_site,
            'confidence': 0.8,  # Development version has lower confidence
            'source': 'dev_classifier',
            'metadata': {
                'processing_notes': 'Classified in development mode with relaxed validation',
                'fallback_rules_applied': not strict,
                'dev_mode': True
            }
        }
        
        logger.debug(f"DEV: Classification result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"DEV: Error classifying driver: {str(e)}")
        # In dev mode, we return partial results even on error
        return {
            'name': driver_data.get('name', 'Unknown Driver'),
            'status': 'error',
            'error': str(e),
            'source': 'dev_classifier',
            'metadata': {
                'processing_notes': f'Error in classification: {str(e)}',
                'dev_mode': True
            }
        }

def batch_classify_drivers(drivers_data, strict=False):
    """
    Classify multiple drivers in a batch.
    
    Args:
        drivers_data (list): List of driver activity data dictionaries
        strict (bool): Whether to use strict validation rules
        
    Returns:
        list: List of classification results
    """
    logger.info(f"DEV: Batch classifying {len(drivers_data)} drivers")
    
    results = []
    for driver_data in drivers_data:
        try:
            result = classify_driver(driver_data, strict)
            results.append(result)
        except Exception as e:
            logger.error(f"DEV: Error in batch classification for driver: {str(e)}")
            # In dev mode, we continue processing despite errors
            results.append({
                'name': driver_data.get('name', 'Unknown Driver'),
                'status': 'error',
                'error': str(e),
                'source': 'dev_classifier',
                'skipped': True
            })
    
    logger.info(f"DEV: Completed batch classification of {len(results)} drivers")
    return results