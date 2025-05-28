def validate_driver_row(row):
    required_fields = ["vehicle_type", "usage_type", "jobsite_id"]
    for field in required_fields:
        if field not in row or row[field] is None:
            return False, f"Missing or null field: {field}"
    return True, "OK"
