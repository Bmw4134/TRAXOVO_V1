"""
Timecard Integration Module

This module provides functionality for parsing and analyzing timecard data
from the Ground Works Timecard system to identify employees with less than
40 hours per week and zero-hour records.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Directory setup
TIMECARD_DIR = Path('./uploads/timecards')
REPORTS_DIR = Path('./reports/timecards')

# Ensure directories exist
TIMECARD_DIR.mkdir(exist_ok=True, parents=True)
REPORTS_DIR.mkdir(exist_ok=True, parents=True)

def find_timecard_files():
    """Find timecard Excel files in the uploads directory"""
    excel_files = []
    
    # Look for Excel files with timecard naming patterns
    patterns = ['Timecard', 'Time card', 'Weekly Hours', 'Employee Hours']
    
    # Check for files in the specified directory
    for file in TIMECARD_DIR.glob('*.xlsx'):
        for pattern in patterns:
            if pattern.lower() in file.name.lower():
                excel_files.append(file)
                break
    
    # Sort by modification time (newest first)
    excel_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    return excel_files

def analyze_timecard(file_path):
    """
    Analyze a timecard Excel file to identify employees with less than 40 hours
    and zero-hour records
    
    Args:
        file_path (Path): Path to the timecard Excel file
        
    Returns:
        dict: Analysis results
    """
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Try to identify key columns
        employee_col = None
        hours_col = None
        date_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Find employee name/ID column
            if any(term in col_lower for term in ['employee', 'name', 'worker', 'person']):
                employee_col = col
            
            # Find hours column
            elif any(term in col_lower for term in ['hours', 'time', 'duration']):
                hours_col = col
            
            # Find date column
            elif any(term in col_lower for term in ['date', 'week', 'day']):
                date_col = col
        
        # Fall back to positional guessing if columns not found
        if not employee_col and len(df.columns) > 0:
            employee_col = df.columns[0]
        
        if not hours_col and len(df.columns) > 1:
            for col in df.columns:
                # Try to find a numeric column for hours
                if pd.api.types.is_numeric_dtype(df[col]):
                    hours_col = col
                    break
        
        # If still not found, use the second column as a guess
        if not hours_col and len(df.columns) > 1:
            hours_col = df.columns[1]
        
        # Make sure we have at least employee and hours columns
        if not employee_col or not hours_col:
            return {
                'error': 'Could not identify employee and hours columns',
                'file': str(file_path)
            }
        
        # Convert hours to numeric, handling any conversion errors
        if hours_col:
            df[hours_col] = pd.to_numeric(df[hours_col], errors='coerce')
        
        # Group by employee and sum hours if needed
        if employee_col:
            # Check if we need to group (multiple rows per employee)
            if df[employee_col].duplicated().any():
                employee_hours = df.groupby(employee_col)[hours_col].sum().reset_index()
            else:
                employee_hours = df[[employee_col, hours_col]].copy()
            
            # Find employees with less than 40 hours
            under_40 = employee_hours[employee_hours[hours_col] < 40]
            
            # Find employees with zero hours
            zero_hours = employee_hours[employee_hours[hours_col] == 0]
            
            # Extract week ending date from filename if possible
            week_ending = None
            filename = file_path.name
            
            # Try to parse date from filename
            for fmt in ['%Y-%m-%d', '%Y%m%d', '%m-%d-%Y', '%m%d%Y']:
                try:
                    # Find a date-like pattern in filename
                    for part in filename.replace('.xlsx', '').replace('.xls', '').split(' '):
                        try:
                            date_obj = datetime.strptime(part, fmt)
                            week_ending = date_obj.strftime('%Y-%m-%d')
                            break
                        except ValueError:
                            continue
                    if week_ending:
                        break
                except ValueError:
                    continue
            
            # If date not found in filename, try to extract from the dataframe
            if not week_ending and date_col:
                try:
                    latest_date = pd.to_datetime(df[date_col]).max()
                    week_ending = latest_date.strftime('%Y-%m-%d')
                except:
                    # Use current date as fallback
                    week_ending = datetime.now().strftime('%Y-%m-%d')
            
            # Prepare results
            return {
                'file': str(file_path),
                'week_ending': week_ending,
                'employee_count': len(employee_hours),
                'under_40_count': len(under_40),
                'zero_hours_count': len(zero_hours),
                'under_40': under_40.to_dict('records'),
                'zero_hours': zero_hours.to_dict('records'),
                'employee_col': employee_col,
                'hours_col': hours_col
            }
            
    except Exception as e:
        return {
            'error': str(e),
            'file': str(file_path)
        }

def generate_timecard_report(timecard_data):
    """
    Generate a report of employees with attendance issues
    
    Args:
        timecard_data (dict): Timecard analysis results
        
    Returns:
        str: Path to the generated report
    """
    try:
        # Create output directory if it doesn't exist
        REPORTS_DIR.mkdir(exist_ok=True, parents=True)
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        week_ending = timecard_data.get('week_ending', timestamp)
        output_file = REPORTS_DIR / f"Attendance_Issues_{week_ending}_{timestamp}.csv"
        
        # Extract column names
        employee_col = timecard_data.get('employee_col', 'Employee')
        hours_col = timecard_data.get('hours_col', 'Hours')
        
        # Combine under 40 and zero hour employees
        under_40 = timecard_data.get('under_40', [])
        zero_hours = timecard_data.get('zero_hours', [])
        
        # Create a combined dataframe
        all_issues = []
        
        for record in under_40:
            issue = {
                employee_col: record.get(employee_col, 'Unknown'),
                hours_col: record.get(hours_col, 0),
                'Issue': 'Under 40 Hours'
            }
            all_issues.append(issue)
        
        for record in zero_hours:
            issue = {
                employee_col: record.get(employee_col, 'Unknown'),
                hours_col: 0,
                'Issue': 'Zero Hours'
            }
            all_issues.append(issue)
        
        # Create and save DataFrame
        if all_issues:
            df = pd.DataFrame(all_issues)
            df.to_csv(output_file, index=False)
            
            return str(output_file)
        else:
            return None
            
    except Exception as e:
        return str(e)

def process_timecard_files():
    """
    Process all available timecard files and generate reports
    
    Returns:
        list: Paths to generated reports
    """
    # Find timecard files
    timecard_files = find_timecard_files()
    
    if not timecard_files:
        return {
            'error': 'No timecard files found',
            'reports': []
        }
    
    # Process each file
    results = []
    reports = []
    
    for file_path in timecard_files:
        # Analyze the timecard
        analysis = analyze_timecard(file_path)
        results.append(analysis)
        
        # Generate report if there are issues
        if 'error' not in analysis and (analysis.get('under_40_count', 0) > 0 or analysis.get('zero_hours_count', 0) > 0):
            report_path = generate_timecard_report(analysis)
            if report_path:
                reports.append(report_path)
    
    return {
        'processed_files': len(timecard_files),
        'reports': reports,
        'results': results
    }