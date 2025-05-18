"""
Process PM Allocations

This script integrates the PM allocation revisions into the base file to generate
the final required deliverables with the correct updated total.
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

def find_base_file():
    """Find the base allocation file (should be the working sheet)"""
    patterns = [
        "EQ MONTHLY BILLINGS WORKING SPREADSHEET*APRIL*2025*.xlsx",
        "EQMO.*BILLING*ALLOCATIONS*APRIL*2025*.xlsx"
    ]
    
    for pattern in patterns:
        files = glob.glob(os.path.join(ATTACHED_ASSETS_DIR, pattern))
        if files:
            # Sort by file timestamp (most recent last)
            files.sort(key=lambda x: os.path.getmtime(x))
            # Get the oldest file as the base
            return files[0]
    
    return None

def find_pm_revision_files():
    """Find all PM allocation revision files"""
    pattern = "*EQMO.*BILLING*ALLOCATIONS*APRIL*2025*.xlsx"
    revision_files = []
    
    # Get all potential files
    all_files = glob.glob(os.path.join(ATTACHED_ASSETS_DIR, pattern))
    logger.info(f"Found {len(all_files)} potential PM allocation files")
    
    # Identify specific PM revision files (files with PM names in them)
    pm_keywords = [
        "HARDIMO", "KOCMICK", "MORALES", "ALVAREZ", "allocated", "TR-FINAL", "REVISIONS"
    ]
    
    for file_path in all_files:
        filename = os.path.basename(file_path)
        if any(keyword in filename.upper() for keyword in pm_keywords):
            revision_files.append(file_path)
            logger.info(f"Identified PM revision file: {filename}")
    
    logger.info(f"Found {len(revision_files)} PM revision files")
    return revision_files

def load_workbook_sheet(file_path, try_sheets=None):
    """Load a specific sheet from an Excel file, trying multiple sheet names"""
    if not try_sheets:
        try_sheets = ["Sheet1", "Sheet 1", "Data", "Allocations", "Billing"]
    
    # First, get all sheet names
    try:
        xlsx = pd.ExcelFile(file_path)
        sheet_names = xlsx.sheet_names
        
        # Try to find the data sheet
        # First try to find sheets with 'allocation' in the name
        allocation_sheets = [sheet for sheet in sheet_names if 'allocation' in sheet.lower()]
        if allocation_sheets:
            try_sheets = allocation_sheets + try_sheets
        
        # Or sheets that might contain 'PM', 'EQMO', or 'billing'
        billing_sheets = [sheet for sheet in sheet_names if any(keyword in sheet.lower() for keyword in ['pm', 'eqmo', 'billing'])]
        if billing_sheets:
            try_sheets = billing_sheets + try_sheets
        
        # Try each sheet until we find one with data
        for sheet_name in try_sheets:
            if sheet_name in sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                if not df.empty:
                    logger.info(f"Loaded sheet '{sheet_name}' from {os.path.basename(file_path)}")
                    return df
        
        # If none of the specific sheets work, try all sheets
        for sheet_name in sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            if not df.empty:
                logger.info(f"Loaded sheet '{sheet_name}' from {os.path.basename(file_path)}")
                return df
        
        logger.warning(f"No data found in any sheet for {os.path.basename(file_path)}")
        return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error loading {os.path.basename(file_path)}: {str(e)}")
        return pd.DataFrame()

def identify_key_columns(df):
    """Identify the key columns in a dataframe"""
    # Map of column types to potential column names
    column_types = {
        'equip_id': ['equip #', 'equip id', 'equipment', 'equipment id', 'eq #', 'eq id'],
        'job': ['job', 'job #', 'job number', 'job id'],
        'date': ['date', 'service date'],
        'units': ['units', 'qty', 'quantity', 'hours'],
        'rate': ['rate', 'unit rate', 'billing rate'],
        'amount': ['amount', 'total', 'billing amount'],
        'division': ['division', 'div', 'region'],
        'cost_code': ['cost code', 'cc', 'costcode'],
        'description': ['description', 'equipment description', 'desc']
    }
    
    column_map = {}
    for column_type, potential_names in column_types.items():
        for col in df.columns:
            col_str = str(col).lower()
            if any(name in col_str for name in potential_names):
                column_map[column_type] = col
                break
    
    return column_map

def standardize_dataframe(df, column_map):
    """Standardize a dataframe based on the provided column map"""
    standardized_df = pd.DataFrame()
    
    # Copy identified columns
    for column_type, original_col in column_map.items():
        if original_col in df.columns:
            standardized_df[column_type] = df[original_col]
    
    return standardized_df

def calculate_amount(df):
    """Calculate the amount column if missing"""
    if 'amount' not in df.columns and 'units' in df.columns and 'rate' in df.columns:
        # Convert to numeric
        df['units'] = pd.to_numeric(df['units'], errors='coerce').fillna(0)
        df['rate'] = pd.to_numeric(df['rate'], errors='coerce').fillna(0)
        
        # Calculate amount
        df['amount'] = df['units'] * df['rate']
    
    return df

def generate_division_imports(df):
    """Generate division import files"""
    if 'division' not in df.columns:
        logger.warning("Division column not found, cannot generate division imports")
        return
    
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Process each division
    for division in ['DFW', 'WTX', 'HOU']:
        division_data = df[df['division'] == division].copy()
        
        if not division_data.empty:
            # Create export dataframe
            export_df = pd.DataFrame()
            
            # Map columns for export
            column_mapping = {
                'equip_id': 'Equipment_Number',
                'date': 'Date',
                'job': 'Job',
                'cost_code': 'Cost_Code',
                'units': 'Hours',
                'rate': 'Rate',
                'amount': 'Amount'
            }
            
            for source_col, target_col in column_mapping.items():
                if source_col in division_data.columns:
                    export_df[target_col] = division_data[source_col]
                else:
                    export_df[target_col] = ""
            
            # Format date column
            if 'Date' in export_df.columns and not export_df['Date'].empty:
                export_df['Date'] = pd.to_datetime(export_df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Write CSV
            output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
            export_df.to_csv(output_path, index=False)
            
            division_total = 0
            if 'Amount' in export_df.columns:
                division_total = pd.to_numeric(export_df['Amount'], errors='coerce').sum()
            
            logger.info(f"Generated {division} Import File: {output_path} with {len(export_df)} records - Total: ${division_total:,.2f}")

def process_allocations():
    """Process the base file and PM revisions to generate deliverables"""
    base_file = find_base_file()
    
    if not base_file:
        logger.error("Base allocation file not found!")
        return False
    
    # Load base file
    base_df = load_workbook_sheet(base_file)
    
    if base_df.empty:
        logger.error(f"Could not load data from base file: {base_file}")
        return False
    
    # Get column mappings from base file
    base_column_map = identify_key_columns(base_df)
    logger.info(f"Base file column mapping: {base_column_map}")
    
    # Standardize base data
    standard_base_df = standardize_dataframe(base_df, base_column_map)
    standard_base_df = calculate_amount(standard_base_df)
    
    # Calculate base total
    original_total = 0
    if 'amount' in standard_base_df.columns:
        original_total = pd.to_numeric(standard_base_df['amount'], errors='coerce').sum()
        logger.info(f"Original base file total: ${original_total:,.2f}")
    
    # Find PM revision files
    revision_files = find_pm_revision_files()
    
    # Create master dataframe to collect all PM revisions
    # Start with the base standardized dataframe
    master_df = standard_base_df.copy()
    
    # Process each revision file
    for revision_file in revision_files:
        revision_df = load_workbook_sheet(revision_file)
        
        if revision_df.empty:
            logger.warning(f"No data found in revision file: {os.path.basename(revision_file)}")
            continue
        
        # Get column mappings from revision file
        revision_column_map = identify_key_columns(revision_df)
        logger.info(f"Revision file {os.path.basename(revision_file)} column mapping: {revision_column_map}")
        
        # Standardize revision data
        standard_revision_df = standardize_dataframe(revision_df, revision_column_map)
        standard_revision_df = calculate_amount(standard_revision_df)
        
        # Calculate revision total
        revision_total = 0
        if 'amount' in standard_revision_df.columns:
            revision_total = pd.to_numeric(standard_revision_df['amount'], errors='coerce').sum()
            logger.info(f"Revision file {os.path.basename(revision_file)} total: ${revision_total:,.2f}")
        
        # Apply this revision to the master dataframe
        # First, identify equipment IDs in the revision
        if 'equip_id' in standard_revision_df.columns:
            equip_ids = standard_revision_df['equip_id'].unique()
            
            # For each equipment ID, update or add records in the master dataframe
            for eq_id in equip_ids:
                if pd.isna(eq_id) or eq_id == "":
                    continue
                
                # Get revision records for this equipment
                eq_revisions = standard_revision_df[standard_revision_df['equip_id'] == eq_id]
                
                # Replace or add these records to the master dataframe
                if 'equip_id' in master_df.columns:
                    # Remove existing records for this equipment
                    master_df = master_df[master_df['equip_id'] != eq_id]
                
                # Append the revision records
                master_df = pd.concat([master_df, eq_revisions], ignore_index=True)
    
    # Calculate the final total after all revisions
    final_total = 0
    if 'amount' in master_df.columns:
        final_total = pd.to_numeric(master_df['amount'], errors='coerce').sum()
        logger.info(f"Final total after all revisions: ${final_total:,.2f}")
        logger.info(f"Changed amount: ${final_total - original_total:,.2f}")
    
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Generate the three required deliverables
    
    # 1. FINALIZED MASTER ALLOCATION SHEET
    # Use the master_df with standardized columns
    # Convert to Excel-friendly format
    excel_output = master_df.copy()
    
    # Rename columns to more user-friendly names
    column_renames = {
        'equip_id': 'Equip #',
        'description': 'Equipment Description',
        'date': 'Date',
        'job': 'Job',
        'cost_code': 'Cost Code',
        'units': 'Units',
        'rate': 'Rate',
        'amount': 'Amount',
        'division': 'Division'
    }
    excel_output.rename(columns=column_renames, inplace=True)
    
    # Write to Excel
    master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
    excel_output.to_excel(master_allocation_path, index=False, sheet_name='Master Allocation')
    logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
    
    # 2. MASTER BILLINGS SHEET (Same content, different name)
    master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
    excel_output.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
    logger.info(f"Generated Master Billings Sheet: {master_billing_path}")
    
    # 3. FINAL REGION IMPORT FILES
    generate_division_imports(master_df)
    
    return True

if __name__ == "__main__":
    process_allocations()