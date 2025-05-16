"""
Direct PM Allocation Processing for Urgent Need

This is a simplified processor to extract the key data from EQMO allocation files
"""
import os
import pandas as pd
import glob
import shutil
from datetime import datetime

# Make sure the export directory exists
os.makedirs('exports/pm_allocations', exist_ok=True)

# Find all the EQMO PM Billing files with April 2025 in the name
pm_files = glob.glob('attached_assets/*EQMO*APRIL*2025*.xlsx')

# Also add the main working spreadsheet
monthly_billing_file = 'attached_assets/EQ MONTHLY BILLINGS WORKING SPREADSHEET - APRIL 2025.xlsx'
if os.path.exists(monthly_billing_file):
    pm_files.append(monthly_billing_file)
print(f"Found {len(pm_files)} PM allocation files")

# Process the files
for file_path in pm_files:
    filename = os.path.basename(file_path)
    print(f"\nProcessing: {filename}")
    
    # Extract job number from filename if possible
    job_id = "Unknown"
    for part in filename.split():
        if part.startswith('202') and '-' in part:
            job_id = part
            break
    
    # Simply copy the file to the exports directory with a clear name
    dest_file = f"exports/pm_allocations/{job_id}_PM_ALLOCATION_{datetime.now().strftime('%H%M%S')}.xlsx"
    shutil.copy(file_path, dest_file)
    print(f"Exported to: {dest_file}")

# Find and process the specific "final revision" file which is the most important
final_file = None
for file in pm_files:
    if "FINAL REVISIONS" in file.upper():
        final_file = file
        break

if final_file:
    print(f"\nExtracting data from final revision file: {os.path.basename(final_file)}")
    
    try:
        # Extract the main data sheet
        xls = pd.ExcelFile(final_file)
        main_sheet = None
        for sheet in xls.sheet_names:
            if 'EQ ALLOCATIONS' in sheet.upper() or 'ALL DIV' in sheet.upper():
                main_sheet = sheet
                break
        
        if not main_sheet and 'ALL' in xls.sheet_names:
            main_sheet = 'ALL'
        
        if main_sheet:
            print(f"Using sheet: {main_sheet}")
            df = pd.read_excel(final_file, sheet_name=main_sheet)
            
            # Save to a clean CSV format for easy processing
            csv_output = f"exports/pm_allocations/FINAL_PM_ALLOCATION_DATA.csv"
            df.to_csv(csv_output, index=False)
            print(f"Extracted main data to CSV: {csv_output}")
            
            # Also save as Excel
            xlsx_output = f"exports/pm_allocations/FINAL_PM_ALLOCATION_DATA.xlsx"
            df.to_excel(xlsx_output, index=False)
            print(f"Extracted main data to Excel: {xlsx_output}")
    except Exception as e:
        print(f"Error extracting data: {str(e)}")

print("\nProcessing complete!")
print(f"All files saved to: exports/pm_allocations/")