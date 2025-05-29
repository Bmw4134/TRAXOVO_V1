# kaizen_monitor.py
import os
import time
import subprocess
import datetime

WATCH_PATHS = ["data", "active"]
LOG_FILE = "meta/kaizen_monitor_log.txt"

def log(message):
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"🛡️ {message}")

def check_file_integrity():
    expected_files = [
        "dashboard_summary.json",
        "attendance_summary.json",
        "eq_idle_report.csv",
        "po_blocklist.json"
    ]
    issues = False
    for file in expected_files:
        if not os.path.exists(file) or os.path.getsize(file) == 0:
            log(f"⚠️ Missing or empty: {file}")
            issues = True
    return not issues

def rerun_parser():
    try:
        result = subprocess.run(["python3", "kaizen_live_parser.py"], capture_output=True, text=True)
        log("🔁 Parser output: " + result.stdout.splitlines()[-1])
    except Exception as e:
        log(f"❌ Parser error: {e}")

def main_loop():
    log("🚀 Kaizen Monitor started...")
    previous_snapshots = {path: os.listdir(path) if os.path.exists(path) else [] for path in WATCH_PATHS}
    while True:
        time.sleep(60)
        for path in WATCH_PATHS:
            if not os.path.exists(path):
                continue
            current_files = os.listdir(path)
            if current_files != previous_snapshots[path]:
                log(f"📂 Detected file change in {path}")
                rerun_parser()
                previous_snapshots[path] = current_files
        if not check_file_integrity():
            log("🚨 System state is not healthy. Review needed.")
        else:
            log("✅ System validated successfully.")

if __name__ == "__main__":
    main_loop()
