"""
Extract PM Allocations

This script extracts data from the PM allocation files to get the properly allocated units
and calculated amounts based on units × rates.
"""
import os
import pandas as pd
import glob
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

def find_pm_allocation_files():
    """Find all PM allocation files"""
    allocation_patterns = [
        "*ALLOCATION*APRIL*2025*.xlsx",
        "*ALLOCATION*APR*2025*.xlsx",
        "*ALLOCATIONS*APRIL*2025*.xlsx"
    ]
    
    all_files = []
    for pattern in allocation_patterns:
        all_files.extend(glob.glob(os.path.join(ATTACHED_ASSETS_DIR, pattern)))
    
    logger.info(f"Found {len(all_files)} potential allocation files")
    return all_files

def extract_rates_from_ragle():
    """Extract equipment rates from the RAGLE file"""
    ragle_file = os.path.join(ATTACHED_ASSETS_DIR, "RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm")
    
    if not os.path.exists(ragle_file):
        logger.warning(f"RAGLE file not found: {ragle_file}")
        return {}
    
    try:
        # Try to find the Equip Rates sheet
        xlsx = pd.ExcelFile(ragle_file)
        if "Equip Rates" in xlsx.sheet_names:
            rates_df = pd.read_excel(ragle_file, sheet_name="Equip Rates")
            
            # Find equipment ID and rate columns
            equip_col = None
            rate_col = None
            
            for col in rates_df.columns:
                if col == "Equip #" or "equipment" in str(col).lower() or "equip" in str(col).lower():
                    equip_col = col
                    break
            
            for col in rates_df.columns:
                if col == "Rate" or "rate" in str(col).lower():
                    rate_col = col
                    break
            
            if equip_col and rate_col:
                # Create dictionary mapping equipment ID to rate
                rates_dict = dict(zip(rates_df[equip_col].astype(str), rates_df[rate_col]))
                logger.info(f"Extracted {len(rates_dict)} equipment rates from RAGLE file")
                return rates_dict
            else:
                logger.warning("Could not identify equipment ID and rate columns in RAGLE file")
                return {}
        else:
            # Try the Equip Billings sheet for rates
            billings_df = pd.read_excel(ragle_file, sheet_name="Equip Billings")
            if "Equip #" in billings_df.columns and "Rate" in billings_df.columns:
                rates_dict = dict(zip(billings_df["Equip #"].astype(str), billings_df["Rate"]))
                logger.info(f"Extracted {len(rates_dict)} equipment rates from RAGLE Equip Billings sheet")
                return rates_dict
            else:
                logger.warning("Could not find rates in RAGLE file")
                return {}
    except Exception as e:
        logger.error(f"Error extracting rates from RAGLE file: {str(e)}")
        return {}

def process_allocation_files():
    """Process all PM allocation files"""
    # Find all allocation files
    allocation_files = find_pm_allocation_files()
    if not allocation_files:
        logger.error("No allocation files found")
        return False
    
    # Extract rates
    rates_dict = extract_rates_from_ragle()
    
    # Process each allocation file
    all_allocation_data = []
    for file_path in allocation_files:
        try:
            logger.info(f"Processing {os.path.basename(file_path)}")
            df = pd.read_excel(file_path)
            
            # Skip files with no data
            if df.empty:
                logger.warning(f"Empty file: {file_path}")
                continue
            
            # Identify key columns
            potential_equipment_cols = ["equip id", "equip_id", "equipment", "equipment_id", "equip #", "eq id", "eq #"]
            equip_col = None
            for col in df.columns:
                if any(potential_name in str(col).lower() for potential_name in potential_equipment_cols):
                    equip_col = col
                    break
            
            potential_unit_cols = ["units", "hours", "qty", "quantity"]
            unit_col = None
            for col in df.columns:
                if any(potential_name in str(col).lower() for potential_name in potential_unit_cols):
                    unit_col = col
                    break
            
            # Skip files without equipment column
            if not equip_col:
                logger.warning(f"Could not identify equipment column in {file_path}")
                continue
            
            # Prepare data for analysis
            allocation_data = df.copy()
            
            # Handle rates and calculate amount
            if unit_col:
                # Convert units to numeric
                allocation_data[unit_col] = pd.to_numeric(allocation_data[unit_col], errors='coerce').fillna(0)
                
                # Add rate based on equipment ID
                rate_col = None
                for col in allocation_data.columns:
                    if "rate" in str(col).lower():
                        rate_col = col
                        break
                
                if not rate_col and rates_dict:
                    # Add rates from our dictionary
                    allocation_data['rate'] = allocation_data[equip_col].astype(str).map(rates_dict).fillna(0)
                    rate_col = 'rate'
                
                # Calculate amount if we have rates
                if rate_col:
                    allocation_data[rate_col] = pd.to_numeric(allocation_data[rate_col], errors='coerce').fillna(0)
                    amount_col = None
                    for col in allocation_data.columns:
                        if "amount" in str(col).lower() or "total" in str(col).lower():
                            amount_col = col
                            break
                    
                    if not amount_col:
                        allocation_data['amount'] = allocation_data[unit_col] * allocation_data[rate_col]
                        amount_col = 'amount'
                    
                    logger.info(f"File: {os.path.basename(file_path)}, Records: {len(allocation_data)}, Total: ${allocation_data[amount_col].sum():,.2f}")
            
            all_allocation_data.append(allocation_data)
        
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
    
    if not all_allocation_data:
        logger.error("No data extracted from allocation files")
        return False
    
    # Combine all allocation data
    combined_data = pd.concat(all_allocation_data, ignore_index=True)
    
    # Calculate overall total
    total = 0
    for df in all_allocation_data:
        for col in df.columns:
            if "amount" in str(col).lower() or "total" in str(col).lower():
                total += df[col].sum()
                break
    
    logger.info(f"Combined total from all allocation files: ${total:,.2f}")
    
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Generate the three required deliverables
    
    # 1. FINALIZED MASTER ALLOCATION SHEET
    master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
    combined_data.to_excel(master_allocation_path, index=False)
    logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
    
    # 2. MASTER BILLINGS SHEET
    master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
    combined_data.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
    logger.info(f"Generated Master Billings Sheet: {master_billing_path}")
    
    # 3. FINAL REGION IMPORT FILES
    # Try to identify division column
    division_col = None
    for col in combined_data.columns:
        if "division" in str(col).lower():
            division_col = col
            break
    
    if division_col:
        for division in ['DFW', 'WTX', 'HOU']:
            division_data = combined_data[combined_data[division_col] == division].copy()
            
            if not division_data.empty:
                # Create export data
                export_data = pd.DataFrame()
                
                # Find required columns
                required_cols = ['equip_id', 'date', 'job', 'cost_code', 'units', 'rate', 'amount']
                for req_col in required_cols:
                    for col in division_data.columns:
                        if req_col in str(col).lower():
                            export_data[req_col.capitalize()] = division_data[col]
                            break
                    if req_col not in [c.lower() for c in export_data.columns]:
                        export_data[req_col.capitalize()] = ""
                
                # Rename to standardized format
                export_data.columns = ['Equipment_Number', 'Date', 'Job', 'Cost_Code', 'Hours', 'Rate', 'Amount']
                
                # Write CSV
                output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
                export_data.to_csv(output_path, index=False)
                
                division_amount = 0
                if 'Amount' in export_data.columns:
                    division_amount = export_data['Amount'].sum()
                
                logger.info(f"Generated {division} Import File: {output_path} with {len(export_data)} records - Total: ${division_amount:,.2f}")
    
    return True

if __name__ == "__main__":
    process_allocation_files()