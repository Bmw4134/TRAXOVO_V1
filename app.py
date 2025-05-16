import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from utils import load_data, filter_assets, get_asset_by_id, get_asset_categories, get_asset_locations, get_asset_status
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fleet-management-default-key")

# Configure session timeout (30 minutes of inactivity)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# Configure database

# Import timecard processor
from utils.timecard_processor import load_timecard_data, generate_attendance_report
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Import database module
from db import db, init_app
init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

# Import models after db initialization to avoid circular imports
from models import User, Asset, AssetHistory, MaintenanceRecord, APIConfig, Geofence

# Import blueprints
from blueprints.reports import reports_bp  # noqa: E402

# Register blueprints
app.register_blueprint(reports_bp)

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    # Import the User model directly to avoid circular imports
    from models.models import User
    return User.query.get(int(user_id))

# Create initial admin users (will only be created if they don't exist)
def create_admin_users():
    """Create initial admin users if they don't exist"""
    # Define admin users
    admin_users = [
        {
            'username': 'admin',
            'email': 'admin@systemsmith.com',
            'password': 'SystemSmith2025!',
            'is_admin': True
        },
        {
            'username': 'manager',
            'email': 'manager@systemsmith.com',
            'password': 'FleetManager2025!',
            'is_admin': True
        },
        {
            'username': 'analyst',
            'email': 'analyst@systemsmith.com',
            'password': 'DataAnalyst2025!',
            'is_admin': False
        }
    ]
    
    # Check if users exist and create them if they don't
    with app.app_context():
        for user_data in admin_users:
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    is_admin=user_data['is_admin']
                )
                user.set_password(user_data['password'])
                db.session.add(user)
                logger.info(f"Created user: {user_data['username']}")
        
        db.session.commit()
        logger.info("Admin users setup complete")

# Import blueprints
from blueprints.parsers import parser_bp
try:
    from blueprints.kaizen import kaizen_bp
    from blueprints.map import map_bp, register_blueprint as register_map_blueprint
    from blueprints.utilization import utilization_bp, register_blueprint as register_utilization_blueprint
    from blueprints.maintenance import maintenance_bp, register_blueprint as register_maintenance_blueprint
    from blueprints.fuel import fuel_bp, register_blueprint as register_fuel_blueprint
    from blueprints.kpi import kpi_bp, register_blueprint as register_kpi_blueprint
    from blueprints.fringe import fringe_bp, register_blueprint as register_fringe_blueprint
    from blueprints.depreciation import depreciation_bp, register_blueprint as register_depreciation_blueprint
    from blueprints.bpp import bpp_bp, register_blueprint as register_bpp_blueprint
    from blueprints.billing import billing_bp, register_blueprint as register_billing_blueprint
    from blueprints.attendance import attendance_bp, register_blueprint as register_attendance_blueprint
    from routes.asset_drivers import asset_drivers_bp
    
    # Register blueprints
    app.register_blueprint(parser_bp)
    app.register_blueprint(kaizen_bp)
    app.register_blueprint(asset_drivers_bp)
    register_map_blueprint(app)
    register_utilization_blueprint(app)
    register_maintenance_blueprint(app)
    register_fuel_blueprint(app)
    register_kpi_blueprint(app)
    register_fringe_blueprint(app)
    register_depreciation_blueprint(app)
    register_bpp_blueprint(app)
    register_billing_blueprint(app)
    register_attendance_blueprint(app)
    logger.info("Registered application blueprints")
except ImportError as e:
    logger.warning(f"Could not register all blueprints: {e}")

# Initialize with app context
with app.app_context():
    try:
        create_admin_users()
    except Exception as e:
        logger.error(f"Error creating admin users: {e}")

# Login and logout routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if user and user.check_password(password):
            # Log in the user
            login_user(user, remember=remember)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Set session to permanent to apply timeout
            session.permanent = True
            
            # Redirect to the requested page or default to index
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(next_page)
        else:
            flash("Invalid username or password", "danger")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for('login'))

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
@login_required
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
@login_required
def asset_detail(asset_id):
    """Render the asset detail page"""
    asset = get_asset_by_id(assets_data, asset_id)
    
    if not asset:
        flash('Asset not found', 'danger')
        return redirect(url_for('index'))
    
    return render_template('asset_detail.html', asset=asset)

@app.route('/reports')
@login_required
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

@app.route('/report_dashboard')
@login_required
def report_dashboard():
    """Main reports dashboard"""
    # Get dates for default form values
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    current_month = datetime.now().strftime('%Y-%m')
    
    return render_template('reports_dashboard.html',
                          title="Reports Dashboard",
                          today=today,
                          yesterday=yesterday,
                          current_month=current_month,
                          attendance_reports=[],
                          billing_exports=[])
                          
@app.route('/generate_prior_day_report', methods=['POST'])
@login_required
def generate_prior_day_report():
    """Generate prior day attendance report"""
    date_str = request.form.get('date')
    
    if not date_str:
        flash('Please provide a valid date', 'danger')
        return redirect(url_for('report_dashboard'))
    
    flash(f'Prior day report for {date_str} would be processed here', 'info')
    return redirect(url_for('report_dashboard'))

@app.route('/generate_current_day_report', methods=['POST'])
@login_required
def generate_current_day_report():
    """Generate current day attendance report"""
    date_str = request.form.get('date')
    
    if not date_str:
        flash('Please provide a valid date', 'danger')
        return redirect(url_for('report_dashboard'))
    
    flash(f'Current day report for {date_str} would be processed here', 'info')
    return redirect(url_for('report_dashboard'))

@app.route('/generate_regional_billing', methods=['POST'])
@login_required
def generate_regional_billing():
    """Generate regional billing exports"""
    month_str = request.form.get('month')
    
    if not month_str:
        flash('Please provide a valid month', 'danger')
        return redirect(url_for('report_dashboard'))
    
    flash(f'Regional billing exports for {month_str} would be generated here', 'info')
    return redirect(url_for('report_dashboard'))

@app.route('/review_pm_allocations', methods=['POST'])
@login_required
def review_pm_allocations():
    """Review PM allocation changes"""
    month_str = request.form.get('month')
    
    if not month_str:
        flash('Please provide a valid month', 'danger')
        return redirect(url_for('report_dashboard'))
    
    flash(f'PM allocation review for {month_str} would be processed here', 'info')
    return redirect(url_for('report_dashboard'))

@app.route('/equipment_utilization')
@login_required
def equipment_utilization():
    """Equipment utilization report"""
    flash('Equipment utilization reports would be displayed here', 'info')
    return redirect(url_for('report_dashboard'))

@app.route('/maintenance_roi')
@login_required
def maintenance_roi():
    """Maintenance ROI report"""
    flash('Maintenance ROI analytics would be displayed here', 'info')
    return redirect(url_for('report_dashboard'))

@app.route('/gps_efficiency')
@login_required
def gps_efficiency():
    """GPS efficiency report"""
    flash('GPS efficiency analytics would be displayed here', 'info')
    return redirect(url_for('report_dashboard'))

@app.route('/attendance/trends')
@login_required
def attendance_trends():
    """Display attendance trends and analytics"""
    from models.attendance import Driver, JobSite, AttendanceRecord
    from utils.attendance_analytics import (
        get_trend_summary, 
        get_top_drivers_with_issues, 
        get_weekly_comparison_data, 
        get_attendance_by_job_site,
        get_attendance_trends
    )
    
    # Get filter parameters
    date_range = int(request.args.get('date_range', '30'))
    status_type = request.args.get('status_type', 'all')
    job_site_id = request.args.get('job_site', 'all')
    
    # Calculate date ranges for queries
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=date_range)
    
    # Get trend summary data
    trends = get_trend_summary()
    
    # Get chart data for attendance trends over time
    all_trends_data = {}
    for status in ['LATE_START', 'EARLY_END', 'NOT_ON_JOB']:
        trend_data = get_attendance_trends(
            start_date=datetime.now().date() - timedelta(days=7),
            end_date=datetime.now().date(),
            status_type=status
        )
        all_trends_data[status] = trend_data
    
    # Format trend data for chart
    trend_dates = all_trends_data['LATE_START']['dates'][-7:]  # Last 7 days
    chart_data = {
        'labels': [d.strftime('%b %d') if isinstance(d, datetime) else d.strftime('%b %d') for d in trend_dates],
        'late_start': all_trends_data['LATE_START']['counts'][-7:],
        'early_end': all_trends_data['EARLY_END']['counts'][-7:],
        'not_on_job': all_trends_data['NOT_ON_JOB']['counts'][-7:]
    }
    
    # Get weekly comparison data
    weekly_comparison = get_weekly_comparison_data('LATE_START', weeks=4)
    
    # Get top drivers with attendance issues
    selected_status = status_type if status_type != 'all' else 'LATE_START'
    top_drivers = get_top_drivers_with_issues(start_date, end_date, selected_status, limit=10)
    
    # Get attendance by job site
    job_site_data = get_attendance_by_job_site(start_date, end_date, limit=5)
    
    # Get total drivers count for percentage calculations
    total_drivers = Driver.query.filter_by(is_active=True).count() or 1
    
    # Get job sites for filter
    job_sites = JobSite.query.filter_by(is_active=True).order_by(JobSite.name).all()
    
    return render_template('reports/trends.html',
                          title="Attendance Trends",
                          trends=trends,
                          chart_data=chart_data,
                          weekly_comparison=weekly_comparison,
                          top_drivers=top_drivers,
                          job_site_data=job_site_data,
                          total_drivers=total_drivers,
                          job_sites=job_sites,
                          date_range=date_range,
                          status_type=status_type,
                          job_site=job_site_id,
                          last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/download_report/<path:report_path>')
@login_required
def download_report(report_path):
    """Download a report file"""
    flash('Report download would be processed here', 'info')
    return redirect(url_for('report_dashboard'))

@app.route('/download_export/<path:export_path>')
@login_required
def download_export(export_path):
    """Download an export file"""
    flash('Export download would be processed here', 'info')
    return redirect(url_for('report_dashboard'))

@app.route('/reports/maintenance')
@login_required
def maintenance_reports():
    """Render the maintenance analytics and ROI reports page"""
    from utils.maintenance_analytics import process_work_order_report, analyze_equipment_roi
    import os
    from pathlib import Path
    
    # Look for work order and utilization reports in attached assets
    wo_report_path = None
    utilization_path = None
    
    for file_path in Path('attached_assets').glob('*'):
        file_name = file_path.name.lower()
        if 'wo' in file_name or 'work order' in file_name:
            wo_report_path = str(file_path)
        elif 'util' in file_name or 'hour' in file_name:
            utilization_path = str(file_path)
    
    # Process data if files are found
    maintenance_data = None
    roi_data = None
    error_message = None
    
    try:
        if wo_report_path and os.path.exists(wo_report_path):
            # Process work order report
            maintenance_data = process_work_order_report(wo_report_path)
            
            # Process utilization data if available
            utilization_data = None
            if utilization_path and os.path.exists(utilization_path):
                # TODO: Implement utilization data processing
                pass
            
            # Analyze ROI
            roi_data = analyze_equipment_roi(maintenance_data=maintenance_data, utilization_data=utilization_data)
        else:
            error_message = "No work order report found. Please upload a report file."
    except Exception as e:
        logger.error(f"Error processing maintenance data: {e}")
        error_message = f"Error processing maintenance data: {str(e)}"
    
    # Format last updated time
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return render_template('maintenance_reports.html',
                          maintenance_data=maintenance_data,
                          roi_data=roi_data,
                          error_message=error_message,
                          last_updated=last_updated)

@app.route('/api/assets')
@login_required
def api_assets():
    """API endpoint to get asset data in JSON format"""
    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')
    location = request.args.get('location', 'all')
    
    filtered_assets = filter_assets(assets_data, status, category, location)
    return jsonify(filtered_assets)

@app.route('/api/asset/<asset_id>')
@login_required
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
@login_required
def admin_settings():
    """Admin settings page for API configuration"""
    # Only allow admin users to access this page
    if not current_user.is_admin:
        flash('You do not have permission to access admin settings', 'danger')
        return redirect(url_for('index'))
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
    
    # Update database configuration if using it
    try:
        from models import APIConfig
        
        # Store in database for persistence
        APIConfig.set('GAUGE_API_URL', gauge_api_url)
        APIConfig.set('GAUGE_API_KEY', gauge_api_key, is_secret=True)
        APIConfig.set('GAUGE_API_USER', gauge_api_user)
        if gauge_api_password:
            APIConfig.set('GAUGE_API_PASSWORD', gauge_api_password, is_secret=True)
        APIConfig.set('ENABLE_AUTO_UPDATES', str(enable_auto_updates).lower())
        APIConfig.set('MORNING_UPDATE_TIME', morning_update)
        APIConfig.set('MIDDAY_UPDATE_TIME', midday_update)
        APIConfig.set('EVENING_UPDATE_TIME', evening_update)
        
        flash('Settings updated successfully and saved to database', 'success')
    except Exception as e:
        # If database storage fails, still use environment variables
        logger.warning(f"Could not store settings in database: {e}")
        flash('Settings updated successfully (in memory only)', 'warning')
    
    # Restart the scheduler with new settings
    try:
        import schedule
        schedule.clear()  # Clear all jobs
        from scheduler import start_scheduler_thread
        start_scheduler_thread()  # Restart with new settings
        flash('Scheduler restarted with new settings', 'success')
    except Exception as e:
        logger.error(f"Error restarting scheduler: {e}")
        flash(f"Error restarting scheduler: {e}", "danger")
    
    return redirect(url_for('admin_settings'))

@app.route('/admin/update_data')
def manual_update():
    """Manually update data from API"""
    try:
        # Clear cached data
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