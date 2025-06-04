"""
TRAXORA Iterative Learning System

This module implements a feedback loop for improving driver attendance classification
by learning from historical patterns and adjusting classification rules over time.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define constants
LEARNING_DATA_DIR = "data/learning"
THRESHOLDS_FILE = os.path.join(LEARNING_DATA_DIR, "classification_thresholds.json")
DRIVER_PATTERNS_FILE = os.path.join(LEARNING_DATA_DIR, "driver_patterns.json")
REPORTS_DIR = "reports"

# Default thresholds
DEFAULT_THRESHOLDS = {
    "late_start_time": "07:30:00",
    "early_end_time": "16:00:00",
    "confidence_threshold": 0.75,
    "last_updated": datetime.now().isoformat()
}

def ensure_learning_dirs():
    """Ensure learning data directories exist"""
    os.makedirs(LEARNING_DATA_DIR, exist_ok=True)
    
    # Initialize threshold file if it doesn't exist
    if not os.path.exists(THRESHOLDS_FILE):
        with open(THRESHOLDS_FILE, 'w') as f:
            json.dump(DEFAULT_THRESHOLDS, f, indent=2)
    
    # Initialize driver patterns file if it doesn't exist
    if not os.path.exists(DRIVER_PATTERNS_FILE):
        with open(DRIVER_PATTERNS_FILE, 'w') as f:
            json.dump({}, f, indent=2)

def load_classification_thresholds():
    """Load current classification thresholds"""
    ensure_learning_dirs()
    
    try:
        with open(THRESHOLDS_FILE, 'r') as f:
            thresholds = json.load(f)
        return thresholds
    except Exception as e:
        logger.error(f"Error loading classification thresholds: {e}")
        return DEFAULT_THRESHOLDS

def save_classification_thresholds(thresholds):
    """Save updated classification thresholds"""
    ensure_learning_dirs()
    
    try:
        # Update last_updated timestamp
        thresholds['last_updated'] = datetime.now().isoformat()
        
        with open(THRESHOLDS_FILE, 'w') as f:
            json.dump(thresholds, f, indent=2)
        
        logger.info(f"Classification thresholds updated: {thresholds}")
        return True
    except Exception as e:
        logger.error(f"Error saving classification thresholds: {e}")
        return False

def load_driver_patterns():
    """Load driver behavior patterns"""
    ensure_learning_dirs()
    
    try:
        with open(DRIVER_PATTERNS_FILE, 'r') as f:
            patterns = json.load(f)
        return patterns
    except Exception as e:
        logger.error(f"Error loading driver patterns: {e}")
        return {}

def save_driver_patterns(patterns):
    """Save driver behavior patterns"""
    ensure_learning_dirs()
    
    try:
        with open(DRIVER_PATTERNS_FILE, 'w') as f:
            json.dump(patterns, f, indent=2)
        
        logger.info(f"Driver patterns updated for {len(patterns)} drivers")
        return True
    except Exception as e:
        logger.error(f"Error saving driver patterns: {e}")
        return False

def get_recent_reports(days=30):
    """Get attendance reports from the last X days"""
    try:
        reports = []
        today = datetime.now().date()
        
        # Find all report files
        for file in os.listdir(REPORTS_DIR):
            if file.startswith('attendance_report_') and file.endswith('.json'):
                date_str = file.replace('attendance_report_', '').replace('.json', '')
                try:
                    report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # Only include reports within the specified time range
                    if (today - report_date).days <= days:
                        report_path = os.path.join(REPORTS_DIR, file)
                        with open(report_path, 'r') as f:
                            report_data = json.load(f)
                            reports.append({
                                'date': date_str,
                                'data': report_data
                            })
                except Exception as e:
                    logger.warning(f"Error processing report file {file}: {e}")
        
        return sorted(reports, key=lambda x: x['date'], reverse=True)
    except Exception as e:
        logger.error(f"Error getting recent reports: {e}")
        return []

def update_driver_patterns(days=30):
    """Update driver behavior patterns based on recent reports"""
    try:
        # Get recent reports
        reports = get_recent_reports(days)
        if not reports:
            logger.warning("No recent reports found for updating driver patterns")
            return False
        
        # Load existing patterns
        patterns = load_driver_patterns()
        
        # Process all reports
        for report in reports:
            date_str = report['date']
            driver_records = report['data'].get('driver_records', [])
            
            for driver in driver_records:
                driver_name = driver.get('driver_name', '').lower()
                if not driver_name:
                    continue
                
                # Initialize driver pattern if not exists
                if driver_name not in patterns:
                    patterns[driver_name] = {
                        'start_times': [],
                        'end_times': [],
                        'classifications': {
                            'on_time': 0,
                            'late': 0,
                            'early_end': 0,
                            'not_on_job': 0
                        },
                        'job_sites': {},
                        'last_updated': datetime.now().isoformat()
                    }
                
                # Update start and end times
                if 'start_time' in driver and driver['start_time']:
                    patterns[driver_name]['start_times'].append(driver['start_time'])
                    # Keep only the last 30 entries
                    patterns[driver_name]['start_times'] = patterns[driver_name]['start_times'][-30:]
                
                if 'end_time' in driver and driver['end_time']:
                    patterns[driver_name]['end_times'].append(driver['end_time'])
                    # Keep only the last 30 entries
                    patterns[driver_name]['end_times'] = patterns[driver_name]['end_times'][-30:]
                
                # Update classification counts
                if 'classification' in driver:
                    classification = driver['classification']
                    if classification in patterns[driver_name]['classifications']:
                        patterns[driver_name]['classifications'][classification] += 1
                
                # Update job site frequency
                if 'job_site' in driver and driver['job_site']:
                    job_site = driver['job_site']
                    if job_site not in patterns[driver_name]['job_sites']:
                        patterns[driver_name]['job_sites'][job_site] = 1
                    else:
                        patterns[driver_name]['job_sites'][job_site] += 1
                
                # Update timestamp
                patterns[driver_name]['last_updated'] = datetime.now().isoformat()
        
        # Save updated patterns
        save_driver_patterns(patterns)
        logger.info(f"Driver patterns updated for {len(patterns)} drivers")
        
        # Update classification thresholds based on patterns
        update_classification_thresholds(patterns)
        
        return True
    except Exception as e:
        logger.error(f"Error updating driver patterns: {e}")
        return False

def update_classification_thresholds(patterns):
    """Update classification thresholds based on driver patterns"""
    try:
        # Load current thresholds
        thresholds = load_classification_thresholds()
        
        # Extract all start times and end times
        all_start_times = []
        all_end_times = []
        
        for driver, data in patterns.items():
            all_start_times.extend(data['start_times'])
            all_end_times.extend(data['end_times'])
        
        if not all_start_times or not all_end_times:
            logger.warning("Not enough data to update classification thresholds")
            return False
        
        # Convert times to datetime objects for analysis
        start_times = []
        for time_str in all_start_times:
            try:
                if ':' in time_str:
                    hours, minutes, seconds = map(int, time_str.split(':'))
                    start_times.append(hours * 3600 + minutes * 60 + seconds)
            except Exception:
                pass
        
        end_times = []
        for time_str in all_end_times:
            try:
                if ':' in time_str:
                    hours, minutes, seconds = map(int, time_str.split(':'))
                    end_times.append(hours * 3600 + minutes * 60 + seconds)
            except Exception:
                pass
        
        if not start_times or not end_times:
            logger.warning("Could not parse time data for threshold analysis")
            return False
        
        # Only adjust thresholds if we have sufficient data
        if len(start_times) > 50 and len(end_times) > 50:
            # Calculate 25th percentile for start time (earlier than 75% of starts)
            start_percentile = int(np.percentile(start_times, 25))
            start_hours = start_percentile // 3600
            start_minutes = (start_percentile % 3600) // 60
            start_seconds = start_percentile % 60
            
            # Calculate 75th percentile for end time (later than 75% of ends)
            end_percentile = int(np.percentile(end_times, 75))
            end_hours = end_percentile // 3600
            end_minutes = (end_percentile % 3600) // 60
            end_seconds = end_percentile % 60
            
            # Format as time strings
            new_late_start = f"{start_hours:02d}:{start_minutes:02d}:{start_seconds:02d}"
            new_early_end = f"{end_hours:02d}:{end_minutes:02d}:{end_seconds:02d}"
            
            # Update thresholds if they're reasonable (7-9 AM for start, 3-5 PM for end)
            if 7 <= start_hours <= 9:
                thresholds['late_start_time'] = new_late_start
                logger.info(f"Updated late start threshold to {new_late_start}")
            
            if 15 <= end_hours <= 17:
                thresholds['early_end_time'] = new_early_end
                logger.info(f"Updated early end threshold to {new_early_end}")
            
            # Save updated thresholds
            save_classification_thresholds(thresholds)
            return True
        else:
            logger.info("Not enough data points to update thresholds yet")
            return False
    except Exception as e:
        logger.error(f"Error updating classification thresholds: {e}")
        return False

def get_driver_suggestions(driver_name):
    """Get personalized suggestions for a driver based on patterns"""
    try:
        driver_name = driver_name.lower()
        patterns = load_driver_patterns()
        
        if driver_name not in patterns:
            return None
        
        driver_data = patterns[driver_name]
        
        # Calculate common start time
        start_times = []
        for time_str in driver_data['start_times']:
            try:
                if ':' in time_str:
                    hours, minutes, seconds = map(int, time_str.split(':'))
                    start_times.append(hours * 3600 + minutes * 60 + seconds)
            except Exception:
                pass
        
        if start_times:
            avg_start = int(sum(start_times) / len(start_times))
            avg_start_hours = avg_start // 3600
            avg_start_minutes = (avg_start % 3600) // 60
            
            common_start = f"{avg_start_hours:02d}:{avg_start_minutes:02d}"
        else:
            common_start = "unknown"
        
        # Find most common job site
        if driver_data['job_sites']:
            most_common_job = max(driver_data['job_sites'].items(), key=lambda x: x[1])[0]
        else:
            most_common_job = "unknown"
        
        # Calculate attendance reliability
        total_records = sum(driver_data['classifications'].values())
        if total_records > 0:
            on_time_percentage = (driver_data['classifications']['on_time'] / total_records) * 100
        else:
            on_time_percentage = 0
        
        # Generate suggestions
        suggestions = {
            'common_start_time': common_start,
            'most_common_job_site': most_common_job,
            'on_time_percentage': round(on_time_percentage, 1),
            'reliability_rating': 'High' if on_time_percentage >= 85 else 
                                'Medium' if on_time_percentage >= 70 else 'Low',
            'suggestion': ""
        }
        
        # Add personalized suggestion
        if on_time_percentage < 70:
            late_count = driver_data['classifications']['late']
            early_end_count = driver_data['classifications']['early_end']
            
            if late_count > early_end_count:
                suggestions['suggestion'] = f"Consider arriving earlier. Your typical start time is {common_start}, " \
                                           f"but you've been late {late_count} times recently."
            elif early_end_count > late_count:
                suggestions['suggestion'] = f"Try to complete full work days. You've left early {early_end_count} " \
                                           f"times recently."
            else:
                suggestions['suggestion'] = f"Your attendance needs improvement. On-time rate is only {round(on_time_percentage, 1)}%."
        else:
            suggestions['suggestion'] = f"Good attendance record with {round(on_time_percentage, 1)}% on-time rate."
        
        return suggestions
    except Exception as e:
        logger.error(f"Error getting driver suggestions: {e}")
        return None

def get_adaptive_thresholds_for_driver(driver_name):
    """Get personalized classification thresholds for a specific driver"""
    try:
        # Start with the global thresholds
        global_thresholds = load_classification_thresholds()
        driver_name = driver_name.lower()
        
        # Load driver patterns
        patterns = load_driver_patterns()
        
        # If no pattern exists for this driver or not enough data, use global thresholds
        if driver_name not in patterns or len(patterns[driver_name]['start_times']) < 5:
            return global_thresholds
        
        # Get this driver's typical patterns
        driver_data = patterns[driver_name]
        
        # Calculate personalized start time threshold (10 minutes later than usual start)
        start_times = []
        for time_str in driver_data['start_times']:
            try:
                if ':' in time_str:
                    hours, minutes, seconds = map(int, time_str.split(':'))
                    start_times.append(hours * 3600 + minutes * 60 + seconds)
            except Exception:
                pass
        
        if start_times:
            avg_start = int(sum(start_times) / len(start_times))
            # Add 10 minutes tolerance
            personalized_start = avg_start + (10 * 60)
            
            start_hours = personalized_start // 3600
            start_minutes = (personalized_start % 3600) // 60
            start_seconds = personalized_start % 60
            
            # Only use personalized threshold if it's within reasonable bounds (6-9 AM)
            if 6 <= start_hours <= 9:
                personalized_late_start = f"{start_hours:02d}:{start_minutes:02d}:{start_seconds:02d}"
                
                # Create a copy of global thresholds with personalized values
                personalized_thresholds = global_thresholds.copy()
                personalized_thresholds['late_start_time'] = personalized_late_start
                
                return personalized_thresholds
        
        # If we can't calculate a personalized threshold, return global thresholds
        return global_thresholds
    except Exception as e:
        logger.error(f"Error getting adaptive thresholds for driver {driver_name}: {e}")
        return load_classification_thresholds()  # Fallback to global thresholds

# Function to be called by the attendance pipeline
def get_classification_thresholds(driver_name=None):
    """
    Get classification thresholds, personalized for driver if specified
    
    Args:
        driver_name (str, optional): Driver name for personalized thresholds
        
    Returns:
        dict: Classification thresholds
    """
    if driver_name:
        return get_adaptive_thresholds_for_driver(driver_name)
    else:
        return load_classification_thresholds()