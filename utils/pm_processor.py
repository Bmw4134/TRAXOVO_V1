"""
PM Allocation Processing Functions

This module contains functions for processing PM allocation data and
preserving formulas from the monthly billing workbook.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side


def process_pm_allocation():
    """
    Process PM allocation sheets and apply formulas from the monthly billing workbook.
    Returns paths to the generated files.
    """
    print("Processing PM allocation sheets...")
    
    # Directories
    source_dir = 'attached_assets'
    output_dir = 'exports/pm_allocations'
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all PM allocation files
    allocation_files = []
    for filename in os.listdir(source_dir):
        if 'EQMO. BILLING ALLOCATIONS - APRIL 2025' in filename and filename.endswith('.xlsx'):
            allocation_files.append(os.path.join(source_dir, filename))
    
    print(f"Found {len(allocation_files)} PM allocation files")
    
    # Create result dict
    result = {
        'allocation_files': [],
        'summary_file': None,
        'template_file': None
    }
    
    # Process each file
    for file_path in allocation_files:
        try:
            basename = os.path.basename(file_path)
            
            # Extract job number if possible
            job_number = 'Unknown'
            if basename.startswith('202') and '-' in basename[:8]:
                job_number = basename[:7]  # Extract like 2024-030
            
            # Load data
            df = pd.read_excel(file_path)
            
            # Create output file name
            output_filename = f"{job_number}_PM_ALLOCATION.xlsx"
            output_path = os.path.join(output_dir, output_filename)
            
            # Save to Excel
            df.to_excel(output_path, index=False)
            
            # Add to result list
            result['allocation_files'].append(output_path)
            
            print(f"Processed {basename} -> {output_filename}")
            
        except Exception as e:
            print(f"Error processing {os.path.basename(file_path)}: {str(e)}")
    
    # Create summary file
    if result['allocation_files']:
        try:
            summary_data = []
            
            for file_path in result['allocation_files']:
                # Load data
                df = pd.read_excel(file_path)
                
                # Extract job number from filename
                basename = os.path.basename(file_path)
                job_number = basename.split('_')[0] if '_' in basename else 'Unknown'
                
                # Calculate summary statistics
                equipment_count = len(df)
                
                # Find possible amount/total column
                amount_col = None
                for col in df.columns:
                    col_str = str(col).upper()
                    if 'AMOUNT' in col_str or 'TOTAL' in col_str:
                        amount_col = col
                        break
                
                total_amount = 0
                if amount_col:
                    try:
                        total_amount = df[amount_col].sum()
                    except:
                        pass
                
                summary_data.append({
                    'Job Number': job_number,
                    'Equipment Count': equipment_count, 
                    'Total Amount': total_amount,
                    'Source File': os.path.basename(file_path)
                })
            
            # Create summary DataFrame
            summary_df = pd.DataFrame(summary_data)
            
            # Save summary to Excel
            summary_path = os.path.join(output_dir, "PM_Allocation_Summary.xlsx")
            with pd.ExcelWriter(summary_path) as writer:
                summary_df.to_excel(writer, sheet_name="Summary", index=False)
            
            result['summary_file'] = summary_path
            print(f"Created summary file: {os.path.basename(summary_path)}")
            
        except Exception as e:
            print(f"Error creating summary file: {str(e)}")
    
    # Extract formulas from monthly billing workbook
    monthly_billing_file = os.path.join(source_dir, "EQ MONTHLY BILLINGS WORKING SPREADSHEET - APRIL 2025.xlsx")
    
    if os.path.exists(monthly_billing_file):
        try:
            print(f"Analyzing monthly billing workbook: {os.path.basename(monthly_billing_file)}")
            
            # Create simplified template file with key structure information
            template_path = os.path.join(output_dir, "Monthly_Billing_Template.xlsx")
            
            # Extract sheet names
            xl = pd.ExcelFile(monthly_billing_file)
            sheet_names = xl.sheet_names
            print(f"Found {len(sheet_names)} sheets in monthly billing workbook")
            
            # Create a workbook for the template
            wb = openpyxl.Workbook()
            
            # Remove default sheet
            if 'Sheet' in wb.sheetnames:
                wb.remove(wb['Sheet'])
            
            # Create summary sheet
            summary = wb.create_sheet("Summary")
            summary.cell(row=1, column=1).value = "Monthly Billing Template"
            summary.cell(row=1, column=1).font = Font(bold=True, size=14)
            
            # Add sheet list to summary
            summary.cell(row=3, column=1).value = "Sheet Name"
            summary.cell(row=3, column=1).font = Font(bold=True)
            
            summary.cell(row=3, column=2).value = "Description"
            summary.cell(row=3, column=2).font = Font(bold=True)
            
            # Define key sheets and descriptions
            key_sheets = {
                'M-SELECT': 'SELECT master equipment data',
                'M-RAGLE': 'RAGLE master equipment data',
                'ATOS': 'Asset time on site tracking data',
                'TRKG': 'Truck usage calculation data',
                'DUSG-PT': 'Daily usage for pickup trucks'
            }
            
            # Add key sheets to summary
            row = 4
            for sheet_name in sheet_names:
                summary.cell(row=row, column=1).value = sheet_name
                if sheet_name in key_sheets:
                    summary.cell(row=row, column=2).value = key_sheets[sheet_name]
                row += 1
            
            # Create sample sheets for key sheets only
            for sheet_name in key_sheets:
                if sheet_name in sheet_names:
                    try:
                        # Create a sheet
                        sheet = wb.create_sheet(sheet_name)
                        
                        # Add header
                        sheet.cell(row=1, column=1).value = f"{sheet_name} Structure Template"
                        sheet.cell(row=1, column=1).font = Font(bold=True, size=14)
                        
                        # Read sample data (first 10 rows)
                        sample_df = pd.read_excel(monthly_billing_file, sheet_name=sheet_name, nrows=10)
                        
                        # Add column headers
                        for col_idx, col_name in enumerate(sample_df.columns, 1):
                            sheet.cell(row=3, column=col_idx).value = col_name
                            sheet.cell(row=3, column=col_idx).font = Font(bold=True)
                        
                        print(f"Added structure template for {sheet_name}")
                        
                    except Exception as e:
                        print(f"Error creating template for {sheet_name}: {str(e)}")
            
            # Save the template
            wb.save(template_path)
            result['template_file'] = template_path
            print(f"Created monthly billing template: {os.path.basename(template_path)}")
            
        except Exception as e:
            print(f"Error analyzing monthly billing workbook: {str(e)}")
    
    return result


def create_consolidated_file():
    """
    Create a consolidated file with all PM allocation data.
    This function merges all processed allocation files into one.
    """
    print("Creating consolidated PM allocation file...")
    
    # Directories
    allocation_dir = 'exports/pm_allocations'
    
    # Check if directory exists
    if not os.path.exists(allocation_dir):
        print(f"Allocation directory not found: {allocation_dir}")
        return None
    
    # Find all allocation files
    allocation_files = []
    for filename in os.listdir(allocation_dir):
        if filename.endswith('.xlsx') and 'PM_ALLOCATION' in filename:
            allocation_files.append(os.path.join(allocation_dir, filename))
    
    print(f"Found {len(allocation_files)} allocation files to consolidate")
    
    if not allocation_files:
        print("No allocation files found for consolidation")
        return None
    
    try:
        # Read and concatenate all data
        dfs = []
        
        for file_path in allocation_files:
            try:
                # Extract job number from filename
                basename = os.path.basename(file_path)
                job_number = basename.split('_')[0] if '_' in basename else 'Unknown'
                
                # Read data
                df = pd.read_excel(file_path)
                
                # Add job number if not present
                if 'Job Number' not in df.columns:
                    df['Job Number'] = job_number
                
                dfs.append(df)
                print(f"Added data from {basename}")
                
            except Exception as e:
                print(f"Error reading {os.path.basename(file_path)}: {str(e)}")
        
        if not dfs:
            print("No data loaded from allocation files")
            return None
        
        # Concatenate all DataFrames
        consolidated_df = pd.concat(dfs, ignore_index=True)
        print(f"Consolidated {len(consolidated_df)} rows of data")
        
        # Save to Excel and CSV
        output_excel = os.path.join(allocation_dir, "FINAL_PM_ALLOCATION_DATA.xlsx")
        output_csv = os.path.join(allocation_dir, "FINAL_PM_ALLOCATION_DATA.csv")
        
        consolidated_df.to_excel(output_excel, index=False)
        consolidated_df.to_csv(output_csv, index=False)
        
        print(f"Saved consolidated data to Excel: {os.path.basename(output_excel)}")
        print(f"Saved consolidated data to CSV: {os.path.basename(output_csv)}")
        
        return {
            'excel': output_excel,
            'csv': output_csv,
            'count': len(consolidated_df)
        }
        
    except Exception as e:
        print(f"Error creating consolidated file: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Process all PM allocation files
    result = process_pm_allocation()
    
    # Create consolidated file
    consolidated = create_consolidated_file()
    
    print("Processing complete!")