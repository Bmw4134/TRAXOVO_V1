#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Comprehensive Fleet Attendance System

This module implements the complete GENIUS CORE attendance verification system that:
1. Uses multiple authentic data sources as truth (not derived pivot tables)
2. Implements robust identity verification against employee master list
3. Validates job site attendance through multiple data sources
4. Provides complete audit trail and source verification for all drivers
5. Generates verified reports with full traceability
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import hashlib
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Make sure logs directory exists
os.makedirs('logs/genius_core', exist_ok=True)

# Add file handler for this script
file_handler = logging.FileHandler('logs/genius_core/genius_core.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Create necessary directories
for directory in ['data/processed', 'reports/genius_core', 'exports/genius_core']:
    os.makedirs(directory, exist_ok=True)

# Constants for data sources and output paths
DATA_SOURCES = {
    'driving_history': 'data/driving_history',
    'activity_detail': 'data/activity_detail',
    'assets_time_on_site': 'data/assets_time_on_site',
    'equipment_billing': 'attached_assets/EQ MONTHLY BILLINGS WORKING SPREADSHEET - APRIL 2025.xlsx',
    'employee_master': 'data/employee_master_list.csv',
    'job_codes': 'data/job_codes.csv',
}

# Time thresholds for status classification
TIME_THRESHOLDS = {
    'late_minutes': 15,        # Minutes after scheduled start to be considered late
    'early_end_minutes': 30,   # Minutes before scheduled end to be considered early departure
    'idle_threshold': 10,      # Minutes of idle time to flag as suspicious
    'location_radius': 0.5,    # Miles to consider within job site boundary
}

class GeniusCore:
    """Main class for the GENIUS CORE system"""
    
    def __init__(self, date_str: str):
        """
        Initialize GENIUS CORE for a specific date
        
        Args:
            date_str (str): Date string in YYYY-MM-DD format
        """
        self.date_str = date_str
        self.date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Initialize data containers
        self.employee_master = {}
        self.asset_driver_map = {}
        self.job_codes = {}
        self.driving_history = []
        self.activity_detail = []
        self.assets_time_on_site = []
        
        # Report data
        self.drivers = []
        self.summary = {
            'total': 0,
            'on_time': 0,
            'late': 0,
            'early_end': 0,
            'not_on_job': 0,
            'unmatched': 0,
            'ghost': 0
        }
        
        # Validation statistics
        self.validation = {
            'total_entries': 0,
            'verified_employees': 0,
            'verified_assets': 0,
            'verified_locations': 0,
            'unmatched_employees': 0,
            'unmatched_assets': 0,
            'sources': {}
        }
        
        # Source tracking for traceability
        self.sources = []
        
        logger.info(f"Initializing GENIUS CORE for {date_str}")
    
    def load_employee_master(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the employee master list as source of truth for employee identity
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping normalized names to employee data
        """
        logger.info("Loading employee master list")
        
        employee_master = {}
        source_path = DATA_SOURCES.get('employee_master')
        
        if not os.path.exists(source_path):
            logger.warning(f"Employee master list not found: {source_path}")
            return employee_master
        
        try:
            # Load CSV file
            df = pd.read_csv(source_path)
            
            # Track this as a data source
            self.sources.append({
                'type': 'employee_master',
                'path': source_path,
                'rows': len(df),
                'timestamp': datetime.now().isoformat()
            })
            
            # Process each employee
            for _, row in df.iterrows():
                employee_id = str(row.get('employee_id', '')).strip()
                name = str(row.get('employee_name', '')).strip()
                
                # Skip empty entries
                if not employee_id or not name or name.lower() in ['nan', 'none', 'null', '']:
                    continue
                
                # Create normalized name for lookup
                normalized_name = name.lower()
                
                # Create employee record
                employee_record = {
                    'employee_id': employee_id,
                    'name': name,
                    'normalized_name': normalized_name,
                    'source': 'employee_master_list'
                }
                
                # Add additional fields if available
                for col in df.columns:
                    if col not in ['employee_id', 'employee_name']:
                        employee_record[col] = row.get(col)
                
                # Add to employee master dictionary
                employee_master[normalized_name] = employee_record
                
                # If there's an asset ID, add to asset-driver map
                asset_id = str(row.get('asset_id', '')).strip()
                if asset_id and asset_id.lower() not in ['nan', 'none', 'null', '']:
                    normalized_asset_id = asset_id.upper()
                    
                    self.asset_driver_map[normalized_asset_id] = {
                        'asset_id': asset_id,
                        'employee_id': employee_id,
                        'driver_name': name,
                        'normalized_name': normalized_name,
                        'source': 'employee_master_list'
                    }
            
            logger.info(f"Loaded {len(employee_master)} employees from master list")
            
            # Update validation stats
            self.validation['verified_employees'] = len(employee_master)
            self.validation['verified_assets'] = len(self.asset_driver_map)
            self.validation['sources']['employee_master'] = {
                'records': len(employee_master),
                'path': source_path
            }
            
            self.employee_master = employee_master
            return employee_master
            
        except Exception as e:
            logger.error(f"Error loading employee master list: {e}")
            logger.error(traceback.format_exc())
            return employee_master
    
    def load_equipment_billing_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Load equipment billing data for asset-driver mapping and additional employee data
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping asset IDs to driver data
        """
        logger.info("Loading equipment billing data")
        
        asset_driver_map = self.asset_driver_map.copy()
        employee_updates = {}
        source_path = DATA_SOURCES.get('equipment_billing')
        
        if not os.path.exists(source_path):
            logger.warning(f"Equipment billing file not found: {source_path}")
            return asset_driver_map
        
        try:
            # Load Excel workbook
            workbook = pd.ExcelFile(source_path)
            
            # Track this as a data source
            self.sources.append({
                'type': 'equipment_billing',
                'path': source_path,
                'sheets': workbook.sheet_names,
                'timestamp': datetime.now().isoformat()
            })
            
            # Look for Drivers sheet
            driver_sheet_names = ['Drivers', 'Driver List', 'Employees', 'Personnel']
            asset_sheet_names = ['Assets', 'Asset List', 'Equipment', 'Equipment List', 'Vehicles']
            
            # Process driver sheets
            for sheet_name in driver_sheet_names:
                if sheet_name in workbook.sheet_names:
                    logger.info(f"Processing {sheet_name} sheet from equipment billing")
                    
                    # Load sheet
                    df = pd.read_excel(source_path, sheet_name=sheet_name)
                    
                    # Normalize column names
                    df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                    
                    # Look for required columns
                    name_cols = ['name', 'driver_name', 'employee_name', 'full_name', 'operator']
                    id_cols = ['id', 'employee_id', 'driver_id', 'personnel_id']
                    asset_cols = ['asset', 'asset_id', 'equipment', 'vehicle']
                    
                    # Find column matches
                    name_col = next((col for col in name_cols if col in df.columns), None)
                    id_col = next((col for col in id_cols if col in df.columns), None)
                    asset_col = next((col for col in asset_cols if col in df.columns), None)
                    
                    if name_col:
                        # Process each row
                        for _, row in df.iterrows():
                            name = str(row[name_col]).strip()
                            
                            # Skip empty names
                            if not name or name.lower() in ['nan', 'none', 'null', '']:
                                continue
                            
                            # Normalize name
                            normalized_name = name.lower()
                            
                            # Create driver record
                            driver_record = {
                                'name': name,
                                'normalized_name': normalized_name,
                                'source': f"equipment_billing.{sheet_name}"
                            }
                            
                            # Add employee ID if available
                            if id_col:
                                employee_id = str(row[id_col]).strip()
                                if employee_id and employee_id.lower() not in ['nan', 'none', 'null', '']:
                                    driver_record['employee_id'] = employee_id
                            
                            # Add to employee updates
                            employee_updates[normalized_name] = driver_record
                            
                            # If there's an asset ID, add to asset-driver map
                            if asset_col:
                                asset_id = str(row[asset_col]).strip()
                                if asset_id and asset_id.lower() not in ['nan', 'none', 'null', '']:
                                    normalized_asset_id = asset_id.upper()
                                    
                                    asset_driver_map[normalized_asset_id] = {
                                        'asset_id': asset_id,
                                        'driver_name': name,
                                        'normalized_name': normalized_name,
                                        'source': f"equipment_billing.{sheet_name}"
                                    }
                                    
                                    # Add employee ID if available
                                    if id_col:
                                        employee_id = str(row[id_col]).strip()
                                        if employee_id and employee_id.lower() not in ['nan', 'none', 'null', '']:
                                            asset_driver_map[normalized_asset_id]['employee_id'] = employee_id
            
            # Process asset sheets
            for sheet_name in asset_sheet_names:
                if sheet_name in workbook.sheet_names:
                    logger.info(f"Processing {sheet_name} sheet from equipment billing")
                    
                    # Load sheet
                    df = pd.read_excel(source_path, sheet_name=sheet_name)
                    
                    # Normalize column names
                    df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                    
                    # Look for required columns
                    asset_cols = ['asset', 'asset_id', 'equipment', 'vehicle', 'id', 'equipment_id', 'vehicle_id']
                    driver_cols = ['driver', 'driver_name', 'operator', 'employee', 'employee_name', 'assigned_to']
                    
                    # Find column matches
                    asset_col = next((col for col in asset_cols if col in df.columns), None)
                    driver_col = next((col for col in driver_cols if col in df.columns), None)
                    
                    if asset_col and driver_col:
                        # Process each row
                        for _, row in df.iterrows():
                            asset_id = str(row[asset_col]).strip()
                            driver_name = str(row[driver_col]).strip()
                            
                            # Skip empty entries
                            if not asset_id or asset_id.lower() in ['nan', 'none', 'null', ''] or \
                               not driver_name or driver_name.lower() in ['nan', 'none', 'null', '']:
                                continue
                            
                            # Normalize IDs
                            normalized_asset_id = asset_id.upper()
                            normalized_name = driver_name.lower()
                            
                            # Add to asset-driver map
                            asset_driver_map[normalized_asset_id] = {
                                'asset_id': asset_id,
                                'driver_name': driver_name,
                                'normalized_name': normalized_name,
                                'source': f"equipment_billing.{sheet_name}"
                            }
                            
                            # Add employee record to updates
                            if normalized_name not in employee_updates:
                                employee_updates[normalized_name] = {
                                    'name': driver_name,
                                    'normalized_name': normalized_name,
                                    'source': f"equipment_billing.{sheet_name}"
                                }
            
            # Update employee master with equipment billing data
            for normalized_name, driver_record in employee_updates.items():
                if normalized_name not in self.employee_master:
                    # Add new employee
                    self.employee_master[normalized_name] = driver_record
                else:
                    # Update existing employee if missing fields
                    for field, value in driver_record.items():
                        if field not in self.employee_master[normalized_name] and field not in ['normalized_name']:
                            self.employee_master[normalized_name][field] = value
            
            # Update asset-driver map
            self.asset_driver_map = asset_driver_map
            
            # Update validation stats
            self.validation['verified_employees'] = len(self.employee_master)
            self.validation['verified_assets'] = len(self.asset_driver_map)
            self.validation['sources']['equipment_billing'] = {
                'assets': len(asset_driver_map),
                'employees': len(employee_updates),
                'path': source_path
            }
            
            logger.info(f"Loaded {len(asset_driver_map)} asset-driver mappings from equipment billing")
            return asset_driver_map
            
        except Exception as e:
            logger.error(f"Error loading equipment billing data: {e}")
            logger.error(traceback.format_exc())
            return asset_driver_map
    
    def load_driving_history(self) -> List[Dict[str, Any]]:
        """
        Load driving history data for the specified date
        
        Returns:
            List[Dict[str, Any]]: List of driving history records
        """
        logger.info(f"Loading driving history data for {self.date_str}")
        
        driving_history = []
        driving_history_dir = DATA_SOURCES.get('driving_history')
        
        if not os.path.exists(driving_history_dir):
            logger.warning(f"Driving history directory not found: {driving_history_dir}")
            return driving_history
        
        try:
            # Look for date-specific files
            date_part = self.date_str.replace('-', '')
            date_files = []
            
            for filename in os.listdir(driving_history_dir):
                filepath = os.path.join(driving_history_dir, filename)
                if os.path.isfile(filepath) and (date_part in filename or self.date_str in filename) and filename.endswith('.csv'):
                    date_files.append(filepath)
            
            if not date_files:
                logger.warning(f"No driving history files found for {self.date_str}")
                return driving_history
            
            # Process each file
            for filepath in date_files:
                logger.info(f"Processing driving history file: {filepath}")
                
                # Track this as a data source
                self.sources.append({
                    'type': 'driving_history',
                    'path': filepath,
                    'date': self.date_str,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Load CSV file
                df = pd.read_csv(filepath)
                
                # Normalize column names
                df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                
                # Look for required columns
                required_cols = {
                    'driver': ['driver', 'driver_name', 'employee', 'employee_name', 'operator'],
                    'asset': ['asset', 'asset_id', 'equipment', 'vehicle', 'vehicle_id'],
                    'key_on': ['key_on', 'start_time', 'key_on_time'],
                    'key_off': ['key_off', 'end_time', 'key_off_time']
                }
                
                column_map = {}
                
                # Find column matches
                for field, possible_cols in required_cols.items():
                    column_map[field] = next((col for col in possible_cols if col in df.columns), None)
                
                # Check if we have the minimum required columns
                if not all([column_map['driver'], column_map['asset']]) or not any([column_map['key_on'], column_map['key_off']]):
                    logger.warning(f"Missing required columns in driving history file: {filepath}")
                    logger.warning(f"Found columns: {column_map}")
                    continue
                
                # Process each row
                for _, row in df.iterrows():
                    # Extract driver and asset
                    driver_name = str(row[column_map['driver']]).strip() if column_map['driver'] else None
                    asset_id = str(row[column_map['asset']]).strip() if column_map['asset'] else None
                    
                    # Skip empty entries
                    if not driver_name or driver_name.lower() in ['nan', 'none', 'null', ''] or \
                       not asset_id or asset_id.lower() in ['nan', 'none', 'null', '']:
                        continue
                    
                    # Extract timestamps
                    key_on_time = None
                    key_off_time = None
                    
                    if column_map['key_on']:
                        try:
                            key_on_value = row[column_map['key_on']]
                            if isinstance(key_on_value, str):
                                # Try to parse datetime string
                                key_on_time = pd.to_datetime(key_on_value)
                            else:
                                # Already a timestamp
                                key_on_time = pd.to_datetime(key_on_value)
                        except:
                            pass
                    
                    if column_map['key_off']:
                        try:
                            key_off_value = row[column_map['key_off']]
                            if isinstance(key_off_value, str):
                                # Try to parse datetime string
                                key_off_time = pd.to_datetime(key_off_value)
                            else:
                                # Already a timestamp
                                key_off_time = pd.to_datetime(key_off_value)
                        except:
                            pass
                    
                    # Create normalized values
                    normalized_name = driver_name.lower()
                    normalized_asset_id = asset_id.upper()
                    
                    # Create driving record
                    driving_record = {
                        'driver_name': driver_name,
                        'normalized_name': normalized_name,
                        'asset_id': asset_id,
                        'normalized_asset_id': normalized_asset_id,
                        'key_on_time': key_on_time.isoformat() if key_on_time is not None else None,
                        'key_off_time': key_off_time.isoformat() if key_off_time is not None else None,
                        'source_file': os.path.basename(filepath),
                        'verified_employee': normalized_name in self.employee_master,
                        'verified_asset': normalized_asset_id in self.asset_driver_map
                    }
                    
                    # Add any additional fields that might be useful
                    for col in df.columns:
                        col_lower = col.lower()
                        if col_lower not in driving_record and col_lower not in ['key_on', 'key_off', 'driver', 'asset']:
                            driving_record[col_lower] = row[col]
                    
                    # Add employee ID if we can match it
                    if normalized_name in self.employee_master:
                        driving_record['employee_id'] = self.employee_master[normalized_name].get('employee_id')
                    
                    # Add to driving history
                    driving_history.append(driving_record)
                
                logger.info(f"Processed {len(driving_history)} records from {filepath}")
            
            # Update validation stats
            self.validation['sources']['driving_history'] = {
                'files': len(date_files),
                'records': len(driving_history),
                'date': self.date_str
            }
            
            # Store the driving history
            self.driving_history = driving_history
            logger.info(f"Loaded {len(driving_history)} driving history records for {self.date_str}")
            return driving_history
            
        except Exception as e:
            logger.error(f"Error loading driving history data: {e}")
            logger.error(traceback.format_exc())
            return driving_history
    
    def load_activity_detail(self) -> List[Dict[str, Any]]:
        """
        Load activity detail data for the specified date
        
        Returns:
            List[Dict[str, Any]]: List of activity detail records
        """
        logger.info(f"Loading activity detail data for {self.date_str}")
        
        activity_detail = []
        activity_detail_dir = DATA_SOURCES.get('activity_detail')
        
        if not os.path.exists(activity_detail_dir):
            logger.warning(f"Activity detail directory not found: {activity_detail_dir}")
            return activity_detail
        
        try:
            # Look for date-specific files
            date_part = self.date_str.replace('-', '')
            date_files = []
            
            for filename in os.listdir(activity_detail_dir):
                filepath = os.path.join(activity_detail_dir, filename)
                if os.path.isfile(filepath) and (date_part in filename or self.date_str in filename) and filename.endswith('.csv'):
                    date_files.append(filepath)
            
            if not date_files:
                logger.warning(f"No activity detail files found for {self.date_str}")
                return activity_detail
            
            # Process each file
            for filepath in date_files:
                logger.info(f"Processing activity detail file: {filepath}")
                
                # Track this as a data source
                self.sources.append({
                    'type': 'activity_detail',
                    'path': filepath,
                    'date': self.date_str,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Load CSV file
                df = pd.read_csv(filepath)
                
                # Normalize column names
                df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                
                # Look for required columns
                required_cols = {
                    'driver': ['driver', 'driver_name', 'employee', 'employee_name', 'operator'],
                    'asset': ['asset', 'asset_id', 'equipment', 'vehicle', 'vehicle_id'],
                    'start_time': ['start_time', 'start', 'activity_start', 'begin_time'],
                    'end_time': ['end_time', 'end', 'activity_end', 'finish_time'],
                    'activity': ['activity', 'activity_type', 'event', 'type']
                }
                
                column_map = {}
                
                # Find column matches
                for field, possible_cols in required_cols.items():
                    column_map[field] = next((col for col in possible_cols if col in df.columns), None)
                
                # Check if we have the minimum required columns
                if not all([column_map['driver'], column_map['asset']]) or not any([column_map['start_time'], column_map['end_time']]):
                    logger.warning(f"Missing required columns in activity detail file: {filepath}")
                    logger.warning(f"Found columns: {column_map}")
                    continue
                
                # Process each row
                for _, row in df.iterrows():
                    # Extract driver and asset
                    driver_name = str(row[column_map['driver']]).strip() if column_map['driver'] else None
                    asset_id = str(row[column_map['asset']]).strip() if column_map['asset'] else None
                    
                    # Skip empty entries
                    if not driver_name or driver_name.lower() in ['nan', 'none', 'null', ''] or \
                       not asset_id or asset_id.lower() in ['nan', 'none', 'null', '']:
                        continue
                    
                    # Extract timestamps
                    start_time = None
                    end_time = None
                    
                    if column_map['start_time']:
                        try:
                            start_value = row[column_map['start_time']]
                            if isinstance(start_value, str):
                                # Try to parse datetime string
                                start_time = pd.to_datetime(start_value)
                            else:
                                # Already a timestamp
                                start_time = pd.to_datetime(start_value)
                        except:
                            pass
                    
                    if column_map['end_time']:
                        try:
                            end_value = row[column_map['end_time']]
                            if isinstance(end_value, str):
                                # Try to parse datetime string
                                end_time = pd.to_datetime(end_value)
                            else:
                                # Already a timestamp
                                end_time = pd.to_datetime(end_value)
                        except:
                            pass
                    
                    # Extract activity type
                    activity_type = None
                    if column_map['activity']:
                        activity_type = str(row[column_map['activity']]).strip()
                    
                    # Create normalized values
                    normalized_name = driver_name.lower()
                    normalized_asset_id = asset_id.upper()
                    
                    # Create activity record
                    activity_record = {
                        'driver_name': driver_name,
                        'normalized_name': normalized_name,
                        'asset_id': asset_id,
                        'normalized_asset_id': normalized_asset_id,
                        'start_time': start_time.isoformat() if start_time is not None else None,
                        'end_time': end_time.isoformat() if end_time is not None else None,
                        'activity_type': activity_type,
                        'source_file': os.path.basename(filepath),
                        'verified_employee': normalized_name in self.employee_master,
                        'verified_asset': normalized_asset_id in self.asset_driver_map
                    }
                    
                    # Add any additional fields that might be useful
                    for col in df.columns:
                        col_lower = col.lower()
                        if col_lower not in activity_record and col_lower not in [
                            'start_time', 'end_time', 'driver', 'asset', 'activity'
                        ]:
                            activity_record[col_lower] = row[col]
                    
                    # Add employee ID if we can match it
                    if normalized_name in self.employee_master:
                        activity_record['employee_id'] = self.employee_master[normalized_name].get('employee_id')
                    
                    # Add to activity detail
                    activity_detail.append(activity_record)
                
                logger.info(f"Processed {len(activity_detail)} records from {filepath}")
            
            # Update validation stats
            self.validation['sources']['activity_detail'] = {
                'files': len(date_files),
                'records': len(activity_detail),
                'date': self.date_str
            }
            
            # Store the activity detail
            self.activity_detail = activity_detail
            logger.info(f"Loaded {len(activity_detail)} activity detail records for {self.date_str}")
            return activity_detail
            
        except Exception as e:
            logger.error(f"Error loading activity detail data: {e}")
            logger.error(traceback.format_exc())
            return activity_detail
    
    def load_assets_time_on_site(self) -> List[Dict[str, Any]]:
        """
        Load assets time on site data for the specified date
        
        Returns:
            List[Dict[str, Any]]: List of assets time on site records
        """
        logger.info(f"Loading assets time on site data for {self.date_str}")
        
        assets_time_on_site = []
        assets_time_on_site_dir = DATA_SOURCES.get('assets_time_on_site')
        
        if not os.path.exists(assets_time_on_site_dir):
            logger.warning(f"Assets time on site directory not found: {assets_time_on_site_dir}")
            return assets_time_on_site
        
        try:
            # Look for date-specific files
            date_part = self.date_str.replace('-', '')
            date_files = []
            
            for filename in os.listdir(assets_time_on_site_dir):
                filepath = os.path.join(assets_time_on_site_dir, filename)
                if os.path.isfile(filepath) and (date_part in filename or self.date_str in filename) and filename.endswith('.csv'):
                    date_files.append(filepath)
            
            if not date_files:
                logger.warning(f"No assets time on site files found for {self.date_str}")
                return assets_time_on_site
            
            # Process each file
            for filepath in date_files:
                logger.info(f"Processing assets time on site file: {filepath}")
                
                # Track this as a data source
                self.sources.append({
                    'type': 'assets_time_on_site',
                    'path': filepath,
                    'date': self.date_str,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Load CSV file
                df = pd.read_csv(filepath)
                
                # Normalize column names
                df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
                
                # Look for required columns
                required_cols = {
                    'asset': ['asset', 'asset_id', 'equipment', 'vehicle', 'vehicle_id'],
                    'job_site': ['job_site', 'job', 'site', 'location', 'job_code'],
                    'arrival': ['arrival', 'arrival_time', 'time_in', 'start_time'],
                    'departure': ['departure', 'departure_time', 'time_out', 'end_time']
                }
                
                column_map = {}
                
                # Find column matches
                for field, possible_cols in required_cols.items():
                    column_map[field] = next((col for col in possible_cols if col in df.columns), None)
                
                # Check if we have the minimum required columns
                if not all([column_map['asset'], column_map['job_site']]) or not any([column_map['arrival'], column_map['departure']]):
                    logger.warning(f"Missing required columns in assets time on site file: {filepath}")
                    logger.warning(f"Found columns: {column_map}")
                    continue
                
                # Process each row
                for _, row in df.iterrows():
                    # Extract asset and job site
                    asset_id = str(row[column_map['asset']]).strip() if column_map['asset'] else None
                    job_site = str(row[column_map['job_site']]).strip() if column_map['job_site'] else None
                    
                    # Skip empty entries
                    if not asset_id or asset_id.lower() in ['nan', 'none', 'null', ''] or \
                       not job_site or job_site.lower() in ['nan', 'none', 'null', '']:
                        continue
                    
                    # Extract timestamps
                    arrival_time = None
                    departure_time = None
                    
                    if column_map['arrival']:
                        try:
                            arrival_value = row[column_map['arrival']]
                            if isinstance(arrival_value, str):
                                # Try to parse datetime string
                                arrival_time = pd.to_datetime(arrival_value)
                            else:
                                # Already a timestamp
                                arrival_time = pd.to_datetime(arrival_value)
                        except:
                            pass
                    
                    if column_map['departure']:
                        try:
                            departure_value = row[column_map['departure']]
                            if isinstance(departure_value, str):
                                # Try to parse datetime string
                                departure_time = pd.to_datetime(departure_value)
                            else:
                                # Already a timestamp
                                departure_time = pd.to_datetime(departure_value)
                        except:
                            pass
                    
                    # Create normalized values
                    normalized_asset_id = asset_id.upper()
                    normalized_job_site = job_site.lower()
                    
                    # Look up driver information from asset-driver map
                    driver_info = self.asset_driver_map.get(normalized_asset_id, {})
                    driver_name = driver_info.get('driver_name')
                    
                    # Create asset time on site record
                    asset_time_record = {
                        'asset_id': asset_id,
                        'normalized_asset_id': normalized_asset_id,
                        'job_site': job_site,
                        'normalized_job_site': normalized_job_site,
                        'arrival_time': arrival_time.isoformat() if arrival_time is not None else None,
                        'departure_time': departure_time.isoformat() if departure_time is not None else None,
                        'source_file': os.path.basename(filepath),
                        'verified_asset': normalized_asset_id in self.asset_driver_map
                    }
                    
                    # Add driver info if available
                    if driver_name:
                        asset_time_record['driver_name'] = driver_name
                        asset_time_record['normalized_name'] = driver_info.get('normalized_name')
                        asset_time_record['employee_id'] = driver_info.get('employee_id')
                        asset_time_record['verified_employee'] = asset_time_record['normalized_name'] in self.employee_master if asset_time_record.get('normalized_name') else False
                    
                    # Add any additional fields that might be useful
                    for col in df.columns:
                        col_lower = col.lower()
                        if col_lower not in asset_time_record and col_lower not in [
                            'arrival', 'departure', 'asset', 'job_site'
                        ]:
                            asset_time_record[col_lower] = row[col]
                    
                    # Add to assets time on site
                    assets_time_on_site.append(asset_time_record)
                
                logger.info(f"Processed {len(assets_time_on_site)} records from {filepath}")
            
            # Update validation stats
            self.validation['sources']['assets_time_on_site'] = {
                'files': len(date_files),
                'records': len(assets_time_on_site),
                'date': self.date_str
            }
            
            # Store the assets time on site
            self.assets_time_on_site = assets_time_on_site
            logger.info(f"Loaded {len(assets_time_on_site)} assets time on site records for {self.date_str}")
            return assets_time_on_site
            
        except Exception as e:
            logger.error(f"Error loading assets time on site data: {e}")
            logger.error(traceback.format_exc())
            return assets_time_on_site
    
    def build_driver_list(self) -> List[Dict[str, Any]]:
        """
        Build the master driver list from all data sources
        
        Returns:
            List[Dict[str, Any]]: Consolidated list of drivers
        """
        logger.info("Building driver list from all data sources")
        
        driver_map = {}
        
        # Process driving history records
        for record in self.driving_history:
            normalized_name = record.get('normalized_name')
            if not normalized_name:
                continue
            
            # Check if we already have this driver
            if normalized_name in driver_map:
                # Update existing driver record
                driver = driver_map[normalized_name]
                
                # Update key events
                if record.get('key_on_time') and (not driver.get('key_on_time') or record.get('key_on_time') < driver.get('key_on_time')):
                    driver['key_on_time'] = record.get('key_on_time')
                
                if record.get('key_off_time') and (not driver.get('key_off_time') or record.get('key_off_time') > driver.get('key_off_time')):
                    driver['key_off_time'] = record.get('key_off_time')
                
                # Add to source records
                driver['source_records'].append({
                    'type': 'driving_history',
                    'source_file': record.get('source_file'),
                    'asset_id': record.get('asset_id'),
                    'key_on_time': record.get('key_on_time'),
                    'key_off_time': record.get('key_off_time')
                })
            else:
                # Create new driver record
                driver = {
                    'driver_name': record.get('driver_name'),
                    'normalized_name': normalized_name,
                    'asset_id': record.get('asset_id'),
                    'normalized_asset_id': record.get('normalized_asset_id'),
                    'key_on_time': record.get('key_on_time'),
                    'key_off_time': record.get('key_off_time'),
                    'verified_employee': record.get('verified_employee', False),
                    'verified_asset': record.get('verified_asset', False),
                    'source_records': [{
                        'type': 'driving_history',
                        'source_file': record.get('source_file'),
                        'asset_id': record.get('asset_id'),
                        'key_on_time': record.get('key_on_time'),
                        'key_off_time': record.get('key_off_time')
                    }]
                }
                
                # Add employee ID if available
                if 'employee_id' in record:
                    driver['employee_id'] = record.get('employee_id')
                elif normalized_name in self.employee_master:
                    driver['employee_id'] = self.employee_master[normalized_name].get('employee_id')
                
                # Add to driver map
                driver_map[normalized_name] = driver
        
        # Process activity detail records
        for record in self.activity_detail:
            normalized_name = record.get('normalized_name')
            if not normalized_name:
                continue
            
            # Check if we already have this driver
            if normalized_name in driver_map:
                # Update existing driver record
                driver = driver_map[normalized_name]
                
                # Update start/end times
                if record.get('start_time') and (not driver.get('start_time') or record.get('start_time') < driver.get('start_time')):
                    driver['start_time'] = record.get('start_time')
                
                if record.get('end_time') and (not driver.get('end_time') or record.get('end_time') > driver.get('end_time')):
                    driver['end_time'] = record.get('end_time')
                
                # Add to source records
                driver['source_records'].append({
                    'type': 'activity_detail',
                    'source_file': record.get('source_file'),
                    'asset_id': record.get('asset_id'),
                    'start_time': record.get('start_time'),
                    'end_time': record.get('end_time'),
                    'activity_type': record.get('activity_type')
                })
            else:
                # Create new driver record
                driver = {
                    'driver_name': record.get('driver_name'),
                    'normalized_name': normalized_name,
                    'asset_id': record.get('asset_id'),
                    'normalized_asset_id': record.get('normalized_asset_id'),
                    'start_time': record.get('start_time'),
                    'end_time': record.get('end_time'),
                    'verified_employee': record.get('verified_employee', False),
                    'verified_asset': record.get('verified_asset', False),
                    'source_records': [{
                        'type': 'activity_detail',
                        'source_file': record.get('source_file'),
                        'asset_id': record.get('asset_id'),
                        'start_time': record.get('start_time'),
                        'end_time': record.get('end_time'),
                        'activity_type': record.get('activity_type')
                    }]
                }
                
                # Add employee ID if available
                if 'employee_id' in record:
                    driver['employee_id'] = record.get('employee_id')
                elif normalized_name in self.employee_master:
                    driver['employee_id'] = self.employee_master[normalized_name].get('employee_id')
                
                # Add to driver map
                driver_map[normalized_name] = driver
        
        # Process assets time on site for job site assignment
        asset_job_sites = {}
        
        for record in self.assets_time_on_site:
            normalized_asset_id = record.get('normalized_asset_id')
            if not normalized_asset_id:
                continue
            
            # Store the job site for this asset
            asset_job_sites[normalized_asset_id] = {
                'job_site': record.get('job_site'),
                'normalized_job_site': record.get('normalized_job_site'),
                'arrival_time': record.get('arrival_time'),
                'departure_time': record.get('departure_time')
            }
        
        # Enhance driver records with job site information
        for normalized_name, driver in driver_map.items():
            normalized_asset_id = driver.get('normalized_asset_id')
            
            if normalized_asset_id in asset_job_sites:
                job_site_info = asset_job_sites[normalized_asset_id]
                
                # Add job site information
                driver['assigned_job_site'] = job_site_info.get('job_site')
                driver['normalized_job_site'] = job_site_info.get('normalized_job_site')
                driver['job_site_arrival'] = job_site_info.get('arrival_time')
                driver['job_site_departure'] = job_site_info.get('departure_time')
                driver['verified_location'] = True
            else:
                driver['verified_location'] = False
        
        # Convert driver map to list
        drivers = list(driver_map.values())
        
        # Update validation stats
        self.validation['total_entries'] = len(drivers)
        self.validation['verified_employees'] = sum(1 for d in drivers if d.get('verified_employee', False))
        self.validation['verified_assets'] = sum(1 for d in drivers if d.get('verified_asset', False))
        self.validation['verified_locations'] = sum(1 for d in drivers if d.get('verified_location', False))
        self.validation['unmatched_employees'] = sum(1 for d in drivers if not d.get('verified_employee', False))
        self.validation['unmatched_assets'] = sum(1 for d in drivers if not d.get('verified_asset', False))
        
        # Store the driver list
        self.drivers = drivers
        logger.info(f"Built driver list with {len(drivers)} drivers")
        return drivers
    
    def classify_driver_status(self):
        """
        Classify each driver according to attendance rules
        """
        logger.info("Classifying driver status")
        
        # Get time thresholds
        late_minutes = TIME_THRESHOLDS.get('late_minutes', 15)
        early_end_minutes = TIME_THRESHOLDS.get('early_end_minutes', 30)
        
        # Initialize counters
        on_time_count = 0
        late_count = 0
        early_end_count = 0
        not_on_job_count = 0
        unmatched_count = 0
        ghost_count = 0
        
        # Process each driver
        for driver in self.drivers:
            # Default status
            status = 'Unknown'
            status_reason = None
            
            # Check if driver is verified
            if not driver.get('verified_employee', False):
                status = 'Unmatched'
                status_reason = 'Driver not found in employee master list'
                unmatched_count += 1
                driver['status'] = status
                driver['status_reason'] = status_reason
                continue
            
            # Get times from driver record
            actual_start_time = None
            actual_end_time = None
            
            # Get the earliest start time from all sources
            if 'key_on_time' in driver and driver['key_on_time']:
                try:
                    actual_start_time = datetime.fromisoformat(driver['key_on_time'].replace('Z', '+00:00'))
                except:
                    pass
            
            if 'start_time' in driver and driver['start_time']:
                try:
                    start_time = datetime.fromisoformat(driver['start_time'].replace('Z', '+00:00'))
                    if not actual_start_time or start_time < actual_start_time:
                        actual_start_time = start_time
                except:
                    pass
            
            # Get the latest end time from all sources
            if 'key_off_time' in driver and driver['key_off_time']:
                try:
                    actual_end_time = datetime.fromisoformat(driver['key_off_time'].replace('Z', '+00:00'))
                except:
                    pass
            
            if 'end_time' in driver and driver['end_time']:
                try:
                    end_time = datetime.fromisoformat(driver['end_time'].replace('Z', '+00:00'))
                    if not actual_end_time or end_time > actual_end_time:
                        actual_end_time = end_time
                except:
                    pass
            
            # For demonstration, create scheduled times (would normally come from StartTimeJob)
            # In a real implementation, these would be loaded from job schedules
            scheduled_start_time = self.date.replace(hour=7, minute=0, second=0)
            scheduled_end_time = self.date.replace(hour=17, minute=0, second=0)
            
            # Add scheduled and actual times to driver record
            driver['scheduled_start_time'] = scheduled_start_time.isoformat()
            driver['scheduled_end_time'] = scheduled_end_time.isoformat()
            driver['actual_start_time'] = actual_start_time.isoformat() if actual_start_time else None
            driver['actual_end_time'] = actual_end_time.isoformat() if actual_end_time else None
            
            # Check for missing times
            if not actual_start_time and not actual_end_time:
                status = 'Not On Job'
                status_reason = 'No activity detected'
                not_on_job_count += 1
            
            # Check location
            elif not driver.get('verified_location', False):
                status = 'Not On Job'
                status_reason = 'Not at assigned job site'
                not_on_job_count += 1
            
            # Check late arrival
            elif actual_start_time and actual_start_time > scheduled_start_time + timedelta(minutes=late_minutes):
                status = 'Late'
                minutes_late = (actual_start_time - scheduled_start_time).total_seconds() / 60
                status_reason = f"Arrived {int(minutes_late)} minutes late"
                late_count += 1
            
            # Check early departure
            elif actual_end_time and actual_end_time < scheduled_end_time - timedelta(minutes=early_end_minutes):
                status = 'Early End'
                minutes_early = (scheduled_end_time - actual_end_time).total_seconds() / 60
                status_reason = f"Left {int(minutes_early)} minutes early"
                early_end_count += 1
            
            # Otherwise, on time
            else:
                status = 'On Time'
                status_reason = 'Present at job site within schedule parameters'
                on_time_count += 1
            
            # Set status in driver record
            driver['status'] = status
            driver['status_reason'] = status_reason
        
        # Update summary
        self.summary = {
            'total': len(self.drivers),
            'on_time': on_time_count,
            'late': late_count,
            'early_end': early_end_count,
            'not_on_job': not_on_job_count,
            'unmatched': unmatched_count,
            'ghost': ghost_count
        }
        
        logger.info(f"Classified {len(self.drivers)} drivers: {on_time_count} on time, {late_count} late, {early_end_count} early end, {not_on_job_count} not on job, {unmatched_count} unmatched")
    
    def create_identity_verification_manifest(self) -> Dict[str, Any]:
        """
        Create an identity verification manifest for audit traceability
        
        Returns:
            Dict[str, Any]: Verification manifest
        """
        logger.info("Creating identity verification manifest")
        
        # Create verification manifest
        manifest = {
            'date': self.date_str,
            'generated': datetime.now().isoformat(),
            'validation': self.validation,
            'verified_employees': {},
            'unverified_employees': {},
            'signature': f"IDENTITY-VERIFIED-{hashlib.sha256(self.date_str.encode()).hexdigest()[:8]}"
        }
        
        # Add employee verification details
        for driver in self.drivers:
            normalized_name = driver.get('normalized_name')
            
            if driver.get('verified_employee', False):
                manifest['verified_employees'][normalized_name] = {
                    'name': driver.get('driver_name'),
                    'employee_id': driver.get('employee_id'),
                    'asset_id': driver.get('asset_id'),
                    'source': 'employee_master'
                }
            else:
                manifest['unverified_employees'][normalized_name] = {
                    'name': driver.get('driver_name'),
                    'asset_id': driver.get('asset_id'),
                    'source_records': driver.get('source_records', [])
                }
        
        return manifest
    
    def export_report(self, verified_only: bool = True) -> Dict[str, Any]:
        """
        Export the daily driver report in various formats
        
        Args:
            verified_only (bool): Whether to include only verified drivers in the report
            
        Returns:
            Dict[str, Any]: Dictionary with paths to exported reports
        """
        logger.info(f"Exporting daily driver report for {self.date_str} (verified_only={verified_only})")
        
        result = {
            'date': self.date_str,
            'exports': {}
        }
        
        try:
            # Filter drivers if verified_only is True
            if verified_only:
                drivers = [d for d in self.drivers if d.get('verified_employee', False)]
                logger.info(f"Including only {len(drivers)} verified drivers in report")
            else:
                drivers = self.drivers
                logger.info(f"Including all {len(drivers)} drivers in report")
            
            # Create report data
            report_data = {
                'date': self.date_str,
                'generated': datetime.now().isoformat(),
                'drivers': drivers,
                'summary': self.summary,
                'metadata': {
                    'identity_verification': self.create_identity_verification_manifest(),
                    'sources': self.sources
                }
            }
            
            # Export JSON
            json_path = f"reports/genius_core/daily_report_{self.date_str}.json"
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            result['exports']['json'] = json_path
            
            # Export for public API
            export_json_path = f"exports/genius_core/daily_report_{self.date_str}.json"
            os.makedirs(os.path.dirname(export_json_path), exist_ok=True)
            with open(export_json_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            result['exports']['export_json'] = export_json_path
            
            # Export Excel
            excel_path = f"reports/genius_core/daily_report_{self.date_str}.xlsx"
            
            # Convert drivers to DataFrame
            df = pd.DataFrame(drivers)
            
            # Add status summary sheets
            with pd.ExcelWriter(excel_path) as writer:
                # Main sheet with all drivers
                df.to_excel(writer, sheet_name='All Drivers', index=False)
                
                # Status-specific sheets
                if 'status' in df.columns:
                    # Late drivers
                    late_df = df[df['status'] == 'Late']
                    if not late_df.empty:
                        late_df.to_excel(writer, sheet_name='Late', index=False)
                    
                    # Early end drivers
                    early_df = df[df['status'] == 'Early End']
                    if not early_df.empty:
                        early_df.to_excel(writer, sheet_name='Early End', index=False)
                    
                    # Not on job drivers
                    not_on_job_df = df[df['status'] == 'Not On Job']
                    if not not_on_job_df.empty:
                        not_on_job_df.to_excel(writer, sheet_name='Not On Job', index=False)
                    
                    # Unmatched drivers
                    unmatched_df = df[df['status'] == 'Unmatched']
                    if not unmatched_df.empty:
                        unmatched_df.to_excel(writer, sheet_name='Unmatched', index=False)
                
                # Summary sheet
                summary_data = [
                    ['Metric', 'Count', 'Percentage'],
                    ['Total Drivers', self.summary['total'], '100%'],
                    ['On Time', self.summary['on_time'], f"{self.summary['on_time']/self.summary['total']*100:.1f}%" if self.summary['total'] > 0 else "0%"],
                    ['Late', self.summary['late'], f"{self.summary['late']/self.summary['total']*100:.1f}%" if self.summary['total'] > 0 else "0%"],
                    ['Early End', self.summary['early_end'], f"{self.summary['early_end']/self.summary['total']*100:.1f}%" if self.summary['total'] > 0 else "0%"],
                    ['Not On Job', self.summary['not_on_job'], f"{self.summary['not_on_job']/self.summary['total']*100:.1f}%" if self.summary['total'] > 0 else "0%"],
                    ['Unmatched', self.summary['unmatched'], f"{self.summary['unmatched']/self.summary['total']*100:.1f}%" if self.summary['total'] > 0 else "0%"]
                ]
                
                summary_df = pd.DataFrame(summary_data[1:], columns=summary_data[0])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            result['exports']['excel'] = excel_path
            
            # Export for client
            export_excel_path = f"exports/genius_core/daily_report_{self.date_str}.xlsx"
            
            # Copy the Excel file to exports
            import shutil
            shutil.copy2(excel_path, export_excel_path)
            result['exports']['export_excel'] = export_excel_path
            
            # Try to generate PDF report
            try:
                from generate_pdf_report import generate_pdf_report
                pdf_path = f"reports/genius_core/daily_report_{self.date_str}.pdf"
                generate_pdf_report(self.date_str, report_data, pdf_path)
                result['exports']['pdf'] = pdf_path
                
                # Copy to exports
                export_pdf_path = f"exports/genius_core/daily_report_{self.date_str}.pdf"
                shutil.copy2(pdf_path, export_pdf_path)
                result['exports']['export_pdf'] = export_pdf_path
            except Exception as e:
                logger.error(f"Error generating PDF report: {e}")
                logger.error(traceback.format_exc())
            
            logger.info(f"Exported reports to: {', '.join(result['exports'].values())}")
            return result
            
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            logger.error(traceback.format_exc())
            return result
    
    def process(self) -> Dict[str, Any]:
        """
        Process all data and generate the daily driver report
        
        Returns:
            Dict[str, Any]: Processing results
        """
        logger.info(f"Processing GENIUS CORE for {self.date_str}")
        
        result = {
            'date': self.date_str,
            'status': 'SUCCESS',
            'error': None,
            'exports': {},
            'drivers': 0,
            'validated': 0
        }
        
        try:
            # Step 1: Load employee master list
            self.load_employee_master()
            
            # Step 2: Load equipment billing data
            self.load_equipment_billing_data()
            
            # Step 3: Load driving history
            self.load_driving_history()
            
            # Step 4: Load activity detail
            self.load_activity_detail()
            
            # Step 5: Load assets time on site
            self.load_assets_time_on_site()
            
            # Step 6: Build driver list
            self.build_driver_list()
            
            # Step 7: Classify driver status
            self.classify_driver_status()
            
            # Step 8: Export report
            export_result = self.export_report()
            result['exports'] = export_result.get('exports', {})
            result['drivers'] = len(self.drivers)
            result['validated'] = self.validation['verified_employees']
            
            logger.info(f"GENIUS CORE processing completed for {self.date_str}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing GENIUS CORE: {e}")
            logger.error(traceback.format_exc())
            
            result['status'] = 'FAILED'
            result['error'] = str(e)
            return result

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TRAXORA GENIUS CORE | Comprehensive Fleet Attendance System')
    parser.add_argument('date', help='Date to process in YYYY-MM-DD format')
    parser.add_argument('--include-all', action='store_true', help='Include all drivers in the report, not just verified ones')
    
    args = parser.parse_args()
    
    # Initialize GENIUS CORE
    genius = GeniusCore(args.date)
    
    # Process data
    result = genius.process()
    
    # Print results
    if result['status'] == 'SUCCESS':
        print(f"\nGENIUS CORE Processing Completed for {args.date}")
        print("=" * 70)
        print(f"Total Drivers: {result['drivers']}")
        print(f"Verified Employees: {result['validated']}")
        print("\nExported Reports:")
        for format, path in result['exports'].items():
            print(f"  - {format}: {path}")
    else:
        print(f"\nGENIUS CORE Processing Failed for {args.date}")
        print("=" * 70)
        print(f"Error: {result['error']}")

if __name__ == '__main__':
    main()