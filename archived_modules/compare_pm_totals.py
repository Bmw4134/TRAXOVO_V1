"""
Compare PM Totals

This script compares the original total from the RAGLE file with
the PM allocation totals from the revision sheets.
"""
import os
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
ATTACHED_ASSETS_DIR = 'attached_assets'
RAGLE_FILE = 'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm'

def get_original_total():
    """Get the original total from the RAGLE file"""
    ragle_path = os.path.join(ATTACHED_ASSETS_DIR, RAGLE_FILE)
    if not os.path.exists(ragle_path):
        logger.error(f"RAGLE file not found: {ragle_path}")
        return None
    
    try:
        logger.info(f"Loading RAGLE file: {ragle_path}")
        ragle_df = pd.read_excel(ragle_path, sheet_name='Equip Billings')
        logger.info(f"Loaded {len(ragle_df)} records from RAGLE file")
        
        amount_cols = []
        for col in ragle_df.columns:
            if 'Amount' in str(col) or 'AMOUNT' in str(col):
                amount_cols.append(col)
        
        if amount_cols:
            total = ragle_df[amount_cols[0]].sum()
            logger.info(f"Original total from RAGLE file: ${total:,.2f}")
            return total
        else:
            logger.error("No amount column found in RAGLE file")
            return None
    except Exception as e:
        logger.error(f"Error loading RAGLE file: {str(e)}")
        return None

def process_pm_file(file_path):
    """Process a PM allocation file and extract total amount"""
    file_name = os.path.basename(file_path)
    if not os.path.exists(file_path):
        logger.warning(f"PM file not found: {file_name}")
        return 0
    
    try:
        # Try to find relevant sheet
        xlsx = pd.ExcelFile(file_path)
        
        for sheet_name in xlsx.sheet_names:
            sheet_lower = sheet_name.lower()
            if any(keyword in sheet_lower for keyword in ['allocation', 'eq', 'billing']):
                try:
                    logger.info(f"Checking sheet {sheet_name} in {file_name}")
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    if df.empty:
                        continue
                    
                    # Find column containing units and rate or amount
                    unit_cols = []
                    rate_cols = []
                    amount_cols = []
                    revision_cols = []
                    
                    for col in df.columns:
                        col_str = str(col).upper()
                        if any(keyword in col_str for keyword in ['UNIT', 'QTY', 'QUANTITY']):
                            unit_cols.append(col)
                        elif 'RATE' in col_str:
                            rate_cols.append(col)
                        elif any(keyword in col_str for keyword in ['AMOUNT', 'TOTAL']):
                            amount_cols.append(col)
                        elif any(keyword in col_str for keyword in ['REVISION', 'ALLOCAT']):
                            revision_cols.append(col)
                    
                    # Try to use revision columns if found
                    units_col = None
                    for col in revision_cols:
                        # Look for revision columns with units
                        if any(keyword in str(col).upper() for keyword in ['UNIT', 'QTY']):
                            units_col = col
                            break
                    
                    # If no revision column found, use first units column
                    if not units_col and unit_cols:
                        units_col = unit_cols[0]
                    
                    # Try to calculate amount from units and rate
                    if units_col and rate_cols:
                        rate_col = rate_cols[0]
                        
                        # Convert to numeric
                        df[units_col] = pd.to_numeric(df[units_col], errors='coerce').fillna(0)
                        df[rate_col] = pd.to_numeric(df[rate_col], errors='coerce').fillna(0)
                        
                        # Calculate total
                        total = (df[units_col] * df[rate_col]).sum()
                        logger.info(f"Calculated total for {file_name} from {units_col} * {rate_col}: ${total:,.2f}")
                        
                        if total > 0:
                            return total
                    
                    # Try to use amount column directly
                    if amount_cols:
                        amount_col = amount_cols[0]
                        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
                        total = df[amount_col].sum()
                        logger.info(f"Total for {file_name} from {amount_col}: ${total:,.2f}")
                        
                        if total > 0:
                            return total
                
                except Exception as e:
                    logger.error(f"Error processing {sheet_name} in {file_name}: {str(e)}")
        
        logger.warning(f"No valid data found in {file_name}")
        return 0
    
    except Exception as e:
        logger.error(f"Error processing {file_name}: {str(e)}")
        return 0

def main():
    """Main function to compare totals"""
    # Get original total
    original_total = get_original_total()
    
    if original_total is None:
        logger.error("Failed to get original total, cannot continue")
        return
    
    # Process specific PM allocation files for comparison
    pm_files = [
        "EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx",
        "A.HARDIMO EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx",
        "C.KOCMICK EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx",
        "L. MORALES EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx",
        "S. ALVAREZ EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx"
    ]
    
    pm_totals = {}
    for pm_file in pm_files:
        file_path = os.path.join(ATTACHED_ASSETS_DIR, pm_file)
        total = process_pm_file(file_path)
        if total > 0:
            pm_totals[pm_file] = total
    
    # Display results
    print("\n===== COMPARISON OF TOTALS =====")
    print(f"Original Total (RAGLE file): ${original_total:,.2f}")
    print("\nPM Allocation Totals:")
    
    for pm_file, total in pm_totals.items():
        diff = total - original_total
        diff_pct = (diff / original_total) * 100 if original_total else 0
        print(f"- {pm_file}: ${total:,.2f} (Diff: ${diff:,.2f}, {diff_pct:.2f}%)")
    
    # Calculate combined PM total
    combined_pm_total = sum(pm_totals.values())
    if combined_pm_total > 0:
        diff = combined_pm_total - original_total
        diff_pct = (diff / original_total) * 100 if original_total else 0
        print(f"\nCombined PM Total: ${combined_pm_total:,.2f}")
        print(f"Difference from Original: ${diff:,.2f} ({diff_pct:.2f}%)")

if __name__ == "__main__":
    main()