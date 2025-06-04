"""
TRAXORA Fleet Management System - Demo Processor

This module provides demonstration functionality for processing weekly driver reports
without requiring manual file uploads. Used for testing with attached assets.
"""

import os
import logging
from datetime import datetime, timedelta
from utils.weekly_driver_processor import process_weekly_report

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_may_week_report():
    """
    Process May 18-24, 2025 driver report data using attached assets files.
    
    Returns:
        dict: Processed weekly report data
    """
    # Define date range
    start_date = "2025-05-18"
    end_date = "2025-05-24"
    
    # Set file paths
    attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
    
    # Select appropriate files based on date (using most recent versions)
    driving_history_path = os.path.join(attached_assets_dir, 'DrivingHistory (19).csv')
    activity_detail_path = os.path.join(attached_assets_dir, 'ActivityDetail (13).csv')
    time_on_site_path = os.path.join(attached_assets_dir, 'AssetsTimeOnSite (8).csv')
    
    # Ensure files exist
    for file_path in [driving_history_path, activity_detail_path, time_on_site_path]:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
    
    # Process report using the weekly driver processor
    logger.info(f"Starting demo processing for May 18-24 weekly report")
    logger.info(f"Using files:")
    logger.info(f"  - Driving History: {os.path.basename(driving_history_path)}")
    logger.info(f"  - Activity Detail: {os.path.basename(activity_detail_path)}")
    logger.info(f"  - Time on Site: {os.path.basename(time_on_site_path)}")
    
    try:
        report_data = process_weekly_report(
            start_date=start_date,
            end_date=end_date,
            driving_history_path=driving_history_path,
            activity_detail_path=activity_detail_path,
            time_on_site_path=time_on_site_path,
            from_attached_assets=True
        )
        
        logger.info(f"Demo processing completed successfully")
        return report_data
    except Exception as e:
        logger.error(f"Error processing demo report: {str(e)}")
        return None

def get_formatted_dates():
    """Get formatted start and end dates for May 18-24, 2025"""
    start_date = datetime.strptime("2025-05-18", "%Y-%m-%d")
    end_date = datetime.strptime("2025-05-24", "%Y-%m-%d")
    
    start_formatted = start_date.strftime("%B %d, %Y")
    end_formatted = end_date.strftime("%B %d, %Y")
    
    return start_formatted, end_formatted