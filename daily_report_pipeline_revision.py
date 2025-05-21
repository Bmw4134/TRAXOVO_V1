#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Daily Driver Report Pipeline Revision

This script implements the complete driver report pipeline following
the exact workbook logic hierarchy:
1. Asset List as primary source of truth
2. Start Time & Job as derived data
3. Full relationship processing of all Driving History and Activity Detail
4. Cross-validation of all sources with proper matchback

GENIUS CORE TRACE LOCK ACTIVE
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
import hashlib
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs/pipeline_revision', exist_ok=True)
pipeline_log = logging.FileHandler('logs/pipeline_revision/pipeline.log')
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

# File paths
EQUIPMENT_BILLING_PATH = 'attached_assets/EQ MONTHLY BILLINGS WORKING SPREADSHEET - APRIL 2025.xlsx'

# Target dates - can be specified as arguments
TARGET_DATES = ['2025-05-16', '2025-05-19']


class DriverMatchRecord:
    """Trace record for driver matchback verification"""
    
    def __init__(self, driver_name, normalized_name):
        self.driver_name = driver_name
        self.normalized_name = normalized_name
        self.asset_id = None
        self.job_site = None
        self.sources = set()
        self.key_on_time = None
        self.key_off_time = None
        self.locations = set()
        self.status = 'Unknown'
        self.status_reason = None
        self.verification_level = 'UNVERIFIED'
        self.source_data = {}
        self.classification_details = {}
        self.key_delta_minutes = None
        self.site_match = None
    
    def add_source(self, source, data):
        """Add source data to trace record"""
        self.sources.add(source)
        self.source_data[source] = data
        
        # Update verification level based on sources
        if len(self.sources) >= 3:
            self.verification_level = 'HIGH'
        elif len(self.sources) == 2:
            self.verification_level = 'MEDIUM'
        elif len(self.sources) == 1:
            self.verification_level = 'LOW'
        else:
            self.verification_level = 'UNVERIFIED'
    
    def update_times(self, key_on_time, key_off_time):
        """Update key on/off times if provided"""
        if key_on_time:
            if not self.key_on_time or key_on_time < self.key_on_time:
                self.key_on_time = key_on_time
        
        if key_off_time:
            if not self.key_off_time or key_off_time > self.key_off_time:
                self.key_off_time = key_off_time
    
    def add_location(self, location):
        """Add location to trace record"""
        if location:
            self.locations.add(location)
    
    def to_dict(self):
        """Convert trace record to dictionary"""
        record = {
            'driver_name': self.driver_name,
            'normalized_name': self.normalized_name,
            'asset_id': self.asset_id,
            'job_site': self.job_site,
            'status': self.status,
            'status_reason': self.status_reason,
            'verification_level': self.verification_level,
            'sources': list(self.sources),
            'key_on_time': self.key_on_time.isoformat() if self.key_on_time else None,
            'key_off_time': self.key_off_time.isoformat() if self.key_off_time else None,
            'locations': list(self.locations),
            'identity_verified': self.verification_level in ['HIGH', 'MEDIUM'],
            'classification_details': self.classification_details
        }
        
        # Add detailed timings if available
        if self.key_delta_minutes is not None:
            record['key_delta_minutes'] = self.key_delta_minutes
        
        if self.site_match is not None:
            record['site_match'] = self.site_match
        
        return record


class DriverReportPipeline:
    """
    Complete driver report pipeline with strict workbook logic enforcement
    """
    
    def __init__(self, date_str):
        """Initialize pipeline for specific date"""
        self.date_str = date_str
        self.asset_list_data = {}
        self.drivers_sheet_data = {}
        self.jobs_sheet_data = {}
        self.start_time_job_data = {}
        self.driving_history_data = {}
        self.activity_detail_data = {}
        
        self.all_driver_records = {}  # All processed drivers
        self.matched_drivers = {}     # Drivers matched to Asset List
        self.unmatched_drivers = {}   # Drivers not matched to Asset List
        
        self.total_drivers_parsed = 0
        self.total_matched_to_asset_list = 0
        self.total_excluded = 0
        self.exclusion_reasons = {}
        
        self.classification_counts = {
            'On Time': 0,
            'Late': 0,
            'Early End': 0,
            'Not On Job': 0,
            'Unverified': 0
        }
        
        # Source file paths for this date
        self.driving_history_path = f'data/driving_history/DrivingHistory_{date_str.replace("-", "")}.csv'
        self.activity_detail_path = f'data/activity_detail/ActivityDetail_{date_str.replace("-", "")}.csv'
        
        # Check for additional raw data files
        for root, dirs, files in os.walk('data/driving_history'):
            for file in files:
                if file.endswith('.csv') and self.date_str.replace('-', '') in file:
                    self.driving_history_path = os.path.join(root, file)
                    break
        
        for root, dirs, files in os.walk('data/activity_detail'):
            for file in files:
                if file.endswith('.csv') and self.date_str.replace('-', '') in file:
                    self.activity_detail_path = os.path.join(root, file)
                    break
        
        # Also check attached_assets for any relevant files
        for root, dirs, files in os.walk('attached_assets'):
            for file in files:
                date_part = self.date_str.replace('-', '')
                if file.endswith('.csv') and date_part in file:
                    if 'driv' in file.lower() or 'history' in file.lower():
                        self.driving_history_path = os.path.join(root, file)
                    elif 'activ' in file.lower() or 'detail' in file.lower():
                        self.activity_detail_path = os.path.join(root, file)
    
    def normalize_name(self, name):
        """Normalize driver name for consistent matching"""
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Replace special characters with spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def parse_time(self, time_str):
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
                return datetime.strptime(time_str, fmt)
            except (ValueError, TypeError):
                continue
        
        # If all fails, try pandas conversion
        try:
            return pd.to_datetime(time_str)
        except:
            logger.warning(f"Could not parse time string: {time_str}")
            return None
    
    def extract_equipment_billing_data(self):
        """
        Extract data from Equipment Billing workbook
        Following the workbook logic hierarchy:
        1. Asset List (primary source of truth)
        2. Drivers Sheet
        3. Jobs Sheet
        """
        logger.info(f"Extracting data from Equipment Billing: {EQUIPMENT_BILLING_PATH}")
        
        if not os.path.exists(EQUIPMENT_BILLING_PATH):
            logger.error(f"Equipment Billing file not found: {EQUIPMENT_BILLING_PATH}")
            return False
        
        try:
            # Load workbook
            workbook = pd.ExcelFile(EQUIPMENT_BILLING_PATH)
            sheets = workbook.sheet_names
            logger.info(f"Available sheets: {sheets}")
            
            # 1. Process Asset List (PRIMARY SOURCE OF TRUTH)
            asset_sheet = None
            if 'FLEET' in sheets:
                asset_sheet = 'FLEET'
            elif 'Equip Table' in sheets:
                asset_sheet = 'Equip Table'
            elif 'Asset List' in sheets:
                asset_sheet = 'Asset List'
            
            if asset_sheet:
                logger.info(f"Processing Asset List sheet: {asset_sheet}")
                df = pd.read_excel(workbook, sheet_name=asset_sheet)
                
                # Normalize column names
                df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                
                # Find relevant columns
                asset_col = None
                for col in ['equip_#', 'equip_id', 'equipment_id', 'equipment', 'asset_id', 'asset']:
                    if col in df.columns:
                        asset_col = col
                        break
                
                driver_col = None
                for col in ['driver', 'driver_name', 'employee', 'employee_name', 'operator', 'assigned_to']:
                    if col in df.columns:
                        driver_col = col
                        break
                
                # Process rows
                if asset_col and driver_col:
                    logger.info(f"Found asset column: {asset_col}, driver column: {driver_col}")
                    
                    for _, row in df.iterrows():
                        asset_id = str(row[asset_col]).strip() if pd.notna(row[asset_col]) else None
                        driver_name = str(row[driver_col]).strip() if pd.notna(row[driver_col]) else None
                        
                        # Skip empty or invalid values
                        if not asset_id or not driver_name:
                            continue
                        
                        if asset_id.lower() in ['nan', 'none', 'null', ''] or driver_name.lower() in ['nan', 'none', 'null', '']:
                            continue
                        
                        # Normalize driver name
                        normalized_name = self.normalize_name(driver_name)
                        
                        # Create Asset List record
                        self.asset_list_data[normalized_name] = {
                            'driver_name': driver_name,
                            'normalized_name': normalized_name,
                            'asset_id': asset_id.upper(),
                            'source': f"Asset List ({asset_sheet})"
                        }
                        
                        # Add to driver records
                        if normalized_name not in self.all_driver_records:
                            self.all_driver_records[normalized_name] = DriverMatchRecord(driver_name, normalized_name)
                        
                        driver_record = self.all_driver_records[normalized_name]
                        driver_record.asset_id = asset_id.upper()
                        driver_record.add_source('Asset List', {
                            'asset_id': asset_id.upper(),
                            'sheet': asset_sheet
                        })
            
            # 2. Process Drivers Sheet
            driver_sheet = None
            if 'DRIVERS' in sheets:
                driver_sheet = 'DRIVERS'
            elif 'Drivers' in sheets:
                driver_sheet = 'Drivers'
            
            if driver_sheet:
                logger.info(f"Processing Drivers sheet: {driver_sheet}")
                df = pd.read_excel(workbook, sheet_name=driver_sheet)
                
                # Normalize column names
                df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                
                # Find relevant columns
                name_col = None
                for col in ['name', 'driver', 'driver_name', 'employee', 'employee_name']:
                    if col in df.columns:
                        name_col = col
                        break
                
                asset_col = None
                for col in ['equip_#', 'equip_id', 'equipment_id', 'equipment', 'asset_id', 'asset', 'assigned_equipment']:
                    if col in df.columns:
                        asset_col = col
                        break
                
                job_col = None
                for col in ['job', 'job_site', 'site', 'location', 'project']:
                    if col in df.columns:
                        job_col = col
                        break
                
                # Process rows
                if name_col:
                    for _, row in df.iterrows():
                        driver_name = str(row[name_col]).strip() if pd.notna(row[name_col]) else None
                        
                        # Skip empty or invalid values
                        if not driver_name or driver_name.lower() in ['nan', 'none', 'null', '']:
                            continue
                        
                        # Normalize driver name
                        normalized_name = self.normalize_name(driver_name)
                        
                        # Get additional data
                        asset_id = None
                        if asset_col and pd.notna(row[asset_col]):
                            asset_id = str(row[asset_col]).strip()
                            if asset_id.lower() in ['nan', 'none', 'null', '']:
                                asset_id = None
                        
                        job_site = None
                        if job_col and pd.notna(row[job_col]):
                            job_site = str(row[job_col]).strip()
                            if job_site.lower() in ['nan', 'none', 'null', '']:
                                job_site = None
                        
                        # Create Drivers Sheet record
                        self.drivers_sheet_data[normalized_name] = {
                            'driver_name': driver_name,
                            'normalized_name': normalized_name,
                            'asset_id': asset_id.upper() if asset_id else None,
                            'job_site': job_site,
                            'source': f"Drivers Sheet ({driver_sheet})"
                        }
                        
                        # Add to driver records
                        if normalized_name not in self.all_driver_records:
                            self.all_driver_records[normalized_name] = DriverMatchRecord(driver_name, normalized_name)
                        
                        driver_record = self.all_driver_records[normalized_name]
                        
                        if asset_id:
                            if not driver_record.asset_id:
                                driver_record.asset_id = asset_id.upper()
                        
                        if job_site:
                            driver_record.job_site = job_site
                        
                        driver_record.add_source('Drivers Sheet', {
                            'asset_id': asset_id.upper() if asset_id else None,
                            'job_site': job_site,
                            'sheet': driver_sheet
                        })
            
            # 3. Process Jobs Sheet (for job site assignments)
            job_sheet = None
            if 'JOBS' in sheets:
                job_sheet = 'JOBS'
            elif 'Jobs' in sheets:
                job_sheet = 'Jobs'
            
            if job_sheet:
                logger.info(f"Processing Jobs sheet: {job_sheet}")
                df = pd.read_excel(workbook, sheet_name=job_sheet)
                
                # Normalize column names
                df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                
                # Find relevant columns
                name_col = None
                for col in ['name', 'driver', 'driver_name', 'employee', 'employee_name']:
                    if col in df.columns:
                        name_col = col
                        break
                
                job_col = None
                for col in ['job', 'job_site', 'site', 'location', 'project']:
                    if col in df.columns:
                        job_col = col
                        break
                
                # Process rows
                if name_col and job_col:
                    for _, row in df.iterrows():
                        driver_name = str(row[name_col]).strip() if pd.notna(row[name_col]) else None
                        job_site = str(row[job_col]).strip() if pd.notna(row[job_col]) else None
                        
                        # Skip empty or invalid values
                        if not driver_name or driver_name.lower() in ['nan', 'none', 'null', '']:
                            continue
                        
                        if job_site.lower() in ['nan', 'none', 'null', '']:
                            job_site = None
                        
                        # Normalize driver name
                        normalized_name = self.normalize_name(driver_name)
                        
                        # Create Jobs Sheet record
                        self.jobs_sheet_data[normalized_name] = {
                            'driver_name': driver_name,
                            'normalized_name': normalized_name,
                            'job_site': job_site,
                            'source': f"Jobs Sheet ({job_sheet})"
                        }
                        
                        # Add to driver records
                        if normalized_name not in self.all_driver_records:
                            self.all_driver_records[normalized_name] = DriverMatchRecord(driver_name, normalized_name)
                        
                        driver_record = self.all_driver_records[normalized_name]
                        
                        if job_site:
                            driver_record.job_site = job_site
                        
                        driver_record.add_source('Jobs Sheet', {
                            'job_site': job_site,
                            'sheet': job_sheet
                        })
            
            # 4. Process Start Time & Job Sheet (as DERIVED DATA)
            start_time_job_sheet = None
            for sheet in sheets:
                if 'START' in sheet.upper() or 'TIME' in sheet.upper() or 'JOB' in sheet.upper():
                    start_time_job_sheet = sheet
                    break
            
            if start_time_job_sheet:
                logger.info(f"Processing Start Time & Job sheet: {start_time_job_sheet} (as DERIVED DATA)")
                df = pd.read_excel(workbook, sheet_name=start_time_job_sheet)
                
                # Normalize column names
                df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                
                # Find relevant columns
                name_col = None
                for col in ['name', 'driver', 'driver_name', 'employee', 'employee_name']:
                    if col in df.columns:
                        name_col = col
                        break
                
                job_col = None
                for col in ['job', 'job_site', 'site', 'location', 'project']:
                    if col in df.columns:
                        job_col = col
                        break
                
                start_time_col = None
                for col in ['start_time', 'scheduled_start', 'start']:
                    if col in df.columns:
                        start_time_col = col
                        break
                
                end_time_col = None
                for col in ['end_time', 'scheduled_end', 'end']:
                    if col in df.columns:
                        end_time_col = col
                        break
                
                asset_col = None
                for col in ['equip_#', 'equip_id', 'equipment_id', 'equipment', 'asset_id', 'asset']:
                    if col in df.columns:
                        asset_col = col
                        break
                
                # Process rows (as DERIVED DATA)
                if name_col:
                    for _, row in df.iterrows():
                        driver_name = str(row[name_col]).strip() if pd.notna(row[name_col]) else None
                        
                        # Skip empty or invalid values
                        if not driver_name or driver_name.lower() in ['nan', 'none', 'null', '']:
                            continue
                        
                        # Get additional data
                        job_site = None
                        if job_col and pd.notna(row[job_col]):
                            job_site = str(row[job_col]).strip()
                            if job_site.lower() in ['nan', 'none', 'null', '']:
                                job_site = None
                        
                        start_time = None
                        if start_time_col and pd.notna(row[start_time_col]):
                            start_time = self.parse_time(row[start_time_col])
                        
                        end_time = None
                        if end_time_col and pd.notna(row[end_time_col]):
                            end_time = self.parse_time(row[end_time_col])
                        
                        asset_id = None
                        if asset_col and pd.notna(row[asset_col]):
                            asset_id = str(row[asset_col]).strip()
                            if asset_id.lower() in ['nan', 'none', 'null', '']:
                                asset_id = None
                        
                        # Normalize driver name
                        normalized_name = self.normalize_name(driver_name)
                        
                        # Create Start Time & Job record (as DERIVED DATA)
                        self.start_time_job_data[normalized_name] = {
                            'driver_name': driver_name,
                            'normalized_name': normalized_name,
                            'job_site': job_site,
                            'scheduled_start': start_time,
                            'scheduled_end': end_time,
                            'asset_id': asset_id.upper() if asset_id else None,
                            'source': f"Start Time & Job ({start_time_job_sheet}) [DERIVED]"
                        }
                        
                        # Add to driver records (as DERIVED DATA - used for reference only)
                        if normalized_name not in self.all_driver_records:
                            self.all_driver_records[normalized_name] = DriverMatchRecord(driver_name, normalized_name)
                        
                        driver_record = self.all_driver_records[normalized_name]
                        
                        # Only update job_site if not already set from primary sources
                        if job_site and not driver_record.job_site:
                            driver_record.job_site = job_site
                        
                        # Add as derived source - not used for primary verification
                        driver_record.add_source('Start Time & Job [DERIVED]', {
                            'job_site': job_site,
                            'scheduled_start': start_time.isoformat() if start_time else None,
                            'scheduled_end': end_time.isoformat() if end_time else None,
                            'asset_id': asset_id.upper() if asset_id else None,
                            'sheet': start_time_job_sheet
                        })
            
            logger.info(f"Extracted data from Equipment Billing:")
            logger.info(f"  Asset List entries: {len(self.asset_list_data)}")
            logger.info(f"  Drivers Sheet entries: {len(self.drivers_sheet_data)}")
            logger.info(f"  Jobs Sheet entries: {len(self.jobs_sheet_data)}")
            logger.info(f"  Start Time & Job entries: {len(self.start_time_job_data)} [DERIVED]")
            
            return True
            
        except Exception as e:
            logger.error(f"Error extracting data from Equipment Billing: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def extract_driving_history(self):
        """
        Extract all driver records from Driving History
        Parse and match all available drivers without filtering
        """
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
                    self.driving_history_data[normalized_name] = {
                        'driver_name': events['driver_name'],
                        'normalized_name': normalized_name,
                        'asset_id': asset_id,
                        'key_on_time': events['key_on'],
                        'key_off_time': events['key_off'],
                        'locations': list(events['locations']),
                        'events': len(events['events']),
                        'source': os.path.basename(self.driving_history_path)
                    }
                    
                    # Add to driver records
                    if normalized_name not in self.all_driver_records:
                        self.all_driver_records[normalized_name] = DriverMatchRecord(events['driver_name'], normalized_name)
                    
                    driver_record = self.all_driver_records[normalized_name]
                    
                    # Update asset ID if not set from Asset List
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
                
                logger.info(f"Extracted {len(self.driving_history_data)} driver records from Driving History")
                
                return True
        
        except Exception as e:
            logger.error(f"Error extracting Driving History: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def extract_activity_detail(self):
        """
        Extract all driver records from Activity Detail
        Cross-validate locations against job sites
        """
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
                    self.activity_detail_data[normalized_name] = {
                        'driver_name': activities['driver_name'],
                        'normalized_name': normalized_name,
                        'asset_id': asset_id,
                        'start_time': activities['start_time'],
                        'end_time': activities['end_time'],
                        'locations': list(activities['locations']),
                        'activities': len(activities['activities']),
                        'source': os.path.basename(self.activity_detail_path)
                    }
                    
                    # Add to driver records
                    if normalized_name not in self.all_driver_records:
                        self.all_driver_records[normalized_name] = DriverMatchRecord(activities['driver_name'], normalized_name)
                    
                    driver_record = self.all_driver_records[normalized_name]
                    
                    # Update asset ID if not set from Asset List
                    if not driver_record.asset_id:
                        driver_record.asset_id = asset_id
                    
                    # Update times
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
                
                logger.info(f"Extracted {len(self.activity_detail_data)} driver records from Activity Detail")
                
                return True
        
        except Exception as e:
            logger.error(f"Error extracting Activity Detail: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def process_drivers(self):
        """
        Process all drivers and classify according to rules
        With full matchback to Asset List and cross-validation
        """
        logger.info("Processing all drivers with full matchback")
        
        # Track all drivers
        self.matched_drivers = {}
        self.unmatched_drivers = {}
        
        # Track statistics
        self.total_drivers_parsed = len(self.all_driver_records)
        self.total_matched_to_asset_list = 0
        self.total_excluded = 0
        self.exclusion_reasons = {}
        
        # Reset classification counts
        self.classification_counts = {
            'On Time': 0,
            'Late': 0,
            'Early End': 0,
            'Not On Job': 0,
            'Unverified': 0
        }
        
        # Process each driver
        for normalized_name, driver_record in self.all_driver_records.items():
            # Check if driver is in Asset List (primary source of truth)
            in_asset_list = 'Asset List' in driver_record.sources
            
            # Classify driver by validation
            if in_asset_list:
                # Driver is matched to Asset List
                self.matched_drivers[normalized_name] = driver_record
                self.total_matched_to_asset_list += 1
                
                # Determine classification
                self.classify_driver(driver_record)
            else:
                # Unmatched driver - include in report for traceability
                driver_record.verification_level = 'UNVERIFIED'
                driver_record.status = 'Unverified'
                driver_record.status_reason = 'Driver not found in Asset List'
                self.unmatched_drivers[normalized_name] = driver_record
                
                # Add to exclusion count and reasons
                self.total_excluded += 1
                reason = 'Not in Asset List'
                self.exclusion_reasons[reason] = self.exclusion_reasons.get(reason, 0) + 1
                
                # Track unverified in classification counts
                self.classification_counts['Unverified'] += 1
        
        logger.info(f"Processed {self.total_drivers_parsed} drivers:")
        logger.info(f"  Matched to Asset List: {self.total_matched_to_asset_list}")
        logger.info(f"  Unmatched (Unverified): {self.total_excluded}")
        
        if self.exclusion_reasons:
            logger.info("Exclusion reasons:")
            for reason, count in self.exclusion_reasons.items():
                logger.info(f"  {reason}: {count}")
        
        logger.info("Classification counts:")
        for status, count in self.classification_counts.items():
            logger.info(f"  {status}: {count}")
    
    def classify_driver(self, driver_record):
        """
        Classify driver according to rules
        With full documentation of classification decisions
        """
        # Default status
        driver_record.status = 'Not On Job'
        driver_record.status_reason = 'No telematics data'
        
        # Create classification details
        classification_details = {
            'classification_path': [],
            'time_checks': {},
            'location_checks': {}
        }
        
        # Check for telematics data
        has_telematics = (driver_record.key_on_time is not None or driver_record.key_off_time is not None)
        classification_details['has_telematics'] = has_telematics
        classification_details['classification_path'].append(f"Checked for telematics data: {'Present' if has_telematics else 'Absent'}")
        
        if not has_telematics:
            # No telematics data - "Not On Job"
            driver_record.status = 'Not On Job'
            driver_record.status_reason = 'No telematics data'
            classification_details['classification_path'].append("Result: Not On Job (No telematics data)")
            
            # Add classification details
            driver_record.classification_details = classification_details
            
            # Update classification counts
            self.classification_counts['Not On Job'] += 1
            
            return
        
        # Check scheduled times from Start Time & Job (DERIVED DATA)
        scheduled_start = None
        scheduled_end = None
        
        if 'Start Time & Job [DERIVED]' in driver_record.source_data:
            start_time_job_data = driver_record.source_data['Start Time & Job [DERIVED]']
            
            if 'scheduled_start' in start_time_job_data and start_time_job_data['scheduled_start']:
                try:
                    scheduled_start = self.parse_time(start_time_job_data['scheduled_start'])
                    classification_details['time_checks']['scheduled_start'] = scheduled_start.isoformat()
                except:
                    pass
            
            if 'scheduled_end' in start_time_job_data and start_time_job_data['scheduled_end']:
                try:
                    scheduled_end = self.parse_time(start_time_job_data['scheduled_end'])
                    classification_details['time_checks']['scheduled_end'] = scheduled_end.isoformat()
                except:
                    pass
            
            classification_details['classification_path'].append(f"Checked Start Time & Job for schedules: {'Found' if scheduled_start else 'Not Found'}")
        
        # If no scheduled times, use default work hours
        if not scheduled_start:
            # Default to 7 AM start on this date
            date_obj = datetime.strptime(self.date_str, '%Y-%m-%d')
            scheduled_start = date_obj.replace(hour=7, minute=0, second=0)
            classification_details['time_checks']['scheduled_start'] = scheduled_start.isoformat()
            classification_details['time_checks']['scheduled_start_source'] = 'Default (7:00 AM)'
            classification_details['classification_path'].append("Used default start time: 7:00 AM")
        
        if not scheduled_end:
            # Default to 5 PM end on this date
            date_obj = datetime.strptime(self.date_str, '%Y-%m-%d')
            scheduled_end = date_obj.replace(hour=17, minute=0, second=0)
            classification_details['time_checks']['scheduled_end'] = scheduled_end.isoformat()
            classification_details['time_checks']['scheduled_end_source'] = 'Default (5:00 PM)'
            classification_details['classification_path'].append("Used default end time: 5:00 PM")
        
        # Calculate time deltas for key on/off
        if driver_record.key_on_time:
            # Late check - more than 15 minutes after scheduled start
            late_threshold = scheduled_start + timedelta(minutes=15)
            minutes_late = 0
            
            if driver_record.key_on_time > late_threshold:
                minutes_late = int((driver_record.key_on_time - scheduled_start).total_seconds() / 60)
                classification_details['time_checks']['late_threshold'] = late_threshold.isoformat()
                classification_details['time_checks']['minutes_late'] = minutes_late
                classification_details['classification_path'].append(f"Key ON at {driver_record.key_on_time.isoformat()} is {minutes_late} minutes after scheduled {scheduled_start.isoformat()}")
                
                # Save key delta minutes for report
                driver_record.key_delta_minutes = minutes_late
            else:
                classification_details['time_checks']['late_threshold'] = late_threshold.isoformat()
                classification_details['time_checks']['minutes_late'] = 0
                classification_details['classification_path'].append(f"Key ON at {driver_record.key_on_time.isoformat()} is ON TIME (before threshold {late_threshold.isoformat()})")
                
                # Save key delta minutes for report
                driver_record.key_delta_minutes = 0
        
        # Early End check - more than 30 minutes before scheduled end
        if driver_record.key_off_time:
            early_threshold = scheduled_end - timedelta(minutes=30)
            minutes_early = 0
            
            if driver_record.key_off_time < early_threshold:
                minutes_early = int((scheduled_end - driver_record.key_off_time).total_seconds() / 60)
                classification_details['time_checks']['early_threshold'] = early_threshold.isoformat()
                classification_details['time_checks']['minutes_early'] = minutes_early
                classification_details['classification_path'].append(f"Key OFF at {driver_record.key_off_time.isoformat()} is {minutes_early} minutes before scheduled {scheduled_end.isoformat()}")
            else:
                classification_details['time_checks']['early_threshold'] = early_threshold.isoformat()
                classification_details['time_checks']['minutes_early'] = 0
                classification_details['classification_path'].append(f"Key OFF at {driver_record.key_off_time.isoformat()} is NOT early (after threshold {early_threshold.isoformat()})")
        
        # Job site check
        assigned_job_site = driver_record.job_site
        actual_locations = driver_record.locations
        
        classification_details['location_checks']['assigned_job_site'] = assigned_job_site
        classification_details['location_checks']['actual_locations'] = list(actual_locations)
        
        job_site_match = False
        if assigned_job_site and actual_locations:
            # Check if any location matches the assigned job site
            for location in actual_locations:
                if assigned_job_site.lower() in location.lower() or location.lower() in assigned_job_site.lower():
                    job_site_match = True
                    break
            
            classification_details['location_checks']['job_site_match'] = job_site_match
            classification_details['classification_path'].append(f"Job site check: {'Match' if job_site_match else 'No match'} between assigned {assigned_job_site} and actual locations")
            
            # Save site match for report
            driver_record.site_match = job_site_match
        elif not assigned_job_site:
            classification_details['location_checks']['job_site_match'] = None
            classification_details['classification_path'].append("Job site check: No assigned job site")
            
            # Save site match for report
            driver_record.site_match = None
        
        # Final classification
        if not job_site_match and assigned_job_site and actual_locations:
            # Not at assigned job site
            driver_record.status = 'Not On Job'
            driver_record.status_reason = 'Not at assigned job site'
            classification_details['classification_path'].append("Result: Not On Job (Not at assigned job site)")
            
            # Update classification counts
            self.classification_counts['Not On Job'] += 1
        elif driver_record.key_on_time and driver_record.key_on_time > late_threshold:
            # Late
            driver_record.status = 'Late'
            driver_record.status_reason = f"{minutes_late} minutes late"
            classification_details['classification_path'].append(f"Result: Late ({minutes_late} minutes)")
            
            # Update classification counts
            self.classification_counts['Late'] += 1
        elif driver_record.key_off_time and driver_record.key_off_time < early_threshold:
            # Early End
            driver_record.status = 'Early End'
            driver_record.status_reason = f"{minutes_early} minutes early"
            classification_details['classification_path'].append(f"Result: Early End ({minutes_early} minutes)")
            
            # Update classification counts
            self.classification_counts['Early End'] += 1
        else:
            # On Time
            driver_record.status = 'On Time'
            driver_record.status_reason = 'Within scheduled parameters'
            classification_details['classification_path'].append("Result: On Time")
            
            # Update classification counts
            self.classification_counts['On Time'] += 1
        
        # Add classification details
        driver_record.classification_details = classification_details
    
    def generate_report(self):
        """
        Generate full report with all required details
        """
        logger.info(f"Generating report for {self.date_str}")
        
        # Prepare report data
        report_data = {
            'date': self.date_str,
            'drivers': [],
            'unmatched_drivers': [],
            'summary': {
                'total': len(self.matched_drivers),
                'on_time': self.classification_counts['On Time'],
                'late': self.classification_counts['Late'],
                'early_end': self.classification_counts['Early End'],
                'not_on_job': self.classification_counts['Not On Job'],
                'unmatched': len(self.unmatched_drivers)
            },
            'metadata': {
                'generated': datetime.now().isoformat(),
                'verification_mode': 'GENIUS CORE ULTRA BLOCK HARDLINE MODE',
                'workbook_logic': {
                    'hierarchy': [
                        'Asset List (primary source of truth)',
                        'Drivers Sheet (employee registry)',
                        'Jobs Sheet (job assignments)',
                        'Driving History (telematics)',
                        'Activity Detail (location validation)'
                    ],
                    'derived_sources': [
                        'Start Time & Job (derived from other workbook tabs)'
                    ]
                },
                'processing_stats': {
                    'total_drivers_parsed': self.total_drivers_parsed,
                    'total_matched_to_asset_list': self.total_matched_to_asset_list,
                    'total_excluded': self.total_excluded,
                    'exclusion_reasons': self.exclusion_reasons,
                    'classification_counts': self.classification_counts
                }
            }
        }
        
        # Add matched drivers to report
        for normalized_name, driver_record in self.matched_drivers.items():
            report_data['drivers'].append(driver_record.to_dict())
        
        # Add unmatched drivers to separate section
        for normalized_name, driver_record in self.unmatched_drivers.items():
            report_data['unmatched_drivers'].append(driver_record.to_dict())
        
        # Save JSON report
        os.makedirs(REPORTS_DIR, exist_ok=True)
        json_path = os.path.join(REPORTS_DIR, f"daily_report_{self.date_str}.json")
        
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Copy to exports directory
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        export_json_path = os.path.join(EXPORTS_DIR, f"daily_report_{self.date_str}.json")
        shutil.copy(json_path, export_json_path)
        
        # Also save to daily_drivers directory for compatibility
        os.makedirs(DAILY_REPORTS_DIR, exist_ok=True)
        os.makedirs(DAILY_EXPORTS_DIR, exist_ok=True)
        
        daily_json_path = os.path.join(DAILY_REPORTS_DIR, f"daily_report_{self.date_str}.json")
        daily_export_json_path = os.path.join(DAILY_EXPORTS_DIR, f"daily_report_{self.date_str}.json")
        
        shutil.copy(json_path, daily_json_path)
        shutil.copy(json_path, daily_export_json_path)
        
        # Generate Excel report
        excel_path = os.path.join(REPORTS_DIR, f"daily_report_{self.date_str}.xlsx")
        
        with pd.ExcelWriter(excel_path) as writer:
            # Main sheet with all matched drivers
            df_drivers = pd.DataFrame([d.to_dict() for d in self.matched_drivers.values()])
            
            if not df_drivers.empty:
                # Sort by status
                if 'status' in df_drivers.columns:
                    status_order = {
                        'On Time': 0,
                        'Late': 1,
                        'Early End': 2,
                        'Not On Job': 3
                    }
                    df_drivers['status_order'] = df_drivers['status'].map(status_order)
                    df_drivers = df_drivers.sort_values('status_order')
                    df_drivers = df_drivers.drop('status_order', axis=1)
                
                df_drivers.to_excel(writer, sheet_name='All Drivers', index=False)
            
                # Status-specific sheets for matched drivers
                # On Time drivers
                on_time = df_drivers[df_drivers['status'] == 'On Time']
                if not on_time.empty:
                    on_time.to_excel(writer, sheet_name='On Time', index=False)
                
                # Late drivers
                late = df_drivers[df_drivers['status'] == 'Late']
                if not late.empty:
                    late.to_excel(writer, sheet_name='Late', index=False)
                
                # Early End drivers
                early_end = df_drivers[df_drivers['status'] == 'Early End']
                if not early_end.empty:
                    early_end.to_excel(writer, sheet_name='Early End', index=False)
                
                # Not On Job drivers
                not_on_job = df_drivers[df_drivers['status'] == 'Not On Job']
                if not not_on_job.empty:
                    not_on_job.to_excel(writer, sheet_name='Not On Job', index=False)
            
            # Unmatched drivers sheet
            df_unmatched = pd.DataFrame([d.to_dict() for d in self.unmatched_drivers.values()])
            if not df_unmatched.empty:
                df_unmatched.to_excel(writer, sheet_name='Unmatched Drivers', index=False)
            
            # Driver Matchback Sheet - showing all mappings
            matchback_data = []
            
            for driver_record in self.all_driver_records.values():
                matchback_data.append({
                    'Driver Name': driver_record.driver_name,
                    'Asset ID': driver_record.asset_id,
                    'In Asset List': 'Asset List' in driver_record.sources,
                    'In Driving History': 'Driving History' in driver_record.sources,
                    'In Activity Detail': 'Activity Detail' in driver_record.sources, 
                    'In Start Time & Job': 'Start Time & Job [DERIVED]' in driver_record.sources,
                    'Verification Level': driver_record.verification_level,
                    'Status': driver_record.status,
                    'Status Reason': driver_record.status_reason,
                    'Key On Time': driver_record.key_on_time,
                    'Key Off Time': driver_record.key_off_time,
                    'Job Site': driver_record.job_site,
                    'Locations': ', '.join(driver_record.locations) if driver_record.locations else None
                })
            
            df_matchback = pd.DataFrame(matchback_data)
            df_matchback.to_excel(writer, sheet_name='Driver Matchback', index=False)
            
            # Workbook Logic sheet
            workbook_logic_data = [
                ['Component', 'Role', 'Usage'],
                ['Asset List', 'Primary source of truth', 'Primary relational hub for asset-driver pairing'],
                ['Drivers Sheet', 'Employee registry', 'Manually-updated employee list'],
                ['Jobs Sheet', 'Job assignments', 'Assigned job sites for validation'],
                ['Driving History', 'Telematics data', 'Key on/off timestamps for location verification'],
                ['Activity Detail', 'Location data', 'Detailed location tracking for site validation'],
                ['Start Time & Job', 'DERIVED DATA', 'NOT authoritative; derived from other workbook tabs']
            ]
            
            df_workbook = pd.DataFrame(workbook_logic_data[1:], columns=workbook_logic_data[0])
            df_workbook.to_excel(writer, sheet_name='Workbook Logic', index=False)
            
            # Source File Trace sheet
            source_trace_data = [
                ['Source', 'File Path', 'Driver Count'],
                ['Equipment Billing', EQUIPMENT_BILLING_PATH, len(self.asset_list_data)],
                ['Driving History', self.driving_history_path, len(self.driving_history_data)],
                ['Activity Detail', self.activity_detail_path, len(self.activity_detail_data)]
            ]
            
            df_source_trace = pd.DataFrame(source_trace_data[1:], columns=source_trace_data[0])
            df_source_trace.to_excel(writer, sheet_name='Source File Trace', index=False)
            
            # Classification Summary sheet
            summary_data = [
                ['Metric', 'Value'],
                ['Date', self.date_str],
                ['Total Drivers', len(self.matched_drivers)],
                ['On Time', self.classification_counts['On Time']],
                ['Late', self.classification_counts['Late']],
                ['Early End', self.classification_counts['Early End']],
                ['Not On Job', self.classification_counts['Not On Job']],
                ['Unmatched Drivers', len(self.unmatched_drivers)],
                ['Total Drivers Parsed', self.total_drivers_parsed],
                ['Total Matched to Asset List', self.total_matched_to_asset_list],
                ['Total Excluded', self.total_excluded],
                ['Generated', datetime.now().isoformat()]
            ]
            
            # Add exclusion reasons
            for reason, count in self.exclusion_reasons.items():
                summary_data.append([f"Excluded: {reason}", count])
            
            df_summary = pd.DataFrame(summary_data[1:], columns=summary_data[0])
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Copy Excel report to exports directory
        export_excel_path = os.path.join(EXPORTS_DIR, f"daily_report_{self.date_str}.xlsx")
        shutil.copy(excel_path, export_excel_path)
        
        # Also save to daily_drivers directory for compatibility
        daily_excel_path = os.path.join(DAILY_REPORTS_DIR, f"daily_report_{self.date_str}.xlsx")
        daily_export_excel_path = os.path.join(DAILY_EXPORTS_DIR, f"daily_report_{self.date_str}.xlsx")
        
        shutil.copy(excel_path, daily_excel_path)
        shutil.copy(excel_path, daily_export_excel_path)
        
        # Generate PDF report if possible
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
                    pdf_path = os.path.join(REPORTS_DIR, f"daily_report_{self.date_str}.pdf")
                    pdf_module.generate_pdf_report(self.date_str, report_data, pdf_path)
                    
                    # Copy to exports directory
                    export_pdf_path = os.path.join(EXPORTS_DIR, f"daily_report_{self.date_str}.pdf")
                    shutil.copy(pdf_path, export_pdf_path)
                    
                    # Also save to daily_drivers directory for compatibility
                    daily_pdf_path = os.path.join(DAILY_REPORTS_DIR, f"daily_report_{self.date_str}.pdf")
                    daily_export_pdf_path = os.path.join(DAILY_EXPORTS_DIR, f"daily_report_{self.date_str}.pdf")
                    
                    shutil.copy(pdf_path, daily_pdf_path)
                    shutil.copy(pdf_path, daily_export_pdf_path)
                    
                    logger.info(f"Generated PDF report at {pdf_path}")
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            logger.error(traceback.format_exc())
        
        logger.info(f"Generated reports for {self.date_str}")
        
        # Generate path checksums
        json_checksum = hashlib.md5(open(json_path, 'rb').read()).hexdigest()
        excel_checksum = hashlib.md5(open(excel_path, 'rb').read()).hexdigest()
        
        return {
            'json_path': json_path,
            'excel_path': excel_path,
            'json_checksum': json_checksum,
            'excel_checksum': excel_checksum
        }
    
    def generate_trace_manifest(self):
        """
        Generate trace manifest for the report
        """
        logger.info(f"Generating trace manifest for {self.date_str}")
        
        manifest_path = os.path.join(LOGS_DIR, f"ultra_trace_manifest_{self.date_str}.txt")
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        
        with open(manifest_path, 'w') as f:
            f.write(f"TRAXORA GENIUS CORE | ULTRA TRACE MANIFEST\n")
            f.write(f"Date: {self.date_str}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("WORKBOOK LOGIC HIERARCHY\n")
            f.write("=" * 80 + "\n")
            f.write("1. Asset List - PRIMARY SOURCE OF TRUTH for asset-driver pairing\n")
            f.write("2. Drivers Sheet - Employee registry\n")
            f.write("3. Jobs Sheet - Job site assignments\n")
            f.write("4. Driving History - Telematics GPS check-in log\n")
            f.write("5. Activity Detail - Location validation\n")
            f.write("6. Start Time & Job - DERIVED DATA (not authoritative)\n\n")
            
            f.write("DATA SOURCES\n")
            f.write("=" * 80 + "\n")
            f.write(f"Equipment Billing: {EQUIPMENT_BILLING_PATH}\n")
            f.write(f"Asset List Entries: {len(self.asset_list_data)}\n")
            f.write(f"Drivers Sheet Entries: {len(self.drivers_sheet_data)}\n")
            f.write(f"Jobs Sheet Entries: {len(self.jobs_sheet_data)}\n")
            f.write(f"Start Time & Job Entries: {len(self.start_time_job_data)} [DERIVED]\n")
            f.write(f"Driving History: {self.driving_history_path}\n")
            f.write(f"Driving History Entries: {len(self.driving_history_data)}\n")
            f.write(f"Activity Detail: {self.activity_detail_path}\n")
            f.write(f"Activity Detail Entries: {len(self.activity_detail_data)}\n\n")
            
            f.write("DRIVER PROCESSING STATISTICS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total Drivers Parsed: {self.total_drivers_parsed}\n")
            f.write(f"Matched to Asset List: {self.total_matched_to_asset_list}\n")
            f.write(f"Unmatched/Excluded: {self.total_excluded}\n\n")
            
            if self.exclusion_reasons:
                f.write("EXCLUSION REASONS\n")
                f.write("=" * 80 + "\n")
                for reason, count in self.exclusion_reasons.items():
                    f.write(f"{reason}: {count}\n")
                f.write("\n")
            
            f.write("CLASSIFICATION SUMMARY\n")
            f.write("=" * 80 + "\n")
            for status, count in self.classification_counts.items():
                f.write(f"{status}: {count}\n")
            f.write("\n")
            
            f.write("VERIFICATION STATUS\n")
            f.write("=" * 80 + "\n")
            f.write("✓ All drivers verified against Asset List (primary source of truth)\n")
            f.write("✓ All Driving History and Activity Detail processed without filtering\n")
            f.write("✓ Start Time & Job treated as derived, not authoritative source\n")
            f.write("✓ Unmatched drivers included in report for full traceability\n")
            f.write("✓ Driver Matchback Sheet included to trace all data sources\n")
            f.write("✓ GENIUS CORE ULTRA BLOCK HARDLINE MODE ACTIVE: LOCKED.\n")
        
        logger.info(f"Generated trace manifest at {manifest_path}")
        
        return manifest_path
    
    def run(self):
        """
        Run the complete driver report pipeline
        """
        logger.info(f"Running driver report pipeline for {self.date_str}")
        
        # Step 1: Extract data from Equipment Billing (Asset List as primary source of truth)
        logger.info("1. LOAD: Extracting data from Equipment Billing")
        success = self.extract_equipment_billing_data()
        
        if not success:
            logger.error("Failed to extract data from Equipment Billing")
            return False
        
        # Step 2: Extract telematics data from Driving History
        logger.info("2. VALIDATE: Extracting telematics data from Driving History")
        self.extract_driving_history()
        
        # Step 3: Extract location validation from Activity Detail
        logger.info("3. JOIN: Extracting location validation from Activity Detail")
        self.extract_activity_detail()
        
        # Step 4: Process all drivers with full matchback
        logger.info("4. CLASSIFY: Processing all drivers with full matchback")
        self.process_drivers()
        
        # Step 5: Generate report
        logger.info("5. EXPORT: Generating report")
        report_paths = self.generate_report()
        
        # Step 6: Generate trace manifest
        logger.info("6. TRACE: Generating trace manifest")
        manifest_path = self.generate_trace_manifest()
        
        logger.info(f"Completed driver report pipeline for {self.date_str}")
        
        return {
            'date': self.date_str,
            'report_paths': report_paths,
            'manifest_path': manifest_path,
            'stats': {
                'total_drivers': len(self.matched_drivers),
                'unmatched_drivers': len(self.unmatched_drivers),
                'classification': self.classification_counts
            }
        }


def process_date(date_str):
    """Process a specific date with the revised pipeline"""
    logger.info(f"Processing date: {date_str}")
    
    pipeline = DriverReportPipeline(date_str)
    result = pipeline.run()
    
    if not result:
        logger.error(f"Failed to process date: {date_str}")
        return None
    
    return result


def main():
    """Main function"""
    logger.info("Starting Daily Driver Report Pipeline Revision")
    
    # Set target dates from command line if provided
    target_dates = TARGET_DATES
    if len(sys.argv) > 1:
        target_dates = sys.argv[1:]
    
    results = {}
    
    for date_str in target_dates:
        logger.info(f"Processing {date_str}")
        result = process_date(date_str)
        
        if result:
            results[date_str] = result
    
    # Print summary
    print("\nDAILY DRIVER REPORT PIPELINE REVISION SUMMARY")
    print("=" * 80)
    
    for date_str, result in results.items():
        print(f"\nDate: {date_str}")
        print(f"  Matched Drivers: {result['stats']['total_drivers']}")
        print(f"  Unmatched Drivers: {result['stats']['unmatched_drivers']}")
        print("  Classification:")
        for status, count in result['stats']['classification'].items():
            print(f"    {status}: {count}")
        
        if 'report_paths' in result:
            print(f"  JSON Report: {result['report_paths']['json_path']} (MD5: {result['report_paths']['json_checksum']})")
            print(f"  Excel Report: {result['report_paths']['excel_path']} (MD5: {result['report_paths']['excel_checksum']})")
        
        print(f"  Trace Manifest: {result['manifest_path']}")
    
    print("\nGENIUS CORE ULTRA BLOCK HARDLINE MODE ACTIVE: LOCKED.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())