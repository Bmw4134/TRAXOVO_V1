"""
Quick PM Processor

Extracts data from the EQ ALLOCATIONS sheet with the correct structure,
targeting the header row at index 2 and the data starting at row 3.
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
    "WTX EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx", 
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
    """Load the base RAGLE file"""
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

def extract_data_from_pm_file(file_path):
    """Extract data from a PM allocation file using the correct row structure"""
    try:
        # Check if 'EQ ALLOCATIONS - ALL DIV' sheet exists
        xls = pd.ExcelFile(file_path)
        sheet_name = 'EQ ALLOCATIONS - ALL DIV'
        
        if sheet_name not in xls.sheet_names:
            # Try to find a similar sheet
            potential_sheets = [s for s in xls.sheet_names if 'ALLOCATION' in s.upper() or 'DIV' in s.upper()]
            if potential_sheets:
                sheet_name = potential_sheets[0]
            else:
                logger.warning(f"Could not find allocation sheet in {os.path.basename(file_path)}")
                return None
        
        logger.info(f"Using sheet: {sheet_name}")
        
        # Read the entire sheet
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        if len(df) < 4:  # Need at least header + one data row
            logger.warning(f"Not enough data in {sheet_name}")
            return None
        
        # Find the header row (usually at index 2)
        header_row = None
        for i in range(min(10, len(df))):
            row = df.iloc[i].tolist()
            row_values = [str(val).upper() for val in row if pd.notna(val)]
            
            # Check if this row contains the key header fields
            has_asset = any('EQUIP' in val or 'ASSET' in val for val in row_values)
            has_job = any('JOB' in val for val in row_values)
            has_unit = any('UNIT' in val or 'ALLOCATION' in val or 'REVISION' in val for val in row_values)
            
            if has_asset and has_job and has_unit:
                header_row = i
                logger.info(f"Found header row at index {i}")
                break
        
        if header_row is None:
            logger.warning(f"Could not find header row in {sheet_name}")
            return None
        
        # Extract headers and data
        headers = df.iloc[header_row].tolist()
        data_start = header_row + 1
        
        # Create new dataframe with proper column names
        data_df = pd.DataFrame(df.iloc[data_start:].values, columns=headers)
        
        # Map column names to standardized names
        col_mapping = {}
        for col in data_df.columns:
            col_str = str(col).upper()
            if 'EQUIP' in col_str or 'ASSET' in col_str:
                col_mapping[col] = 'Equip #'
            elif 'JOB' in col_str and '#' not in col_str and 'DESC' not in col_str:
                col_mapping[col] = 'Job'
            elif ('UNIT' in col_str and 'ALLOCATION' in col_str) or 'ALLOCATION' in col_str:
                col_mapping[col] = 'Units'
            elif 'COST' in col_str and 'CODE' in col_str:
                col_mapping[col] = 'Cost Code'
            elif 'REVISION' in col_str and 'ALLOCATION' not in col_str:
                col_mapping[col] = 'Revision'
            elif 'RATE' in col_str and 'X' not in col_str:
                col_mapping[col] = 'Rate'
            elif ('RATE' in col_str and 'X' in col_str and 'REVISION' in col_str) or 'AMOUNT' in col_str:
                col_mapping[col] = 'Amount'
        
        # Rename only the columns we could map
        data_df = data_df.rename(columns=col_mapping)
        
        # Ensure Units column is properly set
        if 'Units' not in data_df.columns and 'Revision' in data_df.columns:
            data_df['Units'] = data_df['Revision']
        
        # Select only the columns we need
        needed_cols = ['Equip #', 'Job', 'Units', 'Cost Code', 'Rate', 'Amount']
        keep_cols = [col for col in needed_cols if col in data_df.columns]
        
        # Keep only rows with equipment IDs
        result_df = data_df[keep_cols].copy()
        result_df = result_df.dropna(subset=['Equip #', 'Job'])
        
        # Convert Units to numeric
        if 'Units' in result_df.columns:
            result_df['Units'] = pd.to_numeric(result_df['Units'], errors='coerce')
            result_df = result_df[result_df['Units'] > 0]
        
        # Add source file info
        result_df['Source'] = os.path.basename(file_path)
        
        logger.info(f"Extracted {len(result_df)} records with valid Units values")
        
        return result_df
    
    except Exception as e:
        logger.error(f"Error extracting data from {os.path.basename(file_path)}: {str(e)}")
        return None

def process_all_pm_files():
    """Process all PM allocation files"""
    all_pm_data = []
    
    for pm_file in PM_FILES:
        pm_path = os.path.join(ATTACHED_ASSETS_DIR, pm_file)
        if not os.path.exists(pm_path):
            logger.warning(f"PM file not found: {pm_file}")
            continue
        
        logger.info(f"Processing PM file: {pm_file}")
        pm_df = extract_data_from_pm_file(pm_path)
        
        if pm_df is not None and not pm_df.empty:
            all_pm_data.append(pm_df)
            logger.info(f"Successfully extracted data from {pm_file}")
        else:
            logger.warning(f"No valid data extracted from {pm_file}")
    
    if all_pm_data:
        combined_df = pd.concat(all_pm_data, ignore_index=True)
        logger.info(f"Combined {len(combined_df)} records from all PM files")
        return combined_df
    else:
        logger.warning("No data extracted from any PM file")
        return None

def update_base_with_pm_data(base_df, pm_df):
    """Update the base file with data from PM allocations"""
    if pm_df is None or pm_df.empty:
        logger.warning("No PM data to apply")
        return base_df.copy(), []
    
    # Create a copy to apply updates
    updated_df = base_df.copy()
    
    # Create a lookup dictionary for equipment records
    equipment_dict = {}
    for idx, row in base_df.iterrows():
        equip_id = str(row['Equip #']).strip() if pd.notna(row['Equip #']) else ""
        job = str(row['Job']).strip() if pd.notna(row['Job']) else ""
        key = f"{equip_id}_{job}"
        equipment_dict[key] = idx
    
    # Keep track of revisions
    revisions = []
    
    # Apply PM revisions
    for idx, row in pm_df.iterrows():
        equip_id = str(row['Equip #']).strip() if pd.notna(row['Equip #']) else ""
        job = str(row['Job']).strip() if pd.notna(row['Job']) else ""
        key = f"{equip_id}_{job}"
        
        # Skip if either is empty
        if not equip_id or not job:
            continue
        
        # If this equipment/job combo exists in the base file
        if key in equipment_dict:
            base_idx = equipment_dict[key]
            
            # Update units if available
            if 'Units' in row and pd.notna(row['Units']) and row['Units'] > 0:
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
            
            # Update Cost Code if available
            if 'Cost Code' in row and pd.notna(row['Cost Code']):
                new_cc = str(row['Cost Code']).strip()
                if new_cc:
                    # Add Cost Code column if it doesn't exist
                    if 'Cost Code' not in updated_df.columns:
                        updated_df['Cost Code'] = ""
                    
                    # Update the cost code
                    old_cc = str(updated_df.at[base_idx, 'Cost Code']).strip() if pd.notna(updated_df.at[base_idx, 'Cost Code']) else ""
                    updated_df.at[base_idx, 'Cost Code'] = new_cc
                    
                    logger.info(f"Updated {equip_id} for {job}: Cost Code {old_cc} → {new_cc}")
    
    return updated_df, revisions

def run_pm_processor():
    """Main function to process PM allocations and generate deliverables"""
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Load base file
    base_df = load_base_file()
    if base_df is None:
        return False
    
    original_total = base_df['Amount'].sum()
    
    # Process all PM files
    pm_df = process_all_pm_files()
    
    # Update base file with PM data
    updated_df, revisions = update_base_with_pm_data(base_df, pm_df)
    
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
        job_str = str(job).upper() if pd.notna(job) else ""
        if not job_str:
            return 'DFW'  # Default
            
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
    run_pm_processor()