"""
Report Generator Agent

This agent generates comprehensive reports from processed driver and location data,
with configurable formats, metrics, and detail levels.
"""
import logging
import json
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle(data, config=None):
    """
    Generate reports from processed data
    
    Args:
        data (dict): Processed data including driver and location information
        config (dict): Report configuration options
        
    Returns:
        dict: Structured report data
    """
    start_time = time.time()
    logger.info("Report Generator Agent starting report generation")
    
    # Set defaults for configuration
    if not config:
        config = {}
    
    report_type = config.get('report_type', 'standard')
    include_details = config.get('include_details', True)
    filter_zeros = config.get('filter_zeros', True)
    max_items = config.get('max_items', 1000)
    
    # Extract data components
    drivers_data = data.get('drivers', {})
    job_sites_data = data.get('job_sites', {})
    validation_data = data.get('validation', {})
    
    # Convert to lists if they are dictionaries
    if isinstance(drivers_data, dict):
        drivers_data = list(drivers_data.values())
    if isinstance(job_sites_data, dict):
        job_sites_data = list(job_sites_data.values())
    
    # Generate report based on type
    report = {}
    if report_type == 'driver':
        report = generate_driver_report(drivers_data, include_details, filter_zeros, max_items)
    elif report_type == 'jobsite':
        report = generate_job_site_report(job_sites_data, include_details, filter_zeros, max_items)
    elif report_type == 'compliance':
        report = generate_compliance_report(drivers_data, job_sites_data, validation_data, include_details)
    else:  # standard report
        report = generate_standard_report(drivers_data, job_sites_data, validation_data, include_details, filter_zeros, max_items)
    
    # Add metadata
    report['metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'report_type': report_type,
        'report_version': '1.0',
        'data_sources': data.get('data_sources', []),
        'filter_config': {
            'include_details': include_details,
            'filter_zeros': filter_zeros,
            'max_items': max_items
        }
    }
    
    processing_time = time.time() - start_time
    report['metadata']['processing_time'] = round(processing_time, 3)
    
    # Log usage
    log_usage(
        len(drivers_data) if isinstance(drivers_data, list) else 0,
        len(job_sites_data) if isinstance(job_sites_data, list) else 0,
        report_type,
        processing_time
    )
    
    return report

def run(data, config=None):
    """Alias for handle() function"""
    return handle(data, config)

def generate_driver_report(drivers_data, include_details=True, filter_zeros=True, max_items=1000):
    """
    Generate a comprehensive driver report
    
    Args:
        drivers_data (list): List of driver data
        include_details (bool): Whether to include detailed records
        filter_zeros (bool): Whether to filter out zero-value records
        max_items (int): Maximum items to include
        
    Returns:
        dict: Structured driver report
    """
    if not drivers_data:
        return {'drivers': [], 'summary': {'total_drivers': 0}}
    
    # Filter and limit data if needed
    filtered_data = drivers_data
    if filter_zeros:
        # Example: filter out drivers without job sites or activity
        filtered_data = [d for d in filtered_data if d.get('job_site')]
    
    # Limit to max items
    limited_data = filtered_data[:max_items] if len(filtered_data) > max_items else filtered_data
    
    # Generate driver summary
    driver_count = len(limited_data)
    on_time_count = sum(1 for d in limited_data if d.get('status') == 'on_time')
    late_count = sum(1 for d in limited_data if d.get('status') == 'late')
    early_end_count = sum(1 for d in limited_data if d.get('status') == 'early_end')
    not_on_job_count = sum(1 for d in limited_data if d.get('status') == 'not_on_job')
    
    # Calculate percentages
    on_time_percent = round((on_time_count / driver_count * 100) if driver_count > 0 else 0)
    late_percent = round((late_count / driver_count * 100) if driver_count > 0 else 0)
    early_end_percent = round((early_end_count / driver_count * 100) if driver_count > 0 else 0)
    not_on_job_percent = round((not_on_job_count / driver_count * 100) if driver_count > 0 else 0)
    
    # Build report
    report = {
        'summary': {
            'total_drivers': driver_count,
            'on_time_count': on_time_count,
            'on_time_percent': on_time_percent,
            'late_count': late_count,
            'late_percent': late_percent,
            'early_end_count': early_end_count,
            'early_end_percent': early_end_percent,
            'not_on_job_count': not_on_job_count,
            'not_on_job_percent': not_on_job_percent,
            'overall_compliance': on_time_percent
        }
    }
    
    # Include detail records if requested
    if include_details:
        # Remove large data fields to keep report manageable
        report['drivers'] = []
        for driver in limited_data:
            driver_record = {k: v for k, v in driver.items() if k not in ['raw_data', 'evidence', 'logs']}
            report['drivers'].append(driver_record)
    
    # Include truncation info if data was limited
    if len(filtered_data) > max_items:
        report['truncated'] = {
            'original_count': len(drivers_data),
            'filtered_count': len(filtered_data),
            'displayed_count': len(limited_data),
            'truncated_count': len(filtered_data) - max_items
        }
    
    return report

def generate_job_site_report(job_sites_data, include_details=True, filter_zeros=True, max_items=1000):
    """
    Generate a comprehensive job site report
    
    Args:
        job_sites_data (list): List of job site data
        include_details (bool): Whether to include detailed records
        filter_zeros (bool): Whether to filter out zero-value records
        max_items (int): Maximum items to include
        
    Returns:
        dict: Structured job site report
    """
    if not job_sites_data:
        return {'job_sites': [], 'summary': {'total_job_sites': 0}}
    
    # Filter and limit data if needed
    filtered_data = job_sites_data
    if filter_zeros:
        # Example: filter out job sites without drivers
        filtered_data = [js for js in filtered_data if js.get('driver_count', 0) > 0]
    
    # Limit to max items
    limited_data = filtered_data[:max_items] if len(filtered_data) > max_items else filtered_data
    
    # Generate job site summary
    job_site_count = len(limited_data)
    total_drivers = sum(js.get('driver_count', 0) for js in limited_data)
    total_on_time = sum(js.get('on_time_count', 0) for js in limited_data)
    
    # Calculate compliance rate
    compliance_rate = round((total_on_time / total_drivers * 100) if total_drivers > 0 else 0)
    
    # Build report
    report = {
        'summary': {
            'total_job_sites': job_site_count,
            'total_drivers': total_drivers,
            'total_on_time': total_on_time,
            'compliance_rate': compliance_rate
        }
    }
    
    # Include detail records if requested
    if include_details:
        # Remove large data fields to keep report manageable
        report['job_sites'] = []
        for job_site in limited_data:
            js_record = {k: v for k, v in job_site.items() if k not in ['raw_data', 'coordinates', 'boundaries']}
            
            # Calculate job site compliance rate
            js_record['compliance_rate'] = round(
                (js_record.get('on_time_count', 0) / js_record.get('driver_count', 1) * 100) 
                if js_record.get('driver_count', 0) > 0 else 0
            )
            
            report['job_sites'].append(js_record)
    
    # Include truncation info if data was limited
    if len(filtered_data) > max_items:
        report['truncated'] = {
            'original_count': len(job_sites_data),
            'filtered_count': len(filtered_data),
            'displayed_count': len(limited_data),
            'truncated_count': len(filtered_data) - max_items
        }
    
    return report

def generate_compliance_report(drivers_data, job_sites_data, validation_data, include_details=True):
    """
    Generate a comprehensive compliance report
    
    Args:
        drivers_data (list): List of driver data
        job_sites_data (list): List of job site data
        validation_data (dict): Validation results data
        include_details (bool): Whether to include detailed records
        
    Returns:
        dict: Structured compliance report
    """
    # This is a specialized report that combines driver, job site, and validation data
    if not drivers_data or not job_sites_data:
        return {
            'compliance': {'overall_score': 0},
            'drivers': [],
            'job_sites': [],
            'summary': {'status': 'insufficient_data'}
        }
    
    # Calculate overall compliance
    driver_count = len(drivers_data)
    on_time_count = sum(1 for d in drivers_data if d.get('status') == 'on_time')
    on_time_percent = round((on_time_count / driver_count * 100) if driver_count > 0 else 0)
    
    # Calculate location compliance
    location_validated_count = sum(1 for d in drivers_data if d.get('location_verified', False))
    location_compliance = round((location_validated_count / driver_count * 100) if driver_count > 0 else 0)
    
    # Calculate job site compliance
    job_site_count = len(job_sites_data)
    compliant_sites = sum(1 for js in job_sites_data if 
                           (js.get('on_time_count', 0) / js.get('driver_count', 1) >= 0.8 
                           if js.get('driver_count', 0) > 0 else False))
    site_compliance = round((compliant_sites / job_site_count * 100) if job_site_count > 0 else 0)
    
    # Overall compliance score is a weighted average of time, location, and site compliance
    overall_score = round(on_time_percent * 0.4 + location_compliance * 0.4 + site_compliance * 0.2)
    
    # Build report
    report = {
        'compliance': {
            'overall_score': overall_score,
            'time_compliance': on_time_percent,
            'location_compliance': location_compliance,
            'job_site_compliance': site_compliance,
            'compliance_level': get_compliance_level(overall_score)
        },
        'summary': {
            'total_drivers': driver_count,
            'on_time_drivers': on_time_count,
            'location_verified_drivers': location_validated_count,
            'total_job_sites': job_site_count,
            'compliant_job_sites': compliant_sites
        }
    }
    
    # Include details if requested
    if include_details:
        # Include top 5 most and least compliant job sites
        sorted_sites = sorted(job_sites_data, key=lambda x: 
                             (x.get('on_time_count', 0) / x.get('driver_count', 1)) 
                             if x.get('driver_count', 0) > 0 else 0, 
                             reverse=True)
        
        report['top_job_sites'] = [
            {
                'name': site.get('name', 'Unknown'),
                'driver_count': site.get('driver_count', 0),
                'on_time_count': site.get('on_time_count', 0),
                'compliance_rate': round(
                    (site.get('on_time_count', 0) / site.get('driver_count', 1) * 100) 
                    if site.get('driver_count', 0) > 0 else 0
                )
            }
            for site in sorted_sites[:5] if site.get('driver_count', 0) > 0
        ]
        
        report['bottom_job_sites'] = [
            {
                'name': site.get('name', 'Unknown'),
                'driver_count': site.get('driver_count', 0),
                'on_time_count': site.get('on_time_count', 0),
                'compliance_rate': round(
                    (site.get('on_time_count', 0) / site.get('driver_count', 1) * 100) 
                    if site.get('driver_count', 0) > 0 else 0
                )
            }
            for site in sorted_sites[-5:] if site.get('driver_count', 0) > 0
        ]
        report['bottom_job_sites'].reverse()  # Show the worst first
    
    return report

def generate_standard_report(drivers_data, job_sites_data, validation_data, include_details=True, filter_zeros=True, max_items=1000):
    """
    Generate a standard comprehensive report with driver and job site data
    
    Args:
        drivers_data (list): List of driver data
        job_sites_data (list): List of job site data
        validation_data (dict): Validation results data
        include_details (bool): Whether to include detailed records
        filter_zeros (bool): Whether to filter out zero-value records
        max_items (int): Maximum items to include
        
    Returns:
        dict: Structured standard report
    """
    # Generate individual reports
    driver_report = generate_driver_report(drivers_data, include_details, filter_zeros, max_items)
    job_site_report = generate_job_site_report(job_sites_data, include_details, filter_zeros, max_items)
    
    # Combine the reports
    standard_report = {
        'driver_summary': driver_report['summary'],
        'job_site_summary': job_site_report['summary']
    }
    
    # Add overall metrics
    if driver_report['summary']['total_drivers'] > 0:
        standard_report['overall'] = {
            'compliance_score': driver_report['summary']['on_time_percent'],
            'driver_count': driver_report['summary']['total_drivers'],
            'job_site_count': job_site_report['summary']['total_job_sites'],
            'compliance_level': get_compliance_level(driver_report['summary']['on_time_percent'])
        }
    else:
        standard_report['overall'] = {
            'compliance_score': 0,
            'driver_count': 0,
            'job_site_count': 0,
            'compliance_level': 'insufficient_data'
        }
    
    # Include details if requested
    if include_details:
        if 'drivers' in driver_report:
            standard_report['drivers'] = driver_report['drivers']
        if 'job_sites' in job_site_report:
            standard_report['job_sites'] = job_site_report['job_sites']
    
    # Include truncation info if available
    if 'truncated' in driver_report:
        standard_report['driver_truncation'] = driver_report['truncated']
    if 'truncated' in job_site_report:
        standard_report['job_site_truncation'] = job_site_report['truncated']
    
    return standard_report

def get_compliance_level(score):
    """
    Determine compliance level based on score
    
    Args:
        score (int): Compliance score (0-100)
        
    Returns:
        str: Compliance level
    """
    if score >= 90:
        return 'excellent'
    elif score >= 80:
        return 'good'
    elif score >= 70:
        return 'satisfactory'
    elif score >= 60:
        return 'needs_improvement'
    elif score > 0:
        return 'critical'
    else:
        return 'insufficient_data'

def log_usage(driver_count, job_site_count, report_type, processing_time):
    """
    Log agent usage statistics
    
    Args:
        driver_count (int): Number of drivers processed
        job_site_count (int): Number of job sites processed
        report_type (str): Type of report generated
        processing_time (float): Processing time in seconds
    """
    usage_log = {
        "agent": "report_generator",
        "timestamp": datetime.now().isoformat(),
        "driver_count": driver_count,
        "job_site_count": job_site_count,
        "report_type": report_type,
        "processing_time": round(processing_time, 3),
        "records_per_second": round((driver_count + job_site_count) / processing_time, 2) if processing_time > 0 else 0
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
    test_drivers = [
        {"name": "John Doe", "job_site": "Downtown Project", "status": "on_time", "location_verified": True},
        {"name": "Jane Smith", "job_site": "Uptown Project", "status": "late", "location_verified": True},
        {"name": "Bob Johnson", "job_site": "Downtown Project", "status": "early_end", "location_verified": False}
    ]
    
    test_job_sites = [
        {"name": "Downtown Project", "driver_count": 2, "on_time_count": 1, "location": "Downtown"},
        {"name": "Uptown Project", "driver_count": 1, "on_time_count": 0, "location": "Uptown"}
    ]
    
    test_data = {
        "drivers": test_drivers,
        "job_sites": test_job_sites,
        "validation": {},
        "data_sources": ["driving_history", "activity_detail"]
    }
    
    result = handle(test_data, {"report_type": "standard", "include_details": True})
    print(json.dumps(result, indent=2))