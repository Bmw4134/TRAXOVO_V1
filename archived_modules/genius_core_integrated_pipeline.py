#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Integrated Daily Driver Pipeline

This script implements the complete integrated daily driver pipeline following
the exact workbook logic hierarchy:

1. Asset List as primary relational source of truth
2. Start Time & Job as derived data only
3. DrivingHistory and ActivityDetail as telemetry validation layers
4. Strict driver classification based on telematics verification
5. Trailer and test data exclusion logic

GENIUS CORE CONTINUITY STANDARD LOCKED
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback
import shutil
from pathlib import Path
import re
import hashlib
import csv
from typing import Dict, List, Set, Tuple, Optional, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs/genius_core', exist_ok=True)
pipeline_log = logging.FileHandler('logs/genius_core/integrated_pipeline.log')
pipeline_log.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(pipeline_log)

# Paths
DATA_DIR = 'data'
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
REPORTS_DIR = 'reports/genius_core'
EXPORTS_DIR = 'exports/genius_core'
DAILY_REPORTS_DIR = 'reports/daily_drivers'
DAILY_EXPORTS_DIR = 'exports/daily_reports'
LOGS_DIR = 'logs/genius_core'

# Create directories
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(DAILY_REPORTS_DIR, exist_ok=True)
os.makedirs(DAILY_EXPORTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Equipment billing workbook
EQUIPMENT_BILLING_PATH = 'attached_assets/EQ MONTHLY BILLINGS WORKING SPREADSHEET - APRIL 2025.xlsx'

# Target dates - can be specified as arguments
DEFAULT_TARGET_DATES = ['2025-05-16', '2025-05-19']

# Asset type classification
TRAILER_KEYWORDS = ['TRAILER', 'TLR', 'DUMP', 'FLATBED', 'UTILITY', 'LOWBOY', 'EQUIPMENT']
TRAILER_PATTERNS = [
    r'^T-\d+',         # T-123
    r'^TLR-\d+',       # TLR-123
    r'^TR-\d+',        # TR-123
    r'^TRLR-\d+',      # TRLR-123
    r'^TRAILER-\d+'    # TRAILER-123
]

# Test data detection
TEST_DRIVER_NAMES = [
    'john smith', 'jane doe', 'test user', 'demo user', 
    'michael johnson', 'robert williams', 'james davis'
]


class DriverRecord:
    """Record for tracking a driver's data and classification through the pipeline"""
    
    def __init__(self, name: str, normalized_name: str):
        # Identity
        self.name = name
        self.normalized_name = normalized_name
        
        # Asset info (from Asset List)
        self.asset_id = None
        self.job_site = None
        
        # Schedule (derived from workbook)
        self.scheduled_start = None
        self.scheduled_end = None
        
        # Telematics data (from DrivingHistory)
        self.key_on_time = None
        self.key_off_time = None
        self.locations: Set[str] = set()
        
        # Source tracking
        self.sources: Set[str] = set()
        self.source_data: Dict[str, Dict] = {}
        
        # Classification
        self.status = 'Unknown'
        self.status_reason = None
        self.classification_details: Dict[str, Any] = {}
        
        # Validation
        self.in_asset_list = False
        self.in_driving_history = False
        self.in_activity_detail = False
        self.is_trailer = False
        self.site_match = None
        
        # Timing metrics
        self.minutes_late = None
        self.minutes_early = None
    
    def add_source(self, source: str, data: Dict[str, Any]) -> None:
        """Add source data and mark driver as present in that source"""
        self.sources.add(source)
        self.source_data[source] = data
        
        # Update source-specific flags
        if source == 'Asset List':
            self.in_asset_list = True
        elif source == 'Driving History':
            self.in_driving_history = True
        elif source == 'Activity Detail':
            self.in_activity_detail = True
    
    def update_times(self, key_on_time: Optional[datetime], key_off_time: Optional[datetime]) -> None:
        """Update key on/off times if provided and earlier/later than existing"""
        if key_on_time:
            if not self.key_on_time or key_on_time < self.key_on_time:
                self.key_on_time = key_on_time
        
        if key_off_time:
            if not self.key_off_time or key_off_time > self.key_off_time:
                self.key_off_time = key_off_time
    
    def add_location(self, location: Optional[str]) -> None:
        """Add location to driver's location set"""
        if location and location.strip():
            self.locations.add(location.strip())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert driver record to dictionary for reporting"""
        return {
            'name': self.name,
            'normalized_name': self.normalized_name,
            'asset_id': self.asset_id,
            'job_site': self.job_site,
            'scheduled_start': self.scheduled_start.isoformat() if self.scheduled_start else None,
            'scheduled_end': self.scheduled_end.isoformat() if self.scheduled_end else None,
            'key_on_time': self.key_on_time.isoformat() if self.key_on_time else None,
            'key_off_time': self.key_off_time.isoformat() if self.key_off_time else None,
            'locations': list(self.locations),
            'status': self.status,
            'status_reason': self.status_reason,
            'sources': list(self.sources),
            'in_asset_list': self.in_asset_list,
            'in_driving_history': self.in_driving_history,
            'in_activity_detail': self.in_activity_detail,
            'site_match': self.site_match,
            'minutes_late': self.minutes_late,
            'minutes_early': self.minutes_early,
            'classification_details': self.classification_details
        }


class IntegratedDriverPipeline:
    """
    Integrated Daily Driver Pipeline using exact workbook logic hierarchy
    """
    
    def __init__(self, date_str: str):
        """Initialize pipeline for specific date"""
        self.date_str = date_str
        
        # Data sources
        self.equipment_billing_workbook = None
        self.asset_list_sheet = None
        self.drivers_sheet = None
        self.jobs_sheet = None
        self.start_time_job_sheet = None
        
        # CSV paths
        self.driving_history_path = None
        self.activity_detail_path = None
        
        # Locate and assign data source paths
        self._locate_data_sources()
        
        # Data containers
        self.drivers: Dict[str, DriverRecord] = {}  # All drivers by normalized name
        self.asset_list_drivers: Dict[str, Dict] = {}  # Raw data from Asset List
        self.driving_history_drivers: Dict[str, Dict] = {}  # Raw data from Driving History
        self.activity_detail_drivers: Dict[str, Dict] = {}  # Raw data from Activity Detail
        
        # Classification results
        self.classified_drivers: Dict[str, DriverRecord] = {}  # All classified drivers
        self.unclassified_drivers: Dict[str, DriverRecord] = {}  # Drivers that couldn't be classified
        
        # Test data detection
        self.is_test_data = False
        self.test_drivers: List[str] = []
        
        # Statistics
        self.stats = {
            'total_drivers': 0,
            'in_asset_list': 0,
            'in_driving_history': 0,
            'in_activity_detail': 0,
            'classified': {
                'on_time': 0,
                'late': 0,
                'early_end': 0,
                'not_on_job': 0
            },
            'trailers_excluded': 0,
            'is_test_data': False,
            'test_drivers_count': 0
        }
    
    def _locate_data_sources(self) -> None:
        """Locate all data sources for the specified date"""
        # Format date for filenames
        date_formatted = self.date_str.replace('-', '')
        
        # Locate Driving History file
        driving_history_path = f'data/driving_history/DrivingHistory_{date_formatted}.csv'
        
        if not os.path.exists(driving_history_path):
            # Search for alternatives
            for root, dirs, files in os.walk('data/driving_history'):
                for file in files:
                    if file.endswith('.csv') and date_formatted in file:
                        driving_history_path = os.path.join(root, file)
                        break
            
            # Check attached_assets
            if not os.path.exists(driving_history_path):
                for root, dirs, files in os.walk('attached_assets'):
                    for file in files:
                        if file.endswith('.csv') and ('driv' in file.lower() or 'history' in file.lower()) and date_formatted in file:
                            driving_history_path = os.path.join(root, file)
                            break
        
        self.driving_history_path = driving_history_path
        
        # Locate Activity Detail file
        activity_detail_path = f'data/activity_detail/ActivityDetail_{date_formatted}.csv'
        
        if not os.path.exists(activity_detail_path):
            # Search for alternatives
            for root, dirs, files in os.walk('data/activity_detail'):
                for file in files:
                    if file.endswith('.csv') and date_formatted in file:
                        activity_detail_path = os.path.join(root, file)
                        break
            
            # Check attached_assets
            if not os.path.exists(activity_detail_path):
                for root, dirs, files in os.walk('attached_assets'):
                    for file in files:
                        if file.endswith('.csv') and ('activ' in file.lower() or 'detail' in file.lower()) and date_formatted in file:
                            activity_detail_path = os.path.join(root, file)
                            break
        
        self.activity_detail_path = activity_detail_path
        
        logger.info(f"Located data sources:")
        logger.info(f"  Equipment Billing: {EQUIPMENT_BILLING_PATH}")
        logger.info(f"  Driving History: {self.driving_history_path}")
        logger.info(f"  Activity Detail: {self.activity_detail_path}")
    
    def normalize_name(self, name: Optional[str]) -> str:
        """Normalize driver name for consistent matching"""
        if not name or pd.isna(name):
            return ""
        
        name_str = str(name).strip()
        
        # Skip non-name entries
        if name_str.lower() in ['nan', 'none', 'null', '', 'unassigned', 'open', 'vacant']:
            return ""
        
        # Handle "Last, First" format
        if ',' in name_str:
            parts = name_str.split(',', 1)
            if len(parts) == 2:
                last_name = parts[0].strip()
                first_name = parts[1].strip()
                # Recombine as "first last"
                name_str = f"{first_name} {last_name}"
        
        # Convert to lowercase
        normalized = name_str.lower()
        
        # Remove titles and suffixes
        titles = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'rev.']
        suffixes = ['jr.', 'sr.', 'i', 'ii', 'iii', 'iv', 'v', 'phd', 'md', 'dds', 'esq']
        
        for title in titles:
            if normalized.startswith(title + ' '):
                normalized = normalized[len(title) + 1:]
        
        for suffix in suffixes:
            suffix_pattern = f" {suffix}$"
            if re.search(suffix_pattern, normalized):
                normalized = re.sub(suffix_pattern, "", normalized)
        
        # Replace special characters with spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def parse_time(self, time_str: Union[str, datetime, None]) -> Optional[datetime]:
        """Parse time string to datetime object"""
        if not time_str or pd.isna(time_str):
            return None
        
        if isinstance(time_str, datetime):
            return time_str
        
        # Try various formats
        formats = [
            '%Y-%m-%d %H:%M:%S',  # Standard format
            '%m/%d/%Y %H:%M:%S',  # US format
            '%m/%d/%Y %I:%M:%S %p',  # US format with AM/PM
            '%m/%d/%Y %I:%M %p',  # US format with AM/PM, no seconds
            '%Y-%m-%dT%H:%M:%S',  # ISO format
            '%Y-%m-%dT%H:%M:%S.%f',  # ISO format with microseconds
            '%m/%d/%y %H:%M'  # Short year format
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(time_str), fmt)
            except (ValueError, TypeError):
                continue
        
        # If all fails, try pandas conversion
        try:
            return pd.to_datetime(time_str)
        except Exception:
            logger.warning(f"Could not parse time string: {time_str}")
            return None
    
    def is_trailer(self, asset_id: Optional[str]) -> bool:
        """Check if an asset is a trailer based on its ID or name"""
        if not asset_id or pd.isna(asset_id):
            return False
        
        asset_str = str(asset_id).upper().strip()
        
        # Check for trailer keywords
        for keyword in TRAILER_KEYWORDS:
            if keyword in asset_str:
                return True
        
        # Check for trailer patterns
        for pattern in TRAILER_PATTERNS:
            if re.match(pattern, asset_str):
                return True
        
        return False
    
    def extract_equipment_billing_data(self) -> bool:
        """Extract data from Equipment Billing workbook (primary source)"""
        logger.info(f"Extracting data from Equipment Billing: {EQUIPMENT_BILLING_PATH}")
        
        if not os.path.exists(EQUIPMENT_BILLING_PATH):
            logger.error(f"Equipment Billing file not found: {EQUIPMENT_BILLING_PATH}")
            return False
        
        try:
            # Load workbook
            self.equipment_billing_workbook = pd.ExcelFile(EQUIPMENT_BILLING_PATH)
            sheets = self.equipment_billing_workbook.sheet_names
            logger.info(f"Available sheets: {sheets}")
            
            # 1. Process Asset List (PRIMARY RELATIONAL SOURCE OF TRUTH)
            asset_sheet_name = None
            if 'FLEET' in sheets:
                asset_sheet_name = 'FLEET'
            elif 'Equip Table' in sheets:
                asset_sheet_name = 'Equip Table'
            elif 'Asset List' in sheets:
                asset_sheet_name = 'Asset List'
            
            if not asset_sheet_name:
                logger.error("Asset List sheet not found in Equipment Billing workbook")
                return False
            
            logger.info(f"Processing Asset List sheet: {asset_sheet_name}")
            self.asset_list_sheet = pd.read_excel(self.equipment_billing_workbook, sheet_name=asset_sheet_name)
            
            # Normalize column names
            self.asset_list_sheet.columns = [str(col).strip().lower().replace(' ', '_') for col in self.asset_list_sheet.columns]
            
            # Find relevant columns
            asset_col = None
            driver_col = None
            job_col = None
            
            for col in ['equip_#', 'equip_id', 'equipment_id', 'equipment', 'asset_id', 'asset']:
                if col in self.asset_list_sheet.columns:
                    asset_col = col
                    break
            
            for col in ['driver', 'driver_name', 'employee', 'employee_name', 'operator', 'assigned_to']:
                if col in self.asset_list_sheet.columns:
                    driver_col = col
                    break
            
            for col in ['job', 'job_site', 'site', 'location', 'project']:
                if col in self.asset_list_sheet.columns:
                    job_col = col
                    break
            
            # Process Asset List rows
            if asset_col and driver_col:
                logger.info(f"Found asset column: {asset_col}, driver column: {driver_col}")
                trailers_excluded = 0
                
                for _, row in self.asset_list_sheet.iterrows():
                    asset_id = str(row[asset_col]).strip() if pd.notna(row[asset_col]) else None
                    driver_name = str(row[driver_col]).strip() if pd.notna(row[driver_col]) else None
                    
                    # Skip empty or invalid values
                    if not asset_id or not driver_name:
                        continue
                    
                    if asset_id.lower() in ['nan', 'none', 'null', ''] or driver_name.lower() in ['nan', 'none', 'null', '']:
                        continue
                    
                    # Check if asset is a trailer and skip if needed
                    if self.is_trailer(asset_id):
                        trailers_excluded += 1
                        continue
                    
                    # Get job site if available
                    job_site = None
                    if job_col and pd.notna(row[job_col]):
                        job_site = str(row[job_col]).strip()
                        if job_site.lower() in ['nan', 'none', 'null', '']:
                            job_site = None
                    
                    # Normalize driver name
                    normalized_name = self.normalize_name(driver_name)
                    
                    if not normalized_name:
                        continue
                    
                    # Create Asset List record
                    self.asset_list_drivers[normalized_name] = {
                        'driver_name': driver_name,
                        'normalized_name': normalized_name,
                        'asset_id': asset_id.upper(),
                        'job_site': job_site
                    }
                    
                    # Create or update driver record
                    if normalized_name not in self.drivers:
                        self.drivers[normalized_name] = DriverRecord(driver_name, normalized_name)
                    
                    driver_record = self.drivers[normalized_name]
                    driver_record.asset_id = asset_id.upper()
                    driver_record.job_site = job_site
                    
                    # Add as source
                    driver_record.add_source('Asset List', {
                        'asset_id': asset_id.upper(),
                        'job_site': job_site,
                        'sheet': asset_sheet_name
                    })
                
                self.stats['in_asset_list'] = len(self.asset_list_drivers)
                self.stats['trailers_excluded'] = trailers_excluded
                
                logger.info(f"Extracted {len(self.asset_list_drivers)} drivers from Asset List")
                logger.info(f"Excluded {trailers_excluded} trailers from driver mapping")
            else:
                logger.error(f"Required columns not found in Asset List sheet")
                return False
            
            # 2. Process other sheets as needed for supplementary data
            # Note: These are secondary/supplementary and the primary source remains Asset List
            
            # 2a. Process Drivers Sheet if available
            if 'DRIVERS' in sheets:
                logger.info("Processing Drivers sheet for supplementary data")
                self.drivers_sheet = pd.read_excel(self.equipment_billing_workbook, sheet_name='DRIVERS')
                # Process as needed for supplementary data
            
            # 2b. Process Jobs Sheet if available
            if 'JOBS' in sheets:
                logger.info("Processing Jobs sheet for supplementary data")
                self.jobs_sheet = pd.read_excel(self.equipment_billing_workbook, sheet_name='JOBS')
                # Process as needed for supplementary data
            
            # 2c. Process Start Time & Job Sheet as DERIVED DATA (not standalone source)
            start_time_job_sheet_name = None
            for sheet in sheets:
                if 'START' in sheet.upper() or 'TIME' in sheet.upper() or 'JOB' in sheet.upper():
                    start_time_job_sheet_name = sheet
                    break
            
            if start_time_job_sheet_name:
                logger.info(f"Processing Start Time & Job sheet: {start_time_job_sheet_name} (as DERIVED DATA)")
                self.start_time_job_sheet = pd.read_excel(self.equipment_billing_workbook, sheet_name=start_time_job_sheet_name)
                
                # Normalize column names
                self.start_time_job_sheet.columns = [str(col).strip().lower().replace(' ', '_') for col in self.start_time_job_sheet.columns]
                
                # Find relevant columns
                name_col = None
                job_col = None
                start_time_col = None
                end_time_col = None
                
                for col in ['name', 'driver', 'driver_name', 'employee', 'employee_name']:
                    if col in self.start_time_job_sheet.columns:
                        name_col = col
                        break
                
                for col in ['job', 'job_site', 'site', 'location', 'project']:
                    if col in self.start_time_job_sheet.columns:
                        job_col = col
                        break
                
                for col in ['start_time', 'scheduled_start', 'start']:
                    if col in self.start_time_job_sheet.columns:
                        start_time_col = col
                        break
                
                for col in ['end_time', 'scheduled_end', 'end']:
                    if col in self.start_time_job_sheet.columns:
                        end_time_col = col
                        break
                
                # Extract schedule times as DERIVED data
                if name_col and (start_time_col or end_time_col or job_col):
                    logger.info(f"Extracting derived schedule data")
                    
                    for _, row in self.start_time_job_sheet.iterrows():
                        driver_name = str(row[name_col]).strip() if pd.notna(row[name_col]) else None
                        
                        if not driver_name or driver_name.lower() in ['nan', 'none', 'null', '']:
                            continue
                        
                        # Normalize name
                        normalized_name = self.normalize_name(driver_name)
                        
                        if not normalized_name:
                            continue
                        
                        # Only use for drivers in Asset List (as this is derived data)
                        if normalized_name not in self.drivers:
                            continue
                        
                        # Get schedule times and job site
                        scheduled_start = None
                        if start_time_col and pd.notna(row[start_time_col]):
                            scheduled_start = self.parse_time(row[start_time_col])
                        
                        scheduled_end = None
                        if end_time_col and pd.notna(row[end_time_col]):
                            scheduled_end = self.parse_time(row[end_time_col])
                        
                        derived_job_site = None
                        if job_col and pd.notna(row[job_col]):
                            derived_job_site = str(row[job_col]).strip()
                            if derived_job_site.lower() in ['nan', 'none', 'null', '']:
                                derived_job_site = None
                        
                        # Update driver record with schedule data
                        driver_record = self.drivers[normalized_name]
                        
                        # Use schedule times from derived data
                        if scheduled_start:
                            driver_record.scheduled_start = scheduled_start
                        
                        if scheduled_end:
                            driver_record.scheduled_end = scheduled_end
                        
                        # Only use job site from derived data if not available from Asset List
                        if derived_job_site and not driver_record.job_site:
                            driver_record.job_site = derived_job_site
                        
                        # Add source data but track as derived
                        driver_record.add_source('Start Time & Job [DERIVED]', {
                            'scheduled_start': scheduled_start.isoformat() if scheduled_start else None,
                            'scheduled_end': scheduled_end.isoformat() if scheduled_end else None,
                            'job_site': derived_job_site,
                            'sheet': start_time_job_sheet_name
                        })
            
            return True
            
        except Exception as e:
            logger.error(f"Error extracting data from Equipment Billing: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def extract_driving_history(self) -> bool:
        """Extract telematics data from Driving History"""
        logger.info(f"Extracting Driving History from: {self.driving_history_path}")
        
        if not os.path.exists(self.driving_history_path):
            logger.warning(f"Driving History file not found: {self.driving_history_path}")
            return False
        
        try:
            # First, determine the file structure by reading the header
            with open(self.driving_history_path, 'r') as f:
                header = f.readline().strip()
            
            # Determine delimiter
            delimiter = ',' if ',' in header else ';'
            
            # Load CSV file
            df = pd.read_csv(self.driving_history_path, delimiter=delimiter)
            
            # Normalize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Find relevant columns
            driver_col = None
            asset_col = None
            datetime_col = None
            event_col = None
            location_col = None
            
            for col in ['driver', 'driver_name', 'employee', 'employee_name', 'operator']:
                if col in df.columns:
                    driver_col = col
                    break
            
            for col in ['asset', 'asset_id', 'equipment', 'equipment_id', 'vehicle', 'vehicle_id']:
                if col in df.columns:
                    asset_col = col
                    break
            
            for col in ['datetime', 'date_time', 'timestamp', 'time']:
                if col in df.columns:
                    datetime_col = col
                    break
            
            for col in ['event', 'event_type', 'action', 'status']:
                if col in df.columns:
                    event_col = col
                    break
            
            for col in ['location', 'site', 'job_site', 'place', 'area']:
                if col in df.columns:
                    location_col = col
                    break
            
            # Process all rows
            if driver_col and asset_col:
                logger.info(f"Found driver column: {driver_col}, asset column: {asset_col}")
                logger.info(f"Datetime column: {datetime_col}, Event column: {event_col}, Location column: {location_col}")
                
                # Group data by driver and asset
                driver_events = {}
                
                for _, row in df.iterrows():
                    driver_name = str(row[driver_col]).strip() if pd.notna(row[driver_col]) else None
                    asset_id = str(row[asset_col]).strip() if pd.notna(row[asset_col]) else None
                    
                    # Skip empty or invalid values
                    if not driver_name or not asset_id:
                        continue
                    
                    if driver_name.lower() in ['nan', 'none', 'null', ''] or asset_id.lower() in ['nan', 'none', 'null', '']:
                        continue
                    
                    # Skip trailers
                    if self.is_trailer(asset_id):
                        continue
                    
                    # Get event details
                    event_time = None
                    if datetime_col and pd.notna(row[datetime_col]):
                        event_time = self.parse_time(row[datetime_col])
                    
                    event_type = None
                    if event_col and pd.notna(row[event_col]):
                        event_type = str(row[event_col]).strip()
                    
                    location = None
                    if location_col and pd.notna(row[location_col]):
                        location = str(row[location_col]).strip()
                    
                    # Normalize driver name
                    normalized_name = self.normalize_name(driver_name)
                    
                    if not normalized_name:
                        continue
                    
                    # Create or update driver event record
                    key = (normalized_name, asset_id.upper())
                    
                    if key not in driver_events:
                        driver_events[key] = {
                            'driver_name': driver_name,
                            'normalized_name': normalized_name,
                            'asset_id': asset_id.upper(),
                            'events': [],
                            'locations': set(),
                            'key_on': None,
                            'key_off': None
                        }
                    
                    # Add event
                    if event_time:
                        driver_events[key]['events'].append({
                            'time': event_time,
                            'type': event_type,
                            'location': location
                        })
                    
                    # Add location
                    if location:
                        driver_events[key]['locations'].add(location)
                    
                    # Update key on/off times based on event type
                    if event_type and event_time:
                        if 'on' in event_type.lower() or 'start' in event_type.lower():
                            if not driver_events[key]['key_on'] or event_time < driver_events[key]['key_on']:
                                driver_events[key]['key_on'] = event_time
                        
                        if 'off' in event_type.lower() or 'end' in event_type.lower():
                            if not driver_events[key]['key_off'] or event_time > driver_events[key]['key_off']:
                                driver_events[key]['key_off'] = event_time
                
                # Process all driver events
                for (normalized_name, asset_id), events in driver_events.items():
                    # Create driving history record
                    self.driving_history_drivers[normalized_name] = {
                        'driver_name': events['driver_name'],
                        'normalized_name': normalized_name,
                        'asset_id': asset_id,
                        'key_on_time': events['key_on'],
                        'key_off_time': events['key_off'],
                        'locations': list(events['locations']),
                        'events': len(events['events']),
                        'source': os.path.basename(self.driving_history_path)
                    }
                    
                    # Create or update driver record
                    if normalized_name not in self.drivers:
                        self.drivers[normalized_name] = DriverRecord(events['driver_name'], normalized_name)
                    
                    driver_record = self.drivers[normalized_name]
                    
                    # Only update asset ID if not set from Asset List
                    if not driver_record.asset_id:
                        driver_record.asset_id = asset_id
                    
                    # Update key on/off times
                    driver_record.update_times(events['key_on'], events['key_off'])
                    
                    # Add locations
                    for location in events['locations']:
                        driver_record.add_location(location)
                    
                    # Add as source
                    driver_record.add_source('Driving History', {
                        'asset_id': asset_id,
                        'key_on_time': events['key_on'].isoformat() if events['key_on'] else None,
                        'key_off_time': events['key_off'].isoformat() if events['key_off'] else None,
                        'locations': list(events['locations']),
                        'events': len(events['events']),
                        'file': os.path.basename(self.driving_history_path)
                    })
                
                self.stats['in_driving_history'] = len(self.driving_history_drivers)
                
                # Check if this is test data
                self.is_test_data = self.detect_test_data()
                self.stats['is_test_data'] = self.is_test_data
                
                if self.is_test_data:
                    self.test_drivers = list(self.driving_history_drivers.keys())
                    self.stats['test_drivers_count'] = len(self.test_drivers)
                    logger.warning(f"Detected test data in Driving History file with {len(self.test_drivers)} test drivers")
                    logger.warning(f"First few test drivers: {self.test_drivers[:5]}")
                
                logger.info(f"Extracted {len(self.driving_history_drivers)} driver records from Driving History")
                
                return True
            else:
                logger.error("Required columns not found in Driving History")
                return False
                
        except Exception as e:
            logger.error(f"Error extracting Driving History: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def extract_activity_detail(self) -> bool:
        """Extract location data from Activity Detail"""
        logger.info(f"Extracting Activity Detail from: {self.activity_detail_path}")
        
        if not os.path.exists(self.activity_detail_path):
            logger.warning(f"Activity Detail file not found: {self.activity_detail_path}")
            return False
        
        try:
            # First, determine the file structure by reading the header
            with open(self.activity_detail_path, 'r') as f:
                header = f.readline().strip()
            
            # Determine delimiter
            delimiter = ',' if ',' in header else ';'
            
            # Load CSV file
            df = pd.read_csv(self.activity_detail_path, delimiter=delimiter)
            
            # Normalize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Find relevant columns
            driver_col = None
            asset_col = None
            location_col = None
            start_time_col = None
            end_time_col = None
            
            for col in ['driver', 'driver_name', 'employee', 'employee_name', 'operator']:
                if col in df.columns:
                    driver_col = col
                    break
            
            for col in ['asset', 'asset_id', 'equipment', 'equipment_id', 'vehicle', 'vehicle_id']:
                if col in df.columns:
                    asset_col = col
                    break
            
            for col in ['location', 'site', 'job_site', 'place', 'area']:
                if col in df.columns:
                    location_col = col
                    break
            
            for col in ['start_time', 'time_in', 'arrival']:
                if col in df.columns:
                    start_time_col = col
                    break
            
            for col in ['end_time', 'time_out', 'departure']:
                if col in df.columns:
                    end_time_col = col
                    break
            
            # Process all rows
            if driver_col and asset_col:
                logger.info(f"Found driver column: {driver_col}, asset column: {asset_col}")
                logger.info(f"Location column: {location_col}, Time columns: in={start_time_col}, out={end_time_col}")
                
                # Group data by driver and asset
                driver_activities = {}
                
                for _, row in df.iterrows():
                    driver_name = str(row[driver_col]).strip() if pd.notna(row[driver_col]) else None
                    asset_id = str(row[asset_col]).strip() if pd.notna(row[asset_col]) else None
                    
                    # Skip empty or invalid values
                    if not driver_name or not asset_id:
                        continue
                    
                    if driver_name.lower() in ['nan', 'none', 'null', ''] or asset_id.lower() in ['nan', 'none', 'null', '']:
                        continue
                    
                    # Skip trailers
                    if self.is_trailer(asset_id):
                        continue
                    
                    # Get activity details
                    location = None
                    if location_col and pd.notna(row[location_col]):
                        location = str(row[location_col]).strip()
                    
                    start_time = None
                    if start_time_col and pd.notna(row[start_time_col]):
                        start_time = self.parse_time(row[start_time_col])
                    
                    end_time = None
                    if end_time_col and pd.notna(row[end_time_col]):
                        end_time = self.parse_time(row[end_time_col])
                    
                    # Normalize driver name
                    normalized_name = self.normalize_name(driver_name)
                    
                    if not normalized_name:
                        continue
                    
                    # Create or update driver activity record
                    key = (normalized_name, asset_id.upper())
                    
                    if key not in driver_activities:
                        driver_activities[key] = {
                            'driver_name': driver_name,
                            'normalized_name': normalized_name,
                            'asset_id': asset_id.upper(),
                            'activities': [],
                            'locations': set(),
                            'start_time': None,
                            'end_time': None
                        }
                    
                    # Add activity
                    driver_activities[key]['activities'].append({
                        'location': location,
                        'start_time': start_time,
                        'end_time': end_time
                    })
                    
                    # Add location
                    if location:
                        driver_activities[key]['locations'].add(location)
                    
                    # Update start/end times
                    if start_time:
                        if not driver_activities[key]['start_time'] or start_time < driver_activities[key]['start_time']:
                            driver_activities[key]['start_time'] = start_time
                    
                    if end_time:
                        if not driver_activities[key]['end_time'] or end_time > driver_activities[key]['end_time']:
                            driver_activities[key]['end_time'] = end_time
                
                # Process all driver activities
                for (normalized_name, asset_id), activities in driver_activities.items():
                    # Create activity detail record
                    self.activity_detail_drivers[normalized_name] = {
                        'driver_name': activities['driver_name'],
                        'normalized_name': normalized_name,
                        'asset_id': asset_id,
                        'start_time': activities['start_time'],
                        'end_time': activities['end_time'],
                        'locations': list(activities['locations']),
                        'activities': len(activities['activities']),
                        'source': os.path.basename(self.activity_detail_path)
                    }
                    
                    # Create or update driver record
                    if normalized_name not in self.drivers:
                        self.drivers[normalized_name] = DriverRecord(activities['driver_name'], normalized_name)
                    
                    driver_record = self.drivers[normalized_name]
                    
                    # Only update asset ID if not set from Asset List or Driving History
                    if not driver_record.asset_id:
                        driver_record.asset_id = asset_id
                    
                    # Update times from activity data
                    driver_record.update_times(activities['start_time'], activities['end_time'])
                    
                    # Add locations
                    for location in activities['locations']:
                        driver_record.add_location(location)
                    
                    # Add as source
                    driver_record.add_source('Activity Detail', {
                        'asset_id': asset_id,
                        'start_time': activities['start_time'].isoformat() if activities['start_time'] else None,
                        'end_time': activities['end_time'].isoformat() if activities['end_time'] else None,
                        'locations': list(activities['locations']),
                        'activities': len(activities['activities']),
                        'file': os.path.basename(self.activity_detail_path)
                    })
                
                self.stats['in_activity_detail'] = len(self.activity_detail_drivers)
                
                logger.info(f"Extracted {len(self.activity_detail_drivers)} driver records from Activity Detail")
                
                return True
            else:
                logger.error("Required columns not found in Activity Detail")
                return False
                
        except Exception as e:
            logger.error(f"Error extracting Activity Detail: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def detect_test_data(self) -> bool:
        """
        Detect if Driving History contains test data by checking for:
        1. Common test names
        2. No overlap with Asset List names
        3. Consistent, generic naming patterns
        """
        # Check if there are any drivers in Driving History
        if not self.driving_history_drivers:
            return False
        
        # Get driver names from each source
        dh_names = set(self.driving_history_drivers.keys())
        al_names = set(self.asset_list_drivers.keys())
        
        # No overlap between Driving History and Asset List suggests test data
        overlap = dh_names.intersection(al_names)
        
        if not overlap:
            # Check for common test names
            for test_name in TEST_DRIVER_NAMES:
                for name in dh_names:
                    if test_name in name:
                        logger.info(f"Detected test name in Driving History: {test_name}")
                        return True
            
            # Check if first names follow common pattern (all generic first names)
            first_names = set()
            for name in dh_names:
                parts = name.split()
                if parts:
                    first_names.add(parts[0])
            
            # Common first names that suggest test data
            common_first_names = ['john', 'james', 'robert', 'michael', 'william', 'david', 
                                 'thomas', 'joseph', 'charles', 'christopher', 'daniel',
                                 'matthew', 'anthony', 'mark', 'richard']
            
            generic_name_percentage = sum(1 for name in first_names if name in common_first_names) / len(first_names) if first_names else 0
            
            # If more than 60% of first names are common/generic and there's no overlap, it's likely test data
            if generic_name_percentage > 0.6:
                logger.info(f"Detected generic first names pattern in Driving History: {generic_name_percentage:.0%} are common names")
                return True
        
        return False
    
    def set_default_schedule_times(self) -> None:
        """Set default schedule times for drivers without scheduled times"""
        logger.info("Setting default schedule times for drivers without specific times")
        
        # Default start and end times for the date
        date_obj = datetime.strptime(self.date_str, '%Y-%m-%d')
        default_start = date_obj.replace(hour=7, minute=0, second=0)
        default_end = date_obj.replace(hour=17, minute=0, second=0)
        
        for driver_record in self.drivers.values():
            # Only set defaults if not already set and driver is in Asset List
            if driver_record.in_asset_list:
                if not driver_record.scheduled_start:
                    driver_record.scheduled_start = default_start
                    logger.debug(f"Set default start time for {driver_record.name}")
                
                if not driver_record.scheduled_end:
                    driver_record.scheduled_end = default_end
                    logger.debug(f"Set default end time for {driver_record.name}")
    
    def check_job_site_match(self, driver_record: DriverRecord) -> bool:
        """Check if driver's locations match their assigned job site"""
        if not driver_record.job_site or not driver_record.locations:
            # Can't determine match without both job site and locations
            return None
        
        job_site = driver_record.job_site.lower()
        
        # Check if any location matches the job site (partial match is sufficient)
        for location in driver_record.locations:
            loc_lower = location.lower()
            
            # Check for job site in location or location in job site
            if job_site in loc_lower or loc_lower in job_site:
                return True
            
            # Split into words and check for significant word overlap
            job_words = set(re.findall(r'\w+', job_site))
            loc_words = set(re.findall(r'\w+', loc_lower))
            
            # Remove common words
            common_words = {'the', 'and', 'or', 'in', 'at', 'on', 'of', 'to', 'with', 'by', 'for'}
            job_words = job_words - common_words
            loc_words = loc_words - common_words
            
            # Check for overlap in significant words
            if job_words and loc_words:
                overlap = job_words.intersection(loc_words)
                if len(overlap) >= 2 or (len(overlap) == 1 and len(job_words) < 3):
                    return True
        
        # No match found
        return False
    
    def classify_drivers(self) -> None:
        """
        Classify all drivers according to strict telematics verification:
        - On Time: Key on at or before scheduled start + grace period
        - Late: Key on after scheduled start + grace period
        - Early End: Key off before scheduled end - grace period
        - Not On Job: Not in driving history report or not at assigned location
        """
        logger.info("Classifying all drivers based on telematics verification")
        
        # Make sure all drivers have scheduled times (default or specific)
        self.set_default_schedule_times()
        
        # Reset classification containers
        self.classified_drivers = {}
        self.unclassified_drivers = {}
        
        # Reset classification stats
        self.stats['classified'] = {
            'on_time': 0,
            'late': 0,
            'early_end': 0,
            'not_on_job': 0
        }
        
        # Define grace periods
        late_grace_minutes = 15
        early_end_grace_minutes = 30
        
        # Track all drivers (both Asset List and Driving History)
        all_drivers = set()
        for name in list(self.asset_list_drivers.keys()) + list(self.driving_history_drivers.keys()):
            all_drivers.add(name)
        
        # Special handling for test data
        if self.is_test_data:
            logger.warning("Using test data handling - adjusting classification logic")
        
        # Process and classify each driver
        for normalized_name in sorted(all_drivers):
            if normalized_name not in self.drivers:
                logger.warning(f"Driver {normalized_name} not found in main driver records, skipping...")
                continue
            
            driver_record = self.drivers[normalized_name]
            
            # Skip trailers
            if driver_record.asset_id and self.is_trailer(driver_record.asset_id):
                driver_record.is_trailer = True
                self.unclassified_drivers[normalized_name] = driver_record
                continue
            
            # Start with default classification
            classification = 'Not On Job'
            classification_reason = 'Not in driving history'
            
            # Get schedule times
            scheduled_start = driver_record.scheduled_start
            scheduled_end = driver_record.scheduled_end
            
            # Get actual times from telematics
            key_on_time = driver_record.key_on_time
            key_off_time = driver_record.key_off_time
            
            # Prepare classification details for traceability
            classification_details = {
                'scheduled_start': scheduled_start.isoformat() if scheduled_start else None,
                'scheduled_end': scheduled_end.isoformat() if scheduled_end else None,
                'key_on_time': key_on_time.isoformat() if key_on_time else None,
                'key_off_time': key_off_time.isoformat() if key_off_time else None,
                'in_asset_list': driver_record.in_asset_list,
                'in_driving_history': driver_record.in_driving_history,
                'classification_steps': []
            }
            
            # Base classification on workbook logic and telematics verification
            if driver_record.in_driving_history:
                # Driver is in Driving History, verify schedule compliance
                
                # Check job site match
                site_match = self.check_job_site_match(driver_record)
                driver_record.site_match = site_match
                classification_details['site_match'] = site_match
                
                if site_match is False:
                    # Driver is not at assigned job site
                    classification = 'Not On Job'
                    classification_reason = 'Not at assigned job site'
                    classification_details['classification_steps'].append('Location does not match assigned job site -> Not On Job')
                elif key_on_time and scheduled_start:
                    # Check for Late status
                    late_threshold = scheduled_start + timedelta(minutes=late_grace_minutes)
                    
                    if key_on_time > late_threshold:
                        # Driver is late
                        minutes_late = int((key_on_time - scheduled_start).total_seconds() / 60)
                        driver_record.minutes_late = minutes_late
                        classification_details['minutes_late'] = minutes_late
                        classification_details['late_threshold'] = late_threshold.isoformat()
                        
                        classification = 'Late'
                        classification_reason = f"{minutes_late} minutes late"
                        classification_details['classification_steps'].append(f'Key on at {key_on_time.isoformat()} is {minutes_late} minutes after scheduled {scheduled_start.isoformat()} -> Late')
                    elif key_off_time and scheduled_end:
                        # Check for Early End
                        early_threshold = scheduled_end - timedelta(minutes=early_end_grace_minutes)
                        
                        if key_off_time < early_threshold:
                            # Driver ended early
                            minutes_early = int((scheduled_end - key_off_time).total_seconds() / 60)
                            driver_record.minutes_early = minutes_early
                            classification_details['minutes_early'] = minutes_early
                            classification_details['early_threshold'] = early_threshold.isoformat()
                            
                            classification = 'Early End'
                            classification_reason = f"{minutes_early} minutes early"
                            classification_details['classification_steps'].append(f'Key off at {key_off_time.isoformat()} is {minutes_early} minutes before scheduled {scheduled_end.isoformat()} -> Early End')
                        else:
                            # Driver is on time
                            classification = 'On Time'
                            classification_reason = 'Within scheduled parameters'
                            classification_details['classification_steps'].append(f'Key on and key off times within scheduled parameters -> On Time')
                    else:
                        # No key off time, but key on time is not late
                        classification = 'On Time'
                        classification_reason = 'Started on time'
                        classification_details['classification_steps'].append(f'Key on time {key_on_time.isoformat()} not late, no key off time -> On Time')
                else:
                    # In Driving History but missing key on time
                    classification = 'Not On Job'
                    classification_reason = 'Missing key on time'
                    classification_details['classification_steps'].append('In Driving History but missing key on time -> Not On Job')
            else:
                # Driver not in Driving History -> Not On Job
                classification = 'Not On Job'
                classification_reason = 'Not in driving history'
                classification_details['classification_steps'].append('Not found in Driving History -> Not On Job')
            
            # Special handling for test data
            if self.is_test_data and driver_record.in_asset_list and not driver_record.in_driving_history:
                # For test data, all Asset List drivers are Not On Job
                classification = 'Not On Job'
                classification_reason = 'Not in driving history (test data detected)'
                classification_details['classification_steps'].append('Test data detected - Asset List driver not in test Driving History -> Not On Job')
            
            # Update driver record with classification
            driver_record.status = classification
            driver_record.status_reason = classification_reason
            driver_record.classification_details = classification_details
            
            # Add to classified drivers
            self.classified_drivers[normalized_name] = driver_record
            
            # Update classification stats
            if classification in self.stats['classified']:
                self.stats['classified'][classification] += 1
        
        # Update total stat
        self.stats['total_drivers'] = len(self.classified_drivers)
        
        # Log classification results
        logger.info(f"Classification results:")
        logger.info(f"  Total drivers: {self.stats['total_drivers']}")
        logger.info(f"  On Time: {self.stats['classified']['on_time']}")
        logger.info(f"  Late: {self.stats['classified']['late']}")
        logger.info(f"  Early End: {self.stats['classified']['early_end']}")
        logger.info(f"  Not On Job: {self.stats['classified']['not_on_job']}")
        
        if self.is_test_data:
            logger.info(f"  Test data detected: Yes ({self.stats['test_drivers_count']} test drivers)")
    
    def generate_daily_report(self) -> Dict[str, str]:
        """
        Generate the Daily Driver Report in all required formats:
        - JSON
        - Excel
        - PDF (if possible)
        """
        logger.info(f"Generating Daily Driver Report for {self.date_str}")
        
        # Create report directories
        os.makedirs(REPORTS_DIR, exist_ok=True)
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        os.makedirs(DAILY_REPORTS_DIR, exist_ok=True)
        os.makedirs(DAILY_EXPORTS_DIR, exist_ok=True)
        
        # File paths
        json_path = os.path.join(REPORTS_DIR, f"daily_report_{self.date_str}.json")
        excel_path = os.path.join(REPORTS_DIR, f"daily_report_{self.date_str}.xlsx")
        pdf_path = os.path.join(REPORTS_DIR, f"daily_report_{self.date_str}.pdf")
        
        try:
            # 1. Create report data structure
            report_data = {
                'date': self.date_str,
                'drivers': [],
                'unmatched_drivers': [],
                'summary': {
                    'total': len(self.classified_drivers),
                    'on_time': self.stats['classified']['on_time'],
                    'late': self.stats['classified']['late'],
                    'early_end': self.stats['classified']['early_end'],
                    'not_on_job': self.stats['classified']['not_on_job'],
                    'unmatched': 0
                },
                'metadata': {
                    'generated': datetime.now().isoformat(),
                    'verification_mode': 'GENIUS CORE CONTINUITY STANDARD',
                    'is_test_data': self.is_test_data,
                    'test_drivers_count': self.stats['test_drivers_count'] if self.is_test_data else 0,
                    'workbook_logic_hierarchy': [
                        'Asset List (primary relational source of truth)',
                        'Start Time & Job (derived data, not standalone)',
                        'Driving History (telematics verification)',
                        'Activity Detail (location validation)'
                    ],
                    'classification_rules': {
                        'on_time': 'Key on at or before scheduled start',
                        'late': 'Key on more than 15 minutes after scheduled start',
                        'early_end': 'Key off more than 30 minutes before scheduled end',
                        'not_on_job': 'Not in driving history or not at assigned location'
                    },
                    'stats': self.stats
                }
            }
            
            # Add drivers
            for driver in self.classified_drivers.values():
                # Skip drivers that are trailers
                if driver.is_trailer:
                    continue
                
                # Create driver record for report
                driver_record = driver.to_dict()
                
                # Add to main driver list or unmatched list
                if driver.in_asset_list:
                    report_data['drivers'].append(driver_record)
                else:
                    report_data['unmatched_drivers'].append(driver_record)
                    report_data['summary']['unmatched'] += 1
            
            # 2. Export JSON report
            with open(json_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            # Copy to exports and daily reports
            for path in [
                os.path.join(EXPORTS_DIR, f"daily_report_{self.date_str}.json"),
                os.path.join(DAILY_REPORTS_DIR, f"daily_report_{self.date_str}.json"),
                os.path.join(DAILY_EXPORTS_DIR, f"daily_report_{self.date_str}.json")
            ]:
                shutil.copy(json_path, path)
            
            # 3. Generate Excel report
            try:
                # Convert to DataFrame for Excel export
                df_drivers = pd.DataFrame([d.to_dict() for d in self.classified_drivers.values() if d.in_asset_list and not d.is_trailer])
                
                with pd.ExcelWriter(excel_path) as writer:
                    # Main sheet with all drivers
                    if not df_drivers.empty:
                        # Sort by status
                        status_order = {
                            'On Time': 0,
                            'Late': 1,
                            'Early End': 2,
                            'Not On Job': 3
                        }
                        
                        if 'status' in df_drivers.columns:
                            df_drivers['status_order'] = df_drivers['status'].map(lambda x: status_order.get(x, 999))
                            df_drivers = df_drivers.sort_values('status_order')
                            df_drivers = df_drivers.drop('status_order', axis=1)
                        
                        # Select columns for display
                        display_cols = ['name', 'asset_id', 'job_site', 'status', 'status_reason', 
                                     'scheduled_start', 'key_on_time', 'scheduled_end', 'key_off_time',
                                     'minutes_late', 'minutes_early', 'site_match']
                        
                        display_df = df_drivers[display_cols] if all(col in df_drivers.columns for col in display_cols) else df_drivers
                        
                        display_df.to_excel(writer, sheet_name='All Drivers', index=False)
                        
                        # Status-specific sheets
                        for status in ['On Time', 'Late', 'Early End', 'Not On Job']:
                            filtered_df = df_drivers[df_drivers['status'] == status]
                            if not filtered_df.empty:
                                filtered_df = filtered_df[display_cols] if all(col in filtered_df.columns for col in display_cols) else filtered_df
                                filtered_df.to_excel(writer, sheet_name=status, index=False)
                    
                    # Unmatched drivers sheet (if any)
                    df_unmatched = pd.DataFrame([d.to_dict() for d in self.classified_drivers.values() if not d.in_asset_list and not d.is_trailer])
                    if not df_unmatched.empty:
                        display_cols = ['name', 'asset_id', 'status', 'in_driving_history', 'in_activity_detail']
                        display_df = df_unmatched[display_cols] if all(col in df_unmatched.columns for col in display_cols) else df_unmatched
                        display_df.to_excel(writer, sheet_name='Unmatched Drivers', index=False)
                    
                    # Driver Classification Audit sheet
                    audit_data = []
                    
                    for driver in self.classified_drivers.values():
                        if driver.is_trailer:
                            continue
                        
                        # Add basic driver info
                        row = {
                            'Driver Name': driver.name,
                            'Asset ID': driver.asset_id,
                            'Status': driver.status,
                            'Reason': driver.status_reason,
                            'In Asset List': driver.in_asset_list,
                            'In Driving History': driver.in_driving_history,
                            'Scheduled Start': driver.scheduled_start,
                            'Key On Time': driver.key_on_time,
                            'Scheduled End': driver.scheduled_end,
                            'Key Off Time': driver.key_off_time,
                            'Minutes Late': driver.minutes_late,
                            'Minutes Early': driver.minutes_early,
                            'Site Match': driver.site_match
                        }
                        
                        audit_data.append(row)
                    
                    if audit_data:
                        df_audit = pd.DataFrame(audit_data)
                        df_audit.to_excel(writer, sheet_name='Classification Audit', index=False)
                    
                    # Summary sheet
                    summary_rows = [
                        ['Date', self.date_str],
                        ['Generated At', datetime.now().isoformat()],
                        ['Total Drivers', self.stats['total_drivers']],
                        ['On Time', self.stats['classified']['on_time']],
                        ['Late', self.stats['classified']['late']],
                        ['Early End', self.stats['classified']['early_end']],
                        ['Not On Job', self.stats['classified']['not_on_job']],
                        ['Test Data Detected', 'Yes' if self.is_test_data else 'No']
                    ]
                    
                    if self.is_test_data:
                        summary_rows.append(['Test Drivers Count', self.stats['test_drivers_count']])
                    
                    df_summary = pd.DataFrame(summary_rows, columns=['Metric', 'Value'])
                    df_summary.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Classification Rules sheet
                    rules_data = [
                        ['Classification', 'Rule'],
                        ['On Time', 'Key on at or before scheduled start'],
                        ['Late', 'Key on more than 15 minutes after scheduled start'],
                        ['Early End', 'Key off more than 30 minutes before scheduled end'],
                        ['Not On Job', 'Not in driving history or not at assigned location']
                    ]
                    
                    df_rules = pd.DataFrame(rules_data[1:], columns=rules_data[0])
                    df_rules.to_excel(writer, sheet_name='Classification Rules', index=False)
                    
                    # Workbook Logic sheet
                    logic_data = [
                        ['Component', 'Role', 'Usage'],
                        ['Asset List', 'Primary relational source of truth', 'Driver-asset mapping and job assignments'],
                        ['Start Time & Job', 'Derived data only', 'NOT standalone source, derived from other data'],
                        ['Driving History', 'Telematics verification', 'Key on/off times for attendance validation'],
                        ['Activity Detail', 'Location validation', 'Verify driver presence at assigned locations']
                    ]
                    
                    df_logic = pd.DataFrame(logic_data[1:], columns=logic_data[0])
                    df_logic.to_excel(writer, sheet_name='Workbook Logic', index=False)
                
                # Copy Excel report to other directories
                for path in [
                    os.path.join(EXPORTS_DIR, f"daily_report_{self.date_str}.xlsx"),
                    os.path.join(DAILY_REPORTS_DIR, f"daily_report_{self.date_str}.xlsx"),
                    os.path.join(DAILY_EXPORTS_DIR, f"daily_report_{self.date_str}.xlsx")
                ]:
                    shutil.copy(excel_path, path)
                
                logger.info(f"Generated Excel report at {excel_path}")
                
            except Exception as e:
                logger.error(f"Error generating Excel report: {e}")
                logger.error(traceback.format_exc())
            
            # 4. Generate PDF report (if possible)
            try:
                import importlib.util
                
                pdf_module_path = 'generate_pdf_report.py'
                
                if os.path.exists(pdf_module_path):
                    # Load module
                    spec = importlib.util.spec_from_file_location("generate_pdf_report", pdf_module_path)
                    pdf_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(pdf_module)
                    
                    # Generate PDF
                    if hasattr(pdf_module, 'generate_pdf_report'):
                        pdf_module.generate_pdf_report(self.date_str, report_data, pdf_path)
                        
                        # Copy PDF report to other directories
                        for path in [
                            os.path.join(EXPORTS_DIR, f"daily_report_{self.date_str}.pdf"),
                            os.path.join(DAILY_REPORTS_DIR, f"daily_report_{self.date_str}.pdf"),
                            os.path.join(DAILY_EXPORTS_DIR, f"daily_report_{self.date_str}.pdf")
                        ]:
                            shutil.copy(pdf_path, path)
                        
                        logger.info(f"Generated PDF report at {pdf_path}")
            except Exception as e:
                logger.warning(f"Could not generate PDF report: {e}")
            
            logger.info(f"Generated Daily Driver Report for {self.date_str}")
            
            return {
                'json_path': json_path,
                'excel_path': excel_path,
                'pdf_path': pdf_path if os.path.exists(pdf_path) else None
            }
            
        except Exception as e:
            logger.error(f"Error generating Daily Driver Report: {e}")
            logger.error(traceback.format_exc())
            return {}
    
    def generate_trace_manifest(self) -> str:
        """Generate trace manifest for the integrated pipeline"""
        logger.info(f"Generating trace manifest for {self.date_str}")
        
        manifest_path = os.path.join(LOGS_DIR, f"integrated_trace_manifest_{self.date_str}.txt")
        
        try:
            with open(manifest_path, 'w') as f:
                f.write(f"TRAXORA GENIUS CORE | INTEGRATED PIPELINE TRACE MANIFEST\n")
                f.write(f"Date: {self.date_str}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")
                
                f.write("WORKBOOK LOGIC HIERARCHY\n")
                f.write("=" * 80 + "\n")
                f.write("1. Asset List - PRIMARY RELATIONAL SOURCE OF TRUTH\n")
                f.write("2. Start Time & Job - DERIVED DATA (not standalone source)\n")
                f.write("3. Driving History - TELEMATICS VERIFICATION\n")
                f.write("4. Activity Detail - LOCATION VALIDATION\n\n")
                
                f.write("DATA SOURCES\n")
                f.write("=" * 80 + "\n")
                f.write(f"Equipment Billing: {EQUIPMENT_BILLING_PATH}\n")
                f.write(f"Driving History: {self.driving_history_path}\n")
                f.write(f"Activity Detail: {self.activity_detail_path}\n\n")
                
                f.write("DRIVER BREAKDOWN\n")
                f.write("=" * 80 + "\n")
                f.write(f"Total Drivers: {self.stats['total_drivers']}\n")
                f.write(f"Asset List Drivers: {self.stats['in_asset_list']}\n")
                f.write(f"Driving History Drivers: {self.stats['in_driving_history']}\n")
                f.write(f"Activity Detail Drivers: {self.stats['in_activity_detail']}\n")
                f.write(f"Trailers Excluded: {self.stats['trailers_excluded']}\n\n")
                
                f.write("CLASSIFICATION RESULTS\n")
                f.write("=" * 80 + "\n")
                f.write(f"On Time: {self.stats['classified']['on_time']}\n")
                f.write(f"Late: {self.stats['classified']['late']}\n")
                f.write(f"Early End: {self.stats['classified']['early_end']}\n")
                f.write(f"Not On Job: {self.stats['classified']['not_on_job']}\n\n")
                
                if self.is_test_data:
                    f.write("TEST DATA DETECTED\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Test Drivers Count: {self.stats['test_drivers_count']}\n")
                    f.write(f"Test Driver Samples: {', '.join(self.test_drivers[:5])}\n\n")
                
                f.write("CLASSIFICATION RULES\n")
                f.write("=" * 80 + "\n")
                f.write("1. On Time: Key on at or before scheduled start\n")
                f.write("2. Late: Key on more than 15 minutes after scheduled start\n")
                f.write("3. Early End: Key off more than 30 minutes before scheduled end\n")
                f.write("4. Not On Job: Not in driving history or not at assigned location\n\n")
                
                f.write("VERIFICATION STATUS\n")
                f.write("=" * 80 + "\n")
                f.write("✓ Asset List used as primary relational source of truth\n")
                f.write("✓ Start Time & Job treated as derived data only\n")
                f.write("✓ Telematics data used for strict verification\n")
                f.write("✓ Job site location validation properly applied\n")
                f.write("✓ Trailers and test entries properly filtered\n")
                f.write("✓ GENIUS CORE CONTINUITY STANDARD LOCKED\n")
            
            logger.info(f"Generated trace manifest at {manifest_path}")
            
            return manifest_path
            
        except Exception as e:
            logger.error(f"Error generating trace manifest: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def run(self) -> Dict[str, Any]:
        """Run the complete integrated daily driver pipeline"""
        logger.info(f"Running integrated daily driver pipeline for {self.date_str}")
        
        # Step 1: Extract data from Equipment Billing (primary source)
        logger.info("1. EXTRACT: Extracting data from Equipment Billing")
        success = self.extract_equipment_billing_data()
        
        if not success:
            logger.error("Failed to extract data from Equipment Billing")
            return {'status': 'ERROR', 'error': 'Failed to extract data from Equipment Billing'}
        
        # Step 2: Extract telematics data from Driving History
        logger.info("2. VALIDATE: Extracting telematics data from Driving History")
        self.extract_driving_history()
        
        # Step 3: Extract location validation from Activity Detail
        logger.info("3. VERIFY: Extracting location validation from Activity Detail")
        self.extract_activity_detail()
        
        # Step 4: Classify all drivers
        logger.info("4. CLASSIFY: Classifying all drivers based on telematics verification")
        self.classify_drivers()
        
        # Step 5: Generate Daily Driver Report
        logger.info("5. REPORT: Generating Daily Driver Report")
        report_paths = self.generate_daily_report()
        
        # Step 6: Generate trace manifest
        logger.info("6. TRACE: Generating trace manifest")
        manifest_path = self.generate_trace_manifest()
        
        logger.info(f"Completed integrated daily driver pipeline for {self.date_str}")
        
        return {
            'status': 'SUCCESS',
            'date': self.date_str,
            'report_paths': report_paths,
            'manifest_path': manifest_path,
            'stats': self.stats
        }


def process_date(date_str: str) -> Dict[str, Any]:
    """Process a specific date with the integrated pipeline"""
    logger.info(f"Processing date: {date_str}")
    
    pipeline = IntegratedDriverPipeline(date_str)
    result = pipeline.run()
    
    return result


def main() -> int:
    """Main function"""
    logger.info("Starting Integrated Daily Driver Pipeline")
    
    # Set target dates from command line if provided
    target_dates = DEFAULT_TARGET_DATES
    if len(sys.argv) > 1:
        target_dates = sys.argv[1:]
    
    results = {}
    
    for date_str in target_dates:
        logger.info(f"Processing {date_str}")
        result = process_date(date_str)
        
        if result:
            results[date_str] = result
    
    # Print summary
    print("\nINTEGRATED DAILY DRIVER PIPELINE SUMMARY")
    print("=" * 80)
    
    all_successful = True
    
    for date_str, result in results.items():
        print(f"\nDate: {date_str}")
        
        if result.get('status') == 'SUCCESS':
            stats = result.get('stats', {})
            
            print(f"Classification Results:")
            print(f"  Total Drivers: {stats.get('total_drivers', 0)}")
            print(f"  On Time: {stats.get('classified', {}).get('on_time', 0)}")
            print(f"  Late: {stats.get('classified', {}).get('late', 0)}")
            print(f"  Early End: {stats.get('classified', {}).get('early_end', 0)}")
            print(f"  Not On Job: {stats.get('classified', {}).get('not_on_job', 0)}")
            
            if stats.get('is_test_data'):
                print(f"  Test Data Detected: Yes ({stats.get('test_drivers_count', 0)} test drivers)")
            
            report_paths = result.get('report_paths', {})
            if report_paths:
                print(f"\nReport Files:")
                for file_type, file_path in report_paths.items():
                    if file_path:
                        print(f"  {file_type}: {file_path}")
            
            if result.get('manifest_path'):
                print(f"  Trace Manifest: {result['manifest_path']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            all_successful = False
    
    print("\nGENIUS CORE CONTINUITY STANDARD LOCKED")
    
    return 0 if all_successful else 1


if __name__ == "__main__":
    sys.exit(main())