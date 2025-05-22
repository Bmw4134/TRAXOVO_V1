"""
Standalone test for driver classifier agent
"""
import json
import os
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle(data, config=None):
    """
    Process and classify driver data based on strict criteria
    
    Args:
        data (list): List of driver data dictionaries to classify
        config (dict, optional): Configuration parameters for classification
        
    Returns:
        dict: Results containing classified drivers, skipped records, and metrics
    """
    start_time = time.time()
    logger.info(f"Driver Classifier Agent processing {len(data) if data else 0} records")
    
    # Initialize result containers
    classified_drivers = []
    skipped_drivers = []
    error_count = 0
    
    # Initialize counters for skip reasons
    skip_reasons = {
        "not_pickup_truck": 0,
        "not_on_road": 0,
        "invalid_jobsite": 0,
        "error": 0
    }
    
    # Set default configuration if not provided
    if not config:
        config = {
            "strict_mode": True,
            "log_skipped": True
        }
    
    # Process each driver record
    for record in data if data else []:
        try:
            skip_reason = None
            
            # Apply filtering criteria with detailed tracing
            # 1. Check vehicle type - must be 'Pickup Truck'
            vehicle_type = str(record.get("vehicle_type", "")).lower().strip()
            if vehicle_type != "pickup truck":
                skip_reason = "not_pickup_truck"
                skip_reasons["not_pickup_truck"] += 1
            
            # 2. Check usage type - must be 'On-Road'
            elif str(record.get("usage_type", "")).lower().strip() != "on-road":
                skip_reason = "not_on_road"
                skip_reasons["not_on_road"] += 1
            
            # 3. Check jobsite ID - must be valid (not null, 0, 'Unknown', or empty string)
            elif (record.get("jobsite_id") is None or 
                  record.get("jobsite_id") == 0 or 
                  str(record.get("jobsite_id", "")).lower() in ["unknown", "none", "", "0"]):
                skip_reason = "invalid_jobsite"
                skip_reasons["invalid_jobsite"] += 1
            
            # Record passes all criteria - add to classified list
            if not skip_reason:
                # Add classification metadata
                record["classification"] = {
                    "status": "classified",
                    "timestamp": datetime.now().isoformat(),
                    "criteria_matched": [
                        "vehicle_type:pickup_truck",
                        "usage_type:on-road",
                        "valid_jobsite"
                    ]
                }
                classified_drivers.append(record)
            else:
                # Add skipped record with reason
                if config.get("log_skipped", True):
                    record["classification"] = {
                        "status": "skipped",
                        "reason": skip_reason,
                        "timestamp": datetime.now().isoformat()
                    }
                    skipped_drivers.append(record)
        
        except Exception as e:
            logger.error(f"Error processing driver record: {str(e)}")
            error_count += 1
            skip_reasons["error"] += 1
            
            if config.get("log_skipped", True):
                record_copy = record.copy() if isinstance(record, dict) else {"raw": str(record)}
                record_copy["classification"] = {
                    "status": "error",
                    "reason": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                skipped_drivers.append(record_copy)
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Prepare result structure
    result = {
        "classified_drivers": classified_drivers,
        "skipped": skipped_drivers,
        "count": len(classified_drivers),
        "metrics": {
            "total_processed": len(data) if data else 0,
            "classified_count": len(classified_drivers),
            "skipped_count": len(skipped_drivers),
            "skip_reasons": skip_reasons,
            "error_count": error_count,
            "processing_time_seconds": round(processing_time, 3)
        }
    }
    
    return result

def test_driver_classification():
    """Test driver classification with various test cases"""
    
    # Create test data with various combinations of criteria
    test_data = [
        # Valid record - should pass all criteria
        {
            "driver_id": 1, 
            "name": "John Doe", 
            "vehicle_type": "Pickup Truck", 
            "usage_type": "On-Road", 
            "jobsite_id": 101,
            "jobsite_name": "Main Construction Site"
        },
        
        # Invalid vehicle type
        {
            "driver_id": 2, 
            "name": "Jane Smith", 
            "vehicle_type": "Sedan", 
            "usage_type": "On-Road", 
            "jobsite_id": 102,
            "jobsite_name": "Downtown Project"
        },
        
        # Invalid usage type
        {
            "driver_id": 3, 
            "name": "Bob Johnson", 
            "vehicle_type": "Pickup Truck", 
            "usage_type": "Off-Road", 
            "jobsite_id": 103,
            "jobsite_name": "Mountain Site"
        },
        
        # Invalid jobsite ID (zero)
        {
            "driver_id": 4, 
            "name": "Alice Brown", 
            "vehicle_type": "Pickup Truck", 
            "usage_type": "On-Road", 
            "jobsite_id": 0,
            "jobsite_name": "Unassigned"
        },
        
        # Valid record
        {
            "driver_id": 5, 
            "name": "Charlie Davis", 
            "vehicle_type": "Pickup Truck", 
            "usage_type": "On-Road", 
            "jobsite_id": 105,
            "jobsite_name": "Bridge Project"
        },
        
        # Invalid jobsite ID ("Unknown")
        {
            "driver_id": 6, 
            "name": "Eve Wilson", 
            "vehicle_type": "Pickup Truck", 
            "usage_type": "On-Road", 
            "jobsite_id": "Unknown",
            "jobsite_name": "Unknown Location"
        },
        
        # Valid record
        {
            "driver_id": 7, 
            "name": "Frank Miller", 
            "vehicle_type": "Pickup Truck", 
            "usage_type": "On-Road", 
            "jobsite_id": 107,
            "jobsite_name": "Highway Extension"
        },
        
        # Case sensitivity test
        {
            "driver_id": 8, 
            "name": "Grace Taylor", 
            "vehicle_type": "pickup truck", 
            "usage_type": "on-road", 
            "jobsite_id": 108,
            "jobsite_name": "City Center"
        },
        
        # Whitespace test
        {
            "driver_id": 9, 
            "name": "Henry Clark", 
            "vehicle_type": " Pickup Truck ", 
            "usage_type": " On-Road ", 
            "jobsite_id": 109,
            "jobsite_name": "Suburban Development"
        },
        
        # Mixed case with special characters
        {
            "driver_id": 10, 
            "name": "Ivy Martin", 
            "vehicle_type": "Pick-up Truck", 
            "usage_type": "ON-road", 
            "jobsite_id": 110,
            "jobsite_name": "Corporate HQ"
        }
    ]
    
    # Run the classification
    result = handle(test_data)
    
    # Print summary
    print("\n=== DRIVER CLASSIFICATION TEST RESULTS ===")
    print(f"Total drivers tested: {result['metrics']['total_processed']}")
    print(f"Classified drivers: {result['metrics']['classified_count']}")
    print(f"Skipped drivers: {result['metrics']['skipped_count']}")
    print("\nSkip reasons:")
    for reason, count in result['metrics']['skip_reasons'].items():
        if count > 0:
            print(f"  - {reason}: {count}")
    
    print("\nClassified drivers:")
    for driver in result['classified_drivers']:
        print(f"  - Driver {driver['driver_id']}: {driver['name']} (Vehicle: {driver['vehicle_type']}, Job Site: {driver.get('jobsite_name', driver['jobsite_id'])})")
    
    # Write full results to file for detailed inspection
    with open("test_driver_classification_results.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("\nFull results written to test_driver_classification_results.json")
    
    return result

if __name__ == "__main__":
    test_driver_classification()