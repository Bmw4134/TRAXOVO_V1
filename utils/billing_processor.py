"""
Billing Processor Utility

This module handles the processing of monthly billing data from multiple sources,
including SELECT and RAGLE billing files, and applies the formulas from the
EQ MONTHLY BILLINGS WORKING SPREADSHEET.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

class BillingProcessor:
    """Class for processing and combining monthly billing data"""
    
    def __init__(self):
        """Initialize the billing processor"""
        self.source_dir = 'attached_assets'
        self.output_dir = 'exports/billing'
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize file paths
        self.select_file = None
        self.ragle_file = None
        self.monthly_billing_file = None
        
        # Key sheet names in the monthly billing spreadsheet
        self.key_sheets = {
            'M-SELECT': 'SELECT master equipment data',
            'M-RAGLE': 'RAGLE master equipment data',
            'ATOS': 'Asset time on site tracking data',
            'TRKG': 'Truck usage calculation data',
            'DUSG-PT': 'Daily usage for pickup trucks'
        }
        
        # Output files
        self.output_monthly_file = None
        self.output_csv_file = None
        
    def find_source_files(self):
        """Find all source files needed for processing"""
        print("Searching for source files...")
        
        for filename in os.listdir(self.source_dir):
            # Find SELECT billing file
            if 'SELECT' in filename.upper() and 'BILLINGS' in filename.upper() and filename.endswith('.xlsx'):
                self.select_file = os.path.join(self.source_dir, filename)
                print(f"Found SELECT billing file: {filename}")
            
            # Find RAGLE billing file
            elif 'RAGLE' in filename.upper() and 'BILLINGS' in filename.upper() and filename.endswith(('.xlsx', '.xlsm')):
                self.ragle_file = os.path.join(self.source_dir, filename)
                print(f"Found RAGLE billing file: {filename}")
            
            # Find monthly billing working spreadsheet
            elif 'EQ MONTHLY BILLINGS WORKING SPREADSHEET' in filename.upper() and filename.endswith('.xlsx'):
                self.monthly_billing_file = os.path.join(self.source_dir, filename)
                print(f"Found monthly billing spreadsheet: {filename}")
        
        # Check if all required files were found
        if not self.select_file:
            print("WARNING: SELECT billing file not found")
        if not self.ragle_file:
            print("WARNING: RAGLE billing file not found")
        if not self.monthly_billing_file:
            print("WARNING: Monthly billing spreadsheet not found")
        
        return (self.select_file is not None and 
                self.ragle_file is not None and 
                self.monthly_billing_file is not None)
    
    def extract_select_data(self):
        """Extract data from SELECT billing file"""
        if not self.select_file:
            print("SELECT billing file not found")
            return None
        
        print(f"Extracting data from SELECT billing file: {os.path.basename(self.select_file)}")
        
        try:
            # Read Excel file
            xl = pd.ExcelFile(self.select_file)
            sheet_names = xl.sheet_names
            
            # Find the main data sheet - typically the first non-empty sheet
            main_sheet = None
            for sheet in sheet_names:
                df = pd.read_excel(self.select_file, sheet_name=sheet, nrows=5)
                if not df.empty:
                    main_sheet = sheet
                    break
            
            if not main_sheet:
                print("No data found in SELECT billing file")
                return None
            
            # Read data from the main sheet
            select_data = pd.read_excel(self.select_file, sheet_name=main_sheet)
            print(f"Extracted {len(select_data)} rows from SELECT billing file")
            
            return select_data
            
        except Exception as e:
            print(f"Error extracting SELECT data: {str(e)}")
            return None
    
    def extract_ragle_data(self):
        """Extract data from RAGLE billing file"""
        if not self.ragle_file:
            print("RAGLE billing file not found")
            return None
        
        print(f"Extracting data from RAGLE billing file: {os.path.basename(self.ragle_file)}")
        
        try:
            # Read Excel file
            xl = pd.ExcelFile(self.ragle_file)
            sheet_names = xl.sheet_names
            
            # Find the main data sheet - typically the first sheet with 'BILLINGS' in the name
            main_sheet = None
            for sheet in sheet_names:
                if 'BILLINGS' in sheet.upper() or 'BILLING' in sheet.upper() or 'EQ' in sheet.upper():
                    main_sheet = sheet
                    break
            
            # If no billing sheet found, use the first sheet
            if not main_sheet and sheet_names:
                main_sheet = sheet_names[0]
            
            if not main_sheet:
                print("No data found in RAGLE billing file")
                return None
            
            # Read data from the main sheet
            ragle_data = pd.read_excel(self.ragle_file, sheet_name=main_sheet)
            print(f"Extracted {len(ragle_data)} rows from RAGLE billing file")
            
            return ragle_data
            
        except Exception as e:
            print(f"Error extracting RAGLE data: {str(e)}")
            return None
    
    def extract_formulas(self):
        """Extract key formulas from monthly billing file"""
        if not self.monthly_billing_file:
            print("Monthly billing file not found")
            return None
        
        print(f"Extracting formulas from monthly billing file: {os.path.basename(self.monthly_billing_file)}")
        
        try:
            # Load workbook using openpyxl to access formulas
            wb = openpyxl.load_workbook(self.monthly_billing_file, data_only=False)
            
            formulas = {}
            
            # Extract formulas from key sheets
            for sheet_name in self.key_sheets:
                if sheet_name in wb.sheetnames:
                    sheet = wb[sheet_name]
                    sheet_formulas = {}
                    
                    # Scan cells for formulas
                    for row in sheet.iter_rows():
                        for cell in row:
                            if cell.data_type == 'f':  # Formula
                                formula_text = cell.value
                                if formula_text and isinstance(formula_text, str) and formula_text.startswith('='):
                                    # Store formula with its cell reference
                                    cell_ref = f"{get_column_letter(cell.column)}{cell.row}"
                                    sheet_formulas[cell_ref] = formula_text
                    
                    formulas[sheet_name] = sheet_formulas
                    print(f"Extracted {len(sheet_formulas)} formulas from sheet {sheet_name}")
            
            return formulas
        
        except Exception as e:
            print(f"Error extracting formulas: {str(e)}")
            return None
    
    def create_formula_template(self, formulas):
        """Create a formula template workbook"""
        if not formulas:
            print("No formulas to create template from")
            return None
        
        print("Creating formula template workbook...")
        
        try:
            # Create a new workbook
            wb = openpyxl.Workbook()
            
            # Remove default sheet
            if 'Sheet' in wb.sheetnames:
                wb.remove(wb['Sheet'])
            
            # Add a summary sheet
            summary = wb.create_sheet("Summary")
            summary.cell(row=1, column=1).value = "Monthly Billing Formula Template"
            summary.cell(row=1, column=1).font = Font(bold=True, size=14)
            
            # Add sheet list to summary
            summary.cell(row=3, column=1).value = "Sheet Name"
            summary.cell(row=3, column=1).font = Font(bold=True)
            
            summary.cell(row=3, column=2).value = "Formula Count"
            summary.cell(row=3, column=2).font = Font(bold=True)
            
            # Add sheets with formulas
            row = 4
            for sheet_name, sheet_formulas in formulas.items():
                # Add to summary
                summary.cell(row=row, column=1).value = sheet_name
                summary.cell(row=row, column=2).value = len(sheet_formulas)
                row += 1
                
                # Create a sheet
                sheet = wb.create_sheet(sheet_name)
                
                # Add header
                sheet.cell(row=1, column=1).value = f"{sheet_name} Formula Template"
                sheet.cell(row=1, column=1).font = Font(bold=True, size=14)
                
                # Add formula list
                sheet.cell(row=3, column=1).value = "Cell"
                sheet.cell(row=3, column=1).font = Font(bold=True)
                
                sheet.cell(row=3, column=2).value = "Formula"
                sheet.cell(row=3, column=2).font = Font(bold=True)
                
                # Add formulas
                row = 4
                for cell_ref, formula in sheet_formulas.items():
                    sheet.cell(row=row, column=1).value = cell_ref
                    sheet.cell(row=row, column=2).value = formula
                    row += 1
            
            # Save template
            template_path = os.path.join(self.output_dir, "Formula_Template.xlsx")
            wb.save(template_path)
            print(f"Saved formula template to {os.path.basename(template_path)}")
            
            return template_path
        
        except Exception as e:
            print(f"Error creating formula template: {str(e)}")
            return None
    
    def combine_data(self, select_data, ragle_data):
        """Combine data from SELECT and RAGLE files"""
        if select_data is None and ragle_data is None:
            print("No data to combine")
            return None
        
        print("Combining SELECT and RAGLE data...")
        
        try:
            combined_data = []
            
            # Process SELECT data if available
            if select_data is not None:
                # Standardize column names by converting to uppercase
                select_data.columns = [str(col).upper() for col in select_data.columns]
                
                # Add source column
                select_data['DATA_SOURCE'] = 'SELECT'
                combined_data.append(select_data)
            
            # Process RAGLE data if available
            if ragle_data is not None:
                # Standardize column names by converting to uppercase
                ragle_data.columns = [str(col).upper() for col in ragle_data.columns]
                
                # Add source column
                ragle_data['DATA_SOURCE'] = 'RAGLE'
                combined_data.append(ragle_data)
            
            # Combine the data
            if combined_data:
                # Use concat with join='outer' to keep all columns from both dataframes
                result = pd.concat(combined_data, ignore_index=True, sort=False, join='outer')
                print(f"Combined data has {len(result)} rows and {len(result.columns)} columns")
                return result
            else:
                return None
            
        except Exception as e:
            print(f"Error combining data: {str(e)}")
            return None
    
    def save_combined_data(self, combined_data):
        """Save combined data to Excel workbook"""
        if combined_data is None:
            print("No combined data to save")
            return False
        
        print("Saving combined billing data...")
        
        try:
            # Create output filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_excel = os.path.join(self.output_dir, f"Combined_Billing_Data_{timestamp}.xlsx")
            output_csv = os.path.join(self.output_dir, f"Combined_Billing_Data_{timestamp}.csv")
            
            # Save to Excel
            combined_data.to_excel(output_excel, index=False, sheet_name="Combined_Data")
            print(f"Saved combined data to Excel: {os.path.basename(output_excel)}")
            
            # Save to CSV
            combined_data.to_csv(output_csv, index=False)
            print(f"Saved combined data to CSV: {os.path.basename(output_csv)}")
            
            # Store output file paths
            self.output_monthly_file = output_excel
            self.output_csv_file = output_csv
            
            return True
            
        except Exception as e:
            print(f"Error saving combined data: {str(e)}")
            return False
    
    def process_all(self):
        """Process all billing data files"""
        print("Starting billing data processing...")
        
        # Find all source files
        if not self.find_source_files():
            print("ERROR: Not all required source files were found")
            return {
                'success': False,
                'message': 'Not all required source files were found. Please check logs for details.',
                'files': {
                    'select': self.select_file,
                    'ragle': self.ragle_file,
                    'monthly': self.monthly_billing_file
                }
            }
        
        # Extract data from SELECT file
        select_data = self.extract_select_data()
        
        # Extract data from RAGLE file
        ragle_data = self.extract_ragle_data()
        
        # Extract formulas from monthly billing file
        formulas = self.extract_formulas()
        
        # Create formula template
        if formulas:
            template_path = self.create_formula_template(formulas)
        else:
            template_path = None
        
        # Combine data from SELECT and RAGLE files
        combined_data = self.combine_data(select_data, ragle_data)
        
        # Save combined data
        if combined_data is not None:
            self.save_combined_data(combined_data)
        
        # Return results
        return {
            'success': True,
            'message': 'Billing data processed successfully',
            'files': {
                'select': self.select_file,
                'ragle': self.ragle_file,
                'monthly': self.monthly_billing_file,
                'combined_excel': self.output_monthly_file,
                'combined_csv': self.output_csv_file,
                'template': template_path
            },
            'stats': {
                'select_rows': len(select_data) if select_data is not None else 0,
                'ragle_rows': len(ragle_data) if ragle_data is not None else 0,
                'combined_rows': len(combined_data) if combined_data is not None else 0,
                'formula_count': sum(len(f) for f in formulas.values()) if formulas else 0
            }
        }


def process_monthly_billing():
    """Process monthly billing data"""
    processor = BillingProcessor()
    return processor.process_all()


if __name__ == "__main__":
    # Run the processor when executed directly
    result = process_monthly_billing()
    print("\nProcessing complete!")
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    
    if result['success']:
        print("\nStatistics:")
        print(f"SELECT rows: {result['stats']['select_rows']}")
        print(f"RAGLE rows: {result['stats']['ragle_rows']}")
        print(f"Combined rows: {result['stats']['combined_rows']}")
        print(f"Formulas extracted: {result['stats']['formula_count']}")
        
        print("\nOutput files:")
        if result['files']['combined_excel']:
            print(f"Combined Excel: {os.path.basename(result['files']['combined_excel'])}")
        if result['files']['combined_csv']:
            print(f"Combined CSV: {os.path.basename(result['files']['combined_csv'])}")
        if result['files']['template']:
            print(f"Formula template: {os.path.basename(result['files']['template'])}")