"""
Data Seeder Script

This script populates the attendance database with sample data for testing.
"""
import os
import sqlite3
from datetime import datetime, timedelta

# Path to the attendance database
ATTENDANCE_DB_PATH = 'data/attendance.db'

def create_sample_attendance_data():
    """Create sample attendance data for testing the dashboard"""
    print("Creating sample attendance data...")
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(ATTENDANCE_DB_PATH), exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(ATTENDANCE_DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        driver_name TEXT NOT NULL,
        asset_id TEXT,
        scheduled_start TEXT,
        actual_start TEXT,
        scheduled_end TEXT,
        actual_end TEXT,
        location TEXT,
        job_site TEXT,
        is_late INTEGER DEFAULT 0,
        is_early_end INTEGER DEFAULT 0,
        late_minutes INTEGER DEFAULT 0,
        early_minutes INTEGER DEFAULT 0,
        company TEXT,
        status TEXT,
        region TEXT
    )
    ''')
    
    # Create index on date and driver_name
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_driver ON attendance_records(date, driver_name)')
    
    # Create audit log table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        file_path TEXT,
        file_type TEXT,
        driver_count INTEGER,
        timestamp TEXT,
        status TEXT
    )
    ''')

    # Sample drivers and assets
    drivers = [
        {"name": "DAVID MARTINEZ", "asset_id": "ET-42", "job_site": "2023-034 KELLER HS ADDITION", "region": "West"},
        {"name": "JOHN WILLIAMS", "asset_id": "ET-15", "job_site": "2024-025 TIMBER CREEK HS ADDITION", "region": "North"},
        {"name": "MICHAEL JOHNSON", "asset_id": "ET-33", "job_site": "2023-032 SOUTH HILLS HS ADDITION", "region": "South"},
        {"name": "ROBERT SMITH", "asset_id": "ET-21", "job_site": "2024-019 EATON HS ADDITION", "region": "East"},
        {"name": "JAMES BROWN", "asset_id": "PT-07", "job_site": "2022-008 NORTHWEST HS ADDITION", "region": "North"}
    ]
    
    # Generate dates for the last 5 days
    today = datetime.now().date()
    dates = [(today - timedelta(days=x)).strftime("%Y-%m-%d") for x in range(5)]
    
    # Clear existing data
    cursor.execute('DELETE FROM attendance_records')
    cursor.execute('DELETE FROM attendance_audit')
    
    # Generate attendance records
    record_id = 1
    for date in dates:
        for driver in drivers:
            # Randomly make some drivers late or leave early
            is_late = 1 if driver["name"] in ["DAVID MARTINEZ", "JOHN WILLIAMS"] and date in [dates[0], dates[2]] else 0
            is_early = 1 if driver["name"] in ["MICHAEL JOHNSON", "JAMES BROWN"] and date in [dates[1], dates[3]] else 0
            
            # Calculate late/early minutes
            late_minutes = 15 if is_late else 0
            early_minutes = 20 if is_early else 0
            
            # Set scheduled and actual times
            scheduled_start = "07:00:00"
            actual_start = "07:15:00" if is_late else "07:00:00"
            scheduled_end = "17:00:00"
            actual_end = "16:40:00" if is_early else "17:00:00"
            
            # Insert record
            cursor.execute('''
            INSERT INTO attendance_records (
                date, driver_name, asset_id, scheduled_start, actual_start,
                scheduled_end, actual_end, location, job_site, is_late,
                is_early_end, late_minutes, early_minutes, company, status, region
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date, driver["name"], driver["asset_id"], scheduled_start, actual_start,
                scheduled_end, actual_end, "Dallas, TX", driver["job_site"], is_late,
                is_early, late_minutes, early_minutes, "RAGLE", "ACTIVE", driver["region"]
            ))
            
            record_id += 1
    
    # Add some audit log entries
    for date in dates:
        cursor.execute('''
        INSERT INTO attendance_audit (
            date, file_path, file_type, driver_count, timestamp, status
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            date, f"attached_assets/DailyUsage_{date}.csv", "daily_usage", 5,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "COMPLETE"
        ))
    
    # Save changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Successfully created sample data for {len(dates)} days with {len(drivers)} drivers each.")

if __name__ == "__main__":
    create_sample_attendance_data()