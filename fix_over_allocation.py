"""
Fix Over-Allocated Equipment

This script identifies and fixes equipment that has been allocated more than 1.0 units
total across all jobs. It adjusts the allocations to ensure no equipment exceeds 1.0 units.
"""
import os
import pandas as pd
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
EXPORTS_DIR = 'exports'
MONTH_NAME = 'APRIL'
YEAR = '2025'
MASTER_FILE = f"FINALIZED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
FIXED_FILE = f"CORRECTED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx"
ZIP_FILENAME = f"CORRECTED_PM_ALLOCATIONS_PACKAGE_{MONTH_NAME}_{YEAR}.zip"

def fix_over_allocations():
    """Fix equipment that has been allocated more than 1.0 units total"""
    master_path = os.path.join(EXPORTS_DIR, MASTER_FILE)
    if not os.path.exists(master_path):
        logger.error(f"Master allocation file not found: {master_path}")
        return None
        
    # Load the master allocation sheet
    df = pd.read_excel(master_path)
    logger.info(f"Loaded {len(df)} records from master allocation sheet")
    
    # Calculate total allocation per equipment
    equipment_totals = df.groupby('Equip #')['Units'].sum().reset_index()
    over_allocated = equipment_totals[equipment_totals['Units'] > 1.0]
    
    if len(over_allocated) == 0:
        logger.info("No over-allocated equipment found!")
        return df
        
    logger.info(f"Found {len(over_allocated)} pieces of equipment with allocations > 1.0")
    
    # Create a copy of the dataframe to modify
    fixed_df = df.copy()
    
    # Track the adjustments
    adjustments = []
    
    # Process each over-allocated equipment
    for _, row in over_allocated.iterrows():
        equip_id = row['Equip #']
        total_units = row['Units']
        
        logger.info(f"Fixing {equip_id} with total allocation of {total_units}")
        
        # Get all rows for this equipment
        equip_rows = fixed_df[fixed_df['Equip #'] == equip_id].copy()
        
        # Sort by Units descending to start with largest allocations
        equip_rows = equip_rows.sort_values('Units', ascending=False)
        
        # Calculate scaling factor to bring total to 1.0
        scaling_factor = 1.0 / total_units
        
        # Track old and new allocations
        old_allocations = []
        new_allocations = []
        
        # Apply scaling to each row
        for idx, job_row in equip_rows.iterrows():
            job = job_row['Job']
            old_units = job_row['Units']
            old_allocations.append((job, old_units))
            
            # Calculate new units (scaled proportionally)
            new_units = round(old_units * scaling_factor, 2)
            
            # Update the dataframe
            fixed_df.at[idx, 'Units'] = new_units
            
            # Update the amount based on rate
            rate = job_row['Rate']
            fixed_df.at[idx, 'Amount'] = new_units * rate
            
            new_allocations.append((job, new_units))
            
            logger.info(f"  {equip_id} on job {job}: {old_units} → {new_units}")
        
        # Add to adjustments list
        adjustments.append({
            'Equip ID': equip_id,
            'Old Total': total_units,
            'New Total': sum(na[1] for na in new_allocations),
            'Old Allocations': ', '.join([f"{job}: {units}" for job, units in old_allocations]),
            'New Allocations': ', '.join([f"{job}: {units}" for job, units in new_allocations])
        })
    
    # Create adjustments dataframe
    adjustments_df = pd.DataFrame(adjustments)
    
    # Save the adjustments to Excel
    adjustments_path = os.path.join(EXPORTS_DIR, f"ALLOCATION_ADJUSTMENTS_{MONTH_NAME}_{YEAR}.xlsx")
    adjustments_df.to_excel(adjustments_path, index=False)
    logger.info(f"Saved allocation adjustments to {adjustments_path}")
    
    # Verify the fix worked
    new_totals = fixed_df.groupby('Equip #')['Units'].sum().reset_index()
    still_over = new_totals[new_totals['Units'] > 1.01]  # Allow a small margin for floating point errors
    
    if len(still_over) > 0:
        logger.warning(f"There are still {len(still_over)} over-allocated equipment!")
        for _, row in still_over.iterrows():
            logger.warning(f"  {row['Equip #']}: {row['Units']}")
    else:
        logger.info("All equipment allocations have been fixed!")
    
    return fixed_df

def recalculate_division_totals(df):
    """Recalculate division totals after fixing allocations"""
    dfw_total = df[df['Division'] == 'DFW']['Amount'].sum()
    hou_total = df[df['Division'] == 'HOU']['Amount'].sum()
    wt_total = df[df['Division'] == 'WT']['Amount'].sum()
    
    logger.info(f"Updated division totals after fixing allocations:")
    logger.info(f"DFW: ${dfw_total:,.2f}")
    logger.info(f"HOU: ${hou_total:,.2f}")
    logger.info(f"WT: ${wt_total:,.2f}")
    logger.info(f"Combined: ${dfw_total + hou_total + wt_total:,.2f}")
    
    return {
        'DFW': dfw_total,
        'HOU': hou_total,
        'WT': wt_total,
        'Total': dfw_total + hou_total + wt_total
    }

def generate_corrected_deliverables(df):
    """Generate corrected deliverables with fixed allocations"""
    # 1. Save corrected master allocation sheet
    fixed_master_path = os.path.join(EXPORTS_DIR, FIXED_FILE)
    df.to_excel(fixed_master_path, index=False)
    logger.info(f"Saved corrected master allocation sheet: {fixed_master_path}")
    
    # 2. Generate corrected region import files
    for division in ['DFW', 'HOU', 'WT']:
        division_data = df[df['Division'] == division].copy()
        
        if not division_data.empty:
            # Create export dataframe with required columns
            import_df = pd.DataFrame()
            
            # Map columns for export
            import_mapping = {
                'Equip #': 'Equipment_Number',
                'Equipment': 'Equipment_Description',
                'Job': 'Job_Number',
                'Job Description': 'Job_Description',
                'Units': 'Units',
                'Rate': 'Unit_Rate',
                'Amount': 'Amount',
                'Cost Code': 'Cost_Code'
            }
            
            # Copy and rename columns
            for src, target in import_mapping.items():
                if src in division_data.columns:
                    import_df[target] = division_data[src]
            
            # Export to CSV
            import_path = os.path.join(EXPORTS_DIR, f"CORRECTED_REGION_IMPORT_{division}_{MONTH_NAME}_{YEAR}.csv")
            import_df.to_csv(import_path, index=False)
            
            div_total = division_data['Amount'].sum()
            logger.info(f"Generated corrected {division} import file: {import_path} - {len(division_data)} records, Total: ${div_total:,.2f}")
    
    logger.info("All corrected deliverables generated successfully!")

def create_corrected_package():
    """Create a zip file with all corrected deliverables"""
    # List of files to include
    files_to_package = [
        f"CORRECTED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx",
        f"ALLOCATION_ADJUSTMENTS_{MONTH_NAME}_{YEAR}.xlsx",
        f"CORRECTED_REGION_IMPORT_DFW_{MONTH_NAME}_{YEAR}.csv",
        f"CORRECTED_REGION_IMPORT_HOU_{MONTH_NAME}_{YEAR}.csv",
        f"CORRECTED_REGION_IMPORT_WT_{MONTH_NAME}_{YEAR}.csv"
    ]
    
    # Check if all files exist
    missing_files = []
    for file in files_to_package:
        file_path = os.path.join(EXPORTS_DIR, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing files: {', '.join(missing_files)}")
        return False
    
    # Create zip file
    import zipfile
    
    zip_path = os.path.join(EXPORTS_DIR, ZIP_FILENAME)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_package:
            file_path = os.path.join(EXPORTS_DIR, file)
            zipf.write(file_path, arcname=file)
            logger.info(f"Added {file} to package")
    
    logger.info(f"Created corrected export package: {zip_path}")
    
    # Check if ZIP file was created successfully
    if os.path.exists(zip_path):
        size_kb = os.path.getsize(zip_path) / 1024
        logger.info(f"Package size: {size_kb:.1f} KB")
        return True
    else:
        logger.error("Failed to create export package")
        return False

def main():
    """Main function"""
    # Fix over-allocated equipment
    fixed_df = fix_over_allocations()
    if fixed_df is None:
        logger.error("Failed to fix over-allocations")
        return
    
    # Recalculate division totals
    recalculate_division_totals(fixed_df)
    
    # Generate corrected deliverables
    generate_corrected_deliverables(fixed_df)
    
    # Create corrected package
    create_corrected_package()
    
    logger.info("Corrected PM allocations process complete!")

if __name__ == "__main__":
    main()