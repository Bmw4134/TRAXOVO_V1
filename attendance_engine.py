# attendance_engine.py (ULTRA BLOCK with Advanced Control)

import pandas as pd
import os
import json
import time
from datetime import datetime

DATA_DIR = "data"
QUEUE_FILE = os.path.join(DATA_DIR, "input_queue.json")

# 🔧 Setup Directories and Input Queue

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'w') as f:
            json.dump([], f)

# 🔁 Force Restart to Clear Memory Cache (Replit Stability Fix)

def force_restart():
    print(f"🔁 Force restart triggered @ {datetime.now().isoformat()}")
    time.sleep(1)
    os._exit(1)

# 🔍 Diagnostic Sync Check

def verify_file_sync(file_path):
    print(f"📁 Verifying file sync: {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ File missing: {file_path}")
    with open(file_path, 'r') as f:
        head = f.read(200)
    print(f"✅ Top of file:\n{head[:300]}")

# 📌 Queue an Input File

def queue_input(file_name, source="unknown"):
    ensure_dirs()
    with open(QUEUE_FILE, 'r') as f:
        queue = json.load(f)
    timestamp = datetime.now().isoformat()
    queue.append({"file": file_name, "source": source, "status": "pending", "timestamp": timestamp})
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)
    print(f"✅ Queued {file_name} from {source}")

# 📥 Load Telematics and Timecards

def load_telematics(file_path):
    df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
    df.columns = [c.strip() for c in df.columns]
    return df

def load_timecards(file_path):
    df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
    df.columns = [c.strip() for c in df.columns]
    return df

# 📊 Infer Attendance

def infer_attendance(telematics_df, timecards_df):
    attendance_records = []

    for _, row in telematics_df.iterrows():
        emp_id = row.get("EMP ID") or row.get("EmployeeNo")
        start = row.get("StartTime") or row.get("Began Day On Site")
        end = row.get("EndTime") or row.get("Ended Day On Site")
        job = row.get("JOB") or row.get("ProjectNo")

        try:
            start_time = pd.to_datetime(start)
            end_time = pd.to_datetime(end)
        except:
            continue

        duration = (end_time - start_time).seconds / 3600
        attendance_records.append({
            "Employee ID": emp_id,
            "Job": job,
            "Start Time": start_time,
            "End Time": end_time,
            "Hours Worked": round(duration, 2)
        })

    attendance_df = pd.DataFrame(attendance_records)

    if not timecards_df.empty:
        attendance_df = attendance_df.merge(timecards_df, how="left", on="Employee ID")

    return attendance_df

# 💾 Export Final Report

def generate_report(attendance_df, output_file="attendance_report.xlsx"):
    attendance_df.to_excel(output_file, index=False)
    print(f"📊 Report saved to {output_file}")

# -------------------------
# 🟢 MASTER EXECUTION BLOCK
# -------------------------

if __name__ == "__main__":
    ensure_dirs()
    queue_input("telematics.csv", source="mobile")
    verify_file_sync("attendance_engine.py")
    telematics = load_telematics("data/telematics.csv")
    timecards = load_timecards("data/timecards.xlsx")
    attendance = infer_attendance(telematics, timecards)
    generate_report(attendance)
    force_restart()