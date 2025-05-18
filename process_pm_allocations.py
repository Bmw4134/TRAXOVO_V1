"""
Process PM Allocations

This script correctly extracts and processes the PM allocation data from the 'ALL' sheet
in each PM allocation file, then merges it with the base RAGLE file.
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

# PM allocation files - prioritize the specific PM allocations to avoid duplicates
PM_FILES = [
    "WTX EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx",  # Add this first - it's the one we successfully analyzed
    "A.HARDIMO EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx",
    "C.KOCMICK EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx",
    "L. MORALES EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx",
    "S. ALVAREZ EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx"
]

# Output file names
FINALIZED_MASTER_ALLOCATION = f"FINALIZED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
MASTER_BILLINGS = f"MASTER_BILLINGS_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
REGION_IMPORT_PREFIX = f"FINAL_REGION_IMPORT_"

def load_base_file():
    """Load and process the base RAGLE file"""
    base_path = os.path.join(ATTACHED_ASSETS_DIR, BASE_FILE)
    if not os.path.exists(base_path):
        logger.error(f"Base file not found: {base_path}")
        return None
    
    try:
        logger.info(f"Loading base RAGLE file: {base_path}")
        base_df = pd.read_excel(base_path, sheet_name='Equip Billings')
        original_total = base_df['Amount'].sum()
        logger.info(f"Loaded {len(base_df)} records from base file")
        logger.info(f"Original total: ${original_total:,.2f}")
        return base_df
    except Exception as e:
        logger.error(f"Error loading base file: {str(e)}")
        return None

def process_pm_files():
    """Process all PM allocation files and extract data"""
    all_pm_data = []
    
    for pm_file in PM_FILES:
        pm_path = os.path.join(ATTACHED_ASSETS_DIR, pm_file)
        if not os.path.exists(pm_path):
            logger.warning(f"PM file not found: {pm_file}")
            continue
        
        logger.info(f"Processing PM file: {pm_file}")
        
        try:
            # Check if the 'ALL' sheet exists, which has the structured data
            xls = pd.ExcelFile(pm_path)
            
            if 'ALL' in xls.sheet_names:
                sheet_name = 'ALL'
                logger.info(f"Using 'ALL' sheet in {pm_file}")
            else:
                # Try to find a suitable allocation sheet
                for sheet in xls.sheet_names:
                    if 'EQ ALLOCATIONS' in sheet or 'ALLOCATION' in sheet.upper():
                        sheet_name = sheet
                        logger.info(f"Using '{sheet}' sheet in {pm_file}")
                        break
                else:
                    logger.warning(f"Could not find suitable sheet in {pm_file}")
                    continue
            
            # Load the sheet
            pm_df = pd.read_excel(pm_path, sheet_name=sheet_name)
            
            # Check if the required columns exist
            required_cols = {'Equip #', 'Job', 'Units'}
            found_cols = set()
            for col in pm_df.columns:
                col_str = str(col).upper()
                if 'EQUIP' in col_str and '#' in col_str:
                    found_cols.add('Equip #')
                elif 'JOB' in col_str:
                    found_cols.add('Job')
                elif 'UNIT' in col_str and not 'RATE' in col_str:
                    found_cols.add('Units')
            
            missing_cols = required_cols - found_cols
            if missing_cols:
                logger.warning(f"Missing required columns in {pm_file}: {missing_cols}")
                for col in pm_df.columns:
                    logger.info(f"Available column: {col}")
                continue
            
            # Normalize column names
            col_mapping = {}
            for col in pm_df.columns:
                col_str = str(col).upper()
                if 'EQUIP' in col_str and '#' in col_str:
                    col_mapping[col] = 'Equip #'
                elif 'JOB' in col_str:
                    col_mapping[col] = 'Job'
                elif 'UNIT' in col_str and not 'RATE' in col_str:
                    col_mapping[col] = 'Units'
                elif 'COST' in col_str and 'CODE' in col_str:
                    col_mapping[col] = 'Cost Code'
                elif 'RATE' in col_str:
                    col_mapping[col] = 'Rate'
                elif 'AMOUNT' in col_str or 'TOTAL' in col_str:
                    col_mapping[col] = 'Amount'
            
            # Rename the columns
            pm_df = pm_df.rename(columns=col_mapping)
            
            # Keep only relevant columns
            keep_cols = ['Equip #', 'Job', 'Units', 'Rate', 'Amount', 'Cost Code']
            keep_cols = [col for col in keep_cols if col in pm_df.columns]
            pm_df = pm_df[keep_cols].copy()
            
            # Remove rows with missing equipment IDs or job numbers
            pm_df = pm_df.dropna(subset=['Equip #', 'Job'])
            
            # Add source file column
            pm_df['Source'] = pm_file
            
            logger.info(f"Extracted {len(pm_df)} records from {pm_file}")
            
            # Add to collection
            all_pm_data.append(pm_df)
            
        except Exception as e:
            logger.error(f"Error processing {pm_file}: {str(e)}")
    
    # Combine all PM data
    if all_pm_data:
        combined_df = pd.concat(all_pm_data, ignore_index=True)
        logger.info(f"Combined {len(combined_df)} records from all PM files")
        return combined_df
    else:
        logger.warning("No PM data could be extracted")
        return None

def merge_and_generate_deliverables():
    """Merge base file with PM allocations and generate deliverables"""
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Load base file
    base_df = load_base_file()
    if base_df is None:
        return False
    
    original_total = base_df['Amount'].sum()
    
    # Process PM files
    pm_df = process_pm_files()
    if pm_df is None:
        logger.warning("Using base file without PM revisions")
        pm_df = pd.DataFrame()
    
    # Create a copy of the base file to apply updates
    updated_df = base_df.copy()
    
    # Keep track of revisions
    revisions = []
    
    # Create a lookup dictionary for base records
    equipment_dict = {}
    for idx, row in base_df.iterrows():
        equip_id = str(row['Equip #']).strip()
        job = str(row['Job']).strip()
        key = f"{equip_id}_{job}"
        equipment_dict[key] = idx
    
    # Apply PM allocations
    if not pm_df.empty:
        for idx, row in pm_df.iterrows():
            # Standardize the key values
            equip_id = str(row['Equip #']).strip()
            job = str(row['Job']).strip()
            key = f"{equip_id}_{job}"
            
            # If this equipment/job combo exists in the base file
            if key in equipment_dict:
                base_idx = equipment_dict[key]
                
                # Check if Units column exists and has a value
                if 'Units' in row and not pd.isna(row['Units']):
                    try:
                        old_units = updated_df.at[base_idx, 'Units']
                        new_units = float(row['Units'])
                        
                        # Only update if there's a change
                        if new_units != old_units:
                            # Record the revision
                            revisions.append({
                                'Equip ID': equip_id,
                                'Job': job,
                                'Source': row['Source'],
                                'Old Units': old_units,
                                'New Units': new_units,
                                'Change': new_units - old_units
                            })
                            
                            # Update the units
                            updated_df.at[base_idx, 'Units'] = new_units
                            
                            # Recalculate the amount
                            rate = updated_df.at[base_idx, 'Rate']
                            updated_df.at[base_idx, 'Amount'] = new_units * rate
                            
                            logger.info(f"Updated {equip_id} for {job}: Units {old_units} → {new_units}")
                    except Exception as e:
                        logger.error(f"Error updating {equip_id} for {job}: {str(e)}")
                
                # Update Cost Code if available
                if 'Cost Code' in row and not pd.isna(row['Cost Code']):
                    try:
                        new_cc = str(row['Cost Code']).strip()
                        if new_cc:
                            # Add Cost Code column if it doesn't exist
                            if 'Cost Code' not in updated_df.columns:
                                updated_df['Cost Code'] = ""
                            
                            # Update the cost code
                            old_cc = str(updated_df.at[base_idx, 'Cost Code']).strip() if pd.notna(updated_df.at[base_idx, 'Cost Code']) else ""
                            updated_df.at[base_idx, 'Cost Code'] = new_cc
                            
                            logger.info(f"Updated {equip_id} for {job}: Cost Code {old_cc} → {new_cc}")
                    except Exception as e:
                        logger.error(f"Error updating cost code for {equip_id}, {job}: {str(e)}")
    
    # Log summary of changes
    if revisions:
        logger.info(f"Made {len(revisions)} revisions")
        revisions_df = pd.DataFrame(revisions)
        
        # Calculate the net change in units
        total_unit_change = sum(revision['Change'] for revision in revisions)
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

if __name__ == "__main__":
    merge_and_generate_deliverables()