"""
TRAXOVO Core Application - Complete Flask Implementation
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traxovo-enterprise-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

@app.route('/validation')
def visual_validation():
    """Visual validation dashboard for authentic RAGLE INC data"""
    return render_template('visual_validation.html')

@app.route('/api/ragle-daily-hours')
def api_ragle_daily_hours():
    """API endpoint for RAGLE daily hours and quantities data"""
    try:
        from ragle_daily_hours_processor import RagleDailyHoursProcessor
        processor = RagleDailyHoursProcessor()
        
        # Load and process data
        success = processor.load_daily_hours_data()
        
        if success:
            return jsonify({
                "status": "success",
                "data": processor.get_summary_report(),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to load RAGLE daily hours data",
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logging.error(f"Error in RAGLE daily hours API: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500