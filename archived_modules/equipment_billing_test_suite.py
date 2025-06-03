"""
Complete Equipment Billing Process Testing Suite
End-to-end testing with authentic data validation
"""

import os
import pandas as pd
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EquipmentBillingProcessor:
    """Complete equipment billing process with authentic data validation"""
    
    def __init__(self):
        self.processed_data = {}
        self.validation_results = {}
        self.billing_summary = {}
        self.data_sources = []
        
    def upload_and_process_billing_file(self, file_path: str, file_type: str = 'auto') -> Dict[str, Any]:
        """Process uploaded billing file with comprehensive validation"""
        
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        try:
            # Determine file type
            if file_type == 'auto':
                if file_path.endswith('.xlsx') or file_path.endswith('.xlsm'):
                    file_type = 'excel'
                elif file_path.endswith('.csv'):
                    file_type = 'csv'
                else:
                    return {'error': 'Unsupported file format'}
            
            # Load data based on file type
            if file_type == 'excel':
                result = self._process_excel_billing_file(file_path)
            elif file_type == 'csv':
                result = self._process_csv_billing_file(file_path)
            else:
                return {'error': f'Unsupported file type: {file_type}'}
            
            # Store processing results
            self.data_sources.append({
                'file_path': file_path,
                'processed_at': datetime.now().isoformat(),
                'records_processed': result.get('records_processed', 0),
                'validation_status': result.get('validation_status', 'unknown')
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing billing file {file_path}: {e}")
            return {'error': f'Processing failed: {str(e)}'}
    
    def _process_excel_billing_file(self, file_path: str) -> Dict[str, Any]:
        """Process Excel billing file with sheet detection"""
        
        try:
            excel_file = pd.ExcelFile(file_path)
            sheets = excel_file.sheet_names
            
            results = {
                'file_path': file_path,
                'sheets_found': sheets,
                'sheets_processed': [],
                'total_records': 0,
                'billing_data': [],
                'equipment_list': [],
                'validation_status': 'processing'
            }
            
            # Process each sheet
            for sheet_name in sheets:
                sheet_result = self._process_sheet(excel_file, sheet_name, file_path)
                if sheet_result['success']:
                    results['sheets_processed'].append(sheet_result)
                    results['total_records'] += sheet_result['record_count']
                    
                    # Aggregate billing data
                    if sheet_result['data_type'] == 'billing':
                        results['billing_data'].extend(sheet_result['records'])
                    elif sheet_result['data_type'] == 'equipment':
                        results['equipment_list'].extend(sheet_result['records'])
            
            # Validate processed data
            validation = self._validate_billing_data(results)
            results['validation'] = validation
            results['validation_status'] = 'completed'
            
            # Generate summary
            summary = self._generate_billing_summary(results)
            results['summary'] = summary
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {e}")
            return {'error': f'Excel processing failed: {str(e)}'}
    
    def _process_sheet(self, excel_file, sheet_name: str, file_path: str) -> Dict[str, Any]:
        """Process individual Excel sheet"""
        
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Skip empty sheets
            if df.empty:
                return {'success': False, 'reason': 'empty_sheet'}
            
            # Detect data type based on columns
            columns = [str(col).lower() for col in df.columns]
            
            # Determine sheet type
            data_type = self._detect_sheet_type(columns)
            
            # Process based on detected type
            if data_type == 'billing':
                records = self._extract_billing_records(df)
            elif data_type == 'equipment':
                records = self._extract_equipment_records(df)
            elif data_type == 'driver':
                records = self._extract_driver_records(df)
            else:
                records = self._extract_generic_records(df)
            
            return {
                'success': True,
                'sheet_name': sheet_name,
                'data_type': data_type,
                'record_count': len(records),
                'records': records,
                'columns': list(df.columns)
            }
            
        except Exception as e:
            logger.error(f"Error processing sheet {sheet_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _detect_sheet_type(self, columns: List[str]) -> str:
        """Detect the type of data in the sheet"""
        
        billing_indicators = ['total', 'amount', 'revenue', 'billing', 'cost', 'charge']
        equipment_indicators = ['equipment', 'asset', 'unit', 'machine', 'fleet']
        driver_indicators = ['driver', 'operator', 'employee', 'name']
        
        billing_score = sum(1 for col in columns if any(indicator in col for indicator in billing_indicators))
        equipment_score = sum(1 for col in columns if any(indicator in col for indicator in equipment_indicators))
        driver_score = sum(1 for col in columns if any(indicator in col for indicator in driver_indicators))
        
        if billing_score >= 2:
            return 'billing'
        elif equipment_score >= 2:
            return 'equipment'
        elif driver_score >= 1:
            return 'driver'
        else:
            return 'generic'
    
    def _extract_billing_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract billing records from DataFrame"""
        
        records = []
        
        # Find key columns
        amount_cols = [col for col in df.columns if any(term in str(col).lower() 
                      for term in ['total', 'amount', 'revenue', 'billing'])]
        equipment_cols = [col for col in df.columns if any(term in str(col).lower() 
                         for term in ['equipment', 'asset', 'unit'])]
        date_cols = [col for col in df.columns if any(term in str(col).lower() 
                    for term in ['date', 'time', 'period'])]
        
        for _, row in df.iterrows():
            record = {
                'record_type': 'billing',
                'equipment_id': row[equipment_cols[0]] if equipment_cols else None,
                'amount': row[amount_cols[0]] if amount_cols else None,
                'date': row[date_cols[0]] if date_cols else None,
                'raw_data': row.to_dict()
            }
            
            # Clean and validate data
            if record['amount'] and pd.notna(record['amount']):
                try:
                    record['amount'] = float(record['amount'])
                except:
                    record['amount'] = 0
            
            records.append(record)
        
        return records
    
    def _extract_equipment_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract equipment records from DataFrame"""
        
        records = []
        
        # Find key columns
        id_cols = [col for col in df.columns if any(term in str(col).lower() 
                  for term in ['id', 'number', 'unit'])]
        name_cols = [col for col in df.columns if any(term in str(col).lower() 
                    for term in ['name', 'description', 'type'])]
        
        for _, row in df.iterrows():
            record = {
                'record_type': 'equipment',
                'equipment_id': row[id_cols[0]] if id_cols else None,
                'equipment_name': row[name_cols[0]] if name_cols else None,
                'raw_data': row.to_dict()
            }
            records.append(record)
        
        return records
    
    def _extract_driver_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract driver records from DataFrame"""
        
        records = []
        
        # Find key columns
        name_cols = [col for col in df.columns if any(term in str(col).lower() 
                    for term in ['name', 'driver', 'operator'])]
        
        for _, row in df.iterrows():
            record = {
                'record_type': 'driver',
                'driver_name': row[name_cols[0]] if name_cols else None,
                'raw_data': row.to_dict()
            }
            records.append(record)
        
        return records
    
    def _extract_generic_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract generic records from DataFrame"""
        
        records = []
        for _, row in df.iterrows():
            record = {
                'record_type': 'generic',
                'raw_data': row.to_dict()
            }
            records.append(record)
        
        return records
    
    def _process_csv_billing_file(self, file_path: str) -> Dict[str, Any]:
        """Process CSV billing file"""
        
        try:
            df = pd.read_csv(file_path)
            
            # Detect data type
            columns = [str(col).lower() for col in df.columns]
            data_type = self._detect_sheet_type(columns)
            
            # Extract records
            if data_type == 'billing':
                records = self._extract_billing_records(df)
            else:
                records = self._extract_generic_records(df)
            
            results = {
                'file_path': file_path,
                'data_type': data_type,
                'total_records': len(records),
                'records': records,
                'validation_status': 'completed'
            }
            
            # Validate data
            validation = self._validate_billing_data(results)
            results['validation'] = validation
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {e}")
            return {'error': f'CSV processing failed: {str(e)}'}
    
    def _validate_billing_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate processed billing data"""
        
        validation = {
            'total_records': results.get('total_records', 0),
            'valid_records': 0,
            'invalid_records': 0,
            'warnings': [],
            'errors': [],
            'summary': {}
        }
        
        billing_data = results.get('billing_data', [])
        
        for record in billing_data:
            is_valid = True
            
            # Check for required fields
            if not record.get('equipment_id'):
                validation['warnings'].append('Missing equipment ID')
                is_valid = False
            
            if not record.get('amount') or record.get('amount') == 0:
                validation['warnings'].append('Missing or zero amount')
                is_valid = False
            
            if is_valid:
                validation['valid_records'] += 1
            else:
                validation['invalid_records'] += 1
        
        # Calculate summary statistics
        if billing_data:
            amounts = [r.get('amount', 0) for r in billing_data if r.get('amount')]
            validation['summary'] = {
                'total_amount': sum(amounts),
                'average_amount': sum(amounts) / len(amounts) if amounts else 0,
                'record_count': len(billing_data)
            }
        
        return validation
    
    def _generate_billing_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate billing summary from processed data"""
        
        summary = {
            'processing_date': datetime.now().isoformat(),
            'file_processed': results.get('file_path', ''),
            'total_sheets': len(results.get('sheets_processed', [])),
            'total_records': results.get('total_records', 0),
            'data_quality': 'good' if results.get('validation', {}).get('valid_records', 0) > 0 else 'needs_review'
        }
        
        # Add financial summary if billing data exists
        billing_data = results.get('billing_data', [])
        if billing_data:
            amounts = [r.get('amount', 0) for r in billing_data if r.get('amount')]
            summary['financial'] = {
                'total_revenue': sum(amounts),
                'billing_records': len(billing_data),
                'average_billing': sum(amounts) / len(amounts) if amounts else 0
            }
        
        return summary
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        
        return {
            'files_processed': len(self.data_sources),
            'last_processed': self.data_sources[-1] if self.data_sources else None,
            'total_records': sum(source.get('records_processed', 0) for source in self.data_sources),
            'processing_summary': self.billing_summary
        }

# Global processor instance
billing_processor = EquipmentBillingProcessor()

# Flask Blueprint
billing_test_blueprint = Blueprint('billing_test', __name__)

@billing_test_blueprint.route('/equipment_billing_test')
def billing_test_dashboard():
    """Equipment billing test dashboard"""
    status = billing_processor.get_processing_status()
    return render_template('equipment_billing_test.html', status=status)

@billing_test_blueprint.route('/api/upload_billing_file', methods=['POST'])
def upload_billing_file():
    """Upload and process billing file"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        
        # Ensure uploads directory exists
        os.makedirs('uploads', exist_ok=True)
        
        # Save uploaded file
        file.save(file_path)
        
        # Process the file
        result = billing_processor.upload_and_process_billing_file(file_path)
        
        return jsonify(result)

@billing_test_blueprint.route('/api/process_existing_file', methods=['POST'])
def process_existing_file():
    """Process existing billing file"""
    
    data = request.json
    file_path = data.get('file_path')
    
    if not file_path:
        return jsonify({'error': 'File path required'}), 400
    
    result = billing_processor.upload_and_process_billing_file(file_path)
    return jsonify(result)

@billing_test_blueprint.route('/api/billing_test_status')
def billing_test_status():
    """Get billing test status"""
    
    status = billing_processor.get_processing_status()
    return jsonify(status)

def integrate_billing_test_suite(app):
    """Integrate billing test suite with main app"""
    app.register_blueprint(billing_test_blueprint, url_prefix='/billing_test')
    return billing_processor