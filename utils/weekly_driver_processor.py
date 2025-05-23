"""
TRAXORA Fleet Management System - Weekly Driver Processor

This module provides functionality for processing weekly driver reports from various data sources.
It combines data from driving history, time on site, activity detail, and timecard files to generate
comprehensive weekly driver attendance reports.
"""

import os
import csv
import json
import logging
import pandas as pd
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class WeeklyDriverProcessor:
    """
    Processor for weekly driver reports that combines data from multiple sources
    to generate comprehensive attendance reports for a week.
    """
    
    def __init__(self, start_date, end_date):
        """
        Initialize the weekly driver processor.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
        """
        self.start_date = start_date
        self.end_date = end_date
        self.driving_history_path = None
        self.activity_detail_path = None
        self.time_on_site_path = None
        self.timecard_paths = []
        
        self.driving_history_data = []
        self.activity_detail_data = []
        self.time_on_site_data = []
        self.timecard_data = []
        
        self.start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        self.date_range = self._generate_date_range()
        
        # Initialize data structures
        self.driver_data = {}  # Maps drivers to their daily attendance records
        self.job_data = {}     # Maps job sites to their daily driver records
        self.daily_reports = {}  # Daily report data by date
        
        # Debug info
        logger.info(f"Weekly Driver Processor initialized for date range: {self.start_date} to {self.end_date}")
        logger.info(f"Date range contains {len(self.date_range)} days")
        
        logger.info(f"Initialized Weekly Driver Processor for {start_date} to {end_date}")
    
    def _generate_date_range(self):
        """Generate a list of dates in the range (inclusive)"""
        date_range = []
        current_date = self.start_datetime
        while current_date <= self.end_datetime:
            date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        return date_range
    
    def load_files(self, driving_history_path=None, activity_detail_path=None, 
                  time_on_site_path=None, timecard_paths=None):
        """
        Load data files for processing.
        
        Args:
            driving_history_path (str): Path to driving history CSV file
            activity_detail_path (str): Path to activity detail CSV file
            time_on_site_path (str): Path to time on site CSV file
            timecard_paths (list): List of paths to timecard Excel files
        """
        self.driving_history_path = driving_history_path
        self.activity_detail_path = activity_detail_path
        self.time_on_site_path = time_on_site_path
        self.timecard_paths = timecard_paths or []
        
        # Load driving history data
        if driving_history_path and os.path.exists(driving_history_path):
            logger.info(f"Loading driving history data from {driving_history_path}")
            self.driving_history_data = self._load_csv_file(driving_history_path)
        
        # Load activity detail data
        if activity_detail_path and os.path.exists(activity_detail_path):
            logger.info(f"Loading activity detail data from {activity_detail_path}")
            self.activity_detail_data = self._load_csv_file(activity_detail_path)
        
        # Load time on site data
        if time_on_site_path and os.path.exists(time_on_site_path):
            logger.info(f"Loading time on site data from {time_on_site_path}")
            self.time_on_site_data = self._load_csv_file(time_on_site_path)
        
        # Load timecard data
        for timecard_path in self.timecard_paths:
            if os.path.exists(timecard_path):
                logger.info(f"Loading timecard data from {timecard_path}")
                try:
                    timecard_data = pd.read_excel(timecard_path)
                    self.timecard_data.append(timecard_data)
                except Exception as e:
                    logger.error(f"Error loading timecard file {timecard_path}: {str(e)}")
    
    def _load_csv_file(self, file_path):
        """
        Load a CSV file into a list of dictionaries.
        
        Args:
            file_path (str): Path to the CSV file
            
        Returns:
            list: List of dictionaries with the CSV data
        """
        try:
            # Check if this is a Gauge CSV file with metadata at the top
            from utils.csv_parser_fix import parse_gauge_csv, parse_time_on_site_csv
            
            # Determine file type based on filename
            if 'DrivingHistory' in file_path:
                logger.info(f"Using specialized parser for DrivingHistory file: {file_path}")
                return parse_gauge_csv(file_path, self.date_range)
            elif 'ActivityDetail' in file_path:
                logger.info(f"Using specialized parser for ActivityDetail file: {file_path}")
                return parse_gauge_csv(file_path, self.date_range)
            elif 'TimeOnSite' in file_path:
                logger.info(f"Using specialized parser for TimeOnSite file: {file_path}")
                return parse_time_on_site_csv(file_path, self.date_range)
            
            # Default CSV reading for other files
            with open(file_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
                # Try to auto-detect the delimiter
                dialect = csv.Sniffer().sniff(csvfile.read(4096))
                csvfile.seek(0)
                
                # Read the CSV file
                reader = csv.DictReader(csvfile, dialect=dialect)
                data = list(reader)
                
                # 🚨 STRICT COLUMN ENFORCEMENT WITH FIELD MAPPING
                if data and len(data) > 0:
                    # Map alternative field names to our required ones
                    column_mappings = {
                        "Contact": ["Driver", "Driver Name", "DriverName"],
                        "Locationx": ["Location", "JobSite", "Jobsite", "Job Site", "Job"],
                        "EventDateTime": ["DateTime", "Timestamp", "Time", "EventDateTimex"]
                    }
                    
                    # Apply field mappings to standardize columns
                    for row in data:
                        for target_col, source_cols in column_mappings.items():
                            # If target column is missing but an alternative exists, map it
                            if target_col not in row or not row[target_col]:
                                for source_col in source_cols:
                                    if source_col in row and row[source_col]:
                                        row[target_col] = row[source_col]
                                        break
                    
                    # Verify required columns exist after mapping
                    required_cols = ["Contact", "Locationx", "EventDateTime"]
                    sample_row = data[0]  # Use first row after mapping
                    
                    # Check for missing columns
                    missing = []
                    for col in required_cols:
                        if col not in sample_row or not sample_row[col]:
                            missing.append(col)
                    
                    if missing:
                        available_cols = list(sample_row.keys())
                        logger.error(f"Missing required columns after mapping: {missing}")
                        logger.error(f"Available columns: {available_cols}")
                        raise ValueError(f"Missing required columns: {missing}")
                    
                    logger.info(f"📄 [VALID] Processing {len(data)} rows with required columns Contact+Locationx+EventDateTime")
                
                return data
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {str(e)}")
            return []
    
    def process(self):
        """
        Process the loaded data and generate a weekly driver report.
        
        Returns:
            dict: Weekly driver report data
        """
        logger.info("Starting weekly driver report processing")
        
        # Process each date in the range
        for date_str in self.date_range:
            logger.info(f"Processing data for date: {date_str}")
            daily_data = self._process_daily_data(date_str)
            self.daily_reports[date_str] = daily_data
        
        # Generate summary data
        summary = self._generate_summary()
        
        # Return the complete report
        report = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'daily_reports': self.daily_reports,
            'summary': summary,
            'driver_data': self.driver_data,
            'job_data': self.job_data
        }
        
        logger.info("Weekly driver report processing complete")
        return report
    
    def _process_daily_data(self, date_str):
        """
        Process data for a specific date.
        
        Args:
            date_str (str): Date string in YYYY-MM-DD format
            
        Returns:
            dict: Daily report data
        """
        # Filter data for the specific date
        driving_records = self._filter_driving_records(date_str)
        activity_records = self._filter_activity_records(date_str)
        time_on_site_records = self._filter_time_on_site_records(date_str)
        timecard_records = self._filter_timecard_records(date_str)
        
        # Process driver attendance for the day
        drivers = self._get_all_drivers(driving_records, activity_records, time_on_site_records)
        
        # Initialize daily report data
        daily_report = {
            'date': date_str,
            'drivers': {},
            'driver_records': [],  # List of driver records for the view template
            'job_sites': {},
            'attendance': {
                'on_time': 0,
                'late_start': 0,
                'early_end': 0,
                'not_on_job': 0,
                'total': 0
            }
        }
        
        # Process each driver
        for driver_name in drivers:
            driver_record = self._process_driver(driver_name, date_str, driving_records, 
                                               activity_records, time_on_site_records)
            
            # Skip drivers with no data for this day
            if not driver_record:
                continue
            
            # Add driver to daily report
            daily_report['drivers'][driver_name] = driver_record
            
            # Add to driver_records list (used by the view template)
            formatted_record = {
                'driver_name': driver_name,
                'attendance_status': driver_record.get('status', 'unknown'),
                'job_site': driver_record.get('job_site', 'Unknown'),
                'first_seen': driver_record.get('first_seen', ''),
                'last_seen': driver_record.get('last_seen', ''),
                'total_time': driver_record.get('total_time', 0)
            }
            daily_report['driver_records'].append(formatted_record)
            
            # Update job site data
            job_site = driver_record.get('job_site')
            if job_site:
                if job_site not in daily_report['job_sites']:
                    daily_report['job_sites'][job_site] = {
                        'drivers': [],
                        'attendance': {
                            'on_time': 0,
                            'late_start': 0,
                            'early_end': 0,
                            'not_on_job': 0,
                            'total': 0
                        }
                    }
                
                daily_report['job_sites'][job_site]['drivers'].append(driver_name)
                status = driver_record.get('status', 'unknown')
                if status in daily_report['job_sites'][job_site]['attendance']:
                    daily_report['job_sites'][job_site]['attendance'][status] += 1
                daily_report['job_sites'][job_site]['attendance']['total'] += 1
            
            # Update daily attendance counters
            status = driver_record.get('status', 'unknown')
            if status in daily_report['attendance']:
                daily_report['attendance'][status] += 1
            daily_report['attendance']['total'] += 1
            
            # Update driver data for the week
            if driver_name not in self.driver_data:
                self.driver_data[driver_name] = {
                    'days': {},
                    'summary': {
                        'on_time': 0,
                        'late_start': 0,
                        'early_end': 0,
                        'not_on_job': 0,
                        'total': 0
                    }
                }
            
            self.driver_data[driver_name]['days'][date_str] = driver_record
            status = driver_record.get('status', 'unknown')
            if status in self.driver_data[driver_name]['summary']:
                self.driver_data[driver_name]['summary'][status] += 1
            self.driver_data[driver_name]['summary']['total'] += 1
        
        # Log how many driver records we found for debugging
        logger.info(f"Date {date_str}: Processed {len(daily_report['driver_records'])} driver records")
        
        # Log a few sample driver names for verification if we have any
        if daily_report['driver_records']:
            sample_drivers = [rec['driver_name'] for rec in daily_report['driver_records'][:5]]
            logger.info(f"Date {date_str}: Sample drivers: {', '.join(sample_drivers)}")
        else:
            logger.warning(f"Date {date_str}: No driver records found")
            
        return daily_report
    
    def _filter_driving_records(self, date_str):
        """Filter driving history records for a specific date"""
        filtered_records = []
        logger.debug(f"Filtering driving records for date: {date_str}")
        
        # Print sample of first few records for debugging
        if self.driving_history_data and len(self.driving_history_data) > 0:
            logger.debug(f"Sample driving record: {self.driving_history_data[0]}")
        
        for record in self.driving_history_data:
            # Check if record has a timestamp field
            timestamp = record.get('Timestamp')
            if not timestamp:
                continue
            
            # Try multiple date formats
            try:
                # Try to extract just the date portion if timestamp includes time
                if ' ' in timestamp:
                    date_part = timestamp.split(' ')[0]
                else:
                    date_part = timestamp
                
                # Try different date formats
                formats_to_try = ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']
                
                for date_format in formats_to_try:
                    try:
                        record_date = datetime.strptime(date_part, date_format)
                        if record_date.strftime('%Y-%m-%d') == date_str:
                            filtered_records.append(record)
                            break
                    except ValueError:
                        continue
                        
            except (ValueError, IndexError) as e:
                logger.debug(f"Could not parse timestamp: {timestamp} - {str(e)}")
                pass
        
        logger.debug(f"Found {len(filtered_records)} driving records for date {date_str}")
        return filtered_records
    
    def _filter_activity_records(self, date_str):
        """Filter activity detail records for a specific date"""
        filtered_records = []
        logger.debug(f"Filtering activity records for date: {date_str}")
        
        # Print sample of first few records for debugging
        if self.activity_detail_data and len(self.activity_detail_data) > 0:
            logger.debug(f"Sample activity record: {self.activity_detail_data[0]}")
            
        for record in self.activity_detail_data:
            # Check if record has a timestamp field
            timestamp = record.get('Timestamp')
            if not timestamp:
                continue
            
            # Try multiple date formats
            try:
                # Try to extract just the date portion if timestamp includes time
                if ' ' in timestamp:
                    date_part = timestamp.split(' ')[0]
                else:
                    date_part = timestamp
                
                # Try different date formats
                formats_to_try = ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']
                
                for date_format in formats_to_try:
                    try:
                        record_date = datetime.strptime(date_part, date_format)
                        if record_date.strftime('%Y-%m-%d') == date_str:
                            filtered_records.append(record)
                            break
                    except ValueError:
                        continue
                        
            except (ValueError, IndexError) as e:
                logger.debug(f"Could not parse timestamp: {timestamp} - {str(e)}")
                pass
                
        logger.debug(f"Found {len(filtered_records)} activity records for date {date_str}")
        return filtered_records
    
    def _filter_time_on_site_records(self, date_str):
        """Filter time on site records for a specific date"""
        filtered_records = []
        logger.debug(f"Filtering time on site records for date: {date_str}")
        
        # Print sample of first few records for debugging
        if self.time_on_site_data and len(self.time_on_site_data) > 0:
            logger.debug(f"Sample time on site record: {self.time_on_site_data[0]}")
            
        for record in self.time_on_site_data:
            # Check if record has a timestamp field
            timestamp = record.get('Timestamp')
            if not timestamp:
                continue
            
            # Try multiple date formats
            try:
                # Try to extract just the date portion if timestamp includes time
                if ' ' in timestamp:
                    date_part = timestamp.split(' ')[0]
                else:
                    date_part = timestamp
                
                # Try different date formats
                formats_to_try = ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']
                
                for date_format in formats_to_try:
                    try:
                        record_date = datetime.strptime(date_part, date_format)
                        if record_date.strftime('%Y-%m-%d') == date_str:
                            filtered_records.append(record)
                            break
                    except ValueError:
                        continue
                        
            except (ValueError, IndexError) as e:
                logger.debug(f"Could not parse timestamp: {timestamp} - {str(e)}")
                pass
                
        logger.debug(f"Found {len(filtered_records)} time on site records for date {date_str}")
        return filtered_records
    
    def _filter_timecard_records(self, date_str):
        """Filter timecard records for a specific date"""
        filtered_records = []
        for timecard_df in self.timecard_data:
            try:
                # Check if the dataframe has date columns
                date_col = None
                for col in timecard_df.columns:
                    if 'date' in col.lower():
                        date_col = col
                        break
                
                if date_col:
                    # Filter by date
                    for _, row in timecard_df.iterrows():
                        record_date = row[date_col]
                        if isinstance(record_date, str):
                            try:
                                record_date = datetime.strptime(record_date, '%Y-%m-%d')
                            except ValueError:
                                continue
                        
                        if record_date.strftime('%Y-%m-%d') == date_str:
                            filtered_records.append(row.to_dict())
            except Exception as e:
                logger.error(f"Error filtering timecard records: {str(e)}")
        
        return filtered_records
    
    def _get_all_drivers(self, driving_records, activity_records, time_on_site_records):
        """Get a set of all drivers from the records"""
        drivers = set()
        
        # Extract drivers from driving records (check both Driver and Contact fields)
        for record in driving_records:
            driver_name = record.get('Driver') or record.get('Contact') or record.get('Driver Name')
            if driver_name:
                # Extract driver name from various formats
                cleaned_name = self._extract_driver_name(driver_name)
                if cleaned_name:
                    drivers.add(cleaned_name)
        
        # Extract drivers from activity records (check both Driver and Contact fields)
        for record in activity_records:
            driver_name = record.get('Driver') or record.get('Contact') or record.get('Driver Name')
            if driver_name:
                cleaned_name = self._extract_driver_name(driver_name)
                if cleaned_name:
                    drivers.add(cleaned_name)
        
        # Extract drivers from time on site records (check both Driver and Contact fields)
        for record in time_on_site_records:
            driver_name = record.get('Driver') or record.get('Contact') or record.get('Driver Name')
            if driver_name:
                cleaned_name = self._extract_driver_name(driver_name)
                if cleaned_name:
                    drivers.add(cleaned_name)
        
        # If no drivers found, use weekly report data
        if len(drivers) == 0 and hasattr(self, 'weekly_report_data'):
            for date, daily_data in self.weekly_report_data.get('daily_reports', {}).items():
                for driver_name in daily_data.get('drivers', {}).keys():
                    if driver_name and driver_name != "Unknown":
                        drivers.add(driver_name)
        
        return drivers
    
    def _extract_driver_name(self, name_field):
        """
        Extract driver name from various formats:
        - 'Ammar Elhamad (210003)'
        - 'Ammar Elhamad'
        - etc.
        
        Args:
            name_field (str): Driver or Contact field from CSV
            
        Returns:
            str: Cleaned driver name or None
        """
        if not name_field or not isinstance(name_field, str):
            return None
            
        # Remove phone numbers and extra info, extract name portion
        if '(' in name_field:
            name_part = name_field.split('(')[0].strip()
        else:
            name_part = name_field.strip()
            
        # Basic validation - must have at least first and last name
        if len(name_part.split()) >= 2:
            return name_part
            
        return None
    
    def _process_driver(self, driver_name, date_str, driving_records, activity_records, time_on_site_records):
        """
        Process driver data for a specific date.
        
        Args:
            driver_name (str): Driver name
            date_str (str): Date string in YYYY-MM-DD format
            driving_records (list): Filtered driving records for the date
            activity_records (list): Filtered activity records for the date
            time_on_site_records (list): Filtered time on site records for the date
            
        Returns:
            dict: Driver record with attendance classification
        """
        # Filter records for this driver using Contact field and extract driver names
        driver_driving_records = []
        for r in driving_records:
            contact = r.get('Contact', '')
            extracted_name = self._extract_driver_name(contact)
            if extracted_name == driver_name:
                driver_driving_records.append(r)
        
        driver_activity_records = []
        for r in activity_records:
            contact = r.get('Contact', '')
            extracted_name = self._extract_driver_name(contact)
            if extracted_name == driver_name:
                driver_activity_records.append(r)
        
        driver_time_on_site = []
        for r in time_on_site_records:
            contact = r.get('Contact', '')
            extracted_name = self._extract_driver_name(contact)
            if extracted_name == driver_name:
                driver_time_on_site.append(r)
        
        # Skip if no records found for this driver
        if not driver_driving_records and not driver_activity_records and not driver_time_on_site:
            return None
        
        # Extract key data points
        first_seen = None
        last_seen = None
        job_site = None
        
        # Process driving records - check multiple field names
        if driver_driving_records:
            # Try different timestamp field names
            timestamps = []
            for r in driver_driving_records:
                timestamp = (r.get('EventDateTime') or r.get('DateTime') or 
                            r.get('Timestamp') or r.get('Time'))
                if timestamp:
                    timestamps.append(timestamp)
            
            # Try different location field names
            locations = []
            for r in driver_driving_records:
                location = (r.get('Location') or r.get('Locationx') or 
                           r.get('JobSite') or r.get('Jobsite') or 
                           r.get('Job Site') or r.get('Job'))
                if location and isinstance(location, str) and location.strip():
                    locations.append(location.strip())
            
            if timestamps:
                timestamps.sort()
                if not first_seen or timestamps[0] < first_seen:
                    first_seen = timestamps[0]
                if not last_seen or timestamps[-1] > last_seen:
                    last_seen = timestamps[-1]
            
            if locations:
                # Use the most common location as the job site
                location_counts = {}
                for loc in locations:
                    location_counts[loc] = location_counts.get(loc, 0) + 1
                
                if location_counts:
                    job_site = max(location_counts.items(), key=lambda x: x[1])[0]
        
        # Process activity records - check multiple field names
        if driver_activity_records:
            # Try different timestamp field names
            timestamps = []
            for r in driver_activity_records:
                timestamp = (r.get('EventDateTimex') or r.get('EventDateTime') or 
                            r.get('DateTime') or r.get('Timestamp') or r.get('Time'))
                if timestamp:
                    timestamps.append(timestamp)
            
            # Try different location field names
            locations = []
            for r in driver_activity_records:
                location = (r.get('Locationx') or r.get('Location') or 
                           r.get('JobSite') or r.get('Jobsite') or 
                           r.get('Job Site') or r.get('Job'))
                if location and isinstance(location, str) and location.strip():
                    locations.append(location.strip())
            
            if timestamps:
                timestamps.sort()
                if not first_seen or timestamps[0] < first_seen:
                    first_seen = timestamps[0]
                if not last_seen or timestamps[-1] > last_seen:
                    last_seen = timestamps[-1]
            
            if locations and not job_site:
                # Use the most common location as the job site
                location_counts = {}
                for loc in locations:
                    location_counts[loc] = location_counts.get(loc, 0) + 1
                
                if location_counts:
                    job_site = max(location_counts.items(), key=lambda x: x[1])[0]
        
        # Process time on site records - check multiple field names
        if driver_time_on_site:
            # Try different timestamp field names
            timestamps = []
            for r in driver_time_on_site:
                timestamp = (r.get('EventDateTime') or r.get('DateTime') or 
                            r.get('Timestamp') or r.get('Time'))
                if timestamp:
                    timestamps.append(timestamp)
            
            # Try different location field names
            locations = []
            for r in driver_time_on_site:
                location = (r.get('Jobsite') or r.get('JobSite') or r.get('Location') or
                           r.get('Locationx') or r.get('Job Site') or r.get('Job'))
                if location and isinstance(location, str) and location.strip():
                    locations.append(location.strip())
            
            if timestamps:
                timestamps.sort()
                if not first_seen or timestamps[0] < first_seen:
                    first_seen = timestamps[0]
                if not last_seen or timestamps[-1] > last_seen:
                    last_seen = timestamps[-1]
            
            if locations and not job_site:
                # Use the most common location as the job site
                location_counts = {}
                for loc in locations:
                    location_counts[loc] = location_counts.get(loc, 0) + 1
                
                if location_counts:
                    job_site = max(location_counts.items(), key=lambda x: x[1])[0]
                    
        # Default job site if none was found in any of the records
        if not job_site:
            job_site = "Job Site Pending"
        
        # Skip if no timestamps found
        if not first_seen or not last_seen:
            return None
        
        # Parse timestamps
        try:
            first_seen_time = datetime.strptime(first_seen, '%Y-%m-%d %H:%M:%S')
            last_seen_time = datetime.strptime(last_seen, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return None
        
        # Create driver record
        driver_record = {
            'name': driver_name,
            'job_site': job_site,
            'first_seen': first_seen,
            'last_seen': last_seen,
            'first_seen_time': first_seen_time.strftime('%H:%M:%S'),
            'last_seen_time': last_seen_time.strftime('%H:%M:%S'),
            'hours_on_site': (last_seen_time - first_seen_time).total_seconds() / 3600
        }
        
        # Classify driver attendance
        driver_record['status'] = self._classify_driver_attendance(driver_record)
        
        # Debug logging for field mapping verification
        logger.info(f"FIELD MAPPING DEBUG - Driver: {driver_name}")
        logger.info(f"  Job Site Found: {job_site}")
        logger.info(f"  Driving Records: {len(driver_driving_records)}")
        logger.info(f"  Activity Records: {len(driver_activity_records)}")
        logger.info(f"  Time on Site Records: {len(driver_time_on_site)}")
        logger.info(f"  Classification: {driver_record['status']}")
        
        return driver_record
    
    def _classify_driver_attendance(self, driver_record):
        """
        Classify driver attendance based on time and location data.
        
        Args:
            driver_record (dict): Driver record with attendance data
            
        Returns:
            str: Attendance classification (on_time, late_start, early_end, not_on_job)
        """
        first_seen_time = driver_record.get('first_seen_time')
        last_seen_time = driver_record.get('last_seen_time')
        job_site = driver_record.get('job_site')
        hours_on_site = driver_record.get('hours_on_site', 0)
        
        # STRICT CLASSIFICATION - NO DEFAULTS
        # First evaluate if driver was on job site
        if not job_site or job_site == "Job Site Pending":
            logger.warning(f"Driver classified as NOT_ON_JOB due to missing job site")
            return 'not_on_job'
        
        # Then evaluate arrival time (late start check)
        if first_seen_time and first_seen_time > '07:30:00':
            minutes_late = (datetime.strptime(first_seen_time, '%H:%M:%S') - 
                           datetime.strptime('07:30:00', '%H:%M:%S')).total_seconds() / 60
            logger.info(f"Driver classified as LATE_START - {minutes_late:.1f} minutes late")
            return 'late_start'
        
        # Then evaluate departure time (early end check)
        if last_seen_time and last_seen_time < '16:00:00':
            minutes_early = (datetime.strptime('16:00:00', '%H:%M:%S') - 
                            datetime.strptime(last_seen_time, '%H:%M:%S')).total_seconds() / 60
            logger.info(f"Driver classified as EARLY_END - {minutes_early:.1f} minutes early")
            return 'early_end'
        
        # Check total hours (sanity check for early leave)
        if hours_on_site < 7:
            logger.info(f"Driver classified as EARLY_END - Only {hours_on_site:.1f} hours on site")
            return 'early_end'
        
        # Only if all other conditions are not met, classify as on time
        logger.info(f"Driver classified as ON_TIME ✓")
        return 'on_time'
    
    def _generate_summary(self):
        """
        Generate summary data for the weekly report.
        
        Returns:
            dict: Summary data
        """
        # Initialize summary data
        summary = {
            'total_drivers': len(self.driver_data),
            'attendance_totals': {
                'late_start': 0,
                'early_end': 0,
                'not_on_job': 0,
                'on_time': 0,
                'total_tracked': 0
            },
            'attendance_percentages': {
                'late_start': 0,
                'early_end': 0,
                'not_on_job': 0,
                'on_time': 0
            },
            'daily_totals': {}
        }
        
        # Count attendance by day
        for date_str, daily_report in self.daily_reports.items():
            summary['daily_totals'][date_str] = daily_report['attendance']
            
            # Add to weekly totals
            summary['attendance_totals']['late_start'] += daily_report['attendance']['late_start']
            summary['attendance_totals']['early_end'] += daily_report['attendance']['early_end']
            summary['attendance_totals']['not_on_job'] += daily_report['attendance']['not_on_job']
            summary['attendance_totals']['on_time'] += daily_report['attendance']['on_time']
            summary['attendance_totals']['total_tracked'] += daily_report['attendance']['total']
        
        # Calculate percentages
        total = summary['attendance_totals']['total_tracked']
        if total > 0:
            summary['attendance_percentages']['late_start'] = round(summary['attendance_totals']['late_start'] / total * 100)
            summary['attendance_percentages']['early_end'] = round(summary['attendance_totals']['early_end'] / total * 100)
            summary['attendance_percentages']['not_on_job'] = round(summary['attendance_totals']['not_on_job'] / total * 100)
            summary['attendance_percentages']['on_time'] = round(summary['attendance_totals']['on_time'] / total * 100)
        
        return summary


def process_weekly_report(start_date, end_date, driving_history_path=None, activity_detail_path=None,
                         time_on_site_path=None, timecard_paths=None, from_attached_assets=False):
    """
    Process a weekly driver report for the specified date range.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        driving_history_path (str): Path to the driving history CSV file
        activity_detail_path (str): Path to the activity detail CSV file
        time_on_site_path (str): Path to the time on site CSV file
        timecard_paths (list): List of paths to timecard Excel files
        from_attached_assets (bool): Whether the file paths are relative to the attached_assets directory
        
    Returns:
        dict: Weekly driver report data
    """
    # Convert relative paths to absolute paths if needed
    if from_attached_assets:
        attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
        
        if driving_history_path:
            driving_history_path = os.path.join(attached_assets_dir, driving_history_path)
        
        if activity_detail_path:
            activity_detail_path = os.path.join(attached_assets_dir, activity_detail_path)
        
        if time_on_site_path:
            time_on_site_path = os.path.join(attached_assets_dir, time_on_site_path)
        
        if timecard_paths:
            timecard_paths = [os.path.join(attached_assets_dir, path) for path in timecard_paths]
    
    # Initialize the processor
    processor = WeeklyDriverProcessor(start_date, end_date)
    
    # Load the files
    processor.load_files(
        driving_history_path=driving_history_path,
        activity_detail_path=activity_detail_path,
        time_on_site_path=time_on_site_path,
        timecard_paths=timecard_paths
    )
    
    # Process the data
    return processor.process()