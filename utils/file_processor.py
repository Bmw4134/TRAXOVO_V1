"""
File Processor Module

This module handles file uploads, processing, and routing to appropriate domain-specific modules.
It serves as the central ingestion pipeline for all SYSTEMSMITH data sources.
"""

import os
import json
import shutil
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from utils.cya import backup_file, log_action
from utils.parsers.excel_parser import ExcelParser

# Setup logging
logger = logging.getLogger(__name__)

# Constants
UPLOAD_FOLDER = os.path.join('data', 'uploads')
PROCESSED_FOLDER = os.path.join('data', 'processed')
BACKUP_FOLDER = 'backups'

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)

# File type definitions
FILE_TYPES = {
    'fringe': {
        'description': 'Auto Fringe Files',
        'module': 'compliance',
        'patterns': ['fringe', 'auto fringe', 'autofringe', 'bw updated'],
        'extensions': ['.xlsx', '.xlsm', '.xls'],
        'processor': 'process_fringe_file'
    },
    'billing': {
        'description': 'Monthly Billing & Allocations',
        'module': 'billing',
        'patterns': ['eq billing', 'eq monthly', 'billing', 'allocations', 'profit report'],
        'extensions': ['.xlsx', '.xlsm', '.xls', '.csv'],
        'processor': 'process_billing_file'
    },
    'maintenance': {
        'description': 'Work Order Reports',
        'module': 'maintenance',
        'patterns': ['wo detail', 'maintenance', 'uvc', 'heavy eq expenses', 'repair'],
        'extensions': ['.xlsx', '.xlsm', '.xls', '.csv'],
        'processor': 'process_maintenance_file'
    },
    'activity': {
        'description': 'Activity Detail & Driving History',
        'module': 'activity',
        'patterns': ['gps', 'efficiency', 'work zone', 'workzone', 'driver history'],
        'extensions': ['.xlsx', '.xlsm', '.xls', '.csv'],
        'processor': 'process_activity_file'
    },
    'utilization': {
        'description': 'Time-on-Site & Utilization',
        'module': 'utilization',
        'patterns': ['utilization', 'fleet', 'usage', 'hours report'],
        'extensions': ['.xlsx', '.xlsm', '.xls', '.csv'],
        'processor': 'process_utilization_file'
    },
    'compliance': {
        'description': 'BPP Compliance Documents',
        'module': 'compliance',
        'patterns': ['compliance', 'bpp', 'tax', 'property'],
        'extensions': ['.xlsx', '.xlsm', '.xls', '.pdf'],
        'processor': 'process_compliance_file'
    },
    'fuel': {
        'description': 'Fuel Transaction Reports',
        'module': 'fuel',
        'patterns': ['wex', 'fuel', 'transaction', 'card report'],
        'extensions': ['.xlsx', '.xlsm', '.xls', '.csv', '.pdf'],
        'processor': 'process_fuel_file'
    },
    'tolls': {
        'description': 'Toll Transaction Reports',
        'module': 'tolls',
        'patterns': ['ntta', 'toll', 'trx'],
        'extensions': ['.xlsx', '.xlsm', '.xls', '.csv', '.pdf'],
        'processor': 'process_toll_file'
    },
    'employee': {
        'description': 'Employee Assignment & Status',
        'module': 'personnel',
        'patterns': ['employee', 'personnel', 'assignment', 'daily late'],
        'extensions': ['.xlsx', '.xlsm', '.xls', '.csv'],
        'processor': 'process_employee_file'
    },
    'gauge': {
        'description': 'Gauge API Data',
        'module': 'api',
        'patterns': ['gauge', 'api', 'json'],
        'extensions': ['.json'],
        'processor': 'process_gauge_file'
    }
}

class FileProcessor:
    """
    Handles file uploads, processing, and routing to appropriate modules
    """
    
    def __init__(self):
        """
        Initialize the file processor
        """
        self.excel_parser = ExcelParser()
        self.processing_history = []
        
    def _get_file_extension(self, filename: str) -> str:
        """
        Get file extension from filename
        
        Args:
            filename (str): Name of the file
            
        Returns:
            str: File extension with dot (e.g., ".xlsx")
        """
        _, extension = os.path.splitext(filename)
        return extension.lower()
    
    def _detect_file_type(self, filename: str) -> str:
        """
        Detect file type based on filename patterns
        
        Args:
            filename (str): Name of the file
            
        Returns:
            str: Detected file type or "unknown"
        """
        filename_lower = filename.lower()
        extension = self._get_file_extension(filename)
        
        # Check each defined file type
        for file_type, config in FILE_TYPES.items():
            # Check if extension matches
            if extension in config['extensions']:
                # Check if filename contains any of the patterns
                for pattern in config['patterns']:
                    if pattern in filename_lower:
                        return file_type
        
        # Default to unknown
        return "unknown"
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a file before processing
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            'is_valid': False,
            'file_path': file_path,
            'errors': [],
            'warnings': []
        }
        
        # Check if file exists
        if not os.path.exists(file_path):
            result['errors'].append(f"File does not exist: {file_path}")
            return result
        
        # Get file extension
        extension = self._get_file_extension(file_path)
        
        # Validate based on extension
        if extension in ['.xlsx', '.xlsm', '.xls']:
            try:
                # Try to open with pandas
                xls = pd.ExcelFile(file_path)
                
                # Check if file has any sheets
                if len(xls.sheet_names) == 0:
                    result['warnings'].append("Excel file has no sheets")
                
                # Check if sheets have data
                empty_sheets = []
                for sheet in xls.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet)
                    if df.empty:
                        empty_sheets.append(sheet)
                
                if empty_sheets:
                    result['warnings'].append(f"The following sheets are empty: {', '.join(empty_sheets)}")
                
                # File is valid if we got this far
                result['is_valid'] = True
                result['sheet_count'] = len(xls.sheet_names)
                result['sheets'] = xls.sheet_names
                
            except Exception as e:
                result['errors'].append(f"Invalid Excel file: {str(e)}")
        
        elif extension == '.csv':
            try:
                # Try to open with pandas
                df = pd.read_csv(file_path)
                
                # Check if file has data
                if df.empty:
                    result['warnings'].append("CSV file is empty")
                
                # File is valid if we got this far
                result['is_valid'] = True
                result['row_count'] = len(df)
                result['column_count'] = len(df.columns)
                
            except Exception as e:
                result['errors'].append(f"Invalid CSV file: {str(e)}")
        
        elif extension == '.json':
            try:
                # Try to open and parse JSON
                with open(file_path, 'r') as f:
                    json_data = json.load(f)
                
                # File is valid if we got this far
                result['is_valid'] = True
                
                # Check if JSON is an array or object
                if isinstance(json_data, list):
                    result['item_count'] = len(json_data)
                    result['structure'] = 'array'
                else:
                    result['key_count'] = len(json_data.keys())
                    result['structure'] = 'object'
                
            except Exception as e:
                result['errors'].append(f"Invalid JSON file: {str(e)}")
        
        elif extension == '.pdf':
            # Basic check for PDF - just check if file is not empty
            if os.path.getsize(file_path) == 0:
                result['errors'].append("PDF file is empty")
            else:
                result['is_valid'] = True
                result['file_size'] = os.path.getsize(file_path)
        
        else:
            result['errors'].append(f"Unsupported file type: {extension}")
        
        return result
    
    def process_file(self, file_path: str, file_type: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Process an uploaded file
        
        Args:
            file_path (str): Path to the file
            file_type (str, optional): Type of file (if None, will be auto-detected)
            user_id (str, optional): ID of the user who uploaded the file
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            filename = os.path.basename(file_path)
            logger.info(f"Processing file: {filename}")
            
            # Create result structure
            result = {
                'success': False,
                'file_path': file_path,
                'filename': filename,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'message': "",
                'details': {}
            }
            
            # First validate the file
            validation = self.validate_file(file_path)
            if not validation['is_valid']:
                result['message'] = f"File validation failed: {', '.join(validation['errors'])}"
                result['details']['validation'] = validation
                
                # Log the failed validation
                log_action('file_validation_failed', user_id, file_path, 
                           {'errors': validation['errors'], 'warnings': validation['warnings']}, 
                           'error')
                
                return result
            
            # Store validation info
            result['details']['validation'] = validation
            
            # Detect file type if not provided
            if file_type is None or file_type == 'auto':
                detected_type = self._detect_file_type(filename)
                file_type = detected_type
                result['details']['file_type'] = file_type
                result['details']['auto_detected'] = True
            else:
                result['details']['file_type'] = file_type
                result['details']['auto_detected'] = False
            
            # Backup the file
            backup_path = backup_file(file_path, user_id)
            result['details']['backup_path'] = backup_path
            
            # Log the upload
            log_action('file_upload', user_id, file_path, 
                       {'file_type': file_type, 'backup_path': backup_path}, 
                       'success')
            
            # Get file extension
            extension = self._get_file_extension(filename)
            
            # Process based on file type and extension
            processor_result = {}
            
            # Excel file processing
            if extension in ['.xlsx', '.xlsm', '.xls']:
                # Parse with Excel parser
                parse_result = self.excel_parser.parse_excel(file_path)
                if parse_result['success']:
                    processor_result = parse_result
                    
                    # Save parsing results
                    metadata_file = f"{file_path}.meta.json"
                    with open(metadata_file, 'w') as f:
                        # Convert DataFrames to list of dicts for JSON serialization
                        serializable_result = parse_result.copy()
                        for sheet_name, sheet_data in serializable_result.get('sheets', {}).items():
                            if 'data' in sheet_data and isinstance(sheet_data['data'], pd.DataFrame):
                                sheet_data['data'] = sheet_data['data'].to_dict('records')
                        
                        json.dump(serializable_result, f, indent=2, default=str)
                    
                    result['details']['metadata_file'] = metadata_file
                    
                    # Route to appropriate domain-specific processor if available
                    if file_type in FILE_TYPES:
                        module_name = FILE_TYPES[file_type]['module']
                        processor_name = FILE_TYPES[file_type]['processor']
                        
                        # Try to import and call the specific processor
                        try:
                            # Dynamic import
                            module_path = f"utils.processors.{module_name}"
                            processor_module = __import__(module_path, fromlist=[processor_name])
                            
                            # Get the processor function
                            processor_func = getattr(processor_module, processor_name)
                            
                            # Call the processor
                            domain_result = processor_func(file_path, parse_result, user_id)
                            
                            # Add domain result to result
                            result['details']['domain_processing'] = domain_result
                            
                            # Log the domain processing
                            log_action('domain_processing', user_id, file_path,
                                      {'module': module_name, 'processor': processor_name, 
                                       'result': domain_result.get('success', False)},
                                      'success' if domain_result.get('success', False) else 'error')
                            
                        except (ImportError, AttributeError) as e:
                            # Module or function not found, log but continue
                            logger.warning(f"Domain processor not found: {e}")
                            result['details']['domain_processing'] = {
                                'success': False,
                                'message': f"Domain processor not found: {module_path}.{processor_name}",
                                'error': str(e)
                            }
                            
                            # Log the error
                            log_action('domain_processing_error', user_id, file_path,
                                      {'module': module_name, 'processor': processor_name, 'error': str(e)},
                                      'error')
                        
                        except Exception as e:
                            # Other processing error
                            logger.error(f"Error in domain processing: {e}")
                            result['details']['domain_processing'] = {
                                'success': False,
                                'message': f"Error in domain processing: {str(e)}",
                                'error': str(e)
                            }
                            
                            # Log the error
                            log_action('domain_processing_error', user_id, file_path,
                                      {'module': module_name, 'processor': processor_name, 'error': str(e)},
                                      'error')
                else:
                    # Excel parsing failed
                    result['message'] = f"Excel parsing failed: {parse_result.get('error', 'Unknown error')}"
                    result['details']['parse_result'] = parse_result
                    
                    # Log the failed parsing
                    log_action('file_parsing_failed', user_id, file_path,
                              {'error': parse_result.get('error', 'Unknown error')},
                              'error')
                    
                    return result
            
            # CSV file processing
            elif extension == '.csv':
                try:
                    # Read CSV file
                    df = pd.read_csv(file_path)
                    
                    # Basic CSV processing
                    processor_result = {
                        'success': True,
                        'row_count': len(df),
                        'column_count': len(df.columns),
                        'columns': df.columns.tolist(),
                        'file_path': file_path
                    }
                    
                    # Save a sample of the data
                    sample_rows = min(10, len(df))
                    processor_result['sample'] = df.head(sample_rows).to_dict('records')
                    
                    # Save as processed data
                    metadata_file = f"{file_path}.meta.json"
                    with open(metadata_file, 'w') as f:
                        json.dump(processor_result, f, indent=2, default=str)
                    
                    result['details']['metadata_file'] = metadata_file
                    
                except Exception as e:
                    # CSV processing failed
                    result['message'] = f"CSV processing failed: {str(e)}"
                    result['details']['error'] = str(e)
                    
                    # Log the failed processing
                    log_action('file_processing_failed', user_id, file_path,
                              {'error': str(e)},
                              'error')
                    
                    return result
            
            # JSON file processing
            elif extension == '.json':
                try:
                    # Read JSON file
                    with open(file_path, 'r') as f:
                        json_data = json.load(f)
                    
                    # Basic JSON processing
                    processor_result = {
                        'success': True,
                        'file_path': file_path
                    }
                    
                    # Check if JSON is an array or object
                    if isinstance(json_data, list):
                        processor_result['item_count'] = len(json_data)
                        processor_result['structure'] = 'array'
                        
                        # Save a sample of the data
                        sample_items = min(5, len(json_data))
                        processor_result['sample'] = json_data[:sample_items]
                    else:
                        processor_result['key_count'] = len(json_data.keys())
                        processor_result['structure'] = 'object'
                        processor_result['keys'] = list(json_data.keys())
                    
                    # Save as processed data
                    metadata_file = f"{file_path}.meta.json"
                    with open(metadata_file, 'w') as f:
                        json.dump(processor_result, f, indent=2, default=str)
                    
                    result['details']['metadata_file'] = metadata_file
                    
                except Exception as e:
                    # JSON processing failed
                    result['message'] = f"JSON processing failed: {str(e)}"
                    result['details']['error'] = str(e)
                    
                    # Log the failed processing
                    log_action('file_processing_failed', user_id, file_path,
                              {'error': str(e)},
                              'error')
                    
                    return result
            
            # PDF file processing
            elif extension == '.pdf':
                # For now, just log that we received a PDF
                # Future: implement PDF text extraction
                processor_result = {
                    'success': True,
                    'file_path': file_path,
                    'file_size': os.path.getsize(file_path),
                    'message': "PDF received and backed up. Text extraction not yet implemented."
                }
                
                # Save as processed data
                metadata_file = f"{file_path}.meta.json"
                with open(metadata_file, 'w') as f:
                    json.dump(processor_result, f, indent=2, default=str)
                
                result['details']['metadata_file'] = metadata_file
            
            else:
                # Unsupported file type
                result['message'] = f"Unsupported file type: {extension}"
                
                # Log the unsupported file type
                log_action('unsupported_file_type', user_id, file_path,
                          {'extension': extension},
                          'error')
                
                return result
            
            # Mark as success
            result['success'] = True
            result['message'] = f"File processed successfully: {filename}"
            result['details']['processor_result'] = processor_result
            
            # Log successful processing
            log_action('file_processing_completed', user_id, file_path,
                      {'file_type': file_type, 'processor_result': processor_result.get('success', False)},
                      'success')
            
            # Add to processing history
            self.processing_history.append({
                'timestamp': datetime.now().isoformat(),
                'filename': filename,
                'file_path': file_path,
                'file_type': file_type,
                'user_id': user_id,
                'success': True
            })
            
            return result
            
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Error processing file {file_path}: {e}")
            
            # Log the error
            log_action('file_processing_error', user_id, file_path,
                      {'error': str(e)},
                      'error')
            
            # Add to processing history
            self.processing_history.append({
                'timestamp': datetime.now().isoformat(),
                'filename': filename if 'filename' in locals() else os.path.basename(file_path),
                'file_path': file_path,
                'file_type': file_type if 'file_type' in locals() else None,
                'user_id': user_id,
                'success': False,
                'error': str(e)
            })
            
            return {
                'success': False,
                'file_path': file_path,
                'message': f"Error processing file: {str(e)}",
                'details': {'error': str(e)}
            }
    
    def get_processing_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get file processing history
        
        Args:
            limit (int): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: Processing history
        """
        # Return most recent first
        return sorted(self.processing_history, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def reprocess_file(self, file_path: str, file_type: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Reprocess a previously uploaded file
        
        Args:
            file_path (str): Path to the file
            file_type (str, optional): Type of file (if None, will be auto-detected)
            user_id (str, optional): ID of the user who requested reprocessing
            
        Returns:
            Dict[str, Any]: Processing result
        """
        # Check if file exists
        if not os.path.exists(file_path):
            message = f"File not found: {file_path}"
            
            # Log the error
            log_action('file_reprocessing_error', user_id, file_path,
                      {'error': message},
                      'error')
            
            return {
                'success': False,
                'file_path': file_path,
                'message': message
            }
        
        # Log reprocessing attempt
        log_action('file_reprocessing_started', user_id, file_path,
                  {'file_type': file_type},
                  'info')
        
        # Process the file
        result = self.process_file(file_path, file_type, user_id)
        
        # Add reprocessing flag
        result['reprocessed'] = True
        
        return result
    
    def compare_files(self, file1_path: str, file2_path: str, 
                     sheet_name: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Compare two files and identify differences
        
        Args:
            file1_path (str): Path to the first file
            file2_path (str): Path to the second file
            sheet_name (str, optional): Name of the sheet to compare (for Excel files)
            user_id (str, optional): ID of the user who requested comparison
            
        Returns:
            Dict[str, Any]: Comparison result
        """
        # Check if files exist
        if not os.path.exists(file1_path):
            return {
                'success': False,
                'message': f"First file not found: {file1_path}"
            }
        
        if not os.path.exists(file2_path):
            return {
                'success': False,
                'message': f"Second file not found: {file2_path}"
            }
        
        # Get file extensions
        ext1 = self._get_file_extension(file1_path)
        ext2 = self._get_file_extension(file2_path)
        
        # For now, only compare Excel files
        if ext1 in ['.xlsx', '.xlsm', '.xls'] and ext2 in ['.xlsx', '.xlsm', '.xls']:
            from utils.cya import compare_excel_files
            
            # Log comparison attempt
            log_action('file_comparison_started', user_id, file1_path,
                      {'file2_path': file2_path, 'sheet_name': sheet_name},
                      'info')
            
            # Compare Excel files
            comparison = compare_excel_files(file1_path, file2_path, sheet_name)
            
            # Create result
            result = {
                'success': 'error' not in comparison,
                'file1_path': file1_path,
                'file2_path': file2_path,
                'comparison': comparison
            }
            
            if 'error' in comparison:
                result['message'] = f"Comparison failed: {comparison['error']}"
            else:
                result['message'] = f"Comparison complete: {comparison['total_diff_count']} differences found"
            
            return result
        else:
            message = f"File comparison not supported for extensions: {ext1} and {ext2}"
            
            # Log the error
            log_action('file_comparison_error', user_id, file1_path,
                      {'file2_path': file2_path, 'error': message},
                      'error')
            
            return {
                'success': False,
                'message': message
            }


# Module-level instance for easy access
file_processor = FileProcessor()

# Utility functions
def allowed_file(filename: str) -> bool:
    """
    Check if a filename has an allowed extension
    
    Args:
        filename (str): Filename to check
        
    Returns:
        bool: True if allowed, False otherwise
    """
    allowed_extensions = {'.xlsx', '.xlsm', '.xls', '.csv', '.json', '.pdf'}
    
    return os.path.splitext(filename)[1].lower() in allowed_extensions

def process_file(file_path: str, file_type: str = None, user_id: str = None) -> Dict[str, Any]:
    """
    Process a file using the module-level file processor
    
    Args:
        file_path (str): Path to the file
        file_type (str, optional): Type of file (if None, will be auto-detected)
        user_id (str, optional): ID of the user who uploaded the file
        
    Returns:
        Dict[str, Any]: Processing result
    """
    return file_processor.process_file(file_path, file_type, user_id)