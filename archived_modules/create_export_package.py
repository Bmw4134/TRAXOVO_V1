"""
Create Export Package

This script packages all the output files into a single zip file for easier download.
"""
import os
import zipfile
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
EXPORTS_DIR = 'exports'
MONTH_NAME = 'APRIL'
YEAR = '2025'
ZIP_FILENAME = f"PM_ALLOCATIONS_FINAL_PACKAGE_{MONTH_NAME}_{YEAR}.zip"

def create_export_package():
    """Create a zip package with all the export files"""
    # Check if exports directory exists
    if not os.path.exists(EXPORTS_DIR):
        logger.error(f"Exports directory not found: {EXPORTS_DIR}")
        return False
        
    # List of files to include in the package
    required_files = [
        f"FINALIZED_MASTER_ALLOCATION_SHEET_{MONTH_NAME}_{YEAR}.xlsx",
        f"MASTER_BILLINGS_SHEET_{MONTH_NAME}_{YEAR}.xlsx",
        f"FINAL_REGION_IMPORT_DFW_{MONTH_NAME}_{YEAR}.csv",
        f"FINAL_REGION_IMPORT_HOU_{MONTH_NAME}_{YEAR}.csv",
        f"FINAL_REGION_IMPORT_WT_{MONTH_NAME}_{YEAR}.csv",
        f"PM_REVISIONS_{MONTH_NAME}_{YEAR}.xlsx"
    ]
    
    # Check if all required files exist
    missing_files = []
    for file in required_files:
        file_path = os.path.join(EXPORTS_DIR, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing files: {', '.join(missing_files)}")
        return False
    
    # Create zip file
    zip_path = os.path.join(EXPORTS_DIR, ZIP_FILENAME)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in required_files:
            file_path = os.path.join(EXPORTS_DIR, file)
            # Add file to zip with just the filename (no path)
            zipf.write(file_path, arcname=file)
            logger.info(f"Added {file} to package")
    
    logger.info(f"Created export package: {zip_path}")
    
    # Check if ZIP file was created successfully
    if os.path.exists(zip_path):
        size_kb = os.path.getsize(zip_path) / 1024
        logger.info(f"Package size: {size_kb:.1f} KB")
        return True
    else:
        logger.error("Failed to create export package")
        return False

if __name__ == "__main__":
    if create_export_package():
        logger.info("Export package created successfully!")
    else:
        logger.error("Failed to create export package")