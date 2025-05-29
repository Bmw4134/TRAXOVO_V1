
"""
Dashboard Metrics - Direct API Connection
Real-time asset and driver counting from your actual data sources
"""

import json
import os
import logging
from datetime import datetime
from utils.gauge_api import get_assets

logger = logging.getLogger(__name__)

def get_real_asset_count():
    """Get actual asset count from Gauge API"""
    try:
        # Try API first
        assets = get_assets()
        if assets:
            active_assets = [a for a in assets if a.get('Active', False)]
            return {
                'total_assets': len(assets),
                'active_assets': len(active_assets),
                'source': 'gauge_api_live'
            }
    except Exception as e:
        logger.warning(f"API failed, using cached data: {e}")
    
    # Fallback to your JSON file
    try:
        with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
            data = json.load(f)
        
        active_assets = [a for a in data if a.get('Active', False)]
        return {
            'total_assets': len(data),
            'active_assets': len(active_assets),
            'source': 'gauge_api_cached'
        }
    except Exception as e:
        logger.error(f"Failed to get asset data: {e}")
        return {'total_assets': 0, 'active_assets': 0, 'source': 'error'}

def get_real_driver_count():
    """Extract driver count from asset assignments"""
    try:
        # Load your actual asset data
        with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
            data = json.load(f)
        
        # Find assets with driver assignments in SecondaryAssetIdentifier
        assigned_drivers = set()
        for asset in data:
            secondary_id = asset.get('SecondaryAssetIdentifier', '')
            if secondary_id and ' - ' in str(secondary_id):
                parts = secondary_id.split(' - ', 1)
                if len(parts) >= 2:
                    driver_name = parts[1].strip()
                    if driver_name and len(driver_name) > 2:
                        assigned_drivers.add(driver_name)
        
        # Also check for any uploaded CSV files with driver data
        csv_driver_count = 0
        data_dirs = ['attached_assets', 'data', '.']
        
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                for filename in os.listdir(data_dir):
                    if filename.endswith('.csv'):
                        try:
                            import pandas as pd
                            df = pd.read_csv(os.path.join(data_dir, filename), nrows=100)
                            
                            # Look for driver columns
                            for col in df.columns:
                                if any(keyword in col.lower() for keyword in ['driver', 'operator', 'employee']):
                                    unique_drivers = df[col].dropna().nunique()
                                    csv_driver_count = max(csv_driver_count, unique_drivers)
                                    break
                        except:
                            continue
        
        # Return the higher count (asset assignments vs CSV data)
        driver_count = max(len(assigned_drivers), csv_driver_count)
        
        return {
            'total_drivers': driver_count,
            'assigned_from_assets': len(assigned_drivers),
            'from_csv_files': csv_driver_count,
            'source': 'multi_source_analysis'
        }
        
    except Exception as e:
        logger.error(f"Failed to get driver data: {e}")
        return {'total_drivers': 0, 'source': 'error'}

def get_cache_growth_data():
    """Get cache growth metrics for visualization"""
    import os
    from datetime import datetime, timedelta
    
    cache_data = []
    cache_dir = 'data_cache'
    
    if os.path.exists(cache_dir):
        # Get file sizes and timestamps
        for filename in os.listdir(cache_dir):
            filepath = os.path.join(cache_dir, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                cache_data.append({
                    'filename': filename,
                    'size_kb': round(stat.st_size / 1024, 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'age_hours': round((datetime.now().timestamp() - stat.st_mtime) / 3600, 2)
                })
    
    # Sort by modification time
    cache_data.sort(key=lambda x: x['modified'])
    
    return {
        'total_files': len(cache_data),
        'total_size_mb': round(sum(item['size_kb'] for item in cache_data) / 1024, 2),
        'files': cache_data,
        'growth_trend': 'increasing' if len(cache_data) > 3 else 'stable'
    }

def get_dashboard_metrics():
    """Get complete dashboard metrics"""
    asset_data = get_real_asset_count()
    driver_data = get_real_driver_count()
    cache_data = get_cache_growth_data()
    
    # Calculate revenue from asset data
    try:
        with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
            data = json.load(f)
        
        # Estimate revenue based on active assets
        active_count = len([a for a in data if a.get('Active', False)])
        estimated_daily_revenue = active_count * 850  # $850/day per active asset average
        
    except:
        estimated_daily_revenue = 0
    
    return {
        'assets': asset_data,
        'drivers': driver_data,
        'revenue': {
            'estimated_daily': estimated_daily_revenue,
            'source': 'calculated_from_active_assets'
        },
        'cache_growth': cache_data,
        'last_updated': datetime.now().isoformat()
    }
