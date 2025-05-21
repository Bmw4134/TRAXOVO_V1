#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Enhanced Driver Identity Mapper

This script implements enhanced fuzzy matching between driver names to correctly
map drivers across different data sources. It specifically addresses the format
differences between Asset List and Driving History records.
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
from fuzzywuzzy import fuzz, process

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs/identity_mapper', exist_ok=True)
mapper_log = logging.FileHandler('logs/identity_mapper/enhanced_mapper.log')
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

# Name matching threshold - adjust as needed
FUZZY_MATCH_THRESHOLD = 85  # Minimum score for a fuzzy match


class EnhancedDriverMapper:
    """
    Enhanced mapper with advanced fuzzy matching for driver identity resolution.
    """
    
    def __init__(self):
        """Initialize the enhanced driver mapper"""
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
        
        # Name mapping and matching
        self.original_to_normalized = {}  # Original names to normalized forms
        self.normalized_to_original = {}  # Normalized names to original forms
        self.asset_list_names = []  # All normalized names from Asset List
        self.driving_history_names = []  # All normalized names from Driving History
        
        # Match records
        self.match_records = []  # Records of each match with scores
        
        # Mapping statistics
        self.mapping_stats = {
            'total_asset_list': 0,
            'total_driving_history': 0,
            'total_activity_detail': 0,
            'matched_driving_history': 0,
            'matched_activity_detail': 0,
            'unmatched_driving_history': 0,
            'unmatched_activity_detail': 0,
            'fuzzy_matched': 0,
            'exact_matched': 0,
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
        
        # Store original to normalized mapping
        self.original_to_normalized[name_str] = normalized
        
        # Store normalized to original mapping
        if normalized not in self.normalized_to_original:
            self.normalized_to_original[normalized] = []
        if name_str not in self.normalized_to_original[normalized]:
            self.normalized_to_original[normalized].append(name_str)
        
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
                
                # Reset asset list names
                self.asset_list_names = []
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
                    
                    # Add to asset list names for matching
                    if normalized_name not in self.asset_list_names:
                        self.asset_list_names.append(normalized_name)
                    
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
                
                # Reset driving history drivers and names
                self.driving_history_drivers = {}
                self.driving_history_names = []
                
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
                    
                    # Add to driving history names for matching
                    if normalized_name not in self.driving_history_names:
                        self.driving_history_names.append(normalized_name)
                    
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
                logger.info(f"Unique driver names in Driving History: {len(self.driving_history_names)}")
                
                return True
            else:
                logger.error("Required columns not found in Driving History")
                return False
                
        except Exception as e:
            logger.error(f"Error extracting Driving History data: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def match_driver_names(self):
        """
        Match driver names between Asset List and Driving History using enhanced fuzzy matching
        """
        logger.info("Matching driver names with enhanced fuzzy matching")
        
        # Reset match records
        self.match_records = []
        
        # Reset match statistics
        self.mapping_stats['matched_driving_history'] = 0
        self.mapping_stats['unmatched_driving_history'] = 0
        self.mapping_stats['fuzzy_matched'] = 0
        self.mapping_stats['exact_matched'] = 0
        
        # Prep for displaying sample names from each source
        asset_list_samples = self.asset_list_names[:5] if len(self.asset_list_names) >= 5 else self.asset_list_names
        driving_history_samples = self.driving_history_names[:5] if len(self.driving_history_names) >= 5 else self.driving_history_names
        
        logger.info(f"Asset List name samples: {asset_list_samples}")
        logger.info(f"Driving History name samples: {driving_history_samples}")
        
        # Track all matches
        matches = {}
        
        # First try exact matches
        for dh_name in self.driving_history_names:
            if dh_name in self.asset_list_names:
                # Exact match
                matches[dh_name] = {
                    'asset_list_name': dh_name,
                    'score': 100,
                    'match_type': 'exact'
                }
                self.mapping_stats['exact_matched'] += 1
                
                # Record match
                self.match_records.append({
                    'driving_history_name': dh_name,
                    'driving_history_original': self.driving_history_drivers[dh_name]['name'],
                    'asset_list_name': dh_name,
                    'asset_list_original': self.asset_list_drivers[dh_name]['name'] if dh_name in self.asset_list_drivers else 'Unknown',
                    'score': 100,
                    'match_type': 'exact'
                })
        
        # Then try fuzzy matching for remaining unmatched names
        unmatched_names = [name for name in self.driving_history_names if name not in matches]
        
        for dh_name in unmatched_names:
            # Get fuzzy matches
            match_results = process.extractBests(
                dh_name, 
                self.asset_list_names, 
                scorer=fuzz.token_sort_ratio,
                score_cutoff=FUZZY_MATCH_THRESHOLD,
                limit=3
            )
            
            if match_results:
                # Get best match
                best_match = match_results[0]
                asset_list_name, score = best_match
                
                # Store match
                matches[dh_name] = {
                    'asset_list_name': asset_list_name,
                    'score': score,
                    'match_type': 'fuzzy'
                }
                self.mapping_stats['fuzzy_matched'] += 1
                
                # Record match
                self.match_records.append({
                    'driving_history_name': dh_name,
                    'driving_history_original': self.driving_history_drivers[dh_name]['name'],
                    'asset_list_name': asset_list_name,
                    'asset_list_original': self.asset_list_drivers[asset_list_name]['name'] if asset_list_name in self.asset_list_drivers else 'Unknown',
                    'score': score,
                    'match_type': 'fuzzy',
                    'alternatives': match_results[1:] if len(match_results) > 1 else []
                })
            else:
                # No match found
                self.match_records.append({
                    'driving_history_name': dh_name,
                    'driving_history_original': self.driving_history_drivers[dh_name]['name'],
                    'asset_list_name': None,
                    'asset_list_original': None,
                    'score': 0,
                    'match_type': 'none'
                })
        
        # Update match stats
        self.mapping_stats['matched_driving_history'] = len(matches)
        self.mapping_stats['unmatched_driving_history'] = len(self.driving_history_names) - len(matches)
        
        # Update driver records with matches
        for dh_name, match_info in matches.items():
            asset_list_name = match_info['asset_list_name']
            
            # Update driving history record
            self.driving_history_drivers[dh_name]['asset_list_match'] = asset_list_name
            self.driving_history_drivers[dh_name]['match_score'] = match_info['score']
            self.driving_history_drivers[dh_name]['match_type'] = match_info['match_type']
            
            # Update asset list record
            if asset_list_name in self.asset_list_drivers:
                if 'driving_history_matches' not in self.asset_list_drivers[asset_list_name]:
                    self.asset_list_drivers[asset_list_name]['driving_history_matches'] = []
                
                self.asset_list_drivers[asset_list_name]['driving_history_matches'].append({
                    'name': dh_name,
                    'score': match_info['score'],
                    'match_type': match_info['match_type']
                })
        
        # Update unmatched driver records
        for dh_name in unmatched_names:
            if dh_name not in matches:
                self.driving_history_drivers[dh_name]['asset_list_match'] = None
                self.driving_history_drivers[dh_name]['match_score'] = 0
                self.driving_history_drivers[dh_name]['match_type'] = 'none'
        
        logger.info(f"Matching results:")
        logger.info(f"  Total Driving History drivers: {len(self.driving_history_names)}")
        logger.info(f"  Matched: {self.mapping_stats['matched_driving_history']} (Exact: {self.mapping_stats['exact_matched']}, Fuzzy: {self.mapping_stats['fuzzy_matched']})")
        logger.info(f"  Unmatched: {self.mapping_stats['unmatched_driving_history']}")
        
        return matches
    
    def create_unified_dataset(self):
        """
        Create a unified driver identity dataset with match information
        """
        logger.info("Creating unified driver identity dataset")
        
        # Reset identity dataset
        self.identity_dataset = {}
        
        # Start with all drivers from Asset List
        for normalized_name, driver in self.asset_list_drivers.items():
            self.identity_dataset[normalized_name] = {
                'name': driver['name'],
                'normalized_name': normalized_name,
                'assets': driver['assets'],
                'job_sites': list(driver['job_sites']) if 'job_sites' in driver else [],
                'sources': ['Asset List'],
                'in_driving_history': False,
                'driving_history_match': None,
                'match_score': 0,
                'match_type': 'none'
            }
        
        # Add/update with Driving History data and match information
        for normalized_name, driver in self.driving_history_drivers.items():
            asset_list_match = driver.get('asset_list_match')
            
            if asset_list_match:
                # Update existing record
                if asset_list_match in self.identity_dataset:
                    self.identity_dataset[asset_list_match]['in_driving_history'] = True
                    self.identity_dataset[asset_list_match]['driving_history_match'] = {
                        'name': driver['name'],
                        'normalized_name': normalized_name,
                        'assets': driver['assets'],
                        'score': driver.get('match_score', 0),
                        'match_type': driver.get('match_type', 'unknown')
                    }
                    self.identity_dataset[asset_list_match]['match_score'] = driver.get('match_score', 0)
                    self.identity_dataset[asset_list_match]['match_type'] = driver.get('match_type', 'unknown')
                    
                    # Add to sources
                    if 'Driving History' not in self.identity_dataset[asset_list_match]['sources']:
                        self.identity_dataset[asset_list_match]['sources'].append('Driving History')
            else:
                # Add as new record
                self.identity_dataset[normalized_name] = {
                    'name': driver['name'],
                    'normalized_name': normalized_name,
                    'assets': driver['assets'],
                    'job_sites': [],
                    'sources': ['Driving History'],
                    'in_driving_history': True,
                    'driving_history_match': None,
                    'match_score': 0,
                    'match_type': 'none'
                }
        
        logger.info(f"Created unified dataset with {len(self.identity_dataset)} driver identities")
        
        return True
    
    def generate_match_report(self, date_str=None):
        """
        Generate a detailed match report with all driver matches
        """
        if not date_str:
            # Default to today
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Generating match report for {date_str}")
        
        # Create file paths
        match_report_path = os.path.join(REPORTS_DIR, f"driver_match_report_{date_str}.json")
        match_csv_path = os.path.join(REPORTS_DIR, f"driver_match_report_{date_str}.csv")
        
        # Create directories if needed
        os.makedirs(os.path.dirname(match_report_path), exist_ok=True)
        
        try:
            # Export as JSON
            match_report = {
                'date': date_str,
                'matches': self.match_records,
                'stats': {
                    'total_driving_history': len(self.driving_history_names),
                    'total_asset_list': len(self.asset_list_names),
                    'matched': self.mapping_stats['matched_driving_history'],
                    'exact_matched': self.mapping_stats['exact_matched'],
                    'fuzzy_matched': self.mapping_stats['fuzzy_matched'],
                    'unmatched': self.mapping_stats['unmatched_driving_history'],
                    'match_threshold': FUZZY_MATCH_THRESHOLD
                }
            }
            
            with open(match_report_path, 'w') as f:
                json.dump(match_report, f, indent=2)
            
            # Export as CSV
            with open(match_csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Driving History Name', 'Original DH Name', 
                    'Asset List Name', 'Original AL Name',
                    'Match Score', 'Match Type'
                ])
                
                # Write data
                for match in self.match_records:
                    writer.writerow([
                        match['driving_history_name'],
                        match['driving_history_original'],
                        match['asset_list_name'] or 'NO MATCH',
                        match['asset_list_original'] or 'N/A',
                        match['score'],
                        match['match_type']
                    ])
            
            # Copy to exports directory
            export_match_report_path = os.path.join(EXPORTS_DIR, f"driver_match_report_{date_str}.json")
            export_match_csv_path = os.path.join(EXPORTS_DIR, f"driver_match_report_{date_str}.csv")
            
            os.makedirs(os.path.dirname(export_match_report_path), exist_ok=True)
            
            import shutil
            shutil.copy(match_report_path, export_match_report_path)
            shutil.copy(match_csv_path, export_match_csv_path)
            
            logger.info(f"Generated match report at {match_report_path} and {match_csv_path}")
            
            return {
                'json_path': match_report_path,
                'csv_path': match_csv_path
            }
            
        except Exception as e:
            logger.error(f"Error generating match report: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def export_dataset(self, date_str=None):
        """
        Export the unified identity dataset with match information
        """
        if not date_str:
            # Default to today
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Exporting enhanced identity dataset for {date_str}")
        
        # Create file paths
        json_path = os.path.join(REPORTS_DIR, f"enhanced_identity_dataset_{date_str}.json")
        csv_path = os.path.join(REPORTS_DIR, f"enhanced_identity_dataset_{date_str}.csv")
        stats_path = os.path.join(REPORTS_DIR, f"enhanced_identity_stats_{date_str}.json")
        
        # Create directories if needed
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        try:
            # Export as JSON
            with open(json_path, 'w') as f:
                json.dump(self.identity_dataset, f, indent=2)
            
            # Export as CSV
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Name', 'Normalized Name', 'Assets', 'Job Sites',
                    'In Driving History', 'Match Type', 'Match Score',
                    'DH Match Name', 'DH Match Assets', 'Sources'
                ])
                
                # Write data
                for normalized_name, driver in self.identity_dataset.items():
                    # Extract Driving History match info
                    dh_match = driver.get('driving_history_match')
                    dh_match_name = dh_match['name'] if dh_match else 'N/A'
                    dh_match_assets = ', '.join(dh_match['assets']) if dh_match and 'assets' in dh_match else 'N/A'
                    
                    writer.writerow([
                        driver['name'],
                        normalized_name,
                        ', '.join(driver['assets']),
                        ', '.join(driver['job_sites']),
                        driver['in_driving_history'],
                        driver['match_type'],
                        driver['match_score'],
                        dh_match_name,
                        dh_match_assets,
                        ', '.join(driver['sources'])
                    ])
            
            # Export mapping statistics
            stats = {
                'date': date_str,
                'match_threshold': FUZZY_MATCH_THRESHOLD,
                'asset_counts': self.asset_counts,
                'mapping_stats': self.mapping_stats,
                'summary': {
                    'total_unique_drivers': len(self.identity_dataset),
                    'in_asset_list': len(self.asset_list_drivers),
                    'in_driving_history': len(self.driving_history_drivers),
                    'matched_drivers': self.mapping_stats['matched_driving_history'],
                    'fuzzy_matched': self.mapping_stats['fuzzy_matched'],
                    'exact_matched': self.mapping_stats['exact_matched'],
                    'unmatched': self.mapping_stats['unmatched_driving_history']
                }
            }
            
            with open(stats_path, 'w') as f:
                json.dump(stats, f, indent=2)
            
            # Copy to exports directory
            export_json_path = os.path.join(EXPORTS_DIR, f"enhanced_identity_dataset_{date_str}.json")
            export_csv_path = os.path.join(EXPORTS_DIR, f"enhanced_identity_dataset_{date_str}.csv")
            export_stats_path = os.path.join(EXPORTS_DIR, f"enhanced_identity_stats_{date_str}.json")
            
            os.makedirs(os.path.dirname(export_json_path), exist_ok=True)
            
            import shutil
            shutil.copy(json_path, export_json_path)
            shutil.copy(csv_path, export_csv_path)
            shutil.copy(stats_path, export_stats_path)
            
            logger.info(f"Exported enhanced identity dataset to {json_path}, {csv_path}, and {stats_path}")
            
            return {
                'json_path': json_path,
                'csv_path': csv_path,
                'stats_path': stats_path
            }
            
        except Exception as e:
            logger.error(f"Error exporting enhanced identity dataset: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def run(self, date_str=None):
        """
        Run the enhanced driver identity mapping process
        """
        if not date_str:
            # Default to today
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Running enhanced driver identity mapping for {date_str}")
        
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
            logger.error("Failed to extract data from Driving History")
            return False
        
        # Step 3: Match driver names with enhanced fuzzy matching
        logger.info("3. Matching driver names with enhanced fuzzy matching")
        matches = self.match_driver_names()
        
        if not matches:
            logger.warning("No matches found between Asset List and Driving History")
        
        # Step 4: Create unified driver identity dataset
        logger.info("4. Creating unified driver identity dataset")
        success = self.create_unified_dataset()
        
        if not success:
            logger.error("Failed to create unified driver identity dataset")
            return False
        
        # Step 5: Generate match report
        logger.info("5. Generating match report")
        match_report = self.generate_match_report(date_str)
        
        if not match_report:
            logger.error("Failed to generate match report")
            return False
        
        # Step 6: Export the unified identity dataset
        logger.info("6. Exporting enhanced identity dataset")
        export_paths = self.export_dataset(date_str)
        
        if not export_paths:
            logger.error("Failed to export enhanced identity dataset")
            return False
        
        logger.info(f"Completed enhanced driver identity mapping for {date_str}")
        
        return {
            'date': date_str,
            'match_report': match_report,
            'identity_dataset': export_paths,
            'matches': matches
        }


def install_fuzzywuzzy():
    """
    Ensure the required fuzzy matching libraries are installed
    """
    try:
        import fuzzywuzzy
        logger.info("FuzzyWuzzy is already installed")
        return True
    except ImportError:
        logger.info("Installing FuzzyWuzzy library")
        try:
            import pip
            pip.main(['install', 'fuzzywuzzy', 'python-Levenshtein'])
            logger.info("FuzzyWuzzy installed successfully")
            return True
        except Exception as e:
            logger.error(f"Error installing FuzzyWuzzy: {e}")
            logger.error(traceback.format_exc())
            return False


def process_date(date_str):
    """Process a specific date with enhanced driver identity mapping"""
    logger.info(f"Processing date: {date_str}")
    
    # Ensure required libraries are installed
    if not install_fuzzywuzzy():
        logger.error("Failed to install required libraries")
        print("Unable to install required libraries. Please run:")
        print("pip install fuzzywuzzy python-Levenshtein")
        return None
    
    # Run the enhanced driver mapper
    mapper = EnhancedDriverMapper()
    result = mapper.run(date_str)
    
    return result


def main():
    """Main function"""
    logger.info("Starting Enhanced Driver Identity Mapper")
    
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
    print("\nENHANCED DRIVER IDENTITY MAPPER SUMMARY")
    print("=" * 80)
    
    for date_str, result in results.items():
        print(f"\nDate: {date_str}")
        
        # Match report
        if 'match_report' in result:
            print("Match Report:")
            for file_type, file_path in result['match_report'].items():
                print(f"  {file_type}: {file_path}")
        
        # Identity dataset
        if 'identity_dataset' in result:
            print("Identity Dataset:")
            for file_type, file_path in result['identity_dataset'].items():
                print(f"  {file_type}: {file_path}")
        
        # Match statistics
        if 'matches' in result:
            matched_count = len(result['matches'])
            print(f"Matched Drivers: {matched_count}")
    
    print("\nEnhanced Driver Identity Mapper Complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())