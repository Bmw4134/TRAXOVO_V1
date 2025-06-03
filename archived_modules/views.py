"""
TRAXORA Fleet Management System - Core Views

This module contains the core views for the main application.
"""
import os
import logging
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import text

# Set up logging
logger = logging.getLogger(__name__)

def register_views(app):
    """Register view functions with the Flask app"""
    
    from app import db
    
    # Helper functions for the dashboard
    def check_gauge_api_status():
        """Check the status of the Gauge API connection."""
        try:
            from gauge_api_legacy import GaugeAPI
            api = GaugeAPI()
            return api.check_connection()
        except Exception as e:
            logger.error(f"Failed to check Gauge API status: {str(e)}")
            return False

    def check_database_status():
        """Check the status of the database connection."""
        try:
            # Use text() from sqlalchemy to create a proper SQL expression
            db.session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Failed to check database status: {str(e)}")
            return False

    def check_filesystem_status():
        """Check if required directories are available and writable."""
        required_dirs = ['data', 'reports', 'exports', 'uploads', 'templates', 'static']
        try:
            for directory in required_dirs:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    logger.info(f"Created missing directory: {directory}")
                
                # Try to create a test file to verify write permissions
                test_file = os.path.join(directory, '.write_test')
                with open(test_file, 'w') as f:
                    f.write('test')
                if os.path.exists(test_file):
                    os.remove(test_file)
            return True
        except Exception as e:
            logger.error(f"Failed to check filesystem status: {str(e)}")
            return False

    def get_asset_count():
        """Get the total count of assets in the system."""
        try:
            from models import Asset
            return Asset.query.count()
        except Exception as e:
            logger.error(f"Failed to get asset count: {str(e)}")
            # Fallback to direct data file check
            try:
                import glob
                asset_files = glob.glob('data/assets/*.json')
                if asset_files:
                    return len(asset_files)
                return 0
            except Exception as inner_e:
                logger.error(f"Failed to get asset count from files: {str(inner_e)}")
                return 0

    def get_driver_count():
        """Get the total count of drivers in the system."""
        try:
            from models import Driver
            return Driver.query.count()
        except Exception as e:
            logger.error(f"Failed to get driver count: {str(e)}")
            # Fallback to direct data file check
            try:
                import csv
                driver_file = 'data/drivers.csv'
                if os.path.exists(driver_file):
                    with open(driver_file, 'r') as f:
                        reader = csv.reader(f)
                        # Subtract 1 for header row
                        return max(0, sum(1 for _ in reader) - 1)
                return 0
            except Exception as inner_e:
                logger.error(f"Failed to get driver count from file: {str(inner_e)}")
                return 0

    def get_last_sync_time():
        """Get the timestamp of the last data synchronization."""
        try:
            # Check multiple possible locations for sync timestamp
            possible_files = [
                os.path.join('data', 'last_sync.txt'),
                os.path.join('data', 'api_sync.log'),
                os.path.join('logs', 'sync.log')
            ]
            
            for sync_file in possible_files:
                if os.path.exists(sync_file):
                    with open(sync_file, 'r') as f:
                        content = f.read().strip()
                        if content:
                            return content
            
            # If no sync file found, check the modification time of data directory
            data_dir = 'data'
            if os.path.exists(data_dir):
                mtime = os.path.getmtime(data_dir)
                return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            return 'Never'
        except Exception as e:
            logger.error(f"Failed to get last sync time: {str(e)}")
            return 'Unknown'
    
    @app.route('/')
    def index():
        """Application main dashboard"""
        # API status check
        api_status = {
            'gauge_api': check_gauge_api_status(),
            'database': check_database_status(),
            'file_system': check_filesystem_status()
        }
        
        # Get system stats
        system_stats = {
            'asset_count': get_asset_count(),
            'driver_count': get_driver_count(),
            'last_sync': get_last_sync_time()
        }
        
        return render_template('dashboard.html', 
                            api_status=api_status,
                            system_stats=system_stats,
                            current_date=datetime.now().strftime('%Y-%m-%d'))
    
    @app.route('/asset-map')
    def asset_map_redirect():
        """Direct access to the Asset Map"""
        return redirect(url_for('asset_map.asset_map'))
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'ok',
            'database': check_database_status(),
            'gauge_api': check_gauge_api_status(),
            'filesystem': check_filesystem_status(),
            'timestamp': datetime.now().isoformat()
        })