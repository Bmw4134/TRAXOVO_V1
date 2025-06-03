"""
Billing Report Processor with QQ Enhancement
Automated processing of source billing reports with intelligent data extraction
"""

import os
import json
import sqlite3
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import time
import re
import hashlib
from pathlib import Path
import openpyxl
import csv

@dataclass
class BillingRecord:
    """Individual billing record with QQ analytics"""
    record_id: str
    project_code: str
    employee_id: str
    employee_name: str
    date: str
    hours_worked: float
    hourly_rate: float
    total_amount: float
    department: str
    cost_center: str
    billing_category: str
    description: str
    approved_by: str
    qq_accuracy_score: float
    qq_completeness_score: float

@dataclass
class ProcessedBillingReport:
    """Processed billing report with comprehensive analytics"""
    report_id: str
    source_filename: str
    processing_timestamp: str
    total_records: int
    total_hours: float
    total_amount: float
    date_range_start: str
    date_range_end: str
    departments: List[str]
    employees_count: int
    qq_processing_quality: float
    anomalies_detected: List[Dict[str, Any]]
    validation_status: str
    records: List[BillingRecord]

class BillingReportProcessor:
    """
    QQ-Enhanced Billing Report Processor
    Intelligent extraction and validation of billing data from various formats
    """
    
    def __init__(self):
        self.logger = logging.getLogger("billing_processor")
        self.db_path = "billing_data.db"
        
        # Initialize QQ billing model
        self.qq_billing_model = self._initialize_qq_billing_model()
        
        # Initialize billing database
        self._initialize_billing_database()
        
        # Supported file formats
        self.supported_formats = {'.xlsx', '.xls', '.csv', '.txt'}
        
    def _initialize_qq_billing_model(self) -> Dict[str, Any]:
        """Initialize QQ model for billing processing"""
        return {
            'data_quality_weights': {
                'completeness': 0.30,
                'accuracy': 0.25,
                'consistency': 0.20,
                'timeliness': 0.15,
                'validity': 0.10
            },
            'anomaly_detection_rules': {
                'excessive_hours_daily': 12.0,
                'zero_rate_threshold': 0.01,
                'duplicate_entry_tolerance': 0.95,
                'outlier_rate_multiplier': 3.0,
                'missing_data_threshold': 0.05
            },
            'validation_thresholds': {
                'minimum_accuracy_score': 0.85,
                'minimum_completeness_score': 0.90,
                'maximum_anomaly_percentage': 5.0
            },
            'standard_rates': {
                'project_manager': 125.0,
                'senior_engineer': 95.0,
                'engineer': 75.0,
                'technician': 55.0,
                'administrator': 45.0,
                'laborer': 35.0
            },
            'department_mappings': {
                'construction': ['construction', 'build', 'site', 'field'],
                'engineering': ['engineering', 'design', 'technical', 'eng'],
                'management': ['management', 'admin', 'office', 'mgmt'],
                'operations': ['operations', 'ops', 'maintenance', 'maint']
            }
        }
        
    def _initialize_billing_database(self):
        """Initialize billing database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Billing reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS billing_reports (
                    report_id TEXT PRIMARY KEY,
                    source_filename TEXT,
                    processing_timestamp TEXT,
                    total_records INTEGER,
                    total_hours REAL,
                    total_amount REAL,
                    date_range_start TEXT,
                    date_range_end TEXT,
                    departments TEXT,
                    employees_count INTEGER,
                    qq_processing_quality REAL,
                    anomalies_detected TEXT,
                    validation_status TEXT,
                    created_timestamp TEXT
                )
            ''')
            
            # Billing records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS billing_records (
                    record_id TEXT PRIMARY KEY,
                    report_id TEXT,
                    project_code TEXT,
                    employee_id TEXT,
                    employee_name TEXT,
                    date TEXT,
                    hours_worked REAL,
                    hourly_rate REAL,
                    total_amount REAL,
                    department TEXT,
                    cost_center TEXT,
                    billing_category TEXT,
                    description TEXT,
                    approved_by TEXT,
                    qq_accuracy_score REAL,
                    qq_completeness_score REAL,
                    created_timestamp TEXT,
                    FOREIGN KEY (report_id) REFERENCES billing_reports (report_id)
                )
            ''')
            
            # Employee rates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employee_rates (
                    employee_id TEXT PRIMARY KEY,
                    employee_name TEXT,
                    current_rate REAL,
                    department TEXT,
                    position TEXT,
                    effective_date TEXT,
                    last_updated TEXT
                )
            ''')
            
            # Project codes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_codes (
                    project_code TEXT PRIMARY KEY,
                    project_name TEXT,
                    client_name TEXT,
                    project_manager TEXT,
                    billing_rate_multiplier REAL,
                    status TEXT,
                    start_date TEXT,
                    end_date TEXT
                )
            ''')
            
            conn.commit()
            
    def process_billing_report(self, file_path: str) -> ProcessedBillingReport:
        """Process billing report with QQ intelligence"""
        
        self.logger.info(f"Processing billing report: {file_path}")
        
        # Validate file
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Billing report file not found: {file_path}")
            
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}")
            
        # Generate report ID
        report_id = f"BILLING_{int(time.time())}_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
        
        # Extract data based on file format
        raw_data = self._extract_data_from_file(file_path)
        
        # Clean and normalize data
        cleaned_data = self._clean_and_normalize_data(raw_data)
        
        # Create billing records
        billing_records = self._create_billing_records(cleaned_data, report_id)
        
        # Validate records and detect anomalies
        anomalies = self._detect_anomalies(billing_records)
        
        # Calculate metrics
        total_hours = sum(record.hours_worked for record in billing_records)
        total_amount = sum(record.total_amount for record in billing_records)
        
        # Get date range
        dates = [record.date for record in billing_records if record.date]
        date_range_start = min(dates) if dates else ""
        date_range_end = max(dates) if dates else ""
        
        # Get departments and employee count
        departments = list(set(record.department for record in billing_records if record.department))
        employees = set(record.employee_id for record in billing_records if record.employee_id)
        
        # Calculate QQ processing quality
        qq_quality = self._calculate_processing_quality(billing_records, anomalies)
        
        # Determine validation status
        validation_status = self._determine_validation_status(qq_quality, anomalies)
        
        processed_report = ProcessedBillingReport(
            report_id=report_id,
            source_filename=os.path.basename(file_path),
            processing_timestamp=datetime.now().isoformat(),
            total_records=len(billing_records),
            total_hours=total_hours,
            total_amount=total_amount,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            departments=departments,
            employees_count=len(employees),
            qq_processing_quality=qq_quality,
            anomalies_detected=anomalies,
            validation_status=validation_status,
            records=billing_records
        )
        
        # Store processed report
        self._store_processed_report(processed_report)
        
        return processed_report
        
    def _extract_data_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract raw data from file based on format"""
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.xlsx', '.xls']:
            return self._extract_from_excel(file_path)
        elif file_ext == '.csv':
            return self._extract_from_csv(file_path)
        elif file_ext == '.txt':
            return self._extract_from_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
            
    def _extract_from_excel(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract data from Excel file"""
        
        try:
            # Try pandas first
            df = pd.read_excel(file_path)
            return df.to_dict('records')
            
        except Exception as e:
            self.logger.warning(f"Pandas extraction failed, trying openpyxl: {e}")
            
            # Fallback to openpyxl
            workbook = openpyxl.load_workbook(file_path)
            sheet = workbook.active
            
            # Get headers from first row
            headers = []
            for cell in sheet[1]:
                headers.append(cell.value)
                
            # Extract data
            data = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                record = {}
                for i, value in enumerate(row):
                    if i < len(headers) and headers[i]:
                        record[headers[i]] = value
                data.append(record)
                
            return data
            
    def _extract_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract data from CSV file"""
        
        data = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            # Try to detect delimiter
            sample = file.read(1024)
            file.seek(0)
            
            delimiter = ','
            if '\t' in sample:
                delimiter = '\t'
            elif ';' in sample:
                delimiter = ';'
                
            reader = csv.DictReader(file, delimiter=delimiter)
            
            for row in reader:
                data.append(dict(row))
                
        return data
        
    def _extract_from_text(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract data from text file"""
        
        data = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
            
        # Try to parse as delimited text
        if len(lines) > 1:
            # Assume first line is header
            headers = lines[0].strip().split('\t')
            
            for line in lines[1:]:
                values = line.strip().split('\t')
                record = {}
                
                for i, value in enumerate(values):
                    if i < len(headers):
                        record[headers[i]] = value
                        
                data.append(record)
                
        return data
        
    def _clean_and_normalize_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and normalize extracted data"""
        
        cleaned_data = []
        
        for record in raw_data:
            cleaned_record = {}
            
            # Normalize field names
            for key, value in record.items():
                if not key:
                    continue
                    
                normalized_key = self._normalize_field_name(key)
                cleaned_record[normalized_key] = self._clean_field_value(value)
                
            # Only keep records with essential data
            if self._is_valid_record(cleaned_record):
                cleaned_data.append(cleaned_record)
                
        return cleaned_data
        
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name to standard format"""
        
        if not field_name:
            return ""
            
        field_name = str(field_name).lower().strip()
        
        # Field mappings
        field_mappings = {
            'emp_id': 'employee_id',
            'emp_name': 'employee_name',
            'name': 'employee_name',
            'worker': 'employee_name',
            'proj': 'project_code',
            'project': 'project_code',
            'hrs': 'hours_worked',
            'hours': 'hours_worked',
            'time': 'hours_worked',
            'rate': 'hourly_rate',
            'pay_rate': 'hourly_rate',
            'amount': 'total_amount',
            'total': 'total_amount',
            'cost': 'total_amount',
            'dept': 'department',
            'division': 'department',
            'desc': 'description',
            'description': 'description',
            'notes': 'description'
        }
        
        return field_mappings.get(field_name, field_name)
        
    def _clean_field_value(self, value: Any) -> Any:
        """Clean individual field value"""
        
        if value is None:
            return None
            
        # Convert to string first
        str_value = str(value).strip()
        
        if not str_value or str_value.lower() in ['none', 'null', 'n/a', '']:
            return None
            
        # Try to convert numeric values
        if re.match(r'^[\d\.,]+$', str_value):
            try:
                # Remove commas and convert
                numeric_value = float(str_value.replace(',', ''))
                return numeric_value
            except ValueError:
                pass
                
        return str_value
        
    def _is_valid_record(self, record: Dict[str, Any]) -> bool:
        """Check if record has minimum required data"""
        
        required_fields = ['employee_name', 'hours_worked']
        
        for field in required_fields:
            if field not in record or record[field] is None:
                return False
                
        # Check if hours is valid
        try:
            hours = float(record['hours_worked'])
            if hours <= 0 or hours > 24:  # Basic sanity check
                return False
        except (ValueError, TypeError):
            return False
            
        return True
        
    def _create_billing_records(self, cleaned_data: List[Dict[str, Any]], report_id: str) -> List[BillingRecord]:
        """Create billing records from cleaned data"""
        
        billing_records = []
        
        for i, record_data in enumerate(cleaned_data):
            record_id = f"{report_id}_REC_{i:04d}"
            
            # Extract fields with defaults
            project_code = record_data.get('project_code', 'UNKNOWN')
            employee_id = record_data.get('employee_id', f"EMP_{i:04d}")
            employee_name = record_data.get('employee_name', 'Unknown Employee')
            date = self._parse_date(record_data.get('date', ''))
            hours_worked = float(record_data.get('hours_worked', 0))
            hourly_rate = self._determine_hourly_rate(record_data)
            total_amount = self._calculate_total_amount(hours_worked, hourly_rate, record_data)
            department = self._determine_department(record_data)
            cost_center = record_data.get('cost_center', '')
            billing_category = record_data.get('billing_category', 'Regular')
            description = record_data.get('description', '')
            approved_by = record_data.get('approved_by', '')
            
            # Calculate QQ scores
            accuracy_score = self._calculate_accuracy_score(record_data)
            completeness_score = self._calculate_completeness_score(record_data)
            
            billing_record = BillingRecord(
                record_id=record_id,
                project_code=project_code,
                employee_id=employee_id,
                employee_name=employee_name,
                date=date,
                hours_worked=hours_worked,
                hourly_rate=hourly_rate,
                total_amount=total_amount,
                department=department,
                cost_center=cost_center,
                billing_category=billing_category,
                description=description,
                approved_by=approved_by,
                qq_accuracy_score=accuracy_score,
                qq_completeness_score=completeness_score
            )
            
            billing_records.append(billing_record)
            
        return billing_records
        
    def _parse_date(self, date_value: Any) -> str:
        """Parse date value to standard format"""
        
        if not date_value:
            return datetime.now().strftime('%Y-%m-%d')
            
        date_str = str(date_value)
        
        # Common date patterns
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{1,2})-(\d{1,2})-(\d{4})',
            r'(\d{4})(\d{2})(\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if pattern == date_patterns[0] or pattern == date_patterns[3]:  # YYYY-MM-DD or YYYYMMDD
                        year, month, day = match.groups()
                    else:  # MM/DD/YYYY or MM-DD-YYYY
                        month, day, year = match.groups()
                        
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime('%Y-%m-%d')
                    
                except ValueError:
                    continue
                    
        return datetime.now().strftime('%Y-%m-%d')
        
    def _determine_hourly_rate(self, record_data: Dict[str, Any]) -> float:
        """Determine hourly rate for record"""
        
        # First try explicit rate from record
        if 'hourly_rate' in record_data and record_data['hourly_rate']:
            try:
                return float(record_data['hourly_rate'])
            except (ValueError, TypeError):
                pass
                
        # Try to determine from employee data
        employee_name = record_data.get('employee_name', '').lower()
        department = self._determine_department(record_data).lower()
        
        # Check if we have stored rate for this employee
        stored_rate = self._get_stored_employee_rate(record_data.get('employee_id', ''))
        if stored_rate:
            return stored_rate
            
        # Use department/position-based rates
        standard_rates = self.qq_billing_model['standard_rates']
        
        # Try to match position keywords
        for position, rate in standard_rates.items():
            if position.replace('_', ' ') in employee_name or position in department:
                return rate
                
        # Default rate based on department
        department_rates = {
            'construction': 55.0,
            'engineering': 75.0,
            'management': 85.0,
            'operations': 65.0
        }
        
        return department_rates.get(department, 50.0)  # Default fallback rate
        
    def _calculate_total_amount(self, hours: float, rate: float, record_data: Dict[str, Any]) -> float:
        """Calculate total amount for record"""
        
        # Check if total amount is explicitly provided
        if 'total_amount' in record_data and record_data['total_amount']:
            try:
                return float(record_data['total_amount'])
            except (ValueError, TypeError):
                pass
                
        # Calculate from hours and rate
        base_amount = hours * rate
        
        # Apply any multipliers (overtime, etc.)
        overtime_multiplier = 1.0
        if hours > 8:  # Overtime after 8 hours
            regular_amount = 8 * rate
            overtime_hours = hours - 8
            overtime_amount = overtime_hours * rate * 1.5  # 1.5x for overtime
            base_amount = regular_amount + overtime_amount
            
        return round(base_amount, 2)
        
    def _determine_department(self, record_data: Dict[str, Any]) -> str:
        """Determine department from record data"""
        
        # First check explicit department field
        if 'department' in record_data and record_data['department']:
            return str(record_data['department']).title()
            
        # Try to infer from other fields
        project_code = record_data.get('project_code', '').lower()
        description = record_data.get('description', '').lower()
        employee_name = record_data.get('employee_name', '').lower()
        
        department_mappings = self.qq_billing_model['department_mappings']
        
        all_text = f"{project_code} {description} {employee_name}"
        
        for dept, keywords in department_mappings.items():
            if any(keyword in all_text for keyword in keywords):
                return dept.title()
                
        return 'General'
        
    def _get_stored_employee_rate(self, employee_id: str) -> Optional[float]:
        """Get stored hourly rate for employee"""
        
        if not employee_id:
            return None
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT current_rate FROM employee_rates WHERE employee_id = ?',
                (employee_id,)
            )
            result = cursor.fetchone()
            
        return result[0] if result else None
        
    def _calculate_accuracy_score(self, record_data: Dict[str, Any]) -> float:
        """Calculate accuracy score for record"""
        
        accuracy_factors = []
        
        # Check numeric field consistency
        hours = record_data.get('hours_worked', 0)
        rate = record_data.get('hourly_rate', 0)
        total = record_data.get('total_amount', 0)
        
        if hours and rate and total:
            expected_total = float(hours) * float(rate)
            accuracy = 1.0 - abs(expected_total - float(total)) / max(expected_total, float(total))
            accuracy_factors.append(accuracy)
            
        # Check date validity
        date_str = record_data.get('date', '')
        if date_str:
            try:
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    accuracy_factors.append(1.0)
                else:
                    accuracy_factors.append(0.5)
            except:
                accuracy_factors.append(0.0)
        else:
            accuracy_factors.append(0.7)  # Missing date gets moderate score
            
        # Check data type consistency
        try:
            float(hours)
            accuracy_factors.append(1.0)
        except:
            accuracy_factors.append(0.0)
            
        return sum(accuracy_factors) / len(accuracy_factors) if accuracy_factors else 0.5
        
    def _calculate_completeness_score(self, record_data: Dict[str, Any]) -> float:
        """Calculate completeness score for record"""
        
        essential_fields = ['employee_name', 'hours_worked', 'date']
        important_fields = ['project_code', 'hourly_rate', 'department']
        optional_fields = ['description', 'approved_by', 'cost_center']
        
        total_score = 0.0
        
        # Essential fields (60% weight)
        essential_present = sum(1 for field in essential_fields if record_data.get(field))
        total_score += (essential_present / len(essential_fields)) * 0.6
        
        # Important fields (30% weight)
        important_present = sum(1 for field in important_fields if record_data.get(field))
        total_score += (important_present / len(important_fields)) * 0.3
        
        # Optional fields (10% weight)
        optional_present = sum(1 for field in optional_fields if record_data.get(field))
        total_score += (optional_present / len(optional_fields)) * 0.1
        
        return total_score
        
    def _detect_anomalies(self, records: List[BillingRecord]) -> List[Dict[str, Any]]:
        """Detect anomalies in billing records"""
        
        anomalies = []
        rules = self.qq_billing_model['anomaly_detection_rules']
        
        # Calculate statistics for outlier detection
        hours_list = [r.hours_worked for r in records]
        rates_list = [r.hourly_rate for r in records]
        
        if hours_list:
            avg_hours = sum(hours_list) / len(hours_list)
            avg_rate = sum(rates_list) / len(rates_list)
            
            for record in records:
                # Check for excessive hours
                if record.hours_worked > rules['excessive_hours_daily']:
                    anomalies.append({
                        'type': 'Excessive Hours',
                        'record_id': record.record_id,
                        'employee': record.employee_name,
                        'hours': record.hours_worked,
                        'threshold': rules['excessive_hours_daily'],
                        'severity': 'HIGH'
                    })
                    
                # Check for zero/low rates
                if record.hourly_rate < rules['zero_rate_threshold']:
                    anomalies.append({
                        'type': 'Zero/Low Rate',
                        'record_id': record.record_id,
                        'employee': record.employee_name,
                        'rate': record.hourly_rate,
                        'severity': 'MEDIUM'
                    })
                    
                # Check for outlier rates
                if record.hourly_rate > avg_rate * rules['outlier_rate_multiplier']:
                    anomalies.append({
                        'type': 'Outlier Rate',
                        'record_id': record.record_id,
                        'employee': record.employee_name,
                        'rate': record.hourly_rate,
                        'average': avg_rate,
                        'severity': 'MEDIUM'
                    })
                    
        # Check for duplicate entries
        self._check_duplicate_entries(records, anomalies, rules)
        
        return anomalies
        
    def _check_duplicate_entries(self, records: List[BillingRecord], 
                                anomalies: List[Dict[str, Any]], 
                                rules: Dict[str, float]):
        """Check for potential duplicate entries"""
        
        # Group by employee and date
        employee_date_records = {}
        
        for record in records:
            key = f"{record.employee_id}_{record.date}"
            if key not in employee_date_records:
                employee_date_records[key] = []
            employee_date_records[key].append(record)
            
        # Check for potential duplicates
        for key, record_group in employee_date_records.items():
            if len(record_group) > 1:
                # Check similarity
                for i, record1 in enumerate(record_group):
                    for record2 in record_group[i+1:]:
                        similarity = self._calculate_record_similarity(record1, record2)
                        
                        if similarity > rules['duplicate_entry_tolerance']:
                            anomalies.append({
                                'type': 'Potential Duplicate',
                                'record_id_1': record1.record_id,
                                'record_id_2': record2.record_id,
                                'employee': record1.employee_name,
                                'similarity': similarity,
                                'severity': 'HIGH'
                            })
                            
    def _calculate_record_similarity(self, record1: BillingRecord, record2: BillingRecord) -> float:
        """Calculate similarity between two records"""
        
        similarity_factors = []
        
        # Compare numeric fields
        if record1.hours_worked == record2.hours_worked:
            similarity_factors.append(1.0)
        else:
            diff = abs(record1.hours_worked - record2.hours_worked)
            similarity_factors.append(max(0, 1 - diff / max(record1.hours_worked, record2.hours_worked)))
            
        if record1.hourly_rate == record2.hourly_rate:
            similarity_factors.append(1.0)
        else:
            diff = abs(record1.hourly_rate - record2.hourly_rate)
            similarity_factors.append(max(0, 1 - diff / max(record1.hourly_rate, record2.hourly_rate)))
            
        # Compare text fields
        if record1.project_code == record2.project_code:
            similarity_factors.append(1.0)
        else:
            similarity_factors.append(0.0)
            
        if record1.description == record2.description:
            similarity_factors.append(1.0)
        else:
            similarity_factors.append(0.5 if record1.description and record2.description else 0.0)
            
        return sum(similarity_factors) / len(similarity_factors)
        
    def _calculate_processing_quality(self, records: List[BillingRecord], 
                                     anomalies: List[Dict[str, Any]]) -> float:
        """Calculate overall processing quality score"""
        
        if not records:
            return 0.0
            
        # Average accuracy and completeness scores
        avg_accuracy = sum(r.qq_accuracy_score for r in records) / len(records)
        avg_completeness = sum(r.qq_completeness_score for r in records) / len(records)
        
        # Anomaly impact
        anomaly_rate = len(anomalies) / len(records)
        anomaly_impact = max(0, 1 - anomaly_rate * 2)  # Penalize anomalies
        
        # Weighted quality score
        weights = self.qq_billing_model['data_quality_weights']
        quality_score = (
            avg_accuracy * weights['accuracy'] +
            avg_completeness * weights['completeness'] +
            anomaly_impact * weights['consistency'] +
            0.9 * weights['timeliness'] +  # Assume good timeliness
            0.85 * weights['validity']     # Assume good validity
        )
        
        return quality_score
        
    def _determine_validation_status(self, quality_score: float, 
                                   anomalies: List[Dict[str, Any]]) -> str:
        """Determine validation status"""
        
        thresholds = self.qq_billing_model['validation_thresholds']
        
        high_severity_anomalies = len([a for a in anomalies if a.get('severity') == 'HIGH'])
        
        if quality_score >= thresholds['minimum_accuracy_score'] and high_severity_anomalies == 0:
            return 'VALIDATED'
        elif quality_score >= 0.7 and high_severity_anomalies <= 2:
            return 'WARNING'
        else:
            return 'REQUIRES_REVIEW'
            
    def _store_processed_report(self, report: ProcessedBillingReport):
        """Store processed report in database"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Store report
            cursor.execute('''
                INSERT INTO billing_reports
                (report_id, source_filename, processing_timestamp, total_records,
                 total_hours, total_amount, date_range_start, date_range_end,
                 departments, employees_count, qq_processing_quality,
                 anomalies_detected, validation_status, created_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.report_id,
                report.source_filename,
                report.processing_timestamp,
                report.total_records,
                report.total_hours,
                report.total_amount,
                report.date_range_start,
                report.date_range_end,
                json.dumps(report.departments),
                report.employees_count,
                report.qq_processing_quality,
                json.dumps(report.anomalies_detected),
                report.validation_status,
                datetime.now().isoformat()
            ))
            
            # Store individual records
            for record in report.records:
                cursor.execute('''
                    INSERT INTO billing_records
                    (record_id, report_id, project_code, employee_id, employee_name,
                     date, hours_worked, hourly_rate, total_amount, department,
                     cost_center, billing_category, description, approved_by,
                     qq_accuracy_score, qq_completeness_score, created_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.record_id,
                    report.report_id,
                    record.project_code,
                    record.employee_id,
                    record.employee_name,
                    record.date,
                    record.hours_worked,
                    record.hourly_rate,
                    record.total_amount,
                    record.department,
                    record.cost_center,
                    record.billing_category,
                    record.description,
                    record.approved_by,
                    record.qq_accuracy_score,
                    record.qq_completeness_score,
                    datetime.now().isoformat()
                ))
                
            conn.commit()
            
    def get_billing_dashboard_data(self) -> Dict[str, Any]:
        """Get billing dashboard data"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get recent reports
            cursor.execute('''
                SELECT * FROM billing_reports
                ORDER BY created_timestamp DESC
                LIMIT 10
            ''')
            
            recent_reports = []
            for row in cursor.fetchall():
                recent_reports.append({
                    'report_id': row[0],
                    'source_filename': row[1],
                    'total_records': row[3],
                    'total_hours': row[4],
                    'total_amount': row[5],
                    'validation_status': row[12],
                    'qq_processing_quality': row[10]
                })
                
            # Get summary statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_reports,
                    SUM(total_records) as total_records,
                    SUM(total_hours) as total_hours,
                    SUM(total_amount) as total_amount,
                    AVG(qq_processing_quality) as avg_quality
                FROM billing_reports
            ''')
            
            summary = cursor.fetchone()
            
        return {
            'recent_reports': recent_reports,
            'summary_stats': {
                'total_reports_processed': summary[0] or 0,
                'total_billing_records': summary[1] or 0,
                'total_hours_tracked': summary[2] or 0,
                'total_amount_processed': summary[3] or 0,
                'average_quality_score': summary[4] or 0
            },
            'processing_capabilities': {
                'supported_formats': list(self.supported_formats),
                'qq_enhancement_active': True,
                'anomaly_detection_enabled': True,
                'automatic_validation': True
            },
            'timestamp': datetime.now().isoformat()
        }

def create_billing_report_processor():
    """Factory function for billing report processor"""
    return BillingReportProcessor()