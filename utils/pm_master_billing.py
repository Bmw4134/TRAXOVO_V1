"""
PM Master Billing Processor

This module processes multiple PM allocation files to create a consolidated
master billing report and generates division-specific exports.

Features:
- Extracts data from all PM allocation files (XLSX and CSV)
- Maps equipment numbers to metadata
- Applies correct billing rates based on frequency
- Generates master billing workbook and division-specific exports
"""

import os
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import logging
from pathlib import Path
import glob
import re
import csv

# Configure debug logging
logging.basicConfig(level=logging.INFO)
# Set up logger
logger = logging.getLogger(__name__)

# Constants
ATTACHED_ASSETS_DIR = Path('attached_assets')
EXPORTS_DIR = Path('exports/pm_master')
DIVISIONS = ['DFW', 'WTX', 'HOU', 'SELECT']
MONTH_NAME = 'APRIL'  # Default month for current processing
YEAR = '2025'  # Default year for current processing

# Ensure exports directory exists
EXPORTS_DIR.mkdir(exist_ok=True, parents=True)

# Column mapping for standardization across different source files
COLUMN_MAPPING = {
    'equip_id': ['EQ#', 'EQ #', 'EQUIPMENT #', 'EQUIP #', 'EQUIP. #', 'EQUIPMENT_ID', 'EQUIPMENT NUMBER', 'EQUIPMENT', 'TRUCK#'],
    'description': ['DESCRIPTION', 'DESC', 'EQUIPMENT DESC', 'EQUIP DESCRIPTION', 'TYPE', 'EQUIPMENT TYPE'],
    'job': ['JOB', 'JOB #', 'PROJECT', 'JOB_NUMBER', 'JOB_CODE', 'JOB CODE', 'JOB NUMBER', 'JOB NAME', 'PROJECT NAME'],
    'date': ['DATE', 'START DATE', 'START', 'BEGIN DATE', 'ALLOCATION DATE', 'SERVICE DATE', 'BILLING DATE'],
    'units': ['UNITS', 'DAYS', 'HRS', 'HOURS', 'QUANTITY', 'QTY', 'DAYS USED'],
    'frequency': ['FREQUENCY', 'RATE TYPE', 'BILLING TYPE', 'BILL TYPE', 'FREQUENCY TYPE', 'TYPE'],
    'amount': ['AMOUNT', 'TOTAL', 'EXTENDED', 'EXTENDED AMOUNT', 'EXTENDED PRICE', 'COST', 'BILLING', 'BILLINGS'],
    'rate': ['RATE', 'UNIT PRICE', 'PRICE', 'UNIT RATE', 'RATE AMOUNT', 'DAILY RATE', 'MONTHLY RATE', 'HOURLY RATE'],
    'division': ['DIVISION', 'DIV', 'REGION', 'LOCATION', 'BRANCH', 'AREA', 'DISTRICT'],
    'cost_code': ['COST CODE', 'COSTCODE', 'ACCT CODE', 'ACCOUNT CODE', 'CODE'],
    'phase': ['PHASE', 'PH', 'PHASE CODE', 'PHASE NUMBER']
}

# Rate mapping based on frequency
FREQUENCY_MAPPING = {
    'MO': 'MONTHLY',
    'MONTHLY': 'MONTHLY',
    'MONTH': 'MONTHLY',
    'HR': 'HOURLY',
    'HOURLY': 'HOURLY',
    'HOUR': 'HOURLY',
    'DAY': 'DAILY',
    'DAILY': 'DAILY',
    'WK': 'WEEKLY',
    'WEEK': 'WEEKLY',
    'WEEKLY': 'WEEKLY'
}

def find_matching_column(df, patterns):
    """Find the first column that matches one of the patterns"""
    for col in df.columns:
        col_str = str(col).strip().upper()
        for pattern in patterns:
            if re.search(pattern, col_str, re.IGNORECASE):
                return col
    return None

def find_all_allocation_files():
    """Find all allocation files (XLSX and CSV) in the attached_assets directory"""
    allocation_files = []
    
    # Look for Excel files containing EQMO and BILLING ALLOCATIONS in the filename
    excel_pattern = os.path.join(ATTACHED_ASSETS_DIR, '*EQMO*BILLING*ALLOCATIONS*.xlsx')
    excel_files = glob.glob(excel_pattern)
    allocation_files.extend(excel_files)
    
    # Look for RAGLE EQ BILLINGS file which contains the rate information
    ragle_pattern = os.path.join(ATTACHED_ASSETS_DIR, 'RAGLE*EQ*BILLINGS*.xls*')
    ragle_files = glob.glob(ragle_pattern)
    allocation_files.extend(ragle_files)
    
    # Look for division-specific CSV files
    for division in DIVISIONS:
        # Try different naming patterns for CSV files
        csv_patterns = [
            os.path.join(ATTACHED_ASSETS_DIR, f'*{division}*APR*2025*.csv'),
            os.path.join(ATTACHED_ASSETS_DIR, f'*{division}*APRIL*2025*.csv'),
            os.path.join(ATTACHED_ASSETS_DIR, f'SM*{division}*APR*.csv'),
            os.path.join(ATTACHED_ASSETS_DIR, f'*{division}*.csv'),
        ]
        
        for pattern in csv_patterns:
            csv_files = glob.glob(pattern)
            allocation_files.extend(csv_files)
    
    # Remove duplicates while preserving order
    seen = set()
    allocation_files = [x for x in allocation_files if not (x in seen or seen.add(x))]
    
    logger.info(f"Found {len(allocation_files)} allocation files matching patterns")
    return allocation_files

def find_equipment_rates_file():
    """Find the equipment rates file or master billing workbook"""
    # First, look for RAGLE EQ BILLINGS file which has the April 2025 rates
    ragle_pattern = os.path.join(ATTACHED_ASSETS_DIR, 'RAGLE*EQ*BILLINGS*APRIL*2025*.xls*')
    files = glob.glob(ragle_pattern)
    
    if not files:
        # Try other patterns for the RAGLE file
        ragle_pattern = os.path.join(ATTACHED_ASSETS_DIR, 'RAGLE*EQ*BILLINGS*.xls*')
        files = glob.glob(ragle_pattern)
    
    if files:
        logger.info(f"Found equipment rates in RAGLE file: {os.path.basename(files[0])}")
        return files[0]
    
    # Look for the EQ MONTHLY BILLINGS file as fallback
    eq_monthly_pattern = os.path.join(ATTACHED_ASSETS_DIR, 'EQ*MONTHLY*BILLINGS*.xlsx')
    files = glob.glob(eq_monthly_pattern)
    
    if files:
        logger.info(f"Found equipment rates in monthly billing spreadsheet: {os.path.basename(files[0])}")
        return files[0]
    
    # As a last resort, look for any equipment rates workbook
    rates_pattern = os.path.join(ATTACHED_ASSETS_DIR, '*EQUIP*RATES*.xlsx')
    files = glob.glob(rates_pattern)
    
    if files:
        logger.info(f"Found equipment rates file: {os.path.basename(files[0])}")
        return files[0]
    
    logger.warning("No equipment rates file found. Will proceed without rates.")
    return None

def extract_equipment_rates(rates_file):
    """Extract equipment rates from the rates file"""
    if not rates_file:
        return pd.DataFrame()
    
    try:
        # Check if it's a RAGLE file which has a specific format
        is_ragle_file = 'RAGLE' in os.path.basename(rates_file).upper()
        
        # Load the workbook
        wb = openpyxl.load_workbook(rates_file, data_only=True)
        
        # For RAGLE files, look for the "Equip Rates" sheet specifically
        if is_ragle_file:
            rates_sheet = None
            for sheet_name in wb.sheetnames:
                if 'EQUIP RATES' in sheet_name.upper():
                    rates_sheet = sheet_name
                    break
            
            if not rates_sheet:
                # If no "Equip Rates" sheet, look for sheets with "RATES" in the name
                for sheet_name in wb.sheetnames:
                    if 'RATES' in sheet_name.upper():
                        rates_sheet = sheet_name
                        break
        # For non-RAGLE files, use a more general approach
        else:
            rates_sheet = None
            sheet_patterns = ['EQUIP RATES', 'RATES', 'EQUIPMENT', 'BILLING RATES', 'MONTHLY RATES']
            
            for pattern in sheet_patterns:
                for sheet_name in wb.sheetnames:
                    if pattern in sheet_name.upper():
                        rates_sheet = sheet_name
                        break
                if rates_sheet:
                    break
        
        if not rates_sheet:
            rates_sheet = wb.sheetnames[0]  # Default to first sheet
            
        logger.info(f"Using sheet '{rates_sheet}' for equipment rates from file: {os.path.basename(rates_file)}")
        
        # Load the sheet into a DataFrame
        df = pd.read_excel(rates_file, sheet_name=rates_sheet)
        
        # Find the equipment ID and rate columns
        equip_col = find_matching_column(df, COLUMN_MAPPING['equip_id'])
        monthly_rate_col = find_matching_column(df, ['MONTHLY RATE', 'MONTHLY', 'MO RATE'])
        daily_rate_col = find_matching_column(df, ['DAILY RATE', 'DAILY', 'DAY RATE'])
        hourly_rate_col = find_matching_column(df, ['HOURLY RATE', 'HOURLY', 'HR RATE'])
        desc_col = find_matching_column(df, COLUMN_MAPPING['description'])
        
        if not equip_col:
            logger.error("Equipment ID column not found in rates file")
            return pd.DataFrame()
        
        # Create a standardized rates DataFrame
        rates_df = pd.DataFrame()
        rates_df['EQUIPMENT_ID'] = df[equip_col].astype(str).str.strip().str.upper()
        
        # Add description if available
        if desc_col:
            rates_df['DESCRIPTION'] = df[desc_col].astype(str).str.strip()
        else:
            rates_df['DESCRIPTION'] = ""
        
        # Add rates by frequency
        if monthly_rate_col:
            rates_df['MONTHLY_RATE'] = pd.to_numeric(df[monthly_rate_col], errors='coerce').fillna(0)
        else:
            rates_df['MONTHLY_RATE'] = 0
            
        if daily_rate_col:
            rates_df['DAILY_RATE'] = pd.to_numeric(df[daily_rate_col], errors='coerce').fillna(0)
        else:
            rates_df['DAILY_RATE'] = 0
            
        if hourly_rate_col:
            rates_df['HOURLY_RATE'] = pd.to_numeric(df[hourly_rate_col], errors='coerce').fillna(0)
        else:
            rates_df['HOURLY_RATE'] = 0
        
        # Remove rows with no equipment ID or all zero rates
        rates_df = rates_df[rates_df['EQUIPMENT_ID'].notna()]
        rates_df = rates_df[~(rates_df['EQUIPMENT_ID'] == '')]
        rates_df = rates_df[~((rates_df['MONTHLY_RATE'] == 0) & 
                              (rates_df['DAILY_RATE'] == 0) & 
                              (rates_df['HOURLY_RATE'] == 0))]
        
        # Standardize equipment ID format to match allocation files
        rates_df['EQUIPMENT_ID'] = rates_df['EQUIPMENT_ID'].str.replace(r'\s+', '', regex=True)
        
        logger.info(f"Extracted {len(rates_df)} equipment rates")
        return rates_df
        
    except Exception as e:
        logger.error(f"Error extracting equipment rates: {str(e)}")
        return pd.DataFrame()

def process_allocation_file(file_path):
    """Process a single allocation file to extract equipment billing data"""
    logger.info(f"Processing allocation file: {os.path.basename(file_path)}")
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        # Handle different file formats
        if file_ext == '.csv':
            # Determine if it's a division-specific CSV
            filename = os.path.basename(file_path).upper()
            is_division_csv = any(div in filename for div in DIVISIONS) or any(prefix in filename for prefix in ["01 - ", "02 - ", "03 - ", "SM - "])
            
            # For division-specific CSVs which might have different formats
            if is_division_csv:
                logger.info(f"Processing division-specific CSV: {filename}")
                
                # Determine division from filename
                if "DFW" in filename or "01 -" in filename:
                    division = "DFW"
                elif "HOU" in filename or "02 -" in filename:
                    division = "HOU"
                elif "WTX" in filename or "WT" in filename or "03 -" in filename:
                    division = "WTX"
                elif "SELECT" in filename or "SM -" in filename:
                    division = "SELECT"
                else:
                    division = "OTHER"
                
                # First try to check if the file has headers or not
                # These division CSV files typically don't have headers
                try:
                    # Read just the first row to check the content
                    sample = pd.read_csv(file_path, nrows=1)
                    # If the first column looks like an equipment ID (e.g., PT-159), it's likely headerless
                    first_col_value = str(sample.iloc[0, 0]).strip()
                    
                    if re.match(r'^[A-Z]{1,3}-\d+$', first_col_value):
                        # This is a headerless CSV with the format we know
                        logger.info(f"Detected headerless division-specific CSV: {filename}")
                        
                        # Define the headers based on the sample we saw
                        headers = ["equip_id", "description", "date", "job", "phase", "cost_code", 
                                "units", "rate", "frequency", "monthly_rate", "amount"]
                        
                        # Read the CSV file without headers
                        df = pd.read_csv(file_path, header=None, names=headers)
                        
                        # Add division column
                        df['division'] = division
                        logger.info(f"Processed headerless CSV with {len(df)} records from {division}")
                    else:
                        # It has headers, process normally
                        df = pd.read_csv(file_path)
                except Exception as e:
                    logger.warning(f"Error detecting headers: {str(e)}. Trying standard processing.")
                    # Try with various options to handle different CSV formats
                    try:
                        df = pd.read_csv(file_path, encoding='utf-8')
                    except:
                        try:
                            df = pd.read_csv(file_path, encoding='latin1')
                        except:
                            df = pd.read_csv(file_path, encoding='utf-8', sep=';')
            else:
                # Standard CSV
                df = pd.read_csv(file_path)
        
        elif file_ext in ['.xlsx', '.xls', '.xlsm']:
            # For Excel files, we need to determine the correct sheet
            excel_file = pd.ExcelFile(file_path)
            
            # Look for sheets with allocation or billing data
            sheet_name = None
            sheet_keywords = ['BILLINGS', 'ALLOCATION', 'DATA', 'EQUIP BILLINGS', 'EQUIP']
            
            for keyword in sheet_keywords:
                matching_sheets = [s for s in excel_file.sheet_names if keyword in s.upper()]
                if matching_sheets:
                    sheet_name = matching_sheets[0]
                    break
            
            # If no specific sheet found, use the first sheet
            if not sheet_name and excel_file.sheet_names:
                sheet_name = excel_file.sheet_names[0]
            
            if sheet_name:
                logger.info(f"Using sheet '{sheet_name}' from {os.path.basename(file_path)}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                logger.error(f"No valid sheets found in {os.path.basename(file_path)}")
                return pd.DataFrame()
        else:
            logger.error(f"Unsupported file format: {file_ext}")
            return pd.DataFrame()
        
        # Find standardized column names
        data = {}
        for col_type, patterns in COLUMN_MAPPING.items():
            col = find_matching_column(df, patterns)
            if col:
                data[col_type] = col
        
        # Skip if essential columns are missing
        if 'equip_id' not in data or 'job' not in data:
            logger.warning(f"Missing essential columns in file: {os.path.basename(file_path)}")
            
            # Special handling for division-specific CSVs which might have non-standard formats
            filename = os.path.basename(file_path).upper()
            if any(div in filename for div in DIVISIONS):
                logger.info(f"Attempting special handling for division file: {filename}")
                
                # For some division files, the equipment might be in a different format
                # Try to identify potential equipment ID columns based on values matching equipment patterns
                if 'equip_id' not in data:
                    for col in df.columns:
                        # Check if column values match typical equipment number patterns
                        sample_values = df[col].astype(str).str.strip().dropna().head(10).tolist()
                        if any(re.match(r'^[A-Z]+\d+$', str(val)) for val in sample_values):
                            data['equip_id'] = col
                            logger.info(f"Found potential equipment ID column: {col}")
                            break
                
                # For job column, look for columns with typical job number formats
                if 'job' not in data:
                    for col in df.columns:
                        sample_values = df[col].astype(str).str.strip().dropna().head(10).tolist()
                        if any(re.match(r'^\d{4}-\d{3}$', str(val)) for val in sample_values):
                            data['job'] = col
                            logger.info(f"Found potential job column: {col}")
                            break
            
            # If still missing essential columns, skip this file
            if 'equip_id' not in data or 'job' not in data:
                logger.error(f"Unable to find essential columns in file: {os.path.basename(file_path)}")
                return pd.DataFrame()
        
        # Extract filename elements to determine division if not found in the data
        if 'division' not in data:
            filename = os.path.basename(file_path).upper()
            for div in DIVISIONS:
                if div in filename:
                    logger.info(f"Determined division {div} from filename")
                    df['DIVISION'] = div
                    data['division'] = 'DIVISION'
                    break
            
            # If still no division, check if we can determine from file path or contents
            if 'division' not in data:
                # Check for patterns in sheet content that might indicate division
                for div in DIVISIONS:
                    # Check if division appears in any cell in the first few rows
                    for col in df.columns:
                        if df[col].astype(str).str.contains(div, case=False, na=False).any():
                            logger.info(f"Determined division {div} from content")
                            df['DIVISION'] = div
                            data['division'] = 'DIVISION'
                            break
                    if 'division' in data:
                        break
        
        # Standardize column names for further processing
        rename_dict = {data[col_type]: col_type for col_type in data}
        
        # Add any missing columns with default values
        for col_type in COLUMN_MAPPING.keys():
            if col_type not in data:
                df[col_type] = None
                
                # Provide default values for required fields
                if col_type == 'frequency':
                    df[col_type] = 'MONTHLY'  # Default billing frequency
                elif col_type == 'date':
                    df[col_type] = f'APRIL 1, {YEAR}'  # Default date
                elif col_type == 'phase':
                    df[col_type] = '01'  # Default phase
                elif col_type == 'cost_code':
                    df[col_type] = '10-100'  # Default cost code
        
        # Rename columns to standardized names
        df = df.rename(columns=rename_dict)
        
        # Filter out rows with no equipment ID
        df = df[df['equip_id'].notna()]
        
        # Standardize equipment ID format (remove spaces, leading zeros, etc.)
        df['equip_id'] = df['equip_id'].astype(str).str.strip().str.upper()
        df['equip_id'] = df['equip_id'].str.replace(r'\s+', '', regex=True)  # Remove all whitespace
        
        # Ensure numeric columns are correctly typed
        if 'units' in df.columns:
            df['units'] = pd.to_numeric(df['units'], errors='coerce').fillna(0)
        
        if 'rate' in df.columns:
            df['rate'] = pd.to_numeric(df['rate'], errors='coerce').fillna(0)
        
        if 'amount' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
        
        # Standardize job numbers
        if 'job' in df.columns:
            # Standardize job number format (e.g., '2024-015')
            df['job'] = df['job'].astype(str).str.strip().str.upper()
            
            # Fix common job number format issues
            # Convert patterns like "24-15" to "2024-015"
            df['job'] = df['job'].apply(lambda x: re.sub(r'^(\d{2})-(\d{1,3})$', 
                                                        lambda m: f'20{m.group(1)}-{m.group(2).zfill(3)}', 
                                                        str(x)) if pd.notna(x) else x)
        
        # Add source file column for tracking
        df['source_file'] = os.path.basename(file_path)
        
        logger.info(f"Successfully processed {os.path.basename(file_path)}: Found {len(df)} equipment records")
        return df
    
    except Exception as e:
        logger.error(f"Error processing file {os.path.basename(file_path)}: {str(e)}")
        return pd.DataFrame()

def generate_master_billing(allocation_data, rates_data):
    """Generate the master billing dataset by applying rates to allocation data"""
    if allocation_data.empty:
        logger.error("No allocation data provided")
        return pd.DataFrame()
    
    logger.info(f"Generating master billing from {len(allocation_data)} allocation records")
    
    # Create a copy to avoid modifying the original
    billing_df = allocation_data.copy()
    
    # Ensure all column names are lowercased for consistency
    billing_df.columns = [col.lower() for col in billing_df.columns]
    
    # Make sure required columns exist
    required_columns = ['equip_id', 'job', 'units', 'rate', 'amount', 'division']
    for col in required_columns:
        if col not in billing_df.columns:
            billing_df[col] = None if col != 'units' and col != 'rate' and col != 'amount' else 0
    
    # Convert numeric columns
    numeric_cols = ['units', 'rate', 'amount']
    for col in numeric_cols:
        if col in billing_df.columns:
            billing_df[col] = pd.to_numeric(billing_df[col], errors='coerce').fillna(0)
    
    # Initialize new columns for rate-adjusted values
    billing_df['HAS_RATE'] = False
    billing_df['RATE_SOURCE'] = 'Default'
    
    # Apply rates from rates data if available
    if not rates_data.empty:
        logger.info(f"Applying rates from rates data with {len(rates_data)} equipment rate records")
        
        # Merge with rates data to get the appropriate rate
        for idx, row in billing_df.iterrows():
            equip_id = row['equip_id']
            frequency = str(row['frequency']).upper() if pd.notna(row['frequency']) else 'MONTHLY'
            
            # Find matching equipment in rates data
            rate_matches = rates_data[rates_data['EQUIPMENT_ID'] == equip_id]
            
            if not rate_matches.empty:
                # Determine which rate to use based on frequency
                if frequency == 'MONTHLY' and rate_matches['MONTHLY_RATE'].iloc[0] > 0:
                    billing_df.at[idx, 'rate'] = rate_matches['MONTHLY_RATE'].iloc[0]
                    billing_df.at[idx, 'HAS_RATE'] = True
                    billing_df.at[idx, 'RATE_SOURCE'] = 'Monthly Rate'
                elif frequency == 'DAILY' and rate_matches['DAILY_RATE'].iloc[0] > 0:
                    billing_df.at[idx, 'rate'] = rate_matches['DAILY_RATE'].iloc[0]
                    billing_df.at[idx, 'HAS_RATE'] = True
                    billing_df.at[idx, 'RATE_SOURCE'] = 'Daily Rate'
                elif frequency == 'HOURLY' and rate_matches['HOURLY_RATE'].iloc[0] > 0:
                    billing_df.at[idx, 'rate'] = rate_matches['HOURLY_RATE'].iloc[0]
                    billing_df.at[idx, 'HAS_RATE'] = True
                    billing_df.at[idx, 'RATE_SOURCE'] = 'Hourly Rate'
                # If frequency doesn't match available rates, find the first non-zero rate
                else:
                    if rate_matches['MONTHLY_RATE'].iloc[0] > 0:
                        billing_df.at[idx, 'rate'] = rate_matches['MONTHLY_RATE'].iloc[0]
                        billing_df.at[idx, 'frequency'] = 'MONTHLY'
                        billing_df.at[idx, 'HAS_RATE'] = True
                        billing_df.at[idx, 'RATE_SOURCE'] = 'Monthly Rate (Default)'
                    elif rate_matches['DAILY_RATE'].iloc[0] > 0:
                        billing_df.at[idx, 'rate'] = rate_matches['DAILY_RATE'].iloc[0]
                        billing_df.at[idx, 'frequency'] = 'DAILY'
                        billing_df.at[idx, 'HAS_RATE'] = True
                        billing_df.at[idx, 'RATE_SOURCE'] = 'Daily Rate (Default)'
                    elif rate_matches['HOURLY_RATE'].iloc[0] > 0:
                        billing_df.at[idx, 'rate'] = rate_matches['HOURLY_RATE'].iloc[0]
                        billing_df.at[idx, 'frequency'] = 'HOURLY'
                        billing_df.at[idx, 'HAS_RATE'] = True
                        billing_df.at[idx, 'RATE_SOURCE'] = 'Hourly Rate (Default)'
                
                # Update description if it's empty and available in rates data
                if (not pd.notna(row['description']) or row['description'] == '') and pd.notna(rate_matches['DESCRIPTION'].iloc[0]):
                    billing_df.at[idx, 'description'] = rate_matches['DESCRIPTION'].iloc[0]
            
            # If equipment is missing a rate, log it
            if not billing_df.at[idx, 'HAS_RATE']:
                logger.warning(f"No matching rate found for equipment {equip_id} with frequency {frequency}")
    
    # Calculate amount if rate and units are available but amount is not
    for idx, row in billing_df.iterrows():
        if pd.notna(row['rate']) and pd.notna(row['units']) and row['rate'] > 0 and row['units'] > 0:
            if not pd.notna(row['amount']) or row['amount'] == 0:
                billing_df.at[idx, 'amount'] = row['rate'] * row['units']
    
    # Create standardized master billing format
    master_billing = pd.DataFrame({
        'Division': billing_df['division'],
        'Equip #': billing_df['equip_id'],
        'Description': billing_df['description'],
        'Date': billing_df['date'],
        'Job': billing_df['job'],
        'Phase': billing_df['phase'],
        'Cost Code': billing_df['cost_code'],
        'Units': billing_df['units'],
        'Rate': billing_df['rate'],
        'Amount': billing_df['amount'],
        'Frequency': billing_df['frequency'],
        'Source File': billing_df['source_file'],
        'Has Rate': billing_df['HAS_RATE'],
        'Rate Source': billing_df['RATE_SOURCE']
    })
    
    # Log missing rates
    missing_rates = master_billing[master_billing['Rate'] == 0]
    if not missing_rates.empty:
        logger.warning(f"Missing rates for {len(missing_rates)} equipment records")
    
    return master_billing

def filter_by_division(master_billing, division):
    """Filter the master billing data by division"""
    if master_billing.empty:
        return pd.DataFrame()
    
    # Division might be stored differently (case, spaces, etc.)
    division_filter = master_billing['Division'].str.upper().str.strip() == division.upper()
    
    return master_billing[division_filter].copy()

def export_master_billing(master_billing, output_path, create_division_sheets=False):
    """
    Export the master billing data to Excel
    
    Args:
        master_billing (DataFrame): The billing data to export
        output_path (str): Path to save the Excel file
        create_division_sheets (bool): Whether to create separate sheets for each division
        
    Returns:
        bool: True if export was successful, False otherwise
    """
    if master_billing.empty:
        logger.error("No data to export")
        return False
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to Excel
        writer = pd.ExcelWriter(output_path, engine='openpyxl')
        
        # Create the main sheet with all data
        master_billing.to_excel(writer, sheet_name='Equip Billings', index=False)
        
        # Add division-specific sheets if requested (for master export)
        if create_division_sheets:
            for division in DIVISIONS:
                division_data = filter_by_division(master_billing, division)
                if not division_data.empty:
                    # Create a sheet for this division
                    division_data.to_excel(writer, sheet_name=division, index=False)
                    logger.info(f"Added {division} sheet with {len(division_data)} records")
        
        # Access the workbook and the main worksheet
        workbook = writer.book
        worksheet = writer.sheets['Equip Billings']
        
        # Define styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="0072C6", end_color="0072C6", fill_type="solid")
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # Apply formatting
        for col_num, col_name in enumerate(master_billing.columns, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            
            # Auto-size columns
            worksheet.column_dimensions[get_column_letter(col_num)].width = max(12, len(str(col_name)) + 2)
        
        # Add title
        title_row = worksheet.insert_rows(1)
        title_cell = worksheet.cell(row=1, column=1)
        title_cell.value = f"EQUIPMENT BILLING EXPORT - {MONTH_NAME} {YEAR}"
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal='center')
        
        # Merge cells for title
        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(master_billing.columns))
        
        # Format numeric columns
        money_format = workbook.add_format({'num_format': '$#,##0.00'})
        for row_idx in range(3, len(master_billing) + 3):  # +3 because of title row and header row
            rate_cell = worksheet.cell(row=row_idx, column=master_billing.columns.get_loc('Rate') + 1)
            amount_cell = worksheet.cell(row=row_idx, column=master_billing.columns.get_loc('Amount') + 1)
            
            if rate_cell.value and isinstance(rate_cell.value, (int, float)):
                rate_cell.number_format = '$#,##0.00'
            
            if amount_cell.value and isinstance(amount_cell.value, (int, float)):
                amount_cell.number_format = '$#,##0.00'
        
        # Apply alternating row colors
        for row_idx in range(3, len(master_billing) + 3):  # +3 because of title row and header row
            if row_idx % 2 == 0:
                for col_idx in range(1, len(master_billing.columns) + 1):
                    cell = worksheet.cell(row=row_idx, column=col_idx)
                    cell.fill = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
        
        # Apply borders to all cells
        thin_border = Border(left=Side(style='thin'), 
                            right=Side(style='thin'),
                            top=Side(style='thin'),
                            bottom=Side(style='thin'))
        
        for row_idx in range(1, len(master_billing) + 3):  # +3 because of title row and header row
            for col_idx in range(1, len(master_billing.columns) + 1):
                cell = worksheet.cell(row=row_idx, column=col_idx)
                cell.border = thin_border
        
        # Add summary information
        summary_row = len(master_billing) + 4
        worksheet.cell(row=summary_row, column=1).value = "SUMMARY"
        worksheet.cell(row=summary_row, column=1).font = Font(bold=True)
        
        worksheet.cell(row=summary_row+1, column=1).value = "Total Records:"
        worksheet.cell(row=summary_row+1, column=2).value = len(master_billing)
        
        worksheet.cell(row=summary_row+2, column=1).value = "Total Amount:"
        worksheet.cell(row=summary_row+2, column=2).value = master_billing['Amount'].sum()
        worksheet.cell(row=summary_row+2, column=2).number_format = '$#,##0.00'
        
        worksheet.cell(row=summary_row+3, column=1).value = "Missing Rates:"
        worksheet.cell(row=summary_row+3, column=2).value = len(master_billing[master_billing['Rate'] == 0])
        
        worksheet.cell(row=summary_row+4, column=1).value = "Export Date:"
        worksheet.cell(row=summary_row+4, column=2).value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save the workbook
        writer.close()
        
        logger.info(f"Successfully exported master billing to {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error exporting master billing: {str(e)}")
        return False

def generate_division_exports(master_billing):
    """Generate division-specific exports"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    export_paths = {}
    for division in DIVISIONS:
        division_data = filter_by_division(master_billing, division)
        
        if division_data.empty:
            logger.warning(f"No data found for division {division}")
            continue
        
        output_path = os.path.join(EXPORTS_DIR, f"{division}_EQUIP_BILLINGS_{MONTH_NAME}_{YEAR}.xlsx")
        if export_master_billing(division_data, output_path):
            export_paths[division] = output_path
            logger.info(f"Created {division} export with {len(division_data)} records")
    
    return export_paths

def process_master_billing():
    """Main function to process all allocation files and generate master billing with division exports"""
    try:
        logger.info("Starting PM Master Billing processing")
        
        # Find all allocation files
        allocation_files = find_all_allocation_files()
        if not allocation_files:
            logger.error("No allocation files found")
            return {
                'success': False,
                'message': "No allocation files found",
                'exports': {}
            }
        
        # Find equipment rates file
        rates_file = find_equipment_rates_file()
        
        # Process each allocation file
        all_allocation_data = []
        for file_path in allocation_files:
            # Skip rates file if it's in the allocation files list
            if rates_file and os.path.samefile(file_path, rates_file):
                continue
                
            allocation_data = process_allocation_file(file_path)
            if not allocation_data.empty:
                all_allocation_data.append(allocation_data)
        
        if not all_allocation_data:
            logger.error("Failed to extract data from allocation files")
            return {
                'success': False,
                'message': "Failed to extract data from allocation files",
                'exports': {}
            }
        
        # Combine all allocation data
        combined_data = pd.concat(all_allocation_data, ignore_index=True)
        logger.info(f"Extracted {len(combined_data)} billing records from {len(allocation_files)} files")
        
        # Extract equipment rates
        rates_data = extract_equipment_rates(rates_file)
        
        # Generate master billing
        master_billing = generate_master_billing(combined_data, rates_data)
        
        # Export master billing file with division-specific sheets as requested
        # This will create a single Excel file with sheets named DFW, WTX, HOU, SELECT
        master_output_path = os.path.join(EXPORTS_DIR, f"MASTER_EQUIP_BILLINGS_{MONTH_NAME}_{YEAR}.xlsx")
        master_export_success = export_master_billing(master_billing, master_output_path, create_division_sheets=True)
        
        # Create exports dictionary with master billing file
        exports = {
            'MASTER': master_output_path if master_export_success else None
        }
        
        # Also create individual division export files for users who need them
        for division in DIVISIONS:
            division_data = filter_by_division(master_billing, division)
            if not division_data.empty:
                division_output_path = os.path.join(EXPORTS_DIR, f"{division}_EQUIP_BILLINGS_{MONTH_NAME}_{YEAR}.xlsx")
                if export_master_billing(division_data, division_output_path):
                    exports[division] = division_output_path
                    logger.info(f"Created {division} export with {len(division_data)} records")
        
        logger.info("PM Master Billing processing completed successfully")
        return {
            'success': True,
            'message': f"Successfully processed {len(allocation_files)} allocation files and generated {len(exports)} exports",
            'record_count': len(master_billing),
            'file_count': len(allocation_files),
            'exports': exports,
            'missing_rates': len(master_billing[(master_billing['Rate'] == 0) | (master_billing['Amount'] == 0)])
        }
    
    except Exception as e:
        logger.error(f"Error processing master billing: {str(e)}")
        return {
            'success': False,
            'message': f"Error processing master billing: {str(e)}",
            'exports': {}
        }

if __name__ == "__main__":
    # If run as a script, process all files
    result = process_master_billing()
    print(result)