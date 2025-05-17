"""
Export Utilities

This module provides functions for exporting various system reports
in multiple formats (Excel, CSV, PDF).
"""

import os
import csv
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Define export directory
EXPORTS_DIR = Path('exports')

def ensure_export_dir():
    """Ensure the exports directory exists"""
    if not EXPORTS_DIR.exists():
        EXPORTS_DIR.mkdir(parents=True)
    
    # Create subdirectories for different report types
    for subdir in ['assets', 'alerts', 'maintenance', 'driver_reports', 'billing']:
        subdir_path = EXPORTS_DIR / subdir
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True)

def export_assets_to_excel(assets, filename=None):
    """
    Export assets list to Excel format
    
    Args:
        assets (list): List of asset objects or dictionaries
        filename (str, optional): Output filename. If None, will generate a default name.
        
    Returns:
        str: Path to the exported file
    """
    ensure_export_dir()
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"assets_export_{timestamp}.xlsx"
    
    # Ensure .xlsx extension
    if not filename.endswith('.xlsx'):
        filename += '.xlsx'
        
    # Full path to output file
    filepath = EXPORTS_DIR / 'assets' / filename
    
    try:
        # Convert assets to a format pandas can handle
        assets_data = []
        for asset in assets:
            # Handle both ORM objects and dictionaries
            if hasattr(asset, '__dict__'):
                # Convert ORM object to dict, excluding SQLAlchemy special attributes
                asset_dict = {k: v for k, v in asset.__dict__.items() 
                             if not k.startswith('_')}
                assets_data.append(asset_dict)
            else:
                # Already a dict
                assets_data.append(asset)
        
        # Create DataFrame
        df = pd.DataFrame(assets_data)
        
        # Write to Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Assets', index=False)
            
            # Auto-adjust column widths for better readability
            worksheet = writer.sheets['Assets']
            for idx, col in enumerate(df.columns):
                max_len = df[col].astype(str).map(len).max()
                max_len = max(max_len, len(col)) + 2  # Add a little extra space
                worksheet.column_dimensions[worksheet.cell(1, idx+1).column_letter].width = max_len
        
        logger.info(f"Exported {len(assets)} assets to Excel: {filepath}")
        return str(filepath)
    
    except Exception as e:
        logger.error(f"Error exporting assets to Excel: {e}")
        raise

def export_assets_to_csv(assets, filename=None):
    """
    Export assets list to CSV format
    
    Args:
        assets (list): List of asset objects or dictionaries
        filename (str, optional): Output filename. If None, will generate a default name.
        
    Returns:
        str: Path to the exported file
    """
    ensure_export_dir()
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"assets_export_{timestamp}.csv"
    
    # Ensure .csv extension
    if not filename.endswith('.csv'):
        filename += '.csv'
        
    # Full path to output file
    filepath = EXPORTS_DIR / 'assets' / filename
    
    try:
        # Convert assets to a list of dictionaries
        assets_data = []
        for asset in assets:
            # Handle both ORM objects and dictionaries
            if hasattr(asset, '__dict__'):
                # Convert ORM object to dict, excluding SQLAlchemy special attributes
                asset_dict = {k: v for k, v in asset.__dict__.items() 
                             if not k.startswith('_')}
                assets_data.append(asset_dict)
            else:
                # Already a dict
                assets_data.append(asset)
        
        # If no assets, create empty file with headers
        if not assets_data:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['No assets found'])
            return str(filepath)
            
        # Get field names from first asset
        fieldnames = list(assets_data[0].keys())
        
        # Write to CSV
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for asset in assets_data:
                writer.writerow(asset)
        
        logger.info(f"Exported {len(assets)} assets to CSV: {filepath}")
        return str(filepath)
    
    except Exception as e:
        logger.error(f"Error exporting assets to CSV: {e}")
        raise

def export_assets_to_json(assets, filename=None):
    """
    Export assets list to JSON format
    
    Args:
        assets (list): List of asset objects or dictionaries
        filename (str, optional): Output filename. If None, will generate a default name.
        
    Returns:
        str: Path to the exported file
    """
    ensure_export_dir()
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"assets_export_{timestamp}.json"
    
    # Ensure .json extension
    if not filename.endswith('.json'):
        filename += '.json'
        
    # Full path to output file
    filepath = EXPORTS_DIR / 'assets' / filename
    
    try:
        # Convert assets to a list of dictionaries
        assets_data = []
        for asset in assets:
            # Handle both ORM objects and dictionaries
            if hasattr(asset, '__dict__'):
                # Convert ORM object to dict, excluding SQLAlchemy special attributes
                asset_dict = {k: v for k, v in asset.__dict__.items() 
                             if not k.startswith('_')}
                
                # Convert datetime objects to strings for JSON serialization
                for key, value in asset_dict.items():
                    if isinstance(value, datetime):
                        asset_dict[key] = value.isoformat()
                
                assets_data.append(asset_dict)
            else:
                # Already a dict, but need to handle datetime objects
                asset_dict = asset.copy()
                for key, value in asset_dict.items():
                    if isinstance(value, datetime):
                        asset_dict[key] = value.isoformat()
                
                assets_data.append(asset_dict)
        
        # Write to JSON
        with open(filepath, 'w') as jsonfile:
            json.dump(assets_data, jsonfile, indent=2)
        
        logger.info(f"Exported {len(assets)} assets to JSON: {filepath}")
        return str(filepath)
    
    except Exception as e:
        logger.error(f"Error exporting assets to JSON: {e}")
        raise

def export_alerts_to_excel(alerts, filename=None):
    """
    Export equipment alerts to Excel format
    
    Args:
        alerts (list): List of alert objects or dictionaries
        filename (str, optional): Output filename. If None, will generate a default name.
        
    Returns:
        str: Path to the exported file
    """
    ensure_export_dir()
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"equipment_alerts_{timestamp}.xlsx"
    
    # Ensure .xlsx extension
    if not filename.endswith('.xlsx'):
        filename += '.xlsx'
        
    # Full path to output file
    filepath = EXPORTS_DIR / 'alerts' / filename
    
    try:
        # Convert alerts to a format pandas can handle
        alerts_data = []
        for alert in alerts:
            # Handle both ORM objects and dictionaries
            if hasattr(alert, '__dict__'):
                # Convert ORM object to dict, excluding SQLAlchemy special attributes
                alert_dict = {k: v for k, v in alert.__dict__.items() 
                             if not k.startswith('_')}
                
                # Handle nested details field
                if 'details' in alert_dict and isinstance(alert_dict['details'], dict):
                    for key, value in alert_dict['details'].items():
                        alert_dict[f"detail_{key}"] = value
                    
                alerts_data.append(alert_dict)
            else:
                # Already a dict
                alert_dict = alert.copy()
                
                # Handle nested details field
                if 'details' in alert_dict and isinstance(alert_dict['details'], dict):
                    for key, value in alert_dict['details'].items():
                        alert_dict[f"detail_{key}"] = value
                
                alerts_data.append(alert_dict)
        
        # Create DataFrame
        df = pd.DataFrame(alerts_data)
        
        # Write to Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Equipment Alerts', index=False)
            
            # Auto-adjust column widths for better readability
            worksheet = writer.sheets['Equipment Alerts']
            for idx, col in enumerate(df.columns):
                max_len = df[col].astype(str).map(len).max()
                max_len = max(max_len, len(col)) + 2  # Add a little extra space
                worksheet.column_dimensions[worksheet.cell(1, idx+1).column_letter].width = max_len
        
        logger.info(f"Exported {len(alerts)} alerts to Excel: {filepath}")
        return str(filepath)
    
    except Exception as e:
        logger.error(f"Error exporting alerts to Excel: {e}")
        raise

def export_alerts_to_csv(alerts, filename=None):
    """
    Export equipment alerts to CSV format
    
    Args:
        alerts (list): List of alert objects or dictionaries
        filename (str, optional): Output filename. If None, will generate a default name.
        
    Returns:
        str: Path to the exported file
    """
    ensure_export_dir()
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"equipment_alerts_{timestamp}.csv"
    
    # Ensure .csv extension
    if not filename.endswith('.csv'):
        filename += '.csv'
        
    # Full path to output file
    filepath = EXPORTS_DIR / 'alerts' / filename
    
    try:
        # Convert alerts to a list of dictionaries
        alerts_data = []
        for alert in alerts:
            # Handle both ORM objects and dictionaries
            if hasattr(alert, '__dict__'):
                # Convert ORM object to dict, excluding SQLAlchemy special attributes
                alert_dict = {k: v for k, v in alert.__dict__.items() 
                             if not k.startswith('_')}
                
                # Handle nested details field
                if 'details' in alert_dict and isinstance(alert_dict['details'], dict):
                    # Flatten the details field
                    for key, value in alert_dict['details'].items():
                        alert_dict[f"detail_{key}"] = value
                    del alert_dict['details']
                
                alerts_data.append(alert_dict)
            else:
                # Already a dict
                alert_dict = alert.copy()
                
                # Handle nested details field
                if 'details' in alert_dict and isinstance(alert_dict['details'], dict):
                    # Flatten the details field
                    for key, value in alert_dict['details'].items():
                        alert_dict[f"detail_{key}"] = value
                    del alert_dict['details']
                
                alerts_data.append(alert_dict)
        
        # If no alerts, create empty file with headers
        if not alerts_data:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['No alerts found'])
            return str(filepath)
            
        # Get field names from all alerts (some might have different fields)
        fieldnames = set()
        for alert in alerts_data:
            fieldnames.update(alert.keys())
        fieldnames = sorted(list(fieldnames))
        
        # Write to CSV
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for alert in alerts_data:
                writer.writerow(alert)
        
        logger.info(f"Exported {len(alerts)} alerts to CSV: {filepath}")
        return str(filepath)
    
    except Exception as e:
        logger.error(f"Error exporting alerts to CSV: {e}")
        raise

def export_driver_report_to_excel(report_data, filename=None):
    """
    Export driver attendance report to Excel format
    
    Args:
        report_data (dict): Dictionary containing report sections (late_starts, early_ends, not_on_job)
        filename (str, optional): Output filename. If None, will generate a default name.
        
    Returns:
        str: Path to the exported file
    """
    ensure_export_dir()
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"driver_report_{timestamp}.xlsx"
    
    # Ensure .xlsx extension
    if not filename.endswith('.xlsx'):
        filename += '.xlsx'
        
    # Full path to output file
    filepath = EXPORTS_DIR / 'driver_reports' / filename
    
    try:
        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Export late starts
            if 'late_starts' in report_data and report_data['late_starts']:
                late_df = pd.DataFrame(report_data['late_starts'])
                late_df.to_excel(writer, sheet_name='Late Starts', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Late Starts']
                for idx, col in enumerate(late_df.columns):
                    max_len = late_df[col].astype(str).map(len).max()
                    max_len = max(max_len, len(col)) + 2  # Add a little extra space
                    worksheet.column_dimensions[worksheet.cell(1, idx+1).column_letter].width = max_len
            
            # Export early ends
            if 'early_ends' in report_data and report_data['early_ends']:
                early_df = pd.DataFrame(report_data['early_ends'])
                early_df.to_excel(writer, sheet_name='Early Ends', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Early Ends']
                for idx, col in enumerate(early_df.columns):
                    max_len = early_df[col].astype(str).map(len).max()
                    max_len = max(max_len, len(col)) + 2  # Add a little extra space
                    worksheet.column_dimensions[worksheet.cell(1, idx+1).column_letter].width = max_len
            
            # Export not on job
            if 'not_on_job' in report_data and report_data['not_on_job']:
                noj_df = pd.DataFrame(report_data['not_on_job'])
                noj_df.to_excel(writer, sheet_name='Not On Job', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Not On Job']
                for idx, col in enumerate(noj_df.columns):
                    max_len = noj_df[col].astype(str).map(len).max()
                    max_len = max(max_len, len(col)) + 2  # Add a little extra space
                    worksheet.column_dimensions[worksheet.cell(1, idx+1).column_letter].width = max_len
            
            # Export summary
            if 'summary' in report_data:
                summary_data = []
                summary_data.append({'Metric': 'Late Starts', 'Count': len(report_data.get('late_starts', []))})
                summary_data.append({'Metric': 'Early Ends', 'Count': len(report_data.get('early_ends', []))})
                summary_data.append({'Metric': 'Not On Job', 'Count': len(report_data.get('not_on_job', []))})
                summary_data.append({'Metric': 'Total Issues', 'Count': (
                    len(report_data.get('late_starts', [])) + 
                    len(report_data.get('early_ends', [])) + 
                    len(report_data.get('not_on_job', []))
                )})
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Summary']
                for idx, col in enumerate(summary_df.columns):
                    max_len = summary_df[col].astype(str).map(len).max()
                    max_len = max(max_len, len(col)) + 2  # Add a little extra space
                    worksheet.column_dimensions[worksheet.cell(1, idx+1).column_letter].width = max_len
        
        logger.info(f"Exported driver report to Excel: {filepath}")
        return str(filepath)
    
    except Exception as e:
        logger.error(f"Error exporting driver report to Excel: {e}")
        raise

def export_billing_data_to_excel(billing_data, filename=None):
    """
    Export PM billing allocation data to Excel format
    
    Args:
        billing_data (dict): Dictionary containing billing sections
        filename (str, optional): Output filename. If None, will generate a default name.
        
    Returns:
        str: Path to the exported file
    """
    ensure_export_dir()
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pm_billing_{timestamp}.xlsx"
    
    # Ensure .xlsx extension
    if not filename.endswith('.xlsx'):
        filename += '.xlsx'
        
    # Full path to output file
    filepath = EXPORTS_DIR / 'billing' / filename
    
    try:
        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Export each section to its own sheet
            for section_name, section_data in billing_data.items():
                if isinstance(section_data, list) and section_data:
                    df = pd.DataFrame(section_data)
                    df.to_excel(writer, sheet_name=section_name[:31], index=False)  # Limit sheet name to 31 chars
                    
                    # Auto-adjust column widths
                    worksheet = writer.sheets[section_name[:31]]
                    for idx, col in enumerate(df.columns):
                        max_len = df[col].astype(str).map(len).max()
                        max_len = max(max_len, len(col)) + 2  # Add a little extra space
                        worksheet.column_dimensions[worksheet.cell(1, idx+1).column_letter].width = max_len
        
        logger.info(f"Exported billing data to Excel: {filepath}")
        return str(filepath)
    
    except Exception as e:
        logger.error(f"Error exporting billing data to Excel: {e}")
        raise