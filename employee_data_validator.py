"""
Employee Data Validator

This module provides functions to validate driver data against official employee records
from ELIST and JLIST files. It ensures that only authentic employee entries are
included in reports, with proper formatting and validation.
"""
import os
import csv
import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up unmatched drivers log
unmatched_log = logging.getLogger('unmatched_drivers')
unmatched_log.setLevel(logging.WARNING)

if not os.path.exists('logs'):
    os.makedirs('logs')

unmatched_handler = logging.FileHandler('logs/unmatched_drivers.log')
unmatched_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
unmatched_log.addHandler(unmatched_handler)

# Division mapping
DIVISION_MAPPING = {
    'DFW': 'DIV 2',
    'HOU': 'DIV 4',
    'WT': 'DIV 3',
    'TEXDIST': 'DIV 8',
    'DALOH-HH': 'DIV 2',
    'HOUOH-HH': 'DIV 4',
    'WTOH-HH': 'DIV 3'
}

# Asset prefix to division mapping
ASSET_PREFIX_MAPPING = {
    'DFW': ['DFW', 'DAL', 'D-', 'D_'],
    'HOU': ['HOU', 'H-', 'H_'],
    'WT': ['WT', 'W-', 'W_'],
}

class EmployeeValidator:
    """Class to validate employee data against official records"""
    
    def __init__(self):
        """Initialize the validator with employee data"""
        self.employees = {}
        self.employee_ids = set()
        self.loaded = False
    
    def load_employee_data(self):
        """Load employee data from official sources"""
        logger.info("Loading employee data from official sources")
        
        # Find the paths for the employee list files
        elist_contact_path = None
        jlist_dfw_path = None
        jlist_hou_path = None
        jlist_wt_path = None
        
        for file in os.listdir('attached_assets'):
            if 'RAG-ELIST' in file and 'contact info' in file:
                elist_contact_path = os.path.join('attached_assets', file)
            elif 'RAG-JLIST' in file and 'DFW' in file:
                jlist_dfw_path = os.path.join('attached_assets', file)
            elif 'RAG-JLIST' in file and 'HOU' in file:
                jlist_hou_path = os.path.join('attached_assets', file)
            elif 'RAG-JLIST' in file and 'WT' in file:
                jlist_wt_path = os.path.join('attached_assets', file)
        
        if not elist_contact_path:
            logger.error("Employee contact list file not found")
            return False
        
        # Load employee data from ELIST file
        logger.info(f"Loading employee data from {elist_contact_path}")
        try:
            # Try different encodings since CSV files might have encoding issues
            encodings = ['utf-8', 'latin-1', 'cp1252']
            loaded = False
            
            for encoding in encodings:
                try:
                    with open(elist_contact_path, 'r', encoding=encoding) as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # Extract relevant data - normalize field names to handle different formats
                            employee_id = None
                            name = None
                            first_name = None
                            last_name = None
                            email = None
                            phone = None
                            division = None
                            job_title = None
                            
                            # Try all possible field names for employee ID
                            for field in ['EMPLOYEE ID', 'EMPLOYEEID', 'EMP ID', 'EMPID', 'ID']:
                                if field in row and row[field]:
                                    employee_id = row[field].strip()
                                    break
                            
                            if not employee_id:
                                continue
                            
                            # Name fields
                            for field in ['NAME', 'EMPLOYEE NAME', 'FULL NAME']:
                                if field in row and row[field]:
                                    name = row[field].strip()
                                    break
                            
                            for field in ['FIRST NAME', 'FIRSTNAME', 'FNAME']:
                                if field in row and row[field]:
                                    first_name = row[field].strip()
                                    break
                            
                            for field in ['LAST NAME', 'LASTNAME', 'LNAME']:
                                if field in row and row[field]:
                                    last_name = row[field].strip()
                                    break
                            
                            # Other fields
                            for field in ['EMAIL', 'E-MAIL', 'EMAIL ADDRESS']:
                                if field in row and row[field]:
                                    email = row[field].strip().lower()
                                    break
                            
                            for field in ['PHONE', 'TELEPHONE', 'PHONE NUMBER', 'CONTACT']:
                                if field in row and row[field]:
                                    phone = row[field].strip()
                                    break
                            
                            for field in ['DIVISION', 'DIV', 'DEPT', 'DEPARTMENT']:
                                if field in row and row[field]:
                                    division = row[field].strip()
                                    break
                            
                            for field in ['JOB TITLE', 'TITLE', 'POSITION']:
                                if field in row and row[field]:
                                    job_title = row[field].strip()
                                    break
                            
                            # If name is missing but we have first and last, construct it
                            if not name and first_name and last_name:
                                name = f"{first_name} {last_name}"
                            
                            # Store with employee ID as key
                            self.employees[employee_id] = {
                                'id': employee_id,
                                'name': self._format_name(name or ''),
                                'first_name': self._format_name(first_name or ''),
                                'last_name': self._format_name(last_name or ''),
                                'email': email or '',
                                'phone': self._format_phone(phone or ''),
                                'division': division or '',
                                'job_title': job_title or '',
                                'source': 'ELIST'
                            }
                            
                            # Add to employee IDs set
                            self.employee_ids.add(employee_id)
                    
                    loaded = True
                    logger.info(f"Loaded {len(self.employees)} employees from ELIST using {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    logger.warning(f"Could not read file with {encoding} encoding, trying next...")
                except Exception as e:
                    logger.error(f"Error reading ELIST file with {encoding} encoding: {e}")
            
            if not loaded:
                logger.error("Could not load employee data from ELIST file with any encoding")
            
            # For the JLIST files, we'll try all encodings as well
            for jlist_path, division in [
                (jlist_dfw_path, 'DFW'),
                (jlist_hou_path, 'HOU'),
                (jlist_wt_path, 'WT')
            ]:
                if jlist_path:
                    self._load_jlist_file(jlist_path, division)
            
            self.loaded = True
            return True
        
        except Exception as e:
            logger.error(f"Error loading employee data: {e}")
            return False
    
    def _load_jlist_file(self, jlist_path, division):
        """Load job assignments from JLIST file"""
        logger.info(f"Loading job assignments from {jlist_path}")
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(jlist_path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Try different field names for employee ID
                        employee_id = None
                        for field in ['EMPLOYEE ID', 'EMPLOYEEID', 'EMP ID', 'EMPID', 'ID']:
                            if field in row and row[field]:
                                employee_id = row[field].strip()
                                break
                        
                        if not employee_id or employee_id not in self.employees:
                            continue
                        
                        # Try different field names for other data
                        job_number = None
                        for field in ['JOB NUMBER', 'JOBNUMBER', 'JOB', 'JOB #']:
                            if field in row and row[field]:
                                job_number = row[field].strip()
                                break
                        
                        job_name = None
                        for field in ['JOB NAME', 'JOBNAME', 'PROJECT', 'PROJECT NAME']:
                            if field in row and row[field]:
                                job_name = row[field].strip()
                                break
                        
                        cost_code = None
                        for field in ['COST CODE', 'COSTCODE', 'CODE']:
                            if field in row and row[field]:
                                cost_code = row[field].strip()
                                break
                        
                        location = None
                        for field in ['LOCATION', 'LOC', 'SITE', 'JOBSITE']:
                            if field in row and row[field]:
                                location = row[field].strip()
                                break
                        
                        # Update employee record with job data
                        self.employees[employee_id].update({
                            'job_number': job_number or '',
                            'job_name': job_name or '',
                            'cost_code': cost_code or '',
                            'assigned_division': division,
                            'location': location or ''
                        })
                
                logger.info(f"Successfully loaded job assignments from {jlist_path} using {encoding} encoding")
                return True
            
            except UnicodeDecodeError:
                logger.warning(f"Could not read JLIST file with {encoding} encoding, trying next...")
            except Exception as e:
                logger.error(f"Error loading JLIST file {jlist_path} with {encoding} encoding: {e}")
        
        logger.error(f"Failed to load JLIST file {jlist_path} with any encoding")
        return False
    
    def _format_name(self, name):
        """Format name in title case with proper spacing"""
        if not name:
            return ''
        
        # Remove extra spaces
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Title case with exceptions for prefixes and suffixes
        words = name.split()
        formatted_words = []
        
        for word in words:
            # Check for common prefixes/suffixes
            if word.lower() in ['jr', 'jr.', 'sr', 'sr.', 'ii', 'iii', 'iv']:
                formatted_words.append(word.upper())
            elif word.lower() in ['de', 'del', 'la', 'van', 'von', 'mc', 'mac']:
                formatted_words.append(word.lower().capitalize())
            elif "'" in word:  # Handle names like O'Brien
                parts = word.split("'")
                formatted_words.append(parts[0].capitalize() + "'" + parts[1].capitalize())
            elif "-" in word:  # Handle hyphenated names
                parts = word.split("-")
                formatted_words.append("-".join([p.capitalize() for p in parts]))
            else:
                formatted_words.append(word.capitalize())
        
        return ' '.join(formatted_words)
    
    def _format_phone(self, phone):
        """Format phone number consistently"""
        if not phone:
            return ''
        
        # Remove non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
        else:
            return phone.strip()
    
    def validate_driver(self, driver_data, source_file=None):
        """
        Validate a driver against employee records
        
        Args:
            driver_data (dict): Driver data including name, asset, etc.
            source_file (str): Source file for the driver data (for logging)
            
        Returns:
            dict: Validated employee data if found, None if not found
        """
        if not self.loaded:
            self.load_employee_data()
        
        # Extract driver name and asset ID
        driver_name = driver_data.get('name', '').strip()
        asset_id = driver_data.get('asset', '').strip()
        
        if not driver_name:
            unmatched_log.warning(f"Driver with empty name skipped in {source_file}")
            return None
        
        # Check if the driver name is a known synthetic or test name
        synthetic_names = ['john smith', 'mary johnson', 'robert williams', 'patricia brown', 
                         'michael davis', 'linda miller', 'james wilson', 'elizabeth moore', 
                         'david taylor', 'jennifer anderson', 'charles thomas', 'barbara jackson', 
                         'roger doddy', 'john doe', 'jane doe']
        
        if driver_name.lower() in synthetic_names:
            unmatched_log.warning(f"Synthetic driver name '{driver_name}' removed from {source_file}")
            return None
        
        # First, try to find an exact match by name
        for employee_id, employee in self.employees.items():
            if driver_name.lower() == employee['name'].lower():
                # Found a match by name
                logger.info(f"Found employee match by name: {driver_name}")
                return self._enrich_driver_data(driver_data, employee)
        
        # Try to match by last name + first initial
        driver_parts = driver_name.split()
        if len(driver_parts) >= 2:
            last_name = driver_parts[-1]
            first_initial = driver_parts[0][0] if driver_parts[0] else ''
            
            for employee_id, employee in self.employees.items():
                emp_last = employee['last_name']
                emp_first = employee['first_name']
                
                if (emp_last.lower() == last_name.lower() and 
                    emp_first and emp_first[0].lower() == first_initial.lower()):
                    # Partial match
                    logger.info(f"Found partial employee match: {driver_name} -> {employee['name']}")
                    return self._enrich_driver_data(driver_data, employee)
        
        # No match found
        unmatched_log.warning(
            f"Unmatched driver: '{driver_name}', Asset: '{asset_id}', Source: {source_file} - "
            f"UNMATCHED – NOT IN SYSTEM"
        )
        return None
    
    def _enrich_driver_data(self, driver_data, employee):
        """
        Enrich driver data with employee information
        
        Args:
            driver_data (dict): Original driver data
            employee (dict): Employee data from official records
            
        Returns:
            dict: Enriched driver data
        """
        # Create a copy of the original driver data
        enriched = driver_data.copy()
        
        # Update with employee information
        enriched.update({
            'name': employee['name'],
            'employee_id': employee['id'],
            'email': employee.get('email', ''),
            'phone': employee.get('phone', ''),
            'division': employee.get('division', ''),
            'job_title': employee.get('job_title', ''),
            'job_number': employee.get('job_number', ''),
            'job_name': employee.get('job_name', ''),
            'cost_code': employee.get('cost_code', ''),
            'validated': True
        })
        
        # Determine division from asset if not available
        if not enriched.get('division') and enriched.get('asset'):
            enriched['division'] = self._determine_division_from_asset(enriched['asset'])
        
        return enriched
    
    def _determine_division_from_asset(self, asset_id):
        """
        Determine division from asset ID prefix
        
        Args:
            asset_id (str): Asset ID
            
        Returns:
            str: Division code or empty string if not determined
        """
        if not asset_id:
            return ''
        
        # Check asset prefix against mapping
        asset_upper = asset_id.upper()
        for division, prefixes in ASSET_PREFIX_MAPPING.items():
            for prefix in prefixes:
                if asset_upper.startswith(prefix):
                    return DIVISION_MAPPING.get(division, '')
        
        return ''
    
    def build_validated_report(self, date_str, drivers_data):
        """
        Build a validated report with only authentic employee entries
        
        Args:
            date_str (str): Report date in YYYY-MM-DD format
            drivers_data (list): List of driver data dictionaries
            
        Returns:
            dict: Validated report data
        """
        if not self.loaded:
            self.load_employee_data()
        
        # Format date for display
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
        except:
            formatted_date = date_str
        
        # Validate each driver and keep only authentic entries
        validated_drivers = []
        seen_ids = set()  # Track employee IDs to prevent duplicates
        
        for driver in drivers_data:
            validated = self.validate_driver(driver, f"report_{date_str}")
            if validated:
                # Check for duplicate employee IDs
                employee_id = validated.get('employee_id')
                if employee_id and employee_id in seen_ids:
                    logger.warning(f"Duplicate employee ID {employee_id} skipped")
                    continue
                
                # Add to validated list and track ID
                validated_drivers.append(validated)
                if employee_id:
                    seen_ids.add(employee_id)
        
        logger.info(f"Validated report contains {len(validated_drivers)} authentic drivers out of {len(drivers_data)} original entries")
        
        # Build the report data
        report_data = {
            'date': date_str,
            'report_date': formatted_date,
            'drivers': validated_drivers,
            'validated': True,
            'total_drivers': len(validated_drivers)
        }
        
        return report_data

# Create a global instance for use across modules
employee_validator = EmployeeValidator()