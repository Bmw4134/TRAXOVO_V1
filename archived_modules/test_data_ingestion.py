"""
TRAXORA Data Ingestion Test Script

This script demonstrates the use of the data ingestion module with various
Gauge report file formats.
"""
import os
import sys
import logging
import pandas as pd
from utils.data_ingestion import load_gauge_file, DataIngestionError

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('data_ingestion_test')

def test_file_ingestion(file_path):
    """Test ingestion of a specific file"""
    try:
        logger.info(f"Testing ingestion of file: {file_path}")
        
        # Load the file
        df = load_gauge_file(file_path)
        
        # Print summary information
        logger.info(f"Successfully loaded file with shape: {df.shape}")
        logger.info(f"Columns: {', '.join(df.columns[:10])}...")
        
        # Check for null values
        null_counts = df.isnull().sum()
        high_null_cols = null_counts[null_counts > df.shape[0] * 0.5].index.tolist()
        if high_null_cols:
            logger.warning(f"Columns with >50% null values: {', '.join(high_null_cols[:5])}...")
        
        # Show first 5 rows
        logger.info("First 5 rows:")
        print(df.head())
        print("\n" + "-"*80 + "\n")
        
        return True
    
    except DataIngestionError as e:
        logger.error(f"Data ingestion error: {str(e)}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def main():
    """Main test function"""
    # Get all Excel and CSV files in the attached_assets directory
    logger.info("Scanning for test files in attached_assets directory")
    
    file_count = 0
    success_count = 0
    
    test_dirs = ['attached_assets']
    if os.path.exists('test_data'):
        test_dirs.append('test_data')
    
    for test_dir in test_dirs:
        if not os.path.exists(test_dir):
            continue
            
        for file_name in os.listdir(test_dir):
            if file_name.endswith(('.xlsx', '.xls', '.csv')):
                file_path = os.path.join(test_dir, file_name)
                file_count += 1
                
                if test_file_ingestion(file_path):
                    success_count += 1
    
    # Print summary
    logger.info(f"Test completed: {success_count}/{file_count} files successfully processed")
    
    if file_count == 0:
        logger.warning("No test files found. Please add some Excel or CSV files to the attached_assets directory.")

if __name__ == "__main__":
    main()