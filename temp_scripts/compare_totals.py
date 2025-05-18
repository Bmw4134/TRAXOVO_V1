import pandas as pd

# Load the original file
try:
    original_file = 'exports/FINALIZED_MASTER_ALLOCATION_SHEET_APRIL_2025.xlsx'
    original_df = pd.read_excel(original_file)
    
    # Calculate division totals
    dfw_total_orig = original_df[original_df['Division'] == 'DFW']['Amount'].sum()
    hou_total_orig = original_df[original_df['Division'] == 'HOU']['Amount'].sum()
    wt_total_orig = original_df[original_df['Division'] == 'WT']['Amount'].sum()
    
    print('ORIGINAL TOTALS:')
    print(f'DFW: ${dfw_total_orig:,.2f}')
    print(f'HOU: ${hou_total_orig:,.2f}')
    print(f'WT: ${wt_total_orig:,.2f}')
    print(f'Combined: ${dfw_total_orig + hou_total_orig + wt_total_orig:,.2f}')
    
    # Load the corrected file
    corrected_file = 'exports/CORRECTED_MASTER_ALLOCATION_SHEET_APRIL_2025.xlsx'
    corrected_df = pd.read_excel(corrected_file)
    
    # Calculate division totals
    dfw_total_corr = corrected_df[corrected_df['Division'] == 'DFW']['Amount'].sum()
    hou_total_corr = corrected_df[corrected_df['Division'] == 'HOU']['Amount'].sum()
    wt_total_corr = corrected_df[corrected_df['Division'] == 'WT']['Amount'].sum()
    
    print('\nCORRECTED TOTALS:')
    print(f'DFW: ${dfw_total_corr:,.2f}')
    print(f'HOU: ${hou_total_corr:,.2f}')
    print(f'WT: ${wt_total_corr:,.2f}')
    print(f'Combined: ${dfw_total_corr + hou_total_corr + wt_total_corr:,.2f}')
    
    # Calculate the difference
    dfw_diff = dfw_total_corr - dfw_total_orig
    hou_diff = hou_total_corr - hou_total_orig
    wt_diff = wt_total_corr - wt_total_orig
    total_diff = (dfw_total_corr + hou_total_corr + wt_total_corr) - (dfw_total_orig + hou_total_orig + wt_total_orig)
    
    print('\nDIFFERENCE (Corrected - Original):')
    print(f'DFW: ${dfw_diff:,.2f}')
    print(f'HOU: ${hou_diff:,.2f}')
    print(f'WT: ${wt_diff:,.2f}')
    print(f'Combined: ${total_diff:,.2f}')
    
except Exception as e:
    print(f'Error: {e}')
