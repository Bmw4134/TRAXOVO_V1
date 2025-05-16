"""
Quick PM Processor - Formula Extractor

This script quickly extracts the key formulas and structure from the monthly
billing workbook without processing the entire workbook.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

def process_monthly_worksheet():
    """Extract key information from the monthly billing workbook"""
    print("Extracting key formulas from monthly billing workbook...")
    
    # Source and output paths
    source_file = 'attached_assets/EQ MONTHLY BILLINGS WORKING SPREADSHEET - APRIL 2025.xlsx'
    output_dir = 'exports/pm_formula_extraction'
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if source file exists
    if not os.path.exists(source_file):
        print(f"Source file not found: {source_file}")
        return False
    
    try:
        # Load using pandas for quicker processing
        print(f"Reading workbook structure: {source_file}")
        xl = pd.ExcelFile(source_file)
        sheet_names = xl.sheet_names
        print(f"Found {len(sheet_names)} sheets: {', '.join(sheet_names[:5])}...")
        
        # Create a summary CSV file with sheet information
        summary_data = []
        key_sheets = ['M-SELECT', 'M-RAGLE', 'ATOS', 'TRKG', 'DUSG-PT']
        
        for sheet_name in key_sheets:
            if sheet_name in sheet_names:
                # Read a sample of the sheet (first 10 rows)
                try:
                    df = pd.read_excel(source_file, sheet_name=sheet_name, nrows=10)
                    row_count = 10  # We only read 10 rows for quick analysis
                    col_count = len(df.columns)
                    
                    # Identify potential formula columns
                    formula_indicators = []
                    for col in df.columns:
                        col_str = str(col).upper()
                        if 'SUM' in col_str or 'TOTAL' in col_str or '=' in col_str:
                            formula_indicators.append(str(col))
                    
                    # Get first 5 column headers for reference
                    first_cols = [str(col) for col in df.columns[:5]]
                    
                    summary_data.append({
                        'Sheet Name': sheet_name,
                        'Sample Row Count': row_count,
                        'Column Count': col_count,
                        'Potential Formula Columns': ', '.join(formula_indicators[:3]),
                        'Sample Column Headers': ', '.join(first_cols)
                    })
                    
                    print(f"Processed sheet: {sheet_name} - Found {len(formula_indicators)} potential formula columns")
                    
                    # Save a sample of this sheet to CSV for reference
                    sample_csv = os.path.join(output_dir, f"{sheet_name}_SAMPLE.csv")
                    df.to_csv(sample_csv, index=False)
                    print(f"  Sample saved to: {sample_csv}")
                    
                except Exception as e:
                    print(f"Error reading sheet {sheet_name}: {str(e)}")
        
        # Create a summary CSV
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_csv = os.path.join(output_dir, "Monthly_Billing_Structure.csv")
            summary_df.to_csv(summary_csv, index=False)
            print(f"\nWorkbook structure summary saved to: {summary_csv}")
        
        # Extract job-specific allocation data from the processed PM files
        print("\nExtracting job allocations from previously processed PM files...")
        
        allocation_dir = 'exports/pm_allocations'
        final_data_file = os.path.join(allocation_dir, 'FINAL_PM_ALLOCATION_DATA.xlsx')
        
        if os.path.exists(final_data_file):
            try:
                # Read the final allocation data
                allocation_df = pd.read_excel(final_data_file)
                print(f"Read allocation data: {len(allocation_df)} rows")
                
                # Identify job number column
                job_col = None
                for col in allocation_df.columns:
                    if 'JOB' in str(col).upper() and 'NUMBER' in str(col).upper():
                        job_col = col
                        break
                
                if job_col:
                    # Get distinct job numbers
                    job_numbers = allocation_df[job_col].unique()
                    print(f"Found {len(job_numbers)} distinct job numbers")
                    
                    # Create a job summary
                    job_summary = []
                    for job in job_numbers:
                        job_data = allocation_df[allocation_df[job_col] == job]
                        
                        # Try to find amount column
                        amount_col = None
                        for col in allocation_df.columns:
                            if 'AMOUNT' in str(col).upper() or 'TOTAL' in str(col).upper():
                                amount_col = col
                                break
                        
                        job_total = 0
                        if amount_col:
                            job_total = job_data[amount_col].sum()
                        
                        job_summary.append({
                            'Job Number': job,
                            'Equipment Count': len(job_data),
                            'Total Amount': job_total
                        })
                    
                    # Save job summary
                    job_summary_df = pd.DataFrame(job_summary)
                    job_summary_csv = os.path.join(output_dir, "Job_Allocation_Summary.csv")
                    job_summary_df.to_csv(job_summary_csv, index=False)
                    print(f"Job allocation summary saved to: {job_summary_csv}")
                
                # Create a simplified formula mapping template
                print("\nCreating a formula mapping template...")
                mapping_data = []
                
                # Define the structure of key formulas based on analysis
                key_formula_maps = [
                    {'Sheet': 'M-SELECT', 'Formula Type': 'Equipment Hours Allocation', 
                     'Description': 'Allocation of equipment hours by job'},
                    {'Sheet': 'M-RAGLE', 'Formula Type': 'Billing Rate Calculation', 
                     'Description': 'Calculation of billing rates by equipment type'},
                    {'Sheet': 'ATOS', 'Formula Type': 'Asset Time on Site', 
                     'Description': 'Total time spent by asset on each job site'},
                    {'Sheet': 'TRKG', 'Formula Type': 'Truck Usage Calculation', 
                     'Description': 'Calculation of truck usage metrics'},
                    {'Sheet': 'DUSG-PT', 'Formula Type': 'Daily Usage Pickup Trucks', 
                     'Description': 'Daily usage metrics for pickup trucks'}
                ]
                
                for formula_map in key_formula_maps:
                    mapping_data.append(formula_map)
                
                # Save the formula mapping template
                mapping_df = pd.DataFrame(mapping_data)
                mapping_csv = os.path.join(output_dir, "Formula_Mapping_Template.csv")
                mapping_df.to_csv(mapping_csv, index=False)
                print(f"Formula mapping template saved to: {mapping_csv}")
                
            except Exception as e:
                print(f"Error processing allocation data: {str(e)}")
        else:
            print(f"Final allocation data file not found: {final_data_file}")
        
        print("\nQuick processing complete!")
        return True
        
    except Exception as e:
        print(f"Error in quick processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    process_monthly_worksheet()