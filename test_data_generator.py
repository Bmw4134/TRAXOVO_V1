"""
Test Data Generator for Attendance Reports

This script generates mock DailyUsage.csv-style data for testing the attendance reporting system.
It creates realistic test data with various edge cases and attendance scenarios.
"""

import os
import csv
import argparse
import random
from datetime import datetime, timedelta

# Configuration
ASSET_PREFIXES = ["ET-", "PT-", "LT-", "CT-", "RT-", "HT-"]
VEHICLE_TYPES = ["RAM-2500", "F-150", "CHEVY SILVERADO", "FORD F250", "GMC SIERRA"]
FIRST_NAMES = [
    "James", "Robert", "John", "Michael", "David", "William", "Richard", "Joseph", "Thomas", "Charles",
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
    "José", "Luis", "Carlos", "Juan", "Miguel", "Jorge", "Pedro", "Roberto", "Antonio", "Francisco",
    "María", "Ana", "Sofía", "Carmen", "Isabel", "Rosa", "Laura", "Gabriela", "Juana", "Teresa"
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Perez", "Sanchez", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright",
    "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall"
]
COMPANIES = ["Ragle Inc.", "Select Contracting", "Texas Earth Movers", "Highland Construction"]
JOB_SITES = [
    "Dallas North", "Fort Worth West", "Arlington Central", "Plano East", "Irving South",
    "Grapevine Mall", "Richardson Office Park", "Frisco Town Center", "Denton Highway", "Southlake Plaza",
    "McKinney Residential", "Allen Sports Complex", "Carrollton Bridge", "Lewisville Dam", "Coppell Industrial"
]

# Default date format for file naming and CSV data
DATE_FORMAT = "%Y-%m-%d"

# Default expected start/end times
EXPECTED_START = "07:00 AM"
EXPECTED_END = "03:30 PM"

def generate_driver():
    """Generate a random driver name"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Occasionally add middle initial
    if random.random() < 0.3:
        middle_initial = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + "."
        full_name = f"{first_name} {middle_initial} {last_name}"
    else:
        full_name = f"{first_name} {last_name}"
    
    # Occasionally add employee ID
    if random.random() < 0.4:
        employee_id = f"EMP{random.randint(1000, 9999)}"
        
        # Format can vary
        id_format = random.randint(1, 3)
        if id_format == 1:
            full_name = f"{full_name} ({employee_id})"
        elif id_format == 2:
            full_name = f"{full_name} - {employee_id}"
        else:
            full_name = f"{full_name} {employee_id}"
    
    return full_name

def generate_asset_label():
    """Generate a random asset label"""
    asset_type = random.random()
    
    # Equipment with standard prefix (70% of cases)
    if asset_type < 0.7:
        prefix = random.choice(ASSET_PREFIXES)
        number = random.randint(1, 99)
        return f"{prefix}{number:02d}"
    
    # Regular vehicle (30% of cases)
    else:
        return random.choice(VEHICLE_TYPES)

def generate_time(base_time, variance_minutes=0, skip_probability=0):
    """
    Generate a time string with potential variance
    
    Args:
        base_time (str): Base time in format "HH:MM AM/PM"
        variance_minutes (int): Maximum minutes to vary from base time (can be negative)
        skip_probability (float): Probability to return empty string (0-1)
        
    Returns:
        str: Time string or empty string if skipped
    """
    # Check if we should skip this time (for missing records)
    if random.random() < skip_probability:
        return ""
    
    # Parse base time
    try:
        base_dt = datetime.strptime(base_time, "%I:%M %p")
    except ValueError:
        base_dt = datetime.strptime(base_time, "%H:%M")
    
    # Apply variance
    if variance_minutes != 0:
        # If variance_minutes is positive, it can be early or late
        # If negative, it's specifically that direction
        if variance_minutes > 0:
            actual_variance = random.randint(-variance_minutes, variance_minutes)
        else:
            actual_variance = variance_minutes
            
        base_dt += timedelta(minutes=actual_variance)
    
    # Format the time (50/50 between 12-hour and 24-hour formats)
    if random.random() < 0.5:
        return base_dt.strftime("%I:%M %p")
    else:
        return base_dt.strftime("%H:%M")

def generate_test_data(date=None, count=100, random_date=False):
    """
    Generate test attendance data
    
    Args:
        date (str): Date to use for all records (YYYY-MM-DD format)
        count (int): Number of records to generate
        random_date (bool): Whether to use a random date instead of the provided one
        
    Returns:
        list: List of dictionaries with test data
    """
    if random_date or not date:
        # Generate a random date in the last 30 days
        days_ago = random.randint(0, 30)
        record_date = (datetime.now() - timedelta(days=days_ago)).strftime(DATE_FORMAT)
    else:
        record_date = date
    
    test_data = []
    
    # Generate data for different scenarios
    
    # 1. Normal on-time drivers (40% of total)
    normal_count = int(count * 0.4)
    for _ in range(normal_count):
        # Small variance but within acceptable range
        start_time = generate_time(EXPECTED_START, variance_minutes=10)
        end_time = generate_time(EXPECTED_END, variance_minutes=10)
        
        asset_label = generate_asset_label()
        driver = generate_driver()
        
        test_data.append({
            "Date": record_date,
            "Asset": f"{asset_label} {driver}",
            "Time Start": start_time,
            "Time Stop": end_time,
            "Company": random.choice(COMPANIES),
            "Job Site": random.choice(JOB_SITES)
        })
    
    # 2. Late start drivers (20% of total)
    late_count = int(count * 0.2)
    for _ in range(late_count):
        # Late by 16-60 minutes (beyond grace period)
        start_time = generate_time(EXPECTED_START, variance_minutes=random.randint(16, 60))
        end_time = generate_time(EXPECTED_END, variance_minutes=10)
        
        asset_label = generate_asset_label()
        driver = generate_driver()
        
        test_data.append({
            "Date": record_date,
            "Asset": f"{asset_label} {driver}",
            "Time Start": start_time,
            "Time Stop": end_time,
            "Company": random.choice(COMPANIES),
            "Job Site": random.choice(JOB_SITES)
        })
    
    # 3. Early end drivers (15% of total)
    early_count = int(count * 0.15)
    for _ in range(early_count):
        # Early by 16-90 minutes (beyond grace period)
        start_time = generate_time(EXPECTED_START, variance_minutes=10)
        end_time = generate_time(EXPECTED_END, variance_minutes=random.randint(-90, -16))
        
        asset_label = generate_asset_label()
        driver = generate_driver()
        
        test_data.append({
            "Date": record_date,
            "Asset": f"{asset_label} {driver}",
            "Time Start": start_time,
            "Time Stop": end_time,
            "Company": random.choice(COMPANIES),
            "Job Site": random.choice(JOB_SITES)
        })
    
    # 4. Missing start or end time (not on job - 10% of total)
    not_on_job_count = int(count * 0.1)
    for _ in range(not_on_job_count):
        # 50/50 chance of missing start vs. missing end
        if random.random() < 0.5:
            start_time = ""
            end_time = generate_time(EXPECTED_END, variance_minutes=10)
        else:
            start_time = generate_time(EXPECTED_START, variance_minutes=10)
            end_time = ""
        
        asset_label = generate_asset_label()
        driver = generate_driver()
        
        test_data.append({
            "Date": record_date,
            "Asset": f"{asset_label} {driver}",
            "Time Start": start_time,
            "Time Stop": end_time,
            "Company": random.choice(COMPANIES),
            "Job Site": random.choice(JOB_SITES)
        })
    
    # 5. Double issue - both late and early (5% of total)
    double_issue_count = int(count * 0.05)
    for _ in range(double_issue_count):
        start_time = generate_time(EXPECTED_START, variance_minutes=random.randint(16, 60))
        end_time = generate_time(EXPECTED_END, variance_minutes=random.randint(-90, -16))
        
        asset_label = generate_asset_label()
        driver = generate_driver()
        
        test_data.append({
            "Date": record_date,
            "Asset": f"{asset_label} {driver}",
            "Time Start": start_time,
            "Time Stop": end_time,
            "Company": random.choice(COMPANIES),
            "Job Site": random.choice(JOB_SITES)
        })
    
    # 6. No times at all (5% of total)
    no_times_count = int(count * 0.05)
    for _ in range(no_times_count):
        asset_label = generate_asset_label()
        driver = generate_driver()
        
        test_data.append({
            "Date": record_date,
            "Asset": f"{asset_label} {driver}",
            "Time Start": "",
            "Time Stop": "",
            "Company": random.choice(COMPANIES),
            "Job Site": random.choice(JOB_SITES)
        })
    
    # 7. Edge cases (5% of total)
    edge_case_count = count - len(test_data)  # Whatever is left to reach the desired count
    for _ in range(edge_case_count):
        edge_type = random.randint(1, 5)
        
        # Generate base data
        asset_label = generate_asset_label()
        driver = generate_driver()
        
        if edge_type == 1:
            # Very late start
            start_time = generate_time(EXPECTED_START, variance_minutes=random.randint(120, 300))
            end_time = generate_time(EXPECTED_END, variance_minutes=10)
        elif edge_type == 2:
            # Very early end
            start_time = generate_time(EXPECTED_START, variance_minutes=10)
            end_time = generate_time("12:00 PM", variance_minutes=random.randint(-60, 0))
        elif edge_type == 3:
            # Malformed asset label (no space between asset and driver)
            asset_label = f"{asset_label}{driver}"
            start_time = generate_time(EXPECTED_START, variance_minutes=10)
            end_time = generate_time(EXPECTED_END, variance_minutes=10)
        elif edge_type == 4:
            # Multiple driver names
            driver = f"{driver} / {generate_driver()}"
            start_time = generate_time(EXPECTED_START, variance_minutes=10)
            end_time = generate_time(EXPECTED_END, variance_minutes=10)
        else:
            # Timezone included in time
            start_time = f"{generate_time(EXPECTED_START, variance_minutes=10)} CT"
            end_time = f"{generate_time(EXPECTED_END, variance_minutes=10)} CT"
        
        test_data.append({
            "Date": record_date,
            "Asset": f"{asset_label} {driver}" if edge_type != 3 else asset_label,
            "Time Start": start_time,
            "Time Stop": end_time,
            "Company": random.choice(COMPANIES),
            "Job Site": random.choice(JOB_SITES)
        })
    
    # Shuffle the data to mix up the order
    random.shuffle(test_data)
    
    return test_data

def write_csv(data, output_file):
    """
    Write data to a CSV file in the DailyUsage.csv format
    
    Args:
        data (list): List of dictionaries with data
        output_file (str): Path to output file
    """
    if not data:
        print("No data to write.")
        return False
    
    try:
        # Ensure the directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Get field names from the first record
        fieldnames = list(data[0].keys())
        
        # Add header rows similar to real DailyUsage.csv files
        with open(output_file, 'w', newline='') as csvfile:
            # Write header rows (mock the format of real files)
            csvfile.write("Gauge Fleet Solutions\n")
            csvfile.write("Daily Usage Report\n")
            csvfile.write("\n")
            csvfile.write(f"Generated on: {datetime.now().strftime('%m/%d/%Y %I:%M %p')}\n")
            csvfile.write(f"Report date: {data[0]['Date']}\n")
            csvfile.write("\n")
            csvfile.write("Daily Usage Data:\n")
            
            # Write the actual data
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
        print(f"Successfully wrote {len(data)} records to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error writing to CSV: {e}")
        return False

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='Generate test data for attendance reporting system.')
    parser.add_argument('-d', '--date', help='Date to use for all records (YYYY-MM-DD format)')
    parser.add_argument('-c', '--count', type=int, default=100, help='Number of records to generate (default: 100)')
    parser.add_argument('-o', '--output', default='mock_DailyUsage.csv', help='Output file path (default: mock_DailyUsage.csv)')
    parser.add_argument('-r', '--random', action='store_true', help='Use a random date instead of today')
    
    args = parser.parse_args()
    
    # Generate test data
    test_data = generate_test_data(args.date, args.count, args.random)
    
    # Write to CSV
    success = write_csv(test_data, args.output)
    
    if success:
        # Show next steps
        print("\nTest data generated successfully!")
        print("\nNext steps:")
        print(f"1. Use this file with the attendance processor: python -c \"import sys; sys.path.append('.'); from utils.attendance_processor import read_daily_usage_file; print(read_daily_usage_file('{args.output}'))\"")
        print(f"2. Validate the generated report: python report_validator.py -d {args.date or datetime.now().strftime(DATE_FORMAT)}")
        print("\nThis will verify that the attendance data is processed correctly and validate the integrity of the resulting report.")

if __name__ == "__main__":
    main()