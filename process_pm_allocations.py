"""
Process PM Allocations and Incorporate Custom Formulas

This script extracts the key formulas from the monthly billing spreadsheet
and applies them to the processed PM allocation data.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side


def create_formula_template():
    """
    Create a template workbook with the key formulas from the monthly billing spreadsheet.
    """
    print("Creating formula template for PM allocations...")
    
    # Source file path
    source_file = 'attached_assets/EQ MONTHLY BILLINGS WORKING SPREADSHEET - APRIL 2025.xlsx'
    
    # Check if source file exists
    if not os.path.exists(source_file):
        print(f"Source file not found: {source_file}")
        return False
    
    # Output directory
    output_dir = 'exports/pm_templates'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create new workbook
    wb = openpyxl.Workbook()
    
    # Remove default sheet
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb['Sheet'])
    
    # Load source workbook to extract formulas
    try:
        print(f"Loading source workbook: {source_file}")
        source_wb = openpyxl.load_workbook(source_file, data_only=False)
        
        # List of important sheets to process
        key_sheets = ['M-SELECT', 'M-RAGLE', 'ATOS']
        
        # Create sheets and copy headers and key formulas
        for sheet_name in key_sheets:
            if sheet_name in source_wb.sheetnames:
                print(f"Processing sheet: {sheet_name}")
                
                # Create sheet in new workbook
                new_sheet = wb.create_sheet(sheet_name)
                
                # Get source sheet
                source_sheet = source_wb[sheet_name]
                
                # Copy headers (first 5 rows)
                for row in range(1, 6):
                    for col in range(1, min(30, source_sheet.max_column + 1)):
                        source_cell = source_sheet.cell(row=row, column=col)
                        new_cell = new_sheet.cell(row=row, column=col)
                        
                        # Copy value and style
                        new_cell.value = source_cell.value
                        
                        # Apply basic formatting
                        if source_cell.font and source_cell.font.bold:
                            new_cell.font = Font(bold=True)
                
                # Find and copy key formulas
                formula_count = 0
                for row in range(1, min(50, source_sheet.max_row + 1)):
                    for col in range(1, min(30, source_sheet.max_column + 1)):
                        source_cell = source_sheet.cell(row=row, column=col)
                        
                        # Check if cell contains a formula
                        if source_cell.formula:
                            new_cell = new_sheet.cell(row=row, column=col)
                            formula = source_cell.formula
                            
                            # Save the formula
                            new_cell.value = f"={formula}"
                            formula_count += 1
                            
                            # Print first few formulas for verification
                            if formula_count <= 5:
                                print(f"  - Formula at {get_column_letter(col)}{row}: {formula[:50]}...")
                
                print(f"  - Copied {formula_count} formulas from {sheet_name}")
        
        # Save the template
        output_file = os.path.join(output_dir, "PM_Formula_Template.xlsx")
        wb.save(output_file)
        print(f"Formula template saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"Error creating formula template: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def consolidate_pm_allocation_data():
    """
    Consolidate the processed PM allocation data
    """
    print("\nConsolidating PM allocation data...")
    
    # Directory with PM allocation files
    allocation_dir = 'exports/pm_allocations'
    
    # Output directory
    output_dir = 'exports/pm_processed'
    os.makedirs(output_dir, exist_ok=True)
    
    # Find the consolidated data file
    consolidated_file = os.path.join(allocation_dir, 'FINAL_PM_ALLOCATION_DATA.xlsx')
    
    if not os.path.exists(consolidated_file):
        print(f"Consolidated data file not found: {consolidated_file}")
        return False
    
    try:
        # Read the consolidated data
        print(f"Reading consolidated data from: {consolidated_file}")
        df = pd.read_excel(consolidated_file)
        
        # Create a pivot table by job number
        print("Creating pivot table by job number...")
        
        # Try to identify job number column
        job_col = None
        for col in df.columns:
            if 'JOB' in str(col).upper() and 'NUMBER' in str(col).upper():
                job_col = col
                break
        
        if job_col is None:
            print("Could not identify job number column")
            # Try using the second column as a fallback
            if len(df.columns) >= 2:
                job_col = df.columns[1]
                print(f"Using {job_col} as job number column")
            else:
                print("Not enough columns to identify job number")
                return False
        
        # Create a workbook to store the pivot data
        wb = openpyxl.Workbook()
        
        # Remove default sheet
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])
        
        # Create summary sheet
        summary_sheet = wb.create_sheet("Summary")
        
        # Add headers to summary sheet
        headers = ["Job Number", "Equipment Count", "Total Hours", "Total Amount"]
        for col, header in enumerate(headers, 1):
            cell = summary_sheet.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True)
        
        # Group the data by job number
        try:
            job_groups = df.groupby(job_col)
            print(f"Found {len(job_groups)} job groups")
            
            # Process each job group
            row = 2  # Start from row 2 in summary sheet
            for job_number, group in job_groups:
                print(f"Processing job: {job_number}")
                
                # Create a sheet for this job
                sheet_name = f"Job-{job_number}"
                if len(sheet_name) > 31:  # Excel has a 31 character limit for sheet names
                    sheet_name = sheet_name[:31]
                
                job_sheet = wb.create_sheet(sheet_name)
                
                # Add job header
                job_sheet.cell(row=1, column=1).value = f"Job {job_number} - Equipment Allocations"
                job_sheet.cell(row=1, column=1).font = Font(bold=True, size=14)
                
                # Add column headers
                for col, header in enumerate(group.columns, 1):
                    cell = job_sheet.cell(row=3, column=col)
                    cell.value = header
                    cell.font = Font(bold=True)
                
                # Add data rows
                for i, (_, data_row) in enumerate(group.iterrows(), 4):
                    for col, value in enumerate(data_row, 1):
                        job_sheet.cell(row=i, column=col).value = value
                
                # Add to summary
                equipment_count = len(group)
                
                # Try to find hours and amount columns
                hours_col = None
                amount_col = None
                
                for col in group.columns:
                    col_upper = str(col).upper()
                    if 'HOUR' in col_upper or 'HRS' in col_upper:
                        hours_col = col
                    elif 'AMOUNT' in col_upper or 'TOTAL' in col_upper or '$' in col_upper:
                        amount_col = col
                
                # Calculate totals
                total_hours = 0
                if hours_col:
                    total_hours = group[hours_col].sum()
                
                total_amount = 0
                if amount_col:
                    total_amount = group[amount_col].sum()
                
                # Add to summary sheet
                summary_sheet.cell(row=row, column=1).value = job_number
                summary_sheet.cell(row=row, column=2).value = equipment_count
                summary_sheet.cell(row=row, column=3).value = total_hours
                summary_sheet.cell(row=row, column=4).value = total_amount
                
                # Format amount as currency
                summary_sheet.cell(row=row, column=4).number_format = '$#,##0.00'
                
                row += 1
        
        except Exception as e:
            print(f"Error processing job groups: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Save the consolidated workbook
        output_file = os.path.join(output_dir, f"PM_Processed_Data_{datetime.now().strftime('%Y%m%d')}.xlsx")
        wb.save(output_file)
        print(f"Consolidated data saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"Error consolidating PM allocation data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("=== PM Allocation Formula Preservation ===")
    
    # Create formula template from source workbook
    create_formula_template()
    
    # Consolidate PM allocation data
    consolidate_pm_allocation_data()
    
    print("\nProcessing complete!")


if __name__ == "__main__":
    main()