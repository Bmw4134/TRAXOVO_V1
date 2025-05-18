"""
Calculate PM Allocations

This script locates all PM allocation sheets, applies their changes to the base RAGLE file,
and generates the final deliverables with the updated totals.
"""
import os
import pandas as pd
import glob
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
ATTACHED_ASSETS_DIR = 'attached_assets'
EXPORTS_DIR = 'exports'
MONTH_NAME = 'APRIL'
YEAR = '2025'

# Output file names
FINALIZED_MASTER_ALLOCATION = f"FINALIZED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
MASTER_BILLINGS = f"MASTER_EQUIP_BILLINGS_{MONTH_NAME}_{YEAR}.xlsx"
REGION_IMPORT_PREFIX = "FINAL_REGION_IMPORT_"

# Source files
RAGLE_FILE = "RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm"
PM_ALLOCATION_PATTERN = "*EQMO. BILLING ALLOCATIONS*"

def find_pm_allocation_files():
    """Find all PM allocation files"""
    pm_files = []
    patterns = [
        "*EQMO. BILLING ALLOCATIONS*APRIL*2025*.xlsx", 
        "*ALLOCATIONS*APRIL*2025*.xlsx",
        "*ALLOCATION*APR*2025*.xlsx"
    ]
    
    for pattern in patterns:
        pattern_files = glob.glob(os.path.join(ATTACHED_ASSETS_DIR, pattern))
        for file in pattern_files:
            # Check if it's a PM revision file by looking for PM names or revision indicators
            filename = os.path.basename(file).upper()
            if any(keyword in filename for keyword in 
                   ["HARDIMO", "KOCMICK", "MORALES", "ALVAREZ", "REVISION", "ALLOCATED", "TR-FINAL"]):
                pm_files.append(file)
    
    logger.info(f"Found {len(pm_files)} PM allocation files")
    return pm_files

def load_base_file():
    """Load the base RAGLE file"""
    ragle_path = os.path.join(ATTACHED_ASSETS_DIR, RAGLE_FILE)
    if not os.path.exists(ragle_path):
        logger.error(f"Base RAGLE file not found: {ragle_path}")
        return None
    
    try:
        logger.info(f"Loading base RAGLE file: {ragle_path}")
        ragle_df = pd.read_excel(ragle_path, sheet_name="Equip Billings")
        logger.info(f"Loaded {len(ragle_df)} records from base RAGLE file")
        return ragle_df
    except Exception as e:
        logger.error(f"Error loading base RAGLE file: {str(e)}")
        return None

def load_pm_allocation_file(file_path):
    """Load a PM allocation file and extract the relevant data"""
    try:
        logger.info(f"Processing PM allocation file: {os.path.basename(file_path)}")
        
        # First get all sheet names
        xls = pd.ExcelFile(file_path)
        sheet_names = xls.sheet_names
        
        # Try to find sheets with relevant names
        allocation_sheet = None
        for sheet in sheet_names:
            sheet_lower = sheet.lower()
            if any(keyword in sheet_lower for keyword in ["allocation", "billing", "equip", "pm", "data"]):
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet)
                    # Check if this sheet has data and relevant columns
                    if not df.empty and any(col for col in df.columns if isinstance(col, str) and 
                                          any(name in col.lower() for name in ["equip", "job", "amount", "unit"])):
                        allocation_sheet = sheet
                        break
                except:
                    continue
        
        # If no sheet found with those names, try the first sheet
        if not allocation_sheet and sheet_names:
            allocation_sheet = sheet_names[0]
        
        if not allocation_sheet:
            logger.warning(f"Could not find a valid allocation sheet in {os.path.basename(file_path)}")
            return None
        
        # Load the sheet
        df = pd.read_excel(file_path, sheet_name=allocation_sheet)
        
        # Try to identify key columns
        key_columns = {
            'equip_id': ['equip', 'equipment', 'eq #', 'eq id', 'equip id'],
            'job': ['job', 'job #', 'job number', 'job id'],
            'cost_code': ['cost code', 'cost', 'cc', 'code'],
            'phase': ['phase', 'ph', 'phase code'],
            'units': ['units', 'qty', 'quantity', 'hrs', 'hours', 'unit', 'allocated'],
            'rate': ['rate', 'unit rate', 'equip rate', 'billing rate'],
            'amount': ['amount', 'total', 'billing amount']
        }
        
        column_map = {}
        for key, patterns in key_columns.items():
            for col in df.columns:
                if isinstance(col, str) and any(pattern in col.lower() for pattern in patterns):
                    column_map[key] = col
                    break
        
        # Check if we have the minimum required columns
        if 'equip_id' not in column_map or ('units' not in column_map and 'amount' not in column_map):
            logger.warning(f"Missing required columns in {os.path.basename(file_path)}")
            return None
        
        # Create standardized dataframe
        std_df = pd.DataFrame()
        
        # Copy data from original columns to standardized columns
        for std_col, orig_col in column_map.items():
            std_df[std_col] = df[orig_col]
        
        # Calculate missing values if possible
        if 'units' in std_df.columns and 'rate' in std_df.columns and 'amount' not in std_df.columns:
            std_df['units'] = pd.to_numeric(std_df['units'], errors='coerce').fillna(0)
            std_df['rate'] = pd.to_numeric(std_df['rate'], errors='coerce').fillna(0)
            std_df['amount'] = std_df['units'] * std_df['rate']
        
        # Log summary
        logger.info(f"Extracted {len(std_df)} records from {os.path.basename(file_path)}")
        if 'amount' in std_df.columns:
            total = pd.to_numeric(std_df['amount'], errors='coerce').sum()
            logger.info(f"Total amount in {os.path.basename(file_path)}: ${total:,.2f}")
        
        return std_df
    
    except Exception as e:
        logger.error(f"Error processing {os.path.basename(file_path)}: {str(e)}")
        return None

def merge_pm_allocations(base_df, pm_allocation_dfs):
    """Merge PM allocation data with the base data"""
    if not base_df or base_df.empty:
        logger.error("Base dataframe is empty")
        return None
    
    # Make a copy of the base dataframe
    merged_df = base_df.copy()
    merged_df.columns = [col.lower() if isinstance(col, str) else col for col in merged_df.columns]
    
    # Track base total
    base_total = 0
    for col in merged_df.columns:
        if isinstance(col, str) and 'amount' in col.lower():
            base_total = pd.to_numeric(merged_df[col], errors='coerce').sum()
            break
    
    logger.info(f"Base total before PM allocations: ${base_total:,.2f}")
    
    # Merge each PM allocation dataframe
    for pm_df in pm_allocation_dfs:
        if pm_df is None or pm_df.empty:
            continue
        
        # Get the equipment IDs from this PM allocation
        if 'equip_id' in pm_df.columns:
            equip_ids = pm_df['equip_id'].unique()
            logger.info(f"Processing PM changes for {len(equip_ids)} equipment IDs")
            
            # Find equipment ID column in merged_df
            equip_col = None
            for col in merged_df.columns:
                if isinstance(col, str) and any(name in col.lower() for name in ['equip #', 'equipment', 'equip id']):
                    equip_col = col
                    break
            
            if not equip_col:
                logger.warning("Could not find equipment ID column in base data")
                continue
            
            # Process each equipment ID
            for equip_id in equip_ids:
                # Find all records for this equipment in the PM allocation
                pm_equip_records = pm_df[pm_df['equip_id'] == equip_id]
                
                if not pm_equip_records.empty:
                    # Remove existing records for this equipment from merged_df
                    merged_df = merged_df[merged_df[equip_col] != equip_id]
                    
                    # Create records to add
                    new_records = []
                    for _, pm_row in pm_equip_records.iterrows():
                        new_record = {}
                        
                        # First find corresponding columns in merged_df for each PM allocation column
                        for pm_col in pm_row.index:
                            if pm_col == 'equip_id':
                                new_record[equip_col] = pm_row[pm_col]
                            else:
                                # Find matching column in merged_df
                                for merged_col in merged_df.columns:
                                    if isinstance(merged_col, str) and pm_col in merged_col.lower():
                                        new_record[merged_col] = pm_row[pm_col]
                                        break
                        
                        # Add missing columns with empty values
                        for col in merged_df.columns:
                            if col not in new_record:
                                new_record[col] = None
                        
                        new_records.append(new_record)
                    
                    # Add the new records to merged_df
                    new_records_df = pd.DataFrame(new_records)
                    merged_df = pd.concat([merged_df, new_records_df], ignore_index=True)
    
    # Calculate the new total
    merged_total = 0
    for col in merged_df.columns:
        if isinstance(col, str) and 'amount' in col.lower():
            merged_total = pd.to_numeric(merged_df[col], errors='coerce').sum()
            break
    
    logger.info(f"Merged total after PM allocations: ${merged_total:,.2f}")
    logger.info(f"Change in total: ${merged_total - base_total:,.2f}")
    
    return merged_df

def generate_deliverables(merged_df):
    """Generate the three required deliverables from the merged data"""
    if merged_df is None or merged_df.empty:
        logger.error("Merged dataframe is empty, cannot generate deliverables")
        return False
    
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # 1. Generate FINALIZED MASTER ALLOCATION SHEET
    master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
    merged_df.to_excel(master_allocation_path, index=False, sheet_name='Master Allocation')
    logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
    
    # 2. Generate MASTER BILLINGS SHEET (same content, different filename)
    master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
    merged_df.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
    logger.info(f"Generated Master Billings Sheet: {master_billing_path}")
    
    # 3. Generate FINAL REGION IMPORT FILES
    # First identify division column
    division_col = None
    for col in merged_df.columns:
        if isinstance(col, str) and 'division' in col.lower():
            division_col = col
            break
    
    if not division_col:
        logger.warning("Could not identify division column, using backup approach for division imports")
        # Try to identify divisions based on job numbers or other patterns
        # This is a fallback approach
        return False
    
    # Generate import files for each division
    for division in ['DFW', 'WTX', 'HOU']:
        # For WTX, look for both WTX and WT
        if division == 'WTX':
            division_data = merged_df[merged_df[division_col].isin(['WTX', 'WT'])].copy()
        else:
            division_data = merged_df[merged_df[division_col] == division].copy()
        
        if not division_data.empty:
            # Map columns for the export
            column_mapping = {}
            for target, patterns in {
                'Equipment_Number': ['equip #', 'equipment', 'equip id'],
                'Date': ['date', 'service date'],
                'Job': ['job', 'job #', 'job number'],
                'Cost_Code': ['cost code', 'cc', 'costcode'],
                'Hours': ['units', 'qty', 'quantity', 'hours'],
                'Rate': ['rate', 'unit rate'],
                'Amount': ['amount', 'total']
            }.items():
                for col in division_data.columns:
                    if isinstance(col, str) and any(pattern in col.lower() for pattern in patterns):
                        column_mapping[col] = target
                        break
            
            # Create export dataframe
            export_df = pd.DataFrame()
            for source, target in column_mapping.items():
                export_df[target] = division_data[source]
            
            # Make sure all required columns exist
            for col in ['Equipment_Number', 'Date', 'Job', 'Cost_Code', 'Hours', 'Rate', 'Amount']:
                if col not in export_df.columns:
                    export_df[col] = ""
            
            # Format date column
            if 'Date' in export_df.columns and not export_df['Date'].empty:
                export_df['Date'] = pd.to_datetime(export_df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Write CSV
            output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
            export_df.to_csv(output_path, index=False)
            
            division_total = pd.to_numeric(export_df['Amount'], errors='coerce').sum()
            logger.info(f"Generated {division} Import File: {output_path} with {len(export_df)} records - Total: ${division_total:,.2f}")
    
    return True

def main():
    """Main function to process PM allocations and generate deliverables"""
    # 1. Load the base RAGLE file
    base_df = load_base_file()
    if base_df is None:
        return False
    
    # 2. Find and load all PM allocation files
    pm_files = find_pm_allocation_files()
    pm_allocation_dfs = []
    
    for pm_file in pm_files:
        pm_df = load_pm_allocation_file(pm_file)
        if pm_df is not None:
            pm_allocation_dfs.append(pm_df)
    
    # 3. Merge PM allocations with base data
    merged_df = merge_pm_allocations(base_df, pm_allocation_dfs)
    
    # 4. Generate the required deliverables
    generate_deliverables(merged_df)
    
    return True

if __name__ == "__main__":
    main()