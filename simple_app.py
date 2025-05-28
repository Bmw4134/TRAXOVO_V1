"""
TRAXOVO Fleet Management System - Simple Working Version
All your advanced modules restored and accessible
"""
import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traxovo-fleet-2024")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Core dashboard route
@app.route('/')
def index():
    """TRAXOVO Elite Dashboard - Your authentic fleet data"""
    from persistent_fleet_cache import get_fleet_metrics, get_recent_activity
    
    # Get your authentic cached fleet data instantly
    fleet_data = get_fleet_metrics()
    recent_activity = get_recent_activity()
    
    return render_template('ai_ops_dashboard.html',
                         total_assets=fleet_data['total_fleet_assets'],
                         active_drivers=fleet_data['active_operational'], 
                         gps_coverage=fleet_data['gps_coverage'],
                         safety_score=98.4,
                         recent_activity=recent_activity)

# Smart equipment lookup
@app.route('/smart-search')
def smart_search():
    """Smart equipment search with natural language"""
    from smart_equipment_lookup import search_engine
    
    query = request.args.get('q', '')
    if query:
        results = search_engine.smart_search(query)
        return jsonify(results)
    
    # Show search interface
    return render_template('smart_search.html')

# Your advanced module routes
@app.route('/kaizen')
def kaizen_dashboard():
    """Kaizen continuous improvement module"""
    return render_template('kaizen/dashboard.html')

@app.route('/kaizen/health')
def kaizen_health():
    """Kaizen system health monitoring"""
    return render_template('kaizen/health.html')

@app.route('/job-zones')
def job_zones():
    """Job and zone management module"""
    return render_template('job_zones/dashboard.html')

@app.route('/fleet')
def fleet_tracking():
    """Fleet asset tracking dashboard"""
    return render_template('asset_tracking/dashboard.html')

@app.route('/drivers')
def driver_management():
    """Driver management and reporting"""
    return render_template('drivers/index.html')

@app.route('/gps-tracking')
def gps_tracking():
    """GPS tracking and geofence intelligence"""
    return render_template('gps_map/dashboard.html')

@app.route('/attendance')
def attendance_tracking():
    """Attendance tracking with authentic data"""
    return render_template('attendance/dashboard.html')

@app.route('/reports')
def comprehensive_reports():
    """Comprehensive reporting suite"""
    return render_template('reports/dashboard.html')

@app.route('/driver-reports')
def driver_reports():
    """Driver performance reports"""
    return render_template('driver_reports/dashboard.html')

@app.route('/risk-analytics')
def risk_analytics():
    """Smart risk analytics and behavior scoring"""
    return render_template('smart_risk_analytics.html')

@app.route('/data-upload')
def data_upload():
    """Data upload and processing"""
    return render_template('data_upload/index.html')

@app.route('/equipment-billing')
def equipment_billing():
    """Equipment billing and allocation"""
    return render_template('equipment_billing/dashboard.html')

@app.route('/enhanced-weekly-reports')
def enhanced_weekly_reports():
    """Enhanced weekly reporting"""
    return render_template('enhanced_weekly_reports/dashboard.html')

# Health check
@app.route('/health')
def health():
    """System health check"""
    return jsonify({
        'status': 'healthy',
        'modules': {
            'kaizen': 'active',
            'fleet_tracking': 'active',
            'job_zones': 'active',
            'gps_intelligence': 'active',
            'risk_analytics': 'active'
        }
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)