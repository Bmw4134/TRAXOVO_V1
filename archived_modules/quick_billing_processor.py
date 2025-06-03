"""
Quick Billing Processor

This script quickly generates all required billing deliverables from the Ragle reviewed file,
ensuring the correct total amount and divisions are preserved.
"""
import os
import pandas as pd
import logging

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

# Source file (JG reviewed Ragle file)
RAGLE_FILE = "RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm"

def quick_process():
    """Process the Ragle file and generate deliverables quickly"""
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Load the Ragle file
    ragle_path = os.path.join(ATTACHED_ASSETS_DIR, RAGLE_FILE)
    if not os.path.exists(ragle_path):
        logger.error(f"Ragle file not found: {ragle_path}")
        return False
    
    try:
        # Read the Equip Billings sheet
        logger.info(f"Loading data from {ragle_path}")
        billing_data = pd.read_excel(ragle_path, sheet_name="Equip Billings")
        logger.info(f"Loaded {len(billing_data)} records")
        
        # Calculate total amount
        total_amount = billing_data['Amount'].sum()
        logger.info(f"Total billing amount: ${total_amount:,.2f}")
        
        # 1. Generate FINALIZED MASTER ALLOCATION SHEET
        master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
        billing_data.to_excel(master_allocation_path, index=False, sheet_name='Master Allocation')
        logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
        
        # 2. Generate MASTER BILLINGS SHEET (same content, different filename)
        master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
        billing_data.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
        logger.info(f"Generated Master Billings Sheet: {master_billing_path}")
        
        # 3. Generate FINAL REGION IMPORT FILES
        for division in ['DFW', 'WTX', 'HOU']:
            # For WTX division, look for both 'WTX' and 'WT' in the Division column
            if division == 'WTX':
                division_data = billing_data[billing_data['Division'].isin(['WTX', 'WT'])].copy()
            else:
                division_data = billing_data[billing_data['Division'] == division].copy()
            
            if not division_data.empty:
                # Create standardized export columns
                export_df = pd.DataFrame()
                
                column_mapping = {
                    'Equip #': 'Equipment_Number',
                    'Date': 'Date',
                    'Job': 'Job',
                    'Cost Code': 'Cost_Code',
                    'Units': 'Hours',
                    'Rate': 'Rate',
                    'Amount': 'Amount'
                }
                
                for source, target in column_mapping.items():
                    if source in division_data.columns:
                        export_df[target] = division_data[source]
                    else:
                        export_df[target] = ""
                
                # Format date column
                if 'Date' in export_df.columns and not export_df['Date'].empty:
                    export_df['Date'] = pd.to_datetime(export_df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                
                # Write CSV
                output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
                export_df.to_csv(output_path, index=False)
                
                division_total = export_df['Amount'].sum()
                logger.info(f"Generated {division} Import File: {output_path} with {len(export_df)} records - Total: ${division_total:,.2f}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing Ragle file: {str(e)}")
        return False

if __name__ == "__main__":
    quick_process()