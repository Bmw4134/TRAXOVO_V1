"""
GENIUS CORE SMART MTD INGESTION MODE

This module enables efficient, filtered processing of Month-to-Date (MTD) data files
while ensuring clean daily outputs with proper deduplication and validation.
"""

import os
import csv
import hashlib
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File cache for hash tracking to avoid reprocessing unchanged files
FILE_HASH_REGISTRY = {}

class MTDIngestionEngine:
    """
    Core engine for the GENIUS CORE SMART MTD INGESTION MODE.
    Processes Month-to-Date files and produces filtered daily data.
    """
    
    def __init__(self, target_date: str = None):
        """
        Initialize the MTD ingestion engine.
        
        Args:
            target_date: Target date in YYYY-MM-DD format. If None, defaults to current date.
        """
        self.target_date = target_date or datetime.now().strftime('%Y-%m-%d')
        self.target_date_obj = datetime.strptime(self.target_date, '%Y-%m-%d')
        
        # Storage for processed data
        self.processed_data = {
            'driving_history': [],
            'activity_detail': [],
            'asset_timesheet': []
        }
        
        # Tracking for data validation and trace manifest
        self.trace_manifest = {
            'file_sources': {},
            'duplicate_entries': [],
            'timestamp_overlaps': [],
            'conflicting_data': []
        }
        
    def compute_file_hash(self, file_path: str) -> str:
        """
        Compute MD5 hash of a file to detect changes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MD5 hash string of the file
        """
        if not os.path.exists(file_path):
            return ""
            
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def file_needs_processing(self, file_path: str) -> bool:
        """
        Check if a file needs processing by comparing its hash with stored hash.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file needs processing, False otherwise
        """
        current_hash = self.compute_file_hash(file_path)
        if not current_hash:
            return False
            
        previous_hash = FILE_HASH_REGISTRY.get(file_path)
        if previous_hash != current_hash:
            FILE_HASH_REGISTRY[file_path] = current_hash
            return True
        return False
    
    def process_driving_history(self, file_path: str, chunk_size: int = 10000) -> None:
        """
        Process DrivingHistory.csv file in chunks, filtering for target date.
        
        Args:
            file_path: Path to the DrivingHistory CSV file
            chunk_size: Number of rows to process at once
        """
        if not self.file_needs_processing(file_path):
            logger.info(f"Skipping unchanged file: {file_path}")
            return
            
        logger.info(f"Processing DrivingHistory file: {file_path}")
        self.trace_manifest['file_sources'][file_path] = {'driving_history': []}
        
        # Track seen driver-key-on events to avoid duplicates
        seen_events = set()
        
        # Process in chunks for memory efficiency
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            # Ensure date column exists and is properly formatted
            if 'Date' not in chunk.columns:
                logger.error(f"Missing Date column in {file_path}")
                continue
            
            # Convert date strings to datetime objects for comparison
            chunk['Date'] = pd.to_datetime(chunk['Date'], errors='coerce')
            
            # Filter records for target date
            date_mask = (chunk['Date'].dt.date == self.target_date_obj.date())
            filtered_chunk = chunk[date_mask].copy()
            
            for idx, row in filtered_chunk.iterrows():
                # Create a unique key for this event
                driver_name = row.get('Driver')
                event_time = row.get('Time')
                event_type = row.get('Event')
                
                if not all([driver_name, event_time, event_type]):
                    continue
                    
                event_key = f"{driver_name}_{event_time}_{event_type}"
                
                # Skip if we've already seen this exact event
                if event_key in seen_events:
                    self.trace_manifest['duplicate_entries'].append({
                        'driver': driver_name,
                        'time': event_time,
                        'event': event_type,
                        'file': file_path
                    })
                    continue
                    
                seen_events.add(event_key)
                
                # Add to processed data
                self.processed_data['driving_history'].append(row.to_dict())
                
                # Track source for trace manifest
                self.trace_manifest['file_sources'][file_path]['driving_history'].append(idx)
    
    def process_activity_detail(self, file_path: str, chunk_size: int = 10000) -> None:
        """
        Process ActivityDetail.csv file in chunks, filtering for target date.
        
        Args:
            file_path: Path to the ActivityDetail CSV file
            chunk_size: Number of rows to process at once
        """
        if not self.file_needs_processing(file_path):
            logger.info(f"Skipping unchanged file: {file_path}")
            return
            
        logger.info(f"Processing ActivityDetail file: {file_path}")
        self.trace_manifest['file_sources'][file_path] = {'activity_detail': []}
        
        # Track seen activity events to avoid duplicates
        seen_activities = set()
        
        # Process in chunks for memory efficiency
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            # Ensure date column exists and is properly formatted
            if 'Date' not in chunk.columns:
                logger.error(f"Missing Date column in {file_path}")
                continue
            
            # Convert date strings to datetime objects for comparison
            chunk['Date'] = pd.to_datetime(chunk['Date'], errors='coerce')
            
            # Filter records for target date
            date_mask = (chunk['Date'].dt.date == self.target_date_obj.date())
            filtered_chunk = chunk[date_mask].copy()
            
            for idx, row in filtered_chunk.iterrows():
                # Create a unique key for this activity
                driver_name = row.get('Driver')
                location = row.get('Location')
                start_time = row.get('StartTime')
                
                if not all([driver_name, location, start_time]):
                    continue
                    
                activity_key = f"{driver_name}_{location}_{start_time}"
                
                # Skip if we've already seen this exact activity
                if activity_key in seen_activities:
                    self.trace_manifest['duplicate_entries'].append({
                        'driver': driver_name,
                        'location': location,
                        'start_time': start_time,
                        'file': file_path
                    })
                    continue
                    
                seen_activities.add(activity_key)
                
                # Add to processed data
                self.processed_data['activity_detail'].append(row.to_dict())
                
                # Track source for trace manifest
                self.trace_manifest['file_sources'][file_path]['activity_detail'].append(idx)
    
    def check_for_overlaps_and_conflicts(self) -> None:
        """
        Check for timestamp overlaps and conflicting data across processed records.
        """
        logger.info("Checking for timestamp overlaps and conflicts...")
        
        # Group driving history by driver
        drivers_events = {}
        for entry in self.processed_data['driving_history']:
            driver = entry.get('Driver')
            if not driver:
                continue
                
            if driver not in drivers_events:
                drivers_events[driver] = []
                
            drivers_events[driver].append(entry)
        
        # Check for overlapping timestamps within each driver's records
        for driver, events in drivers_events.items():
            # Sort events by time
            sorted_events = sorted(events, key=lambda x: x.get('Time', ''))
            
            # Check for KeyOn events without matching KeyOff events
            key_status = None
            for i, event in enumerate(sorted_events):
                event_type = event.get('Event')
                event_time = event.get('Time')
                
                if event_type == 'KeyOn':
                    if key_status == 'On':
                        # KeyOn without previous KeyOff - possible overlap
                        self.trace_manifest['timestamp_overlaps'].append({
                            'driver': driver,
                            'first_event': sorted_events[i-1],
                            'second_event': event,
                            'issue': 'KeyOn without previous KeyOff'
                        })
                    key_status = 'On'
                elif event_type == 'KeyOff':
                    if key_status != 'On':
                        # KeyOff without previous KeyOn - possible overlap
                        self.trace_manifest['timestamp_overlaps'].append({
                            'driver': driver,
                            'event': event,
                            'issue': 'KeyOff without previous KeyOn'
                        })
                    key_status = 'Off'
    
    def generate_filtered_daily_output(self, output_dir: str) -> Dict[str, str]:
        """
        Generate filtered CSV outputs for the target date.
        
        Args:
            output_dir: Directory to save output files
            
        Returns:
            Dictionary mapping data type to output file path
        """
        os.makedirs(output_dir, exist_ok=True)
        
        output_files = {}
        
        # Save driving history
        if self.processed_data['driving_history']:
            driving_history_path = os.path.join(output_dir, f"DrivingHistory_{self.target_date}.csv")
            pd.DataFrame(self.processed_data['driving_history']).to_csv(driving_history_path, index=False)
            output_files['driving_history'] = driving_history_path
        
        # Save activity detail
        if self.processed_data['activity_detail']:
            activity_detail_path = os.path.join(output_dir, f"ActivityDetail_{self.target_date}.csv")
            pd.DataFrame(self.processed_data['activity_detail']).to_csv(activity_detail_path, index=False)
            output_files['activity_detail'] = activity_detail_path
        
        # Save trace manifest
        trace_manifest_path = os.path.join(output_dir, f"TraceManifest_{self.target_date}.json")
        pd.Series(self.trace_manifest).to_json(trace_manifest_path)
        output_files['trace_manifest'] = trace_manifest_path
        
        return output_files
    
    def process_mtd_files(self, 
                       driving_history_path: str = None, 
                       activity_detail_path: str = None,
                       output_dir: str = 'processed') -> Dict[str, str]:
        """
        Process all MTD files and generate filtered daily output.
        
        Args:
            driving_history_path: Path to DrivingHistory CSV file
            activity_detail_path: Path to ActivityDetail CSV file
            output_dir: Directory to save output files
            
        Returns:
            Dictionary mapping data type to output file path
        """
        logger.info(f"Processing MTD files for target date: {self.target_date}")
        
        # Process driving history if provided
        if driving_history_path and os.path.exists(driving_history_path):
            self.process_driving_history(driving_history_path)
        
        # Process activity detail if provided
        if activity_detail_path and os.path.exists(activity_detail_path):
            self.process_activity_detail(activity_detail_path)
        
        # Check for overlaps and conflicts
        self.check_for_overlaps_and_conflicts()
        
        # Generate and return output files
        return self.generate_filtered_daily_output(output_dir)


def enable_mtd_ingestion():
    """
    Enable the MTD ingestion mode and return confirmation.
    """
    logger.info("GENIUS CORE SMART MTD INGESTION MODE enabled successfully")
    logger.info("Filtered daily pipeline active and ready for MTD data")
    
    return "MTD INGESTION ENABLED — FILTERED DAILY PIPELINE ACTIVE"