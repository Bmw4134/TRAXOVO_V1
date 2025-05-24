# TRAXORA Core Code Samples

## Field Mapping Implementation

The following code shows how we handle field mapping for CSV files with inconsistent column names:

```python
# From utils/weekly_driver_processor.py
def _load_csv_file(self, file_path):
    """Load a CSV file into a list of dictionaries."""
    try:
        # Open the CSV file
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            # Try to auto-detect the delimiter
            dialect = csv.Sniffer().sniff(csvfile.read(4096))
            csvfile.seek(0)
            
            # Read the CSV file
            reader = csv.DictReader(csvfile, dialect=dialect)
            data = list(reader)
            
            # 🚨 STRICT COLUMN ENFORCEMENT WITH FIELD MAPPING
            if data and len(data) > 0:
                # Map alternative field names to our required ones
                column_mappings = {
                    "Contact": ["Driver", "Driver Name", "DriverName"],
                    "Locationx": ["Location", "JobSite", "Jobsite", "Job Site", "Job"],
                    "EventDateTime": ["DateTime", "Timestamp", "Time", "EventDateTimex"]
                }
                
                # Apply field mappings to standardize columns
                for row in data:
                    for target_col, source_cols in column_mappings.items():
                        # If target column is missing but an alternative exists, map it
                        if target_col not in row or not row[target_col]:
                            for source_col in source_cols:
                                if source_col in row and row[source_col]:
                                    row[target_col] = row[source_col]
                                    break
                
                # Verify required columns exist after mapping
                required_cols = ["Contact", "Locationx", "EventDateTime"]
                sample_row = data[0]  # Use first row after mapping
                
                # Check for missing columns
                missing = []
                for col in required_cols:
                    if col not in sample_row or not sample_row[col]:
                        missing.append(col)
                
                if missing:
                    available_cols = list(sample_row.keys())
                    logger.error(f"Missing required columns after mapping: {missing}")
                    logger.error(f"Available columns: {available_cols}")
                    raise ValueError(f"Missing required columns: {missing}")
                
                logger.info(f"📄 [VALID] Processing {len(data)} rows with required columns")
            
            return data
    except Exception as e:
        logger.error(f"Error loading CSV file {file_path}: {str(e)}")
        return []
```

## Driver Classification Logic

This code implements the attendance classification rules:

```python
def _classify_driver_attendance(self, driver_record):
    """
    Classify driver attendance based on time and location data.
    
    Args:
        driver_record (dict): Driver record with attendance data
        
    Returns:
        str: Attendance classification (on_time, late_start, early_end, not_on_job)
    """
    first_seen_time = driver_record.get('first_seen_time')
    last_seen_time = driver_record.get('last_seen_time')
    job_site = driver_record.get('job_site')
    hours_on_site = driver_record.get('hours_on_site', 0)
    
    # STRICT CLASSIFICATION - NO DEFAULTS
    # First evaluate if driver was on job site
    if not job_site or job_site == "Job Site Pending":
        logger.warning(f"Driver classified as NOT_ON_JOB due to missing job site")
        return 'not_on_job'
    
    # Then evaluate arrival time (late start check)
    if first_seen_time and first_seen_time > '07:30:00':
        minutes_late = (datetime.strptime(first_seen_time, '%H:%M:%S') - 
                       datetime.strptime('07:30:00', '%H:%M:%S')).total_seconds() / 60
        logger.info(f"Driver classified as LATE_START - {minutes_late:.1f} minutes late")
        return 'late_start'
    
    # Then evaluate departure time (early end check)
    if last_seen_time and last_seen_time < '16:00:00':
        minutes_early = (datetime.strptime('16:00:00', '%H:%M:%S') - 
                        datetime.strptime(last_seen_time, '%H:%M:%S')).total_seconds() / 60
        logger.info(f"Driver classified as EARLY_END - {minutes_early:.1f} minutes early")
        return 'early_end'
    
    # Check total hours (sanity check for early leave)
    if hours_on_site < 7:
        logger.info(f"Driver classified as EARLY_END - Only {hours_on_site:.1f} hours on site")
        return 'early_end'
    
    # Only if all other conditions are not met, classify as on time
    logger.info(f"Driver classified as ON_TIME ✓")
    return 'on_time'
```

## Report Processing Route

This route handles file uploads and processes the driver report:

```python
@enhanced_weekly_report_bp.route('/process', methods=['POST'])
def process_report():
    """Process uploaded files and generate report"""
    try:
        # Get form data
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        # If dates not provided, use defaults (May 18-24, 2025)
        if not start_date or not end_date:
            start_date = "2025-05-18"
            end_date = "2025-05-24"
        
        # Check for required files
        if 'driving_history' not in request.files or \
           'activity_detail' not in request.files or \
           'assets_time' not in request.files:
            flash('Missing required files', 'danger')
            return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
        
        # Get uploaded files
        driving_history_file = request.files['driving_history']
        activity_detail_file = request.files['activity_detail']
        assets_time_file = request.files['assets_time']
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded files
        driving_history_path = os.path.join(upload_dir, secure_filename(driving_history_file.filename))
        activity_detail_path = os.path.join(upload_dir, secure_filename(activity_detail_file.filename))
        assets_time_path = os.path.join(upload_dir, secure_filename(assets_time_file.filename))
        
        driving_history_file.save(driving_history_path)
        activity_detail_file.save(activity_detail_path)
        assets_time_file.save(assets_time_path)
        
        # Process the uploaded files
        report_data = process_weekly_report(
            start_date=start_date,
            end_date=end_date,
            driving_history_path=driving_history_path,
            activity_detail_path=activity_detail_path,
            time_on_site_path=assets_time_path
        )
        
        # Save report data to session for accessing in other routes
        session['weekly_report_data'] = report_data
        session['weekly_report_start_date'] = start_date
        session['weekly_report_end_date'] = end_date
        
        # Calculate date formatting
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        start_formatted = start_datetime.strftime('%B %d, %Y')
        end_formatted = end_datetime.strftime('%B %d, %Y')
        
        # Render report view
        return render_template('enhanced_weekly_report/view.html',
                              report=report_data,
                              start_date=start_date,
                              end_date=end_date,
                              start_formatted=start_formatted,
                              end_formatted=end_formatted,
                              date_range=report_data.get('date_range', []))
    except Exception as e:
        logger.error(f"Error processing report: {str(e)}")
        flash(f"An error occurred while processing your report: {str(e)}", 'danger')
        return redirect(url_for('enhanced_weekly_report_bp.dashboard'))
```

## Demo Data Processor

This shows how we process May 18-24 data from attached assets:

```python
def process_may_week_report():
    """
    Process May 18-24, 2025 driver report data using attached assets files.
    
    Returns:
        dict: Processed weekly report data
    """
    # Define date range
    start_date = "2025-05-18"
    end_date = "2025-05-24"
    
    # Set file paths
    attached_assets_dir = os.path.join(os.getcwd(), 'attached_assets')
    
    # Select appropriate files based on date (using most recent versions)
    driving_history_path = os.path.join(attached_assets_dir, 'DrivingHistory (19).csv')
    activity_detail_path = os.path.join(attached_assets_dir, 'ActivityDetail (13).csv')
    time_on_site_path = os.path.join(attached_assets_dir, 'AssetsTimeOnSite (8).csv')
    
    # Ensure files exist
    for file_path in [driving_history_path, activity_detail_path, time_on_site_path]:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
    
    # Process report using the weekly driver processor
    logger.info(f"Starting demo processing for May 18-24 weekly report")
    logger.info(f"Using files:")
    logger.info(f"  - Driving History: {os.path.basename(driving_history_path)}")
    logger.info(f"  - Activity Detail: {os.path.basename(activity_detail_path)}")
    logger.info(f"  - Time on Site: {os.path.basename(time_on_site_path)}")
    
    try:
        report_data = process_weekly_report(
            start_date=start_date,
            end_date=end_date,
            driving_history_path=driving_history_path,
            activity_detail_path=activity_detail_path,
            time_on_site_path=time_on_site_path,
            from_attached_assets=True
        )
        
        logger.info(f"Demo processing completed successfully")
        return report_data
    except Exception as e:
        logger.error(f"Error processing demo report: {str(e)}")
        return None
```