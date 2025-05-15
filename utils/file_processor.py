"""
File Processor Module

This module processes files uploaded to the system. It provides a unified interface
for handling different file types (Excel, CSV, etc.) and extracting relevant information.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename

# Setup logging
logger = logging.getLogger(__name__)

class FileProcessor:
    """
    Base class for processing uploaded files
    """
    def __init__(self, file_path, file_type=None, user_id=0):
        """
        Initialize the file processor
        
        Args:
            file_path (str): Path to the file to process
            file_type (str, optional): Type of file ('excel', 'csv', etc). Detected automatically if None.
            user_id (int): ID of the user who uploaded the file
        """
        self.file_path = file_path
        self.original_filename = os.path.basename(file_path)
        self.file_type = file_type or self._detect_file_type()
        self.user_id = user_id
        self.processed_data = None
        self.metadata = {
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'upload_time': datetime.now().isoformat(),
            'user_id': self.user_id,
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        }
        
    def _detect_file_type(self):
        """
        Detect the file type based on extension
        
        Returns:
            str: Detected file type
        """
        _, ext = os.path.splitext(self.file_path)
        ext = ext.lower()
        
        if ext in ['.xlsx', '.xlsm', '.xls']:
            return 'excel'
        elif ext == '.csv':
            return 'csv'
        elif ext == '.json':
            return 'json'
        elif ext == '.pdf':
            return 'pdf'
        else:
            return 'unknown'
    
    def process(self):
        """
        Process the file and return the results
        
        Returns:
            dict: Processing results
        """
        if not os.path.exists(self.file_path):
            return {
                'success': False,
                'message': f"File not found: {self.file_path}",
                'data': None,
                'metadata': self.metadata
            }
        
        try:
            if self.file_type == 'excel':
                self.processed_data = self._process_excel()
            elif self.file_type == 'csv':
                self.processed_data = self._process_csv()
            elif self.file_type == 'json':
                self.processed_data = self._process_json()
            else:
                return {
                    'success': False,
                    'message': f"Unsupported file type: {self.file_type}",
                    'data': None,
                    'metadata': self.metadata
                }
            
            # Update metadata
            self.metadata['row_count'] = len(self.processed_data) if isinstance(self.processed_data, pd.DataFrame) else 0
            self.metadata['processing_time'] = datetime.now().isoformat()
            
            return {
                'success': True,
                'message': f"Successfully processed {self.file_type} file: {self.original_filename}",
                'data': self.processed_data,
                'metadata': self.metadata
            }
        except Exception as e:
            logger.error(f"Error processing file {self.file_path}: {e}")
            return {
                'success': False,
                'message': f"Error processing file: {str(e)}",
                'data': None,
                'metadata': self.metadata,
                'error': str(e)
            }
    
    def _process_excel(self):
        """
        Process Excel file
        
        Returns:
            pd.DataFrame: Processed data
        """
        # Read the Excel file
        df = pd.read_excel(self.file_path)
        return df
    
    def _process_csv(self):
        """
        Process CSV file
        
        Returns:
            pd.DataFrame: Processed data
        """
        # Read the CSV file
        df = pd.read_csv(self.file_path)
        return df
    
    def _process_json(self):
        """
        Process JSON file
        
        Returns:
            dict or list: Processed data
        """
        # Read the JSON file
        with open(self.file_path, 'r') as f:
            data = json.load(f)
        return data
    
    def save_processed_data(self, output_path=None):
        """
        Save processed data to a file
        
        Args:
            output_path (str, optional): Path to save the processed data. If None, uses a default path.
            
        Returns:
            str: Path to the saved file
        """
        if self.processed_data is None:
            raise ValueError("No processed data to save. Call process() first.")
        
        if output_path is None:
            # Generate a default output path
            filename, _ = os.path.splitext(self.original_filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join('data', 'processed')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{filename}_processed_{timestamp}.json")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the data based on its type
        if isinstance(self.processed_data, pd.DataFrame):
            # For DataFrames, convert to dict and save as JSON
            data_dict = self.processed_data.to_dict(orient='records')
            with open(output_path, 'w') as f:
                json.dump(data_dict, f, indent=2)
        elif isinstance(self.processed_data, (dict, list)):
            # For dict/list, save directly as JSON
            with open(output_path, 'w') as f:
                json.dump(self.processed_data, f, indent=2)
        else:
            # For other types, convert to string and save
            with open(output_path, 'w') as f:
                f.write(str(self.processed_data))
        
        # Update metadata with output path
        self.metadata['output_path'] = output_path
        
        return output_path
    
    def match_dataframe(self, employee_col="employee_name", asset_col="asset_id"):
        """
        Match employee names to assets in the dataframe
        
        Args:
            employee_col (str): Column name for employee names
            asset_col (str): Column name for asset IDs
            
        Returns:
            pd.DataFrame: DataFrame with matched employee names
        """
        if not isinstance(self.processed_data, pd.DataFrame):
            raise TypeError("Processed data must be a DataFrame to use match_dataframe")
        
        # Check if columns exist
        if employee_col not in self.processed_data.columns:
            raise ValueError(f"Column '{employee_col}' not found in DataFrame")
        if asset_col not in self.processed_data.columns:
            raise ValueError(f"Column '{asset_col}' not found in DataFrame")
        
        # Copy the dataframe to avoid modifying the original
        df = self.processed_data.copy()
        
        # This is a placeholder for actual matching logic
        # In a real implementation, this would use the employee mapper
        df['match_confidence'] = 0.85  # Placeholder confidence score
        
        return df


def process_file(file_path, file_type, user_id=0):
    """
    Process a file using the appropriate processor
    
    Args:
        file_path (str): Path to the file to process
        file_type (str): Type of file ('excel', 'csv', etc)
        user_id (int, optional): ID of the user who uploaded the file
        
    Returns:
        dict: Processing results
    """
    # Create and run the file processor
    processor = FileProcessor(file_path, file_type, user_id)
    return processor.process()


def allowed_file(filename, allowed_extensions=None):
    """
    Check if a file is allowed
    
    Args:
        filename (str): Name of the file to check
        allowed_extensions (list, optional): List of allowed extensions
        
    Returns:
        bool: True if file is allowed, False otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = {'xlsx', 'xls', 'csv', 'json', 'pdf'}
    
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions