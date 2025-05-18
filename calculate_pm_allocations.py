"""
Calculate PM Allocations with Proper Unit x Rate Calculation

This script focuses on the real allocation data from PM reviews and calculates
the proper billable amounts based on units x rate rather than using pre-calculated amounts.
"""
import os
import pandas as pd
import glob
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
ATTACHED_ASSETS_DIR = 'attached_assets'
EXPORTS_DIR = 'exports'
DEFAULT_COST_CODE = '9000 100F'
MONTH_NAME = 'APRIL'
YEAR = '2025'
DIVISIONS = ['DFW', 'HOU', 'WTX', 'SELECT']

# Output file names
FINALIZED_MASTER_ALLOCATION = f"FINALIZED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
MASTER_BILLINGS = f"MASTER_EQUIP_BILLINGS_{MONTH_NAME}_{YEAR}.xlsx"
REGION_IMPORT_PREFIX = "FINAL_REGION_IMPORT_"

def find_pm_allocation_files():
    """Find the final PM allocation files with highest priority to most recent revisions"""
    # Define priority patterns (highest priority first)
    priority_patterns = [
        "*FINAL*REVISION*05.15.2025*.xlsx",  # Final revisions on 5/15 are highest priority
        "*ALLOCATION*CODED*.xlsx",           # Coded files are second priority
        "*ALLOCATION*APRIL*2025*.xlsx",      # Regular allocation files
        "*BILLING*ALLOCATION*2025*.xlsx",    # Billing allocation files
    ]
    
    # Collect all matching files with priority info
    file_candidates = []
    for priority, pattern in enumerate(priority_patterns):
        matches = glob.glob(os.path.join(ATTACHED_ASSETS_DIR, pattern))
        for match in matches:
            file_candidates.append({
                'path': match,
                'priority': priority,
                'mtime': os.path.getmtime(match),
                'filename': os.path.basename(match)
            })
    
    # Sort by priority (lowest number first) and then by modification time (newest first)
    file_candidates.sort(key=lambda x: (x['priority'], -x['mtime']))
    
    # Log the found files
    if file_candidates:
        logger.info(f"Found {len(file_candidates)} allocation files")
        for file in file_candidates[:5]:  # Log the top 5 files
            logger.info(f"Priority {file['priority']}: {file['filename']}")
    else:
        logger.warning("No allocation files found matching priority patterns")
    
    # Also look for division-specific CSV files
    csv_files = []
    for division in DIVISIONS:
        pattern = os.path.join(ATTACHED_ASSETS_DIR, f"*{division}*APR*2025*.csv")
        matches = glob.glob(pattern)
        for match in matches:
            csv_files.append(match)
    
    if csv_files:
        logger.info(f"Found {len(csv_files)} division-specific CSV files")
    
    # Return the allocation Excel files and CSV files
    return [f['path'] for f in file_candidates] + csv_files

def load_equipment_rates():
    """Load equipment rates from available sources"""
    # Try to find the rates file
    rates_patterns = [
        "*EQUIP*RATES*.xlsx",
        "*EQ*RATES*.xlsx",
        "*RAGLE*EQ*BILLINGS*.xlsm"
    ]
    
    for pattern in rates_patterns:
        matches = glob.glob(os.path.join(ATTACHED_ASSETS_DIR, pattern))
        if matches:
            try:
                # For RAGLE file, look for the Equip Rates sheet
                if "RAGLE" in matches[0].upper():
                    xlsx = pd.ExcelFile(matches[0])
                    if "Equip Rates" in xlsx.sheet_names:
                        rates_df = pd.read_excel(matches[0], sheet_name="Equip Rates")
                        logger.info(f"Loaded equipment rates from {os.path.basename(matches[0])}")
                        
                        # Check column names to find equipment and rate columns
                        for eq_col in ['Equip #', 'Equipment', 'equip_id']:
                            if eq_col in rates_df.columns:
                                equip_col = eq_col
                                break
                        else:
                            equip_col = rates_df.columns[0]  # Fallback to first column
                        
                        for rate_col in ['Monthly Rate', 'Rate', 'rate']:
                            if rate_col in rates_df.columns:
                                rate_col_name = rate_col
                                break
                        else:
                            # Try to find a column with "rate" in the name
                            rate_cols = [c for c in rates_df.columns if 'rate' in c.lower()]
                            rate_col_name = rate_cols[0] if rate_cols else None
                        
                        if rate_col_name:
                            # Convert to dictionary mapping equipment ID to rate
                            rates_dict = dict(zip(rates_df[equip_col].astype(str), rates_df[rate_col_name]))
                            return rates_dict
                else:
                    # Generic rates file
                    rates_df = pd.read_excel(matches[0])
                    logger.info(f"Loaded equipment rates from {os.path.basename(matches[0])}")
                    
                    # Identify columns (assuming first column is equipment ID and second is rate)
                    equip_col = rates_df.columns[0]
                    rate_col = rates_df.columns[1]
                    
                    # Convert to dictionary
                    rates_dict = dict(zip(rates_df[equip_col].astype(str), rates_df[rate_col]))
                    return rates_dict
            except Exception as e:
                logger.error(f"Error loading rates from {matches[0]}: {str(e)}")
    
    # If we couldn't find a rates file, return an empty dictionary
    logger.warning("Could not find equipment rates file, will use default rates")
    return {}

def process_allocation_files():
    """Process PM allocation files and calculate correct amounts based on units x rate"""
    start_time = datetime.now()
    logger.info(f"Starting PM allocation processing at {start_time}")
    
    # Ensure exports directory exists
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    
    # Find all allocation files
    allocation_files = find_pm_allocation_files()
    if not allocation_files:
        logger.error("No allocation files found")
        return False
    
    # Load equipment rates
    rates_dict = load_equipment_rates()
    
    # Process each allocation file
    all_data = []
    equipment_set = set()  # Track processed equipment to avoid duplicates
    
    for file_path in allocation_files:
        try:
            logger.info(f"Processing {os.path.basename(file_path)}")
            
            # Load the data based on file type
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name=0)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_path}")
                continue
            
            # Skip empty dataframes
            if df.empty:
                logger.warning(f"Empty dataframe in {file_path}")
                continue
                
            # Identify the equipment ID column
            equip_id_col = None
            equip_id_candidates = ['equip_id', 'equip #', 'equip.', 'equipment', 'equipment #', 'equipment_number', 'Equipment_Number']
            
            for candidate in equip_id_candidates:
                matching_cols = [col for col in df.columns if str(col).lower() == candidate.lower()]
                if matching_cols:
                    equip_id_col = matching_cols[0]
                    break
            
            # If we still can't find the equipment column, try to infer from the data
            if not equip_id_col and len(df.columns) > 0:
                # Look for a column that might contain equipment IDs (typically first or second column)
                for i in range(min(3, len(df.columns))):
                    col = df.columns[i]
                    # Check if values in this column look like equipment IDs
                    if df[col].dtype == object and df[col].astype(str).str.match(r'^[A-Z0-9]+$').any():
                        equip_id_col = col
                        logger.info(f"Inferred equipment ID column: {equip_id_col}")
                        break
            
            if not equip_id_col:
                logger.warning(f"Could not identify equipment ID column in {file_path}")
                continue
            
            # Standardize column names
            column_mapping = {
                equip_id_col: 'equip_id',
                'desc': 'description',
                'equipment description': 'description',
                'cost code': 'cost_code',
                'costcode': 'cost_code',
                'cost_class': 'cost_class',
                'frequency': 'frequency',
                'freq': 'frequency',
                'hours': 'units',
                'amt': 'amount',
                'total': 'amount',
                'division': 'division'
            }
            
            # Rename columns that match our mapping
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df.rename(columns={old_col: new_col}, inplace=True)
            
            # Try to infer division from filename if not in columns
            if 'division' not in df.columns:
                for division in DIVISIONS:
                    if division in file_path.upper():
                        df['division'] = division
                        logger.info(f"Inferred division {division} from filename")
                        break
            
            # Filter out already processed equipment IDs to avoid duplicates
            if 'equip_id' in df.columns:
                # Convert equipment IDs to strings and drop NAs
                equipment_ids = df['equip_id'].dropna().astype(str).unique()
                new_equipment = [eq_id for eq_id in equipment_ids if eq_id not in equipment_set]
                
                if len(new_equipment) < len(equipment_ids):
                    logger.info(f"Skipping {len(equipment_ids) - len(new_equipment)} duplicate equipment IDs")
                    df = df[df['equip_id'].astype(str).isin(new_equipment)]
                
                # Add new equipment to the processed set
                equipment_set.update(new_equipment)
            
            # Apply default cost code where missing
            if 'cost_code' in df.columns:
                df['cost_code'] = df['cost_code'].fillna(DEFAULT_COST_CODE)
                mask = df['cost_code'].astype(str).str.contains('NEEDED|REQUIRE|TBD', na=False, case=False)
                df.loc[mask, 'cost_code'] = DEFAULT_COST_CODE
            
            # Make sure units column exists and is numeric
            if 'units' not in df.columns and 'Hours' in df.columns:
                df.rename(columns={'Hours': 'units'}, inplace=True)
            
            if 'units' in df.columns:
                df['units'] = pd.to_numeric(df['units'], errors='coerce').fillna(0)
            else:
                df['units'] = 0
            
            # Apply rates based on equipment ID and calculate amounts
            if 'equip_id' in df.columns:
                # See if rate column already exists
                if 'rate' not in df.columns and 'Rate' in df.columns:
                    df.rename(columns={'Rate': 'rate'}, inplace=True)
                
                if 'rate' not in df.columns:
                    # Create rate column by lookup from rates dictionary
                    df['rate'] = df['equip_id'].astype(str).map(rates_dict).fillna(0)
                else:
                    # Convert existing rate column to numeric
                    df['rate'] = pd.to_numeric(df['rate'], errors='coerce').fillna(0)
                
                # Calculate amount based on units * rate
                df['amount'] = df['units'] * df['rate']
                
                logger.info(f"Processed {len(df)} rows with total amount: ${df['amount'].sum():,.2f}")
            
            all_data.append(df)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
    
    if not all_data:
        logger.error("No data could be processed from allocation files")
        return False
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # Calculate total billable amount
    total_amount = combined_data['amount'].sum()
    logger.info(f"Total calculated billable amount: ${total_amount:,.2f}")
    
    # Generate the three required deliverables
    
    # 1. FINALIZED MASTER ALLOCATION SHEET
    master_allocation_path = os.path.join(EXPORTS_DIR, FINALIZED_MASTER_ALLOCATION)
    combined_data.to_excel(master_allocation_path, index=False, sheet_name='Master Allocation')
    logger.info(f"Generated Finalized Master Allocation Sheet: {master_allocation_path}")
    
    # 2. MASTER BILLINGS SHEET
    # Make sure all required columns exist
    required_columns = ['equip_id', 'description', 'date', 'job', 'cost_code', 'units', 'rate', 'amount', 'division']
    for col in required_columns:
        if col not in combined_data.columns:
            if col in ['rate', 'units', 'amount']:
                combined_data[col] = 0.0
            else:
                combined_data[col] = ''
    
    # Write the Master Billings Sheet
    master_billing_path = os.path.join(EXPORTS_DIR, MASTER_BILLINGS)
    combined_data.to_excel(master_billing_path, index=False, sheet_name='Equip Billings')
    logger.info(f"Generated Master Billings Sheet: {master_billing_path}")
    
    # 3. FINAL REGION IMPORT FILES for DFW, WTX, HOU
    for division in DIVISIONS[:3]:  # Just the first three divisions (DFW, WTX, HOU)
        # Filter data for this division
        if 'division' in combined_data.columns:
            division_data = combined_data[combined_data['division'] == division].copy()
            
            if not division_data.empty:
                # Prepare export columns
                export_cols = ['equip_id', 'date', 'job', 'cost_code', 'units', 'rate', 'amount']
                export_data = pd.DataFrame()
                
                for col in export_cols:
                    if col in division_data.columns:
                        export_data[col] = division_data[col]
                    else:
                        export_data[col] = ""
                
                # Rename columns for export format
                export_data.columns = ['Equipment_Number', 'Date', 'Job', 'Cost_Code', 'Hours', 'Rate', 'Amount']
                
                # Format date column
                if 'Date' in export_data.columns:
                    export_data['Date'] = pd.to_datetime(export_data['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                
                # Write to CSV
                output_path = os.path.join(EXPORTS_DIR, f"{REGION_IMPORT_PREFIX}{division}_{MONTH_NAME}_{YEAR}.csv")
                export_data.to_csv(output_path, index=False)
                
                division_total = export_data['Amount'].sum()
                logger.info(f"Generated {division} Import File: {output_path} with {len(export_data)} records - Total: ${division_total:,.2f}")
    
    # Summarize results
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    logger.info(f"Processing completed in {processing_time:.2f} seconds")
    logger.info(f"Final calculated billable amount: ${total_amount:,.2f}")
    
    return True

if __name__ == "__main__":
    process_allocation_files()