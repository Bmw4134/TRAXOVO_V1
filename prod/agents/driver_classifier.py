"""
Driver Classifier Agent (Production Version)

This module handles driver classification based on their activity patterns.
Production version with strict validation and optimized performance.
"""
import logging

logger = logging.getLogger(__name__)

def classify_driver(driver_data, strict=True):
    """
    Classify a driver based on their activity data.
    
    Args:
        driver_data (dict): Driver activity data
        strict (bool): Whether to use strict validation rules (default True in production)
        
    Returns:
        dict: Classification results with status and metadata
    """
    logger.debug(f"PROD: Classifying driver")
    
    # Production mode enforces data quality
    try:
        # Validate required fields
        required_fields = ['name', 'start_time', 'end_time', 'job_site']
        for field in required_fields:
            if field not in driver_data or not driver_data[field]:
                if strict:
                    raise ValueError(f"Missing required field: {field}")
                # If not strict, continue with incomplete data
        
        driver_name = driver_data.get('name', 'Unknown Driver')
        start_time = driver_data.get('start_time', 'Unknown')
        end_time = driver_data.get('end_time', 'Unknown')
        job_site = driver_data.get('job_site', 'Unknown')
        
        # Strict classification logic for production
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
            'confidence': 0.95,  # Production version has higher confidence
            'source': 'prod_classifier',
            'metadata': {
                'processing_notes': 'Classified in production mode with strict validation',
                'strict_mode': strict,
                'dev_mode': False
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"PROD: Error classifying driver: {str(e)}")
        if strict:
            # In strict mode, propagate errors
            raise
        else:
            # In non-strict mode, return error result
            return {
                'name': driver_data.get('name', 'Unknown Driver'),
                'status': 'error',
                'error': str(e),
                'source': 'prod_classifier',
                'metadata': {
                    'processing_notes': f'Error in classification: {str(e)}',
                    'dev_mode': False
                }
            }

def batch_classify_drivers(drivers_data, strict=True):
    """
    Classify multiple drivers in a batch.
    
    Args:
        drivers_data (list): List of driver activity data dictionaries
        strict (bool): Whether to use strict validation rules
        
    Returns:
        list: List of classification results
    """
    logger.info(f"PROD: Batch classifying {len(drivers_data)} drivers")
    
    results = []
    error_count = 0
    max_errors = 10  # In production, limit errors before failing
    
    for driver_data in drivers_data:
        try:
            result = classify_driver(driver_data, strict)
            results.append(result)
        except Exception as e:
            error_count += 1
            logger.error(f"PROD: Error in batch classification for driver: {str(e)}")
            
            # In production strict mode, fail after too many errors
            if strict and error_count > max_errors:
                logger.critical(f"PROD: Exceeded maximum error threshold ({max_errors}), aborting batch")
                raise RuntimeError(f"Exceeded maximum error threshold: {error_count} errors")
            
            # Add error entry
            results.append({
                'name': driver_data.get('name', 'Unknown Driver'),
                'status': 'error',
                'error': str(e),
                'source': 'prod_classifier',
                'skipped': True
            })
    
    logger.info(f"PROD: Completed batch classification of {len(results)} drivers with {error_count} errors")
    return results