"""
Robust CSV Parser for Large MTD Files

This module provides a specialized parser for handling large Month-to-Date CSV files
that may cause memory issues with standard parsers.
"""

import os
import csv
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RobustCSVParser:
    """Robust CSV parser designed for handling large Month-to-Date files efficiently"""
    
    def __init__(self, file_path: str, chunk_size: int = 10000):
        """
        Initialize the parser
        
        Args:
            file_path: Path to the CSV file
            chunk_size: Number of rows to process in each chunk
        """
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.filename = os.path.basename(file_path)
        self.header_row = None
        self.columns = None
        self._detect_header()
    
    def _detect_header(self) -> None:
        """
        Automatically detect the header row in the CSV file
        This helps handle files with varying header positions
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8-sig') as f:
                # Read first 20 rows to find the most likely header
                sample_rows = []
                for _ in range(20):
                    line = f.readline().strip()
                    if line:
                        sample_rows.append(line.split(','))
                    if len(sample_rows) >= 20:
                        break
                
                # Look for rows that contain typical header fields
                header_keywords = ['timestamp', 'driver', 'time', 'date', 'vehicle', 'asset', 'location', 'event']
                best_row_idx = -1
                best_score = -1
                
                for idx, row in enumerate(sample_rows):
                    score = 0
                    for cell in row:
                        cell_lower = cell.lower().strip('"\'')
                        for keyword in header_keywords:
                            if keyword in cell_lower:
                                score += 1
                    
                    if score > best_score:
                        best_score = score
                        best_row_idx = idx
                
                if best_row_idx >= 0:
                    self.header_row = best_row_idx
                    self.columns = [col.strip('"\'') for col in sample_rows[best_row_idx]]
                else:
                    # Fall back to first row as header if detection fails
                    self.header_row = 0
                    self.columns = [col.strip('"\'') for col in sample_rows[0]]
                
                logger.info(f"Detected header row at index {self.header_row}: {self.columns}")
        except Exception as e:
            logger.error(f"Error detecting header: {str(e)}")
            # Default to first row if there's an error
            self.header_row = 0
            self.columns = None
    
    def parse_for_date(self, target_date: str) -> Dict[str, Any]:
        """
        Parse the CSV file for records matching the target date
        
        Args:
            target_date: Target date in YYYY-MM-DD format
            
        Returns:
            Dictionary with parsed data for the target date
        """
        logger.info(f"Parsing file {self.filename} for date {target_date}")
        
        # Initialize results
        results = {
            'file_path': self.file_path,
            'filename': self.filename,
            'target_date': target_date,
            'records': [],
            'total_rows': 0,
            'matched_rows': 0,
            'error_rows': 0
        }
        
        # Determine file type based on filename or content
        file_type = self._detect_file_type()
        results['file_type'] = file_type
        
        try:
            # Use pandas to read in chunks for memory efficiency
            chunk_reader = pd.read_csv(
                self.file_path, 
                chunksize=self.chunk_size,
                skiprows=self.header_row,
                header=0,
                encoding='utf-8-sig',
                on_bad_lines='skip',
                low_memory=False
            )
            
            for chunk_num, chunk in enumerate(chunk_reader):
                logger.debug(f"Processing chunk {chunk_num+1}")
                results['total_rows'] += len(chunk)
                
                # Find date column if it exists
                date_column = self._find_date_column(chunk)
                if not date_column:
                    logger.warning(f"Could not find date column in {self.filename}")
                    continue
                
                # Filter for the target date
                if date_column in chunk.columns:
                    # Convert date column to string for comparison
                    chunk[date_column] = chunk[date_column].astype(str)
                    
                    # Filter rows containing the target date
                    date_mask = chunk[date_column].str.contains(target_date, na=False)
                    if date_mask.any():
                        matching_rows = chunk[date_mask]
                        results['matched_rows'] += len(matching_rows)
                        
                        # Process each matching row
                        for _, row in matching_rows.iterrows():
                            try:
                                processed_row = self._process_row(row, file_type)
                                if processed_row:
                                    results['records'].append(processed_row)
                            except Exception as e:
                                results['error_rows'] += 1
                                logger.error(f"Error processing row: {str(e)}")
            
            logger.info(f"Completed parsing {self.filename}: {results['matched_rows']} rows matched")
            return results
            
        except Exception as e:
            logger.error(f"Error parsing CSV file {self.filename}: {str(e)}")
            results['error'] = str(e)
            return results
    
    def _detect_file_type(self) -> str:
        """
        Detect the type of file (Driving History or Activity Detail)
        based on filename or content
        """
        filename_lower = self.filename.lower()
        
        if 'driving' in filename_lower or 'driver' in filename_lower or 'driverhistory' in filename_lower:
            return 'driving_history'
        elif 'activity' in filename_lower or 'detail' in filename_lower:
            return 'activity_detail'
        else:
            # Check column headers if available
            if self.columns:
                columns_str = ' '.join(self.columns).lower()
                if 'driving' in columns_str or 'driver' in columns_str:
                    return 'driving_history'
                elif 'activity' in columns_str or 'ignition' in columns_str:
                    return 'activity_detail'
            
            # Default to unknown
            return 'unknown'
    
    def _find_date_column(self, data_chunk: pd.DataFrame) -> Optional[str]:
        """Find the column that contains date information"""
        date_keywords = ['date', 'time', 'timestamp']
        
        for col in data_chunk.columns:
            col_lower = col.lower()
            # Check if column name contains date keywords
            if any(keyword in col_lower for keyword in date_keywords):
                return col
                
        # If no obvious date column found, try to detect based on content
        for col in data_chunk.columns:
            # Check first few non-null values for date patterns
            sample = data_chunk[col].dropna().head(5)
            if len(sample) > 0:
                for val in sample:
                    if isinstance(val, str) and self._looks_like_date(val):
                        return col
        
        return None
    
    def _looks_like_date(self, value: str) -> bool:
        """Check if a string looks like a date"""
        if not isinstance(value, str):
            return False
            
        # Common date patterns
        date_patterns = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
            '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S'
        ]
        
        for pattern in date_patterns:
            try:
                datetime.strptime(value, pattern)
                return True
            except ValueError:
                continue
                
        # Check for date-like patterns with digits and separators
        import re
        date_regex = re.compile(r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}')
        return bool(date_regex.search(value))
    
    def _process_row(self, row: pd.Series, file_type: str) -> Dict[str, Any]:
        """
        Process a row based on the file type
        
        Args:
            row: The pandas Series representing a row
            file_type: Type of file (driving_history or activity_detail)
            
        Returns:
            Processed row as a dictionary
        """
        processed = dict(row)
        
        # Add file type metadata
        processed['_source_file'] = self.filename
        processed['_file_type'] = file_type
        
        # Additional processing based on file type
        if file_type == 'driving_history':
            return self._process_driving_history_row(processed)
        elif file_type == 'activity_detail':
            return self._process_activity_detail_row(processed)
        else:
            return processed
    
    def _process_driving_history_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Process a row from driving history file"""
        # Try to extract key information
        try:
            # Standardize column names for driver name
            for col in row:
                if 'driver' in col.lower() and 'name' in col.lower():
                    row['driver_name'] = row[col]
                elif 'driver' in col.lower():
                    if not 'driver_name' in row:
                        row['driver_name'] = row[col]
                        
            # Standardize column names for asset/vehicle
            for col in row:
                if 'asset' in col.lower() or 'vehicle' in col.lower():
                    row['asset_id'] = row[col]
            
            # Process timestamps
            for col in row:
                if 'time' in col.lower() or 'date' in col.lower():
                    # Don't override if already set
                    if not 'timestamp' in row:
                        row['timestamp'] = row[col]
        except Exception as e:
            logger.warning(f"Error standardizing driving history row: {str(e)}")
            
        return row
    
    def _process_activity_detail_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Process a row from activity detail file"""
        # Try to extract key information
        try:
            # Standardize column names for event type
            for col in row:
                if 'event' in col.lower() or 'activity' in col.lower():
                    row['event_type'] = row[col]
                    
            # Standardize column names for location
            for col in row:
                if 'location' in col.lower() or 'address' in col.lower():
                    row['location'] = row[col]
                    
            # Process timestamps
            for col in row:
                if 'time' in col.lower() or 'date' in col.lower():
                    # Don't override if already set
                    if not 'timestamp' in row:
                        row['timestamp'] = row[col]
        except Exception as e:
            logger.warning(f"Error standardizing activity detail row: {str(e)}")
            
        return row

def process_mtd_files_for_date(file_paths: List[str], target_date: str) -> Dict[str, Any]:
    """
    Process multiple MTD files for a specific date
    
    Args:
        file_paths: List of file paths to process
        target_date: Target date in YYYY-MM-DD format
        
    Returns:
        Dictionary with processed data
    """
    results = {
        'target_date': target_date,
        'files_processed': 0,
        'total_rows': 0,
        'matched_rows': 0,
        'error_rows': 0,
        'driving_history': [],
        'activity_detail': [],
        'unknown': []
    }
    
    for file_path in file_paths:
        try:
            parser = RobustCSVParser(file_path)
            file_results = parser.parse_for_date(target_date)
            
            results['files_processed'] += 1
            results['total_rows'] += file_results.get('total_rows', 0)
            results['matched_rows'] += file_results.get('matched_rows', 0)
            results['error_rows'] += file_results.get('error_rows', 0)
            
            file_type = file_results.get('file_type', 'unknown')
            if file_type == 'driving_history':
                results['driving_history'].extend(file_results.get('records', []))
            elif file_type == 'activity_detail':
                results['activity_detail'].extend(file_results.get('records', []))
            else:
                results['unknown'].extend(file_results.get('records', []))
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            results['error_rows'] += 1
    
    logger.info(f"Completed processing {results['files_processed']} files for date {target_date}")
    logger.info(f"Found {len(results['driving_history'])} driving history records and {len(results['activity_detail'])} activity detail records")
    
    return results