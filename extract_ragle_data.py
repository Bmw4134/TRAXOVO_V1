"""
Extract data from the RAGLE EQ BILLINGS file to get correct totals
"""
import pandas as pd
import os

# Path to the RAGLE file
RAGLE_FILE = 'attached_assets/RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm'

# Check if the file exists
if not os.path.exists(RAGLE_FILE):
    print(f"File not found: {RAGLE_FILE}")
    exit(1)

try:
    # Try to find the sheet with billing data
    xlsx = pd.ExcelFile(RAGLE_FILE)
    sheet_names = xlsx.sheet_names
    print(f"Available sheets: {sheet_names}")
    
    # Look for relevant sheets
    billing_sheets = [s for s in sheet_names if any(term in s.upper() for term in ['BILL', 'APR', 'TOTAL', 'DATA'])]
    
    # Try each potential sheet
    for sheet in billing_sheets:
        try:
            print(f"\nTrying sheet: {sheet}")
            df = pd.read_excel(RAGLE_FILE, sheet_name=sheet)
            print(f"Sheet size: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"Column names: {df.columns.tolist()[:10]}")
            
            # Try to find amount/total column
            amount_columns = [col for col in df.columns if any(term in str(col).upper() for term in ['AMOUNT', 'TOTAL', '$'])]
            for col in amount_columns:
                total = df[col].sum()
                print(f"Total for column '{col}': {total:,.2f}")
        except Exception as e:
            print(f"Error reading sheet {sheet}: {str(e)}")
            
except Exception as e:
    print(f"Error opening file: {str(e)}")