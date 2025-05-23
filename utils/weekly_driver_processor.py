"""
TRAXORA Fleet Management System - Weekly Driver Processor

This module provides functionality for processing weekly driver reports across multiple days,
with full drill-down capability and comprehensive analytics.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv
import re
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class WeeklyDriverProcessor:
    """
    Weekly Driver Processor class for handling multi-day reports
    with GENIUS CORE validation and cross-source verification.
    """
    
    def __init__(self, start_date, end_date, root_path=None):
        """
        Initialize the processor with date range
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            root_path (str): Root path for file operations
        """
        self.start_date = start_date
        self.end_date = end_date
        self.root_path = root_path or os.getcwd()
        
        # Parse dates
        self.start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        self.end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Initialize data containers
        self.driving_history_data = {}
        self.activity_detail_data = {}
        self.time_on_site_data = {}
        self.timecard_data = {}
        
        # Initialize result containers
        self.daily_reports = {}
        self.weekly_summary = {}
        
        # Set up directories
        self.setup_directories()
    
    def setup_directories(self):
        """Setup required directories for data and reports"""
        self.data_dir = os.path.join(self.root_path, 'data', 'weekly_driver_reports')
        self.reports_dir = os.path.join(self.root_path, 'reports', 'weekly_driver_reports')
        self.upload_dir = os.path.join(self.root_path, 'uploads', 'weekly_reports')
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def load_files(self, driving_history_path=None, activity_detail_path=None, 
                   time_on_site_path=None, timecard_paths=None, 
                   from_attached_assets=False):
        """
        Load data from provided file paths
        
        Args:
            driving_history_path (str): Path to driving history CSV
            activity_detail_path (str): Path to activity detail CSV
            time_on_site_path (str): Path to time on site CSV
            timecard_paths (list): List of paths to timecard Excel files
            from_attached_assets (bool): Whether to load from attached_assets folder
        """
        logger.info("Loading files for weekly driver report")
        
        # Set base directory for file paths
        base_dir = 'attached_assets' if from_attached_assets else self.upload_dir
        
        # Load driving history data
        if driving_history_path:
            path = os.path.join(base_dir, driving_history_path) if not from_attached_assets else driving_history_path
            logger.info(f"Loading driving history from: {path}")
            self.load_driving_history(path)
        
        # Load activity detail data
        if activity_detail_path:
            path = os.path.join(base_dir, activity_detail_path) if not from_attached_assets else activity_detail_path
            logger.info(f"Loading activity detail from: {path}")
            self.load_activity_detail(path)
        
        # Load time on site data
        if time_on_site_path:
            path = os.path.join(base_dir, time_on_site_path) if not from_attached_assets else time_on_site_path
            logger.info(f"Loading time on site from: {path}")
            self.load_time_on_site(path)
        
        # Load timecard data
        if timecard_paths:
            for timecard_path in timecard_paths:
                path = os.path.join(base_dir, timecard_path) if not from_attached_assets else timecard_path
                logger.info(f"Loading timecard from: {path}")
                self.load_timecard(path)
    
    def load_driving_history(self, file_path):
        """
        Load and parse driving history CSV file
        
        Args:
            file_path (str): Path to driving history CSV
        """
        try:
            # Read the CSV file
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Find the header row
            header_row = None
            for i, row in enumerate(rows):
                if len(row) > 5 and 'EventDateTime' in row or 'Contact' in row:
                    header_row = i
                    break
            
            if header_row is None:
                logger.error("Could not find header row in driving history file")
                return
            
            # Extract headers
            headers = rows[header_row]
            
            # Process data rows
            data_rows = rows[header_row + 1:]
            
            # Organize data by driver and date
            for row in data_rows:
                if len(row) < len(headers):
                    continue
                
                row_dict = dict(zip(headers, row))
                
                # Skip rows without event date/time
                if 'EventDateTime' not in row_dict or not row_dict['EventDateTime']:
                    continue
                
                # Extract date and time information
                try:
                    event_datetime = row_dict['EventDateTime']
                    if isinstance(event_datetime, str) and '/' in event_datetime:
                        dt = datetime.strptime(event_datetime, '%m/%d/%Y %I:%M:%S %p')
                        date_str = dt.strftime('%Y-%m-%d')
                        
                        # Check if date is in our range
                        if dt.date() < self.start_dt or dt.date() > self.end_dt:
                            continue
                        
                        # Get driver name
                        driver_name = None
                        if 'Contact' in row_dict and row_dict['Contact']:
                            # Extract name from format "Name (ID)"
                            contact = row_dict['Contact']
                            if '(' in contact:
                                driver_name = contact.split('(')[0].strip()
                        
                        if not driver_name:
                            # Try to extract from asset label
                            if 'AssetLabel' in row_dict and row_dict['AssetLabel']:
                                asset_label = row_dict['AssetLabel']
                                match = re.search(r'\(([^)]+)\)', asset_label)
                                if match:
                                    driver_name = match.group(1).strip()
                        
                        if not driver_name and 'Textbox53' in row_dict and row_dict['Textbox53']:
                            # Extract from Textbox53 which often contains asset + driver info
                            asset_info = row_dict['Textbox53']
                            match = re.search(r'\(([^)]+)\)', asset_info)
                            if match:
                                driver_name = match.group(1).strip()
                        
                        if not driver_name:
                            continue
                        
                        # Initialize data for this date if needed
                        if date_str not in self.driving_history_data:
                            self.driving_history_data[date_str] = {}
                        
                        # Initialize data for this driver if needed
                        if driver_name not in self.driving_history_data[date_str]:
                            self.driving_history_data[date_str][driver_name] = []
                        
                        # Add event to driver's data
                        self.driving_history_data[date_str][driver_name].append({
                            'time': dt.strftime('%H:%M:%S'),
                            'event_type': row_dict.get('MsgType', ''),
                            'location': row_dict.get('Location', ''),
                            'latitude': row_dict.get('Latitude', ''),
                            'longitude': row_dict.get('Longitude', ''),
                            'raw_data': row_dict
                        })
                except Exception as e:
                    logger.error(f"Error processing driving history row: {e}")
            
            # Sort events by time for each driver
            for date_str in self.driving_history_data:
                for driver_name in self.driving_history_data[date_str]:
                    self.driving_history_data[date_str][driver_name].sort(
                        key=lambda x: datetime.strptime(x['time'], '%H:%M:%S')
                    )
            
            logger.info(f"Loaded driving history for {len(self.driving_history_data)} days")
        
        except Exception as e:
            logger.error(f"Error loading driving history: {e}")
    
    def load_activity_detail(self, file_path):
        """
        Load and parse activity detail CSV file
        
        Args:
            file_path (str): Path to activity detail CSV
        """
        try:
            # Read the CSV file
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Find the header row
            header_row = None
            for i, row in enumerate(rows):
                if len(row) > 5 and 'EventDateTimex' in row or 'AssetLabel' in row:
                    header_row = i
                    break
            
            if header_row is None:
                logger.error("Could not find header row in activity detail file")
                return
            
            # Extract headers
            headers = rows[header_row]
            
            # Process data rows
            data_rows = rows[header_row + 1:]
            
            # Organize data by asset and date
            for row in data_rows:
                if len(row) < len(headers):
                    continue
                
                row_dict = dict(zip(headers, row))
                
                # Skip rows without event date/time
                if 'EventDateTimex' not in row_dict or not row_dict['EventDateTimex']:
                    continue
                
                # Extract date and time information
                try:
                    event_datetime = row_dict['EventDateTimex']
                    if isinstance(event_datetime, str) and '/' in event_datetime:
                        dt = datetime.strptime(event_datetime, '%m/%d/%Y %I:%M:%S %p CT')
                        date_str = dt.strftime('%Y-%m-%d')
                        
                        # Check if date is in our range
                        if dt.date() < self.start_dt or dt.date() > self.end_dt:
                            continue
                        
                        # Get asset label and extract driver name
                        asset_label = row_dict.get('AssetLabel', '')
                        driver_name = None
                        
                        if asset_label:
                            # Extract name from format "ASSET-XX (DRIVER NAME) TYPE"
                            match = re.search(r'\(([^)]+)\)', asset_label)
                            if match:
                                driver_name = match.group(1).strip()
                        
                        if not driver_name and 'Contact' in row_dict and row_dict['Contact']:
                            driver_name = row_dict['Contact'].split('(')[0].strip()
                        
                        if not driver_name:
                            continue
                        
                        # Initialize data for this date if needed
                        if date_str not in self.activity_detail_data:
                            self.activity_detail_data[date_str] = {}
                        
                        # Initialize data for this asset if needed
                        if driver_name not in self.activity_detail_data[date_str]:
                            self.activity_detail_data[date_str][driver_name] = []
                        
                        # Add event to asset's data
                        self.activity_detail_data[date_str][driver_name].append({
                            'time': dt.strftime('%H:%M:%S'),
                            'event_type': row_dict.get('Reasonx', ''),
                            'location': row_dict.get('Locationx', ''),
                            'latitude': row_dict.get('Latitude', ''),
                            'longitude': row_dict.get('Longitude', ''),
                            'raw_data': row_dict
                        })
                except Exception as e:
                    logger.error(f"Error processing activity detail row: {e}")
            
            # Sort events by time for each asset
            for date_str in self.activity_detail_data:
                for driver_name in self.activity_detail_data[date_str]:
                    self.activity_detail_data[date_str][driver_name].sort(
                        key=lambda x: datetime.strptime(x['time'], '%H:%M:%S')
                    )
            
            logger.info(f"Loaded activity detail for {len(self.activity_detail_data)} days")
        
        except Exception as e:
            logger.error(f"Error loading activity detail: {e}")
    
    def load_time_on_site(self, file_path):
        """
        Load and parse time on site CSV file
        
        Args:
            file_path (str): Path to time on site CSV
        """
        try:
            # Read the CSV file
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Find the header row
            header_row = None
            for i, row in enumerate(rows):
                if len(row) > 5 and 'Location' in row and 'Date' in row:
                    header_row = i
                    break
            
            if header_row is None:
                logger.error("Could not find header row in time on site file")
                return
            
            # Extract headers
            headers = rows[header_row]
            
            # Process data rows
            data_rows = rows[header_row + 1:]
            
            # Organize data by asset and date
            for row in data_rows:
                if len(row) < len(headers):
                    continue
                
                row_dict = dict(zip(headers, row))
                
                # Skip rows without date
                if 'Date' not in row_dict or not row_dict['Date']:
                    continue
                
                # Extract date information
                try:
                    date_str_raw = row_dict['Date']
                    if isinstance(date_str_raw, str) and '/' in date_str_raw:
                        date_obj = datetime.strptime(date_str_raw, '%m/%d/%Y').date()
                        date_str = date_obj.strftime('%Y-%m-%d')
                        
                        # Check if date is in our range
                        if date_obj < self.start_dt or date_obj > self.end_dt:
                            continue
                        
                        # Get asset and extract driver name
                        asset = row_dict.get('Asset', '')
                        driver_name = None
                        
                        if asset:
                            # Extract name from format "ASSET-XX (DRIVER NAME) TYPE"
                            match = re.search(r'\(([^)]+)\)', asset)
                            if match:
                                driver_name = match.group(1).strip()
                        
                        # Skip if we couldn't determine driver
                        if not driver_name:
                            continue
                        
                        # Get job site (location)
                        location = row_dict.get('Location', '')
                        
                        # Get start and end times
                        start_time = row_dict.get('StartTime', '')
                        end_time = row_dict.get('EndTime', '')
                        
                        # Skip if we don't have time information
                        if not start_time and not end_time:
                            continue
                        
                        # Process start time
                        start_time_obj = None
                        if start_time and start_time != "—" and start_time != "Began Day On Site":
                            try:
                                start_time_obj = datetime.strptime(start_time, '%I:%M %p CT')
                                start_time = start_time_obj.strftime('%H:%M:%S')
                            except ValueError:
                                start_time = None
                        
                        # Process end time
                        end_time_obj = None
                        if end_time and end_time != "—" and end_time != "Asset On Site":
                            try:
                                end_time_obj = datetime.strptime(end_time, '%I:%M %p CT')
                                end_time = end_time_obj.strftime('%H:%M:%S')
                            except ValueError:
                                end_time = None
                        
                        # Initialize data for this date if needed
                        if date_str not in self.time_on_site_data:
                            self.time_on_site_data[date_str] = {}
                        
                        # Initialize data for this driver if needed
                        if driver_name not in self.time_on_site_data[date_str]:
                            self.time_on_site_data[date_str][driver_name] = []
                        
                        # Add record to driver's data
                        self.time_on_site_data[date_str][driver_name].append({
                            'location': location,
                            'start_time': start_time,
                            'end_time': end_time,
                            'time_on_site': row_dict.get('TimeOnSite', ''),
                            'asset': asset,
                            'raw_data': row_dict
                        })
                except Exception as e:
                    logger.error(f"Error processing time on site row: {e}")
            
            logger.info(f"Loaded time on site data for {len(self.time_on_site_data)} days")
        
        except Exception as e:
            logger.error(f"Error loading time on site: {e}")
    
    def load_timecard(self, file_path):
        """
        Load and parse timecard Excel file
        
        Args:
            file_path (str): Path to timecard Excel
        """
        # This is a stub for now since we can't read Excel files directly with str_replace_editor
        pass
    
    def get_date_range(self):
        """Get all dates in the specified range"""
        date_range = []
        current_date = self.start_dt
        while current_date <= self.end_dt:
            date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        return date_range
    
    def process_daily_report(self, date_str):
        """
        Process a single day's report
        
        Args:
            date_str (str): Date string in YYYY-MM-DD format
            
        Returns:
            dict: Processed daily report
        """
        logger.info(f"Processing daily report for {date_str}")
        
        try:
            # Get data for this date
            driving_history = self.driving_history_data.get(date_str, {})
            activity_detail = self.activity_detail_data.get(date_str, {})
            time_on_site = self.time_on_site_data.get(date_str, {})
            
            # Get all unique drivers
            all_drivers = set()
            all_drivers.update(driving_history.keys())
            all_drivers.update(activity_detail.keys())
            all_drivers.update(time_on_site.keys())
            
            # Initialize driver records
            driver_records = {}
            
            # Process each driver
            for driver_name in all_drivers:
                # Get driver data from each source
                driver_driving = driving_history.get(driver_name, [])
                driver_activity = activity_detail.get(driver_name, [])
                driver_time_on_site = time_on_site.get(driver_name, [])
                
                # Determine job site
                job_site = None
                if driver_time_on_site:
                    # Use most frequent location from time on site
                    locations = [record['location'] for record in driver_time_on_site]
                    if locations:
                        # Count occurrences
                        location_counts = {}
                        for loc in locations:
                            location_counts[loc] = location_counts.get(loc, 0) + 1
                        
                        # Get most frequent
                        job_site = max(location_counts.items(), key=lambda x: x[1])[0]
                
                # If still no job site, try to determine from driving history
                if not job_site and driver_driving:
                    # Look for patterns in locations
                    locations = [record['location'] for record in driver_driving if record['location']]
                    
                    if locations:
                        # Extract job site names (usually before the comma)
                        job_sites = []
                        for loc in locations:
                            if ',' in loc:
                                site = loc.split(',')[0].strip()
                                if site and not site.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                                    job_sites.append(site)
                        
                        if job_sites:
                            # Count occurrences
                            site_counts = {}
                            for site in job_sites:
                                site_counts[site] = site_counts.get(site, 0) + 1
                            
                            # Get most frequent
                            job_site = max(site_counts.items(), key=lambda x: x[1])[0]
                
                # Determine first key on time
                first_key_on = None
                first_key_on_record = None
                
                # Check driving history for first key on
                for record in driver_driving:
                    if record['event_type'] == 'Key On':
                        first_key_on = record['time']
                        first_key_on_record = record
                        break
                
                # If no key on in driving history, check activity detail
                if not first_key_on and driver_activity:
                    for record in driver_activity:
                        if record['event_type'] == 'Key On':
                            first_key_on = record['time']
                            first_key_on_record = record
                            break
                
                # Determine last key off time
                last_key_off = None
                last_key_off_record = None
                
                # Check driving history for last key off
                if driver_driving:
                    for record in reversed(driver_driving):
                        if record['event_type'] == 'Key Off':
                            last_key_off = record['time']
                            last_key_off_record = record
                            break
                
                # If no key off in driving history, check activity detail
                if not last_key_off and driver_activity:
                    for record in reversed(driver_activity):
                        if record['event_type'] == 'Key Off':
                            last_key_off = record['time']
                            last_key_off_record = record
                            break
                
                # Determine status based on times
                status = "Unknown"
                late_minutes = 0
                early_minutes = 0
                
                if first_key_on and job_site:
                    # Parse work start time
                    work_start = datetime.strptime('07:00:00', '%H:%M:%S')
                    key_on_time = datetime.strptime(first_key_on, '%H:%M:%S')
                    
                    # Check if late
                    if key_on_time > work_start:
                        late_minutes = int((key_on_time - work_start).total_seconds() / 60)
                        
                        if late_minutes >= 15:
                            status = "Late Start"
                        else:
                            status = "On Time"
                    else:
                        status = "On Time"
                
                if last_key_off and job_site and status != "Late Start":
                    # Parse work end time
                    work_end = datetime.strptime('17:00:00', '%H:%M:%S')
                    key_off_time = datetime.strptime(last_key_off, '%H:%M:%S')
                    
                    # Check if early
                    if key_off_time < work_end:
                        early_minutes = int((work_end - key_off_time).total_seconds() / 60)
                        
                        if early_minutes >= 15:
                            status = "Early End"
                
                # Check if not on job
                if not job_site or (not first_key_on and not last_key_off):
                    status = "Not On Job"
                
                # Build driver record
                driver_record = {
                    'name': driver_name,
                    'job_site': job_site or "Unknown",
                    'status': status,
                    'first_key_on': first_key_on,
                    'last_key_off': last_key_off,
                    'late_minutes': late_minutes,
                    'early_minutes': early_minutes,
                    'events': {
                        'driving_history': driver_driving,
                        'activity_detail': driver_activity,
                        'time_on_site': driver_time_on_site
                    },
                    'has_driving_data': bool(driver_driving),
                    'has_activity_data': bool(driver_activity),
                    'has_time_on_site': bool(driver_time_on_site)
                }
                
                # Add to driver records
                driver_records[driver_name] = driver_record
            
            # Create classifications
            late_start_drivers = [record for record in driver_records.values() if record['status'] == 'Late Start']
            early_end_drivers = [record for record in driver_records.values() if record['status'] == 'Early End']
            not_on_job_drivers = [record for record in driver_records.values() if record['status'] == 'Not On Job']
            on_time_drivers = [record for record in driver_records.values() if record['status'] == 'On Time']
            
            # Format date for display
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
            
            # Create daily report
            daily_report = {
                'date': date_str,
                'formatted_date': formatted_date,
                'driver_records': driver_records,
                'late_start_drivers': [d['name'] for d in late_start_drivers],
                'early_end_drivers': [d['name'] for d in early_end_drivers],
                'not_on_job_drivers': [d['name'] for d in not_on_job_drivers],
                'on_time_drivers': [d['name'] for d in on_time_drivers],
                'total_drivers': len(driver_records),
                'total_late': len(late_start_drivers),
                'total_early': len(early_end_drivers),
                'total_not_on_job': len(not_on_job_drivers),
                'total_on_time': len(on_time_drivers),
                'has_driving_data': bool(driving_history),
                'has_activity_data': bool(activity_detail),
                'has_time_on_site_data': bool(time_on_site)
            }
            
            logger.info(f"Processed daily report for {date_str} with {len(driver_records)} drivers")
            return daily_report
        
        except Exception as e:
            logger.error(f"Error processing daily report for {date_str}: {e}")
            return None
    
    def generate_weekly_summary(self):
        """
        Generate a summary of the weekly report
        
        Returns:
            dict: Weekly summary data
        """
        logger.info("Generating weekly summary")
        
        try:
            # Initialize summary data
            summary = {
                'date_range': {
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'start_formatted': datetime.strptime(self.start_date, '%Y-%m-%d').strftime('%b %d, %Y'),
                    'end_formatted': datetime.strptime(self.end_date, '%Y-%m-%d').strftime('%b %d, %Y')
                },
                'total_drivers': 0,
                'drivers_by_day': {},
                'status_by_day': {},
                'driver_attendance': {},
                'job_site_attendance': {},
                'chronic_issues': {
                    'late_starts': [],
                    'early_ends': [],
                    'not_on_job': []
                }
            }
            
            # Track all drivers
            all_drivers = set()
            all_job_sites = set()
            
            # Get all dates in range
            date_range = self.get_date_range()
            
            # Initialize date data for status tracking
            for date_str in date_range:
                summary['status_by_day'][date_str] = {
                    'late_start': 0,
                    'early_end': 0,
                    'not_on_job': 0,
                    'on_time': 0,
                    'total': 0
                }
                
                summary['drivers_by_day'][date_str] = {
                    'late_start': [],
                    'early_end': [],
                    'not_on_job': [],
                    'on_time': []
                }
            
            # Process each day
            for date_str, daily_report in self.daily_reports.items():
                # Update unique drivers
                for driver_name, driver_record in daily_report['driver_records'].items():
                    all_drivers.add(driver_name)
                    
                    # Track job sites
                    if driver_record['job_site'] != "Unknown":
                        all_job_sites.add(driver_record['job_site'])
                
                # Update status counts
                summary['status_by_day'][date_str]['late_start'] = len(daily_report['late_start_drivers'])
                summary['status_by_day'][date_str]['early_end'] = len(daily_report['early_end_drivers'])
                summary['status_by_day'][date_str]['not_on_job'] = len(daily_report['not_on_job_drivers'])
                summary['status_by_day'][date_str]['on_time'] = len(daily_report['on_time_drivers'])
                summary['status_by_day'][date_str]['total'] = daily_report['total_drivers']
                
                # Update drivers by status
                summary['drivers_by_day'][date_str]['late_start'] = daily_report['late_start_drivers']
                summary['drivers_by_day'][date_str]['early_end'] = daily_report['early_end_drivers']
                summary['drivers_by_day'][date_str]['not_on_job'] = daily_report['not_on_job_drivers']
                summary['drivers_by_day'][date_str]['on_time'] = daily_report['on_time_drivers']
            
            # Initialize driver attendance tracking
            for driver_name in all_drivers:
                summary['driver_attendance'][driver_name] = {
                    'days_on_time': 0,
                    'days_late': 0,
                    'days_early': 0,
                    'days_not_on_job': 0,
                    'days_present': 0,
                    'attendance_rate': 0,
                    'status_by_day': {}
                }
                
                # Initialize status for each day
                for date_str in date_range:
                    summary['driver_attendance'][driver_name]['status_by_day'][date_str] = 'Not Tracked'
            
            # Initialize job site tracking
            for job_site in all_job_sites:
                summary['job_site_attendance'][job_site] = {
                    'total_assignments': 0,
                    'days_with_late_starts': 0,
                    'days_with_early_ends': 0,
                    'days_with_no_shows': 0,
                    'attendance_by_day': {}
                }
                
                # Initialize attendance for each day
                for date_str in date_range:
                    summary['job_site_attendance'][job_site]['attendance_by_day'][date_str] = {
                        'assigned': 0,
                        'on_time': 0,
                        'late': 0,
                        'early': 0,
                        'not_on_job': 0
                    }
            
            # Update driver and job site data
            for date_str, daily_report in self.daily_reports.items():
                for driver_name, driver_record in daily_report['driver_records'].items():
                    # Update driver attendance
                    if driver_record['status'] == 'On Time':
                        summary['driver_attendance'][driver_name]['days_on_time'] += 1
                        summary['driver_attendance'][driver_name]['days_present'] += 1
                        summary['driver_attendance'][driver_name]['status_by_day'][date_str] = 'On Time'
                    
                    elif driver_record['status'] == 'Late Start':
                        summary['driver_attendance'][driver_name]['days_late'] += 1
                        summary['driver_attendance'][driver_name]['days_present'] += 1
                        summary['driver_attendance'][driver_name]['status_by_day'][date_str] = 'Late Start'
                    
                    elif driver_record['status'] == 'Early End':
                        summary['driver_attendance'][driver_name]['days_early'] += 1
                        summary['driver_attendance'][driver_name]['days_present'] += 1
                        summary['driver_attendance'][driver_name]['status_by_day'][date_str] = 'Early End'
                    
                    elif driver_record['status'] == 'Not On Job':
                        summary['driver_attendance'][driver_name]['days_not_on_job'] += 1
                        summary['driver_attendance'][driver_name]['status_by_day'][date_str] = 'Not On Job'
                    
                    # Update job site attendance
                    job_site = driver_record['job_site']
                    if job_site != "Unknown" and job_site in summary['job_site_attendance']:
                        summary['job_site_attendance'][job_site]['total_assignments'] += 1
                        summary['job_site_attendance'][job_site]['attendance_by_day'][date_str]['assigned'] += 1
                        
                        if driver_record['status'] == 'On Time':
                            summary['job_site_attendance'][job_site]['attendance_by_day'][date_str]['on_time'] += 1
                        
                        elif driver_record['status'] == 'Late Start':
                            summary['job_site_attendance'][job_site]['attendance_by_day'][date_str]['late'] += 1
                            summary['job_site_attendance'][job_site]['days_with_late_starts'] += 1
                        
                        elif driver_record['status'] == 'Early End':
                            summary['job_site_attendance'][job_site]['attendance_by_day'][date_str]['early'] += 1
                            summary['job_site_attendance'][job_site]['days_with_early_ends'] += 1
                        
                        elif driver_record['status'] == 'Not On Job':
                            summary['job_site_attendance'][job_site]['attendance_by_day'][date_str]['not_on_job'] += 1
                            summary['job_site_attendance'][job_site]['days_with_no_shows'] += 1
            
            # Calculate attendance rates for drivers
            for driver_name in summary['driver_attendance']:
                driver_data = summary['driver_attendance'][driver_name]
                total_tracked_days = len([day for day, status in driver_data['status_by_day'].items() if status != 'Not Tracked'])
                
                if total_tracked_days > 0:
                    driver_data['attendance_rate'] = round((driver_data['days_present'] / total_tracked_days) * 100)
            
            # Find chronic issues
            driver_issues = {
                'late_starts': defaultdict(int),
                'early_ends': defaultdict(int),
                'not_on_job': defaultdict(int)
            }
            
            for date_str in date_range:
                for driver in summary['drivers_by_day'][date_str]['late_start']:
                    driver_issues['late_starts'][driver] += 1
                
                for driver in summary['drivers_by_day'][date_str]['early_end']:
                    driver_issues['early_ends'][driver] += 1
                
                for driver in summary['drivers_by_day'][date_str]['not_on_job']:
                    driver_issues['not_on_job'][driver] += 1
            
            # Drivers with multiple issues
            for issue_type, driver_counts in driver_issues.items():
                for driver, count in driver_counts.items():
                    if count >= 2:  # 2 or more occurrences is considered chronic
                        summary['chronic_issues'][issue_type].append({
                            'name': driver,
                            'count': count
                        })
            
            # Sort chronic issues by count
            for issue_type in summary['chronic_issues']:
                summary['chronic_issues'][issue_type].sort(key=lambda x: x['count'], reverse=True)
            
            # Calculate overall totals
            summary['total_drivers'] = len(all_drivers)
            summary['total_job_sites'] = len(all_job_sites)
            
            total_late = sum(day_data['late_start'] for day_data in summary['status_by_day'].values())
            total_early = sum(day_data['early_end'] for day_data in summary['status_by_day'].values())
            total_not_on_job = sum(day_data['not_on_job'] for day_data in summary['status_by_day'].values())
            total_on_time = sum(day_data['on_time'] for day_data in summary['status_by_day'].values())
            total_tracked = total_late + total_early + total_not_on_job + total_on_time
            
            summary['attendance_totals'] = {
                'late_starts': total_late,
                'early_ends': total_early,
                'not_on_job': total_not_on_job,
                'on_time': total_on_time,
                'total_tracked': total_tracked
            }
            
            if total_tracked > 0:
                summary['attendance_percentages'] = {
                    'late_starts': round((total_late / total_tracked) * 100),
                    'early_ends': round((total_early / total_tracked) * 100),
                    'not_on_job': round((total_not_on_job / total_tracked) * 100),
                    'on_time': round((total_on_time / total_tracked) * 100)
                }
            else:
                summary['attendance_percentages'] = {
                    'late_starts': 0,
                    'early_ends': 0,
                    'not_on_job': 0,
                    'on_time': 0
                }
            
            # Update class variable
            self.weekly_summary = summary
            
            logger.info(f"Generated weekly summary with {summary['total_drivers']} drivers across {len(date_range)} days")
            return summary
        
        except Exception as e:
            logger.error(f"Error generating weekly summary: {e}")
            return {}
    
    def process(self):
        """
        Process all data and generate reports
        
        Returns:
            dict: Processed weekly report
        """
        logger.info(f"Processing weekly report for {self.start_date} to {self.end_date}")
        
        try:
            # Process each day in the range
            date_range = self.get_date_range()
            
            for date_str in date_range:
                daily_report = self.process_daily_report(date_str)
                
                if daily_report:
                    self.daily_reports[date_str] = daily_report
                    
                    # Save daily report to file
                    daily_report_dir = os.path.join(self.reports_dir, date_str)
                    os.makedirs(daily_report_dir, exist_ok=True)
                    
                    with open(os.path.join(daily_report_dir, f"driver_report_{date_str}.json"), 'w') as f:
                        json.dump(daily_report, f, indent=2)
            
            # Generate weekly summary
            weekly_summary = self.generate_weekly_summary()
            
            # Create full weekly report
            weekly_report = {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'generated_at': datetime.now().isoformat(),
                'daily_reports': self.daily_reports,
                'summary': weekly_summary
            }
            
            # Save weekly report
            weekly_report_path = os.path.join(self.reports_dir, f"weekly_{self.start_date}_to_{self.end_date}.json")
            with open(weekly_report_path, 'w') as f:
                json.dump(weekly_report, f, indent=2)
            
            logger.info(f"Weekly report generated and saved to {weekly_report_path}")
            return weekly_report
        
        except Exception as e:
            logger.error(f"Error processing weekly report: {e}")
            return None

# Helper function for CLI usage
def process_weekly_report(start_date, end_date, driving_history_path=None, activity_detail_path=None, 
                           time_on_site_path=None, timecard_paths=None, from_attached_assets=False):
    """
    Process a weekly driver report from the command line
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        driving_history_path (str): Path to driving history CSV
        activity_detail_path (str): Path to activity detail CSV
        time_on_site_path (str): Path to time on site CSV
        timecard_paths (list): List of paths to timecard Excel files
        from_attached_assets (bool): Whether to load from attached_assets folder
        
    Returns:
        dict: Processed weekly report
    """
    processor = WeeklyDriverProcessor(start_date, end_date)
    processor.load_files(
        driving_history_path=driving_history_path,
        activity_detail_path=activity_detail_path,
        time_on_site_path=time_on_site_path,
        timecard_paths=timecard_paths,
        from_attached_assets=from_attached_assets
    )
    return processor.process()

if __name__ == "__main__":
    # Example usage
    weekly_report = process_weekly_report(
        start_date="2025-05-18",
        end_date="2025-05-23",
        driving_history_path="DrivingHistory (19).csv",
        activity_detail_path="ActivityDetail (13).csv",
        time_on_site_path="AssetsTimeOnSite (8).csv",
        from_attached_assets=True
    )
    
    if weekly_report:
        logger.info(f"Successfully processed weekly report for {len(weekly_report['daily_reports'])} days")