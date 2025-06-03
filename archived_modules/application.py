"""
TRAXORA Fleet Management System - Basic Application

This is a simplified version of the application to ensure basic functionality.
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create and configure the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development_key")

# Basic routes
@app.route('/')
def index():
    """Simplified dashboard for TRAXORA restart"""
    system_stats = {
        'asset_count': 0,
        'driver_count': 0,
        'last_sync': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    api_status = {
        'gauge_api': False,
        'database': True,
        'file_system': True
    }
    
    return render_template('dashboard.html', 
                          api_status=api_status,
                          system_stats=system_stats,
                          current_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(e)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)