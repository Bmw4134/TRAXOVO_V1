"""
Process PM Allocations

This script directly generates the three required billing deliverables with duplicate handling:
1. FINALIZED MASTER ALLOCATION SHEET
2. MASTER BILLINGS SHEET 
3. FINAL REGION IMPORT FILES (DFW, WTX, HOU)
"""

import os
import pandas as pd
import glob
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
ATTACHED_ASSETS_DIR = 'attached_assets'
EXPORTS_DIR = 'exports'
DEFAULT_COST_CODE = '9000 100F'
MONTH_NAME = 'APRIL'
YEAR = '2025'
DIVISIONS = ['DFW', 'HOU', 'WTX', 'SELECT']

# Output file names
FINALIZED_MASTER_ALLOCATION = f"FINALIZED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
MASTER_BILLINGS = f"MASTER_EQUIP_BILLINGS_{MONTH_NAME}_{YEAR}.xlsx"
REGION_IMPORT_PREFIX = "FINAL_REGION_IMPORT_"

def find_pm_allocation_files():
    """Find PM allocation files with priority handling"""
    # Create a priority list of files based on naming patterns
    priority_patterns = [
        "*FINAL*REVISION*APRIL*2025*.xlsx",  # FINAL REVISIONS have highest priority
        "*ALLOCATIONS*APRIL*2025*CODED*.xlsx",  # CODED files have second priority
        "*ALLOCATIONS*APRIL*2025*.xlsx",  # Regular allocation files have third priority
        "*BILLINGS*APRIL*2025*.xlsm",  # Also look for billing workbooks
        "*EQ*BILLINGS*APRIL*2025*.xlsx",  # Also look for equipment billing workbooks
    ]
    
    file_candidates = []
    for pattern in priority_patterns:
        full_pattern = os.path.join(ATTACHED_ASSETS_DIR, pattern)
        matches = glob.glob(full_pattern)
        for match in matches:
            file_candidates.append({
                'path': match,
                'priority': priority_patterns.index(pattern),
                'mtime': os.path.getmtime(match)
            })
    
    # Sort by priority (lowest number first) and then by modification time (newest first)
    file_candidates.sort(key=lambda x: (x['priority'], -x['mtime']))
    
    # Select the best files for each PM/reviewer
    selected_files = {}
    reviewers = ["A.HARDIMO", "C.KOCMICK", "L. MORALES", "S. ALVAREZ", "TR-FINAL"]
    
    for file_info in file_candidates:
        file_path = file_info['path']
        filename = os.path.basename(file_path)
        
        # Check if this file belongs to a known reviewer
        for reviewer in reviewers:
            if reviewer in filename.upper():
                if reviewer not in selected_files:
                    selected_files[reviewer] = file_path
                    logger.info(f"Selected {filename} for reviewer {reviewer}")
                break
    
    # Also search for CSV files for each division
    division_files = {}
    for division in DIVISIONS:
        csv_pattern = os.path.join(ATTACHED_ASSETS_DIR, f"*{division}*APR*2025*.csv")
        csv_files = glob.glob(csv_pattern)
        if csv_files:
            # Sort by modification time (newest first) and take the most recent
            csv_files.sort(key=lambda x: -os.path.getmtime(x))
            division_files[division] = csv_files[0]
            logger.info(f"Selected {os.path.basename(csv_files[0])} for division {division}")
    
    # Return the selected files
    return list(selected_files.values()) + list(division_files.values())

def process_all_files():
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    start_time = datetime.now()
    
    logger.info(f"Starting PM allocation processing at {start_time}")
    
    # Find the best PM allocation files
    allocation_files = find_pm_allocation_files()
    logger.info(f"Found {len(allocation_files)} PM allocation files")
    
    # Track processed equipment to avoid duplicates
    processed_equipment = set()
    all_data = []
    
    for file_path in allocation_files:
        try:
            # Handle different file types
            if file_path.endswith('.xlsx'):
                # For Excel files
                df = pd.read_excel(file_path, sheet_name=0)
                logger.info(f"Loaded {len(df)} rows from {os.path.basename(file_path)}")
                
                # Identify columns
                equip_id_col = None
                for possible_col in ['equip id', 'equip_id', 'equipment id', 'equipment', 'equip.', 'equip #', 'equipment #']:
                    if possible_col in [col.lower() for col in df.columns]:
                        equip_id_col = next(col for col in df.columns if col.lower() == possible_col)
                        break
                
                if not equip_id_col:
                    logger.warning(f"Could not find equipment ID column in {file_path}")
                    continue
                    
                # Standardize column names
                column_mapping = {
                    equip_id_col: 'equip_id',
                    'description': 'description',
                    'desc': 'description',
                    'date': 'date',
                    'job': 'job',
                    'job #': 'job',
                    'cost code': 'cost_code',
                    'cost_code': 'cost_code',
                    'costcode': 'cost_code',
                    'units': 'units',
                    'hours': 'units',
                    'frequency': 'frequency',
                    'freq': 'frequency',
                    'rate': 'rate',
                    'amount': 'amount',
                    'total': 'amount',
                    'division': 'division'
                }
                
                renamed_cols = {}
                for old_col in df.columns:
                    if old_col.lower() in [c.lower() for c in column_mapping.keys()]:
                        new_col = next(column_mapping[c] for c in column_mapping.keys() if c.lower() == old_col.lower())
                        renamed_cols[old_col] = new_col
                
                df.rename(columns=renamed_cols, inplace=True)
                
                # Try to identify division from filename
                if 'division' not in df.columns:
                    for division in DIVISIONS:
                        if division in file_path.upper():
                            df['division'] = division
                            break
                
                # Filter out equipment that's already been processed (prioritize files loaded earlier)
                if 'equip_id' in df.columns:
                    equip_ids = set(df['equip_id'].dropna().astype(str))
                    new_equip_ids = equip_ids - processed_equipment
                    if len(new_equip_ids) < len(equip_ids):
                        logger.info(f"Skipping {len(equip_ids) - len(new_equip_ids)} duplicate equipment records")
                        df = df[df['equip_id'].astype(str).isin(new_equip_ids)]
                    
                    # Add to processed set
                    processed_equipment.update(new_equip_ids)
                
                all_data.append(df)
                
            elif file_path.endswith('.csv'):
                # For CSV files
                df = pd.read_csv(file_path)
                logger.info(f"Loaded {len(df)} rows from {os.path.basename(file_path)}")
                
                # Rename columns for CSV standard format
                column_mapping = {
                    'Equipment_Number': 'equip_id',
                    'Equipment Number': 'equip_id',
                    'Date': 'date',
                    'Job': 'job',
                    'Cost_Code': 'cost_code',
                    'Hours': 'units',
                    'Rate': 'rate',
                    'Amount': 'amount'
                }
                
                df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)
                
                # Try to identify division from filename
                if 'division' not in df.columns:
                    for division in DIVISIONS:
                        if division in file_path.upper():
                            df['division'] = division
                            break
                
                # Filter out equipment that's already been processed
                if 'equip_id' in df.columns:
                    equip_ids = set(df['equip_id'].dropna().astype(str))
                    new_equip_ids = equip_ids - processed_equipment
                    if len(new_equip_ids) < len(equip_ids):
                        logger.info(f"Skipping {len(equip_ids) - len(new_equip_ids)} duplicate equipment records")
                        df = df[df['equip_id'].astype(str).isin(new_equip_ids)]
                    
                    # Add to processed set
                    processed_equipment.update(new_equip_ids)
                
                all_data.append(df)
        
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            continue
    
    if not all_data:
        logger.error("No data could be extracted from any files")
        return
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    logger.info(f"Combined data has {len(combined_data)} rows and {len(combined_data.columns)} columns")
    
    # Fill in missing values and standardize
    if 'cost_code' in combined_data.columns:
        combined_data['cost_code'] = combined_data['cost_code'].fillna(DEFAULT_COST_CODE)
        combined_data.loc[combined_data['cost_code'].astype(str).str.contains('NEEDED', na=False, case=False), 'cost_code'] = DEFAULT_COST_CODE
        combined_data.loc[combined_data['cost_code'] == '', 'cost_code'] = DEFAULT_COST_CODE
    
    # 1. Generate FINALIZED MASTER ALLOCATION SHEET
    master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
    combined_data.to_excel(master_allocation_path, index=False, sheet_name='Master Allocation')
    logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
    
    # 2. Generate MASTER BILLINGS SHEET
    # Make sure required columns exist
    required_columns = ['equip_id', 'date', 'job', 'cost_code', 'units', 'rate', 'amount']
    for col in required_columns:
        if col not in combined_data.columns:
            if col == 'rate':
                combined_data[col] = 0.0
            elif col == 'amount':
                if 'units' in combined_data.columns and 'rate' in combined_data.columns:
                    combined_data[col] = combined_data['units'] * combined_data['rate'] 
                else:
                    combined_data[col] = 0.0
            elif col == 'units':
                combined_data[col] = 0.0
            else:
                combined_data[col] = ''
    
    # Write master billing sheet
    master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
    combined_data.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
    logger.info(f"Generated Master Billings Sheet: {master_billing_path}")
    
    # 3. Generate FINAL REGION IMPORT FILES for DFW, WTX, HOU
    divisions_to_export = ['DFW', 'WTX', 'HOU']
    
    for division in divisions_to_export:
        # Filter data for this division
        if 'division' in combined_data.columns:
            division_data = combined_data[combined_data['division'] == division].copy()
        else:
            # If no division column, try to infer from other data
            division_data = pd.DataFrame(columns=required_columns)
        
        if not division_data.empty:
            # Prepare export data
            export_cols = ['equip_id', 'date', 'job', 'cost_code', 'units', 'rate', 'amount']
            export_data = division_data[export_cols].copy()
            export_data.columns = ['Equipment_Number', 'Date', 'Job', 'Cost_Code', 'Hours', 'Rate', 'Amount']
            
            # Format date as YYYY-MM-DD
            if 'Date' in export_data.columns:
                export_data['Date'] = pd.to_datetime(export_data['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Create output CSV
            output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
            export_data.to_csv(output_path, index=False)
            logger.info(f"Generated {division} Import File: {output_path} with {len(export_data)} records")
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    logger.info(f"Processing completed in {processing_time:.2f} seconds")
    logger.info(f"Generated all three required deliverables in {EXPORTS_DIR}")
    
    return {
        'status': 'success',
        'record_count': len(combined_data),
        'processing_time': processing_time,
        'finalized_master_allocation': master_allocation_path,
        'master_billings': master_billing_path,
        'region_imports': [os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv") for division in divisions_to_export]
    }

if __name__ == "__main__":
    process_all_files()