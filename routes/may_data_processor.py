"""
May Data Processor for Friday 5/23 to Tuesday 5/27

Handles uploading and processing your specific date range data
to complete May monthly reporting with authentic driver data.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import json
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

may_processor_bp = Blueprint('may_processor', __name__)
logger = logging.getLogger(__name__)

@may_processor_bp.route('/upload-may-week-data')
def upload_may_week_data():
    """Upload page specifically for May 23-27 data"""
    target_dates = [
        '2025-05-23',  # Friday
        '2025-05-24',  # Saturday  
        '2025-05-25',  # Sunday
        '2025-05-26',  # Monday
        '2025-05-27'   # Tuesday
    ]
    
    return render_template('may_week_uploader.html',
                         target_dates=target_dates,
                         current_date=datetime.now().strftime('%Y-%m-%d'))

@may_processor_bp.route('/process-may-files', methods=['POST'])
def process_may_files():
    """Process uploaded files for May 23-27 date range"""
    try:
        uploaded_files = request.files.getlist('files')
        target_date_range = request.form.get('date_range', 'may-23-27')
        
        if not uploaded_files:
            return jsonify({
                'success': False,
                'message': 'No files uploaded'
            }), 400
        
        # Process each uploaded file
        processed_files = []
        for file in uploaded_files:
            if file.filename:
                # Save file to uploads directory
                upload_dir = Path('./uploads')
                upload_dir.mkdir(exist_ok=True)
                
                file_path = upload_dir / file.filename
                file.save(file_path)
                
                # Process the file based on type
                result = process_file_for_may(file_path, target_date_range)
                processed_files.append({
                    'filename': file.filename,
                    'result': result,
                    'processed': result['success'] if result else False
                })
        
        # Generate comprehensive May reports
        may_reports = generate_may_reports(processed_files)
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(processed_files)} files for May 23-27',
            'processed_files': processed_files,
            'may_reports': may_reports
        })
        
    except Exception as e:
        logger.error(f"Error processing May files: {e}")
        return jsonify({
            'success': False,
            'message': f'Processing error: {str(e)}'
        }), 500

def process_file_for_may(file_path, date_range):
    """Process individual file for May date range"""
    try:
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.csv':
            return process_csv_for_may(file_path, date_range)
        elif file_extension in ['.xlsx', '.xls']:
            return process_excel_for_may(file_path, date_range)
        else:
            return {
                'success': False,
                'message': f'Unsupported file type: {file_extension}'
            }
            
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return {
            'success': False,
            'message': f'File processing error: {str(e)}'
        }

def process_csv_for_may(file_path, date_range):
    """Process CSV files for May data extraction with robust parsing"""
    try:
        # Try multiple parsing strategies for real fleet data
        df = None
        
        # Strategy 1: Read with flexible field detection
        try:
            df = pd.read_csv(file_path, sep=',', on_bad_lines='skip', encoding='utf-8')
        except:
            # Strategy 2: Try with different separator
            try:
                df = pd.read_csv(file_path, sep=';', on_bad_lines='skip', encoding='utf-8')
            except:
                # Strategy 3: Read as raw text and parse manually
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Find the most common field count
                field_counts = {}
                for line in lines[1:10]:  # Check first 10 data lines
                    count = len(line.split(','))
                    field_counts[count] = field_counts.get(count, 0) + 1
                
                expected_fields = max(field_counts, key=field_counts.get)
                
                # Read with the expected field count
                df = pd.read_csv(file_path, sep=',', on_bad_lines='skip', 
                               names=range(expected_fields), header=0)
        
        if df is None or df.empty:
            return {
                'success': False,
                'message': 'Could not parse CSV file - no valid data found'
            }
        
        logger.info(f"Successfully parsed CSV with {len(df)} rows and {len(df.columns)} columns")
        
        # Extract relevant data for May 23-27
        may_data = extract_may_driver_data(df, date_range)
        
        # Save processed data
        output_path = save_processed_may_data(may_data, file_path.stem, 'csv')
        
        return {
            'success': True,
            'records_found': len(may_data),
            'output_path': str(output_path),
            'data_preview': may_data[:5] if may_data else [],
            'file_info': {
                'rows': len(df),
                'columns': len(df.columns),
                'filename': file_path.name
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing CSV {file_path}: {e}")
        return {
            'success': False,
            'message': f'CSV processing error: {str(e)}'
        }

def process_excel_for_may(file_path, date_range):
    """Process Excel files for May data extraction"""
    try:
        # Try to read Excel file
        df = pd.read_excel(file_path)
        
        # Extract May-specific data
        may_data = extract_may_driver_data(df, date_range)
        
        # Save processed data
        output_path = save_processed_may_data(may_data, file_path.stem, 'excel')
        
        return {
            'success': True,
            'records_found': len(may_data),
            'output_path': str(output_path),
            'data_preview': may_data[:5] if may_data else []
        }
        
    except Exception as e:
        logger.error(f"Error processing Excel {file_path}: {e}")
        return {
            'success': False,
            'message': f'Excel processing error: {str(e)}'
        }

def extract_may_driver_data(df, date_range):
    """Extract driver data specifically for May 23-27 range"""
    may_records = []
    
    try:
        # Define target dates for May 23-27
        target_dates = ['2025-05-23', '2025-05-24', '2025-05-25', '2025-05-26', '2025-05-27']
        
        # Process each row looking for driver data
        for index, row in df.iterrows():
            # Extract driver information based on your data structure
            driver_record = {
                'date': None,
                'driver_name': None,
                'job_site': None,
                'start_time': None,
                'end_time': None,
                'status': None,
                'vehicle': None
            }
            
            # Look for common column patterns in your data
            for col in df.columns:
                col_lower = str(col).lower()
                
                # Driver name patterns
                if any(pattern in col_lower for pattern in ['name', 'driver', 'employee']):
                    driver_record['driver_name'] = str(row[col]) if pd.notna(row[col]) else None
                
                # Date patterns
                elif any(pattern in col_lower for pattern in ['date', 'day']):
                    date_val = row[col]
                    if pd.notna(date_val):
                        # Try to parse date
                        try:
                            if isinstance(date_val, str):
                                parsed_date = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                            else:
                                parsed_date = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                            driver_record['date'] = parsed_date
                        except:
                            pass
                
                # Job site patterns
                elif any(pattern in col_lower for pattern in ['job', 'site', 'location', 'project']):
                    driver_record['job_site'] = str(row[col]) if pd.notna(row[col]) else None
                
                # Time patterns
                elif 'start' in col_lower and 'time' in col_lower:
                    driver_record['start_time'] = str(row[col]) if pd.notna(row[col]) else None
                elif 'end' in col_lower and 'time' in col_lower:
                    driver_record['end_time'] = str(row[col]) if pd.notna(row[col]) else None
                
                # Vehicle patterns
                elif any(pattern in col_lower for pattern in ['vehicle', 'truck', 'asset']):
                    driver_record['vehicle'] = str(row[col]) if pd.notna(row[col]) else None
            
            # Only include records with valid data for target dates
            if (driver_record['date'] in target_dates and 
                driver_record['driver_name'] and 
                driver_record['driver_name'] != 'nan'):
                
                # Determine status based on timing
                if driver_record['start_time'] and driver_record['end_time']:
                    driver_record['status'] = 'On Time'  # Default - would need logic for late/early
                else:
                    driver_record['status'] = 'Not On Job'
                
                may_records.append(driver_record)
        
        logger.info(f"Extracted {len(may_records)} records for May 23-27")
        return may_records
        
    except Exception as e:
        logger.error(f"Error extracting May data: {e}")
        return []

def save_processed_may_data(may_data, filename, file_type):
    """Save processed May data to output directory"""
    try:
        output_dir = Path('./processed')
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / f"may_processed_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_path, 'w') as f:
            json.dump({
                'filename': filename,
                'file_type': file_type,
                'processed_date': datetime.now().isoformat(),
                'date_range': 'may-23-27',
                'records_count': len(may_data),
                'records': may_data
            }, f, indent=2)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error saving processed data: {e}")
        return None

def generate_may_reports(processed_files):
    """Generate comprehensive May reports from processed data"""
    try:
        all_may_data = []
        
        # Combine all processed data
        for file_info in processed_files:
            if file_info['processed'] and file_info['result']['success']:
                output_path = file_info['result']['output_path']
                if os.path.exists(output_path):
                    with open(output_path, 'r') as f:
                        data = json.load(f)
                        all_may_data.extend(data.get('records', []))
        
        if not all_may_data:
            return {
                'daily_reports': {},
                'weekly_summary': {},
                'monthly_update': {}
            }
        
        # Generate daily reports for each day
        daily_reports = {}
        for date in ['2025-05-23', '2025-05-24', '2025-05-25', '2025-05-26', '2025-05-27']:
            day_data = [record for record in all_may_data if record.get('date') == date]
            daily_reports[date] = {
                'date': date,
                'total_drivers': len(day_data),
                'on_time': len([r for r in day_data if r.get('status') == 'On Time']),
                'issues': len([r for r in day_data if r.get('status') != 'On Time']),
                'drivers': day_data
            }
        
        # Generate week summary
        weekly_summary = {
            'week_range': 'May 23-27, 2025',
            'total_drivers': len(set(record.get('driver_name') for record in all_may_data)),
            'total_records': len(all_may_data),
            'daily_breakdown': daily_reports
        }
        
        # Update monthly totals
        monthly_update = {
            'month': 'May 2025',
            'new_records_added': len(all_may_data),
            'date_range_covered': 'May 23-27, 2025',
            'ready_for_monthly_report': True
        }
        
        # Save comprehensive May report
        save_may_comprehensive_report({
            'daily_reports': daily_reports,
            'weekly_summary': weekly_summary,
            'monthly_update': monthly_update
        })
        
        return {
            'daily_reports': daily_reports,
            'weekly_summary': weekly_summary,
            'monthly_update': monthly_update
        }
        
    except Exception as e:
        logger.error(f"Error generating May reports: {e}")
        return {}

def save_may_comprehensive_report(report_data):
    """Save comprehensive May report"""
    try:
        reports_dir = Path('./reports')
        reports_dir.mkdir(exist_ok=True)
        
        report_path = reports_dir / f"may_comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Saved comprehensive May report to {report_path}")
        return report_path
        
    except Exception as e:
        logger.error(f"Error saving comprehensive report: {e}")
        return None

@may_processor_bp.route('/view-may-reports')
def view_may_reports():
    """View generated May reports"""
    try:
        # Load the most recent May report
        reports_dir = Path('./reports')
        if not reports_dir.exists():
            return render_template('may_reports_view.html', reports=None)
        
        may_reports = list(reports_dir.glob('may_comprehensive_report_*.json'))
        if not may_reports:
            return render_template('may_reports_view.html', reports=None)
        
        # Load the most recent report
        latest_report = max(may_reports, key=os.path.getmtime)
        with open(latest_report, 'r') as f:
            report_data = json.load(f)
        
        return render_template('may_reports_view.html', reports=report_data)
        
    except Exception as e:
        logger.error(f"Error viewing May reports: {e}")
        flash(f'Error loading reports: {str(e)}', 'error')
        return redirect(url_for('index'))