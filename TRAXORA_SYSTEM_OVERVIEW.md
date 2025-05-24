# TRAXORA Fleet Management System - Architecture Overview

## Core System Components

### 1. Data Processing Pipeline
- **Weekly Driver Processor (`utils/weekly_driver_processor.py`)**: Combines data from multiple sources to generate comprehensive driver attendance reports:
  - DrivingHistory CSV - Contains GPS and driver location data
  - ActivityDetail CSV - Contains driver activity logs
  - AssetsTimeOnSite CSV - Contains asset location and time data
  - Classification Logic: Categorizes drivers as "On Time", "Late Start", "Early End", or "Not On Job"

### 2. Web Interface
- **Enhanced Weekly Report (`routes/enhanced_weekly_report.py`)**: Main interface for processing and viewing weekly reports
- **Dashboard (`templates/enhanced_weekly_report/dashboard.html`)**: Upload interface and reporting overview
- **Views (`templates/enhanced_weekly_report/view.html`)**: Detailed report visualizations

### 3. Database Models
- **Driver Model**: Tracks driver information, job site assignments, and report history
- **Asset Model**: Manages equipment location, status, and assignments
- **JobSite Model**: Defines job locations with geofence boundaries

## Data Flow
1. User uploads CSV files (DrivingHistory, ActivityDetail, AssetsTimeOnSite)
2. System maps fields to standardized column names (Contact, Locationx, EventDateTime)
3. Processor combines data to create daily driver records with attendance classification
4. Classification logic applies rules:
   - No job site = "Not On Job"
   - First seen after 7:30 AM = "Late Start"
   - Last seen before 4:00 PM = "Early End"
   - Less than 7 hours on site = "Early End"
   - Otherwise = "On Time"
5. System generates weekly summary with statistics and metrics

## Technical Implementation
- **Backend**: Python/Flask with SQLAlchemy ORM
- **Frontend**: Bootstrap-based responsive design
- **External API**: Gauge API integration for real-time asset tracking
- **Authentication**: User login via Flask-Login
- **Data Processing**: Python with pandas for CSV processing

## Current Enhancement Areas
1. **Field Mapping**: Need to handle variations in CSV column names consistently
2. **Classification Logic**: Ensure accurate categorization of driver attendance
3. **UI Consistency**: Standardize template inheritance and navigation
4. **Performance**: Optimize for large datasets (5000+ rows)
5. **Reporting**: Add trend analysis and exportable reports

## Example Processing Code
```python
def _classify_driver_attendance(self, driver_record):
    """Classify driver attendance based on time and location data."""
    first_seen_time = driver_record.get('first_seen_time')
    last_seen_time = driver_record.get('last_seen_time')
    job_site = driver_record.get('job_site')
    hours_on_site = driver_record.get('hours_on_site', 0)
    
    # First evaluate if driver was on job site
    if not job_site or job_site == "Job Site Pending":
        return 'not_on_job'
    
    # Then evaluate arrival time (late start check)
    if first_seen_time and first_seen_time > '07:30:00':
        return 'late_start'
    
    # Then evaluate departure time (early end check)
    if last_seen_time and last_seen_time < '16:00:00':
        return 'early_end'
    
    # Check total hours (sanity check for early leave)
    if hours_on_site < 7:
        return 'early_end'
    
    # Only if all other conditions are not met, classify as on time
    return 'on_time'
```

## Database Schema Highlights
```python
class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(128), nullable=False)
    employee_id = db.Column(db.String(32))
    job_site_id = db.Column(db.Integer, db.ForeignKey('job_sites.id'))
    is_active = db.Column(db.Boolean, default=True)
    
class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(128))
    last_latitude = db.Column(db.Float)
    last_longitude = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)
    
class DriverReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'))
    job_site_id = db.Column(db.Integer, db.ForeignKey('job_sites.id'))
    report_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32))  # on_time, late_start, early_end, not_on_job
```

## Integration Points
- **GaugeSmart API**: Vehicle telematics integration
- **CSV Data Sources**: Field mapping for flexible data ingestion
- **Export Formats**: CSV, JSON, PDF report generation

## Key Implementation Files
- `utils/weekly_driver_processor.py`: Core data processing
- `routes/enhanced_weekly_report.py`: Main interface routes
- `templates/enhanced_weekly_report/*.html`: User interface
- `models.py`: Database schema
- `main.py`: Application entry point

## Questions for ChatGPT
1. How can we improve the field mapping system to handle inconsistent CSV column names more robustly?
2. What optimizations would you suggest for processing large datasets (5000+ rows)?
3. What additional visualizations would make the attendance data more actionable?
4. How can we enhance the classification logic to account for special cases (half days, split shifts)?
5. What security best practices should we implement to protect sensitive driver data?