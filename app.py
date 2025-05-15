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
    
    return render_template('reports.html', 
                          status_counts=status_counts,
                          category_counts=category_counts,
                          location_counts=location_counts)

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
