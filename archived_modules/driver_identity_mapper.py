#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Driver Identity Mapper

This script creates a robust mapping between driver identities across different data sources:
1. Asset List (primary source of truth)
2. Driving History (telematics data)
3. Activity Detail (location validation)

It handles different name formats, excludes trailers, and creates a unified identity dataset.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import traceback
import re
import csv
from pathlib import Path
import difflib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs/identity_mapper', exist_ok=True)
mapper_log = logging.FileHandler('logs/identity_mapper/mapper.log')
mapper_log.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(mapper_log)

# Paths
DATA_DIR = 'data'
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
REPORTS_DIR = 'reports/identity_mapper'
EXPORTS_DIR = 'exports/identity_mapper'

# Equipment billing workbook
EQUIPMENT_BILLING_PATH = 'attached_assets/EQ MONTHLY BILLINGS WORKING SPREADSHEET - APRIL 2025.xlsx'

# Create directories
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)


class DriverIdentityMapper:
    """
    Maps driver identities across different data sources and creates a unified identity dataset.
    """
    
    def __init__(self):
        """Initialize the identity mapper"""
        # Data sources
        self.asset_list_drivers = {}  # Drivers from Asset List (primary source)
        self.driving_history_drivers = {}  # Drivers from Driving History
        self.activity_detail_drivers = {}  # Drivers from Activity Detail
        
        # Excluded asset types (trailers, etc.)
        self.excluded_asset_types = [
            'TRAILER', 'TLR', 'DUMP', 'FLATBED', 'UTILITY', 'LOWBOY', 'EQUIPMENT'
        ]
        
        # Asset count by type
        self.asset_counts = {
            'total': 0,
            'vehicles': 0,
            'trailers': 0,
            'other': 0
        }
        
        # Normalized names dictionary
        self.name_mappings = {}  # Maps normalized names to original names
        self.reverse_mappings = {}  # Maps original names to normalized names
        
        # Mapping statistics
        self.mapping_stats = {
            'total_asset_list': 0,
            'total_driving_history': 0,
            'total_activity_detail': 0,
            'matched_driving_history': 0,
            'matched_activity_detail': 0,
            'unmatched_driving_history': 0,
            'unmatched_activity_detail': 0,
            'trailers_excluded': 0
        }
        
        # Final identity dataset
        self.identity_dataset = {}
    
    def normalize_name(self, name):
        """
        Normalize driver name for consistent matching across different formats
        Handles various name formats:
        - "Last, First" → "first last"
        - "First Last" → "first last"
        - "LAST, FIRST M." → "first m last"
        """
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
    
    def is_trailer(self, asset_id):
        """
        Check if an asset is a trailer based on its ID
        """
        if not asset_id or pd.isna(asset_id):
            return False
        
        asset_str = str(asset_id).upper().strip()
        
        # Check if asset ID contains trailer keywords
        for trailer_type in self.excluded_asset_types:
            if trailer_type in asset_str:
                return True
        
        # Check if asset ID matches trailer patterns
        trailer_patterns = [
            r'^T-\d+',  # T-123
            r'^TLR-\d+',  # TLR-123
            r'^TR-\d+',  # TR-123
            r'^TRLR-\d+',  # TRLR-123
            r'^TRAILER-\d+'  # TRAILER-123
        ]
        
        for pattern in trailer_patterns:
            if re.match(pattern, asset_str):
                return True
        
        return False
    
    def extract_asset_list(self):
        """
        Extract driver data from the Asset List (primary source of truth)
        """
        logger.info("Extracting driver data from Asset List")
        
        if not os.path.exists(EQUIPMENT_BILLING_PATH):
            logger.error(f"Equipment Billing file not found: {EQUIPMENT_BILLING_PATH}")
            return False
        
        try:
            # Load workbook
            workbook = pd.ExcelFile(EQUIPMENT_BILLING_PATH)
            sheets = workbook.sheet_names
            
            # Find Asset List sheet
            asset_sheet = None
            if 'FLEET' in sheets:
                asset_sheet = 'FLEET'
            elif 'Equip Table' in sheets:
                asset_sheet = 'Equip Table'
            elif 'Asset List' in sheets:
                asset_sheet = 'Asset List'
            
            if not asset_sheet:
                logger.error("Asset List sheet not found in Equipment Billing workbook")
                return False
            
            # Load Asset List sheet
            df = pd.read_excel(workbook, sheet_name=asset_sheet)
            
            # Normalize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Find relevant columns
            asset_col = None
            driver_col = None
            job_col = None
            
            for col in ['equip_#', 'equip_id', 'equipment_id', 'equipment', 'asset_id', 'asset']:
                if col in df.columns:
                    asset_col = col
                    break
            
            for col in ['driver', 'driver_name', 'employee', 'employee_name', 'operator', 'assigned_to']:
                if col in df.columns:
                    driver_col = col
                    break
            
            for col in ['job', 'job_site', 'site', 'location', 'project']:
                if col in df.columns:
                    job_col = col
                    break
            
            # Process rows
            if asset_col and driver_col:
                logger.info(f"Found asset column: {asset_col}, driver column: {driver_col}")
                
                # Reset asset counts
                self.asset_counts = {
                    'total': 0,
                    'vehicles': 0,
                    'trailers': 0,
                    'other': 0
                }
                
                # Count trailers excluded
                trailers_excluded = 0
                
                for _, row in df.iterrows():
                    self.asset_counts['total'] += 1
                    
                    asset_id = str(row[asset_col]).strip() if pd.notna(row[asset_col]) else None
                    driver_name = str(row[driver_col]).strip() if pd.notna(row[driver_col]) else None
                    
                    # Skip empty values
                    if not asset_id or not driver_name:
                        continue
                    
                    if asset_id.lower() in ['nan', 'none', 'null', ''] or driver_name.lower() in ['nan', 'none', 'null', '']:
                        continue
                    
                    # Classify asset
                    if self.is_trailer(asset_id):
                        self.asset_counts['trailers'] += 1
                        trailers_excluded += 1
                        # Skip trailers for driver mapping
                        continue
                    else:
                        self.asset_counts['vehicles'] += 1
                    
                    # Get job site if available
                    job_site = None
                    if job_col and pd.notna(row[job_col]):
                        job_site = str(row[job_col]).strip()
                        if job_site.lower() in ['nan', 'none', 'null', '']:
                            job_site = None
                    
                    # Normalize driver name
                    original_name = driver_name
                    normalized_name = self.normalize_name(driver_name)
                    
                    if not normalized_name:
                        continue
                    
                    # Add to name mappings
                    self.name_mappings[normalized_name] = original_name
                    self.reverse_mappings[original_name] = normalized_name
                    
                    # Create driver record
                    if normalized_name not in self.asset_list_drivers:
                        self.asset_list_drivers[normalized_name] = {
                            'name': original_name,
                            'normalized_name': normalized_name,
                            'assets': [],
                            'job_sites': set()
                        }
                    
                    # Add asset to driver
                    self.asset_list_drivers[normalized_name]['assets'].append(asset_id.upper())
                    
                    # Add job site if available
                    if job_site:
                        self.asset_list_drivers[normalized_name]['job_sites'].add(job_site)
                
                self.mapping_stats['total_asset_list'] = len(self.asset_list_drivers)
                self.mapping_stats['trailers_excluded'] = trailers_excluded
                
                logger.info(f"Extracted {len(self.asset_list_drivers)} drivers from Asset List")
                logger.info(f"Asset counts: Total={self.asset_counts['total']}, Vehicles={self.asset_counts['vehicles']}, Trailers={self.asset_counts['trailers']}")
                logger.info(f"Excluded {trailers_excluded} trailers from driver mapping")
                
                return True
            else:
                logger.error("Required columns not found in Asset List")
                return False
                
        except Exception as e:
            logger.error(f"Error extracting Asset List data: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def extract_driving_history(self, date_str=None):
        """
        Extract driver data from Driving History for a specific date
        """
        if not date_str:
            # Default to today
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        date_formatted = date_str.replace('-', '')
        
        # Look for driving history files
        driving_history_path = f'data/driving_history/DrivingHistory_{date_formatted}.csv'
        
        if not os.path.exists(driving_history_path):
            logger.warning(f"Driving History file not found at {driving_history_path}, looking for alternates...")
            
            # Check for other potential driving history files
            for root, dirs, files in os.walk('data/driving_history'):
                for file in files:
                    if file.endswith('.csv') and date_formatted in file:
                        driving_history_path = os.path.join(root, file)
                        logger.info(f"Found alternate Driving History file: {driving_history_path}")
                        break
            
            # Also check attached_assets
            if not os.path.exists(driving_history_path):
                for root, dirs, files in os.walk('attached_assets'):
                    for file in files:
                        if file.endswith('.csv') and ('driv' in file.lower() or 'history' in file.lower()) and date_formatted in file:
                            driving_history_path = os.path.join(root, file)
                            logger.info(f"Found alternate Driving History file in attached_assets: {driving_history_path}")
                            break
            
            if not os.path.exists(driving_history_path):
                logger.error(f"No Driving History file found for date {date_str}")
                return False
        
        logger.info(f"Extracting driver data from Driving History: {driving_history_path}")
        
        try:
            # Determine delimiter
            with open(driving_history_path, 'r') as f:
                header = f.readline().strip()
            
            delimiter = ',' if ',' in header else ';'
            
            # Load CSV file
            df = pd.read_csv(driving_history_path, delimiter=delimiter)
            
            # Normalize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Find relevant columns
            driver_col = None
            asset_col = None
            
            for col in ['driver', 'driver_name', 'employee', 'employee_name', 'operator']:
                if col in df.columns:
                    driver_col = col
                    break
            
            for col in ['asset', 'asset_id', 'equipment', 'equipment_id', 'vehicle', 'vehicle_id']:
                if col in df.columns:
                    asset_col = col
                    break
            
            # Process rows
            if driver_col and asset_col:
                logger.info(f"Found driver column: {driver_col}, asset column: {asset_col}")
                
                # Reset driving history drivers
                self.driving_history_drivers = {}
                
                for _, row in df.iterrows():
                    driver_name = str(row[driver_col]).strip() if pd.notna(row[driver_col]) else None
                    asset_id = str(row[asset_col]).strip() if pd.notna(row[asset_col]) else None
                    
                    # Skip empty values
                    if not driver_name or not asset_id:
                        continue
                    
                    if driver_name.lower() in ['nan', 'none', 'null', ''] or asset_id.lower() in ['nan', 'none', 'null', '']:
                        continue
                    
                    # Skip trailers
                    if self.is_trailer(asset_id):
                        continue
                    
                    # Normalize driver name
                    original_name = driver_name
                    normalized_name = self.normalize_name(driver_name)
                    
                    if not normalized_name:
                        continue
                    
                    # Add to name mappings
                    self.name_mappings[normalized_name] = original_name
                    self.reverse_mappings[original_name] = normalized_name
                    
                    # Create driver record
                    if normalized_name not in self.driving_history_drivers:
                        self.driving_history_drivers[normalized_name] = {
                            'name': original_name,
                            'normalized_name': normalized_name,
                            'assets': [],
                            'source': os.path.basename(driving_history_path)
                        }
                    
                    # Add asset to driver
                    if asset_id.upper() not in self.driving_history_drivers[normalized_name]['assets']:
                        self.driving_history_drivers[normalized_name]['assets'].append(asset_id.upper())
                
                self.mapping_stats['total_driving_history'] = len(self.driving_history_drivers)
                
                logger.info(f"Extracted {len(self.driving_history_drivers)} drivers from Driving History")
                
                return True
            else:
                logger.error("Required columns not found in Driving History")
                return False
                
        except Exception as e:
            logger.error(f"Error extracting Driving History data: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def extract_activity_detail(self, date_str=None):
        """
        Extract driver data from Activity Detail for a specific date
        """
        if not date_str:
            # Default to today
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        date_formatted = date_str.replace('-', '')
        
        # Look for activity detail files
        activity_detail_path = f'data/activity_detail/ActivityDetail_{date_formatted}.csv'
        
        if not os.path.exists(activity_detail_path):
            logger.warning(f"Activity Detail file not found at {activity_detail_path}, looking for alternates...")
            
            # Check for other potential activity detail files
            for root, dirs, files in os.walk('data/activity_detail'):
                for file in files:
                    if file.endswith('.csv') and date_formatted in file:
                        activity_detail_path = os.path.join(root, file)
                        logger.info(f"Found alternate Activity Detail file: {activity_detail_path}")
                        break
            
            # Also check attached_assets
            if not os.path.exists(activity_detail_path):
                for root, dirs, files in os.walk('attached_assets'):
                    for file in files:
                        if file.endswith('.csv') and ('activ' in file.lower() or 'detail' in file.lower()) and date_formatted in file:
                            activity_detail_path = os.path.join(root, file)
                            logger.info(f"Found alternate Activity Detail file in attached_assets: {activity_detail_path}")
                            break
            
            if not os.path.exists(activity_detail_path):
                logger.warning(f"No Activity Detail file found for date {date_str} - proceeding without it")
                return True
        
        logger.info(f"Extracting driver data from Activity Detail: {activity_detail_path}")
        
        try:
            # Determine delimiter
            with open(activity_detail_path, 'r') as f:
                header = f.readline().strip()
            
            delimiter = ',' if ',' in header else ';'
            
            # Load CSV file
            df = pd.read_csv(activity_detail_path, delimiter=delimiter)
            
            # Normalize column names
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            # Find relevant columns
            driver_col = None
            asset_col = None
            
            for col in ['driver', 'driver_name', 'employee', 'employee_name', 'operator']:
                if col in df.columns:
                    driver_col = col
                    break
            
            for col in ['asset', 'asset_id', 'equipment', 'equipment_id', 'vehicle', 'vehicle_id']:
                if col in df.columns:
                    asset_col = col
                    break
            
            # Process rows
            if driver_col and asset_col:
                logger.info(f"Found driver column: {driver_col}, asset column: {asset_col}")
                
                # Reset activity detail drivers
                self.activity_detail_drivers = {}
                
                for _, row in df.iterrows():
                    driver_name = str(row[driver_col]).strip() if pd.notna(row[driver_col]) else None
                    asset_id = str(row[asset_col]).strip() if pd.notna(row[asset_col]) else None
                    
                    # Skip empty values
                    if not driver_name or not asset_id:
                        continue
                    
                    if driver_name.lower() in ['nan', 'none', 'null', ''] or asset_id.lower() in ['nan', 'none', 'null', '']:
                        continue
                    
                    # Skip trailers
                    if self.is_trailer(asset_id):
                        continue
                    
                    # Normalize driver name
                    original_name = driver_name
                    normalized_name = self.normalize_name(driver_name)
                    
                    if not normalized_name:
                        continue
                    
                    # Add to name mappings
                    self.name_mappings[normalized_name] = original_name
                    self.reverse_mappings[original_name] = normalized_name
                    
                    # Create driver record
                    if normalized_name not in self.activity_detail_drivers:
                        self.activity_detail_drivers[normalized_name] = {
                            'name': original_name,
                            'normalized_name': normalized_name,
                            'assets': [],
                            'source': os.path.basename(activity_detail_path)
                        }
                    
                    # Add asset to driver
                    if asset_id.upper() not in self.activity_detail_drivers[normalized_name]['assets']:
                        self.activity_detail_drivers[normalized_name]['assets'].append(asset_id.upper())
                
                self.mapping_stats['total_activity_detail'] = len(self.activity_detail_drivers)
                
                logger.info(f"Extracted {len(self.activity_detail_drivers)} drivers from Activity Detail")
                
                return True
            else:
                logger.error("Required columns not found in Activity Detail")
                return False
                
        except Exception as e:
            logger.error(f"Error extracting Activity Detail data: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def find_best_match(self, name, candidates):
        """
        Find the best match for a name in a list of candidates using fuzzy matching
        """
        if not name or not candidates:
            return None
        
        # Normalize the name
        normalized_name = self.normalize_name(name)
        
        # Direct match
        if normalized_name in candidates:
            return normalized_name
        
        # Try fuzzy matching
        matches = difflib.get_close_matches(normalized_name, candidates, n=1, cutoff=0.8)
        
        if matches:
            return matches[0]
        
        return None
    
    def match_across_sources(self):
        """
        Match drivers across different data sources
        """
        logger.info("Matching drivers across data sources")
        
        # Reset mapping statistics
        self.mapping_stats['matched_driving_history'] = 0
        self.mapping_stats['matched_activity_detail'] = 0
        self.mapping_stats['unmatched_driving_history'] = 0
        self.mapping_stats['unmatched_activity_detail'] = 0
        
        # Create a master list of all normalized names
        asset_list_names = set(self.asset_list_drivers.keys())
        driving_history_names = set(self.driving_history_drivers.keys())
        activity_detail_names = set(self.activity_detail_drivers.keys())
        
        # Match Driving History drivers to Asset List
        for dh_name in driving_history_names:
            # Try to find a match in Asset List
            asset_list_match = self.find_best_match(dh_name, asset_list_names)
            
            if asset_list_match:
                # Match found
                self.mapping_stats['matched_driving_history'] += 1
                
                # Add match information to both records
                self.driving_history_drivers[dh_name]['asset_list_match'] = asset_list_match
                
                if 'driving_history_matches' not in self.asset_list_drivers[asset_list_match]:
                    self.asset_list_drivers[asset_list_match]['driving_history_matches'] = []
                
                self.asset_list_drivers[asset_list_match]['driving_history_matches'].append(dh_name)
            else:
                # No match found
                self.mapping_stats['unmatched_driving_history'] += 1
                self.driving_history_drivers[dh_name]['asset_list_match'] = None
        
        # Match Activity Detail drivers to Asset List
        for ad_name in activity_detail_names:
            # Try to find a match in Asset List
            asset_list_match = self.find_best_match(ad_name, asset_list_names)
            
            if asset_list_match:
                # Match found
                self.mapping_stats['matched_activity_detail'] += 1
                
                # Add match information to both records
                self.activity_detail_drivers[ad_name]['asset_list_match'] = asset_list_match
                
                if 'activity_detail_matches' not in self.asset_list_drivers[asset_list_match]:
                    self.asset_list_drivers[asset_list_match]['activity_detail_matches'] = []
                
                self.asset_list_drivers[asset_list_match]['activity_detail_matches'].append(ad_name)
            else:
                # No match found
                self.mapping_stats['unmatched_activity_detail'] += 1
                self.activity_detail_drivers[ad_name]['asset_list_match'] = None
        
        logger.info("Matching results:")
        logger.info(f"  Driving History: {self.mapping_stats['matched_driving_history']} matched, {self.mapping_stats['unmatched_driving_history']} unmatched")
        logger.info(f"  Activity Detail: {self.mapping_stats['matched_activity_detail']} matched, {self.mapping_stats['unmatched_activity_detail']} unmatched")
        
        return True
    
    def create_unified_dataset(self):
        """
        Create a unified driver identity dataset
        """
        logger.info("Creating unified driver identity dataset")
        
        # Reset identity dataset
        self.identity_dataset = {}
        
        # Add all drivers from Asset List (primary source of truth)
        for normalized_name, driver in self.asset_list_drivers.items():
            self.identity_dataset[normalized_name] = {
                'name': driver['name'],
                'normalized_name': normalized_name,
                'assets': driver['assets'],
                'job_sites': list(driver['job_sites']) if 'job_sites' in driver else [],
                'sources': ['Asset List'],
                'in_driving_history': False,
                'in_activity_detail': False,
                'source_mappings': {}
            }
        
        # Add/update with Driving History data
        for normalized_name, driver in self.driving_history_drivers.items():
            asset_list_match = driver.get('asset_list_match')
            
            if asset_list_match:
                # Update existing record
                self.identity_dataset[asset_list_match]['in_driving_history'] = True
                
                # Add source mapping
                self.identity_dataset[asset_list_match]['source_mappings']['Driving History'] = {
                    'name': driver['name'],
                    'normalized_name': normalized_name,
                    'assets': driver['assets']
                }
                
                # Add to sources
                if 'Driving History' not in self.identity_dataset[asset_list_match]['sources']:
                    self.identity_dataset[asset_list_match]['sources'].append('Driving History')
            else:
                # New record (not in Asset List)
                self.identity_dataset[normalized_name] = {
                    'name': driver['name'],
                    'normalized_name': normalized_name,
                    'assets': driver['assets'],
                    'job_sites': [],
                    'sources': ['Driving History'],
                    'in_driving_history': True,
                    'in_activity_detail': False,
                    'source_mappings': {
                        'Driving History': {
                            'name': driver['name'],
                            'normalized_name': normalized_name,
                            'assets': driver['assets']
                        }
                    }
                }
        
        # Add/update with Activity Detail data
        for normalized_name, driver in self.activity_detail_drivers.items():
            asset_list_match = driver.get('asset_list_match')
            
            if asset_list_match:
                # Update existing record
                self.identity_dataset[asset_list_match]['in_activity_detail'] = True
                
                # Add source mapping
                self.identity_dataset[asset_list_match]['source_mappings']['Activity Detail'] = {
                    'name': driver['name'],
                    'normalized_name': normalized_name,
                    'assets': driver['assets']
                }
                
                # Add to sources
                if 'Activity Detail' not in self.identity_dataset[asset_list_match]['sources']:
                    self.identity_dataset[asset_list_match]['sources'].append('Activity Detail')
            elif normalized_name in self.identity_dataset:
                # Update existing record (from driving history)
                self.identity_dataset[normalized_name]['in_activity_detail'] = True
                
                # Add source mapping
                self.identity_dataset[normalized_name]['source_mappings']['Activity Detail'] = {
                    'name': driver['name'],
                    'normalized_name': normalized_name,
                    'assets': driver['assets']
                }
                
                # Add to sources
                if 'Activity Detail' not in self.identity_dataset[normalized_name]['sources']:
                    self.identity_dataset[normalized_name]['sources'].append('Activity Detail')
            else:
                # New record (not in Asset List or Driving History)
                self.identity_dataset[normalized_name] = {
                    'name': driver['name'],
                    'normalized_name': normalized_name,
                    'assets': driver['assets'],
                    'job_sites': [],
                    'sources': ['Activity Detail'],
                    'in_driving_history': False,
                    'in_activity_detail': True,
                    'source_mappings': {
                        'Activity Detail': {
                            'name': driver['name'],
                            'normalized_name': normalized_name,
                            'assets': driver['assets']
                        }
                    }
                }
        
        logger.info(f"Created unified dataset with {len(self.identity_dataset)} driver identities")
        
        return True
    
    def export_identity_dataset(self, date_str=None):
        """
        Export the unified driver identity dataset
        """
        if not date_str:
            # Default to today
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Exporting driver identity dataset for {date_str}")
        
        # Create file paths
        json_path = os.path.join(REPORTS_DIR, f"driver_identity_dataset_{date_str}.json")
        csv_path = os.path.join(REPORTS_DIR, f"driver_identity_dataset_{date_str}.csv")
        stats_path = os.path.join(REPORTS_DIR, f"driver_identity_stats_{date_str}.json")
        
        # Create directories if needed
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        try:
            # Export as JSON
            with open(json_path, 'w') as f:
                json.dump(self.identity_dataset, f, indent=2)
            
            # Export as CSV (simplified)
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Name', 'Normalized Name', 'Assets', 'Job Sites',
                    'In Asset List', 'In Driving History', 'In Activity Detail', 'Sources'
                ])
                
                # Write data
                for normalized_name, driver in self.identity_dataset.items():
                    writer.writerow([
                        driver['name'],
                        normalized_name,
                        ', '.join(driver['assets']),
                        ', '.join(driver['job_sites']),
                        'Asset List' in driver['sources'],
                        driver['in_driving_history'],
                        driver['in_activity_detail'],
                        ', '.join(driver['sources'])
                    ])
            
            # Export mapping statistics
            with open(stats_path, 'w') as f:
                stats = {
                    'date': date_str,
                    'asset_counts': self.asset_counts,
                    'mapping_stats': self.mapping_stats,
                    'summary': {
                        'total_unique_drivers': len(self.identity_dataset),
                        'in_asset_list_only': sum(1 for d in self.identity_dataset.values() if len(d['sources']) == 1 and 'Asset List' in d['sources']),
                        'in_driving_history_only': sum(1 for d in self.identity_dataset.values() if len(d['sources']) == 1 and 'Driving History' in d['sources']),
                        'in_activity_detail_only': sum(1 for d in self.identity_dataset.values() if len(d['sources']) == 1 and 'Activity Detail' in d['sources']),
                        'in_multiple_sources': sum(1 for d in self.identity_dataset.values() if len(d['sources']) > 1)
                    }
                }
                
                json.dump(stats, f, indent=2)
            
            # Copy to exports directory
            export_json_path = os.path.join(EXPORTS_DIR, f"driver_identity_dataset_{date_str}.json")
            export_csv_path = os.path.join(EXPORTS_DIR, f"driver_identity_dataset_{date_str}.csv")
            export_stats_path = os.path.join(EXPORTS_DIR, f"driver_identity_stats_{date_str}.json")
            
            os.makedirs(os.path.dirname(export_json_path), exist_ok=True)
            
            import shutil
            shutil.copy(json_path, export_json_path)
            shutil.copy(csv_path, export_csv_path)
            shutil.copy(stats_path, export_stats_path)
            
            logger.info(f"Exported driver identity dataset to {json_path}, {csv_path}, and {stats_path}")
            
            return {
                'json_path': json_path,
                'csv_path': csv_path,
                'stats_path': stats_path
            }
            
        except Exception as e:
            logger.error(f"Error exporting driver identity dataset: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def create_identity_mapping_table(self, date_str=None):
        """
        Create a lookup table for driver identity mapping
        """
        if not date_str:
            # Default to today
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Creating driver identity mapping table for {date_str}")
        
        # Create file paths
        json_path = os.path.join(REPORTS_DIR, f"driver_identity_mapping_{date_str}.json")
        csv_path = os.path.join(REPORTS_DIR, f"driver_identity_mapping_{date_str}.csv")
        
        # Create directories if needed
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        try:
            # Create mapping table
            mapping_table = {}
            
            # Extract all original names from all sources
            all_original_names = set()
            
            # Asset List
            for normalized_name, driver in self.asset_list_drivers.items():
                all_original_names.add(driver['name'])
            
            # Driving History
            for normalized_name, driver in self.driving_history_drivers.items():
                all_original_names.add(driver['name'])
            
            # Activity Detail
            for normalized_name, driver in self.activity_detail_drivers.items():
                all_original_names.add(driver['name'])
            
            # Create mappings for each original name
            for original_name in all_original_names:
                # Skip empty or invalid names
                if not original_name or original_name.lower() in ['nan', 'none', 'null', '']:
                    continue
                
                # Normalize the name
                normalized_name = self.normalize_name(original_name)
                
                if not normalized_name:
                    continue
                
                # Find the canonical record in identity dataset
                canonical_record = None
                
                if normalized_name in self.identity_dataset:
                    canonical_record = self.identity_dataset[normalized_name]
                else:
                    # Try to find a match
                    for dataset_name, driver in self.identity_dataset.items():
                        source_mappings = driver.get('source_mappings', {})
                        
                        for source, mapping in source_mappings.items():
                            if mapping.get('name') == original_name:
                                canonical_record = driver
                                break
                        
                        if canonical_record:
                            break
                
                if canonical_record:
                    # Create mapping entry
                    mapping_table[original_name] = {
                        'original_name': original_name,
                        'normalized_name': normalized_name,
                        'canonical_name': canonical_record['name'],
                        'canonical_normalized': canonical_record['normalized_name'],
                        'assets': canonical_record['assets'],
                        'sources': canonical_record['sources']
                    }
            
            # Export as JSON
            with open(json_path, 'w') as f:
                json.dump(mapping_table, f, indent=2)
            
            # Export as CSV
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Original Name', 'Normalized Name', 'Canonical Name', 'Canonical Normalized',
                    'Assets', 'Sources'
                ])
                
                # Write data
                for original_name, mapping in mapping_table.items():
                    writer.writerow([
                        original_name,
                        mapping['normalized_name'],
                        mapping['canonical_name'],
                        mapping['canonical_normalized'],
                        ', '.join(mapping['assets']),
                        ', '.join(mapping['sources'])
                    ])
            
            # Copy to exports directory
            export_json_path = os.path.join(EXPORTS_DIR, f"driver_identity_mapping_{date_str}.json")
            export_csv_path = os.path.join(EXPORTS_DIR, f"driver_identity_mapping_{date_str}.csv")
            
            os.makedirs(os.path.dirname(export_json_path), exist_ok=True)
            
            import shutil
            shutil.copy(json_path, export_json_path)
            shutil.copy(csv_path, export_csv_path)
            
            logger.info(f"Created driver identity mapping table with {len(mapping_table)} entries")
            logger.info(f"Exported mapping table to {json_path} and {csv_path}")
            
            return {
                'json_path': json_path,
                'csv_path': csv_path,
                'mapping_table': mapping_table
            }
            
        except Exception as e:
            logger.error(f"Error creating driver identity mapping table: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def run(self, date_str=None):
        """
        Run the complete driver identity mapping process
        """
        if not date_str:
            # Default to today
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Running driver identity mapping for {date_str}")
        
        # Step 1: Extract data from Asset List (primary source of truth)
        logger.info("1. Extracting data from Asset List")
        success = self.extract_asset_list()
        
        if not success:
            logger.error("Failed to extract data from Asset List")
            return False
        
        # Step 2: Extract data from Driving History for the specified date
        logger.info(f"2. Extracting data from Driving History for {date_str}")
        success = self.extract_driving_history(date_str)
        
        if not success:
            logger.warning("Failed to extract data from Driving History - proceeding without it")
        
        # Step 3: Extract data from Activity Detail for the specified date
        logger.info(f"3. Extracting data from Activity Detail for {date_str}")
        success = self.extract_activity_detail(date_str)
        
        if not success:
            logger.warning("Failed to extract data from Activity Detail - proceeding without it")
        
        # Step 4: Match drivers across sources
        logger.info("4. Matching drivers across sources")
        success = self.match_across_sources()
        
        if not success:
            logger.error("Failed to match drivers across sources")
            return False
        
        # Step 5: Create unified driver identity dataset
        logger.info("5. Creating unified driver identity dataset")
        success = self.create_unified_dataset()
        
        if not success:
            logger.error("Failed to create unified driver identity dataset")
            return False
        
        # Step 6: Export driver identity dataset
        logger.info("6. Exporting driver identity dataset")
        export_paths = self.export_identity_dataset(date_str)
        
        if not export_paths:
            logger.error("Failed to export driver identity dataset")
            return False
        
        # Step 7: Create identity mapping table
        logger.info("7. Creating identity mapping table")
        mapping_table = self.create_identity_mapping_table(date_str)
        
        if not mapping_table:
            logger.error("Failed to create identity mapping table")
            return False
        
        logger.info(f"Completed driver identity mapping for {date_str}")
        
        return {
            'date': date_str,
            'identity_dataset': export_paths,
            'mapping_table': mapping_table
        }


def process_date(date_str):
    """Process a specific date with driver identity mapping"""
    logger.info(f"Processing date: {date_str}")
    
    mapper = DriverIdentityMapper()
    result = mapper.run(date_str)
    
    return result


def main():
    """Main function"""
    logger.info("Starting Driver Identity Mapper")
    
    # Set target dates from command line if provided
    target_dates = []
    
    if len(sys.argv) > 1:
        target_dates = sys.argv[1:]
    else:
        # Default to today
        target_dates = [datetime.now().strftime('%Y-%m-%d')]
    
    results = {}
    
    for date_str in target_dates:
        logger.info(f"Processing {date_str}")
        result = process_date(date_str)
        
        if result:
            results[date_str] = result
    
    # Print summary
    print("\nDRIVER IDENTITY MAPPER SUMMARY")
    print("=" * 80)
    
    for date_str, result in results.items():
        print(f"\nDate: {date_str}")
        
        # Identity dataset paths
        if 'identity_dataset' in result:
            print("Identity Dataset:")
            for file_type, file_path in result['identity_dataset'].items():
                print(f"  {file_type}: {file_path}")
        
        # Mapping table paths
        if 'mapping_table' in result:
            print("Mapping Table:")
            for file_type, file_path in result['mapping_table'].items():
                if file_type != 'mapping_table':
                    print(f"  {file_type}: {file_path}")
    
    print("\nDriver Identity Mapper Complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())