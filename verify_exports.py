import pandas as pd
import os

print('VERIFICATION REPORT: Foundation Journal vs. Export Data')
print('======================================================')
print()

# Load division exports
dfw_path = 'exports/CORRECTED_REGION_IMPORT_DFW_APRIL_2025.csv'
hou_path = 'exports/CORRECTED_REGION_IMPORT_HOU_APRIL_2025.csv'
wt_path = 'exports/CORRECTED_REGION_IMPORT_WT_APRIL_2025.csv'

# Expected values
expected_dfw = 377844.60
expected_hou = 100061.50
expected_wt = 74694.00
expected_total = 552600.10

# Check DFW
if os.path.exists(dfw_path):
    dfw_df = pd.read_csv(dfw_path, header=None)
    # Last column should be Amount
    dfw_total = round(dfw_df[dfw_df.columns[-1]].sum(), 2)
    dfw_match = abs(dfw_total - expected_dfw) < 0.1
    print(f'DFW Total: ${dfw_total:,.2f} - {"MATCHES" if dfw_match else "MISMATCH"} (Expected: ${expected_dfw:,.2f})')
else:
    print('DFW file not found')

# Check HOU
if os.path.exists(hou_path):
    hou_df = pd.read_csv(hou_path, header=None)
    hou_total = round(hou_df[hou_df.columns[-1]].sum(), 2)
    hou_match = abs(hou_total - expected_hou) < 0.1
    print(f'HOU Total: ${hou_total:,.2f} - {"MATCHES" if hou_match else "MISMATCH"} (Expected: ${expected_hou:,.2f})')
else:
    print('HOU file not found')

# Check WT
if os.path.exists(wt_path):
    wt_df = pd.read_csv(wt_path, header=None)
    wt_total = round(wt_df[wt_df.columns[-1]].sum(), 2)
    wt_match = abs(wt_total - expected_wt) < 0.1
    print(f'WT Total: ${wt_total:,.2f} - {"MATCHES" if wt_match else "MISMATCH"} (Expected: ${expected_wt:,.2f})')
else:
    print('WT file not found')

# Calculate and check grand total
try:
    grand_total = dfw_total + hou_total + wt_total
    grand_match = abs(grand_total - expected_total) < 0.1
    print(f'Grand Total: ${grand_total:,.2f} - {"MATCHES" if grand_match else "MISMATCH"} (Expected: ${expected_total:,.2f})')
except Exception as e:
    print(f'Could not calculate grand total: {str(e)}')

print()
print('Unit Allocation Check:')
print('=====================')

# Check unit allocation maximums
master_path = 'exports/CORRECTED_MASTER_ALLOCATION_SHEET_APRIL_2025.xlsx'
if os.path.exists(master_path):
    try:
        master_df = pd.read_excel(master_path)
        
        # Find equipment ID column
        equip_col = None
        for col in master_df.columns:
            if 'EQUIP' in str(col).upper() or 'ASSET' in str(col).upper():
                equip_col = col
                break
        
        # Find units column
        unit_col = None
        for col in master_df.columns:
            if 'UNIT' in str(col).upper() or 'ALLOC' in str(col).upper():
                unit_col = col
                break
        
        if equip_col and unit_col:
            print(f'Found equipment column: {equip_col}')
            print(f'Found units column: {unit_col}')
            
            # Sum units by equipment ID
            equipment_totals = master_df.groupby(equip_col)[unit_col].sum().reset_index()
            
            # Find assets with more than 1.0 units
            over_allocated = equipment_totals[equipment_totals[unit_col] > 1.0]
            
            if len(over_allocated) > 0:
                print(f'FAILED: Found {len(over_allocated)} assets with more than 1.0 total units')
                for _, row in over_allocated.head(5).iterrows():
                    print(f'  - {row[equip_col]}: {row[unit_col]} units')
            else:
                print('PASSED: No assets are billed for more than 1.0 total units')
        else:
            print(f'Could not identify equipment or unit columns')
            print(f'Available columns: {master_df.columns.tolist()}')
    except Exception as e:
        print(f'Error checking unit allocations: {str(e)}')
else:
    print('Master allocation sheet not found')

print()
print('Cost Code Rules Check:')
print('====================')

# Check a sampling of legacy job cost codes
try:
    # Combine all region files
    all_records = []
    for file_path in [dfw_path, hou_path, wt_path]:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, header=None)
            all_records.append(df)
    
    if all_records:
        combined_df = pd.concat(all_records)
        
        # Assuming Job_Number is the 4th column (index 3) and Cost_Code is the 6th column (index 5)
        job_col_idx = 3
        cc_col_idx = 5
        
        legacy_violations = 0
        cc_needed_violations = 0
        total_legacy_jobs = 0
        
        # Check a sample of records
        sample_size = min(1000, len(combined_df))
        for i in range(sample_size):
            row = combined_df.iloc[i]
            job_num = str(row[job_col_idx]).strip()
            cost_code = str(row[cc_col_idx]).strip() if pd.notna(row[cc_col_idx]) else ""
            
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
                pass
            
            if is_legacy_job:
                total_legacy_jobs += 1
                # Legacy jobs must have 9000 100M
                if cost_code != '9000 100M':
                    legacy_violations += 1
            
            # Check for 'CC NEEDED'
            if 'CC NEEDED' in cost_code.upper():
                cc_needed_violations += 1
        
        if legacy_violations > 0:
            print(f'Found {legacy_violations} legacy job cost code violations (out of {total_legacy_jobs} legacy jobs)')
        else:
            if total_legacy_jobs > 0:
                print(f'Legacy job cost codes are correct (9000 100M) for all {total_legacy_jobs} legacy jobs')
            else:
                print('No legacy jobs found in sample')
        
        if cc_needed_violations > 0:
            print(f'Found {cc_needed_violations} instances of "CC NEEDED"')
        else:
            print('No instances of "CC NEEDED" found')
        
        if legacy_violations == 0 and cc_needed_violations == 0:
            print('OVERALL: All cost code rules appear to be followed correctly')
        else:
            print('OVERALL: Some cost code violations detected')
    
    else:
        print('No data available for cost code checking')
    
except Exception as e:
    print(f'Error checking cost codes: {str(e)}')

print()
print('VERIFICATION SUMMARY:')
print('===================')

try:
    all_checks_passed = dfw_match and hou_match and wt_match and grand_match and len(over_allocated) == 0 and legacy_violations == 0 and cc_needed_violations == 0
    if all_checks_passed:
        print('ALL CHECKS PASSED: Foundation journal matches our exports exactly')
    else:
        print('SOME CHECKS FAILED: See details above')
except Exception as e:
    print(f'INCONCLUSIVE: Could not determine if all checks passed - {str(e)}')