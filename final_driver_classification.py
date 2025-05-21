#!/usr/bin/env python3
"""
TRAXORA GENIUS CORE | Final Driver Classification System

This script implements the final driver classification with proper handling of test data
and correct application of the "Not On Job" classification definition: not in driving history.
It creates a comprehensive report showing real drivers vs. test data.
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
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs/final_classification', exist_ok=True)
classification_log = logging.FileHandler('logs/final_classification/classification.log')
classification_log.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(classification_log)

# Paths
DATA_DIR = 'data'
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
REPORTS_DIR = 'reports/final_classification'
EXPORTS_DIR = 'exports/final_classification'

# Equipment billing workbook
EQUIPMENT_BILLING_PATH = 'attached_assets/EQ MONTHLY BILLINGS WORKING SPREADSHEET - APRIL 2025.xlsx'

# Create directories
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)


class FinalDriverClassification:
    """
    Final driver classification system with proper handling of test data
    and correct application of classification rules.
    """
    
    def __init__(self, date_str):
        """Initialize the final classification system"""
        self.date_str = date_str
        
        # Data sources
        self.asset_list_drivers = {}  # Drivers from Asset List (primary source)
        self.driving_history_drivers = {}  # Drivers from Driving History
        
        # Classification results
        self.classified_drivers = {}
        
        # Test data detection
        self.is_test_data = False
        self.test_drivers = []
        
        # Classification statistics
        self.classification_stats = {
            'total_drivers': 0,
            'on_time': 0,
            'late': 0,
            'early_end': 0,
            'not_on_job': 0,
            'unverified': 0,
            'is_test_data': False,
            'test_drivers_count': 0,
            'real_drivers_count': 0
        }
    
    def normalize_name(self, name):
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
        
        excluded_asset_types = [
            'TRAILER', 'TLR', 'DUMP', 'FLATBED', 'UTILITY', 'LOWBOY', 'EQUIPMENT'
        ]
        
        asset_str = str(asset_id).upper().strip()
        
        # Check if asset ID contains trailer keywords
        for trailer_type in excluded_asset_types:
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
        """Extract driver data from Asset List (primary source of truth)"""
        logger.info("Extracting drivers from Asset List")
        
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
            
            if asset_col and driver_col:
                logger.info(f"Found asset column: {asset_col}, driver column: {driver_col}")
                
                # Process rows
                for _, row in df.iterrows():
                    asset_id = str(row[asset_col]).strip() if pd.notna(row[asset_col]) else None
                    driver_name = str(row[driver_col]).strip() if pd.notna(row[driver_col]) else None
                    
                    # Skip empty or invalid values
                    if not asset_id or not driver_name:
                        continue
                    
                    if asset_id.lower() in ['nan', 'none', 'null', ''] or driver_name.lower() in ['nan', 'none', 'null', '']:
                        continue
                    
                    # Skip trailers
                    if self.is_trailer(asset_id):
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
                    
                    # Create driver record
                    self.asset_list_drivers[normalized_name] = {
                        'name': driver_name,
                        'normalized_name': normalized_name,
                        'asset_id': asset_id.upper(),
                        'job_site': job_site,
                        'in_driving_history': False  # Default to Not On Job (not in driving history)
                    }
                
                logger.info(f"Extracted {len(self.asset_list_drivers)} drivers from Asset List")
                return True
            else:
                logger.error("Required columns not found in Asset List")
                return False
        
        except Exception as e:
            logger.error(f"Error extracting Asset List data: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def extract_driving_history(self):
        """Extract driver data from Driving History"""
        logger.info(f"Extracting drivers from Driving History for {self.date_str}")
        
        # Look for driving history file
        date_formatted = self.date_str.replace('-', '')
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
                logger.error(f"No Driving History file found for date {self.date_str}")
                return False
        
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
            
            if driver_col and asset_col:
                logger.info(f"Found driver column: {driver_col}, asset column: {asset_col}")
                
                # Get unique driver names from Driving History
                unique_drivers = df[driver_col].dropna().unique()
                
                # Process each unique driver
                for driver_name in unique_drivers:
                    if not driver_name or pd.isna(driver_name):
                        continue
                    
                    # Normalize driver name
                    normalized_name = self.normalize_name(driver_name)
                    
                    if not normalized_name:
                        continue
                    
                    # Get asset IDs for this driver
                    driver_rows = df[df[driver_col] == driver_name]
                    asset_ids = driver_rows[asset_col].dropna().unique()
                    
                    # Create driver record
                    self.driving_history_drivers[normalized_name] = {
                        'name': driver_name,
                        'normalized_name': normalized_name,
                        'asset_ids': [str(aid).strip().upper() for aid in asset_ids if pd.notna(aid)]
                    }
                
                # Check if this appears to be test data
                is_test_data = self.detect_test_data()
                if is_test_data:
                    logger.warning("Detected test/sample data in Driving History file")
                    self.is_test_data = True
                    self.test_drivers = list(self.driving_history_drivers.keys())
                
                logger.info(f"Extracted {len(self.driving_history_drivers)} drivers from Driving History")
                logger.info(f"First few drivers: {list(self.driving_history_drivers.keys())[:5]}")
                
                return True
            else:
                logger.error("Required columns not found in Driving History")
                return False
        
        except Exception as e:
            logger.error(f"Error extracting Driving History data: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def detect_test_data(self):
        """
        Detect if the driving history data appears to be test/sample data
        by checking for common test names and no overlap with Asset List
        """
        # Common test names
        test_names = ['john smith', 'jane doe', 'test user', 'demo user', 
                      'michael johnson', 'robert williams', 'james davis']
        
        # Check for overlap between Driving History and Asset List
        dh_names = set(self.driving_history_drivers.keys())
        al_names = set(self.asset_list_drivers.keys())
        
        # If there's no overlap and common test names are present, it's likely test data
        if not dh_names.intersection(al_names):
            # Check if any test names are present
            for name in test_names:
                if any(name in dh_name for dh_name in dh_names):
                    return True
            
            # Check if the first names appear generic
            first_names = []
            for dh_name in dh_names:
                parts = dh_name.split()
                if parts:
                    first_names.append(parts[0])
            
            # Check if all first names are common
            common_first_names = ['john', 'james', 'robert', 'michael', 'william', 'david', 
                                 'thomas', 'joseph', 'charles', 'christopher']
            
            if all(name in common_first_names for name in first_names):
                return True
        
        return False
    
    def classify_drivers(self):
        """
        Classify all drivers according to strict definition:
        - Not On Job: Not present in driving history report
        """
        logger.info("Classifying drivers based on presence in Driving History")
        
        # Reset classification results
        self.classified_drivers = {}
        
        # Reset classification statistics
        self.classification_stats = {
            'total_drivers': len(self.asset_list_drivers),
            'on_time': 0,
            'late': 0,
            'early_end': 0,
            'not_on_job': 0,
            'unverified': 0,
            'is_test_data': self.is_test_data,
            'test_drivers_count': len(self.test_drivers),
            'real_drivers_count': 0
        }
        
        # Process all Asset List drivers
        for normalized_name, driver in self.asset_list_drivers.items():
            # Check if driver is in Driving History
            in_driving_history = normalized_name in self.driving_history_drivers
            
            # Mark driver as in_driving_history
            driver['in_driving_history'] = in_driving_history
            
            # Apply classification based on presence in Driving History
            classification = 'On Time'  # Default for drivers in Driving History
            
            if not in_driving_history:
                # Not On Job definition: Not in driving history report
                classification = 'Not On Job'
                self.classification_stats['not_on_job'] += 1
            else:
                # When driver is in Driving History
                self.classification_stats['on_time'] += 1
                self.classification_stats['real_drivers_count'] += 1
            
            # Create classified driver record
            self.classified_drivers[normalized_name] = {
                'name': driver['name'],
                'normalized_name': normalized_name,
                'asset_id': driver['asset_id'],
                'job_site': driver['job_site'],
                'in_driving_history': in_driving_history,
                'classification': classification,
                'classification_reason': 'Present in Driving History' if in_driving_history else 'Not in Driving History'
            }
        
        # Handle test data case
        if self.is_test_data:
            logger.warning("Using test data handling mode - marking all Asset List drivers as Not On Job")
            
            # When using test data, all real drivers should be Not On Job
            self.classification_stats['on_time'] = 0
            self.classification_stats['not_on_job'] = len(self.asset_list_drivers)
            self.classification_stats['real_drivers_count'] = 0
            
            # Update all driver classifications
            for normalized_name, driver in self.classified_drivers.items():
                driver['classification'] = 'Not On Job'
                driver['classification_reason'] = 'Test data detected - no real drivers in Driving History'
        
        logger.info("Classification statistics:")
        logger.info(f"  Total drivers: {self.classification_stats['total_drivers']}")
        logger.info(f"  On Time: {self.classification_stats['on_time']}")
        logger.info(f"  Not On Job: {self.classification_stats['not_on_job']}")
        logger.info(f"  Test data detected: {self.is_test_data}")
        if self.is_test_data:
            logger.info(f"  Test drivers count: {len(self.test_drivers)}")
        
        return True
    
    def generate_reports(self):
        """Generate comprehensive classification reports"""
        logger.info(f"Generating classification reports for {self.date_str}")
        
        # Create report directories
        os.makedirs(REPORTS_DIR, exist_ok=True)
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        
        # Create file paths
        json_path = os.path.join(REPORTS_DIR, f"driver_classification_{self.date_str}.json")
        excel_path = os.path.join(REPORTS_DIR, f"driver_classification_{self.date_str}.xlsx")
        csv_path = os.path.join(REPORTS_DIR, f"driver_classification_{self.date_str}.csv")
        pdf_path = os.path.join(REPORTS_DIR, f"driver_classification_{self.date_str}.pdf")
        
        try:
            # 1. Generate JSON report
            report_data = {
                'date': self.date_str,
                'generated_at': datetime.now().isoformat(),
                'statistics': self.classification_stats,
                'is_test_data': self.is_test_data,
                'drivers': list(self.classified_drivers.values()),
                'test_drivers': self.test_drivers if self.is_test_data else []
            }
            
            with open(json_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            # 2. Generate CSV report
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Driver Name', 'Asset ID', 'Job Site', 
                    'In Driving History', 'Classification', 'Reason'
                ])
                
                # Write driver data
                for driver in self.classified_drivers.values():
                    writer.writerow([
                        driver['name'],
                        driver['asset_id'],
                        driver['job_site'] or 'N/A',
                        driver['in_driving_history'],
                        driver['classification'],
                        driver['classification_reason']
                    ])
            
            # 3. Generate Excel report
            try:
                # Convert to DataFrame for Excel export
                df_drivers = pd.DataFrame(list(self.classified_drivers.values()))
                
                with pd.ExcelWriter(excel_path) as writer:
                    # Main sheet with all drivers
                    if not df_drivers.empty:
                        # Sort by classification
                        classification_order = {
                            'On Time': 0,
                            'Late': 1,
                            'Early End': 2,
                            'Not On Job': 3
                        }
                        
                        if 'classification' in df_drivers.columns:
                            df_drivers['sort_order'] = df_drivers['classification'].map(
                                lambda x: classification_order.get(x, 999)
                            )
                            df_drivers = df_drivers.sort_values('sort_order')
                            df_drivers = df_drivers.drop('sort_order', axis=1)
                        
                        df_drivers.to_excel(writer, sheet_name='All Drivers', index=False)
                        
                        # Classification-specific sheets
                        for classification in ['On Time', 'Not On Job']:
                            filtered_df = df_drivers[df_drivers['classification'] == classification]
                            if not filtered_df.empty:
                                filtered_df.to_excel(writer, sheet_name=classification, index=False)
                    
                    # Statistics sheet
                    stats_rows = [
                        ['Date', self.date_str],
                        ['Generated At', datetime.now().isoformat()],
                        ['Total Drivers', self.classification_stats['total_drivers']],
                        ['On Time', self.classification_stats['on_time']],
                        ['Not On Job', self.classification_stats['not_on_job']],
                        ['Test Data Detected', 'Yes' if self.is_test_data else 'No']
                    ]
                    
                    if self.is_test_data:
                        stats_rows.append(['Test Drivers Count', len(self.test_drivers)])
                        stats_rows.append(['First Test Drivers', ', '.join(self.test_drivers[:5])])
                    
                    df_stats = pd.DataFrame(stats_rows, columns=['Metric', 'Value'])
                    df_stats.to_excel(writer, sheet_name='Statistics', index=False)
                    
                    # Test data note sheet (if applicable)
                    if self.is_test_data:
                        test_data_note = [
                            ['TEST DATA DETECTED'],
                            [''],
                            ['The system has detected that the Driving History file contains test/sample data.'],
                            [''],
                            ['Key indicators of test data:'],
                            ['- No overlap between Driving History names and Asset List names'],
                            ['- Common test names detected (e.g., John Smith, Michael Johnson)'],
                            [''],
                            ['When test data is detected, all Asset List drivers are classified as "Not On Job"'],
                            ['since they are truly not present in an authentic Driving History report.'],
                            [''],
                            ['To resolve this issue:'],
                            ['1. Replace test data with authentic Driving History exports'],
                            ['2. Ensure driver names in Driving History match Asset List format'],
                            ['3. If name formats differ, use the identity mapper to connect them']
                        ]
                        
                        df_note = pd.DataFrame(test_data_note)
                        df_note.to_excel(writer, sheet_name='Test Data Note', header=False, index=False)
                
                logger.info(f"Generated Excel report at {excel_path}")
                
            except Exception as e:
                logger.error(f"Error generating Excel report: {e}")
                logger.error(traceback.format_exc())
            
            # 4. Generate PDF report (if possible)
            try:
                # Try to use an existing PDF generation module
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
                        logger.info(f"Generated PDF report at {pdf_path}")
                    else:
                        logger.warning("PDF generation module doesn't have generate_pdf_report function")
                else:
                    logger.warning("PDF generation module not found")
            except Exception as e:
                logger.warning(f"Could not generate PDF report: {e}")
            
            # Copy reports to exports directory
            export_json_path = os.path.join(EXPORTS_DIR, f"driver_classification_{self.date_str}.json")
            export_excel_path = os.path.join(EXPORTS_DIR, f"driver_classification_{self.date_str}.xlsx")
            export_csv_path = os.path.join(EXPORTS_DIR, f"driver_classification_{self.date_str}.csv")
            
            shutil.copy(json_path, export_json_path)
            shutil.copy(excel_path, export_excel_path)
            shutil.copy(csv_path, export_csv_path)
            
            if os.path.exists(pdf_path):
                export_pdf_path = os.path.join(EXPORTS_DIR, f"driver_classification_{self.date_str}.pdf")
                shutil.copy(pdf_path, export_pdf_path)
            
            logger.info(f"Generated classification reports for {self.date_str}")
            
            return {
                'json_path': json_path,
                'excel_path': excel_path,
                'csv_path': csv_path,
                'pdf_path': pdf_path if os.path.exists(pdf_path) else None
            }
            
        except Exception as e:
            logger.error(f"Error generating classification reports: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def create_updated_daily_report(self):
        """
        Create an updated daily driver report using the correct classification
        """
        logger.info(f"Creating updated daily driver report for {self.date_str}")
        
        # Paths for updated report
        daily_report_dir = 'reports/daily_drivers'
        daily_exports_dir = 'exports/daily_reports'
        genius_core_dir = 'reports/genius_core'
        
        os.makedirs(daily_report_dir, exist_ok=True)
        os.makedirs(daily_exports_dir, exist_ok=True)
        os.makedirs(genius_core_dir, exist_ok=True)
        
        json_path = os.path.join(daily_report_dir, f"daily_report_{self.date_str}.json")
        excel_path = os.path.join(daily_report_dir, f"daily_report_{self.date_str}.xlsx")
        
        try:
            # Create daily report structure
            report_data = {
                'date': self.date_str,
                'drivers': [],
                'unmatched_drivers': [],
                'summary': {
                    'total': len(self.classified_drivers),
                    'on_time': self.classification_stats['on_time'],
                    'late': self.classification_stats['late'],
                    'early_end': self.classification_stats['early_end'],
                    'not_on_job': self.classification_stats['not_on_job'],
                    'unmatched': 0
                },
                'metadata': {
                    'generated': datetime.now().isoformat(),
                    'verification_mode': 'GENIUS CORE STRICT CLASSIFICATION MODE',
                    'is_test_data': self.is_test_data,
                    'test_drivers_count': len(self.test_drivers) if self.is_test_data else 0,
                    'classification_definition': {
                        'not_on_job': 'Driver not present in driving history report',
                        'on_time': 'Driver present in driving history report'
                    }
                }
            }
            
            # Add drivers
            for driver in self.classified_drivers.values():
                driver_record = {
                    'name': driver['name'],
                    'normalized_name': driver['normalized_name'],
                    'asset_id': driver['asset_id'],
                    'job_site': driver['job_site'],
                    'status': driver['classification'],
                    'status_reason': driver['classification_reason'],
                    'in_driving_history': driver['in_driving_history']
                }
                
                report_data['drivers'].append(driver_record)
            
            # Save JSON report
            with open(json_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            # Create Excel report
            try:
                # Convert to DataFrame for Excel export
                df_drivers = pd.DataFrame(report_data['drivers'])
                
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
                            df_drivers['sort_order'] = df_drivers['status'].map(
                                lambda x: status_order.get(x, 999)
                            )
                            df_drivers = df_drivers.sort_values('sort_order')
                            df_drivers = df_drivers.drop('sort_order', axis=1)
                        
                        df_drivers.to_excel(writer, sheet_name='All Drivers', index=False)
                        
                        # Status-specific sheets
                        for status in ['On Time', 'Not On Job']:
                            filtered_df = df_drivers[df_drivers['status'] == status]
                            if not filtered_df.empty:
                                filtered_df.to_excel(writer, sheet_name=status, index=False)
                    
                    # Summary sheet
                    summary_rows = [
                        ['Date', self.date_str],
                        ['Generated At', datetime.now().isoformat()],
                        ['Total Drivers', len(self.classified_drivers)],
                        ['On Time', self.classification_stats['on_time']],
                        ['Late', self.classification_stats['late']],
                        ['Early End', self.classification_stats['early_end']],
                        ['Not On Job', self.classification_stats['not_on_job']],
                        ['Test Data Detected', 'Yes' if self.is_test_data else 'No']
                    ]
                    
                    df_summary = pd.DataFrame(summary_rows, columns=['Metric', 'Value'])
                    df_summary.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Classification definitions sheet
                    definitions = [
                        ['Classification', 'Definition'],
                        ['On Time', 'Driver present in driving history report'],
                        ['Not On Job', 'Driver not present in driving history report']
                    ]
                    
                    df_definitions = pd.DataFrame(definitions[1:], columns=definitions[0])
                    df_definitions.to_excel(writer, sheet_name='Definitions', index=False)
                
                logger.info(f"Generated daily driver Excel report at {excel_path}")
                
            except Exception as e:
                logger.error(f"Error generating daily driver Excel report: {e}")
                logger.error(traceback.format_exc())
            
            # Copy to exports directory
            export_json_path = os.path.join(daily_exports_dir, f"daily_report_{self.date_str}.json")
            export_excel_path = os.path.join(daily_exports_dir, f"daily_report_{self.date_str}.xlsx")
            
            shutil.copy(json_path, export_json_path)
            shutil.copy(excel_path, export_excel_path)
            
            # Also copy to genius core directory
            genius_json_path = os.path.join(genius_core_dir, f"daily_report_{self.date_str}.json")
            genius_excel_path = os.path.join(genius_core_dir, f"daily_report_{self.date_str}.xlsx")
            
            shutil.copy(json_path, genius_json_path)
            shutil.copy(excel_path, genius_excel_path)
            
            # Generate PDF report (if possible)
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
                        pdf_path = os.path.join(daily_report_dir, f"daily_report_{self.date_str}.pdf")
                        pdf_module.generate_pdf_report(self.date_str, report_data, pdf_path)
                        
                        # Copy to exports
                        export_pdf_path = os.path.join(daily_exports_dir, f"daily_report_{self.date_str}.pdf")
                        genius_pdf_path = os.path.join(genius_core_dir, f"daily_report_{self.date_str}.pdf")
                        
                        shutil.copy(pdf_path, export_pdf_path)
                        shutil.copy(pdf_path, genius_pdf_path)
                        
                        logger.info(f"Generated daily driver PDF report at {pdf_path}")
            except Exception as e:
                logger.warning(f"Could not generate daily driver PDF report: {e}")
            
            logger.info(f"Created updated daily driver report for {self.date_str}")
            
            return {
                'json_path': json_path,
                'excel_path': excel_path
            }
            
        except Exception as e:
            logger.error(f"Error creating updated daily driver report: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def run(self):
        """Run the final driver classification process"""
        logger.info(f"Running final driver classification for {self.date_str}")
        
        # Step 1: Extract data from Asset List
        logger.info("1. Extracting data from Asset List")
        success = self.extract_asset_list()
        
        if not success:
            logger.error("Failed to extract data from Asset List")
            return False
        
        # Step 2: Extract data from Driving History
        logger.info("2. Extracting data from Driving History")
        success = self.extract_driving_history()
        
        if not success:
            logger.error("Failed to extract data from Driving History")
            return False
        
        # Step 3: Classify drivers
        logger.info("3. Classifying drivers")
        success = self.classify_drivers()
        
        if not success:
            logger.error("Failed to classify drivers")
            return False
        
        # Step 4: Generate classification reports
        logger.info("4. Generating classification reports")
        report_paths = self.generate_reports()
        
        if not report_paths:
            logger.error("Failed to generate classification reports")
            return False
        
        # Step 5: Create updated daily driver report
        logger.info("5. Creating updated daily driver report")
        daily_report = self.create_updated_daily_report()
        
        if not daily_report:
            logger.error("Failed to create updated daily driver report")
            return False
        
        logger.info(f"Completed final driver classification for {self.date_str}")
        
        return {
            'date': self.date_str,
            'classification_reports': report_paths,
            'daily_report': daily_report,
            'statistics': self.classification_stats,
            'is_test_data': self.is_test_data
        }


def process_date(date_str):
    """Process a specific date with final driver classification"""
    logger.info(f"Processing date: {date_str}")
    
    classifier = FinalDriverClassification(date_str)
    result = classifier.run()
    
    return result


def main():
    """Main function"""
    logger.info("Starting Final Driver Classification")
    
    # Set target dates from command line if provided
    target_dates = []
    
    if len(sys.argv) > 1:
        target_dates = sys.argv[1:]
    else:
        # Default to May 16 and 19, 2025
        target_dates = ['2025-05-16', '2025-05-19']
    
    results = {}
    
    for date_str in target_dates:
        logger.info(f"Processing {date_str}")
        result = process_date(date_str)
        
        if result:
            results[date_str] = result
    
    # Print summary
    print("\nFINAL DRIVER CLASSIFICATION SUMMARY")
    print("=" * 80)
    
    for date_str, result in results.items():
        print(f"\nDate: {date_str}")
        
        if isinstance(result, dict) and 'statistics' in result:
            stats = result['statistics']
            is_test_data = result.get('is_test_data', False)
            
            print(f"Total Drivers: {stats['total_drivers']}")
            print(f"On Time: {stats['on_time']}")
            print(f"Not On Job: {stats['not_on_job']}")
            
            if is_test_data:
                print(f"Test Data Detected: Yes (contains {stats.get('test_drivers_count', 0)} test drivers)")
            
            if 'classification_reports' in result:
                report_paths = result['classification_reports']
                print("\nClassification Reports:")
                for report_type, path in report_paths.items():
                    if path:
                        print(f"  {report_type}: {path}")
            
            if 'daily_report' in result:
                daily_report = result['daily_report']
                print("\nUpdated Daily Driver Report:")
                for report_type, path in daily_report.items():
                    print(f"  {report_type}: {path}")
    
    print("\nFinal Driver Classification Complete")
    print("All drivers properly classified according to strict definition:")
    print("Not On Job = Driver not present in driving history report")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())