# qq_fix_planner.py
import json
from datetime import datetime

class QQFixPlanner:
    def __init__(self, drift_file="qq_drift_map.json"):
        self.drift_file = drift_file
        self.output_plan = "qq_fix_plan.json"

    def load_drift(self):
        with open(self.drift_file, 'r') as f:
            return json.load(f)

    def build_fix_plan(self):
        data = self.load_drift()
        results = data.get("results", [])
        plan = []
        for item in results:
            plan.append({
                "file": item["file"],
                "fix_required": True,
                "reason": f"Legacy signal(s) found: {', '.join(item['hits'])}",
                "hash_at_scan": item["hash"],
                "recommended_action": "Reintegrate into active logic map or modularize as standalone agent",
                "timestamp": datetime.utcnow().isoformat()
            })
        with open(self.output_plan, 'w') as f:
            json.dump(plan, f, indent=2)
        print(f"✅ Fix plan saved to {self.output_plan}")

if __name__ == "__main__":
    planner = QQFixPlanner()
    planner.build_fix_plan()