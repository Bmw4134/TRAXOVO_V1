"""
TRAXORA Fleet Management System - Comparison Processor

This module provides functionality to compare different processing methods
for the attendance data, allowing users to evaluate which approach best
meets their needs.
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
import shutil

# Import both processing methods
from utils.enhanced_attendance_engine import EnhancedAttendanceProcessor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def prepare_alternative_report_output(alt_results_df, output_path="data/alternative_report.xlsx"):
    """
    Prepare and format the alternative processing results for download.
    
    Args:
        alt_results_df (DataFrame): Alternative processing results DataFrame
        output_path (str): Path to save the formatted output
        
    Returns:
        str: Path to the output file
    """
    try:
        # Make a copy to avoid modifying the original
        output_df = alt_results_df.copy()
        
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Add classification column based on hours worked (simplified approach)
        def classify_attendance(row):
            if pd.isna(row.get('Start Time')) or pd.isna(row.get('End Time')):
                return 'Unknown'
            
            start_time = pd.to_datetime(row['Start Time'])
            end_time = pd.to_datetime(row['End Time'])
            hours = row.get('Hours Worked', 0)
            
            # Simple classification logic for the alternative approach
            if start_time.hour > 7 and start_time.minute > 30:
                return 'Late Start'
            elif end_time.hour < 16:
                return 'Early End'
            elif hours < 7:
                return 'Short Day'
            else:
                return 'On Time'
        
        # Apply classification
        if 'Start Time' in output_df.columns and 'End Time' in output_df.columns:
            output_df['Classification'] = output_df.apply(classify_attendance, axis=1)
        
        # Save to Excel
        output_df.to_excel(output_path, index=False)
        
        # Copy to static directory for web access if it exists
        static_data_dir = os.path.join('static', 'data')
        if not os.path.exists(static_data_dir):
            os.makedirs(static_data_dir, exist_ok=True)
        
        static_output_path = os.path.join(static_data_dir, 'alternative_report.xlsx')
        shutil.copy(output_path, static_output_path)
        
        logger.info(f"Alternative report prepared and saved to {output_path} and {static_output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error preparing alternative report output: {str(e)}")
        return None

def process_comparison(start_date="2025-05-18", end_date="2025-05-24"):
    """
    Process the same data with both methods for comparison.
    
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
    
    logger.info(f"Starting comparison process for {start_date} to {end_date}")
    
    try:
        # Create enhanced processor
        processor = EnhancedAttendanceProcessor(start_date, end_date)
        
        # Process with both methods
        comparison = processor.process_both_methods(
            driving_history_path,
            activity_detail_path,
            time_on_site_path
        )
        
        # Prepare alternative report for download if results exist
        if comparison and comparison.get('alt_results') is not None:
            alt_df = pd.DataFrame.from_dict(comparison['alt_results'])
            alt_report_path = prepare_alternative_report_output(alt_df)
            comparison['alt_stats']['report_path'] = alt_report_path
        
        return comparison
    
    except Exception as e:
        logger.error(f"Error in comparison process: {str(e)}")
        return None