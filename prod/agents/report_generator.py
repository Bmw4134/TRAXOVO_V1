"""
Report Generator Agent (Production Version)

This module handles report generation based on processed driver and location data.
Production version with optimized performance and strict validation.
"""
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_driver_report(driver_data, metrics=None, include_details=True):
    """
    Generate a comprehensive driver report with strict validation.
    
    Args:
        driver_data (list): List of classified driver data
        metrics (dict): Additional metrics to include in the report
        include_details (bool): Whether to include detailed records
        
    Returns:
        dict: Structured driver report
    """
    logger.debug(f"PROD: Generating driver report with {len(driver_data)} records")
    
    try:
        # Validate input data
        if not isinstance(driver_data, list):
            raise ValueError("Driver data must be a list")
            
        if not driver_data:
            logger.warning("PROD: Generating report with empty driver data")
            
        # Calculate report statistics
        total_drivers = len(driver_data)
        status_counts = {
            'on_time': 0,
            'late': 0,
            'early_end': 0,
            'not_on_job': 0,
            'unknown': 0,
            'error': 0
        }
        
        # Track data issues
        data_issues = []
        skipped_records = 0
        
        # Count statuses with strict validation
        for i, driver in enumerate(driver_data):
            # Validate driver record structure
            if not isinstance(driver, dict):
                data_issues.append(f"Record {i} is not a dictionary")
                skipped_records += 1
                continue
                
            # Check for required fields
            if 'name' not in driver:
                data_issues.append(f"Record {i} missing required field: name")
                
            if 'status' not in driver:
                data_issues.append(f"Record {i} missing required field: status")
                status_counts['unknown'] += 1
            else:
                status = driver.get('status')
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts['unknown'] += 1
                    data_issues.append(f"Record {i} has invalid status: {status}")
        
        # Calculate percentages
        status_percentages = {}
        for status, count in status_counts.items():
            if total_drivers > 0:
                status_percentages[status] = round((count / total_drivers) * 100)
            else:
                status_percentages[status] = 0
                
        # Include any additional metrics
        if metrics is None:
            metrics = {}
            
        # Calculate data quality score
        data_quality_score = 1.0
        if total_drivers > 0:
            data_quality_score = round(1.0 - (len(data_issues) / total_drivers), 2)
            data_quality_score = max(0.0, min(1.0, data_quality_score))
        
        # Create the report structure
        report = {
            'summary': {
                'total_drivers': total_drivers,
                'status_counts': status_counts,
                'status_percentages': status_percentages,
                'generation_time': datetime.now().isoformat(),
                'mode': 'production',
                'data_quality_score': data_quality_score,
                'skipped_records': skipped_records
            },
            'metrics': {
                **metrics,
                'processing_duration_ms': metrics.get('processing_duration_ms', 0),
            },
            'validation_status': 'GENIUS CORE Validated' if data_quality_score > 0.8 else 'VALIDATION WARNING'
        }
        
        # Optionally include the detailed driver records
        if include_details:
            # In production, strip out sensitive or debug metadata
            clean_records = []
            for driver in driver_data:
                if isinstance(driver, dict):
                    clean_record = {
                        'id': driver.get('id'),
                        'name': driver.get('name'),
                        'status': driver.get('status'),
                        'start_time': driver.get('start_time'),
                        'end_time': driver.get('end_time'),
                        'job_site': driver.get('job_site'),
                        'location_verified': driver.get('location_verified')
                    }
                    clean_records.append(clean_record)
            report['records'] = clean_records
            
        # Add data issues if any were found, but limit to first 100
        if data_issues:
            issue_count = len(data_issues)
            report['data_issues'] = {
                'count': issue_count,
                'sample': data_issues[:100] if issue_count > 100 else data_issues
            }
        
        logger.info(f"PROD: Driver report generated with {total_drivers} records and {skipped_records} skipped")
        return report
        
    except Exception as e:
        logger.error(f"PROD: Error generating driver report: {str(e)}")
        raise

def export_report_to_json(report, output_path):
    """
    Export report to a JSON file with production optimizations.
    
    Args:
        report (dict): The report data to export
        output_path (str): Path to save the JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate output path
        if not output_path.endswith('.json'):
            output_path += '.json'
            
        # In production mode, don't use indentation to save space
        with open(output_path, 'w') as f:
            json.dump(report, f)
        logger.info(f"PROD: Report exported to {output_path}")
        return True
    except Exception as e:
        logger.error(f"PROD: Error exporting report to JSON: {str(e)}")
        raise

def generate_jobsite_report(jobsite_data, driver_data=None, include_details=True):
    """
    Generate a comprehensive job site report.
    
    Args:
        jobsite_data (list): List of job site data
        driver_data (list): List of driver data for cross-reference
        include_details (bool): Whether to include detailed records
        
    Returns:
        dict: Structured job site report
    """
    logger.debug(f"PROD: Generating job site report with {len(jobsite_data)} sites")
    
    try:
        # Validate input data
        if not isinstance(jobsite_data, list):
            raise ValueError("Job site data must be a list")
            
        if driver_data is not None and not isinstance(driver_data, list):
            raise ValueError("Driver data must be a list")
            
        if not jobsite_data:
            logger.warning("PROD: Generating report with empty job site data")
            
        # Calculate report statistics
        total_sites = len(jobsite_data)
        total_drivers = sum(site.get('driver_count', 0) for site in jobsite_data if isinstance(site, dict))
        
        # Track data issues
        data_issues = []
        skipped_records = 0
        
        # Cross-reference with driver data if available
        if driver_data:
            # Validate driver data
            for i, driver in enumerate(driver_data):
                if not isinstance(driver, dict):
                    data_issues.append(f"Driver record {i} is not a dictionary")
                    skipped_records += 1
                    
            # Group drivers by job site
            drivers_by_site = {}
            for driver in driver_data:
                if isinstance(driver, dict):
                    site = driver.get('job_site', 'Unknown')
                    if site not in drivers_by_site:
                        drivers_by_site[site] = []
                    drivers_by_site[site].append(driver)
                
            # Enhance job site data with driver information
            for i, site in enumerate(jobsite_data):
                if not isinstance(site, dict):
                    data_issues.append(f"Job site record {i} is not a dictionary")
                    skipped_records += 1
                    continue
                    
                site_name = site.get('name', 'Unknown')
                site_drivers = drivers_by_site.get(site_name, [])
                
                # Add driver stats to site data
                if include_details:
                    # In production, include only essential driver fields
                    clean_drivers = []
                    for driver in site_drivers:
                        clean_driver = {
                            'id': driver.get('id'),
                            'name': driver.get('name'),
                            'status': driver.get('status')
                        }
                        clean_drivers.append(clean_driver)
                    site['drivers'] = clean_drivers
                
                site['driver_statuses'] = {
                    'on_time': sum(1 for d in site_drivers if d.get('status') == 'on_time'),
                    'late': sum(1 for d in site_drivers if d.get('status') == 'late'),
                    'early_end': sum(1 for d in site_drivers if d.get('status') == 'early_end'),
                    'not_on_job': sum(1 for d in site_drivers if d.get('status') == 'not_on_job'),
                    'unknown': sum(1 for d in site_drivers if d.get('status') == 'unknown')
                }
        
        # Calculate data quality score
        data_quality_score = 1.0
        if total_sites > 0:
            data_quality_score = round(1.0 - (len(data_issues) / total_sites), 2)
            data_quality_score = max(0.0, min(1.0, data_quality_score))
                
        # Create the report structure
        report = {
            'summary': {
                'total_sites': total_sites,
                'total_drivers': total_drivers,
                'generation_time': datetime.now().isoformat(),
                'mode': 'production',
                'data_quality_score': data_quality_score,
                'skipped_records': skipped_records
            },
            'metrics': {
                'sites_with_drivers': sum(1 for site in jobsite_data 
                                         if isinstance(site, dict) and site.get('driver_count', 0) > 0),
                'avg_drivers_per_site': round(total_drivers / total_sites if total_sites > 0 else 0, 2)
            },
            'validation_status': 'GENIUS CORE Validated' if data_quality_score > 0.8 else 'VALIDATION WARNING'
        }
        
        # Optionally include the detailed job site records
        if include_details:
            # In production, include only essential job site fields
            clean_sites = []
            for site in jobsite_data:
                if isinstance(site, dict):
                    clean_site = {
                        'id': site.get('id'),
                        'name': site.get('name'),
                        'driver_count': site.get('driver_count', 0),
                        'on_time_count': site.get('on_time_count', 0),
                        'driver_statuses': site.get('driver_statuses', {})
                    }
                    # Include drivers if they were added
                    if 'drivers' in site:
                        clean_site['drivers'] = site['drivers']
                    clean_sites.append(clean_site)
            report['sites'] = clean_sites
            
        # Add data issues if any were found, but limit to first 100
        if data_issues:
            issue_count = len(data_issues)
            report['data_issues'] = {
                'count': issue_count,
                'sample': data_issues[:100] if issue_count > 100 else data_issues
            }
        
        logger.info(f"PROD: Job site report generated with {total_sites} sites and {skipped_records} skipped")
        return report
        
    except Exception as e:
        logger.error(f"PROD: Error generating job site report: {str(e)}")
        raise