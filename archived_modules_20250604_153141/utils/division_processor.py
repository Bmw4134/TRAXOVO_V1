"""
Division Data Processor

This module provides functions for processing and analyzing divisional data
for DFW, HOU, and WTX regions. It extracts metrics and generates reports
for regional performance analysis.
"""

import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
from utils.export_utils import ensure_export_dir

# Configure logging
logger = logging.getLogger(__name__)

def load_divisional_csv(file_path):
    """
    Load a divisional CSV file and return a pandas DataFrame
    
    Args:
        file_path (str): Path to the divisional CSV file
        
    Returns:
        pd.DataFrame: DataFrame containing the divisional data
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded divisional data from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading divisional data from {file_path}: {e}")
        return None

def process_divisional_data(division_files, output_format='excel'):
    """
    Process divisional data from multiple files and generate a consolidated report
    
    Args:
        division_files (dict): Dictionary with region keys and file paths as values
            Example: {'DFW': 'path/to/dfw.csv', 'HOU': 'path/to/hou.csv', 'WTX': 'path/to/wtx.csv'}
        output_format (str): Output format, either 'excel' or 'csv'
        
    Returns:
        tuple: (success bool, path to output file or error message)
    """
    try:
        # Initialize dictionaries to store division data and metrics
        division_data = {}
        division_metrics = {}
        
        # Load data from each division
        for division, file_path in division_files.items():
            df = load_divisional_csv(file_path)
            if df is None:
                continue
                
            division_data[division] = df
            
            # Calculate division metrics
            metrics = calculate_division_metrics(df, division)
            division_metrics[division] = metrics
        
        # If no data was loaded successfully, return error
        if not division_data:
            return False, "No divisional data could be loaded. Check file paths and formats."
        
        # Generate consolidated report
        report_path = generate_division_report(division_data, division_metrics, output_format)
        
        if not report_path:
            return False, "Failed to generate division report."
            
        return True, report_path
    except Exception as e:
        logger.error(f"Error processing divisional data: {e}")
        return False, f"Error processing divisional data: {str(e)}"

def calculate_division_metrics(df, division_name):
    """
    Calculate key metrics for a division from its data
    
    Args:
        df (pd.DataFrame): DataFrame containing division data
        division_name (str): Name of the division (DFW, HOU, WTX, etc.)
        
    Returns:
        dict: Dictionary containing division metrics
    """
    metrics = {
        'division': division_name,
        'total_assets': 0,
        'total_hours': 0,
        'total_cost': 0,
        'average_utilization': 0,
        'assets_by_category': {},
        'top_projects': [],
        'cost_by_category': {}
    }
    
    try:
        # These column names will need to be adjusted based on actual CSV structure
        if 'Asset' in df.columns:
            metrics['total_assets'] = df['Asset'].nunique()
            
        if 'Hours' in df.columns:
            metrics['total_hours'] = df['Hours'].sum()
            
        if 'Cost' in df.columns:
            metrics['total_cost'] = df['Cost'].sum()
            
        if 'Utilization' in df.columns:
            metrics['average_utilization'] = df['Utilization'].mean()
            
        if 'Category' in df.columns and 'Asset' in df.columns:
            # Count assets by category
            assets_by_category = df.groupby('Category')['Asset'].nunique()
            metrics['assets_by_category'] = assets_by_category.to_dict()
            
        if 'Project' in df.columns and 'Cost' in df.columns:
            # Get top projects by cost
            top_projects = df.groupby('Project')['Cost'].sum().sort_values(ascending=False).head(5)
            metrics['top_projects'] = [{'project': idx, 'cost': val} for idx, val in top_projects.items()]
            
        if 'Category' in df.columns and 'Cost' in df.columns:
            # Sum costs by category
            cost_by_category = df.groupby('Category')['Cost'].sum()
            metrics['cost_by_category'] = cost_by_category.to_dict()
    except Exception as e:
        logger.error(f"Error calculating metrics for {division_name}: {e}")
    
    return metrics

def generate_division_report(division_data, division_metrics, output_format='excel'):
    """
    Generate a consolidated report for all divisions
    
    Args:
        division_data (dict): Dictionary with division names as keys and DataFrames as values
        division_metrics (dict): Dictionary with division names as keys and metric dictionaries as values
        output_format (str): Output format, either 'excel' or 'csv'
        
    Returns:
        str: Path to the generated report file
    """
    try:
        ensure_export_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format == 'excel':
            return generate_excel_division_report(division_data, division_metrics, timestamp)
        elif output_format == 'csv':
            return generate_csv_division_report(division_data, division_metrics, timestamp)
        else:
            logger.error(f"Unsupported output format: {output_format}")
            return None
    except Exception as e:
        logger.error(f"Error generating division report: {e}")
        return None

def generate_excel_division_report(division_data, division_metrics, timestamp):
    """
    Generate an Excel report for division data
    
    Args:
        division_data (dict): Dictionary with division names as keys and DataFrames as values
        division_metrics (dict): Dictionary with division names as keys and metric dictionaries as values
        timestamp (str): Timestamp for the file name
        
    Returns:
        str: Path to the generated Excel file
    """
    filepath = Path('exports') / 'billing' / f"division_report_{timestamp}.xlsx"
    
    try:
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Create summary sheet
            summary_data = []
            for division, metrics in division_metrics.items():
                summary_data.append({
                    'Division': division,
                    'Total Assets': metrics['total_assets'],
                    'Total Hours': metrics['total_hours'],
                    'Total Cost': metrics['total_cost'],
                    'Average Utilization': metrics['average_utilization']
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Create a sheet for each division with its raw data
            for division, df in division_data.items():
                df.to_excel(writer, sheet_name=f"{division}_Data", index=False)
                
            # Create a metrics sheet for each division
            for division, metrics in division_metrics.items():
                # Convert the metrics to a format that can be saved to Excel
                metrics_list = []
                for key, value in metrics.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            metrics_list.append({
                                'Metric': f"{key.replace('_', ' ').title()} - {sub_key}",
                                'Value': sub_value
                            })
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                for sub_key, sub_value in item.items():
                                    metrics_list.append({
                                        'Metric': f"{key.replace('_', ' ').title()} {i+1} - {sub_key}",
                                        'Value': sub_value
                                    })
                            else:
                                metrics_list.append({
                                    'Metric': f"{key.replace('_', ' ').title()} {i+1}",
                                    'Value': item
                                })
                    else:
                        metrics_list.append({
                            'Metric': key.replace('_', ' ').title(),
                            'Value': value
                        })
                
                metrics_df = pd.DataFrame(metrics_list)
                metrics_df.to_excel(writer, sheet_name=f"{division}_Metrics", index=False)
            
            # Create a comparison sheet
            comparison_data = []
            for division, metrics in division_metrics.items():
                row_data = {'Division': division}
                
                for key, value in metrics.items():
                    if not isinstance(value, (dict, list)) and key != 'division':
                        row_data[key.replace('_', ' ').title()] = value
                
                comparison_data.append(row_data)
            
            comparison_df = pd.DataFrame(comparison_data)
            comparison_df.to_excel(writer, sheet_name='Division_Comparison', index=False)
        
        logger.info(f"Successfully generated division report at {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Error generating Excel division report: {e}")
        return None

def generate_csv_division_report(division_data, division_metrics, timestamp):
    """
    Generate CSV reports for division data
    
    Args:
        division_data (dict): Dictionary with division names as keys and DataFrames as values
        division_metrics (dict): Dictionary with division names as keys and metric dictionaries as values
        timestamp (str): Timestamp for the file name
        
    Returns:
        str: Path to the directory containing the generated CSV files
    """
    report_dir = Path('exports') / 'billing' / f"division_report_{timestamp}"
    
    try:
        # Create report directory if it doesn't exist
        if not report_dir.exists():
            report_dir.mkdir(parents=True)
        
        # Create summary CSV
        summary_data = []
        for division, metrics in division_metrics.items():
            summary_data.append({
                'Division': division,
                'Total Assets': metrics['total_assets'],
                'Total Hours': metrics['total_hours'],
                'Total Cost': metrics['total_cost'],
                'Average Utilization': metrics['average_utilization']
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(report_dir / "summary.csv", index=False)
        
        # Create a CSV for each division with its raw data
        for division, df in division_data.items():
            df.to_csv(report_dir / f"{division}_data.csv", index=False)
            
        # Create a metrics CSV for each division
        for division, metrics in division_metrics.items():
            # Convert the metrics to a format that can be saved to CSV
            metrics_list = []
            for key, value in metrics.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        metrics_list.append({
                            'Metric': f"{key.replace('_', ' ').title()} - {sub_key}",
                            'Value': sub_value
                        })
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            for sub_key, sub_value in item.items():
                                metrics_list.append({
                                    'Metric': f"{key.replace('_', ' ').title()} {i+1} - {sub_key}",
                                    'Value': sub_value
                                })
                        else:
                            metrics_list.append({
                                'Metric': f"{key.replace('_', ' ').title()} {i+1}",
                                'Value': item
                            })
                else:
                    metrics_list.append({
                        'Metric': key.replace('_', ' ').title(),
                        'Value': value
                    })
            
            metrics_df = pd.DataFrame(metrics_list)
            metrics_df.to_csv(report_dir / f"{division}_metrics.csv", index=False)
        
        # Create a comparison CSV
        comparison_data = []
        for division, metrics in division_metrics.items():
            row_data = {'Division': division}
            
            for key, value in metrics.items():
                if not isinstance(value, (dict, list)) and key != 'division':
                    row_data[key.replace('_', ' ').title()] = value
            
            comparison_data.append(row_data)
        
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df.to_csv(report_dir / "division_comparison.csv", index=False)
        
        logger.info(f"Successfully generated division report at {report_dir}")
        return str(report_dir)
    except Exception as e:
        logger.error(f"Error generating CSV division report: {e}")
        return None

def find_division_files(base_dir='attached_assets', month=None, year=None):
    """
    Find CSV files for divisions based on naming patterns
    
    Args:
        base_dir (str): Base directory to search in
        month (str): Month to filter by (e.g., 'JAN', 'FEB', etc.)
        year (str): Year to filter by (e.g., '2025')
        
    Returns:
        dict: Dictionary with division keys and file paths as values
    """
    if month is None:
        month = datetime.now().strftime('%b').upper()
    
    if year is None:
        year = datetime.now().year
    
    base_path = Path(base_dir)
    division_files = {
        'DFW': None,
        'HOU': None,
        'WT': None  # Using WT instead of WTX to match the filename patterns
    }
    
    try:
        for csv_file in base_path.glob('*.csv'):
            filename = csv_file.name.upper()
            
            # Check for division patterns - adjust these patterns based on actual naming conventions
            if month in filename and str(year) in filename:
                if '01 - DFW' in filename or 'DFW' in filename:
                    division_files['DFW'] = str(csv_file)
                elif '02 - HOU' in filename or 'HOU' in filename:
                    division_files['HOU'] = str(csv_file)
                elif '03 - WT' in filename or 'WT' in filename:
                    division_files['WT'] = str(csv_file)
        
        found_divisions = [d for d, f in division_files.items() if f is not None]
        logger.info(f"Found division files for: {', '.join(found_divisions)}")
        return division_files
    except Exception as e:
        logger.error(f"Error finding division files: {e}")
        return division_files