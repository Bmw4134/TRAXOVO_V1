"""
Driver Classifier Agent

This agent analyzes driver data to classify drivers based on various criteria
such as vehicle type, usage type, and job site assignment.
"""
import logging
import json
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle(data):
    """
    Process and classify driver data based on criteria
    
    Args:
        data (list): List of driver data dictionaries to classify
        
    Returns:
        dict: Results containing classified driver data
    """
    start_time = time.time()
    logger.info(f"Driver Classifier Agent processing {len(data) if data else 0} records")
    
    result = []
    for row in data:
        try:
            if not row.get("vehicle_type", "").lower() == "pickup truck":
                continue
            if not row.get("usage_type", "").lower() == "on-road":
                continue
            if not row.get("jobsite_id") or row.get("jobsite_id") == 0:
                continue
            result.append(row)
        except Exception as e:
            logger.error(f"Error processing row: {e}")
    
    processing_time = time.time() - start_time
    
    # Log usage
    log_usage(len(data) if data else 0, len(result), processing_time)
    
    return {"classified_drivers": result}

def run(data):
    """Alias for handle() function"""
    return handle(data)

def log_usage(input_count, output_count, processing_time):
    """
    Log agent usage statistics
    
    Args:
        input_count (int): Number of input records
        output_count (int): Number of output records
        processing_time (float): Processing time in seconds
    """
    usage_log = {
        "agent": "driver_classifier",
        "timestamp": datetime.now().isoformat(),
        "input_count": input_count,
        "output_count": output_count,
        "filtered_count": input_count - output_count,
        "processing_time": round(processing_time, 3),
        "records_per_second": round(input_count / processing_time, 2) if processing_time > 0 else 0
    }
    
    logger.info(f"Agent usage: {json.dumps(usage_log)}")
    
    # In a production environment, this could write to a database or external logging system
    try:
        with open("logs/agent_usage.log", "a") as f:
            f.write(json.dumps(usage_log) + "\n")
    except Exception as e:
        logger.warning(f"Could not write to agent usage log: {e}")

if __name__ == "__main__":
    # Example usage
    test_data = [
        {"driver_id": 1, "vehicle_type": "pickup truck", "usage_type": "on-road", "jobsite_id": 101},
        {"driver_id": 2, "vehicle_type": "sedan", "usage_type": "on-road", "jobsite_id": 102},
        {"driver_id": 3, "vehicle_type": "pickup truck", "usage_type": "off-road", "jobsite_id": 103},
        {"driver_id": 4, "vehicle_type": "pickup truck", "usage_type": "on-road", "jobsite_id": 0},
        {"driver_id": 5, "vehicle_type": "pickup truck", "usage_type": "on-road", "jobsite_id": 105}
    ]
    
    result = handle(test_data)
    print(f"Classified {len(result['classified_drivers'])} drivers out of {len(test_data)}")
    print(json.dumps(result, indent=2))