"""
TRAXORA Validation Core

This module provides comprehensive validation for data and report integrity throughout the
Daily Driver Report pipeline. It ensures consistent handling and validation of all source data,
processing, and output generation.
"""

import os
import sys
import json
import logging
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from pathlib import Path
import traceback
from typing import Dict, List, Tuple, Any, Optional, Set, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs('logs/validation', exist_ok=True)

# Set up validation logger
validation_logger = logging.getLogger('validation')
if not validation_logger.handlers:
    file_handler = logging.FileHandler('logs/validation/validation_core.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    validation_logger.addHandler(file_handler)
    validation_logger.setLevel(logging.INFO)

# Diagnostics logger for critical issues
diagnostics_logger = logging.getLogger('diagnostics')
if not diagnostics_logger.handlers:
    file_handler = logging.FileHandler('logs/validation/diagnostics.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    diagnostics_logger.addHandler(file_handler)
    diagnostics_logger.setLevel(logging.ERROR)

# Validation constants
MINIMUM_SOURCE_FILES = {
    'driving_history': 1,
    'activity_detail': 1,
    'start_time_job': 1,
}
REQUIRED_DRIVER_FIELDS = ['driver_name', 'asset_id', 'job_site', 'scheduled_start', 'scheduled_end']
REQUIRED_SUMMARY_FIELDS = ['total', 'late', 'early_end', 'not_on_job', 'on_time']
GPS_DISTANCE_THRESHOLD = 0.2  # Miles

# Global state tracking
_validation_state = {
    'valid_reports': set(),
    'incomplete_inputs': set(),
    'mismatched_row_counts': set(),
    'job_site_gps_mismatches': set(),
    'dates_processed': set(),
    'validation_report': {}
}

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def log_diagnostics(error_type: str, message: str, details: Optional[Dict] = None):
    """Log diagnostics information for critical errors"""
    diagnostics_logger.error(f"{error_type}: {message}")
    if details:
        diagnostics_logger.error(f"Details: {json.dumps(details, default=str)}")

def validate_source_files(date_str: str) -> Dict[str, List[str]]:
    """
    Validate all source files for a specific date
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        Dict[str, List[str]]: Dictionary of validated source files by category
    """
    validation_logger.info(f"Validating source files for {date_str}")
    
    # Define directories to search
    search_dirs = ['data']
    
    # Initialize source file dictionary
    source_files = {
        'driving_history': [],
        'activity_detail': [],
        'assets_time_on_site': [],
        'start_time_job': []
    }
    
    # Patterns to look for in filenames
    date_pattern = date_str.replace('-', '')
    patterns = {
        'driving_history': [f'driving_history_{date_str}', f'DrivingHistory_{date_pattern}', f'DrivingHistory{date_pattern}'],
        'activity_detail': [f'activity_detail_{date_str}', f'ActivityDetail_{date_pattern}', f'ActivityDetail{date_pattern}'],
        'assets_time_on_site': [f'assets_onsite_{date_str}', f'AssetsTimeOnSite_{date_pattern}', f'AssetsTimeOnSite{date_pattern}'],
        'start_time_job': [f'baseline', f'starttime_{date_str}', f'StartTime_{date_pattern}', f'StartTime{date_pattern}']
    }
    
    # Search for files matching patterns
    for directory in search_dirs:
        if not os.path.exists(directory):
            continue
            
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    # Check each category
                    for category, category_patterns in patterns.items():
                        if any(pattern in file for pattern in category_patterns):
                            # Validate file can be opened and has data
                            try:
                                if file.endswith('.csv'):
                                    df = pd.read_csv(file_path)
                                    if not df.empty:
                                        source_files[category].append(file_path)
                                        validation_logger.info(f"Valid source file found: {file_path} for category {category}")
                                elif file.endswith(('.xlsx', '.xls')):
                                    df = pd.read_excel(file_path)
                                    if not df.empty:
                                        source_files[category].append(file_path)
                                        validation_logger.info(f"Valid source file found: {file_path} for category {category}")
                                elif file.endswith('.json'):
                                    with open(file_path, 'r') as f:
                                        data = json.load(f)
                                    if data:
                                        source_files[category].append(file_path)
                                        validation_logger.info(f"Valid source file found: {file_path} for category {category}")
                            except Exception as e:
                                validation_logger.error(f"Error validating file {file_path}: {e}")
    
    # Check if minimum required source files are present
    missing_categories = []
    for category, min_count in MINIMUM_SOURCE_FILES.items():
        if len(source_files[category]) < min_count:
            missing_categories.append(category)
    
    if missing_categories:
        _validation_state['incomplete_inputs'].add(date_str)
        error_message = f"Missing required source files for {date_str}: {', '.join(missing_categories)}"
        validation_logger.error(error_message)
        log_diagnostics('SOURCE_FILES_MISSING', error_message, {
            'date': date_str,
            'missing_categories': missing_categories,
            'found_files': {k: v for k, v in source_files.items()}
        })
    else:
        validation_logger.info(f"All required source files found for {date_str}")
    
    return source_files

def compute_file_hash(file_path: str) -> str:
    """Compute hash of file contents to track changes"""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        return hashlib.md5(data).hexdigest()
    except Exception as e:
        validation_logger.error(f"Error computing hash for {file_path}: {e}")
        return ""

def validate_data_integrity(processor_output: Dict, source_files: Dict[str, List[str]]) -> bool:
    """
    Validate the integrity of processed data against source files
    
    Args:
        processor_output (Dict): Output from the data processor
        source_files (Dict[str, List[str]]): Source files used for processing
        
    Returns:
        bool: True if data integrity is valid, False otherwise
    """
    validation_logger.info("Validating data integrity")
    
    try:
        # Check if processor output has required fields
        if not all(field in processor_output for field in ['date', 'drivers', 'summary']):
            validation_logger.error("Processor output missing required fields")
            return False
        
        # Check if all drivers have the required fields
        drivers = processor_output.get('drivers', [])
        if not drivers:
            validation_logger.error("No drivers in processor output")
            return False
            
        for i, driver in enumerate(drivers):
            missing_fields = [field for field in REQUIRED_DRIVER_FIELDS if field not in driver]
            if missing_fields:
                validation_logger.error(f"Driver {i} missing fields: {missing_fields}")
                return False
        
        # Check if summary has required fields
        summary = processor_output.get('summary', {})
        missing_summary_fields = [field for field in REQUIRED_SUMMARY_FIELDS if field not in summary]
        if missing_summary_fields:
            validation_logger.error(f"Summary missing fields: {missing_summary_fields}")
            return False
            
        # Check if summary counts match driver counts
        driver_counts = {
            'total': len(drivers),
            'late': sum(1 for d in drivers if d.get('status') == 'Late'),
            'early_end': sum(1 for d in drivers if d.get('status') == 'Early End'),
            'not_on_job': sum(1 for d in drivers if d.get('status') == 'Not On Job'),
            'on_time': sum(1 for d in drivers if d.get('status') == 'On Time')
        }
        
        for field in REQUIRED_SUMMARY_FIELDS:
            if summary.get(field, 0) != driver_counts[field]:
                validation_logger.error(f"Summary count mismatch for {field}: {summary.get(field, 0)} != {driver_counts[field]}")
                return False
        
        # Check that driver names are unique
        driver_names = [d.get('driver_name') for d in drivers]
        if len(driver_names) != len(set(driver_names)):
            validation_logger.error("Duplicate driver names found")
            return False
            
        validation_logger.info("Data integrity validated successfully")
        return True
    
    except Exception as e:
        validation_logger.error(f"Error validating data integrity: {e}")
        return False

def validate_output_files(date_str: str) -> bool:
    """
    Validate all output files for a specific date
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        bool: True if all output files are valid, False otherwise
    """
    validation_logger.info(f"Validating output files for {date_str}")
    
    # Define expected output files
    reports_dir = Path('reports/daily_drivers')
    exports_dir = Path('exports/daily_reports')
    
    expected_files = [
        reports_dir / f"daily_report_{date_str}.json",
        reports_dir / f"daily_report_{date_str}.xlsx",
        reports_dir / f"daily_report_{date_str}.pdf",
        exports_dir / f"{date_str}_DailyDriverReport.pdf",
        exports_dir / f"{date_str}_DailyDriverReport.xlsx",
        exports_dir / f"daily_report_{date_str}.pdf",
        exports_dir / f"daily_report_{date_str}.json"
    ]
    
    # Check if all expected files exist
    missing_files = [str(f) for f in expected_files if not f.exists()]
    
    if missing_files:
        validation_logger.error(f"Missing output files for {date_str}: {missing_files}")
        return False
    
    # Validate JSON file
    json_file = reports_dir / f"daily_report_{date_str}.json"
    try:
        with open(json_file, 'r') as f:
            report_data = json.load(f)
            
        # Check for required fields
        if not all(field in report_data for field in ['date', 'drivers', 'summary']):
            validation_logger.error(f"JSON file missing required fields: {json_file}")
            return False
            
        # Check summary counts match driver list
        summary = report_data.get('summary', {})
        drivers = report_data.get('drivers', [])
        
        driver_counts = {
            'total': len(drivers),
            'late': sum(1 for d in drivers if d.get('status') == 'Late'),
            'early_end': sum(1 for d in drivers if d.get('status') == 'Early End'),
            'not_on_job': sum(1 for d in drivers if d.get('status') == 'Not On Job'),
            'on_time': sum(1 for d in drivers if d.get('status') == 'On Time')
        }
        
        for field in REQUIRED_SUMMARY_FIELDS:
            if summary.get(field, 0) != driver_counts[field]:
                validation_logger.error(f"Summary count mismatch in JSON for {field}")
                return False
                
    except Exception as e:
        validation_logger.error(f"Error validating JSON file {json_file}: {e}")
        return False
    
    validation_logger.info(f"All output files for {date_str} validated successfully")
    return True

def validate_report_generation(date_str: str) -> bool:
    """
    Validate the entire report generation process for a specific date
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        
    Returns:
        bool: True if report generation is valid, False otherwise
    """
    validation_logger.info(f"Validating report generation for {date_str}")
    
    try:
        # Track this date as processed
        _validation_state['dates_processed'].add(date_str)
        
        # Step 1: Validate source files
        source_files = validate_source_files(date_str)
        
        # Skip further validation if missing required source files
        if date_str in _validation_state['incomplete_inputs']:
            validation_logger.warning(f"Skipping further validation for {date_str} due to missing source files")
            return False
        
        # Step 2: Process data
        from genius_processor import process_date
        processor_output = process_date(date_str)
        
        if not processor_output:
            validation_logger.error(f"Processor returned no output for {date_str}")
            return False
        
        # Step 3: Validate data integrity
        if not validate_data_integrity(processor_output, source_files):
            validation_logger.error(f"Data integrity validation failed for {date_str}")
            _validation_state['mismatched_row_counts'].add(date_str)
            return False
        
        # Step 4: Validate output files
        if not validate_output_files(date_str):
            validation_logger.error(f"Output files validation failed for {date_str}")
            return False
        
        # If all validations pass, mark as valid report
        _validation_state['valid_reports'].add(date_str)
        validation_logger.info(f"Report generation validated successfully for {date_str}")
        
        # Build validation report
        _validation_state['validation_report'][date_str] = {
            'valid': True,
            'source_files': {cat: [os.path.basename(f) for f in files] for cat, files in source_files.items()},
            'drivers_count': len(processor_output.get('drivers', [])),
            'summary': processor_output.get('summary', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        return True
        
    except Exception as e:
        validation_logger.error(f"Error in report generation validation for {date_str}: {e}")
        validation_logger.error(traceback.format_exc())
        
        # Log diagnostics
        log_diagnostics('VALIDATION_ERROR', f"Error validating report for {date_str}", {
            'date': date_str,
            'error': str(e),
            'traceback': traceback.format_exc()
        })
        
        # Build error report
        _validation_state['validation_report'][date_str] = {
            'valid': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        
        return False

def get_validation_state() -> Dict:
    """Get the current validation state"""
    return {
        'valid_reports': list(_validation_state['valid_reports']),
        'incomplete_inputs': list(_validation_state['incomplete_inputs']),
        'mismatched_row_counts': list(_validation_state['mismatched_row_counts']),
        'job_site_gps_mismatches': list(_validation_state['job_site_gps_mismatches']),
        'dates_processed': list(_validation_state['dates_processed']),
        'validation_report': _validation_state['validation_report']
    }

def save_validation_state() -> str:
    """
    Save the validation state to a file
    
    Returns:
        str: Path to the saved file
    """
    output_dir = Path('reports/validation')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "validation_state.json"
    
    # Get current validation state
    state = get_validation_state()
    
    # Add timestamp
    state['last_updated'] = datetime.now().isoformat()
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(state, f, indent=2, default=str)
    
    validation_logger.info(f"Validation state saved to {output_file}")
    return str(output_file)

def load_validation_state() -> Dict:
    """
    Load the validation state from a file
    
    Returns:
        Dict: Loaded validation state
    """
    state_file = Path('reports/validation/validation_state.json')
    
    if not state_file.exists():
        validation_logger.warning("Validation state file not found, initializing empty state")
        return get_validation_state()
    
    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        # Convert lists back to sets
        _validation_state['valid_reports'] = set(state.get('valid_reports', []))
        _validation_state['incomplete_inputs'] = set(state.get('incomplete_inputs', []))
        _validation_state['mismatched_row_counts'] = set(state.get('mismatched_row_counts', []))
        _validation_state['job_site_gps_mismatches'] = set(state.get('job_site_gps_mismatches', []))
        _validation_state['dates_processed'] = set(state.get('dates_processed', []))
        _validation_state['validation_report'] = state.get('validation_report', {})
        
        validation_logger.info(f"Validation state loaded from {state_file}")
        return state
    
    except Exception as e:
        validation_logger.error(f"Error loading validation state: {e}")
        return get_validation_state()