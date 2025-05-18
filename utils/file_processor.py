"""
File processing utilities

This module provides utilities for processing Excel and CSV files,
particularly for the PM allocation reconciliation functionality.
"""

import os
import re
import pandas as pd
import numpy as np
from datetime import datetime
import logging

def get_file_list_by_pattern(directory, pattern=None, exclude_pattern=None):
    """
    Get a list of files in a directory that match a regex pattern
    
    Args:
        directory (str): Directory to search in
        pattern (str, optional): Regex pattern to match filenames
        exclude_pattern (str, optional): Regex pattern to exclude filenames
        
    Returns:
        list: List of matching filenames
    """
    if not os.path.exists(directory):
        return []
        
    files = os.listdir(directory)
    
    if pattern:
        pattern_re = re.compile(pattern, re.IGNORECASE)
        files = [f for f in files if pattern_re.search(f)]
        
    if exclude_pattern:
        exclude_re = re.compile(exclude_pattern, re.IGNORECASE)
        files = [f for f in files if not exclude_re.search(f)]
        
    return files

def read_allocation_file(file_path):
    """
    Read an allocation file (Excel or CSV) and extract the data
    
    Args:
        file_path (str): Path to the file to read
        
    Returns:
        pd.DataFrame: DataFrame containing the allocation data
    """
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        raise

def compare_allocation_files(original_file, updated_file):
    """
    Compare original and updated allocation files
    
    Args:
        original_file (str): Path to the original allocation file
        updated_file (str): Path to the updated allocation file
        
    Returns:
        dict: Comparison results with differences
    """
    try:
        # Read the files
        original_df = read_allocation_file(original_file)
        updated_df = read_allocation_file(updated_file)
        
        # Simple comparison for demonstration
        # In a real application, this would do more sophisticated matching and comparison
        
        # Calculate total cost changes
        original_total = original_df.select_dtypes(include=[np.number]).sum().sum()
        updated_total = updated_df.select_dtypes(include=[np.number]).sum().sum()
        
        difference = updated_total - original_total
        percent_change = (difference / original_total) * 100 if original_total != 0 else 0
        
        return {
            'original_file': os.path.basename(original_file),
            'updated_file': os.path.basename(updated_file),
            'original_total': original_total,
            'updated_total': updated_total,
            'difference': difference,
            'percent_change': percent_change,
            'comparison_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'has_changes': abs(percent_change) > 0.01,  # Consider changes greater than 0.01% as significant
            'changes_by_column': {}  # In a real application, this would contain detailed changes by column
        }
    except Exception as e:
        logging.error(f"Error comparing files: {str(e)}")
        raise

def batch_process_allocation_files(file_paths):
    """
    Process multiple allocation files in batch
    
    Args:
        file_paths (list): List of file paths to process
        
    Returns:
        dict: Batch processing results
    """
    results = {
        'processed_files': [],
        'total_files': len(file_paths),
        'success_count': 0,
        'error_count': 0,
        'total_amount': 0,
        'changes_detected': False,
        'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'file_results': []
    }
    
    # If we have only one file, we'll just analyze it
    if len(file_paths) == 1:
        try:
            df = read_allocation_file(file_paths[0])
            total = df.select_dtypes(include=[np.number]).sum().sum()
            
            file_result = {
                'filename': os.path.basename(file_paths[0]),
                'status': 'success',
                'total_amount': total,
                'has_changes': False
            }
            
            results['processed_files'].append(os.path.basename(file_paths[0]))
            results['success_count'] += 1
            results['total_amount'] += total
            results['file_results'].append(file_result)
            
        except Exception as e:
            logging.error(f"Error processing file {file_paths[0]}: {str(e)}")
            results['error_count'] += 1
            results['file_results'].append({
                'filename': os.path.basename(file_paths[0]),
                'status': 'error',
                'error_message': str(e)
            })
    
    # If we have multiple files, we'll compare them
    elif len(file_paths) > 1:
        # Assume the first file is the base file (or original)
        base_file = file_paths[0]
        comparison_files = file_paths[1:]
        
        # Process the base file
        try:
            base_df = read_allocation_file(base_file)
            base_total = base_df.select_dtypes(include=[np.number]).sum().sum()
            
            results['processed_files'].append(os.path.basename(base_file))
            results['success_count'] += 1
            results['total_amount'] += base_total
            results['file_results'].append({
                'filename': os.path.basename(base_file),
                'status': 'success',
                'total_amount': base_total,
                'is_base_file': True,
                'has_changes': False
            })
            
            # Compare each other file to the base file
            for comparison_file in comparison_files:
                try:
                    comparison_result = compare_allocation_files(base_file, comparison_file)
                    
                    if comparison_result['has_changes']:
                        results['changes_detected'] = True
                        
                    results['processed_files'].append(os.path.basename(comparison_file))
                    results['success_count'] += 1
                    results['total_amount'] += comparison_result['updated_total']
                    results['file_results'].append({
                        'filename': os.path.basename(comparison_file),
                        'status': 'success',
                        'total_amount': comparison_result['updated_total'],
                        'difference': comparison_result['difference'],
                        'percent_change': comparison_result['percent_change'],
                        'has_changes': comparison_result['has_changes'],
                        'comparison_result': comparison_result
                    })
                    
                except Exception as e:
                    logging.error(f"Error comparing files {base_file} and {comparison_file}: {str(e)}")
                    results['error_count'] += 1
                    results['file_results'].append({
                        'filename': os.path.basename(comparison_file),
                        'status': 'error',
                        'error_message': str(e)
                    })
                    
        except Exception as e:
            logging.error(f"Error processing base file {base_file}: {str(e)}")
            results['error_count'] += 1
            results['file_results'].append({
                'filename': os.path.basename(base_file),
                'status': 'error',
                'error_message': str(e),
                'is_base_file': True
            })
    
    return results