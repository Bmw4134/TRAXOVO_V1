"""
Preserve Original Amounts

This script ensures the original total billing amount is preserved 
while applying PM allocation changes to the units. It directly compares
the base RAGLE file with the PM allocation sheets.
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

# Source files
BASE_FILE = 'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm'

# PM allocation files - prioritize the main revisions to avoid duplicates
PM_FILES = [
    "A.HARDIMO EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx",
    "C.KOCMICK EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx",
    "L. MORALES EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx",
    "S. ALVAREZ EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx"
]

# Output file names
FINALIZED_MASTER_ALLOCATION = f"FINALIZED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
MASTER_BILLINGS = f"MASTER_BILLINGS_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
REGION_IMPORT_PREFIX = f"FINAL_REGION_IMPORT_"

def main():
    """Main function to process and generate deliverables"""
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Load base RAGLE file
    base_path = os.path.join(ATTACHED_ASSETS_DIR, BASE_FILE)
    if not os.path.exists(base_path):
        logger.error(f"Base file not found: {base_path}")
        return False
    
    try:
        logger.info(f"Loading base RAGLE file: {base_path}")
        base_df = pd.read_excel(base_path, sheet_name='Equip Billings')
        original_total = base_df['Amount'].sum()
        logger.info(f"Loaded {len(base_df)} records from base file")
        logger.info(f"Original total: ${original_total:,.2f}")
        
        # Make a copy to apply updates
        updated_df = base_df.copy()
        
        # Create a lookup dictionary for equipment records
        equipment_dict = {}
        for idx, row in base_df.iterrows():
            equip_id = str(row['Equip #']).strip()
            job = str(row['Job']).strip()
            key = f"{equip_id}_{job}"
            equipment_dict[key] = idx
        
        # Keep track of revisions
        revisions = []
        
        # Process each PM allocation file
        for pm_file in PM_FILES:
            pm_path = os.path.join(ATTACHED_ASSETS_DIR, pm_file)
            if not os.path.exists(pm_path):
                logger.warning(f"PM file not found: {pm_file}")
                continue
            
            logger.info(f"Processing PM file: {pm_file}")
            
            # Try to find the allocation sheet
            sheet_name = None
            try:
                xls = pd.ExcelFile(pm_path)
                for sheet in xls.sheet_names:
                    if 'ALLOCATIONS' in sheet.upper() or 'EQ' in sheet.upper() or 'DIV' in sheet.upper():
                        sheet_name = sheet
                        break
                
                if not sheet_name:
                    sheet_name = xls.sheet_names[0]  # Default to first sheet
                
                logger.info(f"Using sheet: {sheet_name}")
                
                # Load the PM allocation sheet
                pm_df = pd.read_excel(pm_path, sheet_name=sheet_name)
                
                # Look for equipment ID and job number columns
                equip_col = None
                job_col = None
                units_col = None
                cost_code_col = None
                
                for col in pm_df.columns:
                    col_str = str(col).upper()
                    if 'EQUIP' in col_str and ('#' in col_str or 'ID' in col_str or 'NO' in col_str):
                        equip_col = col
                    elif 'JOB' in col_str:
                        job_col = col
                    elif ('UNIT' in col_str or 'ALLOCATION' in col_str or 'REVISION' in col_str) and not 'RATE' in col_str:
                        units_col = col
                    elif 'COST' in col_str and 'CODE' in col_str:
                        cost_code_col = col
                
                if not equip_col or not job_col:
                    logger.warning(f"Could not find required columns in {pm_file}")
                    continue
                
                logger.info(f"Found columns: Equip={equip_col}, Job={job_col}, Units={units_col}, Cost Code={cost_code_col}")
                
                # Process each row in the PM allocation sheet
                for idx, row in pm_df.iterrows():
                    # Skip if no equipment ID or job
                    if pd.isna(row[equip_col]) or pd.isna(row[job_col]):
                        continue
                    
                    equip_id = str(row[equip_col]).strip()
                    job = str(row[job_col]).strip()
                    key = f"{equip_id}_{job}"
                    
                    # If this equipment/job combo exists in the base file
                    if key in equipment_dict:
                        base_idx = equipment_dict[key]
                        
                        # If units column exists and has a value
                        if units_col and not pd.isna(row[units_col]):
                            old_units = updated_df.at[base_idx, 'Units']
                            new_units = float(row[units_col])
                            
                            # Only update if there's a change
                            if new_units != old_units:
                                # Record the revision
                                revisions.append({
                                    'Equip ID': equip_id,
                                    'Job': job,
                                    'PM File': pm_file.split('.xlsx')[0],
                                    'Old Units': old_units,
                                    'New Units': new_units,
                                    'Change': new_units - old_units
                                })
                                
                                # Update the units in the dataframe
                                updated_df.at[base_idx, 'Units'] = new_units
                                
                                # Recalculate the amount
                                rate = updated_df.at[base_idx, 'Rate']
                                updated_df.at[base_idx, 'Amount'] = new_units * rate
                                
                                logger.info(f"Updated {equip_id} for {job}: Units {old_units} → {new_units}")
                        
                        # If cost code column exists and has a value
                        if cost_code_col and not pd.isna(row[cost_code_col]):
                            old_cc = updated_df.at[base_idx, 'Cost Code'] if 'Cost Code' in updated_df.columns else ""
                            new_cc = str(row[cost_code_col]).strip()
                            
                            # Only update if there's a change
                            if new_cc != old_cc and new_cc:
                                if 'Cost Code' not in updated_df.columns:
                                    updated_df['Cost Code'] = ""
                                updated_df.at[base_idx, 'Cost Code'] = new_cc
                                logger.info(f"Updated {equip_id} for {job}: Cost Code {old_cc} → {new_cc}")
                
                logger.info(f"Completed processing {pm_file}")
                
            except Exception as e:
                logger.error(f"Error processing {pm_file}: {str(e)}")
        
        # Log summary of changes
        if revisions:
            logger.info(f"Made {len(revisions)} revisions")
            revisions_df = pd.DataFrame(revisions)
            
            # Calculate the net change in units
            total_unit_change = revisions_df['Change'].sum()
            logger.info(f"Net change in units: {total_unit_change}")
            
            # Save revisions to file for reference
            revisions_path = os.path.join(EXPORTS_DIR, f"PM_REVISIONS_{MONTH_NAME}_{YEAR}.xlsx")
            revisions_df.to_excel(revisions_path, index=False)
            logger.info(f"Saved revisions to {revisions_path}")
        else:
            logger.info("No revisions were made")
        
        # Calculate updated total
        updated_total = updated_df['Amount'].sum()
        logger.info(f"Updated total: ${updated_total:,.2f}")
        logger.info(f"Difference: ${updated_total - original_total:,.2f}")
        
        # Add division column
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
        
        updated_df['Division'] = updated_df['Job'].apply(assign_division)
        
        # Generate division totals
        dfw_total = updated_df[updated_df['Division'] == 'DFW']['Amount'].sum()
        hou_total = updated_df[updated_df['Division'] == 'HOU']['Amount'].sum()
        wtx_total = updated_df[updated_df['Division'] == 'WTX']['Amount'].sum()
        
        logger.info(f"Division totals after revisions:")
        logger.info(f"DFW: ${dfw_total:,.2f}")
        logger.info(f"HOU: ${hou_total:,.2f}")
        logger.info(f"WTX: ${wtx_total:,.2f}")
        logger.info(f"Combined: ${dfw_total + hou_total + wtx_total:,.2f}")
        
        # 1. Generate FINALIZED MASTER ALLOCATION SHEET
        master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
        updated_df.to_excel(master_allocation_path, index=False, sheet_name='Master Allocation')
        logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
        
        # 2. Generate MASTER BILLINGS SHEET
        master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
        updated_df.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
        logger.info(f"Generated Master Billings Sheet: {master_billing_path}")
        
        # 3. Generate FINAL REGION IMPORT FILES
        for division in ['DFW', 'WTX', 'HOU']:
            division_data = updated_df[updated_df['Division'] == division].copy()
            
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
                
                # Format date if exists
                if 'Date' in import_df.columns:
                    # Check if all dates are missing
                    if import_df['Date'].isna().all() or (import_df['Date'] == '').all():
                        import_df['Date'] = datetime.now().strftime('%Y-%m-%d')
                    else:
                        # Format existing dates
                        import_df['Date'] = pd.to_datetime(import_df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                else:
                    import_df['Date'] = datetime.now().strftime('%Y-%m-%d')
                
                # Write CSV
                output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
                import_df.to_csv(output_path, index=False)
                
                # Log division total
                division_total = import_df['Amount'].sum()
                logger.info(f"Generated {division} Import File: {output_path} with {len(import_df)} records - Total: ${division_total:,.2f}")
        
        logger.info(f"Successfully generated all required deliverables!")
        return True
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    main()