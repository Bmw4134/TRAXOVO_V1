"""
TRAXORA Fleet Management System - May Data Processor

This module provides specialized functionality for processing the May 18-24, 2025 
driver report data from specific files in the attached_assets directory.
"""

import os
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_may_weekly_report(attached_assets_dir, weekly_processor_function, report_dir):
    """
    Process the May 18-24, 2025 weekly driver report using specific files from attached_assets.
    
    Args:
        attached_assets_dir (str): Path to the attached_assets directory
        weekly_processor_function (function): Function to process weekly report
        report_dir (str): Directory to save the report
        
    Returns:
        dict: Report data if successful, None if failed
    """
    try:
        # Define date range for May 18-24, 2025
        start_date = "2025-05-18"  # Sunday
        end_date = "2025-05-24"    # Saturday
        
        # Define specific files we need from the attached_assets directory
        driving_history_file = os.path.join(attached_assets_dir, 'DrivingHistory.csv')
        activity_detail_file = os.path.join(attached_assets_dir, 'ActivityDetail (13).csv')
        time_on_site_file = os.path.join(attached_assets_dir, 'AssetsTimeOnSite (8).csv')
        timecard_file = os.path.join(attached_assets_dir, 'Timecards - 2025-05-18 - 2025-05-24 (3).xlsx')
        
        # Verify files exist and find alternatives if needed
        if not os.path.exists(driving_history_file):
            for file in os.listdir(attached_assets_dir):
                if file.startswith("DrivingHistory") and file.endswith(".csv"):
                    driving_history_file = os.path.join(attached_assets_dir, file)
                    logger.info(f"Using driving history file: {file}")
                    break
                    
        if not os.path.exists(activity_detail_file):
            for file in os.listdir(attached_assets_dir):
                if file.startswith("ActivityDetail") and file.endswith(".csv"):
                    activity_detail_file = os.path.join(attached_assets_dir, file)
                    logger.info(f"Using activity detail file: {file}")
                    break
                    
        if not os.path.exists(time_on_site_file):
            for file in os.listdir(attached_assets_dir):
                if file.startswith("AssetsTimeOnSite") and file.endswith(".csv"):
                    time_on_site_file = os.path.join(attached_assets_dir, file)
                    logger.info(f"Using time on site file: {file}")
                    break
                    
        if not os.path.exists(timecard_file):
            for file in os.listdir(attached_assets_dir):
                if "Timecards - 2025-05-18 - 2025-05-24" in file and file.endswith(".xlsx"):
                    timecard_file = os.path.join(attached_assets_dir, file)
                    logger.info(f"Using timecard file: {file}")
                    break
        
        # Check if we have all required files
        missing_files = []
        if not os.path.exists(driving_history_file):
            missing_files.append("Driving History file")
        if not os.path.exists(activity_detail_file):
            missing_files.append("Activity Detail file")
        if not os.path.exists(time_on_site_file):
            missing_files.append("Time on Site file")
        if not os.path.exists(timecard_file):
            missing_files.append("Timecard file")
            
        if missing_files:
            logger.error(f"Missing required files: {', '.join(missing_files)}")
            return None, missing_files
            
        # Log the files we're using
        logger.info(f"Processing May 18-24 report with files:")
        logger.info(f"Driving History: {driving_history_file}")
        logger.info(f"Activity Detail: {activity_detail_file}")
        logger.info(f"Time on Site: {time_on_site_file}")
        logger.info(f"Timecard: {timecard_file}")
        
        # Process the weekly report
        report = weekly_processor_function(
            start_date=start_date,
            end_date=end_date,
            driving_history_path=driving_history_file,
            activity_detail_path=activity_detail_file,
            time_on_site_path=time_on_site_file,
            timecard_paths=[timecard_file]
        )
        
        if not report:
            logger.error("Report generation failed - no data returned")
            return None, ["Report generation failed"]
            
        # Save the report to disk
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"weekly_{start_date}_to_{end_date}.json")
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Report saved to {report_path}")
        
        return report, None
        
    except Exception as e:
        logger.error(f"Error processing May data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None, [str(e)]