"""
File Processor Module for SYSTEMSMITH

Provides intelligent processing of uploaded files for asset tracking and management.
Automatically detects file types, extracts and normalizes data, and integrates with
the database.
"""

import os
import logging
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Union, Optional, Any
from pathlib import Path

from utils.parsers import ExcelParser, ExcelParserException
from utils.mappers.employee_mapper import EmployeeMapper
from utils.cya import backup_file, log_event
from utils.kaizen import process_asset_identifiers

logger = logging.getLogger(__name__)

# Constants
PROCESSED_FILES_DB = "data/cache/processed_files.db"
MAX_BACKUP_FILES = 10  # Maximum number of backup files to keep per file type

class FileProcessorException(Exception):
    """Exception raised for errors in the file processor."""
    pass

class FileProcessor:
    """Intelligent file processor for various file types"""
    
    def __init__(self, user_id: Optional[int] = None):
        """
        Initialize the file processor.
        
        Args:
            user_id: ID of the user performing the processing
        """
        self.user_id = user_id
        self._initialize_processed_files_db()
        self.employee_mapper = EmployeeMapper()
    
    def _initialize_processed_files_db(self):
        """Initialize the processed files database"""
        os.makedirs(os.path.dirname(PROCESSED_FILES_DB), exist_ok=True)
        
        conn = sqlite3.connect(PROCESSED_FILES_DB)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                processed_path TEXT NOT NULL,
                row_count INTEGER,
                column_count INTEGER,
                user_id INTEGER,
                processing_time REAL,
                processing_date TEXT NOT NULL,
                status TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        # Create indices for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_name ON processed_files(file_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_type ON processed_files(file_type)')
        
        conn.commit()
        conn.close()
    
    def process_file(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """
        Process a file and extract normalized data.
        
        Args:
            file_path: Path to the file to process
            file_type: Type of file (billing, utilization, etc.). If None, will attempt to detect.
            
        Returns:
            Dictionary with processing results
        """
        start_time = datetime.now()
        
        try:
            # Create a parser for the file
            parser = ExcelParser(file_path, file_type, user_id=self.user_id)
            
            # Load the file
            df = parser.load()
            
            # Normalize the data
            df = parser.normalize()
            
            # Apply smart employee mapping if the file contains asset identifiers
            has_asset_col = any(col in df.columns for col in ['asset_id', 'asset_identifier', 'unit_number', 'equipment_id'])
            has_employee_col = any(col in df.columns for col in ['employee', 'operator', 'driver', 'technician'])
            
            if has_asset_col:
                asset_col = next(col for col in df.columns if col in ['asset_id', 'asset_identifier', 'unit_number', 'equipment_id'])
                employee_col = next((col for col in df.columns if col in ['employee', 'operator', 'driver', 'technician']), None)
                
                # Apply employee mapping
                df = self.employee_mapper.match_dataframe(df, asset_col, employee_col)
                
                # Process asset identifiers for continuous improvement
                asset_identifiers = df[asset_col].dropna().unique().tolist()
                process_asset_identifiers(asset_identifiers)
            
            # Save normalized data to CSV
            output_path = parser.save_to_csv()
            
            # Record the processing
            processing_time = (datetime.now() - start_time).total_seconds()
            summary = parser.get_summary()
            
            self._record_processing(
                file_path, 
                summary['file_type'], 
                output_path, 
                len(df), 
                len(df.columns), 
                processing_time, 
                'SUCCESS', 
                summary
            )
            
            return {
                'status': 'success',
                'file_name': os.path.basename(file_path),
                'file_type': summary['file_type'],
                'detected_type': summary['detected_type'],
                'sheet_name': summary['sheet_name'],
                'row_count': len(df),
                'column_count': len(df.columns),
                'output_path': output_path,
                'processing_time': processing_time,
                'summary': summary
            }
            
        except Exception as e:
            # Record the error
            error_message = str(e)
            logger.error(f"Failed to process file {file_path}: {error_message}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            file_type_guess = file_type or self._guess_file_type(file_path)
            
            self._record_processing(
                file_path, 
                file_type_guess, 
                '', 
                0, 
                0, 
                processing_time, 
                'ERROR', 
                {'error': error_message}
            )
            
            return {
                'status': 'error',
                'file_name': os.path.basename(file_path),
                'error': error_message,
                'file_type': file_type_guess,
                'processing_time': processing_time
            }
    
    def _guess_file_type(self, file_path: str) -> str:
        """
        Guess the file type based on filename.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Guessed file type
        """
        file_name_lower = os.path.basename(file_path).lower()
        
        if "billing" in file_name_lower or "ragle eq" in file_name_lower or "select eq" in file_name_lower:
            return "billing"
        elif "utilization" in file_name_lower or "fleet" in file_name_lower:
            return "utilization"
        elif "work order" in file_name_lower or "wo " in file_name_lower or "rag wo" in file_name_lower:
            return "work_order"
        elif "attendance" in file_name_lower or "late start" in file_name_lower or "early end" in file_name_lower:
            return "attendance"
        elif "gps" in file_name_lower or "gauge" in file_name_lower or "efficiency" in file_name_lower:
            return "gps"
        else:
            return "unknown"
    
    def _record_processing(self, file_path: str, file_type: str, processed_path: str, 
                          row_count: int, column_count: int, processing_time: float, 
                          status: str, metadata: Dict[str, Any]):
        """
        Record file processing details.
        
        Args:
            file_path: Path to the original file
            file_type: Type of file
            processed_path: Path to the processed file
            row_count: Number of rows processed
            column_count: Number of columns processed
            processing_time: Time taken to process the file (seconds)
            status: Processing status ('SUCCESS' or 'ERROR')
            metadata: Additional metadata about the processing
        """
        try:
            conn = sqlite3.connect(PROCESSED_FILES_DB)
            cursor = conn.cursor()
            
            # Insert record
            cursor.execute('''
                INSERT INTO processed_files 
                (file_name, file_path, file_type, processed_path, row_count, column_count, 
                 user_id, processing_time, processing_date, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                os.path.basename(file_path),
                file_path,
                file_type,
                processed_path,
                row_count,
                column_count,
                self.user_id,
                processing_time,
                datetime.now().isoformat(),
                status,
                str(metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to record processing: {e}")
    
    def get_processing_history(self, file_type: str = None, limit: int = 50, 
                              status: str = None) -> List[Dict[str, Any]]:
        """
        Get file processing history.
        
        Args:
            file_type: Filter by file type
            limit: Maximum number of records to return
            status: Filter by status ('SUCCESS' or 'ERROR')
            
        Returns:
            List of processing history records
        """
        try:
            conn = sqlite3.connect(PROCESSED_FILES_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM processed_files"
            params = []
            
            where_clauses = []
            if file_type:
                where_clauses.append("file_type = ?")
                params.append(file_type)
            
            if status:
                where_clauses.append("status = ?")
                params.append(status)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += " ORDER BY processing_date DESC LIMIT ?"
            params.append(limit)
            
            # Execute query
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            history = [dict(row) for row in rows]
            
            conn.close()
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get processing history: {e}")
            return []
    
    def reprocess_file(self, file_id: int) -> Dict[str, Any]:
        """
        Reprocess a previously processed file.
        
        Args:
            file_id: ID of the file to reprocess
            
        Returns:
            Dictionary with processing results
        """
        try:
            conn = sqlite3.connect(PROCESSED_FILES_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get file details
            cursor.execute("SELECT * FROM processed_files WHERE id = ?", (file_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                raise FileProcessorException(f"File with ID {file_id} not found")
            
            file_details = dict(row)
            conn.close()
            
            # Check if file exists
            file_path = file_details['file_path']
            if not os.path.exists(file_path):
                raise FileProcessorException(f"Original file not found: {file_path}")
            
            # Reprocess the file
            return self.process_file(file_path, file_details['file_type'])
            
        except Exception as e:
            logger.error(f"Failed to reprocess file: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def compare_files(self, file_id1: int, file_id2: int) -> Dict[str, Any]:
        """
        Compare two processed files for differences.
        
        Args:
            file_id1: ID of the first file
            file_id2: ID of the second file
            
        Returns:
            Dictionary with comparison results
        """
        try:
            conn = sqlite3.connect(PROCESSED_FILES_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get file details
            cursor.execute("SELECT * FROM processed_files WHERE id = ?", (file_id1,))
            row1 = cursor.fetchone()
            
            cursor.execute("SELECT * FROM processed_files WHERE id = ?", (file_id2,))
            row2 = cursor.fetchone()
            
            if not row1 or not row2:
                conn.close()
                raise FileProcessorException(f"One or both files not found")
            
            file1 = dict(row1)
            file2 = dict(row2)
            conn.close()
            
            # Check if files exist
            path1 = file1['processed_path']
            path2 = file2['processed_path']
            
            if not os.path.exists(path1) or not os.path.exists(path2):
                raise FileProcessorException(f"One or both processed files not found")
            
            # Load the files
            df1 = pd.read_csv(path1)
            df2 = pd.read_csv(path2)
            
            # Compare the files
            comparison = {
                'file1': {
                    'id': file1['id'],
                    'name': file1['file_name'],
                    'type': file1['file_type'],
                    'row_count': len(df1),
                    'column_count': len(df1.columns)
                },
                'file2': {
                    'id': file2['id'],
                    'name': file2['file_name'],
                    'type': file2['file_type'],
                    'row_count': len(df2),
                    'column_count': len(df2.columns)
                },
                'diff': {
                    'row_count_diff': len(df2) - len(df1),
                    'column_count_diff': len(df2.columns) - len(df1.columns),
                    'shared_columns': sorted(list(set(df1.columns) & set(df2.columns))),
                    'file1_only_columns': sorted(list(set(df1.columns) - set(df2.columns))),
                    'file2_only_columns': sorted(list(set(df2.columns) - set(df1.columns)))
                }
            }
            
            # If files have common columns and are of same type, do deeper comparison
            if comparison['diff']['shared_columns'] and file1['file_type'] == file2['file_type']:
                # For each shared column, calculate differences
                column_diffs = {}
                for col in comparison['diff']['shared_columns']:
                    if col in df1 and col in df2:
                        # Count non-matching values
                        try:
                            # Convert to same dtype if possible for accurate comparison
                            s1 = df1[col].astype(str) if pd.api.types.is_object_dtype(df1[col]) else df1[col]
                            s2 = df2[col].astype(str) if pd.api.types.is_object_dtype(df2[col]) else df2[col]
                            
                            # Create masks for matching rows
                            if s1.dtype == s2.dtype:
                                # Check for NaNs separately
                                nan_match = (s1.isna() & s2.isna())
                                
                                # Check for matching values
                                val_match = (s1 == s2) | (s1.isna() & s2.isna())
                                
                                diff_count = (~val_match).sum()
                                percent_diff = (diff_count / len(s1)) * 100 if len(s1) > 0 else 0
                                
                                column_diffs[col] = {
                                    'diff_count': int(diff_count),
                                    'percent_diff': round(percent_diff, 2)
                                }
                        except Exception as e:
                            column_diffs[col] = {
                                'error': str(e)
                            }
                
                comparison['diff']['column_diffs'] = column_diffs
            
            # Calculate overall difference
            if file1['file_type'] == file2['file_type'] and comparison['diff']['shared_columns']:
                # Calculate average percentage difference across columns
                col_diffs = [d['percent_diff'] for c, d in column_diffs.items() 
                            if 'percent_diff' in d]
                
                if col_diffs:
                    avg_diff = sum(col_diffs) / len(col_diffs)
                    comparison['diff']['overall_percent_diff'] = round(avg_diff, 2)
                    
                    # Determine match quality
                    if avg_diff < 5:
                        comparison['diff']['match_quality'] = 'Excellent'
                    elif avg_diff < 15:
                        comparison['diff']['match_quality'] = 'Good'
                    elif avg_diff < 30:
                        comparison['diff']['match_quality'] = 'Fair'
                    else:
                        comparison['diff']['match_quality'] = 'Poor'
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare files: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }