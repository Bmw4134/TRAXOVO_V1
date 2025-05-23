# TRAXORA Driver Report Generation Guide

This guide will help you process your downloaded files to generate comprehensive driver reports for the week of May 18-24, 2025.

## Quick Start Steps

1. **Upload your downloaded files**
   - Copy all CSV and Excel files to the `uploads` directory
   - This includes DrivingHistory, ActivityDetail, AssetsTimeOnSite, SpeedingReport, and Timecard files

2. **Run the weekly report generator**
   - Execute `./generate_may_week_reports.sh` to process all days at once
   - Or use the web interface to process one day at a time

3. **View generated reports**
   - Navigate to the Driver Reports dashboard to see all generated reports
   - Compare timecard data with GPS records for discrepancies

## Detailed Instructions

### Step 1: Copy Your Files to the Uploads Directory

The simplest way to transfer your files is to use the upload utility:

```bash
# Create uploads directory if it doesn't exist
mkdir -p uploads

# Copy files manually to uploads directory
# Example:
cp ~/Downloads/DrivingHistory*.csv uploads/
cp ~/Downloads/ActivityDetail*.csv uploads/
cp ~/Downloads/AssetsTimeOnSite*.csv uploads/
cp ~/Downloads/SpeedingReport*.csv uploads/
cp ~/Downloads/Timecards*.xlsx uploads/
```

### Step 2: Generate Reports

#### Option A: Generate Reports for the Entire Week at Once

```bash
# Make the script executable
chmod +x generate_may_week_reports.sh

# Run the script
./generate_may_week_reports.sh
```

This will:
- Process all days from May 18 to May 24
- Generate daily classification reports
- Compare timecard data with GPS records

#### Option B: Use the Web Interface

1. Go to the Driver Reports dashboard
2. Click "New Report" button
3. Fill in the form with:
   - Date: Choose a specific date (e.g., 2025-05-18)
   - Driving History Files: Select your DrivingHistory CSVs
   - Activity Detail Files: Select your ActivityDetail CSVs
   - Assets On Site Files: Select your AssetsTimeOnSite CSVs (optional)
   - Equipment Billing: Select your timecard or quantities file (optional)
4. Click "Generate Driver Report"
5. Repeat for each day of the week

### Step 3: Process Timecard Data

After generating reports, you can process the Ground Works timecard data for comparison:

1. Go to the Driver Reports dashboard
2. In the "Timecard Verification" section, upload your timecard file
3. Set date range: 2025-05-18 to 2025-05-24
4. Click "Upload & Compare"

This will highlight any discrepancies between:
- GPS-verified time-in/time-out
- Reported timecard hours in Ground Works

## Understanding the Reports

Each daily report provides:

1. **Driver Classifications**
   - On Time: Drivers who arrived at their assigned job site on time
   - Late: Drivers who arrived late, with average minutes late
   - Early End: Drivers who left before the end of their shift
   - Not On Job: Drivers who were not at their assigned job site

2. **Timecard Comparison**
   - Verifies reported hours against GPS data
   - Flags discrepancies for review before payroll processing

3. **Export Options**
   - PDF Summary: Overall statistics and classifications
   - Excel: Detailed driver-by-driver breakdown
   - JSON: Raw data for further processing
   - PM Reports: Specialized reports for Project Managers

## Troubleshooting

If you encounter issues:

1. **Missing Data**: Ensure all CSV files have data for the selected date range
2. **Format Issues**: Verify CSV files are in the expected GAUGE API format
3. **Process Errors**: Check the application logs for details

For any persistent issues, please contact the TRAXORA support team.