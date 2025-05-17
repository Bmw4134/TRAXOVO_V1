"""
Asset Export Utility

This module provides functions for exporting asset data in various formats
including Excel, CSV, and JSON with additional metadata and formatting.
"""

import os
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

# Ensure exports directory exists
EXPORTS_DIR = Path('exports')
EXPORTS_DIR.mkdir(exist_ok=True)

def generate_asset_export(assets, export_format, filename, organization, region, status):
    """
    Generate an export file for the given assets in the specified format.
    
    Args:
        assets (list): List of Asset model instances to export
        export_format (str): Format to export (excel, csv, json)
        filename (str): Base filename for the export (without extension)
        organization (str): Organization filter used
        region (str): Region filter used
        status (str): Status filter used
        
    Returns:
        str: Path to the generated export file, or None if export failed
    """
    try:
        # Convert assets to a list of dictionaries for easier processing
        asset_data = []
        for asset in assets:
            # Get base asset data
            asset_dict = {
                'id': asset.id,
                'asset_id': asset.asset_id,
                'name': asset.name,
                'type': asset.type,
                'make': asset.make,
                'model': asset.model,
                'serial_number': asset.serial_number,
                'year': asset.year,
                'status': asset.status,
                'region': asset.region,
                'location': asset.location,
                'last_location_update': asset.last_location_update,
                'last_service_date': asset.last_service_date,
                'next_service_date': asset.next_service_date,
                'purchase_date': asset.purchase_date,
                'purchase_price': asset.purchase_price,
                'current_value': asset.current_value,
                'hours': asset.hours,
                'last_hours_update': asset.last_hours_update,
                'fuel_level': asset.fuel_level,
                'last_fuel_update': asset.last_fuel_update,
                'organization': asset.organization.name if asset.organization else 'Unassigned'
            }
            
            # Add GPS data if available
            if hasattr(asset, 'latitude') and hasattr(asset, 'longitude'):
                asset_dict.update({
                    'latitude': asset.latitude,
                    'longitude': asset.longitude
                })
                
            # Add custom fields for different asset types
            if asset.type == 'Heavy Equipment':
                asset_dict.update({
                    'equipment_class': getattr(asset, 'equipment_class', ''),
                    'rental_rate': getattr(asset, 'rental_rate', ''),
                    'monthly_cost': getattr(asset, 'monthly_cost', '')
                })
            elif asset.type == 'Vehicle':
                asset_dict.update({
                    'license_plate': getattr(asset, 'license_plate', ''),
                    'vin': getattr(asset, 'vin', ''),
                    'mileage': getattr(asset, 'mileage', ''),
                    'last_mileage_update': getattr(asset, 'last_mileage_update', '')
                })
                
            asset_data.append(asset_dict)
            
        # Generate export based on requested format
        if export_format == 'excel':
            return export_to_excel(asset_data, filename, organization, region, status)
        elif export_format == 'csv':
            return export_to_csv(asset_data, filename, organization, region, status)
        elif export_format == 'json':
            return export_to_json(asset_data, filename, organization, region, status)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
            
    except Exception as e:
        print(f"Error generating asset export: {e}")
        return None

def export_to_excel(asset_data, filename, organization, region, status):
    """Export asset data to Excel format with multiple sheets and formatting"""
    if not asset_data:
        return None
        
    # Create a pandas DataFrame from the asset data
    df = pd.DataFrame(asset_data)
    
    # Add filename extension
    filename = f"{filename}.xlsx"
    file_path = os.path.join(EXPORTS_DIR, filename)
    
    # Create Excel writer with the ExcelWriter engine
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        # Write main asset data sheet
        df.to_excel(writer, sheet_name='Assets', index=False)
        
        # Create asset counts by type sheet
        type_counts = df['type'].value_counts().reset_index()
        type_counts.columns = ['Asset Type', 'Count']
        type_counts.to_excel(writer, sheet_name='Asset Type Summary', index=False)
        
        # Create asset counts by status sheet
        status_counts = df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        status_counts.to_excel(writer, sheet_name='Status Summary', index=False)
        
        # Create asset counts by region sheet if region data exists
        if 'region' in df.columns:
            region_counts = df['region'].value_counts().reset_index()
            region_counts.columns = ['Region', 'Count']
            region_counts.to_excel(writer, sheet_name='Region Summary', index=False)
        
        # Create an overview sheet with metadata
        metadata = {
            'Export Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Organization': organization,
            'Region Filter': region,
            'Status Filter': status,
            'Total Assets': len(df),
            'Generated By': 'TRAXORA Export System'
        }
        
        # Convert metadata to dataframe for output
        metadata_df = pd.DataFrame(list(metadata.items()), columns=['Property', 'Value'])
        metadata_df.to_excel(writer, sheet_name='Export Info', index=False)
    
    return file_path

def export_to_csv(asset_data, filename, organization, region, status):
    """Export asset data to CSV format"""
    if not asset_data:
        return None
        
    # Create a pandas DataFrame from the asset data
    df = pd.DataFrame(asset_data)
    
    # Add filename extension
    filename = f"{filename}.csv"
    file_path = os.path.join(EXPORTS_DIR, filename)
    
    # Write data to CSV
    df.to_csv(file_path, index=False)
    
    return file_path

def export_to_json(asset_data, filename, organization, region, status):
    """Export asset data to JSON format with metadata"""
    if not asset_data:
        return None
    
    # Create a JSON structure with metadata and asset data
    export_data = {
        'metadata': {
            'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'organization': organization,
            'region_filter': region,
            'status_filter': status,
            'total_assets': len(asset_data),
            'generated_by': 'TRAXORA Export System'
        },
        'assets': asset_data
    }
    
    # Add filename extension
    filename = f"{filename}.json"
    file_path = os.path.join(EXPORTS_DIR, filename)
    
    # Write data to JSON file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    return file_path