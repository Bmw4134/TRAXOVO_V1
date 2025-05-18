"""
Final Billing Processor with correct PM allocation integration

This script properly processes PM allocation data from the 'EQ ALLOCATIONS - ALL DIV' sheet
where the header row is at index 2 and data starts at row 3. It applies these allocations
to update the base RAGLE file, recalculating all amounts based on PM-reviewed unit allocations.
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

# PM allocation files to process
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
    """
    Extract data from a PM allocation file, specifically targeting the 'EQ ALLOCATIONS - ALL DIV' sheet.
    The correct structure: header row is at index 3 (row 4 in Excel), data starts at row 4.
    """
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            logger.error(f"PM file not found: {file_path}")
            return None
        
        file_name = os.path.basename(file_path)
        logger.info(f"Processing PM file: {file_name}")
        
        # Check if 'EQ ALLOCATIONS - ALL DIV' sheet exists
        xls = pd.ExcelFile(file_path)
        sheet_name = 'EQ ALLOCATIONS - ALL DIV'
        
        if sheet_name not in xls.sheet_names:
            # Try to find a similar sheet
            potential_sheets = [s for s in xls.sheet_names if 'ALLOCATION' in s.upper() or 'DIV' in s.upper()]
            if potential_sheets:
                sheet_name = potential_sheets[0]
                logger.info(f"Using alternate sheet: {sheet_name}")
            else:
                logger.warning(f"Could not find allocation sheet in {file_name}")
                return None
        
        # Read with the header at row 3 (4th row in Excel) which we know is the correct structure
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=3)
        
        # Display the column names to verify they're correct
        logger.info(f"Columns from header at row 3: {df.columns.tolist()[:10]}")
        
        # Standardize column names - we should have the actual column names now
        column_mapping = {
            'DIV': 'Division',
            'JOB': 'Job',
            'JOB DESC': 'Job Description',
            'ASSET ID': 'Equip #',
            'EQUIPMENT': 'Equipment',
            'DRIVER': 'Driver',
            'UNIT ALLOCATION': 'Units',
            'COST CODE': 'Cost Code',
            'REVISION': 'Revision',
            'NOTE / DETAIL': 'Notes'
        }
        
        # Apply the column mapping for columns that exist
        mapped_cols = {}
        for src, target in column_mapping.items():
            if src in df.columns:
                mapped_cols[src] = target
        
        result_df = df.rename(columns=mapped_cols)
        
        # Verify required columns are present
        required_cols = ['Job', 'Equip #', 'Units']
        for col in required_cols:
            if col not in result_df.columns:
                # Try to find equivalent columns
                if col == 'Job' and 'JOB' in df.columns:
                    result_df['Job'] = df['JOB']
                elif col == 'Equip #' and 'ASSET ID' in df.columns:
                    result_df['Equip #'] = df['ASSET ID']
                elif col == 'Units' and 'UNIT ALLOCATION' in df.columns:
                    result_df['Units'] = df['UNIT ALLOCATION']
                else:
                    logger.warning(f"Required column {col} not found in {file_name}")
                    return None
        
        # Filter out rows with NaN in critical columns and drop empty rows
        result_df = result_df.dropna(subset=['Job', 'Equip #'])
        
        # Convert Units to numeric and filter for positive values
        result_df['Units'] = pd.to_numeric(result_df['Units'], errors='coerce')
        result_df = result_df[result_df['Units'] > 0]
        
        # Handle "CC NEEDED" in Cost Code
        if 'Cost Code' in result_df.columns:
            def clean_cost_code(cc):
                if pd.isna(cc):
                    return "9000 100F"  # Default cost code
                cc_str = str(cc).strip().upper()
                if "CC NEEDED" in cc_str or cc_str == "" or cc_str == "NAN":
                    return "9000 100F"  # Default cost code
                return cc
            
            result_df['Cost Code'] = result_df['Cost Code'].apply(clean_cost_code)
        else:
            result_df['Cost Code'] = "9000 100F"  # Default cost code for all if column missing
        
        # Add source file info
        result_df['Source'] = file_name
        
        # Clean up columns - keep only what we need
        needed_columns = ['Division', 'Job', 'Equip #', 'Equipment', 'Driver', 'Units', 'Cost Code']
        for col in needed_columns:
            if col not in result_df.columns:
                result_df[col] = None
        
        # Keep only the columns we need
        final_df = result_df[needed_columns + ['Source']].copy()
        
        # Log the results
        logger.info(f"Successfully extracted {len(final_df)} valid records from {file_name}")
        
        return final_df
    
    except Exception as e:
        logger.error(f"Error extracting data from {os.path.basename(file_path)}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def process_all_pm_files():
    """Process all PM allocation files"""
    all_pm_data = []
    
    for pm_file in PM_FILES:
        pm_path = os.path.join(ATTACHED_ASSETS_DIR, pm_file)
        pm_df = extract_data_from_pm_file(pm_path)
        
        if pm_df is not None and not pm_df.empty:
            all_pm_data.append(pm_df)
            logger.info(f"Successfully extracted data from {pm_file}")
        else:
            logger.warning(f"No valid data extracted from {pm_file}")
    
    if all_pm_data:
        combined_df = pd.concat(all_pm_data, ignore_index=True)
        logger.info(f"Combined {len(combined_df)} records from all PM files")
        
        # Remove duplicates - prioritize based on the order of PM_FILES
        # This keeps the first occurrence of each equipment-job combination
        combined_df['Priority'] = combined_df['Source'].apply(lambda x: PM_FILES.index(x) if x in PM_FILES else 999)
        combined_df = combined_df.sort_values('Priority')
        combined_df = combined_df.drop_duplicates(subset=['Equip #', 'Job'], keep='first')
        combined_df = combined_df.drop(columns=['Priority'])
        
        logger.info(f"After removing duplicates: {len(combined_df)} records")
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
    
    # Create a lookup dictionary for equipment records in the base file
    equipment_dict = {}
    for idx, row in base_df.iterrows():
        equip_id = str(row['Equip #']).strip() if pd.notna(row['Equip #']) else ""
        job = str(row['Job']).strip() if pd.notna(row['Job']) else ""
        key = f"{equip_id}_{job}"
        equipment_dict[key] = idx
    
    logger.info(f"Created lookup dictionary with {len(equipment_dict)} equipment-job combinations")
    
    # Extract equipment rates from the base file
    rate_dict = {}
    for idx, row in base_df.iterrows():
        equip_id = str(row['Equip #']).strip() if pd.notna(row['Equip #']) else ""
        if pd.notna(row['Rate']):
            rate_dict[equip_id] = float(row['Rate'])
    
    logger.info(f"Extracted {len(rate_dict)} equipment rates from base file")
    
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
            
            # Check for revision first, then fall back to unit allocation
            new_units = None
            
            # If Revision column exists and has a value, use it
            if 'Revision' in row and pd.notna(row['Revision']) and row['Revision'] != "" and str(row['Revision']).strip() != "0":
                try:
                    new_units = float(row['Revision'])
                    unit_source = "Revision"
                except (ValueError, TypeError):
                    # If revision can't be converted to float, use unit allocation
                    unit_source = "Units (Revision not numeric)"
            
            # If no valid revision, use unit allocation
            if new_units is None and pd.notna(row['Units']) and row['Units'] > 0:
                new_units = float(row['Units'])
                unit_source = "Units"
            
            # Update units if we have a valid value
            if new_units is not None and new_units > 0:
                old_units = updated_df.at[base_idx, 'Units']
                
                # Record all PM allocations as revisions, even if unchanged
                revisions.append({
                    'Equip ID': equip_id,
                    'Job': job,
                    'Source': row['Source'],
                    'Old Units': old_units,
                    'New Units': new_units,
                    'Change': new_units - old_units,
                    'Source Column': unit_source
                })
                
                # Always update with PM allocation value
                updated_df.at[base_idx, 'Units'] = new_units
                
                # Recalculate the amount 
                rate = updated_df.at[base_idx, 'Rate']
                new_amount = new_units * rate
                updated_df.at[base_idx, 'Amount'] = new_amount
                
                logger.info(f"Updated {equip_id} for {job}: Units {old_units} → {new_units} (from {unit_source}), Amount: ${new_amount:,.2f}")
            
            # Update Cost Code if available
            if pd.notna(row['Cost Code']) and row['Cost Code'] != "":
                new_cc = str(row['Cost Code']).strip()
                # Add Cost Code column if it doesn't exist
                if 'Cost Code' not in updated_df.columns:
                    updated_df['Cost Code'] = ""
                
                # Update the cost code
                old_cc = str(updated_df.at[base_idx, 'Cost Code']).strip() if 'Cost Code' in updated_df.columns and pd.notna(updated_df.at[base_idx, 'Cost Code']) else ""
                updated_df.at[base_idx, 'Cost Code'] = new_cc
                
                logger.info(f"Updated {equip_id} for {job}: Cost Code {old_cc} → {new_cc}")
    
    return updated_df, revisions

def generate_deliverables(updated_df):
    """Generate the three required deliverables"""
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Calculate updated total
    updated_total = updated_df['Amount'].sum()
    logger.info(f"Updated total: ${updated_total:,.2f}")
    
    # Add division column if it doesn't exist
    if 'Division' not in updated_df.columns:
        def assign_division(job):
            job_str = str(job).upper() if pd.notna(job) else ""
            if not job_str:
                return 'DFW'  # Default
                
            if job_str.startswith('D') or '2023' in job_str or '2024-' in job_str:
                return 'DFW'
            elif job_str.startswith('H') or '-H' in job_str:
                return 'HOU'
            elif job_str.startswith('W') or 'WTX' in job_str or 'WT-' in job_str:
                return 'WT'  # Changed from 'WTX' to 'WT' to match the actual division code
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
    wtx_total = updated_df[updated_df['Division'] == 'WT']['Amount'].sum()  # Changed from 'WTX' to 'WT'
    
    logger.info(f"Division totals after revisions:")
    logger.info(f"DFW: ${dfw_total:,.2f}")
    logger.info(f"HOU: ${hou_total:,.2f}")
    logger.info(f"WT: ${wtx_total:,.2f}")  # Changed display name to 'WT'
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
            
            # Ensure Cost_Code is set
            if 'Cost_Code' not in import_df.columns or import_df['Cost_Code'].isna().all():
                import_df['Cost_Code'] = "9000 100F"  # Default cost code
            
            # Write CSV
            output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
            import_df.to_csv(output_path, index=False)
            
            # Log division total
            division_total = import_df['Amount'].sum()
            logger.info(f"Generated {division} Import File: {output_path} with {len(import_df)} records - Total: ${division_total:,.2f}")
    
    logger.info(f"Successfully generated all required deliverables!")
    return True

def process_and_generate_deliverables():
    """Main function to process billing data and generate all required deliverables"""
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # 1. Load base file
    base_df = load_base_file()
    if base_df is None:
        logger.error("Failed to load base file. Aborting.")
        return False
    
    original_total = base_df['Amount'].sum()
    logger.info(f"Original base file total: ${original_total:,.2f}")
    
    # 2. Process all PM files
    pm_df = process_all_pm_files()
    if pm_df is None:
        logger.warning("No PM data found. Proceeding with base file only.")
    else:
        logger.info(f"Successfully extracted {len(pm_df)} valid PM allocation records")
    
    # 3. Update base file with PM data
    updated_df, revisions = update_base_with_pm_data(base_df, pm_df)
    
    # 4. Log summary of changes
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
    
    # 5. Generate deliverables
    result = generate_deliverables(updated_df)
    
    # 6. Final check on totals
    updated_total = updated_df['Amount'].sum()
    logger.info(f"Final updated total: ${updated_total:,.2f}")
    logger.info(f"Difference from original: ${updated_total - original_total:,.2f}")
    
    return result

if __name__ == "__main__":
    process_and_generate_deliverables()