# Simplified processor
def process_driver_data(data):
    cleaned = []
    for row in data:
        try:
            if not row.get("vehicle_type", "").lower() in ["pickup truck"]:
                continue
            if not row.get("usage_type", "").lower() == "on-road":
                continue
            if not row.get("jobsite_id") or row.get("jobsite_id") == 0:
                continue
            cleaned.append(row)
        except Exception as e:
            print(f"Skipping row due to error: {e}")
    return cleaned
