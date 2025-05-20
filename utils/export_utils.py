"""
Export utilities for handling file downloads
"""
import os
import logging
from datetime import datetime
from flask import current_app, send_from_directory

logger = logging.getLogger(__name__)

def download_report_file(date_str, file_type='xlsx'):
    """
    Download a report file for a specific date
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        file_type (str): File type (xlsx or pdf)
        
    Returns:
        Flask response
    """
    try:
        # Validate date format
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid date format: {date_str}")
            return None
        
        # Set up file paths with multiple fallback options
        filename = f"{formatted_date}_DailyDriverReport.{file_type}"
        alt_filename = f"daily_report_{formatted_date}.{file_type}"
        
        # Define search directories from most specific to most general
        search_dirs = [
            os.path.join(current_app.root_path, 'exports', 'daily_reports'),
            os.path.join(current_app.root_path, 'static', 'exports', 'daily_reports'),
            os.path.join(current_app.root_path, 'exports'),
            os.path.join(current_app.root_path, 'static', 'exports')
        ]
        
        # Try to find the file in each directory
        for directory in search_dirs:
            if os.path.exists(os.path.join(directory, filename)):
                logger.info(f"Found file {filename} in {directory}")
                return send_from_directory(directory=directory, path=filename, as_attachment=True)
            
            if os.path.exists(os.path.join(directory, alt_filename)):
                logger.info(f"Found alternative file {alt_filename} in {directory}")
                return send_from_directory(directory=directory, path=alt_filename, as_attachment=True)
        
        logger.error(f"Report file not found for date {date_str}, type {file_type}")
        return None
    
    except Exception as e:
        logger.error(f"Error downloading report file: {e}")
        return None