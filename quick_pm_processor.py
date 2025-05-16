"""
Quick PM Allocation Processor - Emergency Version

This script processes the April 2025 PM EQMO allocation files
with minimal processing to get the output quickly.
"""
import os
import pandas as pd
import glob
from datetime import datetime

def process_pm_files():
    # Create output directories
    output_dir = "exports/pm_allocations"
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all April 2025 EQMO files
    pm_files = glob.glob("attached_assets/*APRIL*2025*.xlsx")
    
    print(f"Found {len(pm_files)} PM allocation files")
    
    # Process each file
    results = []
    
    for file_path in pm_files:
        print(f"\nProcessing: {file_path}")
        
        try:
            # Try to load all sheets
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            
            print(f"Found sheets: {sheet_names}")
            
            # Try to find main data sheet
            main_sheet = None
            for sheet in sheet_names:
                if 'ALLOCATION' in sheet.upper() or 'ALL DIV' in sheet.upper():
                    main_sheet = sheet
                    break
            
            if not main_sheet and 'ALL' in sheet_names:
                main_sheet = 'ALL'
            elif not main_sheet and len(sheet_names) > 0:
                main_sheet = sheet_names[0]
            
            if not main_sheet:
                print(f"Error: Could not find a suitable sheet in {file_path}")
                continue
                
            print(f"Using sheet: {main_sheet}")
            
            # Load the sheet
            df = pd.read_excel(file_path, sheet_name=main_sheet)
            
            # Extract basic info
            job_number = "Unknown"
            
            # Try to extract job number from filename
            base_name = os.path.basename(file_path)
            for part in base_name.split():
                if part.startswith('202') and '-' in part:
                    job_number = part
                    break
            
            # Save the sheet directly 
            output_filename = f"{job_number}_PM_Allocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            output_path = os.path.join(output_dir, output_filename)
            
            # Save to Excel
            df.to_excel(output_path, sheet_name='Extracted Data', index=False)
            
            print(f"Saved to: {output_path}")
            
            results.append({
                'job_number': job_number,
                'source_file': file_path,
                'output_file': output_path,
                'rows': len(df),
                'columns': len(df.columns)
            })
        
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Create a summary file
    summary_path = os.path.join(output_dir, f"PM_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    
    # Create summary dataframe
    summary_data = []
    for result in results:
        summary_data.append([
            result['job_number'],
            os.path.basename(result['source_file']),
            os.path.basename(result['output_file']),
            result['rows'],
            result['columns']
        ])
    
    summary_df = pd.DataFrame(
        summary_data,
        columns=['Job Number', 'Source File', 'Output File', 'Rows', 'Columns']
    )
    
    # Save summary
    summary_df.to_excel(summary_path, index=False)
    
    print(f"\nProcessing complete. Summary saved to: {summary_path}")
    print(f"All files saved to: {output_dir}")
    print(f"Total files processed: {len(results)} of {len(pm_files)}")

if __name__ == "__main__":
    process_pm_files()