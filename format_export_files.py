"""
Format Export Files

This script takes the corrected master allocation sheet and creates regional import files
in the exact format required by the system.
"""
import os
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
EXPORTS_DIR = 'exports'
MONTH_NAME = 'APRIL'
YEAR = '2025'
MASTER_FILE = f"CORRECTED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx"

def get_equipment_description(equipment_id, sample_data):
    """Get equipment description from sample data"""
    matching_rows = sample_data[sample_data.iloc[:, 0] == equipment_id]
    if not matching_rows.empty:
        return matching_rows.iloc[0, 1]
    return f"Equipment {equipment_id}"

def format_export_files():
    """Create properly formatted export files from the corrected master allocation sheet"""
    # Load the corrected master allocation sheet
    master_path = os.path.join(EXPORTS_DIR, MASTER_FILE)
    if not os.path.exists(master_path):
        logger.error(f"Master allocation file not found: {master_path}")
        return
        
    master_df = pd.read_excel(master_path)
    logger.info(f"Loaded {len(master_df)} records from corrected master allocation sheet")
    
    # Load sample data for reference (to get equipment descriptions)
    sample_data = None
    try:
        sample_data = pd.read_csv('attached_assets/01 - DFW APR 2025.csv', header=None)
        logger.info("Loaded sample data for reference")
    except Exception as e:
        logger.warning(f"Could not load sample data for reference: {e}")
    
    # Generate export files for each division
    for division in ['DFW', 'HOU', 'WT']:
        division_data = master_df[master_df['Division'] == division].copy()
        
        if division_data.empty:
            logger.warning(f"No data found for division {division}")
            continue
        
        # Create export dataframe
        export_data = []
        
        # Process each row in the division data
        for _, row in division_data.iterrows():
            equipment_id = row['Equip #']
            job = row['Job']
            units = row['Units']
            rate = row['Rate']
            amount = row['Amount']
            # Get the cost code with proper handling for missing codes
            # This prioritizes PM sheet cost codes if available
            if 'Cost Code' in row and pd.notna(row['Cost Code']) and str(row['Cost Code']).strip() != "":
                cost_code = str(row['Cost Code']).strip()
                if "CC NEEDED" in cost_code.upper():
                    cost_code = '9000 100M'  # Default when cost code contains "CC NEEDED"
            else:
                cost_code = '9000 100M'  # Default when cost code is missing
            
            # Get equipment description
            equipment_desc = get_equipment_description(equipment_id, sample_data) if sample_data is not None else ""
            
            # Add row to export data
            export_data.append({
                'Equipment_Number': equipment_id,
                'Equipment_Description': equipment_desc,
                'Date': '4/30/2025',  # Last day of April for April billing
                'Job_Number': job,
                'Period': 1,  # Fixed value
                'Cost_Code': cost_code,
                'Month_Code': 4,  # April = month 4
                'Units': units,
                'Period_Type': 'MONTHLY',
                'Unit_Rate': rate,
                'Amount': amount
            })
        
        # Create export dataframe
        export_df = pd.DataFrame(export_data)
        
        # Export to CSV
        export_path = os.path.join(EXPORTS_DIR, f"CORRECTED_REGION_IMPORT_{division}_{MONTH_NAME}_{YEAR}.csv")
        export_df.to_csv(export_path, index=False)
        
        div_total = division_data['Amount'].sum()
        logger.info(f"Generated corrected {division} import file: {export_path} - {len(division_data)} records, Total: ${div_total:,.2f}")
    
    logger.info("Export files generated successfully!")

def main():
    """Main function"""
    format_export_files()
    
    # Recreate the zip package
    import zipfile
    
    # List of files to include
    files_to_package = [
        f"CORRECTED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx",
        f"ALLOCATION_ADJUSTMENTS_{MONTH_NAME}_{YEAR}.xlsx",
        f"CORRECTED_REGION_IMPORT_DFW_{MONTH_NAME}_{YEAR}.csv",
        f"CORRECTED_REGION_IMPORT_HOU_{MONTH_NAME}_{YEAR}.csv",
        f"CORRECTED_REGION_IMPORT_WT_{MONTH_NAME}_{YEAR}.csv"
    ]
    
    # Create zip file
    zip_filename = f"CORRECTED_PM_ALLOCATIONS_PACKAGE_{MONTH_NAME}_{YEAR}.zip"
    zip_path = os.path.join(EXPORTS_DIR, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_package:
            file_path = os.path.join(EXPORTS_DIR, file)
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=file)
                logger.info(f"Added {file} to package")
            else:
                logger.warning(f"File not found: {file}")
    
    logger.info(f"Created corrected export package: {zip_path}")
    
if __name__ == "__main__":
    main()