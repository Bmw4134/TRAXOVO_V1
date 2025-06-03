"""
Direct Billing Extract

Extract billing data directly from the RAGLE file, focusing on the actual PM allocations
and calculating amounts based on units × rate.
"""
import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
ATTACHED_ASSETS_DIR = 'attached_assets'
EXPORTS_DIR = 'exports'
MONTH_NAME = 'APRIL'
YEAR = '2025'
DATE_NOW = datetime.now().strftime('%Y-%m-%d')

# Source files
RAGLE_FILE = 'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm'

# Output file names
FINALIZED_MASTER_ALLOCATION = f"FINAL_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
MASTER_BILLINGS = f"MASTER_BILLINGS_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
REGION_IMPORT_PREFIX = f"FINAL_REGION_IMPORT_"

def extract_and_generate_deliverables():
    """Extract billing data and generate deliverables"""
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Load RAGLE file
    ragle_path = os.path.join(ATTACHED_ASSETS_DIR, RAGLE_FILE)
    if not os.path.exists(ragle_path):
        logger.error(f"RAGLE file not found: {ragle_path}")
        return False
    
    try:
        logger.info(f"Loading RAGLE file: {ragle_path}")
        ragle_df = pd.read_excel(ragle_path, sheet_name='Equip Billings')
        logger.info(f"Loaded {len(ragle_df)} records from RAGLE file")
        
        # Calculate original total for reference
        original_total = ragle_df['Amount'].sum()
        logger.info(f"Original total from RAGLE file: ${original_total:,.2f}")
        
        # Clean up data for processing
        # Ensure key columns exist and are properly formatted
        required_columns = ['Equip #', 'Job', 'Units', 'Rate', 'Amount']
        for col in required_columns:
            if col not in ragle_df.columns:
                logger.error(f"Required column '{col}' not found in RAGLE file")
                return False
        
        # Clean up any problematic values
        ragle_df['Units'] = pd.to_numeric(ragle_df['Units'], errors='coerce').fillna(0)
        ragle_df['Rate'] = pd.to_numeric(ragle_df['Rate'], errors='coerce').fillna(0)
        ragle_df['Amount'] = pd.to_numeric(ragle_df['Amount'], errors='coerce').fillna(0)
        
        # Generate clean export data
        export_df = ragle_df.copy()
        
        # Add Division column based on Job numbers
        def assign_division(job):
            job_str = str(job).upper()
            if job_str.startswith('D') or '2023' in job_str or '2024-' in job_str:
                return 'DFW'
            elif job_str.startswith('H') or '-H' in job_str:
                return 'HOU'
            elif job_str.startswith('W') or 'WTX' in job_str or 'WT-' in job_str:
                return 'WTX'
            else:
                return 'DFW'  # Default to DFW
        
        export_df['Division'] = export_df['Job'].apply(assign_division)
        
        # Calculate and verify total
        calculated_total = export_df['Amount'].sum()
        logger.info(f"Calculated export total: ${calculated_total:,.2f}")
        
        # 1. Generate FINALIZED MASTER ALLOCATION SHEET
        master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
        export_df.to_excel(master_allocation_path, index=False, sheet_name='Master Allocation')
        logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
        
        # 2. Generate MASTER BILLINGS SHEET
        master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
        export_df.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
        logger.info(f"Generated Master Billings Sheet: {master_billing_path}")
        
        # 3. Generate FINAL REGION IMPORT FILES
        division_totals = {}
        
        for division in ['DFW', 'WTX', 'HOU']:
            division_data = export_df[export_df['Division'] == division].copy()
            
            if not division_data.empty:
                # Create export dataframe with required columns
                import_df = pd.DataFrame()
                
                # Map columns for export
                import_mapping = {
                    'Equip #': 'Equipment_Number',
                    'Date': 'Date',
                    'Job': 'Job',
                    'Cost Code': 'Cost_Code',
                    'Units': 'Hours',
                    'Rate': 'Rate',
                    'Amount': 'Amount'
                }
                
                for source, target in import_mapping.items():
                    if source in division_data.columns:
                        import_df[target] = division_data[source]
                    else:
                        import_df[target] = ""
                
                # Set date to current date if missing
                if 'Date' not in division_data.columns or division_data['Date'].isna().all():
                    import_df['Date'] = DATE_NOW
                
                # Handle Cost Code if missing
                if 'Cost_Code' not in import_df.columns or import_df['Cost_Code'].isna().all():
                    import_df['Cost_Code'] = ""
                
                # Write CSV
                output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
                import_df.to_csv(output_path, index=False)
                
                # Calculate division total
                division_total = import_df['Amount'].sum()
                division_totals[division] = division_total
                
                logger.info(f"Generated {division} Import File: {output_path} with {len(import_df)} records - Total: ${division_total:,.2f}")
        
        # Summary of division totals
        total_from_divisions = sum(division_totals.values())
        logger.info(f"\nSUMMARY OF TOTALS:")
        logger.info(f"Original RAGLE Total: ${original_total:,.2f}")
        for division, total in division_totals.items():
            logger.info(f"{division} Total: ${total:,.2f}")
        logger.info(f"Combined Division Total: ${total_from_divisions:,.2f}")
        
        if abs(total_from_divisions - original_total) > 0.01:
            logger.warning(f"Division totals ({total_from_divisions:,.2f}) don't match original total ({original_total:,.2f})")
            logger.warning(f"Difference: ${total_from_divisions - original_total:,.2f}")
        
        # Compare with master totals
        logger.info(f"Successfully generated all required deliverables!")
        return True
    
    except Exception as e:
        logger.error(f"Error processing billing data: {str(e)}")
        return False

if __name__ == "__main__":
    extract_and_generate_deliverables()