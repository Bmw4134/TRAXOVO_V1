"""
Report Generator Agent (Development Version)

This module handles report generation based on processed driver and location data.
Development version with detailed logging and flexible report formats.
"""
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_driver_report(driver_data, metrics=None, include_details=True):
    """
    Generate a comprehensive driver report.
    
    Args:
        driver_data (list): List of classified driver data
        metrics (dict): Additional metrics to include in the report
        include_details (bool): Whether to include detailed records
        
    Returns:
        dict: Structured driver report
    """
    logger.debug(f"DEV MODE: Generating driver report with {len(driver_data)} records")
    
    try:
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
        
        # Count statuses
        for driver in driver_data:
            status = driver.get('status', 'unknown')
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts['unknown'] += 1
                
        # Calculate percentages (with safeguards for div by zero)
        status_percentages = {}
        for status, count in status_counts.items():
            if total_drivers > 0:
                status_percentages[status] = round((count / total_drivers) * 100)
            else:
                status_percentages[status] = 0
                
        # Include any additional metrics
        if metrics is None:
            metrics = {}
            
        # In development mode, include detailed processing notes
        processing_notes = [
            "Generated in development mode with enhanced debugging",
            f"Processed {total_drivers} driver records",
            f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        # Create the report structure
        report = {
            'summary': {
                'total_drivers': total_drivers,
                'status_counts': status_counts,
                'status_percentages': status_percentages,
                'generation_time': datetime.now().isoformat(),
                'mode': 'development'
            },
            'metrics': {
                **metrics,
                'processing_duration_ms': metrics.get('processing_duration_ms', 0),
                'data_quality_score': metrics.get('data_quality_score', 0.8)  # Dev has lower default score
            },
            'processing_notes': processing_notes,
            'validation_status': 'DEV MODE - Not Validated for Production',
        }
        
        # Optionally include the detailed driver records
        if include_details:
            # In dev mode, include all fields including debug metadata
            report['records'] = driver_data
        
        logger.info(f"DEV: Driver report generated with {total_drivers} records")
        return report
        
    except Exception as e:
        logger.error(f"DEV: Error generating driver report: {str(e)}")
        # In dev mode, return a partial report with error information
        return {
            'error': str(e),
            'summary': {
                'total_drivers': len(driver_data),
                'generation_time': datetime.now().isoformat(),
                'mode': 'development',
                'status': 'error'
            },
            'processing_notes': [f"Error during report generation: {str(e)}"],
            'validation_status': 'Failed - Error in processing'
        }

def export_report_to_json(report, output_path):
    """
    Export report to a JSON file.
    
    Args:
        report (dict): The report data to export
        output_path (str): Path to save the JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # In dev mode, format with indentation for readability
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"DEV: Report exported to {output_path}")
        return True
    except Exception as e:
        logger.error(f"DEV: Error exporting report to JSON: {str(e)}")
        return False

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
    logger.debug(f"DEV MODE: Generating job site report with {len(jobsite_data)} sites")
    
    try:
        # Calculate report statistics
        total_sites = len(jobsite_data)
        total_drivers = sum(site.get('driver_count', 0) for site in jobsite_data)
        
        # Cross-reference with driver data if available
        if driver_data:
            # Group drivers by job site
            drivers_by_site = {}
            for driver in driver_data:
                site = driver.get('job_site', 'Unknown')
                if site not in drivers_by_site:
                    drivers_by_site[site] = []
                drivers_by_site[site].append(driver)
                
            # Enhance job site data with driver information
            for site in jobsite_data:
                site_name = site.get('name', 'Unknown')
                site_drivers = drivers_by_site.get(site_name, [])
                
                # Add driver stats to site data
                site['drivers'] = site_drivers if include_details else len(site_drivers)
                site['driver_statuses'] = {
                    'on_time': sum(1 for d in site_drivers if d.get('status') == 'on_time'),
                    'late': sum(1 for d in site_drivers if d.get('status') == 'late'),
                    'early_end': sum(1 for d in site_drivers if d.get('status') == 'early_end'),
                    'not_on_job': sum(1 for d in site_drivers if d.get('status') == 'not_on_job'),
                    'unknown': sum(1 for d in site_drivers if d.get('status') == 'unknown')
                }
        
        # In development mode, include detailed processing notes
        processing_notes = [
            "Generated in development mode with enhanced debugging",
            f"Processed {total_sites} job sites with {total_drivers} drivers",
            f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        # Create the report structure
        report = {
            'summary': {
                'total_sites': total_sites,
                'total_drivers': total_drivers,
                'generation_time': datetime.now().isoformat(),
                'mode': 'development'
            },
            'metrics': {
                'sites_with_drivers': sum(1 for site in jobsite_data if site.get('driver_count', 0) > 0),
                'avg_drivers_per_site': round(total_drivers / total_sites if total_sites > 0 else 0, 2)
            },
            'processing_notes': processing_notes,
            'validation_status': 'DEV MODE - Not Validated for Production',
        }
        
        # Optionally include the detailed job site records
        if include_details:
            # In dev mode, include all fields including debug metadata
            report['sites'] = jobsite_data
        
        logger.info(f"DEV: Job site report generated with {total_sites} sites")
        return report
        
    except Exception as e:
        logger.error(f"DEV: Error generating job site report: {str(e)}")
        # In dev mode, return a partial report with error information
        return {
            'error': str(e),
            'summary': {
                'total_sites': len(jobsite_data),
                'generation_time': datetime.now().isoformat(),
                'mode': 'development',
                'status': 'error'
            },
            'processing_notes': [f"Error during report generation: {str(e)}"],
            'validation_status': 'Failed - Error in processing'
        }