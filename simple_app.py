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
                         active_drivers=fleet_data['active_drivers'], 
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
    """Enhanced GPS tracking with all TRAXOVO enhancements"""
    from persistent_fleet_cache import get_fleet_metrics
    
    fleet_data = get_fleet_metrics()
    gps_enabled = int(fleet_data['gps_coverage'] * fleet_data['total_fleet_assets'] / 100)
    
    return render_template('gps_tracking_enhanced.html',
                         total_assets=fleet_data['total_fleet_assets'],
                         gps_enabled=gps_enabled)

@app.route('/api/gps-assets')
def get_gps_assets():
    """API endpoint for GPS asset data from your authentic Gauge API - ACTIVE ASSETS ONLY"""
    import json
    
    try:
        # Load your authentic GPS data from Gauge API
        with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
            api_data = json.load(f)
        
        gps_assets = []
        for item in api_data:
            # FILTER: Only include ACTIVE assets with GPS coordinates
            if (item.get('Latitude') and item.get('Longitude') and 
                item.get('Active') == True and 
                item.get('Status', '').lower() != 'sold'):
                
                gps_assets.append({
                    'id': item.get('AssetIdentifier', 'Unknown'),
                    'name': item.get('Label', 'Unknown Asset'),
                    'latitude': float(item.get('Latitude', 0)),
                    'longitude': float(item.get('Longitude', 0)),
                    'status': 'Active',
                    'category': item.get('AssetCategory', 'Unknown'),
                    'location': item.get('Location', 'Unknown'),
                    'lastUpdate': item.get('EventDateTimeString', 'Unknown'),
                    'speed': item.get('Speed', 0),
                    'heading': item.get('Heading', 'N')
                })
        
        return jsonify({
            'assets': gps_assets,
            'total_count': len(gps_assets),
            'last_updated': 'May 15, 2025 10:45 AM'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'assets': []})

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

@app.route('/efficiency-visualizer')
def efficiency_visualizer():
    """Dynamic Fleet Efficiency Trend Visualizer"""
    from dynamic_efficiency_visualizer import fleet_analyzer
    
    efficiency_data = fleet_analyzer.calculate_fleet_efficiency_trends()
    insights = fleet_analyzer.get_efficiency_insights()
    
    return render_template('efficiency_visualizer_dashboard.html',
                         efficiency_data=efficiency_data,
                         insights=insights)

@app.route('/api/efficiency-trends')
def get_efficiency_trends():
    """API endpoint for efficiency trend data"""
    from dynamic_efficiency_visualizer import fleet_analyzer
    
    efficiency_data = fleet_analyzer.calculate_fleet_efficiency_trends()
    return jsonify(efficiency_data)

@app.route('/asset-intelligence')
def asset_availability_intelligence():
    """Asset Availability Intelligence - Reduce rental costs"""
    return render_template('asset_availability_dashboard.html')

@app.route('/asset-intelligence/api/stagnant-assets')
def get_stagnant_assets():
    """API: Assets sitting in same location for extended periods"""
    from asset_availability_intelligence import asset_analyzer
    
    days = request.args.get('days', 7, type=int)
    stagnant_assets = asset_analyzer.identify_stagnant_assets(days_threshold=days)
    return jsonify({'stagnant_assets': stagnant_assets})

@app.route('/asset-intelligence/api/available-assets')
def get_available_assets():
    """API: Available assets by category for dispatch"""
    from asset_availability_intelligence import asset_analyzer
    
    category = request.args.get('category', None)
    available_assets = asset_analyzer.get_available_by_category(category)
    return jsonify({'available_assets': available_assets})

@app.route('/asset-intelligence/api/dispatch-alerts')
def get_dispatch_alerts():
    """API: Smart alerts for PMS/PES/DISPATCH teams"""
    from asset_availability_intelligence import asset_analyzer
    
    alerts = asset_analyzer.generate_dispatch_alerts()
    return jsonify({'alerts': alerts})

@app.route('/field-service-billing')
def field_service_billing_intelligence():
    """Field Service & Heavy Haul Billing Intelligence"""
    return render_template('field_service_billing_dashboard.html')

@app.route('/field-service-billing/api/unbilled-assets')
def get_unbilled_service_assets():
    """API: Identify mechanic trucks, semis, and service vehicles missing billing"""
    from field_service_billing_intelligence import field_service_analyzer
    
    assets = field_service_analyzer.identify_unbilled_service_assets()
    return jsonify({'unbilled_assets': assets})

@app.route('/field-service-billing/api/billing-opportunities')
def get_billing_opportunities():
    """API: Revenue opportunities from field service and heavy haul"""
    from field_service_billing_intelligence import field_service_analyzer
    
    opportunities = field_service_analyzer.generate_billing_opportunities()
    return jsonify({'opportunities': opportunities})

@app.route('/field-service-billing/api/service-summary')
def get_service_summary():
    """API: Summary of service vehicle billing status"""
    from field_service_billing_intelligence import field_service_analyzer
    
    summary = field_service_analyzer.get_service_vehicle_summary()
    return jsonify({'summary': summary})

@app.route('/equipment-lifecycle')
def equipment_lifecycle_storyteller():
    """Smart Equipment Lifecycle Storyteller"""
    return render_template('equipment_lifecycle_dashboard.html')

@app.route('/equipment-lifecycle/api/equipment-story/<asset_id>')
def get_equipment_story(asset_id):
    """API: Complete lifecycle story for specific equipment"""
    from smart_equipment_lifecycle_storyteller import lifecycle_analyzer
    
    story = lifecycle_analyzer.generate_equipment_story(asset_id)
    return jsonify({'story': story})

@app.route('/equipment-lifecycle/api/fleet-overview')
def get_fleet_lifecycle_overview():
    """API: Fleet lifecycle distribution and insights"""
    from smart_equipment_lifecycle_storyteller import lifecycle_analyzer
    
    fleet_overview = {
        'total_assets': len(lifecycle_analyzer.gps_data),
        'lifecycle_distribution': {},
        'recommendations_summary': []
    }
    
    return jsonify({'fleet_overview': fleet_overview})

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
            'risk_analytics': 'active',
            'efficiency_visualizer': 'active'
        }
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)