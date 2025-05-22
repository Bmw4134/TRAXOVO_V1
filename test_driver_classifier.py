"""
Test Driver Classifier Agent

This script tests the driver_classifier_agent to ensure it properly filters drivers
based on vehicle type, usage type, and job site ID criteria.
"""
import json
from agents.driver_classifier_agent import handle

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