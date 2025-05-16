"""
Asset Driver Mapper Utility

This module provides utilities for mapping and managing relationships between
assets and drivers, including extracting relationships from files, validating 
assignments, and tracking historical assignments.
"""

import os
import pandas as pd
from datetime import datetime, date
from flask import session
from sqlalchemy import or_

from models.models import Asset
from models.core import Driver
from app import db

def extract_driver_asset_relationships(file_path, asset_column='Asset ID', driver_column='Driver ID'):
    """
    Extract driver-asset relationships from file
    
    Args:
        file_path (str): Path to file containing driver-asset relationships
        asset_column (str): Column name for asset identifier
        driver_column (str): Column name for driver identifier
        
    Returns:
        list: List of dictionaries with asset_id, driver_id
    """
    # Detect file type from extension
    _, ext = os.path.splitext(file_path)
    
    try:
        if ext.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif ext.lower() == '.csv':
            df = pd.read_csv(file_path)
        else:
            return [], "Unsupported file format. Please upload .xlsx, .xls, or .csv files."
        
        # Verify required columns exist
        if asset_column not in df.columns or driver_column not in df.columns:
            return [], f"Required columns not found. Needed: {asset_column}, {driver_column}"
        
        # Extract relationships
        relationships = []
        for _, row in df.iterrows():
            asset_id = str(row[asset_column]).strip()
            driver_id = str(row[driver_column]).strip()
            
            if not asset_id or not driver_id or pd.isna(asset_id) or pd.isna(driver_id):
                continue
                
            relationship = {
                'asset_id': asset_id,
                'driver_id': driver_id
            }
            relationships.append(relationship)
            
        return relationships, None
    
    except Exception as e:
        return [], f"Error processing file: {str(e)}"

def find_asset_by_identifier(asset_id):
    """
    Find an asset by its identifier
    
    Args:
        asset_id (str): Asset identifier to search for
        
    Returns:
        Asset: Asset object if found, None otherwise
    """
    return Asset.query.filter(Asset.asset_identifier == asset_id).first()

def find_driver_by_identifier(driver_id):
    """
    Find a driver by identifier (name or employee ID)
    
    Args:
        driver_id (str): Driver identifier to search for
        
    Returns:
        Driver: Driver object if found, None otherwise
    """
    # Try exact match on employee ID first
    driver = Driver.query.filter(Driver.employee_id == driver_id).first()
    
    if not driver:
        # Try name (both exact and partial matching)
        driver = Driver.query.filter(or_(
            Driver.name == driver_id,
            Driver.name.ilike(f"%{driver_id}%")
        )).first()
    
    return driver

def process_assignment_file(file_path, asset_column='Asset ID', driver_column='Driver ID', 
                          start_date_column=None, has_header=True, end_previous=True, session_id=None):
    """
    Process an uploaded file containing asset-driver assignments
    
    Args:
        file_path (str): Path to the uploaded file
        asset_column (str): Column name for asset identifier
        driver_column (str): Column name for driver identifier
        start_date_column (str): Column name for start date (optional)
        has_header (bool): Whether the file has a header row
        end_previous (bool): Whether to end previous assignments for assets
        session_id (str): Session ID for storing results
        
    Returns:
        tuple: (preview_data, valid_count)
    """
    try:
        # Read file based on extension
        _, ext = os.path.splitext(file_path)
        
        if ext.lower() in ['.xlsx', '.xls']:
            if has_header:
                df = pd.read_excel(file_path)
            else:
                df = pd.read_excel(file_path, header=None)
                df.columns = [f"Column_{i}" for i in range(len(df.columns))]
                # Assume first column is asset, second is driver
                asset_column = "Column_0"
                driver_column = "Column_1"
                if start_date_column:
                    start_date_column = "Column_2"
                    
        elif ext.lower() == '.csv':
            if has_header:
                df = pd.read_csv(file_path)
            else:
                df = pd.read_csv(file_path, header=None)
                df.columns = [f"Column_{i}" for i in range(len(df.columns))]
                # Assume first column is asset, second is driver
                asset_column = "Column_0"
                driver_column = "Column_1"
                if start_date_column:
                    start_date_column = "Column_2"
        else:
            return [{"status": "error", "message": "Unsupported file format"}], 0
        
        # Verify required columns exist
        if asset_column not in df.columns or driver_column not in df.columns:
            return [{"status": "error", "message": f"Required columns not found: {asset_column}, {driver_column}"}], 0
        
        if start_date_column and start_date_column not in df.columns:
            start_date_column = None
        
        # Process rows
        preview_data = []
        valid_count = 0
        
        for _, row in df.iterrows():
            try:
                asset_id_raw = row[asset_column]
                driver_id_raw = row[driver_column]
                
                # Skip empty rows
                if pd.isna(asset_id_raw) or pd.isna(driver_id_raw):
                    continue
                
                # Convert to string and clean
                asset_id_str = str(asset_id_raw).strip()
                driver_id_str = str(driver_id_raw).strip()
                
                if not asset_id_str or not driver_id_str:
                    continue
                
                # Parse start date if provided
                start_date_value = None
                if start_date_column and start_date_column in df.columns:
                    start_date_raw = row[start_date_column]
                    if not pd.isna(start_date_raw):
                        if isinstance(start_date_raw, (datetime, date)):
                            start_date_value = start_date_raw.date() if isinstance(start_date_raw, datetime) else start_date_raw
                        else:
                            try:
                                start_date_value = pd.to_datetime(start_date_raw).date()
                            except:
                                start_date_value = date.today()
                
                # Find asset and driver
                asset = find_asset_by_identifier(asset_id_str)
                driver = find_driver_by_identifier(driver_id_str)
                
                data = {
                    "asset_id_raw": asset_id_str,
                    "driver_id_raw": driver_id_str,
                    "start_date": start_date_value,
                    "end_previous": end_previous
                }
                
                if not asset:
                    data["status"] = "error"
                    data["message"] = f"Asset not found: {asset_id_str}"
                    data["asset_id"] = asset_id_str
                    data["driver_id"] = driver_id_str
                elif not driver:
                    data["status"] = "error"
                    data["message"] = f"Driver not found: {driver_id_str}"
                    data["asset_id"] = asset_id_str
                    data["driver_id"] = driver_id_str
                else:
                    data["status"] = "valid"
                    data["asset"] = asset
                    data["driver"] = driver
                    data["asset_id"] = asset.id
                    data["driver_id"] = driver.id
                    valid_count += 1
                
                preview_data.append(data)
                
            except Exception as e:
                preview_data.append({
                    "status": "error",
                    "message": f"Error processing row: {str(e)}",
                    "asset_id": str(row.get(asset_column, '')),
                    "driver_id": str(row.get(driver_column, ''))
                })
        
        # Store valid assignments in session for later
        if session_id:
            session[f'asset_driver_import_{session_id}'] = preview_data
        
        return preview_data, valid_count
        
    except Exception as e:
        return [{"status": "error", "message": f"Error processing file: {str(e)}"}], 0

def validate_assignments(assignments):
    """
    Validate a list of asset-driver assignments
    
    Args:
        assignments (list): List of assignment dictionaries
        
    Returns:
        tuple: (valid_assignments, error_messages)
    """
    valid_assignments = []
    error_messages = []
    
    for assignment in assignments:
        asset_id = assignment.get('asset_id')
        driver_id = assignment.get('driver_id')
        
        if not asset_id or not driver_id:
            error_messages.append(f"Missing asset or driver ID: {assignment}")
            continue
        
        asset = find_asset_by_identifier(asset_id)
        driver = find_driver_by_identifier(driver_id)
        
        if not asset:
            error_messages.append(f"Asset not found: {asset_id}")
            continue
            
        if not driver:
            error_messages.append(f"Driver not found: {driver_id}")
            continue
        
        valid_assignment = {
            'asset_id': asset.id,
            'driver_id': driver.id,
            'start_date': assignment.get('start_date', date.today()),
            'end_previous': assignment.get('end_previous', True)
        }
        
        valid_assignments.append(valid_assignment)
    
    return valid_assignments, error_messages