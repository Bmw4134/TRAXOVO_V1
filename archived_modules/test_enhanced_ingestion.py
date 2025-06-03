"""
Test for enhanced data ingestion module

This script tests the ability of the enhanced data ingestion module to handle
mixed-format files and normalize data from both CSV and Excel formats.
"""
import os
import logging
from utils.enhanced_data_ingestion import (
    load_data_file,
    normalize_time,
    is_fluff_row
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_time_normalization():
    """Test the time normalization function"""
    test_cases = [
        ("3:45 PM", "15:45"),
        ("03:45 PM", "15:45"),
        ("3:45 PM CT", "15:45"),
        ("3:45 AM", "03:45"),
        ("12:00 PM", "12:00"),
        ("12:00 AM", "00:00"),
        ("15:30", "15:30"),
        ("9:05", "09:05"),
        ("Invalid", None),
        (None, None),
    ]
    
    success = True
    for input_time, expected_output in test_cases:
        result = normalize_time(input_time)
        if result != expected_output:
            logger.error(f"Time normalization failed: '{input_time}' → '{result}' (expected '{expected_output}')")
            success = False
        else:
            logger.info(f"Time normalization passed: '{input_time}' → '{result}'")
    
    return success

def test_fluff_detection():
    """Test the fluff row detection function"""
    test_cases = [
        ([], True),
        ([""], True),
        (["", ""], True),
        (["------------------"], True),
        (["N/A", "Unknown", "#Error"], True),
        (["Data", "", ""], False),
        ({"col1": "", "col2": ""}, True),
        ({"col1": "Data", "col2": ""}, False),
    ]
    
    success = True
    for input_row, expected_output in test_cases:
        result = is_fluff_row(input_row)
        if result != expected_output:
            logger.error(f"Fluff detection failed: {input_row} → {result} (expected {expected_output})")
            success = False
        else:
            logger.info(f"Fluff detection passed: {type(input_row)} → {result}")
    
    return success

def test_file_loading():
    """Test loading data from sample files"""
    # Look for sample files in common locations
    sample_file_paths = []
    
    # Try to find CSV files
    for path in ["attached_assets", "data", "test_data", "."]:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith(".csv"):
                    sample_file_paths.append(os.path.join(path, file))
                if len(sample_file_paths) >= 2:
                    break
    
    # Try to find Excel files
    for path in ["attached_assets", "data", "test_data", "."]:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith(".xlsx") or file.endswith(".xls"):
                    sample_file_paths.append(os.path.join(path, file))
                if len(sample_file_paths) >= 5:
                    break
    
    # Use at most 5 sample files
    sample_file_paths = sample_file_paths[:5]
    
    if not sample_file_paths:
        logger.warning("No sample files found to test")
        return False
    
    success = True
    for file_path in sample_file_paths:
        logger.info(f"Testing file: {file_path}")
        data = load_data_file(file_path)
        
        if data:
            logger.info(f"Successfully loaded {len(data)} records from {file_path}")
            # Log a sample of the data
            if len(data) > 0:
                logger.info(f"Sample record: {list(data[0].items())[:5]}")
        else:
            logger.warning(f"No data loaded from {file_path}")
            success = False
    
    return success

def main():
    """Run all tests"""
    logger.info("Testing enhanced data ingestion module")
    
    # Run time normalization tests
    logger.info("\n=== Testing time normalization ===")
    time_test_result = test_time_normalization()
    
    # Run fluff detection tests
    logger.info("\n=== Testing fluff detection ===")
    fluff_test_result = test_fluff_detection()
    
    # Run file loading tests
    logger.info("\n=== Testing file loading ===")
    file_test_result = test_file_loading()
    
    # Overall result
    logger.info("\n=== Test Results ===")
    logger.info(f"Time normalization: {'PASSED' if time_test_result else 'FAILED'}")
    logger.info(f"Fluff detection: {'PASSED' if fluff_test_result else 'FAILED'}")
    logger.info(f"File loading: {'PASSED' if file_test_result else 'FAILED'}")
    
    overall_result = time_test_result and fluff_test_result and file_test_result
    logger.info(f"Overall result: {'PASSED' if overall_result else 'FAILED'}")
    
    return overall_result

if __name__ == "__main__":
    main()