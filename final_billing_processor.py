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
FINALIZED_MASTER_ALLOCATION = f"FINALIZED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
MASTER_BILLINGS = f"MASTER_BILLINGS_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
REGION_IMPORT_PREFIX = f"FINAL_REGION_IMPORT_"

def process_and_generate_deliverables():
    """Process billing data and generate all required deliverables"""
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
        
        # Try to load the underlying data table directly
        try:
            # Some Excel files have named tables that can be extracted directly
            xls = pd.ExcelFile(ragle_path)
            sheet = xls.book.worksheets[0]
            
            logger.info(f"Checking for data tables in {RAGLE_FILE}")
            if hasattr(sheet, 'tables') and sheet.tables:
                logger.info(f"Found {len(sheet.tables)} data tables in {RAGLE_FILE}")
                for table_name, table in sheet.tables.items():
                    logger.info(f"Found table: {table_name}")
                    # Try to extract table data directly
                    table_range = table.ref
                    logger.info(f"Table range: {table_range}")
        except Exception as e:
            logger.warning(f"Could not extract tables directly: {str(e)}")
        
        logger.info(f"Loaded {len(ragle_df)} records from RAGLE file")
        
        # Calculate original total for reference
        original_total = ragle_df['Amount'].sum()
        logger.info(f"Original total from RAGLE file: ${original_total:,.2f}")
        
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
                # Extract region code if in job code format "NNN-RDDNNN"
                parts = job_str.split('-')
                if len(parts) > 1 and len(parts[1]) >= 1:
                    region_code = parts[1][0]
                    if region_code == 'D':
                        return 'DFW'
                    elif region_code == 'H':
                        return 'HOU'
                    elif region_code == 'W':
                        return 'WTX'
                return 'DFW'  # Default to DFW
        
        export_df['Division'] = export_df['Job'].apply(assign_division)
        
        # Get division totals before any modifications
        dfw_total = export_df[export_df['Division'] == 'DFW']['Amount'].sum()
        hou_total = export_df[export_df['Division'] == 'HOU']['Amount'].sum()
        wtx_total = export_df[export_df['Division'] == 'WTX']['Amount'].sum()
        
        logger.info(f"Division totals from RAGLE file:")
        logger.info(f"DFW: ${dfw_total:,.2f}")
        logger.info(f"HOU: ${hou_total:,.2f}")
        logger.info(f"WTX: ${wtx_total:,.2f}")
        logger.info(f"Combined: ${dfw_total + hou_total + wtx_total:,.2f}")
        
        # 1. Generate FINALIZED MASTER ALLOCATION SHEET
        master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
        export_df.to_excel(master_allocation_path, index=False, sheet_name='Master Allocation')
        logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
        
        # 2. Generate MASTER BILLINGS SHEET
        master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
        export_df.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
        logger.info(f"Generated Master Billings Sheet: {master_billing_path}")
        
        # 3. Generate FINAL REGION IMPORT FILES
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
                
                # Format date field
                if 'Date' in import_df.columns:
                    # Check if all dates are missing
                    if import_df['Date'].isna().all() or (import_df['Date'] == '').all():
                        import_df['Date'] = DATE_NOW
                    else:
                        # Format existing dates
                        import_df['Date'] = pd.to_datetime(import_df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                else:
                    import_df['Date'] = DATE_NOW
                
                # Write CSV
                output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
                import_df.to_csv(output_path, index=False)
                
                # Log division total
                division_total = import_df['Amount'].sum()
                logger.info(f"Generated {division} Import File: {output_path} with {len(import_df)} records - Total: ${division_total:,.2f}")
        
        # Final check
        logger.info(f"Successfully generated all required deliverables with original total: ${original_total:,.2f}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing billing data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    process_and_generate_deliverables()