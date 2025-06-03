import pandas as pd

# Check available sheets in your April billing file
file_path = 'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm'

try:
    # Get all sheet names
    xl_file = pd.ExcelFile(file_path)
    print("Available sheets in your April EQ billings file:")
    for i, sheet in enumerate(xl_file.sheet_names):
        print(f"{i+1}. {sheet}")
    
    # Try to load a few key sheets to see their structure
    print("\n=== FLEET Sheet Preview ===")
    fleet_df = pd.read_excel(file_path, sheet_name='FLEET', nrows=5)
    print("Columns:", fleet_df.columns.tolist())
    print(fleet_df.head())
    
    # Look for internal rates sheet
    potential_rate_sheets = [sheet for sheet in xl_file.sheet_names 
                           if any(keyword in sheet.upper() for keyword in 
                                 ['RATE', 'INTERNAL', 'PRICING', 'COST', 'MASTER'])]
    
    if potential_rate_sheets:
        print(f"\n=== Potential Internal Rates Sheets ===")
        for sheet in potential_rate_sheets:
            print(f"Found: {sheet}")
            try:
                rates_df = pd.read_excel(file_path, sheet_name=sheet, nrows=5)
                print(f"Columns in {sheet}:", rates_df.columns.tolist())
                print(rates_df.head())
                print("---")
            except Exception as e:
                print(f"Could not read {sheet}: {e}")
    
except Exception as e:
    print(f"Error reading file: {e}")