"""
TRAXORA Fleet Management System - Comparison Processor

This module provides functionality to compare the current TRAXORA processor with 
an alternative approach for processing driver attendance data.
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta

# Import both processing methods
from utils.weekly_driver_processor import process_weekly_report
import alternative_processor as alt_processor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_comparison(start_date="2025-05-18", end_date="2025-05-24"):
    """
    Process the same data with both TRAXORA and alternative methods
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        dict: Comparison results
    """
    # Set file paths to the most recent versions
    attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
    
    driving_history_path = os.path.join(attached_assets_dir, 'DrivingHistory (19).csv')
    activity_detail_path = os.path.join(attached_assets_dir, 'ActivityDetail (13).csv')
    time_on_site_path = os.path.join(attached_assets_dir, 'AssetsTimeOnSite (8).csv')
    
    # Ensure files exist
    for file_path in [driving_history_path, activity_detail_path, time_on_site_path]:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
    
    # Process with TRAXORA method
    logger.info("Processing with TRAXORA method...")
    traxora_results = process_weekly_report(
        start_date=start_date,
        end_date=end_date,
        driving_history_path=driving_history_path,
        activity_detail_path=activity_detail_path,
        time_on_site_path=time_on_site_path,
        from_attached_assets=True
    )
    
    # Create data directory for alternative processor
    os.makedirs("data", exist_ok=True)
    
    # Copy files for alternative processor
    import shutil
    shutil.copy(driving_history_path, "data/telematics.csv")
    
    # Process with alternative method (if possible)
    alt_results = None
    try:
        logger.info("Processing with alternative method...")
        telematics = alt_processor.load_telematics("data/telematics.csv")
        # No timecards available in the same format, so use empty DataFrame
        timecards = pd.DataFrame()
        alt_results = alt_processor.infer_attendance(telematics, timecards)
        alt_processor.generate_report(alt_results, "data/alternative_report.xlsx")
    except Exception as e:
        logger.error(f"Error processing with alternative method: {str(e)}")
    
    # Prepare comparison results
    comparison = {
        "traxora_stats": {
            "total_drivers": len(traxora_results.get("driver_data", [])),
            "date_range": f"{start_date} to {end_date}",
            "classifications": {
                "on_time": traxora_results.get("summary", {}).get("attendance_totals", {}).get("on_time", 0),
                "late_start": traxora_results.get("summary", {}).get("attendance_totals", {}).get("late_start", 0),
                "early_end": traxora_results.get("summary", {}).get("attendance_totals", {}).get("early_end", 0),
                "not_on_job": traxora_results.get("summary", {}).get("attendance_totals", {}).get("not_on_job", 0)
            }
        },
        "alt_stats": {
            "total_drivers": len(alt_results) if alt_results is not None else 0,
            "date_range": f"{start_date} to {end_date}",
            "report_path": "data/alternative_report.xlsx" if alt_results is not None else None
        },
        "traxora_results": traxora_results,
        "alt_results": alt_results.to_dict() if alt_results is not None and not alt_results.empty else None
    }
    
    return comparison