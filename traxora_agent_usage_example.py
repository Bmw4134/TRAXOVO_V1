# 🧠 TRAXORA: Unified Agent Usage Example

# This script shows how to use the modular GENIUS CORE agents
# via the central `agent_controller` interface.

from agents import agent_controller

# Example input data
sample_data = [
    {"vehicle_type": "Pickup Truck", "usage_type": "On-Road", "jobsite_id": "123"},
    {"vehicle_type": "Van", "usage_type": "On-Road", "jobsite_id": "456"},
    {"vehicle_type": "Pickup Truck", "usage_type": "Off-Road", "jobsite_id": "0"},
    {"vehicle_type": "Pickup Truck", "usage_type": "On-Road", "jobsite_id": "Unknown"}
]

# 1. Classify drivers
classified = agent_controller.handle("driver_classifier", sample_data)
print("🚚 Classified Drivers:", classified)

# 2. Validate GPS (stubbed example)
gps_result = agent_controller.handle("geo_validator", {"coords": [123.4, -87.9], "geofence": [123.4, -87.9]})
print("📍 Geo Validation:", gps_result)

# 3. Generate report
report = agent_controller.handle("report_generator", classified.get("classified_drivers", []))
print("📊 Report:", report)

# 4. Format output
formatted = agent_controller.handle("output_formatter", report)
print("📝 Output:
", formatted)
