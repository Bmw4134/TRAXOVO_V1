"""
Asset Driver Mapping Utility

This module extracts driver-asset relationships from Excel files containing the
mapping between drivers and equipment. It helps maintain an up-to-date record
of which drivers are assigned to which assets.
"""

import os
import pandas as pd
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_asset_driver_mappings(file_path, sheet_name="DRIVERS"):
    """
    Extract asset-driver mappings from an Excel file
    
    Args:
        file_path (str): Path to the Excel file containing driver assignments
        sheet_name (str): Name of the sheet containing driver data (default: "DRIVERS")
        
    Returns:
        dict: Mapping of asset_id to driver information
    """
    try:
        # Load the Excel file
        logger.info(f"Loading driver mappings from: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"error": f"File not found: {file_path}"}
        
        # Try to read the Excel file
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            logger.info(f"Successfully loaded sheet: {sheet_name}")
        except Exception as e:
            logger.error(f"Error reading sheet {sheet_name}: {e}")
            
            # Try to get available sheets
            try:
                xl = pd.ExcelFile(file_path)
                available_sheets = xl.sheet_names
                logger.info(f"Available sheets: {available_sheets}")
                
                # Look for a sheet with 'DRIVER' in the name
                driver_sheets = [s for s in available_sheets if 'DRIVER' in s.upper()]
                if driver_sheets:
                    sheet_name = driver_sheets[0]
                    logger.info(f"Using alternative driver sheet: {sheet_name}")
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                else:
                    # Try the first sheet
                    sheet_name = available_sheets[0]
                    logger.info(f"Using first sheet: {sheet_name}")
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
            except Exception as e2:
                logger.error(f"Error reading Excel file: {e2}")
                return {"error": f"Error reading Excel file: {str(e2)}"}
        
        # Find the most recent month's data
        # Common column patterns for asset ID and driver info
        asset_id_cols = []
        for col in df.columns:
            col_str = str(col).upper()
            if 'ASSET ID' in col_str or 'ASSET_ID' in col_str:
                asset_id_cols.append(col)
        
        if not asset_id_cols:
            logger.error("No asset ID column found")
            return {"error": "No asset ID column found"}
        
        # Find months in the column headers
        months = []
        for col in df.columns:
            col_str = str(col).upper()
            month_keywords = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                             'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            year_pattern = r'20\d\d'  # 2020, 2021, 2022, etc.
            
            # Check if column has month and year
            if any(month in col_str for month in month_keywords) and '20' in col_str:
                months.append(col)
        
        months.sort(reverse=True)  # Sort in descending order to get most recent first
        
        # Get most recent month
        recent_month = None
        for col in months:
            if pd.notna(col) and 'DRIVER' in str(col).upper():
                recent_month = col
                break
        
        if not recent_month:
            logger.warning("No month column found, using first column")
            # Just use the first column as fallback
            recent_month = asset_id_cols[0]
        
        logger.info(f"Using column: {recent_month}")
        
        # Find corresponding employee and ID columns
        # Column patterns may vary, but typically they are within a few columns of the asset ID
        asset_id_idx = list(df.columns).index(asset_id_cols[0])
        employee_col = None
        employee_id_col = None
        
        # Look for nearby columns with employee info
        nearby_cols = list(df.columns)[asset_id_idx:asset_id_idx+5]  # Check next 5 columns
        for col in nearby_cols:
            col_str = str(col).upper()
            if 'EMPLOYEE' in col_str and not 'ID' in col_str:
                employee_col = col
            elif 'EMPLOYEE ID' in col_str or 'EMP ID' in col_str or 'EMPLOYEE_ID' in col_str:
                employee_id_col = col
        
        if not employee_col:
            logger.warning("Employee column not found")
        if not employee_id_col:
            logger.warning("Employee ID column not found")
        
        # Parse the data to extract asset-driver mappings
        asset_driver_map = {}
        
        # Skip header rows
        data_start_row = 0
        for i, row in df.iterrows():
            if pd.notna(row.get(asset_id_cols[0])) and 'ASSET ID' in str(row.get(asset_id_cols[0])).upper():
                data_start_row = i + 1
                break
        
        # Process data rows
        for i, row in df.iloc[data_start_row:].iterrows():
            asset_id = row.get(asset_id_cols[0])
            
            # Skip empty asset IDs
            if pd.isna(asset_id) or str(asset_id).strip() == '':
                continue
            
            # Clean up asset ID
            asset_id = str(asset_id).strip()
            
            # Extract employee info
            employee_name = row.get(employee_col) if employee_col and pd.notna(row.get(employee_col)) else None
            employee_id = row.get(employee_id_col) if employee_id_col and pd.notna(row.get(employee_id_col)) else None
            
            # Skip rows with no employee info
            if not employee_name and not employee_id:
                logger.debug(f"No employee info for asset: {asset_id}")
                continue
            
            # Clean up employee info
            if employee_name:
                employee_name = str(employee_name).strip()
                # Handle special cases
                if employee_name.upper() in ['OPEN', 'SOLD', 'RETIRED', 'N/A']:
                    employee_name = None
            
            if employee_id:
                employee_id = str(employee_id).strip()
                # Handle special cases
                if employee_id.upper() in ['OPEN', 'SOLD', 'RETIRED', 'N/A']:
                    employee_id = None
            
            # Store the mapping
            if employee_name or employee_id:
                asset_driver_map[asset_id] = {
                    'asset_id': asset_id,
                    'employee_name': employee_name,
                    'employee_id': employee_id
                }
        
        logger.info(f"Extracted {len(asset_driver_map)} asset-driver mappings")
        
        return {
            "status": "success",
            "mappings": asset_driver_map,
            "count": len(asset_driver_map)
        }
        
    except Exception as e:
        logger.error(f"Error extracting asset-driver mappings: {e}")
        return {"error": str(e)}

def update_drivers_in_database(mappings, db_session=None):
    """
    Update driver information in the database based on extracted mappings
    
    Args:
        mappings (dict): Asset-driver mappings from extract_asset_driver_mappings
        db_session: Database session for SQLAlchemy ORM
        
    Returns:
        dict: Update statistics
    """
    try:
        if not db_session:
            logger.error("No database session provided")
            return {"error": "No database session provided"}
        
        from models import Asset, Driver
        
        updated_count = 0
        new_drivers = 0
        
        for asset_id, data in mappings.items():
            # Find the asset in the database
            asset = db_session.query(Asset).filter_by(asset_identifier=asset_id).first()
            
            if not asset:
                logger.warning(f"Asset not found in database: {asset_id}")
                continue
            
            # Get driver info
            employee_name = data.get('employee_name')
            employee_id = data.get('employee_id')
            
            if not employee_name and not employee_id:
                continue
            
            # Find or create driver
            driver = None
            if employee_id:
                driver = db_session.query(Driver).filter_by(employee_id=employee_id).first()
            
            if not driver and employee_name:
                driver = db_session.query(Driver).filter_by(name=employee_name).first()
            
            # Create a new driver if not found
            if not driver and (employee_name or employee_id):
                driver = Driver(
                    name=employee_name,
                    employee_id=employee_id if employee_id else f"AUTO-{asset_id}",
                    active=True
                )
                db_session.add(driver)
                new_drivers += 1
                logger.info(f"Created new driver: {employee_name} ({employee_id})")
            
            if driver and asset:
                # Update the asset with the driver
                asset.driver_id = driver.id
                updated_count += 1
                logger.info(f"Updated asset {asset_id} with driver {driver.name}")
        
        # Commit changes
        db_session.commit()
        
        return {
            "status": "success",
            "updated_assets": updated_count,
            "new_drivers": new_drivers
        }
        
    except Exception as e:
        logger.error(f"Error updating drivers in database: {e}")
        if db_session:
            db_session.rollback()
        return {"error": str(e)}

def generate_driver_asset_report(mappings, output_path=None):
    """
    Generate a report of driver-asset assignments
    
    Args:
        mappings (dict): Asset-driver mappings
        output_path (str, optional): Path to save Excel report
        
    Returns:
        dict: Report generation status
    """
    try:
        # Convert mappings to DataFrame
        data = []
        for asset_id, info in mappings.items():
            data.append({
                'Asset ID': asset_id,
                'Driver Name': info.get('employee_name'),
                'Driver ID': info.get('employee_id')
            })
        
        df = pd.DataFrame(data)
        
        # Sort by asset ID
        df.sort_values('Asset ID', inplace=True)
        
        # Generate Excel report if output path provided
        if output_path:
            df.to_excel(output_path, index=False, sheet_name='Driver Assignments')
            logger.info(f"Report saved to: {output_path}")
            return {
                "status": "success",
                "report_path": output_path,
                "count": len(data)
            }
        
        return {
            "status": "success",
            "data": df,
            "count": len(data)
        }
        
    except Exception as e:
        logger.error(f"Error generating driver-asset report: {e}")
        return {"error": str(e)}