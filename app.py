import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from utils import load_data, filter_assets, get_asset_by_id, get_asset_categories, get_asset_locations, get_asset_status

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fleet-management-default-key")

# Start the scheduler in a background thread
try:
    from scheduler import start_scheduler_thread
    scheduler_thread = start_scheduler_thread()
    logger.info("Scheduler started successfully")
except Exception as e:
    logger.warning(f"Failed to start scheduler: {e}")

# Load data from JSON file or API
try:
    # Default fallback file path
    file_path = 'attached_assets/GAUGE API PULL 1045AM_05.15.2025.json'
    
    # Check if we already have a cached processed file
    cache_file = 'data/processed_data.json'
    if os.path.exists(cache_file):
        logger.info(f"Found cached data file: {cache_file}")
        file_path = cache_file
    
    assets_data = load_data(file_path)
    logger.info(f"Successfully loaded {len(assets_data)} assets")
except Exception as e:
    logger.error(f"Error loading data: {e}")
    assets_data = []

# Routes
@app.route('/')
def index():
    """Render the main dashboard page"""
    # Get filter parameters from query string
    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')
    location = request.args.get('location', 'all')
    
    # Filter assets based on parameters
    filtered_assets = filter_assets(assets_data, status, category, location)
    
    # Get categories and locations for filter dropdowns
    categories = get_asset_categories(assets_data)
    locations = get_asset_locations(assets_data)
    
    # Calculate dashboard metrics
    total_assets = len(assets_data)
    active_assets = len([a for a in assets_data if a.get('Active', False)])
    inactive_assets = total_assets - active_assets
    
    return render_template('index.html', 
                          assets=filtered_assets,
                          categories=categories,
                          locations=locations,
                          total_assets=total_assets,
                          active_assets=active_assets,
                          inactive_assets=inactive_assets,
                          current_status=status,
                          current_category=category,
                          current_location=location)

@app.route('/asset/<asset_id>')
def asset_detail(asset_id):
    """Render the asset detail page"""
    asset = get_asset_by_id(assets_data, asset_id)
    
    if not asset:
        flash('Asset not found', 'danger')
        return redirect(url_for('index'))
    
    return render_template('asset_detail.html', asset=asset)

@app.route('/reports')
def reports():
    """Render the reports page"""
    # Get categories and locations for charts
    categories = get_asset_categories(assets_data)
    locations = get_asset_locations(assets_data)
    
    # Calculate status counts for reports
    status_counts = {
        'active': len([a for a in assets_data if a.get('Active', False)]),
        'inactive': len([a for a in assets_data if not a.get('Active', False)])
    }
    
    # Count assets by category
    category_counts = {}
    for cat in categories:
        category_counts[cat] = len([a for a in assets_data if a.get('AssetCategory') == cat])
    
    # Count assets by location
    location_counts = {}
    for loc in locations:
        location_counts[loc] = len([a for a in assets_data if a.get('Location') == loc])
    
    # Maintenance data
    maintenance_items = []
    maintenance_due_count = 0
    high_priority_maintenance = 0
    avg_engine_hours = 0
    total_engine_hours = 0
    engine_hours_count = 0
    
    # Calculate maintenance metrics
    for asset in assets_data:
        engine_hours = asset.get('Engine1Hours')
        if engine_hours:
            try:
                engine_hours = float(engine_hours)
                total_engine_hours += engine_hours
                engine_hours_count += 1
                
                # Maintenance thresholds (in hours)
                oil_change = 250
                filter_change = 500
                major_service = 1000
                
                # Calculate hours until next maintenance
                hours_until_oil = oil_change - (engine_hours % oil_change)
                hours_until_filter = filter_change - (engine_hours % filter_change)
                hours_until_major = major_service - (engine_hours % major_service)
                
                # Add to maintenance items if due soon
                threshold = 50  # Consider "due soon" if within 50 hours
                
                if hours_until_oil <= threshold or hours_until_filter <= threshold or hours_until_major <= threshold:
                    maintenance_due_count += 1
                    
                    # Determine service type and priority
                    if hours_until_major <= threshold:
                        service_type = "Major Service"
                        hours_remaining = hours_until_major
                        priority = "High" if hours_until_major <= 20 else "Medium"
                    elif hours_until_filter <= threshold:
                        service_type = "Filter Change"
                        hours_remaining = hours_until_filter
                        priority = "High" if hours_until_filter <= 10 else "Medium"
                    else:
                        service_type = "Oil Change"
                        hours_remaining = hours_until_oil
                        priority = "High" if hours_until_oil <= 10 else "Medium"
                    
                    if priority == "High":
                        high_priority_maintenance += 1
                        
                    maintenance_items.append({
                        "asset_id": asset.get('AssetIdentifier'),
                        "asset_label": asset.get('Label', ''),
                        "engine_hours": engine_hours,
                        "service_type": service_type,
                        "hours_remaining": int(hours_remaining),
                        "priority": priority
                    })
            except (ValueError, TypeError):
                pass
    
    # Calculate average engine hours
    if engine_hours_count > 0:
        avg_engine_hours = total_engine_hours / engine_hours_count
    
    # Sort maintenance items by priority (high first) and hours remaining
    maintenance_items = sorted(
        maintenance_items, 
        key=lambda x: (0 if x['priority'] == 'High' else 1, x['hours_remaining'])
    )
    
    # Activity trend data (last 7 days - example data)
    # In a real implementation, this would come from historical data
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    activity_trend_days = [(today - timedelta(days=i)).strftime('%m/%d') for i in range(6, -1, -1)]
    
    # Example data - in real implementation, we would query a database for historical counts
    activity_trend_active = [450, 455, 460, 465, 462, 470, 475]
    activity_trend_inactive = [251, 246, 241, 236, 239, 231, 226]
    
    # Get top utilized assets
    top_utilized_assets = []
    for asset in assets_data:
        if asset.get('Active', False) and asset.get('Engine1Hours'):
            try:
                engine_hours = float(asset.get('Engine1Hours', 0))
                # Calculate a utilization score (example formula)
                utilization_score = min(100, int((engine_hours / 5000) * 100))
                
                asset_copy = asset.copy()
                asset_copy['utilization_score'] = utilization_score
                top_utilized_assets.append(asset_copy)
            except (ValueError, TypeError):
                pass
    
    # Sort by utilization score and take top 10
    top_utilized_assets = sorted(top_utilized_assets, key=lambda x: x['utilization_score'], reverse=True)[:10]
    
    # Get recent activities (example data)
    recent_activities = [
        {
            "icon": "power-off",
            "title": "Asset Activated",
            "time": "Today, 10:45 AM",
            "description": "EX-34 JOHN DEERE 250G LC was activated at work site",
            "location": "DFW Yard"
        },
        {
            "icon": "map-marker-alt",
            "title": "Location Change",
            "time": "Today, 9:30 AM",
            "description": "R-16 SAKAI SV410 moved to new location",
            "location": "2022-023 Riverfront & Cadiz Bridge Improvement"
        },
        {
            "icon": "tools",
            "title": "Maintenance Performed",
            "time": "Yesterday, 3:15 PM",
            "description": "Oil change completed for SS-11 BOBCAT T750",
            "location": "DFW Yard"
        },
        {
            "icon": "exclamation-triangle",
            "title": "Alert Triggered",
            "time": "Yesterday, 11:20 AM",
            "description": "Low battery warning for ML-03 GENIE S60X",
            "location": "2023-032 SH 345 BRIDGE REHABILITATION"
        },
        {
            "icon": "clock",
            "title": "Engine Hours Updated",
            "time": "3 days ago",
            "description": "Engine hours milestone: D-13 CAT D3K2 XL reached 4000 hours",
            "location": "2022-023 Riverfront & Cadiz Bridge Improvement"
        }
    ]
    
    # Format last updated time
    from datetime import datetime
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return render_template('reports.html', 
                          assets=assets_data,
                          status_counts=status_counts,
                          category_counts=category_counts,
                          location_counts=location_counts,
                          maintenance_items=maintenance_items,
                          maintenance_due_count=maintenance_due_count,
                          high_priority_maintenance=high_priority_maintenance,
                          avg_engine_hours=avg_engine_hours,
                          activity_trend_days=activity_trend_days,
                          activity_trend_active=activity_trend_active,
                          activity_trend_inactive=activity_trend_inactive,
                          top_utilized_assets=top_utilized_assets,
                          recent_activities=recent_activities,
                          last_updated=last_updated)

@app.route('/api/assets')
def api_assets():
    """API endpoint to get asset data in JSON format"""
    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')
    location = request.args.get('location', 'all')
    
    filtered_assets = filter_assets(assets_data, status, category, location)
    return jsonify(filtered_assets)

@app.route('/api/asset/<asset_id>')
def api_asset_detail(asset_id):
    """API endpoint to get a specific asset by ID"""
    asset = get_asset_by_id(assets_data, asset_id)
    
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    return jsonify(asset)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('base.html', error="404 - Page Not Found"), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {e}")
    return render_template('base.html', error="500 - Server Error"), 500

@app.route('/admin')
def admin_settings():
    """Admin settings page for API configuration"""
    # Get current configuration
    config = {
        'GAUGE_API_URL': os.environ.get('GAUGE_API_URL', 'https://api.gaugegps.com/v1/'),
        'GAUGE_API_KEY': os.environ.get('GAUGE_API_KEY', ''),
        'GAUGE_API_USER': os.environ.get('GAUGE_API_USER', ''),
        'GAUGE_API_PASSWORD': os.environ.get('GAUGE_API_PASSWORD', ''),
        'ENABLE_AUTO_UPDATES': os.environ.get('ENABLE_AUTO_UPDATES', 'true').lower() == 'true',
        'MORNING_UPDATE_TIME': os.environ.get('MORNING_UPDATE_TIME', '07:00'),
        'MIDDAY_UPDATE_TIME': os.environ.get('MIDDAY_UPDATE_TIME', '12:00'),
        'EVENING_UPDATE_TIME': os.environ.get('EVENING_UPDATE_TIME', '17:00'),
    }
    
    # Get data status information
    from datetime import datetime
    import time
    import schedule
    
    # Get last update time from file modification time
    cache_file = 'data/processed_data.json'
    last_update = 'Never'
    if os.path.exists(cache_file):
        mtime = os.path.getmtime(cache_file)
        last_update = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    # Determine data source
    data_source = 'File'
    if os.environ.get('GAUGE_API_KEY') or (os.environ.get('GAUGE_API_USER') and os.environ.get('GAUGE_API_PASSWORD')):
        data_source = 'API'
    
    # Get next scheduled update
    next_update = 'N/A'
    if config['ENABLE_AUTO_UPDATES']:
        # Try to get next job's scheduled time
        jobs = schedule.get_jobs()
        if jobs:
            # Find the next job time
            next_runs = [job.next_run for job in jobs if job.next_run is not None]
            if next_runs:
                next_run = min(next_runs)
                next_update = next_run.strftime('%Y-%m-%d %H:%M:%S')
    
    data_status = {
        'last_update': last_update,
        'asset_count': len(assets_data),
        'source': data_source,
        'next_update': next_update
    }
    
    return render_template('admin.html', config=config, data_status=data_status)

@app.route('/admin', methods=['POST'])
def update_admin_settings():
    """Update admin settings"""
    # Get form data
    gauge_api_url = request.form.get('gauge_api_url', 'https://api.gaugegps.com/v1/')
    gauge_api_key = request.form.get('gauge_api_key', '')
    gauge_api_user = request.form.get('gauge_api_user', '')
    gauge_api_password = request.form.get('gauge_api_password', '')
    enable_auto_updates = 'enable_auto_updates' in request.form
    morning_update = request.form.get('morning_update', '07:00')
    midday_update = request.form.get('midday_update', '12:00')
    evening_update = request.form.get('evening_update', '17:00')
    
    # Update environment variables
    os.environ['GAUGE_API_URL'] = gauge_api_url
    os.environ['GAUGE_API_KEY'] = gauge_api_key
    os.environ['GAUGE_API_USER'] = gauge_api_user
    if gauge_api_password:  # Only update password if provided
        os.environ['GAUGE_API_PASSWORD'] = gauge_api_password
    os.environ['ENABLE_AUTO_UPDATES'] = str(enable_auto_updates).lower()
    os.environ['MORNING_UPDATE_TIME'] = morning_update
    os.environ['MIDDAY_UPDATE_TIME'] = midday_update
    os.environ['EVENING_UPDATE_TIME'] = evening_update
    
    # Save settings to config file for persistence across restarts
    config_dir = 'config'
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    try:
        config_file = os.path.join(config_dir, 'settings.json')
        config = {
            'GAUGE_API_URL': gauge_api_url,
            'GAUGE_API_KEY': gauge_api_key,
            'GAUGE_API_USER': gauge_api_user,
            'ENABLE_AUTO_UPDATES': enable_auto_updates,
            'MORNING_UPDATE_TIME': morning_update,
            'MIDDAY_UPDATE_TIME': midday_update,
            'EVENING_UPDATE_TIME': evening_update
        }
        
        with open(config_file, 'w') as f:
            import json
            json.dump(config, f, indent=2)
        
        # Restart scheduler with new settings
        try:
            from scheduler import start_scheduler_thread
            global scheduler_thread
            scheduler_thread = start_scheduler_thread()
            logger.info("Restarted scheduler with new settings")
        except Exception as e:
            logger.warning(f"Failed to restart scheduler: {e}")
        
        flash("Settings updated successfully", "success")
    except Exception as e:
        flash(f"Error saving settings: {e}", "danger")
        logger.error(f"Error saving settings: {e}")
    
    return redirect(url_for('admin_settings'))

@app.route('/update')
def manual_update():
    """Manually update data from API"""
    try:
        # Clear data cache
        cache_file = 'data/processed_data.json'
        if os.path.exists(cache_file):
            os.remove(cache_file)
        
        # Force update from API
        from gauge_api import update_asset_data
        assets = update_asset_data(force=True)
        
        if assets:
            # Generate reports
            from reports_processor import generate_reports
            generate_reports(assets)
            
            # Reload global assets_data
            global assets_data
            assets_data = assets
            
            flash(f"Successfully updated data. Retrieved {len(assets)} assets.", "success")
        else:
            flash("Failed to update data from API. Check your API configuration.", "warning")
    except Exception as e:
        flash(f"Error updating data: {e}", "danger")
        logger.error(f"Error manually updating data: {e}")
    
    return redirect(url_for('admin_settings'))
