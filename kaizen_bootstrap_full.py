# kaizen_bootstrap_full.py
import os
import subprocess

def bootstrap():
    print("🔧 Running full Kaizen system boot...")
    subprocess.call(["python3", "kaizen_stack_integrator.py"])
    subprocess.call(["python3", "modules/data_sync/kaizen_data_sync.py"])
    subprocess.call(["python3", "modules/eq_management/eq_utilization_tracker.py"])
    print("✅ Core systems initialized. Ready for dashboard.")

if __name__ == "__main__":
    bootstrap()
