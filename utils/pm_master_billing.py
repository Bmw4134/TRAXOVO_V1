"""
PM Master Billing Processor

This module processes multiple PM allocation files to create a consolidated
master billing report and generates division-specific exports.

Features:
- Extracts data from all PM allocation files
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

# Set up logger
logger = logging.getLogger(__name__)

# Constants
ATTACHED_ASSETS_DIR = Path('attached_assets')
EXPORTS_DIR = Path('exports/pm_master')
DIVISIONS = ['DFW', 'HOU', 'WTX', 'SELECT']
MONTH_NAME = 'APRIL'  # Default month for current processing
YEAR = '2025'  # Default year for current processing

# Ensure exports directory exists
EXPORTS_DIR.mkdir(exist_ok=True, parents=True)

# Column mapping for standardization across different source files
COLUMN_MAPPING = {
    'equip_id': ['EQ#', 'EQ #', 'EQUIPMENT #', 'EQUIP #', 'EQUIP. #', 'EQUIPMENT_ID', 'EQUIPMENT NUMBER'],
    'description': ['DESCRIPTION', 'DESC', 'EQUIPMENT DESC', 'EQUIP DESCRIPTION'],
    'job': ['JOB', 'JOB #', 'PROJECT', 'JOB_NUMBER', 'JOB_CODE', 'JOB CODE', 'JOB NUMBER'],
    'date': ['DATE', 'START DATE', 'START', 'BEGIN DATE', 'ALLOCATION DATE'],
    'units': ['UNITS', 'DAYS', 'HRS', 'HOURS', 'QUANTITY'],
    'frequency': ['FREQUENCY', 'RATE TYPE', 'BILLING TYPE', 'BILL TYPE', 'FREQUENCY TYPE'],
    'amount': ['AMOUNT', 'TOTAL', 'EXTENDED', 'EXTENDED AMOUNT', 'EXTENDED PRICE', 'COST'],
    'rate': ['RATE', 'UNIT PRICE', 'PRICE', 'UNIT RATE', 'RATE AMOUNT'],
    'division': ['DIVISION', 'DIV', 'REGION', 'LOCATION', 'BRANCH'],
    'cost_code': ['COST CODE', 'COSTCODE', 'ACCT CODE', 'ACCOUNT CODE'],
    'phase': ['PHASE', 'PH', 'PHASE CODE']
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
        col_str = str(col).upper()
        for pattern in patterns:
            if re.search(pattern, col_str, re.IGNORECASE):
                return col
    return None

def find_all_allocation_files():
    """Find all EQMO allocation files in the attached_assets directory"""
    allocation_files = []
    
    # Look for Excel files containing EQMO and BILLING ALLOCATIONS in the filename
    pattern = os.path.join(ATTACHED_ASSETS_DIR, '*EQMO*BILLING*ALLOCATIONS*.xlsx')
    files = glob.glob(pattern)
    
    logger.info(f"Found {len(files)} allocation files matching pattern")
    return files

def find_equipment_rates_file():
    """Find the equipment rates file or master billing workbook"""
    # Look for the monthly billing working spreadsheet first
    pattern = os.path.join(ATTACHED_ASSETS_DIR, '*EQ*MONTHLY*BILLINGS*WORKING*.xlsx')
    files = glob.glob(pattern)
    
    if files:
        logger.info(f"Found equipment rates in monthly billing spreadsheet: {os.path.basename(files[0])}")
        return files[0]
    
    # If not found, look for equipment rates file
    pattern = os.path.join(ATTACHED_ASSETS_DIR, '*EQUIPMENT*RATES*.xlsx')
    files = glob.glob(pattern)
    
    if files:
        logger.info(f"Found equipment rates file: {os.path.basename(files[0])}")
        return files[0]
    
    logger.warning("Equipment rates file not found. Will proceed without rates.")
    return None

def extract_equipment_rates(rates_file):
    """Extract equipment rates from the rates file"""
    if not rates_file:
        return pd.DataFrame()
    
    try:
        # Load the workbook
        wb = openpyxl.load_workbook(rates_file, data_only=True)
        
        # Look for the rates sheet - it's either named "Equip Rates" or contains "RATES" in the name
        rates_sheet = None
        for sheet_name in wb.sheetnames:
            if 'EQUIP RATES' in sheet_name.upper() or 'RATES' in sheet_name.upper():
                rates_sheet = sheet_name
                break
        
        if not rates_sheet:
            rates_sheet = wb.sheetnames[0]  # Default to first sheet
            
        logger.info(f"Using sheet '{rates_sheet}' for equipment rates")
        
        # Load the sheet into a DataFrame
        df = pd.read_excel(rates_file, sheet_name=rates_sheet)
        
        # Find the equipment ID and rate columns
        equip_col = find_matching_column(df, COLUMN_MAPPING['equip_id'])
        
        # Look for rate columns (monthly, hourly, daily, weekly)
        rate_columns = {}
        for col in df.columns:
            col_str = str(col).upper()
            if 'MONTHLY' in col_str or 'MO RATE' in col_str or 'MONTH RATE' in col_str:
                rate_columns['MONTHLY'] = col
            elif 'HOURLY' in col_str or 'HR RATE' in col_str or 'HOUR RATE' in col_str:
                rate_columns['HOURLY'] = col
            elif 'DAILY' in col_str or 'DAY RATE' in col_str:
                rate_columns['DAILY'] = col
            elif 'WEEKLY' in col_str or 'WK RATE' in col_str or 'WEEK RATE' in col_str:
                rate_columns['WEEKLY'] = col
        
        # Create a clean rates DataFrame
        if equip_col and rate_columns:
            # Get equipment IDs and rates
            rates_data = []
            for _, row in df.iterrows():
                equip_id = row[equip_col]
                if pd.notna(equip_id):
                    equip_rates = {'EQUIPMENT_ID': str(equip_id).strip()}
                    for rate_type, rate_col in rate_columns.items():
                        rate = row[rate_col] if pd.notna(row[rate_col]) else 0
                        equip_rates[rate_type + '_RATE'] = rate
                    rates_data.append(equip_rates)
            
            return pd.DataFrame(rates_data)
        else:
            logger.warning("Could not identify equipment ID or rate columns in rates file")
            return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error extracting equipment rates: {str(e)}")
        return pd.DataFrame()

def process_allocation_file(file_path):
    """Process a single allocation file to extract equipment billing data"""
    file_name = os.path.basename(file_path)
    logger.info(f"Processing allocation file: {file_name}")
    
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Find the key columns
        equip_col = find_matching_column(df, COLUMN_MAPPING['equip_id'])
        desc_col = find_matching_column(df, COLUMN_MAPPING['description'])
        job_col = find_matching_column(df, COLUMN_MAPPING['job'])
        date_col = find_matching_column(df, COLUMN_MAPPING['date'])
        units_col = find_matching_column(df, COLUMN_MAPPING['units'])
        freq_col = find_matching_column(df, COLUMN_MAPPING['frequency'])
        amount_col = find_matching_column(df, COLUMN_MAPPING['amount'])
        rate_col = find_matching_column(df, COLUMN_MAPPING['rate'])
        div_col = find_matching_column(df, COLUMN_MAPPING['division'])
        cost_code_col = find_matching_column(df, COLUMN_MAPPING['cost_code'])
        phase_col = find_matching_column(df, COLUMN_MAPPING['phase'])
        
        if not equip_col:
            logger.warning(f"Equipment ID column not found in {file_name}")
            return pd.DataFrame()
        
        # Extract job code from filename if not found in the data
        job_from_filename = None
        for part in file_name.split():
            if part.startswith('202') and '-' in part:
                job_from_filename = part
                break
        
        # Infer division from filename if not found in the data
        div_from_filename = None
        for div in DIVISIONS:
            if div in file_name.upper():
                div_from_filename = div
                break
        
        # Process each row to extract billing data
        billing_data = []
        for idx, row in df.iterrows():
            # Skip rows without equipment ID
            if equip_col and (not pd.notna(row[equip_col]) or str(row[equip_col]).strip() == ''):
                continue
            
            equip_id = str(row[equip_col]).strip() if equip_col else ""
            description = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else ""
            job = str(row[job_col]).strip() if job_col and pd.notna(row[job_col]) else job_from_filename or ""
            date = row[date_col] if date_col and pd.notna(row[date_col]) else datetime.now()
            units = float(row[units_col]) if units_col and pd.notna(row[units_col]) else 0
            frequency = str(row[freq_col]).strip().upper() if freq_col and pd.notna(row[freq_col]) else "MONTHLY"
            amount = float(row[amount_col]) if amount_col and pd.notna(row[amount_col]) else 0
            rate = float(row[rate_col]) if rate_col and pd.notna(row[rate_col]) else 0
            division = str(row[div_col]).strip().upper() if div_col and pd.notna(row[div_col]) else div_from_filename or ""
            cost_code = str(row[cost_code_col]).strip() if cost_code_col and pd.notna(row[cost_code_col]) else ""
            phase = str(row[phase_col]).strip() if phase_col and pd.notna(row[phase_col]) else ""
            
            # Standardize frequency
            if frequency in FREQUENCY_MAPPING:
                frequency = FREQUENCY_MAPPING[frequency]
            elif any(freq in frequency for freq in FREQUENCY_MAPPING.keys()):
                for key, value in FREQUENCY_MAPPING.items():
                    if key in frequency:
                        frequency = value
                        break
            else:
                frequency = "MONTHLY"  # Default to monthly if unknown
            
            # Calculate amount if not available but rate and units are
            if amount == 0 and rate > 0 and units > 0:
                amount = rate * units
            
            # Calculate rate if not available but amount and units are
            if rate == 0 and amount > 0 and units > 0:
                rate = amount / units
            
            # Format date correctly
            if isinstance(date, str):
                try:
                    date = datetime.strptime(date, '%Y-%m-%d')
                except:
                    try:
                        date = datetime.strptime(date, '%m/%d/%Y')
                    except:
                        date = datetime.now()
            
            # Add to billing data
            billing_data.append({
                'EQUIPMENT_ID': equip_id,
                'DESCRIPTION': description,
                'JOB': job,
                'DATE': date,
                'UNITS': units,
                'FREQUENCY': frequency,
                'RATE': rate,
                'AMOUNT': amount,
                'DIVISION': division,
                'COST_CODE': cost_code,
                'PHASE': phase,
                'SOURCE_FILE': file_name
            })
        
        return pd.DataFrame(billing_data)
    
    except Exception as e:
        logger.error(f"Error processing allocation file {file_name}: {str(e)}")
        return pd.DataFrame()

def generate_master_billing(allocation_data, rates_data):
    """Generate the master billing dataset by applying rates to allocation data"""
    # Create a copy of the allocation data
    master_billing = allocation_data.copy()
    
    # Add rates if available
    if not rates_data.empty:
        # Create a lookup dictionary for rates
        rates_lookup = {}
        for _, row in rates_data.iterrows():
            equip_id = row['EQUIPMENT_ID']
            rates = {}
            for rate_type in ['MONTHLY_RATE', 'HOURLY_RATE', 'DAILY_RATE', 'WEEKLY_RATE']:
                if rate_type in row.index and pd.notna(row[rate_type]):
                    rates[rate_type] = row[rate_type]
            rates_lookup[equip_id] = rates
        
        # Apply rates to master billing
        for idx, row in master_billing.iterrows():
            equip_id = row['EQUIPMENT_ID']
            frequency = row['FREQUENCY']
            
            # Skip if already has rate and amount
            if row['RATE'] > 0 and row['AMOUNT'] > 0:
                continue
            
            # Look up rates for this equipment
            if equip_id in rates_lookup:
                rate_key = frequency + '_RATE'
                rate_key = rate_key.replace('LY_', '_')  # Remove 'ly' from frequency
                
                # Find the most appropriate rate
                rate = 0
                if rate_key in rates_lookup[equip_id]:
                    rate = rates_lookup[equip_id][rate_key]
                elif 'MONTHLY_RATE' in rates_lookup[equip_id]:
                    rate = rates_lookup[equip_id]['MONTHLY_RATE']  # Default to monthly rate
                
                # Update rate and calculate amount
                if rate > 0:
                    master_billing.at[idx, 'RATE'] = rate
                    master_billing.at[idx, 'AMOUNT'] = rate * row['UNITS']
    
    # Log missing rates
    missing_rates = master_billing[(master_billing['RATE'] == 0) | (master_billing['AMOUNT'] == 0)]
    if not missing_rates.empty:
        logger.warning(f"Missing rates for {len(missing_rates)} equipment items")
        for _, row in missing_rates.iterrows():
            logger.warning(f"  - Missing rate for {row['EQUIPMENT_ID']} ({row['DESCRIPTION']}) - Job: {row['JOB']}")
    
    return master_billing

def filter_by_division(master_billing, division):
    """Filter the master billing data by division"""
    if division.upper() == 'ALL':
        return master_billing
    
    return master_billing[master_billing['DIVISION'].str.upper() == division.upper()]

def export_master_billing(master_billing, output_path):
    """Export the master billing data to Excel"""
    try:
        # Create a workbook and add a worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Master Billing"
        
        # Define column headers
        headers = [
            'DIVISION', 'EQUIPMENT_ID', 'DESCRIPTION', 'DATE', 'JOB', 
            'PHASE', 'COST_CODE', 'UNITS', 'FREQUENCY', 'RATE', 'AMOUNT', 
            'SOURCE_FILE'
        ]
        
        # Add headers
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E6F0F8", end_color="E6F0F8", fill_type="solid")
        
        # Add data
        for row_idx, row in master_billing.iterrows():
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=row_idx + 2, column=col_idx)
                
                value = row[header] if header in row else ""
                
                # Format date
                if header == 'DATE' and isinstance(value, (datetime, pd.Timestamp)):
                    cell.value = value.strftime('%Y-%m-%d')
                # Format numbers
                elif header in ['UNITS', 'RATE', 'AMOUNT']:
                    cell.value = float(value) if pd.notna(value) else 0
                    cell.number_format = '#,##0.00'
                else:
                    cell.value = value
        
        # Auto-adjust column widths
        for col_idx, _ in enumerate(headers, 1):
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = 15
        
        # Add total row
        total_row = len(master_billing) + 2
        ws.cell(row=total_row, column=1).value = "TOTAL"
        ws.cell(row=total_row, column=1).font = Font(bold=True)
        
        # Add total formula for amount
        amount_col = headers.index('AMOUNT') + 1
        ws.cell(row=total_row, column=amount_col).value = f"=SUM({get_column_letter(amount_col)}2:{get_column_letter(amount_col)}{total_row-1})"
        ws.cell(row=total_row, column=amount_col).font = Font(bold=True)
        ws.cell(row=total_row, column=amount_col).number_format = '#,##0.00'
        
        # Save the workbook
        wb.save(output_path)
        logger.info(f"Master billing exported to {output_path}")
        
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
        
        output_path = os.path.join(EXPORTS_DIR, f"{division}_EQUIP_BILLINGS_{MONTH_NAME}_{timestamp}.xlsx")
        if export_master_billing(division_data, output_path):
            export_paths[division] = output_path
    
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
        
        # Create timestamp for export files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export master billing file
        master_output_path = os.path.join(EXPORTS_DIR, f"MASTER_EQUIP_BILLINGS_{MONTH_NAME}_{timestamp}.xlsx")
        master_export_success = export_master_billing(master_billing, master_output_path)
        
        # Generate division exports
        division_exports = generate_division_exports(master_billing)
        
        # Create combined exports dictionary
        exports = {
            'MASTER': master_output_path if master_export_success else None,
            **division_exports
        }
        
        return {
            'success': True,
            'message': f"Successfully processed {len(allocation_files)} allocation files and generated {len(exports)} exports",
            'record_count': len(master_billing),
            'file_count': len(allocation_files),
            'exports': exports,
            'missing_rates': len(master_billing[(master_billing['RATE'] == 0) | (master_billing['AMOUNT'] == 0)])
        }
    
    except Exception as e:
        logger.error(f"Error processing master billing: {str(e)}")
        return {
            'success': False,
            'message': f"Error processing master billing: {str(e)}",
            'exports': {}
        }

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Process all files
    result = process_master_billing()
    
    # Print results
    print("\nProcessing completed.")
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    
    if result['success']:
        print(f"\nProcessed {result['file_count']} files and extracted {result['record_count']} billing records")
        print(f"Missing rates for {result['missing_rates']} records")
        
        print("\nExports generated:")
        for division, path in result['exports'].items():
            if path:
                print(f"  - {division}: {os.path.basename(path)}")