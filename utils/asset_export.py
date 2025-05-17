"""
Asset Export Utility

This module provides functions for exporting asset data in multiple formats
including Excel, CSV, JSON, and more.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
import io

logger = logging.getLogger(__name__)

def generate_asset_report(assets, output_path, format_type='excel'):
    """
    Generate an asset report in the specified format.
    
    Args:
        assets (list): List of Asset objects to include in the report
        output_path (str or Path): Path where the report should be saved
        format_type (str): Format of the report ('excel', 'csv', 'json')
        
    Returns:
        str: Path to the generated report file
    """
    try:
        # Convert the output_path to a Path object if it's a string
        if isinstance(output_path, str):
            output_path = Path(output_path)
            
        # Create directory if it doesn't exist
        output_path.parent.mkdir(exist_ok=True)
        
        # Convert assets to a list of dictionaries for easier manipulation
        assets_data = []
        for asset in assets:
            asset_dict = {
                'id': asset.id,
                'name': asset.name,
                'asset_number': asset.asset_number,
                'type': asset.type,
                'status': asset.status,
                'manufacturer': asset.manufacturer,
                'model': asset.model,
                'year': asset.year,
                'serial_number': asset.serial_number,
                'region': asset.region,
                'location': asset.location,
                'job_number': asset.job_number,
                'last_maintenance_date': asset.last_maintenance_date.strftime('%Y-%m-%d') if asset.last_maintenance_date else None,
                'next_maintenance_date': asset.next_maintenance_date.strftime('%Y-%m-%d') if asset.next_maintenance_date else None,
                'purchase_date': asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else None,
                'purchase_price': asset.purchase_price,
                'current_value': asset.current_value,
                'monthly_cost': asset.monthly_cost,
                'hourly_rate': asset.hourly_rate,
                'last_hour_reading': asset.last_hour_reading,
                'last_hour_reading_date': asset.last_hour_reading_date.strftime('%Y-%m-%d') if asset.last_hour_reading_date else None,
                'total_hours': asset.total_hours,
                'total_idle_hours': asset.total_idle_hours,
                'fuel_level': asset.fuel_level,
                'organization_id': asset.organization_id,
                'latitude': asset.latitude,
                'longitude': asset.longitude,
                'last_updated': asset.last_updated.strftime('%Y-%m-%d %H:%M:%S') if asset.last_updated else None,
                'notes': asset.notes
            }
            
            # Include any custom fields or calculated values
            asset_dict['utilization_rate'] = calculate_utilization_rate(asset)
            asset_dict['maintenance_status'] = get_maintenance_status(asset)
            asset_dict['days_since_last_maintenance'] = calculate_days_since_last_maintenance(asset)
            
            assets_data.append(asset_dict)
        
        # Create a DataFrame from the assets data
        df = pd.DataFrame(assets_data)
        
        # Generate report based on the requested format
        if format_type.lower() == 'excel':
            return generate_excel_report(df, output_path)
        elif format_type.lower() == 'csv':
            return generate_csv_report(df, output_path)
        elif format_type.lower() == 'json':
            return generate_json_report(assets_data, output_path)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
            
    except Exception as e:
        logger.error(f"Error generating asset report: {str(e)}")
        raise


def generate_excel_report(df, output_path):
    """Generate an Excel report from a DataFrame"""
    try:
        # Create a writer for the Excel file
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Write the main asset data
            df.to_excel(writer, sheet_name='Assets', index=False)
            
            # Create a summary sheet
            summary = create_summary_data(df)
            summary_df = pd.DataFrame(summary)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Create a status breakdown sheet
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            status_counts.to_excel(writer, sheet_name='Status Breakdown', index=False)
            
            # Create a type breakdown sheet
            type_counts = df['type'].value_counts().reset_index()
            type_counts.columns = ['Type', 'Count']
            type_counts.to_excel(writer, sheet_name='Type Breakdown', index=False)
            
            # Create a region breakdown sheet if region column exists
            if 'region' in df.columns:
                region_counts = df['region'].value_counts().reset_index()
                region_counts.columns = ['Region', 'Count']
                region_counts.to_excel(writer, sheet_name='Region Breakdown', index=False)
            
        return str(output_path)
    
    except Exception as e:
        logger.error(f"Error generating Excel report: {str(e)}")
        raise


def generate_csv_report(df, output_path):
    """Generate a CSV report from a DataFrame"""
    try:
        df.to_csv(output_path, index=False)
        return str(output_path)
    
    except Exception as e:
        logger.error(f"Error generating CSV report: {str(e)}")
        raise


def generate_json_report(assets_data, output_path):
    """Generate a JSON report from assets data"""
    try:
        # Add a metadata section to the JSON
        report_data = {
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'asset_count': len(assets_data),
                'report_type': 'Equipment Asset Report'
            },
            'assets': assets_data
        }
        
        # Write the JSON data to the output file
        with open(output_path, 'w') as json_file:
            json.dump(report_data, json_file, indent=2)
            
        return str(output_path)
    
    except Exception as e:
        logger.error(f"Error generating JSON report: {str(e)}")
        raise


def create_summary_data(df):
    """Create summary data for the asset report"""
    summary = []
    
    # Total assets
    summary.append({
        'Metric': 'Total Assets',
        'Value': len(df)
    })
    
    # Assets by status
    for status, count in df['status'].value_counts().items():
        summary.append({
            'Metric': f'Assets with Status: {status}',
            'Value': count
        })
    
    # Assets by type
    for asset_type, count in df['type'].value_counts().items():
        summary.append({
            'Metric': f'Assets of Type: {asset_type}',
            'Value': count
        })
    
    # Total value
    if 'current_value' in df.columns and df['current_value'].notna().any():
        total_value = df['current_value'].sum()
        summary.append({
            'Metric': 'Total Asset Value',
            'Value': f"${total_value:,.2f}"
        })
    
    # Assets needing maintenance
    if 'maintenance_status' in df.columns:
        maintenance_needed = df[df['maintenance_status'] == 'Due'].shape[0]
        summary.append({
            'Metric': 'Assets Needing Maintenance',
            'Value': maintenance_needed
        })
    
    return summary


def calculate_utilization_rate(asset):
    """
    Calculate the asset utilization rate based on total hours and idle hours.
    
    Returns:
        float or None: Utilization rate as a percentage, or None if not enough data
    """
    if asset.total_hours is not None and asset.total_idle_hours is not None and asset.total_hours > 0:
        active_hours = asset.total_hours - asset.total_idle_hours
        return round((active_hours / asset.total_hours) * 100, 2)
    return None


def get_maintenance_status(asset):
    """
    Determine the maintenance status of an asset.
    
    Returns:
        str: Maintenance status ('Due', 'Upcoming', 'OK', or 'Unknown')
    """
    if not asset.next_maintenance_date:
        return 'Unknown'
    
    days_until_maintenance = (asset.next_maintenance_date - datetime.now().date()).days
    
    if days_until_maintenance < 0:
        return 'Due'
    elif days_until_maintenance < 30:
        return 'Upcoming'
    else:
        return 'OK'


def calculate_days_since_last_maintenance(asset):
    """
    Calculate the number of days since the last maintenance.
    
    Returns:
        int or None: Number of days since last maintenance, or None if not available
    """
    if not asset.last_maintenance_date:
        return None
    
    return (datetime.now().date() - asset.last_maintenance_date).days