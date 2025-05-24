#!/bin/bash

# Generate May Week Reports Shell Script
# This script processes the May 18-24, 2025 data using our Daily Driver Engine 2.0

echo "Starting May 18-24 Week Report Generation..."

# Create necessary directories
mkdir -p data
mkdir -p reports/daily_driver_reports
mkdir -p uploads/daily_reports

# Define file paths
DRIVING_HISTORY="attached_assets/weekly_driver_report_2025-05-18_to_2025-05-24.csv"
TIMECARD="attached_assets/Timecards - 2025-05-18 - 2025-05-24 (3).xlsx"

# Process May 18 - Sunday
echo "Processing May 18, 2025 (Sunday)..."
python -c "
import sys
sys.path.append('.')
from utils.attendance_pipeline_v2 import process_attendance_data_v2
from utils.enhanced_data_ingestion import load_csv_file, load_excel_file
from utils.daily_driver_report_generator import generate_daily_report

# Load data
driving_data = load_csv_file('$DRIVING_HISTORY')
timecard_data = load_excel_file('$TIMECARD')

# Create standardized data format
driving_records = []
for record in driving_data:
    if 'Driver Name' in record and 'Date' in record and record['Date'] == '2025-05-18':
        driving_records.append({
            'Driver': record['Driver Name'],
            'Date': record['Date'],
            'EventDateTime': record.get('First Seen', '2025-05-18 07:00:00'),
            'Location': record.get('Job Site', 'Unknown'),
            'Status': record.get('Status', '')
        })

# Process attendance data
attendance_report = process_attendance_data_v2(
    driving_history_data=driving_records,
    timecard_data=timecard_data,
    date_str='2025-05-18'
)

# Generate report
generate_daily_report(
    date_str='2025-05-18',
    driving_history_data=driving_records,
    timecard_data=timecard_data
)
"

# Process May 19 - Monday
echo "Processing May 19, 2025 (Monday)..."
python -c "
import sys
sys.path.append('.')
from utils.attendance_pipeline_v2 import process_attendance_data_v2
from utils.enhanced_data_ingestion import load_csv_file, load_excel_file
from utils.daily_driver_report_generator import generate_daily_report

# Load data
driving_data = load_csv_file('$DRIVING_HISTORY')
timecard_data = load_excel_file('$TIMECARD')

# Create standardized data format
driving_records = []
for record in driving_data:
    if 'Driver Name' in record and 'Date' in record and record['Date'] == '2025-05-19':
        driving_records.append({
            'Driver': record['Driver Name'],
            'Date': record['Date'],
            'EventDateTime': record.get('First Seen', '2025-05-19 07:00:00'),
            'Location': record.get('Job Site', 'Unknown'),
            'Status': record.get('Status', '')
        })

# Process attendance data
attendance_report = process_attendance_data_v2(
    driving_history_data=driving_records,
    timecard_data=timecard_data,
    date_str='2025-05-19'
)

# Generate report
generate_daily_report(
    date_str='2025-05-19',
    driving_history_data=driving_records,
    timecard_data=timecard_data
)
"

# Process May 20 - Tuesday
echo "Processing May 20, 2025 (Tuesday)..."
python -c "
import sys
sys.path.append('.')
from utils.attendance_pipeline_v2 import process_attendance_data_v2
from utils.enhanced_data_ingestion import load_csv_file, load_excel_file
from utils.daily_driver_report_generator import generate_daily_report

# Load data
driving_data = load_csv_file('$DRIVING_HISTORY')
timecard_data = load_excel_file('$TIMECARD')

# Create standardized data format
driving_records = []
for record in driving_data:
    if 'Driver Name' in record and 'Date' in record and record['Date'] == '2025-05-20':
        driving_records.append({
            'Driver': record['Driver Name'],
            'Date': record['Date'],
            'EventDateTime': record.get('First Seen', '2025-05-20 07:00:00'),
            'Location': record.get('Job Site', 'Unknown'),
            'Status': record.get('Status', '')
        })

# Process attendance data
attendance_report = process_attendance_data_v2(
    driving_history_data=driving_records,
    timecard_data=timecard_data,
    date_str='2025-05-20'
)

# Generate report
generate_daily_report(
    date_str='2025-05-20',
    driving_history_data=driving_records,
    timecard_data=timecard_data
)
"

# Process May 21 - Wednesday
echo "Processing May 21, 2025 (Wednesday)..."
python -c "
import sys
sys.path.append('.')
from utils.attendance_pipeline_v2 import process_attendance_data_v2
from utils.enhanced_data_ingestion import load_csv_file, load_excel_file
from utils.daily_driver_report_generator import generate_daily_report

# Load data
driving_data = load_csv_file('$DRIVING_HISTORY')
timecard_data = load_excel_file('$TIMECARD')

# Create standardized data format
driving_records = []
for record in driving_data:
    if 'Driver Name' in record and 'Date' in record and record['Date'] == '2025-05-21':
        driving_records.append({
            'Driver': record['Driver Name'],
            'Date': record['Date'],
            'EventDateTime': record.get('First Seen', '2025-05-21 07:00:00'),
            'Location': record.get('Job Site', 'Unknown'),
            'Status': record.get('Status', '')
        })

# Process attendance data
attendance_report = process_attendance_data_v2(
    driving_history_data=driving_records,
    timecard_data=timecard_data,
    date_str='2025-05-21'
)

# Generate report
generate_daily_report(
    date_str='2025-05-21',
    driving_history_data=driving_records,
    timecard_data=timecard_data
)
"

# Process May 22 - Thursday
echo "Processing May 22, 2025 (Thursday)..."
python -c "
import sys
sys.path.append('.')
from utils.attendance_pipeline_v2 import process_attendance_data_v2
from utils.enhanced_data_ingestion import load_csv_file, load_excel_file
from utils.daily_driver_report_generator import generate_daily_report

# Load data
driving_data = load_csv_file('$DRIVING_HISTORY')
timecard_data = load_excel_file('$TIMECARD')

# Create standardized data format
driving_records = []
for record in driving_data:
    if 'Driver Name' in record and 'Date' in record and record['Date'] == '2025-05-22':
        driving_records.append({
            'Driver': record['Driver Name'],
            'Date': record['Date'],
            'EventDateTime': record.get('First Seen', '2025-05-22 07:00:00'),
            'Location': record.get('Job Site', 'Unknown'),
            'Status': record.get('Status', '')
        })

# Process attendance data
attendance_report = process_attendance_data_v2(
    driving_history_data=driving_records,
    timecard_data=timecard_data,
    date_str='2025-05-22'
)

# Generate report
generate_daily_report(
    date_str='2025-05-22',
    driving_history_data=driving_records,
    timecard_data=timecard_data
)
"

# Process May 23 - Friday
echo "Processing May 23, 2025 (Friday)..."
python -c "
import sys
sys.path.append('.')
from utils.attendance_pipeline_v2 import process_attendance_data_v2
from utils.enhanced_data_ingestion import load_csv_file, load_excel_file
from utils.daily_driver_report_generator import generate_daily_report

# Load data
driving_data = load_csv_file('$DRIVING_HISTORY')
timecard_data = load_excel_file('$TIMECARD')

# Create standardized data format
driving_records = []
for record in driving_data:
    if 'Driver Name' in record and 'Date' in record and record['Date'] == '2025-05-23':
        driving_records.append({
            'Driver': record['Driver Name'],
            'Date': record['Date'],
            'EventDateTime': record.get('First Seen', '2025-05-23 07:00:00'),
            'Location': record.get('Job Site', 'Unknown'),
            'Status': record.get('Status', '')
        })

# Process attendance data
attendance_report = process_attendance_data_v2(
    driving_history_data=driving_records,
    timecard_data=timecard_data,
    date_str='2025-05-23'
)

# Generate report
generate_daily_report(
    date_str='2025-05-23',
    driving_history_data=driving_records,
    timecard_data=timecard_data
)
"

# Process May 24 - Saturday
echo "Processing May 24, 2025 (Saturday)..."
python -c "
import sys
sys.path.append('.')
from utils.attendance_pipeline_v2 import process_attendance_data_v2
from utils.enhanced_data_ingestion import load_csv_file, load_excel_file
from utils.daily_driver_report_generator import generate_daily_report

# Load data
driving_data = load_csv_file('$DRIVING_HISTORY')
timecard_data = load_excel_file('$TIMECARD')

# Create standardized data format
driving_records = []
for record in driving_data:
    if 'Driver Name' in record and 'Date' in record and record['Date'] == '2025-05-24':
        driving_records.append({
            'Driver': record['Driver Name'],
            'Date': record['Date'],
            'EventDateTime': record.get('First Seen', '2025-05-24 07:00:00'),
            'Location': record.get('Job Site', 'Unknown'),
            'Status': record.get('Status', '')
        })

# Process attendance data
attendance_report = process_attendance_data_v2(
    driving_history_data=driving_records,
    timecard_data=timecard_data,
    date_str='2025-05-24'
)

# Generate report
generate_daily_report(
    date_str='2025-05-24',
    driving_history_data=driving_records,
    timecard_data=timecard_data
)
"

echo "May 18-24 week reports generation complete!"
echo "Reports saved to reports/daily_driver_reports/"
ls -la reports/daily_driver_reports/