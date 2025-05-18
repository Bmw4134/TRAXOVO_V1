"""
Extract PM Changes

This script manually extracts data from specific columns in PM allocation files
to determine the updated billing amounts.
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

# Load original file data
def get_original_total():
    """Get the original total from the RAGLE file"""
    ragle_file = os.path.join(ATTACHED_ASSETS_DIR, 'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm')
    if not os.path.exists(ragle_file):
        logger.error(f"RAGLE file not found: {ragle_file}")
        return None
    
    try:
        ragle_df = pd.read_excel(ragle_file, sheet_name='Equip Billings')
        total = ragle_df['Amount'].sum()
        logger.info(f"Original total from RAGLE file: ${total:,.2f}")
        return total
    except Exception as e:
        logger.error(f"Error loading RAGLE file: {str(e)}")
        return None

# Process a PM allocation file, focusing on specific sheets and columns
def process_pm_file(filename):
    """Process a specific PM allocation file"""
    file_path = os.path.join(ATTACHED_ASSETS_DIR, filename)
    if not os.path.exists(file_path):
        logger.error(f"File not found: {filename}")
        return None
    
    try:
        # First check if "EQ ALLOCATIONS - ALL DIV" sheet exists
        xls = pd.ExcelFile(file_path)
        sheet_name = None
        
        for sheet in xls.sheet_names:
            if 'EQ ALLOCATIONS - ALL DIV' in sheet:
                sheet_name = sheet
                break
            elif 'ALLOCATIONS' in sheet.upper():
                sheet_name = sheet
                break
        
        if not sheet_name:
            logger.error(f"Could not find allocation sheet in {filename}")
            return None
        
        # Now load the sheet
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Look for the column with UNITS ALLOCATION or REVISION
        allocation_col = None
        
        for col in df.columns:
            col_name = str(col).upper()
            if ('UNIT' in col_name or 'QTY' in col_name) and ('ALLOCATION' in col_name or 'REVISION' in col_name):
                allocation_col = col
                logger.info(f"Found allocation column: {col}")
                break
        
        if not allocation_col:
            # Try to find any column with unit or qty
            for col in df.columns:
                col_name = str(col).upper()
                if 'UNIT' in col_name or 'QTY' in col_name:
                    allocation_col = col
                    logger.info(f"Using column: {col}")
                    break
        
        # Look for the rate column
        rate_col = None
        
        for col in df.columns:
            col_name = str(col).upper()
            if 'RATE' in col_name:
                rate_col = col
                logger.info(f"Found rate column: {col}")
                break
        
        # Calculate total if both columns are found
        if allocation_col and rate_col:
            # Convert to numeric
            df[allocation_col] = pd.to_numeric(df[allocation_col], errors='coerce').fillna(0)
            df[rate_col] = pd.to_numeric(df[rate_col], errors='coerce').fillna(0)
            
            # Calculate amount
            df['calculated_amount'] = df[allocation_col] * df[rate_col]
            total = df['calculated_amount'].sum()
            
            logger.info(f"PM {filename} total: ${total:,.2f}")
            return total
        else:
            logger.error(f"Could not find required columns in {filename}")
            return None
    
    except Exception as e:
        logger.error(f"Error processing {filename}: {str(e)}")
        return None

def main():
    """Main function"""
    # Get original total
    original_total = get_original_total()
    
    # Process specific PM allocation files
    pm_files = [
        "EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx",
        "A.HARDIMO EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx",
        "C.KOCMICK EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx",
        "L. MORALES EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx",
        "S. ALVAREZ EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx"
    ]
    
    pm_totals = {}
    for pm_file in pm_files:
        total = process_pm_file(pm_file)
        if total:
            pm_totals[pm_file] = total
    
    # Print comparison
    print("\n===== COMPARISON OF TOTALS =====")
    print(f"Original Total: ${original_total:,.2f}")
    print("\nPM Allocation Totals:")
    
    for file, total in pm_totals.items():
        change = total - original_total if original_total else 0
        change_pct = (change / original_total * 100) if original_total else 0
        print(f"- {file}: ${total:,.2f} (Change: ${change:,.2f}, {change_pct:.2f}%)")
    
    # Check if any PM files were processed successfully
    if pm_totals:
        # Calculate average of PM totals (to approximate the revised total)
        avg_total = sum(pm_totals.values()) / len(pm_totals)
        print(f"\nAverage PM Total: ${avg_total:,.2f}")
        
        # Calculate overall change
        if original_total:
            overall_change = avg_total - original_total
            change_pct = overall_change / original_total * 100
            print(f"Estimated Change: ${overall_change:,.2f} ({change_pct:.2f}%)")
    else:
        print("No PM allocation data could be extracted.")

if __name__ == "__main__":
    main()