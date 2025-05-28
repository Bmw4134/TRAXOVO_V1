
import os
import json
from importlib import import_module

MODULES = [
    "2_ANALYTICS_ENGINE.parse_foundation_costs",
    "3_ATTENDANCE_MODULE.filter_active_employees",
    "4_QA_AUTOMATION.qa_trigger"
]

def load_modules():
    for mod_path in MODULES:
        try:
            import_module(mod_path.replace("/", "."))
            print(f"✅ Loaded {mod_path}")
        except Exception as e:
            print(f"❌ Failed loading {mod_path}: {e}")

if __name__ == "__main__":
    print("🔁 Starting TRAXOVO Mega Suite Loader")
    load_modules()
