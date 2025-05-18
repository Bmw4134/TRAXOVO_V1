"""
Final Billing Processor with correct totals

This script directly extracts data from the RAGLE EQ BILLINGS file
and generates the three required deliverables:
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

# Primary source file (contains correct billing amounts)
RAGLE_FILE = os.path.join(ATTACHED_ASSETS_DIR, "RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm")

def process_and_generate_deliverables():
    """Process billing data and generate all required deliverables"""
    start_time = datetime.now()
    logger.info(f"Starting billing processor at {start_time}")
    
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # First, try to load data from the RAGLE file (primary source)
    ragle_data = None
    try:
        logger.info(f"Loading primary data from RAGLE file: {RAGLE_FILE}")
        ragle_data = pd.read_excel(RAGLE_FILE, sheet_name="Equip Billings")
        total_amount = ragle_data['Amount'].sum()
        logger.info(f"Loaded {len(ragle_data)} records with total amount: ${total_amount:,.2f}")
        
        # Rename columns to standardized format
        column_mapping = {
            'Division': 'division',
            'Equip #': 'equip_id',
            'Equipment Description': 'description',
            'Date': 'date',
            'Job': 'job',
            'Phase': 'phase',
            'Cost Code': 'cost_code',
            'Cost Class': 'cost_class',
            'Units': 'units',
            'Frequency': 'frequency',
            'Rate': 'rate',
            'Amount': 'amount'
        }
        
        ragle_data.rename(columns={k: v for k, v in column_mapping.items() if k in ragle_data.columns}, inplace=True)
        
    except Exception as e:
        logger.error(f"Error loading RAGLE file: {str(e)}")
        ragle_data = None
    
    # If we couldn't load the RAGLE file, try to load allocation sheets
    final_data = ragle_data
    if final_data is None or final_data.empty:
        logger.warning("RAGLE file data unavailable, falling back to allocation files")
        
        # Try to find allocation files
        allocation_files = []
        priority_patterns = [
            "*FINAL*REVISION*APRIL*2025*.xlsx",  # FINAL REVISIONS have highest priority
            "*ALLOCATIONS*APRIL*2025*CODED*.xlsx",  # CODED files have second priority
            "*ALLOCATIONS*APRIL*2025*.xlsx",  # Regular allocation files have third priority
        ]
        
        for pattern in priority_patterns:
            full_pattern = os.path.join(ATTACHED_ASSETS_DIR, pattern)
            allocation_files.extend(glob.glob(full_pattern))
        
        # Also look for CSV files for each division
        for division in DIVISIONS:
            csv_pattern = os.path.join(ATTACHED_ASSETS_DIR, f"*{division}*APR*2025*.csv")
            allocation_files.extend(glob.glob(csv_pattern))
        
        if not allocation_files:
            logger.error("No allocation files found")
            return False
        
        logger.info(f"Found {len(allocation_files)} allocation files")
        all_data = []
        
        for file_path in allocation_files:
            try:
                if file_path.endswith('.xlsx'):
                    df = pd.read_excel(file_path, sheet_name=0)
                elif file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    continue
                
                logger.info(f"Loaded {len(df)} rows from {os.path.basename(file_path)}")
                all_data.append(df)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                continue
        
        if not all_data:
            logger.error("No data could be extracted from allocation files")
            return False
        
        # Combine all allocation data
        final_data = pd.concat(all_data, ignore_index=True)
        
        # Standardize column names
        column_mapping = {
            'equip id': 'equip_id',
            'equip.': 'equip_id',
            'equipment': 'equip_id',
            'equipment_number': 'equip_id',
            'desc': 'description',
            'equipment_description': 'description',
            'cost code': 'cost_code',
            'costcode': 'cost_code',
            'frequency': 'frequency',
            'freq': 'frequency',
            'amt': 'amount',
            'total': 'amount'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in final_data.columns and new_col not in final_data.columns:
                final_data.rename(columns={old_col: new_col}, inplace=True)
    
    # Apply default cost codes where missing
    if 'cost_code' in final_data.columns:
        final_data['cost_code'] = final_data['cost_code'].fillna(DEFAULT_COST_CODE)
        mask = final_data['cost_code'].astype(str).str.contains('NEEDED', na=False, case=False)
        final_data.loc[mask, 'cost_code'] = DEFAULT_COST_CODE
    
    # Make sure required columns exist
    required_columns = ['equip_id', 'date', 'job', 'cost_code', 'units', 'rate', 'amount', 'division']
    for col in required_columns:
        if col not in final_data.columns:
            if col == 'division':
                # Try to infer division from existing data
                if 'equip_id' in final_data.columns:
                    # Start with a default division (DFW as most common)
                    final_data[col] = 'DFW'
                    
                    # Apply specific division rules based on equipment ID patterns
                    # (These are example patterns - adjust as needed for your data)
                    mask_hou = final_data['equip_id'].astype(str).str.startswith(('H', '2'))
                    mask_wtx = final_data['equip_id'].astype(str).str.startswith(('W', '3'))
                    mask_select = final_data['equip_id'].astype(str).str.startswith(('S', '4'))
                    
                    final_data.loc[mask_hou, 'division'] = 'HOU'
                    final_data.loc[mask_wtx, 'division'] = 'WTX'
                    final_data.loc[mask_select, 'division'] = 'SELECT'
                else:
                    final_data[col] = 'DFW'  # Default division
            elif col in ['rate', 'units', 'amount']:
                final_data[col] = 0.0
            else:
                final_data[col] = ''
    
    # Ensure numeric columns are numeric
    numeric_cols = ['units', 'rate', 'amount']
    for col in numeric_cols:
        if col in final_data.columns:
            final_data[col] = pd.to_numeric(final_data[col], errors='coerce').fillna(0)
    
    # 1. Generate FINALIZED MASTER ALLOCATION SHEET
    master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
    final_data.to_excel(master_allocation_path, index=False, sheet_name='Master Allocation')
    logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
    
    # 2. Generate MASTER BILLINGS SHEET  
    master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
    final_data.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
    total_amount = final_data['amount'].sum()
    logger.info(f"Generated Master Billings Sheet: {master_billing_path} - Total: ${total_amount:,.2f}")
    
    # 3. Generate FINAL REGION IMPORT FILES for DFW, WTX, HOU
    divisions_to_export = ['DFW', 'WTX', 'HOU']
    division_files = {}
    
    for division in divisions_to_export:
        # Filter data for this division
        division_data = final_data[final_data['division'] == division].copy()
        
        if not division_data.empty:
            # Prepare export data
            export_cols = ['equip_id', 'date', 'job', 'cost_code', 'units', 'rate', 'amount']
            export_data = division_data[export_cols].copy()
            export_data.columns = ['Equipment_Number', 'Date', 'Job', 'Cost_Code', 'Hours', 'Rate', 'Amount']
            
            # Format date as YYYY-MM-DD if not already
            if 'Date' in export_data.columns:
                export_data['Date'] = pd.to_datetime(export_data['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Create output CSV
            output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
            export_data.to_csv(output_path, index=False)
            division_total = export_data['Amount'].sum()
            logger.info(f"Generated {division} Import File: {output_path} with {len(export_data)} records - Total: ${division_total:,.2f}")
            
            division_files[division] = {
                'path': output_path, 
                'count': len(export_data),
                'total': division_total
            }
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    logger.info(f"Processing completed in {processing_time:.2f} seconds")
    logger.info(f"Total billing amount: ${total_amount:,.2f}")
    
    return {
        'status': 'success',
        'record_count': len(final_data),
        'total_amount': total_amount,
        'processing_time': processing_time,
        'finalized_master_allocation': master_allocation_path,
        'master_billings': master_billing_path,
        'region_imports': division_files
    }

if __name__ == "__main__":
    process_and_generate_deliverables()