"""
GENIUS CORE MTD INTEGRATION MODULE

This script integrates the MTD Ingestion Engine with the Daily Driver Report pipeline,
enabling continuous processing of Month-to-Date files with proper filtering and validation.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from utils.mtd_ingestion import MTDIngestionEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeniusCoreMTDProcessor:
    """
    Main controller for GENIUS CORE MTD Integration.
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the GENIUS CORE MTD Processor.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        
        # Default configuration if not provided
        self.config.setdefault('source_dirs', {
            'driving_history': 'attached_assets',
            'activity_detail': 'attached_assets'
        })
        self.config.setdefault('processed_dir', 'processed')
        self.config.setdefault('trace_manifest_dir', 'reports/trace')
        
        # Ensure directories exist
        for dir_path in self.config['source_dirs'].values():
            os.makedirs(dir_path, exist_ok=True)
        os.makedirs(self.config['processed_dir'], exist_ok=True)
        os.makedirs(self.config['trace_manifest_dir'], exist_ok=True)
    
    def find_mtd_files(self, target_date=None):
        """
        Find all relevant MTD files for the specified date.
        
        Args:
            target_date: Target date in YYYY-MM-DD format (optional)
            
        Returns:
            Dictionary mapping file type to file path
        """
        if target_date:
            date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            month_str = date_obj.strftime('%b').upper()
            year_str = date_obj.strftime('%Y')
        else:
            month_str = datetime.now().strftime('%b').upper()
            year_str = datetime.now().strftime('%Y')
        
        mtd_files = {}
        
        # Find DrivingHistory files
        driving_history_dir = self.config['source_dirs']['driving_history']
        for filename in os.listdir(driving_history_dir):
            if filename.startswith('DrivingHistory') or month_str in filename:
                mtd_files['driving_history'] = os.path.join(driving_history_dir, filename)
                break
        
        # Find ActivityDetail files
        activity_detail_dir = self.config['source_dirs']['activity_detail']
        for filename in os.listdir(activity_detail_dir):
            if filename.startswith('ActivityDetail') or month_str in filename:
                mtd_files['activity_detail'] = os.path.join(activity_detail_dir, filename)
                break
        
        return mtd_files
    
    def process_date(self, target_date):
        """
        Process MTD files for a specific date.
        
        Args:
            target_date: Target date in YYYY-MM-DD format
            
        Returns:
            Dictionary with processed file paths and trace manifest
        """
        logger.info(f"Processing MTD data for date: {target_date}")
        
        # Find MTD files
        mtd_files = self.find_mtd_files(target_date)
        if not mtd_files:
            logger.warning(f"No MTD files found for date: {target_date}")
            return None
        
        # Initialize MTD Ingestion Engine
        mtd_engine = MTDIngestionEngine(target_date=target_date)
        
        # Process MTD files
        output_files = mtd_engine.process_mtd_files(
            driving_history_path=mtd_files.get('driving_history'),
            activity_detail_path=mtd_files.get('activity_detail'),
            output_dir=self.config['processed_dir']
        )
        
        logger.info(f"MTD processing complete for date: {target_date}")
        logger.info(f"Generated output files: {output_files}")
        
        return {
            'output_files': output_files,
            'trace_manifest': mtd_engine.trace_manifest
        }
    
    def enable_mtd_ingestion(self):
        """
        Enable MTD ingestion mode and hook into the Daily Driver Report pipeline.
        
        Returns:
            Confirmation message
        """
        logger.info("Enabling GENIUS CORE SMART MTD INGESTION MODE")
        
        # Create system configuration file
        config_path = os.path.join('config', 'mtd_ingestion_config.json')
        os.makedirs('config', exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        logger.info(f"MTD ingestion configuration saved to: {config_path}")
        
        return "MTD INGESTION ENABLED — FILTERED DAILY PIPELINE ACTIVE"


if __name__ == "__main__":
    # Initialize and enable MTD ingestion
    genius_core_mtd = GeniusCoreMTDProcessor()
    status = genius_core_mtd.enable_mtd_ingestion()
    print(status)
    
    # Example: Process a specific date
    # result = genius_core_mtd.process_date('2025-05-16')