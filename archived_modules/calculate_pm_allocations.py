"""
Calculate PM Allocations

This module provides functions for processing PM allocation files,
comparing changes between the base file and PM allocation files,
and generating reconciliation reports.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

def process_pm_allocation_files(base_file_path, pm_file_paths):
    """
    Process PM allocation files and generate reconciliation report.
    
    Args:
        base_file_path (str): Path to the base RAGLE file
        pm_file_paths (list): List of paths to PM allocation files
        
    Returns:
        dict: Results of PM allocation processing
    """
    logger.info(f"Processing PM allocation files")
    logger.info(f"Base file: {base_file_path}")
    logger.info(f"PM files: {pm_file_paths}")
    
    try:
        # Load base file
        base_df = load_excel_file(base_file_path)
        if base_df is None:
            return {"error": "Failed to load base file"}
        
        # Track all changes
        all_changes = []
        changed_jobs = set()
        
        # Process each PM file
        pm_files_info = []
        for file_path in pm_file_paths:
            pm_df = load_excel_file(file_path)
            if pm_df is None:
                logger.warning(f"Failed to load PM file: {file_path}")
                continue
                
            # Compare with base file and track changes
            file_changes = compare_allocation_files(base_df, pm_df)
            if file_changes and len(file_changes) > 0:
                all_changes.extend(file_changes)
                
                # Track changed job numbers
                for change in file_changes:
                    if 'job_number' in change:
                        changed_jobs.add(change['job_number'])
            
            # Add file info
            pm_files_info.append({
                "filename": os.path.basename(file_path),
                "changes_count": len(file_changes) if file_changes else 0
            })
        
        # Generate results
        results = {
            "base_file": os.path.basename(base_file_path),
            "pm_files": pm_files_info,
            "total_changes": len(all_changes),
            "changes": all_changes,
            "changed_jobs": list(changed_jobs),
            "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Export detailed report
        export_detailed_report(results)
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing PM allocation files: {str(e)}")
        return {"error": str(e)}

def load_excel_file(file_path):
    """
    Load an Excel file into a pandas DataFrame.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        DataFrame: Loaded DataFrame or None if failed
    """
    try:
        # Skip empty sheets and text parsing errors
        xls = pd.ExcelFile(file_path)
        
        # Try to find the main sheet with allocation data
        for sheet_name in xls.sheet_names:
            # Look for sheets with job data
            if 'JOB' in sheet_name.upper() or 'ALLOCATION' in sheet_name.upper():
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                return df
        
        # Fall back to first sheet if no job sheet found
        df = pd.read_excel(file_path, sheet_name=0)
        return df
        
    except Exception as e:
        logger.error(f"Error loading Excel file {file_path}: {str(e)}")
        return None

def compare_allocation_files(base_df, pm_df):
    """
    Compare base and PM allocation DataFrames to identify changes.
    
    Args:
        base_df (DataFrame): Base DataFrame
        pm_df (DataFrame): PM DataFrame
        
    Returns:
        list: List of change records
    """
    changes = []
    
    try:
        # Identify common columns that might contain job numbers or amount data
        numeric_columns = base_df.select_dtypes(include=['number']).columns.tolist()
        
        # Find job number column
        job_number_col = None
        for col in base_df.columns:
            if 'JOB' in str(col).upper() or 'NUMBER' in str(col).upper():
                job_number_col = col
                break
        
        if job_number_col is None:
            logger.warning("No job number column identified")
            return changes
        
        # Iterate through rows in PM file to find changes
        for _, row in pm_df.iterrows():
            job_number = row.get(job_number_col)
            if job_number is None or pd.isna(job_number):
                continue
                
            # Find corresponding row in base file
            base_row = base_df[base_df[job_number_col] == job_number]
            if base_row.empty:
                continue
                
            # Compare numeric columns for changes
            for col in numeric_columns:
                if col not in pm_df.columns:
                    continue
                    
                pm_value = row.get(col)
                base_value = base_row.iloc[0].get(col)
                
                # Check for significant changes (avoid floating point precision issues)
                if pd.notna(pm_value) and pd.notna(base_value):
                    if abs(pm_value - base_value) > 0.01:  # Threshold for considering a change
                        changes.append({
                            "job_number": str(job_number),
                            "column": col,
                            "base_value": float(base_value),
                            "pm_value": float(pm_value),
                            "difference": float(pm_value - base_value)
                        })
    
    except Exception as e:
        logger.error(f"Error comparing allocation files: {str(e)}")
    
    return changes

def export_detailed_report(results):
    """
    Export detailed reconciliation report.
    
    Args:
        results (dict): Processing results
        
    Returns:
        str: Path to exported report file
    """
    try:
        # Create exports directory if it doesn't exist
        export_dir = os.path.join('exports', 'pm_allocation')
        os.makedirs(export_dir, exist_ok=True)
        
        # Export as JSON
        json_path = os.path.join(export_dir, 'detailed_reconciliation.json')
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Export as Excel if there are changes
        if results.get('total_changes', 0) > 0:
            excel_path = os.path.join(export_dir, 'pm_reconciliation.xlsx')
            
            # Create DataFrame from changes
            changes_df = pd.DataFrame(results.get('changes', []))
            
            # Group by job number
            if 'job_number' in changes_df.columns:
                job_summary = changes_df.groupby('job_number').agg({
                    'difference': 'sum',
                    'column': 'count'
                }).reset_index()
                job_summary.rename(columns={'column': 'change_count'}, inplace=True)
                
                # Export to Excel with multiple sheets
                with pd.ExcelWriter(excel_path) as writer:
                    changes_df.to_excel(writer, sheet_name='All Changes', index=False)
                    job_summary.to_excel(writer, sheet_name='Job Summary', index=False)
        
        return json_path
        
    except Exception as e:
        logger.error(f"Error exporting detailed report: {str(e)}")
        return None

def find_pm_allocation_files():
    """
    Find all PM allocation files in the designated directory.
    
    Returns:
        tuple: (base_file_path, list of PM file paths)
    """
    try:
        # Look in standard locations
        attached_assets_dir = 'attached_assets'
        uploads_dir = os.path.join('uploads', 'pm_allocation')
        
        base_file = None
        pm_files = []
        
        # Check attached_assets directory
        if os.path.exists(attached_assets_dir):
            for filename in os.listdir(attached_assets_dir):
                if filename.endswith('.xlsx') or filename.endswith('.xls'):
                    file_path = os.path.join(attached_assets_dir, filename)
                    
                    # Identify base RAGLE file
                    if 'RAGLE' in filename.upper() or 'BASE' in filename.upper() or 'MASTER' in filename.upper():
                        base_file = file_path
                    
                    # Identify PM allocation files
                    elif 'PM' in filename.upper() or 'ALLOCATION' in filename.upper():
                        pm_files.append(file_path)
        
        # Check uploads directory
        if os.path.exists(uploads_dir):
            for filename in os.listdir(uploads_dir):
                if filename.endswith('.xlsx') or filename.endswith('.xls'):
                    file_path = os.path.join(uploads_dir, filename)
                    
                    # Check for explicitly marked base file
                    if filename.startswith('base_'):
                        base_file = file_path
                    else:
                        # Add to PM files if not already included
                        if file_path not in pm_files:
                            pm_files.append(file_path)
        
        return base_file, pm_files
        
    except Exception as e:
        logger.error(f"Error finding PM allocation files: {str(e)}")
        return None, []

if __name__ == '__main__':
    # For testing/standalone execution
    base_file, pm_files = find_pm_allocation_files()
    
    if base_file and pm_files:
        logger.info(f"Found base file: {base_file}")
        logger.info(f"Found {len(pm_files)} PM allocation files")
        
        results = process_pm_allocation_files(base_file, pm_files)
        print(json.dumps(results, indent=2))
    else:
        logger.warning("Missing base file or PM allocation files")