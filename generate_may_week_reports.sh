#!/bin/bash
# Run the weekly driver report generator for May 18-24, 2025

# Make script executable
chmod +x weekly_driver_report_generator.py

echo "Starting weekly driver report generation for May 18-24, 2025..."

python weekly_driver_report_generator.py \
  --start-date 2025-05-18 \
  --end-date 2025-05-24 \
  --driving-history-path "uploads/DrivingHistory (19).csv" \
  --activity-detail-path "uploads/ActivityDetail (13).csv" \
  --assets-on-site-path "uploads/AssetsTimeOnSite (8).csv" \
  --speeding-report-path "uploads/SpeedingReport (3).csv" \
  --timecard-path "uploads/Timecards - 2025-05-18 - 2025-05-24 (3).xlsx" \
  --output-dir "reports/driver_reports"

echo "Weekly report generation complete!"