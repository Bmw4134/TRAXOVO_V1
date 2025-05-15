"""
File Comparison Module

This module provides functions for comparing files of various types,
identifying differences, and reconciling conflicts.
"""
import os
import pandas as pd
import numpy as np
import difflib
import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union

# Configure logging
logger = logging.getLogger(__name__)

def compare_files_internal(file1_path: str, file2_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Compare two files and identify differences
    
    Args:
        file1_path (str): Path to the first file
        file2_path (str): Path to the second file
        sheet_name (Optional[str]): Name of the sheet to compare (for Excel files)
        
    Returns:
        Dict[str, Any]: Comparison result
    """
    result = {
        'success': False,
        'message': '',
        'file1_path': file1_path,
        'file2_path': file2_path,
        'sheet_name': sheet_name,
        'differences': {
            'added': [],
            'removed': [],
            'changed': []
        },
        'summary': {
            'total_differences': 0,
            'additions': 0,
            'removals': 0,
            'changes': 0
        }
    }
    
    try:
        # Check if files exist
        if not os.path.exists(file1_path):
            result['message'] = f"File 1 not found: {file1_path}"
            return result
        
        if not os.path.exists(file2_path):
            result['message'] = f"File 2 not found: {file2_path}"
            return result
        
        # Get file extensions
        file1_ext = os.path.splitext(file1_path)[1].lower()
        file2_ext = os.path.splitext(file2_path)[1].lower()
        
        # If different extensions, warn but continue with text comparison
        if file1_ext != file2_ext:
            result['warnings'] = [f"Files have different extensions: {file1_ext} vs {file2_ext}"]
        
        # Process based on file type
        if file1_ext in ['.xlsx', '.xls', '.xlsm']:
            result = compare_excel_files(file1_path, file2_path, sheet_name, result)
        elif file1_ext == '.csv':
            result = compare_csv_files(file1_path, file2_path, result)
        elif file1_ext == '.json':
            result = compare_json_files(file1_path, file2_path, result)
        else:
            # Default to text comparison
            result = compare_text_files(file1_path, file2_path, result)
        
        # Update summary
        result['summary']['additions'] = len(result['differences']['added'])
        result['summary']['removals'] = len(result['differences']['removed'])
        result['summary']['changes'] = len(result['differences']['changed'])
        result['summary']['total_differences'] = (
            result['summary']['additions'] + 
            result['summary']['removals'] + 
            result['summary']['changes']
        )
        
        # Set success flag
        result['success'] = True
        if result['summary']['total_differences'] == 0:
            result['message'] = "Files are identical"
        else:
            result['message'] = f"Found {result['summary']['total_differences']} differences"
        
        return result
        
    except Exception as e:
        logger.exception(f"Error comparing files: {e}")
        result['message'] = f"Error comparing files: {str(e)}"
        return result

def compare_excel_files(file1_path: str, file2_path: str, sheet_name: Optional[str], result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two Excel files
    
    Args:
        file1_path (str): Path to the first file
        file2_path (str): Path to the second file
        sheet_name (Optional[str]): Name of the sheet to compare
        result (Dict[str, Any]): Result dictionary to update
        
    Returns:
        Dict[str, Any]: Updated result dictionary
    """
    try:
        # Read Excel files
        excel1 = pd.ExcelFile(file1_path)
        excel2 = pd.ExcelFile(file2_path)
        
        # Get sheet names
        sheets1 = excel1.sheet_names
        sheets2 = excel2.sheet_names
        result['sheets_info'] = {
            'file1_sheets': sheets1,
            'file2_sheets': sheets2,
            'common_sheets': [s for s in sheets1 if s in sheets2],
            'only_in_file1': [s for s in sheets1 if s not in sheets2],
            'only_in_file2': [s for s in sheets2 if s not in sheets1]
        }
        
        # If sheet name is specified, compare only that sheet
        if sheet_name:
            if sheet_name in sheets1 and sheet_name in sheets2:
                result = compare_excel_sheets(excel1, excel2, sheet_name, result)
            else:
                if sheet_name not in sheets1:
                    result['message'] = f"Sheet '{sheet_name}' not found in file 1"
                else:
                    result['message'] = f"Sheet '{sheet_name}' not found in file 2"
                result['success'] = False
                return result
        else:
            # Compare all common sheets
            common_sheets = result['sheets_info']['common_sheets']
            result['sheet_comparisons'] = {}
            
            for sheet in common_sheets:
                sheet_result = {'differences': {'added': [], 'removed': [], 'changed': []}}
                sheet_result = compare_excel_sheets(excel1, excel2, sheet, sheet_result)
                result['sheet_comparisons'][sheet] = sheet_result
                
                # Aggregate differences
                result['differences']['added'].extend(
                    [f"{sheet}:{diff}" for diff in sheet_result['differences']['added']]
                )
                result['differences']['removed'].extend(
                    [f"{sheet}:{diff}" for diff in sheet_result['differences']['removed']]
                )
                result['differences']['changed'].extend(
                    [f"{sheet}:{diff}" for diff in sheet_result['differences']['changed']]
                )
            
            # Add any missing sheets to the differences
            for sheet in result['sheets_info']['only_in_file1']:
                result['differences']['removed'].append(f"Sheet '{sheet}' only in file 1")
            
            for sheet in result['sheets_info']['only_in_file2']:
                result['differences']['added'].append(f"Sheet '{sheet}' only in file 2")
        
        return result
    
    except Exception as e:
        logger.exception(f"Error comparing Excel files: {e}")
        result['message'] = f"Error comparing Excel files: {str(e)}"
        result['success'] = False
        return result

def compare_excel_sheets(excel1: pd.ExcelFile, excel2: pd.ExcelFile, sheet_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two Excel sheets
    
    Args:
        excel1 (pd.ExcelFile): First Excel file
        excel2 (pd.ExcelFile): Second Excel file
        sheet_name (str): Name of the sheet to compare
        result (Dict[str, Any]): Result dictionary to update
        
    Returns:
        Dict[str, Any]: Updated result dictionary
    """
    try:
        # Read the sheets
        df1 = excel1.parse(sheet_name)
        df2 = excel2.parse(sheet_name)
        
        # Add basic info
        result['sheet_info'] = {
            'name': sheet_name,
            'file1_rows': len(df1),
            'file1_columns': len(df1.columns),
            'file2_rows': len(df2),
            'file2_columns': len(df2.columns)
        }
        
        # Compare columns
        columns1 = list(df1.columns)
        columns2 = list(df2.columns)
        
        missing_columns = [str(c) for c in columns1 if c not in columns2]
        added_columns = [str(c) for c in columns2 if c not in columns1]
        common_columns = [c for c in columns1 if c in columns2]
        
        # Add column differences
        for col in missing_columns:
            result['differences']['removed'].append(f"Column '{col}' removed")
        
        for col in added_columns:
            result['differences']['added'].append(f"Column '{col}' added")
        
        # Compare data in common columns (row by row)
        # For large datasets, this is a simplified approach
        for col in common_columns:
            # Check if columns have the same data type
            if df1[col].dtype != df2[col].dtype:
                result['differences']['changed'].append(
                    f"Column '{col}' has different data types: {df1[col].dtype} vs {df2[col].dtype}"
                )
            
            # Find common row identifiers
            # If we have 'id' or similar column, use that for comparison
            id_col = None
            for potential_id in ['id', 'ID', 'Id', 'index', 'key', 'name']:
                if potential_id in common_columns:
                    id_col = potential_id
                    break
            
            if id_col:
                # Compare by ID
                ids1 = set(df1[id_col].dropna().astype(str))
                ids2 = set(df2[id_col].dropna().astype(str))
                
                # Find rows in file1 but not in file2
                for id_val in ids1 - ids2:
                    result['differences']['removed'].append(
                        f"Row with {id_col}='{id_val}' removed"
                    )
                
                # Find rows in file2 but not in file1
                for id_val in ids2 - ids1:
                    result['differences']['added'].append(
                        f"Row with {id_col}='{id_val}' added"
                    )
                
                # Compare common rows
                common_ids = ids1.intersection(ids2)
                for id_val in common_ids:
                    row1 = df1[df1[id_col].astype(str) == id_val]
                    row2 = df2[df2[id_col].astype(str) == id_val]
                    
                    if len(row1) > 1 or len(row2) > 1:
                        # Duplicate IDs, just note this as a change
                        result['differences']['changed'].append(
                            f"Multiple rows with {id_col}='{id_val}'"
                        )
                        continue
                    
                    # Compare values
                    for col in common_columns:
                        val1 = row1[col].iloc[0]
                        val2 = row2[col].iloc[0]
                        
                        # Handle NaN values
                        if pd.isna(val1) and pd.isna(val2):
                            continue
                        elif pd.isna(val1) or pd.isna(val2):
                            result['differences']['changed'].append(
                                f"Row {id_col}='{id_val}', column '{col}': {val1} -> {val2}"
                            )
                        elif val1 != val2:
                            result['differences']['changed'].append(
                                f"Row {id_col}='{id_val}', column '{col}': {val1} -> {val2}"
                            )
            else:
                # No ID column, compare rows directly
                # This is less accurate for rows that have been reordered
                min_rows = min(len(df1), len(df2))
                
                # Compare row by row
                for i in range(min_rows):
                    for col in common_columns:
                        val1 = df1.iloc[i][col]
                        val2 = df2.iloc[i][col]
                        
                        # Handle NaN values
                        if pd.isna(val1) and pd.isna(val2):
                            continue
                        elif pd.isna(val1) or pd.isna(val2):
                            result['differences']['changed'].append(
                                f"Row {i+1}, column '{col}': {val1} -> {val2}"
                            )
                        elif val1 != val2:
                            result['differences']['changed'].append(
                                f"Row {i+1}, column '{col}': {val1} -> {val2}"
                            )
                
                # Handle different number of rows
                if len(df1) > len(df2):
                    result['differences']['removed'].append(
                        f"{len(df1) - len(df2)} rows at the end of the file were removed"
                    )
                elif len(df2) > len(df1):
                    result['differences']['added'].append(
                        f"{len(df2) - len(df1)} rows at the end of the file were added"
                    )
        
        return result
    
    except Exception as e:
        logger.exception(f"Error comparing Excel sheets: {e}")
        result['message'] = f"Error comparing sheet '{sheet_name}': {str(e)}"
        return result

def compare_csv_files(file1_path: str, file2_path: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two CSV files
    
    Args:
        file1_path (str): Path to the first file
        file2_path (str): Path to the second file
        result (Dict[str, Any]): Result dictionary to update
        
    Returns:
        Dict[str, Any]: Updated result dictionary
    """
    try:
        # Try to read CSVs
        df1 = pd.read_csv(file1_path)
        df2 = pd.read_csv(file2_path)
        
        # Treat as a single Excel sheet
        temp_result = {'differences': {'added': [], 'removed': [], 'changed': []}}
        excel1 = pd.ExcelFile(file1_path)
        excel2 = pd.ExcelFile(file2_path)
        
        temp_result = compare_excel_sheets(excel1, excel2, 0, temp_result)
        
        # Merge differences
        result['differences']['added'].extend(temp_result['differences']['added'])
        result['differences']['removed'].extend(temp_result['differences']['removed'])
        result['differences']['changed'].extend(temp_result['differences']['changed'])
        
        return result
    
    except Exception as e:
        logger.exception(f"Error comparing CSV files: {e}")
        
        # Fall back to text comparison
        return compare_text_files(file1_path, file2_path, result)

def compare_json_files(file1_path: str, file2_path: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two JSON files
    
    Args:
        file1_path (str): Path to the first file
        file2_path (str): Path to the second file
        result (Dict[str, Any]): Result dictionary to update
        
    Returns:
        Dict[str, Any]: Updated result dictionary
    """
    try:
        # Read the files
        df1 = pd.read_json(file1_path)
        df2 = pd.read_json(file2_path)
        
        # If they're tabular, use dataframe comparison
        if isinstance(df1, pd.DataFrame) and isinstance(df2, pd.DataFrame):
            # Treat as a single Excel sheet
            temp_result = {'differences': {'added': [], 'removed': [], 'changed': []}}
            excel1 = pd.ExcelFile(file1_path)
            excel2 = pd.ExcelFile(file2_path)
            
            temp_result = compare_excel_sheets(excel1, excel2, 0, temp_result)
            
            # Merge differences
            result['differences']['added'].extend(temp_result['differences']['added'])
            result['differences']['removed'].extend(temp_result['differences']['removed'])
            result['differences']['changed'].extend(temp_result['differences']['changed'])
        else:
            # Fall back to text comparison
            return compare_text_files(file1_path, file2_path, result)
        
        return result
    
    except Exception as e:
        logger.exception(f"Error comparing JSON files: {e}")
        
        # Fall back to text comparison
        return compare_text_files(file1_path, file2_path, result)

def compare_text_files(file1_path: str, file2_path: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two text files line by line
    
    Args:
        file1_path (str): Path to the first file
        file2_path (str): Path to the second file
        result (Dict[str, Any]): Result dictionary to update
        
    Returns:
        Dict[str, Any]: Updated result dictionary
    """
    try:
        # Read files
        with open(file1_path, 'r', encoding='utf-8', errors='ignore') as f:
            file1_lines = f.readlines()
        
        with open(file2_path, 'r', encoding='utf-8', errors='ignore') as f:
            file2_lines = f.readlines()
        
        # Use difflib to compare
        diff = list(difflib.unified_diff(
            file1_lines, 
            file2_lines,
            fromfile=os.path.basename(file1_path),
            tofile=os.path.basename(file2_path),
            n=0  # Context lines
        ))
        
        # Parse the diff output
        for line in diff[2:]:  # Skip the first two lines (file names)
            if line.startswith('+'):
                result['differences']['added'].append(line[1:].strip())
            elif line.startswith('-'):
                result['differences']['removed'].append(line[1:].strip())
            elif line.startswith('@@'):
                # This is a chunk header, format: @@ -N,M +P,Q @@
                result['differences']['changed'].append(line.strip())
        
        # Add diff for display purposes
        result['text_diff'] = diff
        
        return result
    
    except Exception as e:
        logger.exception(f"Error comparing text files: {e}")
        result['message'] = f"Error comparing text files: {str(e)}"
        return result