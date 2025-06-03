"""
Targeted TRAXORA Pipeline Test

This script tests the data ingestion and driver classification pipeline
using a specific sample file designed for testing all classification criteria.
"""
import os
import json
import logging
from datetime import datetime
from utils.enhanced_data_ingestion import load_data_file
from agents.driver_classifier_agent import handle as classify_drivers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_targeted_test():
    """Run a targeted test with a specific sample file"""
    
    # Use our sample test file
    test_file = "test_data/driver_classification_sample.csv"
    
    if not os.path.exists(test_file):
        logger.error(f"Test file not found: {test_file}")
        return
    
    logger.info("======= TRAXORA Targeted Pipeline Test =======")
    logger.info(f"Using test file: {test_file}")
    
    # Step 1: Load data using enhanced ingestion
    logger.info("\n--- Step 1: Enhanced Data Ingestion ---")
    data = load_data_file(test_file)
    
    if not data:
        logger.error("Failed to load test data")
        return
    
    logger.info(f"Successfully loaded {len(data)} driver records")
    logger.info(f"Sample record: {data[0]}")
    
    # Step 2: Run driver classification
    logger.info(f"\n--- Step 2: Driver Classification ---")
    logger.info(f"Classifying {len(data)} driver records")
    
    result = classify_drivers(data)
    
    # Step 3: Display results
    logger.info("\n--- Step 3: Results Analysis ---")
    
    classified_count = len(result.get("classified_drivers", []))
    skipped_count = len(result.get("skipped", []))
    
    logger.info(f"Total records processed: {len(data)}")
    logger.info(f"Drivers meeting all criteria: {classified_count}")
    logger.info(f"Drivers skipped (filtered out): {skipped_count}")
    
    # Display skip reasons
    if "metrics" in result and "skip_reasons" in result["metrics"]:
        logger.info("\nSkip reasons:")
        for reason, count in result["metrics"]["skip_reasons"].items():
            if count > 0:
                logger.info(f"  - {reason}: {count}")
    
    # Display all classified drivers
    if result.get("classified_drivers"):
        logger.info("\nAll classified drivers (passed filter criteria):")
        for driver in result["classified_drivers"]:
            logger.info(f"  ✓ Driver {driver.get('driver_id')}: {driver.get('name')} - {driver.get('vehicle_type')} - Job Site: {driver.get('jobsite_name', driver.get('jobsite_id'))}")
    
    # Display all skipped drivers with reasons
    if result.get("skipped"):
        logger.info("\nAll skipped drivers (filtered out):")
        for driver in result["skipped"]:
            logger.info(f"  ✗ Driver {driver.get('driver_id')}: {driver.get('name')} - {driver.get('vehicle_type')} - Reason: {driver.get('classification', {}).get('reason', 'unknown')}")
    
    # Write full results to file for detailed inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"targeted_test_results_{timestamp}.json"
    
    try:
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"\nFull results written to {output_file}")
    except Exception as e:
        logger.error(f"Error writing results to file: {str(e)}")
    
    return result

if __name__ == "__main__":
    run_targeted_test()