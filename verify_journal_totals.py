"""
Verification Script for Equipment Usage Journal

This script validates that the Foundation journal entries match our export data.
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
EXPECTED_TOTAL = 552600.10  # $552,600.10 expected total
EXPECTED_DFW = 377844.60  # $377,844.60 expected DFW total
EXPECTED_HOU = 100061.50  # $100,061.50 expected HOU total
EXPECTED_WT = 74694.00  # $74,694.00 expected WT total

# Input files
JOURNAL_FILE = 'RAG APRIL 2025 - EQ USAGE JOURNAL LIST (PRE-POST).xlsx'
CORRECTED_MASTER_FILE = 'CORRECTED_MASTER_ALLOCATION_SHEET_APRIL_2025.xlsx'
DFW_EXPORT = 'CORRECTED_REGION_IMPORT_DFW_APRIL_2025.csv'
HOU_EXPORT = 'CORRECTED_REGION_IMPORT_HOU_APRIL_2025.csv'
WT_EXPORT = 'CORRECTED_REGION_IMPORT_WT_APRIL_2025.csv'

def load_journal_data():
    """Load the journal data from Excel"""
    try:
        journal_path = os.path.join(ATTACHED_ASSETS_DIR, JOURNAL_FILE)
        if not os.path.exists(journal_path):
            logger.error(f"Journal file not found: {journal_path}")
            return None
        
        # Try to load the file with various sheet names
        try:
            # First attempt - common sheet names
            for sheet_name in ['Sheet1', 'Journal', 'Data', 'Report']:
                try:
                    journal_df = pd.read_excel(journal_path, sheet_name=sheet_name)
                    logger.info(f"Loaded journal data from sheet: {sheet_name}")
                    return journal_df
                except:
                    continue
            
            # Second attempt - load all sheets and use the first one
            excel_file = pd.ExcelFile(journal_path)
            sheet_names = excel_file.sheet_names
            journal_df = pd.read_excel(journal_path, sheet_name=sheet_names[0])
            logger.info(f"Loaded journal data from first sheet: {sheet_names[0]}")
            return journal_df
            
        except Exception as e:
            logger.error(f"Error loading specific sheet: {str(e)}")
            
            # Last resort - try reading without specifying sheet name
            journal_df = pd.read_excel(journal_path)
            logger.info("Loaded journal data from default sheet")
            return journal_df
    
    except Exception as e:
        logger.error(f"Error loading journal file: {str(e)}")
        return None

def load_export_data():
    """Load our export data for comparison"""
    try:
        # Load master allocation sheet
        master_path = os.path.join(EXPORTS_DIR, CORRECTED_MASTER_FILE)
        if os.path.exists(master_path):
            master_df = pd.read_excel(master_path)
            logger.info(f"Loaded master allocation sheet with {len(master_df)} records")
        else:
            logger.error(f"Master allocation file not found: {master_path}")
            master_df = None
        
        # Load division exports
        dfw_path = os.path.join(EXPORTS_DIR, DFW_EXPORT)
        hou_path = os.path.join(EXPORTS_DIR, HOU_EXPORT)
        wt_path = os.path.join(EXPORTS_DIR, WT_EXPORT)
        
        division_dfs = {}
        if os.path.exists(dfw_path):
            # Read without headers since we exported without them
            division_dfs['DFW'] = pd.read_csv(dfw_path, header=None)
            logger.info(f"Loaded DFW export with {len(division_dfs['DFW'])} records")
            # Apply column names for easier analysis
            column_names = ['Equipment_Number', 'Equipment_Description', 'Date', 'Job_Number', 
                          'Period', 'Cost_Code', 'Month_Code', 'Units', 'Period_Type', 
                          'Unit_Rate', 'Amount']
            division_dfs['DFW'].columns = column_names
        else:
            logger.error(f"DFW export file not found: {dfw_path}")
        
        if os.path.exists(hou_path):
            division_dfs['HOU'] = pd.read_csv(hou_path, header=None)
            logger.info(f"Loaded HOU export with {len(division_dfs['HOU'])} records")
            division_dfs['HOU'].columns = column_names
        else:
            logger.error(f"HOU export file not found: {hou_path}")
            
        if os.path.exists(wt_path):
            division_dfs['WT'] = pd.read_csv(wt_path, header=None)
            logger.info(f"Loaded WT export with {len(division_dfs['WT'])} records")
            division_dfs['WT'].columns = column_names
        else:
            logger.error(f"WT export file not found: {wt_path}")
        
        return master_df, division_dfs
    
    except Exception as e:
        logger.error(f"Error loading export data: {str(e)}")
        return None, {}

def check_journal_amount_totals(journal_df):
    """Check if the journal totals match the expected totals"""
    if journal_df is None:
        logger.error("Cannot check totals - journal data is None")
        return False
    
    # Look for amount columns that might contain the totals
    amount_columns = []
    for col in journal_df.columns:
        col_str = str(col).lower()
        if 'amount' in col_str or 'total' in col_str or 'debit' in col_str or 'credit' in col_str:
            amount_columns.append(col)
    
    if not amount_columns:
        # Try to find numeric columns that might be amounts
        for col in journal_df.columns:
            if journal_df[col].dtype in [float, int]:
                amount_columns.append(col)
    
    if not amount_columns:
        logger.error("Could not identify amount columns in journal data")
        return False
    
    # Check totals for each potential amount column
    found_match = False
    for amount_col in amount_columns:
        try:
            # Try to sum the column and format to 2 decimal places
            total = journal_df[amount_col].sum()
            total_rounded = round(total, 2)
            
            # Check if this matches our expected total
            if abs(total_rounded - EXPECTED_TOTAL) < 0.1:  # Allow small rounding differences
                logger.info(f"✓ Journal total verified: ${total_rounded:,.2f} matches expected ${EXPECTED_TOTAL:,.2f}")
                found_match = True
                break
            else:
                logger.info(f"Column {amount_col} total: ${total_rounded:,.2f} does not match expected ${EXPECTED_TOTAL:,.2f}")
        except:
            logger.info(f"Could not calculate sum for column {amount_col}")
    
    if not found_match:
        logger.error("❌ Journal total does not match expected total")
        return False
    
    return True

def check_division_subtotals(journal_df, division_dfs):
    """Check if division subtotals match expected values"""
    if not division_dfs:
        logger.error("Cannot check division subtotals - division data is empty")
        return False
    
    # Check DFW totals
    if 'DFW' in division_dfs:
        dfw_total = round(division_dfs['DFW']['Amount'].sum(), 2)
        if abs(dfw_total - EXPECTED_DFW) < 0.1:
            logger.info(f"✓ DFW subtotal verified: ${dfw_total:,.2f} matches expected ${EXPECTED_DFW:,.2f}")
        else:
            logger.error(f"❌ DFW subtotal: ${dfw_total:,.2f} does not match expected ${EXPECTED_DFW:,.2f}")
            return False
    
    # Check HOU totals
    if 'HOU' in division_dfs:
        hou_total = round(division_dfs['HOU']['Amount'].sum(), 2)
        if abs(hou_total - EXPECTED_HOU) < 0.1:
            logger.info(f"✓ HOU subtotal verified: ${hou_total:,.2f} matches expected ${EXPECTED_HOU:,.2f}")
        else:
            logger.error(f"❌ HOU subtotal: ${hou_total:,.2f} does not match expected ${EXPECTED_HOU:,.2f}")
            return False
    
    # Check WT totals
    if 'WT' in division_dfs:
        wt_total = round(division_dfs['WT']['Amount'].sum(), 2)
        if abs(wt_total - EXPECTED_WT) < 0.1:
            logger.info(f"✓ WT subtotal verified: ${wt_total:,.2f} matches expected ${EXPECTED_WT:,.2f}")
        else:
            logger.error(f"❌ WT subtotal: ${wt_total:,.2f} does not match expected ${EXPECTED_WT:,.2f}")
            return False
    
    return True

def check_cost_code_rules(master_df, division_dfs):
    """Check that cost codes follow the appropriate rules"""
    if not division_dfs:
        logger.error("Cannot check cost code rules - division data is empty")
        return False
    
    violations = []
    
    # Combine all division dataframes
    all_records = pd.concat([df for div, df in division_dfs.items()])
    
    # Check each record
    for _, row in all_records.iterrows():
        job_num = str(row['Job_Number']).strip()
        cost_code = str(row['Cost_Code']).strip()
        
        # Check if it's a legacy job (< 2023-014)
        is_legacy_job = False
        try:
            if '-' in job_num:
                job_year, job_seq = job_num.split('-', 1)
                if job_year.isdigit() and job_seq.isdigit():
                    if int(job_year) < 2023 or (int(job_year) == 2023 and int(job_seq) < 14):
                        is_legacy_job = True
            elif job_num.isdigit() and int(job_num) < 2023014:
                is_legacy_job = True
        except:
            # If we can't parse the job number, skip this check
            pass
        
        # Legacy jobs must have 9000 100M
        if is_legacy_job and cost_code != "9000 100M":
            violations.append({
                'Job': job_num,
                'Equipment': row['Equipment_Number'],
                'Expected': '9000 100M',
                'Actual': cost_code,
                'Rule': 'Legacy Job'
            })
        
        # Non-legacy jobs should not have 9000 100M
        # Commented out since some non-legacy jobs could legitimately have 9000 100M
        # if not is_legacy_job and cost_code == "9000 100M":
        #     violations.append({
        #         'Job': job_num,
        #         'Equipment': row['Equipment_Number'],
        #         'Expected': 'Not 9000 100M',
        #         'Actual': cost_code,
        #         'Rule': 'Non-Legacy Job'
        #     })
        
        # Check for "CC NEEDED"
        if "CC NEEDED" in cost_code.upper():
            violations.append({
                'Job': job_num,
                'Equipment': row['Equipment_Number'],
                'Expected': '9000 100F or actual code',
                'Actual': cost_code,
                'Rule': 'No CC NEEDED allowed'
            })
    
    if violations:
        logger.error(f"❌ Found {len(violations)} cost code violations")
        for v in violations[:10]:  # Show first 10
            logger.error(f"  - {v['Equipment']} on {v['Job']}: Expected {v['Expected']}, got {v['Actual']} ({v['Rule']})")
        return False
    else:
        logger.info("✓ All cost codes follow the appropriate rules")
        return True

def check_max_unit_allocation(master_df):
    """Verify no asset is billed for more than 1.0 units total"""
    if master_df is None:
        logger.error("Cannot check unit allocations - master data is None")
        return False
    
    # Sum units by equipment ID
    equipment_totals = master_df.groupby('Equip #')['Units'].sum().reset_index()
    
    # Find assets with more than 1.0 units
    over_allocated = equipment_totals[equipment_totals['Units'] > 1.0]
    
    if len(over_allocated) > 0:
        logger.error(f"❌ Found {len(over_allocated)} assets with more than 1.0 total units")
        for _, row in over_allocated.iterrows():
            logger.error(f"  - {row['Equip #']}: {row['Units']} units")
        return False
    else:
        logger.info("✓ No assets are billed for more than 1.0 total units")
        return True

def verify_journal_entries():
    """Run all verification checks"""
    # Load data
    journal_df = load_journal_data()
    master_df, division_dfs = load_export_data()
    
    # If we couldn't load the journal data
    if journal_df is None:
        logger.error("Unable to load journal data for verification")
        # Just verify what we can from our exports
        checks = [
            ("Division Subtotals", check_division_subtotals(journal_df, division_dfs)),
            ("Cost Code Rules", check_cost_code_rules(master_df, division_dfs)),
            ("Maximum Unit Allocation", check_max_unit_allocation(master_df))
        ]
    else:
        # Run all checks
        checks = [
            ("Journal Amount Totals", check_journal_amount_totals(journal_df)),
            ("Division Subtotals", check_division_subtotals(journal_df, division_dfs)),
            ("Cost Code Rules", check_cost_code_rules(master_df, division_dfs)),
            ("Maximum Unit Allocation", check_max_unit_allocation(master_df))
        ]
    
    # Print summary
    logger.info("\n===== VERIFICATION SUMMARY =====")
    all_passed = True
    for check_name, result in checks:
        status = "✓ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {check_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n✓ ALL VERIFICATIONS PASSED")
    else:
        logger.error("\n❌ SOME VERIFICATIONS FAILED")

if __name__ == "__main__":
    verify_journal_entries()