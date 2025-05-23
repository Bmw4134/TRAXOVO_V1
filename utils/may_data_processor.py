"""
TRAXORA Fleet Management System - May Data Processor

This module provides specialized functionality for processing the May 18-24, 2025 
driver report data from specific files in the attached_assets directory.
"""

import os
import json
import logging
import glob
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def process_may_weekly_report(attached_assets_dir, weekly_processor_function, report_dir):
    """
    Process the May 18-24, 2025 weekly driver report using specific files from attached_assets.
    
    Args:
        attached_assets_dir (str): Path to the attached_assets directory
        weekly_processor_function (function): Function to process weekly report
        report_dir (str): Directory to save the report
        
    Returns:
        tuple: (report_data, errors) - Report data if successful, None if failed and a list of error messages
    """
    try:
        # Define date range
        start_date = '2025-05-18'  # Sunday
        end_date = '2025-05-24'    # Saturday
        
        errors = []
        
        # Check if the attached_assets directory exists
        if not os.path.exists(attached_assets_dir):
            errors.append(f"Attached assets directory not found: {attached_assets_dir}")
            return None, errors
        
        # Find all the necessary data files
        driving_history_paths = []
        activity_detail_paths = []
        time_on_site_paths = []
        timecard_paths = []
        
        # Search for files in the attached_assets directory
        for file in os.listdir(attached_assets_dir):
            file_path = os.path.join(attached_assets_dir, file)
            
            # Skip directories and non-data files
            if os.path.isdir(file_path) or not os.path.isfile(file_path):
                continue
            
            # Find driving history files
            if file.startswith("DrivingHistory") and file.endswith(".csv"):
                driving_history_paths.append(file_path)
                logger.info(f"Found driving history file: {file}")
            
            # Find activity detail files
            elif file.startswith("ActivityDetail") and file.endswith(".csv"):
                activity_detail_paths.append(file_path)
                logger.info(f"Found activity detail file: {file}")
            
            # Find assets time on site files
            elif file.startswith("AssetsTimeOnSite") and file.endswith(".csv"):
                time_on_site_paths.append(file_path)
                logger.info(f"Found time on site file: {file}")
            
            # Find timecard files
            elif file.startswith("Timecards") and file.endswith(".xlsx"):
                timecard_paths.append(file_path)
                logger.info(f"Found timecard file: {file}")
        
        # Use the specific May 18-24 files
        specific_files = {
            'driving_history': 'DrivingHistory (13).csv',
            'activity_detail': 'ActivityDetail (13).csv',
            'time_on_site': 'AssetsTimeOnSite (3).csv',
            'timecard1': 'Timecards - 2025-05-18 - 2025-05-24 (3).xlsx',
            'timecard2': 'Timecards - 2025-05-18 - 2025-05-24 (4).xlsx'
        }
        
        # Search for specific files
        driving_history_path = None
        activity_detail_path = None
        time_on_site_path = None
        selected_timecard_paths = []
        
        # Look for the specific files first
        for file_name, file_pattern in specific_files.items():
            if file_name == 'driving_history':
                matching_files = glob.glob(os.path.join(attached_assets_dir, file_pattern))
                if matching_files:
                    driving_history_path = matching_files[0]
            elif file_name == 'activity_detail':
                matching_files = glob.glob(os.path.join(attached_assets_dir, file_pattern))
                if matching_files:
                    activity_detail_path = matching_files[0]
            elif file_name == 'time_on_site':
                matching_files = glob.glob(os.path.join(attached_assets_dir, file_pattern))
                if matching_files:
                    time_on_site_path = matching_files[0]
            elif file_name.startswith('timecard'):
                matching_files = glob.glob(os.path.join(attached_assets_dir, file_pattern))
                if matching_files:
                    selected_timecard_paths.extend(matching_files)
        
        # If specific files are not found, fall back to the generic ones
        if not driving_history_path and driving_history_paths:
            driving_history_path = driving_history_paths[-1]  # Use the last one (likely most recent)
        
        if not activity_detail_path and activity_detail_paths:
            activity_detail_path = activity_detail_paths[-1]
        
        if not time_on_site_path and time_on_site_paths:
            time_on_site_path = time_on_site_paths[-1]
        
        if not selected_timecard_paths and timecard_paths:
            # Use all timecard files
            selected_timecard_paths = timecard_paths
        
        # Log the files we're using
        logger.info(f"Using driving history: {driving_history_path}")
        logger.info(f"Using activity detail: {activity_detail_path}")
        logger.info(f"Using time on site: {time_on_site_path}")
        logger.info(f"Using {len(selected_timecard_paths)} timecard files")
        
        # Check if we have the minimum required files
        if not driving_history_path:
            errors.append("No driving history file found")
        
        if not time_on_site_path:
            errors.append("No time on site file found")
        
        if errors:
            return None, errors
        
        # Process the weekly report
        report = weekly_processor_function(
            start_date=start_date,
            end_date=end_date,
            driving_history_path=driving_history_path,
            activity_detail_path=activity_detail_path,
            time_on_site_path=time_on_site_path,
            timecard_paths=selected_timecard_paths
        )
        
        # Save the report
        if report:
            # Create reports directory if it doesn't exist
            os.makedirs(report_dir, exist_ok=True)
            
            # Save report to file
            report_path = os.path.join(report_dir, f"weekly_{start_date}_to_{end_date}.json")
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Report saved to {report_path}")
            
            return report, []
        else:
            errors.append("Failed to generate report")
            return None, errors
        
    except Exception as e:
        import traceback
        logger.error(f"Error processing May data: {str(e)}")
        logger.error(traceback.format_exc())
        errors.append(f"Error: {str(e)}")
        return None, errors