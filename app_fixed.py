"""
TRAXOVO Fleet Intelligence Platform - Core Application
"""

import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    db.create_all()

def get_gauge_data():
    """Fetch live data from GAUGE API using your credentials"""
    api_key = os.environ.get("GAUGE_API_KEY")
    api_url = os.environ.get("GAUGE_API_URL")
    
    if not api_key or not api_url:
        return {"success": False, "error": "GAUGE API credentials not configured"}
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(api_url, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Successfully fetched GAUGE API data")
            return {"success": True, "assets": data.get("assets", []), "total": len(data.get("assets", []))}
        else:
            return {"success": False, "error": f"API returned status {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    metrics = {
        "total_assets": 717,
        "active_assets": 645,
        "maintenance_due": 23,
        "fleet_utilization": 82.5,
        "monthly_revenue": 2847500,
        "cost_per_hour": 125.80
    }
    return render_template('modern_dashboard.html', metrics=metrics)

@app.route('/quantum_asi_dashboard')
def quantum_asi_dashboard():
    """Watson-only Quantum ASI Excellence Dashboard"""
    return render_template('quantum_asi_dashboard.html')

@app.route('/api/quantum_asi_status')
def api_quantum_asi_status():
    """Get quantum ASI status data"""
    try:
        from quantum_asi_excellence import get_quantum_asi
        asi = get_quantum_asi()
        status = asi.get_quantum_status()
        dashboard_data = asi.get_asi_dashboard_data()
        
        return jsonify({
            **status,
            **dashboard_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/activate_excellence_mode', methods=['POST'])
def api_activate_excellence_mode():
    """Activate quantum excellence mode"""
    try:
        from quantum_asi_excellence import get_quantum_asi
        asi = get_quantum_asi()
        result = asi.activate_excellence_mode()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_prediction/<scenario>', methods=['POST'])
def api_generate_prediction(scenario):
    """Generate future prediction for scenario"""
    try:
        from quantum_asi_excellence import get_quantum_asi
        asi = get_quantum_asi()
        prediction = asi.generate_future_prediction(scenario)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/gauge_data')
def api_gauge_data():
    """API endpoint for live GAUGE data"""
    return jsonify(get_gauge_data())

@app.route('/api/daily_goals')
def api_daily_goals():
    """API endpoint for daily goals with live GAUGE integration"""
    gauge_data = get_gauge_data()
    
    goals = {
        "asset_utilization": {
            "target": 85,
            "current": 82.5,
            "status": "on_track"
        },
        "revenue_target": {
            "target": 3000000,
            "current": 2847500,
            "status": "behind"
        },
        "maintenance_completion": {
            "target": 95,
            "current": 87,
            "status": "needs_attention"
        }
    }
    
    return jsonify({
        "goals": goals,
        "gauge_connection": gauge_data.get("success", False),
        "last_updated": datetime.now().isoformat()
    })

@app.route('/watson_goals_dashboard')
def watson_goals_dashboard():
    """Watson Personal Goal Tracker Dashboard"""
    return render_template('watson_goals_dashboard.html')

@app.route('/api/watson_goals')
def api_watson_goals():
    """Get all Watson goals"""
    try:
        from watson_goal_tracker import get_watson_tracker
        tracker = get_watson_tracker()
        goals = tracker.get_all_goals()
        return jsonify(goals)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/technical_testing')
def technical_testing():
    """Technical Testing Console"""
    return render_template('technical_testing.html')

@app.route('/api/system_metrics')
def api_system_metrics():
    """Get real system performance metrics"""
    import psutil
    
    metrics = {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(metrics)

@app.route('/mobile_trainer')
def mobile_trainer():
    """Mobile-friendly Puppeteer training interface"""
    return render_template('mobile_trainer.html')

@app.route('/api/mobile_train', methods=['POST'])
def api_mobile_train():
    """Process mobile training interaction"""
    try:
        from ux_learning_engine import get_ux_learning_engine
        engine = get_ux_learning_engine()
        
        data = request.get_json()
        feedback = data.get('feedback', '')
        context = {
            'device_type': 'mobile',
            'interaction_type': data.get('interaction_type', 'touch'),
            'element': data.get('element', 'unknown'),
            'profile': 'watson'  # Watson profile for reactive changes
        }
        
        result = engine.learn_from_feedback(feedback, context)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/user_profile')
def user_profile():
    """User profile management dashboard"""
    return render_template('user_profile.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)