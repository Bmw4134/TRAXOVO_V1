"""
Direct Billing Extract

Extract billing data directly from the RAGLE file, focusing on the actual PM allocations
and calculating amounts based on units × rate.
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

def extract_and_generate_deliverables():
    """Extract billing data and generate deliverables"""
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Direct path to the RAGLE file
    ragle_file = os.path.join(ATTACHED_ASSETS_DIR, "RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm")
    
    if not os.path.exists(ragle_file):
        logger.error(f"RAGLE file not found: {ragle_file}")
        return False
    
    # Load the data from the Equip Billings sheet
    try:
        logger.info(f"Loading data from {ragle_file}")
        billing_data = pd.read_excel(ragle_file, sheet_name="Equip Billings")
        logger.info(f"Loaded {len(billing_data)} records")
        
        # Check total calculated amount
        if 'Amount' in billing_data.columns:
            total_amount = billing_data['Amount'].sum()
            logger.info(f"Total amount: ${total_amount:,.2f}")
        
        # Standardize column names for processing
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
        
        billing_data.rename(columns={k: v for k, v in column_mapping.items() if k in billing_data.columns}, inplace=True)
        
        # Recalculate amount based on units × rate to ensure accuracy
        if 'units' in billing_data.columns and 'rate' in billing_data.columns:
            billing_data['calculated_amount'] = billing_data['units'] * billing_data['rate']
            calc_total = billing_data['calculated_amount'].sum()
            logger.info(f"Recalculated total: ${calc_total:,.2f}")
            
            # Compare with original amount
            if 'amount' in billing_data.columns:
                original_total = billing_data['amount'].sum()
                difference = abs(original_total - calc_total)
                logger.info(f"Original total: ${original_total:,.2f}, Difference: ${difference:,.2f}")
                
                # If significant difference, use calculated amount
                if difference > 1000:
                    logger.warning(f"Significant difference detected, using calculated amounts")
                    billing_data['amount'] = billing_data['calculated_amount']
            else:
                # If no amount column, use calculated
                billing_data['amount'] = billing_data['calculated_amount']
        
        # 1. Generate FINALIZED MASTER ALLOCATION SHEET
        master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
        billing_data.to_excel(master_allocation_path, index=False, sheet_name='Master Allocation')
        logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
        
        # 2. Generate MASTER BILLINGS SHEET
        master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
        billing_data.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
        logger.info(f"Generated Master Billings Sheet: {master_billing_path}")
        
        # 3. Generate FINAL REGION IMPORT FILES for DFW, WTX, HOU
        if 'division' in billing_data.columns:
            divisions = ['DFW', 'WTX', 'HOU']
            for division in divisions:
                division_data = billing_data[billing_data['division'] == division].copy()
                
                if not division_data.empty:
                    # Prepare export data
                    export_cols = ['equip_id', 'date', 'job', 'cost_code', 'units', 'rate', 'amount']
                    export_data = pd.DataFrame()
                    
                    for col in export_cols:
                        if col in division_data.columns:
                            export_data[col] = division_data[col]
                        else:
                            export_data[col] = ""
                    
                    # Rename columns for export format
                    export_data.columns = ['Equipment_Number', 'Date', 'Job', 'Cost_Code', 'Hours', 'Rate', 'Amount']
                    
                    # Format date column
                    if 'Date' in export_data.columns and not export_data['Date'].empty:
                        export_data['Date'] = pd.to_datetime(export_data['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                    
                    # Write to CSV
                    output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
                    export_data.to_csv(output_path, index=False)
                    
                    division_total = export_data['Amount'].sum()
                    logger.info(f"Generated {division} Import File: {output_path} with {len(export_data)} records - Total: ${division_total:,.2f}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing RAGLE file: {str(e)}")
        return False

if __name__ == "__main__":
    extract_and_generate_deliverables()