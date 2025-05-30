"""
Gauge Data Manager - Upload and API Fact-Checking System
Handles your authentic Gauge reports with validation against API
"""

import os
import json
import pandas as pd
import requests
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from services.execute_sql_direct import execute_sql_query
# from services.enterprise_attendance_matrix import get_enterprise_matrix

gauge_bp = Blueprint('gauge_data', __name__)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@gauge_bp.route('/gauge-data-manager')
def gauge_dashboard():
    """Gauge data management dashboard"""
    try:
        # Get existing Gauge data from database
        gauge_records = execute_sql_query("""
            SELECT * FROM public.attendance_matrix 
            WHERE source = 'gauge' 
            ORDER BY date DESC 
            LIMIT 50
        """)
        
        # Get API validation status
        api_status = check_gauge_api_status()
        
        return render_template('gauge/dashboard.html', 
                             gauge_records=gauge_records,
                             api_status=api_status)
    except Exception as e:
        return render_template('gauge/dashboard.html', 
                             gauge_records=[],
                             api_status={'connected': False, 'error': str(e)})

@gauge_bp.route('/gauge-data-manager/upload', methods=['GET', 'POST'])
def upload_gauge_data():
    """Upload and process Gauge reports"""
    if request.method == 'POST':
        try:
            files = request.files.getlist('gauge_files')
            if not files or files[0].filename == '':
                flash('No files selected', 'error')
                return redirect(request.url)
            
            results = []
            
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    
                    # Process the file based on type
                    if filename.lower().endswith('.csv'):
                        result = process_gauge_csv(file, filename)
                    elif filename.lower().endswith(('.xlsx', '.xls')):
                        result = process_gauge_excel(file, filename)
                    elif filename.lower().endswith('.pdf'):
                        result = process_gauge_pdf(file, filename)
                    else:
                        result = {'success': False, 'filename': filename, 'error': 'Unsupported file type'}
                    
                    results.append(result)
            
            # Fact-check against API
            fact_check_results = fact_check_uploaded_data(results)
            
            return jsonify({
                'success': True,
                'upload_results': results,
                'fact_check': fact_check_results,
                'total_files': len(results)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    return render_template('gauge/upload.html')

def process_gauge_csv(file, filename):
    """Process Gauge CSV file"""
    try:
        df = pd.read_csv(file)
        
        # Map common Gauge CSV columns
        records_processed = 0
        for _, row in df.iterrows():
            record = extract_gauge_record(row)
            if record and insert_gauge_record(record):
                records_processed += 1
        
        return {
            'success': True,
            'filename': filename,
            'type': 'csv',
            'records_processed': records_processed
        }
    except Exception as e:
        return {
            'success': False,
            'filename': filename,
            'error': str(e)
        }

def process_gauge_excel(file, filename):
    """Process Gauge Excel file"""
    try:
        # Try multiple sheet names common in Gauge reports
        sheet_names = ['Asset Report', 'Activity Detail', 'Time on Site', 'Weekly Summary', 'Sheet1']
        df = None
        
        for sheet in sheet_names:
            try:
                df = pd.read_excel(file, sheet_name=sheet)
                break
            except:
                continue
        
        if df is None:
            df = pd.read_excel(file)  # Default to first sheet
        
        records_processed = 0
        for _, row in df.iterrows():
            record = extract_gauge_record(row)
            if record and insert_gauge_record(record):
                records_processed += 1
        
        return {
            'success': True,
            'filename': filename,
            'type': 'excel',
            'records_processed': records_processed
        }
    except Exception as e:
        return {
            'success': False,
            'filename': filename,
            'error': str(e)
        }

def process_gauge_pdf(file, filename):
    """Process Gauge PDF report"""
    try:
        # Basic PDF processing - would need more sophisticated parsing
        return {
            'success': True,
            'filename': filename,
            'type': 'pdf',
            'records_processed': 0,
            'note': 'PDF processing requires manual review'
        }
    except Exception as e:
        return {
            'success': False,
            'filename': filename,
            'error': str(e)
        }

def extract_gauge_record(row):
    """Extract standardized record from Gauge data row"""
    try:
        # Handle various Gauge column naming conventions
        asset_id = row.get('Asset ID') or row.get('AssetId') or row.get('Unit') or row.get('Equipment')
        if not asset_id:
            return None
        
        # Parse timestamp
        timestamp = row.get('DateTime') or row.get('Date') or row.get('Timestamp')
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    timestamp = pd.to_datetime(timestamp)
                date = timestamp.date()
            except:
                date = datetime.now().date()
        else:
            date = datetime.now().date()
        
        return {
            'date': date,
            'asset_id': str(asset_id),
            'start_time': timestamp if timestamp else None,
            'job_site': row.get('Location') or row.get('JobSite') or '',
            'engine_hours': float(row.get('Engine Hours', 0) or 0),
            'status': row.get('Status') or 'Unknown',
            'latitude': float(row.get('Latitude', 0) or 0),
            'longitude': float(row.get('Longitude', 0) or 0),
            'source': 'gauge'
        }
    except Exception as e:
        return None

def insert_gauge_record(record):
    """Insert Gauge record into database"""
    try:
        execute_sql_query(f"""
            INSERT INTO public.attendance_matrix 
            (date, asset_id, start_time, job_site, status, source, created_at)
            VALUES ('{record['date']}', '{record['asset_id']}', 
                    '{record['start_time']}', '{record['job_site']}',
                    '{record['status']}', 'gauge', NOW())
            ON CONFLICT DO NOTHING
        """)
        return True
    except Exception as e:
        return False

def check_gauge_api_status():
    """Check Gauge API connection status"""
    try:
        url = 'https://api.gaugesmart.com/AssetList/28dcba94c01e453fa8e9215a068f30e4'
        auth = ('bwatson', 'Plsw@2900413477')
        
        response = requests.get(url, auth=auth, verify=False, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'connected': True,
                'asset_count': len(data) if isinstance(data, list) else 0,
                'last_checked': datetime.now().isoformat()
            }
        else:
            return {
                'connected': False,
                'error': f'API returned status {response.status_code}',
                'last_checked': datetime.now().isoformat()
            }
    except Exception as e:
        return {
            'connected': False,
            'error': str(e),
            'last_checked': datetime.now().isoformat()
        }

def fact_check_uploaded_data(upload_results):
    """Fact-check uploaded data against Gauge API"""
    try:
        # Get current API data
        api_status = check_gauge_api_status()
        if not api_status['connected']:
            return {
                'status': 'api_unavailable',
                'message': 'Cannot fact-check: API connection failed'
            }
        
        # Get API asset list
        url = 'https://api.gaugesmart.com/AssetList/28dcba94c01e453fa8e9215a068f30e4'
        auth = ('bwatson', 'Plsw@2900413477')
        response = requests.get(url, auth=auth, verify=False, timeout=10)
        api_assets = response.json()
        
        # Create API asset lookup
        api_asset_ids = set()
        if isinstance(api_assets, list):
            for asset in api_assets:
                asset_id = asset.get('AssetId') or asset.get('id')
                if asset_id:
                    api_asset_ids.add(str(asset_id))
        
        # Get uploaded asset IDs
        uploaded_assets = execute_sql_query("""
            SELECT DISTINCT asset_id FROM public.attendance_matrix 
            WHERE source = 'gauge' AND created_at >= CURRENT_DATE
        """)
        
        uploaded_asset_ids = {record['asset_id'] for record in uploaded_assets}
        
        # Compare
        verified_assets = uploaded_asset_ids.intersection(api_asset_ids)
        unverified_assets = uploaded_asset_ids - api_asset_ids
        
        return {
            'status': 'completed',
            'total_uploaded': len(uploaded_asset_ids),
            'verified_count': len(verified_assets),
            'unverified_count': len(unverified_assets),
            'verified_assets': list(verified_assets),
            'unverified_assets': list(unverified_assets),
            'accuracy_rate': (len(verified_assets) / len(uploaded_asset_ids) * 100) if uploaded_asset_ids else 0
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

@gauge_bp.route('/api/gauge-api-sync')
def sync_with_gauge_api():
    """Sync directly with Gauge API"""
    try:
        url = 'https://api.gaugesmart.com/AssetList/28dcba94c01e453fa8e9215a068f30e4'
        auth = ('bwatson', 'Plsw@2900413477')
        
        response = requests.get(url, auth=auth, verify=False, timeout=10)
        if response.status_code != 200:
            return jsonify({'success': False, 'error': f'API error: {response.status_code}'})
        
        api_data = response.json()
        synced_count = 0
        
        for asset in api_data:
            record = {
                'date': datetime.now().date(),
                'asset_id': str(asset.get('AssetId', asset.get('id', 'unknown'))),
                'start_time': datetime.now(),
                'job_site': asset.get('Location', ''),
                'status': asset.get('Status', 'Unknown'),
                'latitude': float(asset.get('Latitude', 0) or 0),
                'longitude': float(asset.get('Longitude', 0) or 0),
                'source': 'gauge_api'
            }
            
            if insert_gauge_record(record):
                synced_count += 1
        
        return jsonify({
            'success': True,
            'synced_count': synced_count,
            'total_api_assets': len(api_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@gauge_bp.route('/api/gauge-fact-check')
def manual_fact_check():
    """Manual fact-check trigger"""
    try:
        recent_uploads = execute_sql_query("""
            SELECT filename, COUNT(*) as records 
            FROM public.attendance_matrix 
            WHERE source = 'gauge' AND created_at >= CURRENT_DATE - INTERVAL '1 day'
            GROUP BY filename
        """)
        
        fact_check = fact_check_uploaded_data(recent_uploads)
        return jsonify(fact_check)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})