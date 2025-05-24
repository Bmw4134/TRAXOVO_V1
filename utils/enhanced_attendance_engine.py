"""
TRAXORA Fleet Management System - Enhanced Attendance Engine

This module provides a unified interface between the TRAXORA classification system
and the alternative attendance engine approach, allowing for seamless integration
of both methods.
"""

import os
import logging
import json
import pandas as pd
from datetime import datetime, timedelta

# Import both TRAXORA processor and alternative engine
from utils.weekly_driver_processor import process_weekly_report
import attendance_engine

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class EnhancedAttendanceProcessor:
    """
    Enhanced attendance processor that combines TRAXORA and alternative approaches
    """
    
    def __init__(self, start_date, end_date):
        """
        Initialize the enhanced attendance processor.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
        """
        self.start_date = start_date
        self.end_date = end_date
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.traxora_results = None
        self.alt_results = None
        
    def _prepare_alt_engine_data(self, driving_history_path, time_on_site_path=None):
        """
        Prepare data for the alternative engine.
        
        Args:
            driving_history_path (str): Path to driving history CSV file
            time_on_site_path (str): Path to time on site CSV file
            
        Returns:
            str: Path to prepared telematics data file
        """
        # Ensure directories exist
        attendance_engine.ensure_dirs()
        
        # Copy driving history to telematics.csv
        telematics_path = os.path.join(self.data_dir, "telematics.csv")
        
        # Use pandas to convert the driving history format to what the alternative engine expects
        logger.info(f"Preparing data for alternative engine from {driving_history_path}")
        try:
            df = pd.read_csv(driving_history_path)
            
            # Map fields from TRAXORA format to alternative engine format
            field_mapping = {
                "Contact": "EmployeeNo",
                "EventDateTime": "StartTime",
                "Locationx": "JOB"
            }
            
            # Create a new DataFrame with the mapped fields
            alt_df = pd.DataFrame()
            
            for traxora_field, alt_field in field_mapping.items():
                if traxora_field in df.columns:
                    alt_df[alt_field] = df[traxora_field]
            
            # Generate fake end times (30 minutes after start time) for demonstration
            if "StartTime" in alt_df.columns:
                alt_df["EndTime"] = pd.to_datetime(alt_df["StartTime"]) + pd.Timedelta(minutes=30)
                
            # Save to telematics.csv for alternative engine
            alt_df.to_csv(telematics_path, index=False)
            logger.info(f"Alternative engine data prepared and saved to {telematics_path}")
            
            return telematics_path
        except Exception as e:
            logger.error(f"Error preparing data for alternative engine: {str(e)}")
            return None
    
    def process_with_traxora(self, driving_history_path, activity_detail_path, time_on_site_path):
        """
        Process data with TRAXORA method.
        
        Args:
            driving_history_path (str): Path to driving history CSV file
            activity_detail_path (str): Path to activity detail CSV file
            time_on_site_path (str): Path to time on site CSV file
            
        Returns:
            dict: Processed data
        """
        logger.info("Processing with TRAXORA method...")
        try:
            self.traxora_results = process_weekly_report(
                start_date=self.start_date,
                end_date=self.end_date,
                driving_history_path=driving_history_path,
                activity_detail_path=activity_detail_path,
                time_on_site_path=time_on_site_path,
                from_attached_assets=True
            )
            logger.info("TRAXORA processing completed successfully")
            return self.traxora_results
        except Exception as e:
            logger.error(f"Error processing with TRAXORA method: {str(e)}")
            return None
    
    def process_with_alt_engine(self, driving_history_path):
        """
        Process data with alternative engine method.
        
        Args:
            driving_history_path (str): Path to driving history CSV file
            
        Returns:
            DataFrame: Processed data
        """
        logger.info("Processing with alternative engine method...")
        try:
            # Prepare data for alternative engine
            telematics_path = self._prepare_alt_engine_data(driving_history_path)
            
            if not telematics_path:
                logger.error("Failed to prepare data for alternative engine")
                return None
            
            # Load prepared data
            telematics = attendance_engine.load_telematics(telematics_path)
            
            # Create empty timecards DataFrame
            timecards = pd.DataFrame()
            
            # Process with alternative engine
            self.alt_results = attendance_engine.infer_attendance(telematics, timecards)
            
            # Export results
            output_file = os.path.join(self.data_dir, "alt_attendance_report.xlsx")
            attendance_engine.generate_report(self.alt_results, output_file)
            
            logger.info(f"Alternative engine processing completed successfully. Results saved to {output_file}")
            return self.alt_results
        except Exception as e:
            logger.error(f"Error processing with alternative engine method: {str(e)}")
            return None
    
    def process_both_methods(self, driving_history_path, activity_detail_path, time_on_site_path):
        """
        Process data with both methods and compare results.
        
        Args:
            driving_history_path (str): Path to driving history CSV file
            activity_detail_path (str): Path to activity detail CSV file
            time_on_site_path (str): Path to time on site CSV file
            
        Returns:
            dict: Comparison results
        """
        # Process with TRAXORA method
        traxora_results = self.process_with_traxora(
            driving_history_path, 
            activity_detail_path, 
            time_on_site_path
        )
        
        # Process with alternative engine method
        alt_results = self.process_with_alt_engine(driving_history_path)
        
        # Prepare comparison results
        comparison = {
            "traxora_stats": {
                "total_drivers": len(traxora_results.get("driver_data", [])) if traxora_results else 0,
                "date_range": f"{self.start_date} to {self.end_date}",
                "classifications": {
                    "on_time": traxora_results.get("summary", {}).get("attendance_totals", {}).get("on_time", 0) if traxora_results else 0,
                    "late_start": traxora_results.get("summary", {}).get("attendance_totals", {}).get("late_start", 0) if traxora_results else 0,
                    "early_end": traxora_results.get("summary", {}).get("attendance_totals", {}).get("early_end", 0) if traxora_results else 0,
                    "not_on_job": traxora_results.get("summary", {}).get("attendance_totals", {}).get("not_on_job", 0) if traxora_results else 0
                }
            },
            "alt_stats": {
                "total_drivers": len(alt_results) if alt_results is not None else 0,
                "date_range": f"{self.start_date} to {self.end_date}",
                "report_path": os.path.join(self.data_dir, "alt_attendance_report.xlsx") if alt_results is not None else None
            },
            "traxora_results": traxora_results,
            "alt_results": alt_results.to_dict() if alt_results is not None and not alt_results.empty else None
        }
        
        return comparison


def process_comparison_enhanced(start_date="2025-05-18", end_date="2025-05-24"):
    """
    Process the same data with both methods using the enhanced processor.
    
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
    
    # Create enhanced processor
    processor = EnhancedAttendanceProcessor(start_date, end_date)
    
    # Process with both methods
    comparison = processor.process_both_methods(
        driving_history_path,
        activity_detail_path,
        time_on_site_path
    )
    
    return comparison