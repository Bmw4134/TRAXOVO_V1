"""
MTD Data Review Dashboard

Complete interface for reviewing all your Month-to-Date fleet data
with filtering, search, and detailed analysis capabilities.
"""

from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from utils.monthly_report_generator import extract_all_drivers_from_mtd

logger = logging.getLogger(__name__)

mtd_review_bp = Blueprint('mtd_review', __name__, url_prefix='/mtd-review')

@mtd_review_bp.route('/')
def dashboard():
    """Complete MTD Data Review Dashboard"""
    
    try:
        # Load your complete MTD dataset
        mtd_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
        
        if os.path.exists(mtd_file):
            # Process your real MTD data
            df = pd.read_csv(mtd_file, skiprows=8, low_memory=False)
            
            # Basic statistics with proper error handling
            total_records = len(df)
            unique_assets = 0
            date_range = {'start': 'Unknown', 'end': 'Unknown'}
            
            # Safe asset counting
            if 'Asset' in df.columns:
                try:
                    unique_assets = df['Asset'].nunique()
                except:
                    unique_assets = 0
            
            # Safe date range calculation
            if 'EventDateTime' in df.columns:
                try:
                    df_clean = df.dropna(subset=['EventDateTime'])
                    if len(df_clean) > 0:
                        date_range = {
                            'start': str(df_clean['EventDateTime'].min()),
                            'end': str(df_clean['EventDateTime'].max())
                        }
                except:
                    date_range = {'start': 'Processing...', 'end': 'Processing...'}
            
            # Get all drivers
            all_drivers = extract_all_drivers_from_mtd()
            
            # Activity summary by date
            daily_activity = {}
            recent_activity = 0
            
            if 'EventDateTime' in df.columns:
                try:
                    df['EventDateTime'] = pd.to_datetime(df['EventDateTime'], errors='coerce')
                    # Remove any null/invalid dates
                    valid_dates = df.dropna(subset=['EventDateTime'])
                    if len(valid_dates) > 0:
                        daily_activity = valid_dates.groupby(valid_dates['EventDateTime'].dt.date).size().to_dict()
                        daily_activity = {str(k): int(v) for k, v in daily_activity.items()}
                        
                        # Recent activity calculation
                        recent_cutoff = datetime.now() - timedelta(days=7)
                        recent_data = valid_dates[valid_dates['EventDateTime'] >= recent_cutoff]
                        recent_activity = len(recent_data)
                except Exception as e:
                    logger.warning(f"Date processing error: {e}")
                    daily_activity = {}
                    recent_activity = 0
            
        else:
            # Fallback data structure
            total_records = 0
            unique_assets = 0
            date_range = {'start': 'No data', 'end': 'No data'}
            all_drivers = []
            daily_activity = {}
            recent_activity = 0
        
        dashboard_data = {
            'total_records': total_records,
            'unique_assets': unique_assets,
            'total_drivers': len(all_drivers),
            'date_range': date_range,
            'daily_activity': daily_activity,
            'recent_activity': recent_activity,
            'drivers_list': all_drivers,
            'data_file': mtd_file,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render_template('mtd_review/dashboard.html', data=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error in MTD review dashboard: {e}")
        return f"Error loading MTD review: {e}"

@mtd_review_bp.route('/api/driver-details/<driver_name>')
def driver_details(driver_name):
    """Get detailed activity for a specific driver"""
    
    try:
        mtd_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
        
        if os.path.exists(mtd_file):
            df = pd.read_csv(mtd_file, skiprows=8, low_memory=False)
            
            # Filter for this driver's activity
            driver_data = df[df['Asset'].str.contains(driver_name, case=False, na=False)]
            
            activity_summary = {
                'driver_name': driver_name,
                'total_activities': len(driver_data),
                'date_range': {
                    'start': driver_data['EventDateTime'].min() if len(driver_data) > 0 else 'No data',
                    'end': driver_data['EventDateTime'].max() if len(driver_data) > 0 else 'No data'
                },
                'recent_records': driver_data.head(10).to_dict('records') if len(driver_data) > 0 else []
            }
            
            return jsonify(activity_summary)
        
        return jsonify({'error': 'MTD data file not found'})
        
    except Exception as e:
        return jsonify({'error': str(e)})

@mtd_review_bp.route('/api/date-analysis/<date>')
def date_analysis(date):
    """Get detailed analysis for a specific date"""
    
    try:
        mtd_file = "uploads/daily_reports/2025-05-26/Driving_History_DrivingHistory_050125-052625.csv"
        
        if os.path.exists(mtd_file):
            df = pd.read_csv(mtd_file, skiprows=8, low_memory=False)
            df['EventDateTime'] = pd.to_datetime(df['EventDateTime'], errors='coerce')
            
            # Filter for specific date
            target_date = pd.to_datetime(date).date()
            day_data = df[df['EventDateTime'].dt.date == target_date]
            
            analysis = {
                'date': date,
                'total_events': len(day_data),
                'unique_assets': day_data['Asset'].nunique() if len(day_data) > 0 else 0,
                'hourly_distribution': day_data.groupby(day_data['EventDateTime'].dt.hour).size().to_dict() if len(day_data) > 0 else {},
                'sample_records': day_data.head(20).to_dict('records') if len(day_data) > 0 else []
            }
            
            return jsonify(analysis)
        
        return jsonify({'error': 'MTD data file not found'})
        
    except Exception as e:
        return jsonify({'error': str(e)})