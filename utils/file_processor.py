"""
File Processor Module

This module handles file uploads, processing, and routing to appropriate domain-specific modules.
It serves as the central ingestion pipeline for all SYSTEMSMITH data sources.
"""
import os
import json
import logging
import importlib
import re
import shutil
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from werkzeug.utils import secure_filename

# Configure logging
logger = logging.getLogger(__name__)

# Define allowed file extensions
ALLOWED_EXTENSIONS = {
    'xlsx', 'xlsm', 'xls',  # Excel
    'csv',                  # CSV
    'json',                 # JSON
    'pdf'                   # PDF
}

# File type pattern matching
FILE_TYPE_PATTERNS = {
    'fringe': [
        r'fringe',
        r'benefit',
        r'auto\s*fringe',
        r'monthly\s*benefit'
    ],
    'billing': [
        r'bill',
        r'invoice',
        r'eq\s*monthly\s*billing',
        r'ragle\s*eq\s*billing',
        r'select\s*eq\s*billing'
    ],
    'maintenance': [
        r'maint',
        r'service',
        r'repair',
        r'wo\s*detail',
        r'work\s*order'
    ],
    'activity': [
        r'activ',
        r'usage',
        r'gps\s*efficiency',
        r'hours',
        r'fleet\s*util'
    ],
    'fuel': [
        r'fuel',
        r'wex',
        r'gas',
        r'transaction'
    ]
}

# Processing history file
PROCESSING_HISTORY_FILE = os.path.join('data', 'processing_history.json')

def allowed_file(filename: str) -> bool:
    """
    Check if a filename has an allowed extension
    
    Args:
        filename (str): Filename to check
        
    Returns:
        bool: True if allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename (str): Name of the file
        
    Returns:
        str: File extension with dot (e.g., ".xlsx")
    """
    return os.path.splitext(filename)[1].lower()

def _detect_file_type(filename: str) -> str:
    """
    Detect file type based on filename patterns
    
    Args:
        filename (str): Name of the file
        
    Returns:
        str: Detected file type or "unknown"
    """
    filename_lower = filename.lower()
    
    for file_type, patterns in FILE_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, filename_lower):
                return file_type
    
    return "unknown"

def validate_file(file_path: str) -> Dict[str, Any]:
    """
    Validate a file before processing
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        Dict[str, Any]: Validation result
    """
    if not os.path.exists(file_path):
        return {
            'valid': False,
            'message': f'File not found: {file_path}'
        }
    
    filename = os.path.basename(file_path)
    if not allowed_file(filename):
        return {
            'valid': False,
            'message': f'File type not allowed: {filename}'
        }
    
    # Additional validations could be added here (e.g., file size limits)
    
    return {
        'valid': True,
        'file_type': _detect_file_type(filename),
        'extension': _get_file_extension(filename),
        'message': 'File is valid'
    }

def _get_processor_module(extension: str) -> Optional[str]:
    """
    Get the appropriate processor module for a file extension
    
    Args:
        extension (str): File extension (without dot)
        
    Returns:
        Optional[str]: Module path or None if not supported
    """
    extension = extension.lower().lstrip('.')
    
    if extension in ['xlsx', 'xlsm', 'xls']:
        return 'utils.parsers.excel_parser'
    elif extension == 'csv':
        return 'utils.parsers.csv_parser'
    elif extension == 'json':
        return 'utils.parsers.json_parser'
    elif extension == 'pdf':
        return 'utils.parsers.pdf_parser'
    else:
        return None

def process_file(file_path: str, file_type: str = 'auto', user_id: Optional[str] = None) -> Dict[str, Any]:
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
        # Validate file
        validation = validate_file(file_path)
        if not validation['valid']:
            return {
                'success': False,
                'message': validation['message']
            }
        
        # Get file info
        filename = os.path.basename(file_path)
        extension = _get_file_extension(filename).lstrip('.')
        
        # Auto-detect file type if not specified
        auto_detected = False
        if file_type == 'auto':
            file_type = validation['file_type']
            auto_detected = True
            
            # If still unknown, use filename to guess
            if file_type == 'unknown':
                file_type = _detect_file_type(filename)
                
        # Get the appropriate processor module
        module_path = _get_processor_module(extension)
        if not module_path:
            return {
                'success': False,
                'message': f'Unsupported file type: {extension}'
            }
        
        # Import the processor module
        try:
            processor_module = importlib.import_module(module_path)
        except ImportError as e:
            logger.error(f"Error importing processor module {module_path}: {e}")
            return {
                'success': False,
                'message': f'Processor module not available: {e}'
            }
        
        # Process the file
        logger.info(f"Processing file {filename} with {module_path}, type={file_type}")
        processor_result = processor_module.process_file(file_path, file_type)
        
        # Process results based on file type (domain-specific logic)
        domain_processing = _process_domain_specific(file_path, file_type, processor_result)
        
        # Create result metadata
        result = {
            'success': True,
            'message': 'File processed successfully',
            'details': {
                'file_type': file_type,
                'auto_detected': auto_detected,
                'processor_module': module_path,
                'processor_result': processor_result,
                'domain_processing': domain_processing
            }
        }
        
        # Record processing history
        _record_processing(file_path, filename, file_type, auto_detected, True, user_id)
        
        return result
        
    except Exception as e:
        logger.exception(f"Error processing file {file_path}: {e}")
        
        # Record failure in processing history
        try:
            _record_processing(file_path, os.path.basename(file_path), file_type, False, False, user_id, str(e))
        except Exception as history_error:
            logger.error(f"Error recording processing history: {history_error}")
        
        return {
            'success': False,
            'message': f'Error processing file: {str(e)}'
        }

def _process_domain_specific(file_path: str, file_type: str, processor_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process domain-specific logic based on file type
    
    Args:
        file_path (str): Path to the file
        file_type (str): Type of file
        processor_result (Dict[str, Any]): Result from the file processor
        
    Returns:
        Dict[str, Any]: Domain-specific processing result
    """
    # Check if processor was successful
    if not processor_result.get('success', False):
        return {
            'success': False,
            'message': 'File processor did not succeed'
        }
    
    # Process based on file type
    try:
        if file_type == 'fringe':
            # Import fringe processor only when needed
            from utils.domain.fringe_processor import process_fringe
            return process_fringe(processor_result)
        
        elif file_type == 'billing':
            # Import billing processor only when needed
            from utils.domain.billing_processor import process_billing
            return process_billing(processor_result)
        
        elif file_type == 'maintenance':
            # Import maintenance processor only when needed
            from utils.domain.maintenance_processor import process_maintenance
            return process_maintenance(processor_result)
        
        elif file_type == 'activity':
            # Import activity processor only when needed
            from utils.domain.activity_processor import process_activity
            return process_activity(processor_result)
        
        elif file_type == 'fuel':
            # Import fuel processor only when needed
            from utils.domain.fuel_processor import process_fuel
            return process_fuel(processor_result)
        
        else:
            # Generic processing for other file types
            return {
                'success': True,
                'message': 'No domain-specific processing available for this file type',
                'stats': {
                    'processed_records': processor_result.get('record_count', 0)
                }
            }
            
    except ImportError as e:
        logger.warning(f"Domain processor for {file_type} not available: {e}")
        return {
            'success': False,
            'message': f'Domain processor module not available: {e}'
        }
    except Exception as e:
        logger.exception(f"Error in domain processing for {file_type}: {e}")
        return {
            'success': False,
            'message': f'Error in domain processing: {str(e)}',
            'error': str(e)
        }

def _record_processing(file_path: str, filename: str, file_type: str, auto_detected: bool, 
                      success: bool, user_id: Optional[str] = None, error: Optional[str] = None) -> None:
    """
    Record file processing in history
    
    Args:
        file_path (str): Path to the file
        filename (str): Name of the file
        file_type (str): Type of file
        auto_detected (bool): Whether file type was auto-detected
        success (bool): Whether processing was successful
        user_id (str, optional): ID of the user who processed the file
        error (str, optional): Error message if processing failed
    """
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(PROCESSING_HISTORY_FILE), exist_ok=True)
    
    # Load existing history
    history = []
    if os.path.exists(PROCESSING_HISTORY_FILE):
        try:
            with open(PROCESSING_HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except Exception as e:
            logger.error(f"Error loading processing history: {e}")
    
    # Create new entry
    entry = {
        'file_path': file_path,
        'filename': filename,
        'file_type': file_type,
        'auto_detected': auto_detected,
        'success': success,
        'user_id': user_id,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if error:
        entry['error'] = error
    
    # Add to history
    history.append(entry)
    
    # Limit history size
    if len(history) > 1000:
        history = history[-1000:]
    
    # Save updated history
    try:
        with open(PROCESSING_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving processing history: {e}")

def get_processing_history(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get file processing history
    
    Args:
        limit (int): Maximum number of records to return
        
    Returns:
        List[Dict[str, Any]]: Processing history
    """
    if not os.path.exists(PROCESSING_HISTORY_FILE):
        return []
    
    try:
        with open(PROCESSING_HISTORY_FILE, 'r') as f:
            history = json.load(f)
        
        # Sort by timestamp (newest first) and limit
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return history[:limit]
    
    except Exception as e:
        logger.error(f"Error loading processing history: {e}")
        return []

def reprocess_file(file_path: str, file_type: str = None, user_id: str = None) -> Dict[str, Any]:
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
        return {
            'success': False,
            'message': f'File not found: {file_path}'
        }
    
    # If no file type specified, look up in history
    if file_type is None:
        history = get_processing_history()
        for entry in history:
            if entry.get('file_path') == file_path:
                file_type = entry.get('file_type', 'auto')
                break
    
    # Process the file
    return process_file(file_path, file_type, user_id)

def compare_files(file1_path: str, file2_path: str, 
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
    # Import comparison module
    try:
        from utils.file_comparison import compare_files_internal
        
        return compare_files_internal(file1_path, file2_path, sheet_name)
    except ImportError as e:
        logger.error(f"Error importing comparison module: {e}")
        return {
            'success': False,
            'message': f'Comparison module not available: {e}'
        }
    except Exception as e:
        logger.exception(f"Error comparing files: {e}")
        return {
            'success': False,
            'message': f'Error comparing files: {str(e)}'
        }