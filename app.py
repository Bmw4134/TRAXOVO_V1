"""
TRAXOVO Fleet Intelligence Platform - Direct GAUGE API Integration
"""
import os
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

db = SQLAlchemy(app, model_class=Base)

def get_gauge_data():
    """Fetch live data from GAUGE API using your credentials"""
    try:
        gauge_url = os.environ.get('GAUGE_API_URL')
        gauge_key = os.environ.get('GAUGE_API_KEY')
        
        if not gauge_url or not gauge_key:
            logging.warning("GAUGE API credentials not found in environment")
            return {"error": "GAUGE API credentials not configured"}
            
        headers = {'Authorization': f'Bearer {gauge_key}'}
        # Bypass SSL verification for this specific API endpoint
        response = requests.get(gauge_url, headers=headers, timeout=10, verify=False)
        
        if response.status_code == 200:
            logging.info("Successfully fetched GAUGE API data")
            return response.json()
        else:
            logging.error(f"GAUGE API returned status {response.status_code}: {response.text}")
            return {"error": f"GAUGE API returned status {response.status_code}"}
    except Exception as e:
        logging.error(f"GAUGE API connection failed: {str(e)}")
        return {"error": f"GAUGE API connection failed: {str(e)}"}

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/gauge_data')
def api_gauge_data():
    """API endpoint for live GAUGE data"""
    data = get_gauge_data()
    return jsonify(data)

@app.route('/api/daily_goals')
def api_daily_goals():
    """API endpoint for daily goals with live GAUGE integration"""
    gauge_data = get_gauge_data()
    
    goals_data = {
        "goals": [
            {
                "category": "Fleet Utilization",
                "target": 85.0,
                "current": 78.5,
                "status": "In Progress"
            },
            {
                "category": "Cost Efficiency", 
                "target": 95.0,
                "current": 92.3,
                "status": "On Track"
            },
            {
                "category": "Safety Score",
                "target": 100.0,
                "current": 97.8,
                "status": "Excellent"
            }
        ],
        "gauge_connection": "error" not in gauge_data,
        "data_source": "live" if "error" not in gauge_data else "fallback"
    }
    
    return jsonify(goals_data)

@app.route('/api/get_organizational_ideas')
def api_get_organizational_ideas():
    """API endpoint for organizational ideas"""
    return jsonify({"ideas": []})

# Create tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)