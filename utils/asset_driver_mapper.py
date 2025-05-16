"""
Asset Driver Mapping Utility

This module analyzes multiple data sources to build comprehensive
asset-driver relationships:
- Monthly billing spreadsheets
- Timecard data
- GPS efficiency data

The combined approach gives the most accurate picture of which
drivers are assigned to which assets.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database models (imported here to avoid circular imports)
from minimal import db, Asset, Driver, AssetDriverMapping

class AssetDriverMappingBuilder:
    """Class to build asset-driver mappings from multiple data sources"""
    
    def __init__(self):
        """Initialize the mapping builder"""
        self.asset_map = {}  # Map asset IDs to internal database IDs
        self.driver_map = {}  # Map employee IDs to internal database IDs
        self.assignments = []  # List to hold all potential assignments
        self.confidence_scores = defaultdict(float)  # Track confidence in each assignment
        
    def load_reference_data(self):
        """Load reference data from the database"""
        # Load all assets
        assets = Asset.query.all()
        for asset in assets:
            self.asset_map[asset.asset_identifier] = asset.id
            
        # Load all drivers
        drivers = Driver.query.all()
        for driver in drivers:
            self.driver_map[driver.employee_id] = driver.id
            
        logger.info(f"Loaded {len(self.asset_map)} assets and {len(self.driver_map)} drivers from database")
        
    def process_billing_spreadsheets(self):
        """Process monthly billing spreadsheets for asset-driver relationships"""
        # Look for billing files in the attached_assets folder
        billing_files = []
        for filename in os.listdir('attached_assets'):
            if "BILLING" in filename.upper() and filename.endswith(('.xlsx', '.xlsm')):
                billing_files.append(os.path.join('attached_assets', filename))
                
        if not billing_files:
            logger.warning("No billing spreadsheets found")
            return
            
        for file_path in billing_files:
            try:
                logger.info(f"Processing billing file: {file_path}")
                self._extract_from_billing(file_path)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                
    def _extract_from_billing(self, file_path):
        """Extract asset-driver relationships from a billing spreadsheet"""
        try:
            # Load the Excel file
            xls = pd.ExcelFile(file_path)
            
            # Examine the sheet names to find relevant sheets
            relevant_sheets = []
            for sheet in xls.sheet_names:
                # Look for sheets that might contain asset-driver data
                if any(term in sheet.upper() for term in ['ASSET', 'DRIVER', 'EQUIP', 'BILLING']):
                    relevant_sheets.append(sheet)
                    
            if not relevant_sheets:
                relevant_sheets = xls.sheet_names  # Try all sheets if no obvious matches
                
            # Process each relevant sheet
            for sheet in relevant_sheets:
                df = pd.read_excel(xls, sheet)
                
                # Look for asset ID columns
                asset_cols = [col for col in df.columns if any(term in str(col).upper() 
                             for term in ['ASSET', 'EQUIP', 'ID', 'NUMBER'])]
                
                # Look for driver/operator columns
                driver_cols = [col for col in df.columns if any(term in str(col).upper() 
                              for term in ['DRIVER', 'OPERATOR', 'EMPLOYEE', 'PERSON'])]
                
                if not asset_cols or not driver_cols:
                    continue  # Skip sheets without clear asset-driver columns
                    
                # Use the first identified columns for each
                asset_col = asset_cols[0]
                driver_col = driver_cols[0]
                
                # Extract relationships
                for _, row in df.iterrows():
                    asset_id = str(row[asset_col]).strip()
                    driver_info = str(row[driver_col]).strip()
                    
                    # Skip empty or NaN values
                    if asset_id in ['nan', ''] or driver_info in ['nan', '']:
                        continue
                        
                    # Try to extract employee ID from driver info
                    employee_id = self._extract_employee_id(driver_info)
                    
                    # Check if we have a valid asset and driver ID
                    asset_db_id = self._find_asset_id(asset_id)
                    driver_db_id = self._find_driver_id(employee_id, driver_info)
                    
                    if asset_db_id and driver_db_id:
                        # Add to assignments with a high confidence score (billing data is official)
                        assignment_key = f"{asset_db_id}_{driver_db_id}"
                        self.confidence_scores[assignment_key] += 0.7  # High weight for billing data
                        
                        # Add to assignments list
                        self.assignments.append({
                            'asset_id': asset_db_id,
                            'driver_id': driver_db_id,
                            'source': 'billing',
                            'source_file': os.path.basename(file_path),
                            'confidence': self.confidence_scores[assignment_key]
                        })
                        
                logger.info(f"Processed sheet {sheet} from {os.path.basename(file_path)}")
                
        except Exception as e:
            logger.error(f"Error in _extract_from_billing: {str(e)}")
    
    def process_timecard_data(self):
        """Process timecard data for asset-driver relationships"""
        # Look for timecard files in the attached_assets folder
        timecard_files = []
        for filename in os.listdir('attached_assets'):
            if "TIMECARD" in filename.upper() or "TIME" in filename.upper():
                timecard_files.append(os.path.join('attached_assets', filename))
                
        if not timecard_files:
            logger.warning("No timecard files found")
            return
            
        for file_path in timecard_files:
            try:
                logger.info(f"Processing timecard file: {file_path}")
                self._extract_from_timecard(file_path)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
    
    def _extract_from_timecard(self, file_path):
        """Extract asset-driver relationships from a timecard file"""
        try:
            # Load the Excel file
            xls = pd.ExcelFile(file_path)
            
            # Process each sheet
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet)
                
                # Look for employee/name columns
                employee_cols = [col for col in df.columns if any(term in str(col).upper() 
                                for term in ['EMPLOYEE', 'NAME', 'DRIVER', 'OPERATOR'])]
                
                # Look for equipment/asset columns
                equipment_cols = [col for col in df.columns if any(term in str(col).upper() 
                                 for term in ['EQUIPMENT', 'ASSET', 'VEHICLE', 'EQUIP'])]
                
                if not employee_cols:
                    continue  # Skip sheets without employee/name columns
                
                # If we didn't find explicit equipment columns, look at all columns
                # for ones that might contain equipment IDs
                if not equipment_cols:
                    # Check if any columns have values that look like equipment IDs
                    for col in df.columns:
                        # Skip columns we've already identified as employee columns
                        if col in employee_cols:
                            continue
                            
                        # Sample the column to see if it might contain equipment IDs
                        sample = df[col].dropna().astype(str).tolist()
                        if not sample:
                            continue
                            
                        # Check if any values look like equipment IDs (e.g., TR-1001)
                        if any(re.match(r'[A-Z]+-\d+', str(val)) for val in sample[:20]):
                            equipment_cols.append(col)
                
                if not equipment_cols:
                    continue  # Skip if we still didn't find equipment columns
                
                # Process the timecards
                for _, row in df.iterrows():
                    # Extract employee information
                    employee_info = None
                    for col in employee_cols:
                        if pd.notna(row[col]) and str(row[col]).strip() != '':
                            employee_info = str(row[col]).strip()
                            break
                            
                    if not employee_info:
                        continue
                        
                    # Try to extract employee ID
                    employee_id = self._extract_employee_id(employee_info)
                    driver_db_id = self._find_driver_id(employee_id, employee_info)
                    
                    if not driver_db_id:
                        continue
                        
                    # Look for equipment assignments
                    for col in equipment_cols:
                        if pd.notna(row[col]) and str(row[col]).strip() != '':
                            equip_id = str(row[col]).strip()
                            asset_db_id = self._find_asset_id(equip_id)
                            
                            if asset_db_id:
                                # Add to assignments with a medium confidence score
                                assignment_key = f"{asset_db_id}_{driver_db_id}"
                                self.confidence_scores[assignment_key] += 0.5  # Medium weight for timecard data
                                
                                # Add to assignments list
                                self.assignments.append({
                                    'asset_id': asset_db_id,
                                    'driver_id': driver_db_id,
                                    'source': 'timecard',
                                    'source_file': os.path.basename(file_path),
                                    'confidence': self.confidence_scores[assignment_key]
                                })
                
                logger.info(f"Processed sheet {sheet} from {os.path.basename(file_path)}")
                
        except Exception as e:
            logger.error(f"Error in _extract_from_timecard: {str(e)}")
    
    def process_gps_data(self):
        """Process GPS efficiency data for asset-driver relationships"""
        # Look for GPS data files in the attached_assets folder
        gps_files = []
        for filename in os.listdir('attached_assets'):
            if any(term in filename.upper() for term in ['GPS', 'EFFICIENCY', 'ZONE', 'TRACK']):
                gps_files.append(os.path.join('attached_assets', filename))
                
        if not gps_files:
            logger.warning("No GPS data files found")
            return
            
        for file_path in gps_files:
            try:
                logger.info(f"Processing GPS data file: {file_path}")
                self._extract_from_gps(file_path)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
    
    def _extract_from_gps(self, file_path):
        """Extract asset-driver relationships from GPS data"""
        try:
            # Load the Excel file
            xls = pd.ExcelFile(file_path)
            
            # Process each sheet
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet)
                
                # Look for asset/equipment columns
                asset_cols = [col for col in df.columns if any(term in str(col).upper() 
                             for term in ['ASSET', 'EQUIP', 'VEHICLE', 'UNIT'])]
                
                # Look for driver/operator columns
                driver_cols = [col for col in df.columns if any(term in str(col).upper() 
                              for term in ['DRIVER', 'OPERATOR', 'EMPLOYEE'])]
                
                if not asset_cols or not driver_cols:
                    continue  # Skip sheets without clear asset-driver columns
                    
                # Use the first identified columns for each
                asset_col = asset_cols[0]
                driver_col = driver_cols[0]
                
                # Extract relationships
                for _, row in df.iterrows():
                    asset_id = str(row[asset_col]).strip()
                    driver_info = str(row[driver_col]).strip()
                    
                    # Skip empty or NaN values
                    if asset_id in ['nan', ''] or driver_info in ['nan', '']:
                        continue
                        
                    # Try to extract employee ID from driver info
                    employee_id = self._extract_employee_id(driver_info)
                    
                    # Check if we have a valid asset and driver ID
                    asset_db_id = self._find_asset_id(asset_id)
                    driver_db_id = self._find_driver_id(employee_id, driver_info)
                    
                    if asset_db_id and driver_db_id:
                        # Add to assignments with a lower confidence score (GPS data shows usage, not assignment)
                        assignment_key = f"{asset_db_id}_{driver_db_id}"
                        self.confidence_scores[assignment_key] += 0.3  # Lower weight for GPS data
                        
                        # Add to assignments list
                        self.assignments.append({
                            'asset_id': asset_db_id,
                            'driver_id': driver_db_id,
                            'source': 'gps',
                            'source_file': os.path.basename(file_path),
                            'confidence': self.confidence_scores[assignment_key]
                        })
                        
                logger.info(f"Processed sheet {sheet} from {os.path.basename(file_path)}")
                
        except Exception as e:
            logger.error(f"Error in _extract_from_gps: {str(e)}")
    
    def _extract_employee_id(self, text):
        """Extract employee ID from text using patterns"""
        # Common patterns for employee IDs
        patterns = [
            r'EMP\d+',  # EMP followed by digits
            r'E\d+',    # E followed by digits
            r'ID:?\s*(\d+)',  # ID: followed by digits
            r'#\s*(\d+)',  # # followed by digits
            r'\((\d+)\)'  # Digits in parentheses
        ]
        
        text = str(text).strip()
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # If the pattern uses a capture group, return the captured text
                if '(' in pattern:
                    return match.group(1)
                # Otherwise return the whole match
                return match.group(0)
                
        # If no pattern matched, return the text itself (might be a name or other identifier)
        return text
    
    def _find_asset_id(self, asset_identifier):
        """Find the database ID for an asset based on its identifier"""
        # Try exact match first
        if asset_identifier in self.asset_map:
            return self.asset_map[asset_identifier]
            
        # Try fuzzy matching for asset identifiers
        asset_identifier = str(asset_identifier).strip().upper()
        for db_identifier, db_id in self.asset_map.items():
            db_identifier = str(db_identifier).strip().upper()
            
            # Check for substring match or similarity
            if (asset_identifier in db_identifier or 
                db_identifier in asset_identifier or
                self._similarity(asset_identifier, db_identifier) > 0.8):
                return db_id
                
        # If we get here, we couldn't find a match
        return None
    
    def _find_driver_id(self, employee_id, driver_info):
        """Find the database ID for a driver based on employee ID or name"""
        # Try exact match on employee ID first
        if employee_id in self.driver_map:
            return self.driver_map[employee_id]
            
        # If that fails, try to match on name or other info
        driver_info = str(driver_info).strip().upper()
        for driver in Driver.query.all():
            driver_name = driver.name.upper() if driver.name else ""
            
            # Check for name match
            if driver_name and (driver_name in driver_info or driver_info in driver_name):
                return driver.id
                
        # If we get here, we couldn't find a match
        return None
    
    def _similarity(self, str1, str2):
        """Calculate a simple similarity score between two strings"""
        # Convert to uppercase for case-insensitive comparison
        s1 = str(str1).upper()
        s2 = str(str2).upper()
        
        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(s1, s2))
        
        # Calculate similarity ratio
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 0
        return matches / max_len
    
    def finalize_assignments(self):
        """Finalize assignments by selecting the highest confidence matches"""
        if not self.assignments:
            logger.warning("No assignments found to finalize")
            return []
            
        # Group by asset_id and driver_id, keeping the highest confidence
        final_assignments = {}
        for assignment in self.assignments:
            key = f"{assignment['asset_id']}_{assignment['driver_id']}"
            
            if key not in final_assignments or assignment['confidence'] > final_assignments[key]['confidence']:
                final_assignments[key] = assignment
                
        logger.info(f"Finalized {len(final_assignments)} unique asset-driver assignments")
        return list(final_assignments.values())
    
    def save_to_database(self, assignments, start_date=None):
        """Save the finalized assignments to the database"""
        if not assignments:
            logger.warning("No assignments to save to database")
            return 0
            
        # Use today as the default start date if none provided
        if not start_date:
            start_date = datetime.now().date()
            
        # Keep track of how many new assignments we create
        new_assignments = 0
        
        for assignment in assignments:
            asset_id = assignment['asset_id']
            driver_id = assignment['driver_id']
            
            # Check if there's already a current assignment for this asset
            existing = AssetDriverMapping.query.filter_by(
                asset_id=asset_id,
                is_current=True
            ).first()
            
            # If the existing assignment is for the same driver, skip it
            if existing and existing.driver_id == driver_id:
                continue
                
            # If there's an existing different assignment, end it
            if existing:
                existing.is_current = False
                existing.end_date = start_date - timedelta(days=1)
                db.session.add(existing)
                
            # Create the new assignment
            new_assignment = AssetDriverMapping(
                asset_id=asset_id,
                driver_id=driver_id,
                start_date=start_date,
                is_current=True,
                notes=f"Auto-assigned from {assignment['source']} data"
            )
            
            db.session.add(new_assignment)
            new_assignments += 1
            
        # Commit all changes
        if new_assignments > 0:
            db.session.commit()
            logger.info(f"Created {new_assignments} new asset-driver assignments")
            
        return new_assignments


def import_asset_driver_assignments():
    """Main function to import asset-driver assignments from all data sources"""
    try:
        # Start the mapping builder
        mapper = AssetDriverMappingBuilder()
        
        # Load reference data
        mapper.load_reference_data()
        
        # Process data from each source
        mapper.process_billing_spreadsheets()
        mapper.process_timecard_data()
        mapper.process_gps_data()
        
        # Finalize and save assignments
        assignments = mapper.finalize_assignments()
        new_count = mapper.save_to_database(assignments)
        
        return {
            'success': True,
            'new_assignments': new_count,
            'message': f"Successfully created {new_count} new asset-driver assignments"
        }
        
    except Exception as e:
        logger.error(f"Error importing asset-driver assignments: {str(e)}")
        return {
            'success': False,
            'new_assignments': 0,
            'message': f"Error: {str(e)}"
        }


def get_unique_drivers():
    """Get unique drivers from timecard data for driver import"""
    unique_drivers = []
    driver_ids = set()
    
    try:
        # Look for timecard files in the attached_assets folder
        timecard_files = []
        for filename in os.listdir('attached_assets'):
            if "TIMECARD" in filename.upper() or "TIME" in filename.upper():
                timecard_files.append(os.path.join('attached_assets', filename))
                
        if not timecard_files:
            logger.warning("No timecard files found")
            return []
            
        for file_path in timecard_files:
            try:
                # Load the Excel file
                xls = pd.ExcelFile(file_path)
                
                # Process each sheet
                for sheet in xls.sheet_names:
                    df = pd.read_excel(xls, sheet)
                    
                    # Look for employee/name columns
                    employee_cols = [col for col in df.columns if any(term in str(col).upper() 
                                    for term in ['EMPLOYEE', 'NAME', 'DRIVER', 'OPERATOR'])]
                    
                    if not employee_cols:
                        continue  # Skip sheets without employee/name columns
                    
                    # Extract employee information
                    for _, row in df.iterrows():
                        for col in employee_cols:
                            if pd.notna(row[col]) and str(row[col]).strip() != '':
                                employee_info = str(row[col]).strip()
                                
                                # Try to extract a name and employee ID
                                employee_id = None
                                name = employee_info
                                
                                # Try to extract employee ID using various patterns
                                id_match = None
                                for pattern in [r'EMP\d+', r'E\d+', r'ID:?\s*(\d+)', r'#\s*(\d+)', r'\((\d+)\)']:
                                    match = re.search(pattern, employee_info)
                                    if match:
                                        id_match = match
                                        break
                                        
                                if id_match:
                                    # If we found an ID, extract it and clean up the name
                                    if '(' in pattern:
                                        employee_id = id_match.group(1)
                                    else:
                                        employee_id = id_match.group(0)
                                        
                                    # Remove the ID from the name
                                    name = employee_info.replace(id_match.group(0), '').strip()
                                    
                                    # Clean up any remaining parentheses, commas, etc.
                                    name = re.sub(r'[,;:()\[\]]', ' ', name).strip()
                                    name = re.sub(r'\s+', ' ', name).strip()
                                else:
                                    # If we couldn't extract an ID, make one up based on the name
                                    name = re.sub(r'[,;:()\[\]]', ' ', employee_info).strip()
                                    name = re.sub(r'\s+', ' ', name).strip()
                                    employee_id = 'EMP' + str(abs(hash(name)) % 10000)
                                
                                # Look for region/department info in other columns
                                region = None
                                department = None
                                
                                for dept_col in df.columns:
                                    if isinstance(dept_col, str) and 'DEPARTMENT' in dept_col.upper():
                                        if pd.notna(row[dept_col]):
                                            department = str(row[dept_col]).strip()
                                            
                                for region_col in df.columns:
                                    if isinstance(region_col, str) and any(r in region_col.upper() for r in ['REGION', 'LOCATION', 'SITE']):
                                        if pd.notna(row[region_col]):
                                            region = str(row[region_col]).strip()
                                
                                # Skip if we've already seen this employee ID
                                if employee_id in driver_ids:
                                    continue
                                    
                                # Add to our list
                                driver_ids.add(employee_id)
                                unique_drivers.append({
                                    'name': name,
                                    'employee_id': employee_id,
                                    'department': department,
                                    'region': region
                                })
                                
                                # Only process the first employee column that has a value
                                break
                                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                
        return unique_drivers
        
    except Exception as e:
        logger.error(f"Error getting unique drivers: {str(e)}")
        return []