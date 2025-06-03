"""
Quick script to properly process PM allocation sheets with REVISION values
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
DALLAS_PM_FILE = "2023-034 EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx"

def load_base_file():
    """Load the base RAGLE file"""
    base_path = os.path.join(ATTACHED_ASSETS_DIR, BASE_FILE)
    if not os.path.exists(base_path):
        logger.error(f"Base file not found: {base_path}")
        return None
    
    try:
        logger.info(f"Loading base RAGLE file: {base_path}")
        base_df = pd.read_excel(base_path, sheet_name='Equip Billings')
        return base_df
    except Exception as e:
        logger.error(f"Error loading base file: {str(e)}")
        return None

def extract_revisions_from_dallas_file():
    """Extract the revision values from the Dallas file"""
    dallas_path = os.path.join(ATTACHED_ASSETS_DIR, DALLAS_PM_FILE)
    if not os.path.exists(dallas_path):
        logger.error(f"Dallas file not found: {dallas_path}")
        return None
    
    try:
        # Open the Excel file
        logger.info(f"Extracting revisions from Dallas file: {dallas_path}")
        xls = pd.ExcelFile(dallas_path)
        
        # Find the allocation sheet
        sheet_name = None
        for name in xls.sheet_names:
            if 'EQ ALLOCATIONS - ALL DIV' in name or 'ALL DIV' in name:
                sheet_name = name
                break
        
        if not sheet_name:
            logger.error(f"Could not find allocation sheet in Dallas file")
            return None
            
        # Read with header at row 4 (index 3)
        df = pd.read_excel(dallas_path, sheet_name=sheet_name, header=3)
        
        # Keep only necessary columns
        if 'ASSET ID' not in df.columns or 'JOB' not in df.columns or 'REVISION' not in df.columns:
            logger.error(f"Required columns not found in Dallas file")
            return None
            
        # Convert to numeric values
        df['REVISION'] = pd.to_numeric(df['REVISION'], errors='coerce')
        
        # Filter for valid revision values
        revisions_df = df[~df['REVISION'].isna() & (df['REVISION'] > 0)]
        
        logger.info(f"Found {len(revisions_df)} valid revisions in Dallas file")
        
        # Create a clean dataframe with just the key fields
        result = pd.DataFrame()
        result['Equip #'] = revisions_df['ASSET ID']
        result['Job'] = revisions_df['JOB']
        result['New Units'] = revisions_df['REVISION']
        
        return result
    
    except Exception as e:
        logger.error(f"Error extracting revisions: {str(e)}")
        return None

def apply_revisions_to_base(base_df, revisions_df):
    """Apply the revision values to the base file"""
    if base_df is None or revisions_df is None:
        logger.error("Cannot apply revisions - missing data")
        return None
    
    # Create a copy to modify
    updated_df = base_df.copy()
    
    # Keep track of changes
    changes = []
    
    # Apply each revision
    for _, row in revisions_df.iterrows():
        equip_id = str(row['Equip #']).strip()
        job = str(row['Job']).strip()
        new_units = float(row['New Units'])
        
        # Find matching row in base dataframe
        matching_rows = updated_df[(updated_df['Equip #'] == equip_id) & (updated_df['Job'] == job)]
        
        if not matching_rows.empty:
            idx = matching_rows.index[0]
            old_units = updated_df.at[idx, 'Units']
            rate = updated_df.at[idx, 'Rate']
            
            changes.append({
                'Equip ID': equip_id,
                'Job': job,
                'Old Units': old_units,
                'New Units': new_units,
                'Change': new_units - old_units,
                'Old Amount': old_units * rate,
                'New Amount': new_units * rate
            })
            
            # Update the values
            updated_df.at[idx, 'Units'] = new_units
            updated_df.at[idx, 'Amount'] = new_units * rate
            
            logger.info(f"Updated {equip_id} for {job}: Units {old_units} → {new_units}, Amount: ${new_units * rate:,.2f}")
    
    # Create changes dataframe
    changes_df = pd.DataFrame(changes)
    
    # Save the changes to Excel
    changes_path = os.path.join(EXPORTS_DIR, f"REVISION_CHANGES_{MONTH_NAME}_{YEAR}.xlsx")
    changes_df.to_excel(changes_path, index=False)
    logger.info(f"Saved {len(changes)} revision changes to {changes_path}")
    
    # Calculate the total change in billing
    total_old = changes_df['Old Amount'].sum()
    total_new = changes_df['New Amount'].sum()
    logger.info(f"Total change in billing: ${total_old:,.2f} → ${total_new:,.2f}, Difference: ${total_new - total_old:,.2f}")
    
    return updated_df, changes_df

def save_updated_master(updated_df):
    """Save the updated master sheet"""
    if updated_df is None:
        logger.error("Cannot save - missing data")
        return
    
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Calculate totals by division
    dfw_total = updated_df[updated_df['Division'] == 'DFW']['Amount'].sum()
    hou_total = updated_df[updated_df['Division'] == 'HOU']['Amount'].sum()
    wt_total = updated_df[updated_df['Division'] == 'WT']['Amount'].sum()
    total = updated_df['Amount'].sum()
    
    logger.info(f"Division totals after applying revisions:")
    logger.info(f"DFW: ${dfw_total:,.2f}")
    logger.info(f"HOU: ${hou_total:,.2f}")
    logger.info(f"WT: ${wt_total:,.2f}")
    logger.info(f"Combined: ${total:,.2f}")
    
    # Save to Excel
    updated_path = os.path.join(EXPORTS_DIR, f"UPDATED_MASTER_WITH_REVISIONS_{MONTH_NAME}_{YEAR}.xlsx")
    updated_df.to_excel(updated_path, index=False)
    logger.info(f"Saved updated master to {updated_path}")
    
    # Save division import files
    for division in ['DFW', 'HOU', 'WT']:
        div_df = updated_df[updated_df['Division'] == division]
        if not div_df.empty:
            import_path = os.path.join(EXPORTS_DIR, f"IMPORT_READY_{division}_{MONTH_NAME}_{YEAR}.csv")
            div_df.to_csv(import_path, index=False)
            div_total = div_df['Amount'].sum()
            logger.info(f"Saved {division} import file to {import_path} - {len(div_df)} records, Total: ${div_total:,.2f}")

def main():
    """Main function to run the script"""
    # Load the base file
    base_df = load_base_file()
    if base_df is None:
        logger.error("Cannot proceed without base file")
        return
    
    # Extract revisions from the Dallas file
    revisions_df = extract_revisions_from_dallas_file()
    if revisions_df is None or revisions_df.empty:
        logger.error("No valid revisions found")
        return
    
    # Apply the revisions to the base file
    updated_df, changes_df = apply_revisions_to_base(base_df, revisions_df)
    if updated_df is None:
        logger.error("Failed to apply revisions")
        return
    
    # Save the updated master
    save_updated_master(updated_df)
    
    logger.info("Completed processing PM allocations with revisions!")

if __name__ == "__main__":
    main()