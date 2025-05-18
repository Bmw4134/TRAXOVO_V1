"""
Auto Process PM Allocations

This script focuses on specific PM allocation files to update the base amounts
and generate the required deliverables.
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
MONTH_NAME = 'APRIL'
YEAR = '2025'

# Output file names
FINALIZED_MASTER_ALLOCATION = f"FINALIZED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
MASTER_BILLINGS = f"MASTER_EQUIP_BILLINGS_{MONTH_NAME}_{YEAR}.xlsx"
REGION_IMPORT_PREFIX = "FINAL_REGION_IMPORT_"

# Source files - specifically target the main PM allocation files
PM_FILES = [
    "A.HARDIMO EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx",
    "C.KOCMICK EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx",
    "L. MORALES EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx",
    "S. ALVAREZ EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx"
]

def process_pm_allocations():
    """Process PM allocations and generate deliverables"""
    # Load all PM-specific data
    pm_records = []
    
    # Dictionary to store equipment data by ID
    equipment_dict = {}
    
    # Process each PM file
    for pm_file in PM_FILES:
        file_path = os.path.join(ATTACHED_ASSETS_DIR, pm_file)
        if not os.path.exists(file_path):
            logger.warning(f"PM file not found: {pm_file}")
            continue
            
        try:
            logger.info(f"Processing PM file: {pm_file}")
            
            # Try to find "EQ ALLOCATIONS - ALL DIV" sheet
            sheets_to_try = ["EQ ALLOCATIONS - ALL DIV", "ALLOCATIONS", "Sheet1", "Allocations"]
            df = None
            
            for sheet in sheets_to_try:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet)
                    if not df.empty:
                        logger.info(f"Found data in sheet {sheet}")
                        break
                except:
                    continue
                    
            if df is None or df.empty:
                logger.warning(f"No data found in {pm_file}")
                continue
                
            # Look for columns with EQUIP #, JOB #, COST CODE, UNITS, RATE, AMOUNT
            # The exact column names vary by PM sheet, so we need to search
            equip_col = next((col for col in df.columns if 'EQUIP #' in str(col).upper() or 'EQUIP ID' in str(col).upper()), None)
            job_col = next((col for col in df.columns if 'JOB' in str(col).upper() or 'JOB #' in str(col).upper()), None)
            cost_code_col = next((col for col in df.columns if 'COST CODE' in str(col).upper() or 'CC' in str(col).upper()), None)
            units_col = next((col for col in df.columns if 'UNITS' in str(col).upper() or 'QTY' in str(col).upper() 
                              or 'ALLOCATION' in str(col).upper() or 'REVISION' in str(col).upper()), None)
            rate_col = next((col for col in df.columns if 'RATE' in str(col).upper() or 'UNIT RATE' in str(col).upper()), None)
            amount_col = next((col for col in df.columns if 'AMOUNT' in str(col).upper() or 'TOTAL' in str(col).upper()), None)
            
            if not equip_col or not job_col or (not units_col and not amount_col):
                logger.warning(f"Missing required columns in {pm_file}")
                continue
                
            # Extract rows with equipment IDs
            if equip_col:
                df = df[df[equip_col].notna()]
                
                # Specific column with revisions/allocations used
                rev_col = None
                for col in df.columns:
                    col_str = str(col).upper()
                    if ('REVISION' in col_str or 'ALLOCAT' in col_str) and 'UNIT' in col_str:
                        rev_col = col
                        break
                        
                # If found a specific revision column, use it
                if rev_col and rev_col != units_col:
                    logger.info(f"Using revision column: {rev_col}")
                    units_col = rev_col
                    
                # Process each row
                for idx, row in df.iterrows():
                    if pd.isna(row[equip_col]) or str(row[equip_col]).strip() == "":
                        continue
                        
                    equip_id = str(row[equip_col]).strip()
                    
                    # Skip if no job specified
                    if job_col is None or pd.isna(row[job_col]) or str(row[job_col]).strip() == "":
                        continue
                        
                    job = str(row[job_col]).strip()
                    
                    # Get cost code if available
                    cost_code = ""
                    if cost_code_col and not pd.isna(row[cost_code_col]):
                        cost_code = str(row[cost_code_col]).strip()
                        
                    # Get units and rate
                    units = 0
                    if units_col and not pd.isna(row[units_col]):
                        try:
                            units = float(row[units_col])
                        except:
                            units = 0
                            
                    rate = 0
                    if rate_col and not pd.isna(row[rate_col]):
                        try:
                            rate = float(row[rate_col])
                        except:
                            rate = 0
                            
                    # Calculate amount if not provided
                    amount = 0
                    if amount_col and not pd.isna(row[amount_col]):
                        try:
                            amount = float(row[amount_col])
                        except:
                            amount = 0
                    elif units > 0 and rate > 0:
                        amount = units * rate
                        
                    # Skip if no amount
                    if amount <= 0:
                        continue
                        
                    # Store equipment data
                    key = f"{equip_id}_{job}_{cost_code}"
                    equipment_dict[key] = {
                        'equip_id': equip_id,
                        'job': job,
                        'cost_code': cost_code,
                        'units': units,
                        'rate': rate,
                        'amount': amount,
                        'pm': os.path.splitext(pm_file)[0]  # PM name without extension
                    }
                    
            logger.info(f"Extracted {len(equipment_dict)} unique records from all PM files")
                
        except Exception as e:
            logger.error(f"Error processing {pm_file}: {str(e)}")
            
    # Convert equipment dictionary to dataframe
    if equipment_dict:
        pm_data = pd.DataFrame(list(equipment_dict.values()))
        logger.info(f"Final PM allocation dataframe has {len(pm_data)} records")
        
        # Calculate total
        if 'amount' in pm_data.columns:
            pm_total = pm_data['amount'].sum()
            logger.info(f"Total PM amount: ${pm_total:,.2f}")
            
        # Generate CSV with PM-specific allocations
        pm_data['pm'] = pm_data['pm'].fillna('Unknown')
        
        # Generate division data based on job number patterns
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
                
        pm_data['division'] = pm_data['job'].apply(assign_division)
        
        # 1. Generate FINALIZED MASTER ALLOCATION SHEET
        # Enhance with more columns from base data if needed
        export_df = pm_data.copy()
        
        # Add any missing columns expected in the output
        for col in ['date', 'description', 'phase', 'frequency']:
            if col not in export_df.columns:
                export_df[col] = ''
                
        # Rename columns for the export
        column_mapping = {
            'equip_id': 'Equip #',
            'description': 'Equipment Description',
            'date': 'Date',
            'job': 'Job',
            'phase': 'Phase',
            'cost_code': 'Cost Code',
            'units': 'Units',
            'frequency': 'Frequency',
            'rate': 'Rate',
            'amount': 'Amount',
            'division': 'Division',
            'pm': 'PM Allocation'
        }
        
        export_df.rename(columns=column_mapping, inplace=True)
        
        # Ensure exports directory exists
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        
        # Write to Excel
        master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
        export_df.to_excel(master_allocation_path, index=False, sheet_name='Master Allocation')
        logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
        
        # 2. Generate MASTER BILLINGS SHEET (same data, different name)
        master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
        export_df.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
        logger.info(f"Generated Master Billings Sheet: {master_billing_path}")
        
        # 3. Generate FINAL REGION IMPORT FILES
        for division in ['DFW', 'WTX', 'HOU']:
            division_data = export_df[export_df['Division'] == division].copy()
            
            if not division_data.empty:
                # Create export dataframe
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
                
                # Format date column - use today's date if missing
                if 'Date' in import_df.columns:
                    if import_df['Date'].isna().all() or (import_df['Date'] == '').all():
                        import_df['Date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
                    else:
                        import_df['Date'] = pd.to_datetime(import_df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                
                # Write CSV
                output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
                import_df.to_csv(output_path, index=False)
                
                division_total = import_df['Amount'].sum()
                logger.info(f"Generated {division} Import File: {output_path} with {len(import_df)} records - Total: ${division_total:,.2f}")
        
        return True
    else:
        logger.error("No equipment data found in PM files")
        return False
            
if __name__ == "__main__":
    process_pm_allocations()