"""
TRAXORA Integration Test: Data Ingestion + Driver Classification Pipeline

This script demonstrates the full pipeline from data ingestion to driver classification,
showing how the enhanced data ingestion module and driver classifier agent work together.
"""
import os
import json
import logging
from datetime import datetime
from utils.enhanced_data_ingestion import load_data_file, batch_load_data_files
from agents.driver_classifier_agent import handle as classify_drivers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_pipeline_test(file_paths=None):
    """
    Run the data ingestion and driver classification pipeline
    
    Args:
        file_paths (list): Optional list of file paths to use for testing
    """
    # If no files provided, look for sample files in common locations
    if not file_paths:
        file_paths = []
        
        # Look for CSV files in attached_assets and other directories
        for path in ["attached_assets", "data", "test_data", "uploads"]:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.lower().endswith(".csv") and "time" in file.lower():
                        file_paths.append(os.path.join(path, file))
                    if len(file_paths) >= 2:
                        break
        
        # Look for Excel files in attached_assets and other directories
        for path in ["attached_assets", "data", "test_data", "uploads"]:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if (file.lower().endswith(".xlsx") or file.lower().endswith(".xls")) and "time" in file.lower():
                        file_paths.append(os.path.join(path, file))
                    if len(file_paths) >= 3:
                        break
    
    # Use at most 3 sample files
    file_paths = file_paths[:3]
    
    if not file_paths:
        logger.error("No suitable test files found")
        return
    
    logger.info("======= TRAXORA Pipeline Test: Data Ingestion → Driver Classification =======")
    logger.info(f"Using test files: {', '.join(file_paths)}")
    
    # Step 1: Load data using enhanced ingestion
    logger.info("\n--- Step 1: Enhanced Data Ingestion ---")
    all_data = []
    
    for file_path in file_paths:
        logger.info(f"Loading file: {file_path}")
        data = load_data_file(file_path)
        
        if data:
            logger.info(f"Successfully loaded {len(data)} records from {file_path}")
            # Add minimal required fields if not present (for testing purposes)
            for record in data:
                if "vehicle_type" not in record and "asset_type" in record:
                    record["vehicle_type"] = record["asset_type"]
                if "usage_type" not in record:
                    record["usage_type"] = "On-Road"  # Default for testing
                if "jobsite_id" not in record and "job_id" in record:
                    record["jobsite_id"] = record["job_id"]
                
            all_data.extend(data)
    
    if not all_data:
        logger.error("No data loaded from any file")
        return
    
    # Step 2: Run driver classification
    logger.info(f"\n--- Step 2: Driver Classification ---")
    logger.info(f"Classifying {len(all_data)} driver records")
    
    # Try to classify with the available data
    result = classify_drivers(all_data)
    
    # Step 3: Display results
    logger.info("\n--- Step 3: Results Analysis ---")
    
    classified_count = len(result.get("classified_drivers", []))
    skipped_count = len(result.get("skipped", []))
    
    logger.info(f"Total records processed: {len(all_data)}")
    logger.info(f"Drivers meeting all criteria: {classified_count}")
    logger.info(f"Drivers skipped (filtered out): {skipped_count}")
    
    # Display skip reasons
    if "metrics" in result and "skip_reasons" in result["metrics"]:
        logger.info("\nSkip reasons:")
        for reason, count in result["metrics"]["skip_reasons"].items():
            if count > 0:
                logger.info(f"  - {reason}: {count}")
    
    # Display sample of classified drivers
    if result.get("classified_drivers"):
        logger.info("\nSample of classified drivers:")
        for driver in result["classified_drivers"][:3]:
            # Create a simplified view of the driver data
            simplified = {
                "driver_id": driver.get("driver_id"),
                "name": driver.get("name"),
                "vehicle_type": driver.get("vehicle_type"),
                "usage_type": driver.get("usage_type"),
                "jobsite_id": driver.get("jobsite_id"),
                "jobsite_name": driver.get("jobsite_name", "N/A")
            }
            logger.info(f"  ✓ {simplified}")
    
    # Display sample of skipped drivers
    if result.get("skipped"):
        logger.info("\nSample of skipped drivers:")
        for driver in result["skipped"][:3]:
            # Create a simplified view of the driver data
            simplified = {
                "driver_id": driver.get("driver_id"),
                "name": driver.get("name"),
                "vehicle_type": driver.get("vehicle_type"),
                "usage_type": driver.get("usage_type"),
                "jobsite_id": driver.get("jobsite_id"),
                "reason": driver.get("classification", {}).get("reason", "unknown")
            }
            logger.info(f"  ✗ {simplified}")
    
    # Write full results to file for reference
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"pipeline_test_results_{timestamp}.json"
    
    try:
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"\nFull results written to {output_file}")
    except Exception as e:
        logger.error(f"Error writing results to file: {str(e)}")
    
    # Return results for further analysis if needed
    return result

if __name__ == "__main__":
    run_pipeline_test()