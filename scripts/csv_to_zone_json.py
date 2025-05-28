import csv, json

def generate_zone_json(csv_path, rules_path, consolidated_path):
    zones = {}
    rules = []

    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            parent_id = row["Parent Zone ID"]
            if parent_id not in zones:
                zones[parent_id] = {"zone_id": parent_id, "subzones": []}
            zones[parent_id]["subzones"].append({
                "subzone_id": row["Subzone ID"],
                "description": row["Project Description"],
                "address": row["Site Address"],
                "latitude": float(row["Latitude"]),
                "longitude": float(row["Longitude"])
            })

            rules.append({
                "zone_id": parent_id,
                "start_time": "07:00",
                "end_time": "16:00",
                "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "late_threshold_minutes": 10,
                "early_leave_threshold_minutes": 15,
                "sr_pm": row.get("Project Manager", "unassigned")
            })

    with open(rules_path, 'w') as out_rules:
        json.dump(rules, out_rules, indent=2)

    with open(consolidated_path, 'w') as out_consolidated:
        json.dump(list(zones.values()), out_consolidated, indent=2)

# Example usage:
# generate_zone_json("zones.csv", "zone_schedule_rules.json", "consolidated_zones.json")
