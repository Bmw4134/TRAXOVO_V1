"""
TRAXOVO Fleet Management System - Fixed Authentication
Main Application with Working Login System
"""

import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traxovo-fleet-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Simple session-based authentication
@app.before_request
def check_authentication():
    """Check if user is authenticated for protected routes"""
    # Skip auth check for login routes and assets
    if request.endpoint in ['login', 'simple_login', 'static'] or request.path.startswith('/api/'):
        return
    
    # Check if user is authenticated
    if not session.get('authenticated'):
        if request.path == '/':
            return redirect(url_for('login'))
        else:
            return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate credentials
        if (username == 'tester' and password == 'tester') or (username == 'watson' and password == 'watson'):
            session['authenticated'] = True
            session['username'] = username
            session.permanent = True
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for('dashboard'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('login.html', error="Invalid credentials. Use tester/tester or watson/watson")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/fleet-map')
@app.route('/map')
def fleet_map():
    """Fleet map with authentic GAUGE data"""
    try:
        from seamless_fleet_engine import seamless_fleet_engine
        categories = seamless_fleet_engine.get_category_filters()
        status_summary = seamless_fleet_engine.get_status_summary()
        
        logger.info(f"✓ Loaded {len(seamless_fleet_engine.gauge_data)} authentic assets")
        
        return render_template('seamless_fleet_map.html', 
                             categories=categories,
                             status_summary=status_summary,
                             username=session.get('username'))
    except Exception as e:
        logger.error(f"Fleet map error: {e}")
        return f"Fleet map error: {e}", 500

# API endpoints for fleet data
@app.route('/api/fleet/assets')
def api_fleet_assets():
    """Your authentic GAUGE assets API"""
    try:
        from seamless_fleet_engine import seamless_fleet_engine
        category_filter = request.args.get('category', 'all')
        assets = seamless_fleet_engine.get_all_assets_for_map()
        
        if category_filter != 'all':
            categories = seamless_fleet_engine.get_category_filters()
            category_obj = next((c for c in categories if c['id'] == category_filter), None)
            if category_obj and category_obj.get('category'):
                assets = [a for a in assets if a['category'] == category_obj['category']]
        
        return jsonify({
            'status': 'success',
            'assets': assets,
            'count': len(assets),
            'source': 'authentic_gauge_api'
        })
    except Exception as e:
        logger.error(f"Assets API error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/fleet/categories')
def api_fleet_categories():
    """Your authentic equipment categories API"""
    try:
        from seamless_fleet_engine import seamless_fleet_engine
        categories = seamless_fleet_engine.get_category_filters()
        return jsonify({'status': 'success', 'categories': categories})
    except Exception as e:
        logger.error(f"Categories API error: {e}")
        return jsonify({'status': 'error', 'categories': []}), 500

@app.route('/api/fleet/search')
def api_fleet_search():
    """Search your authentic assets API"""
    try:
        from seamless_fleet_engine import seamless_fleet_engine
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify({'results': []})
        
        results = seamless_fleet_engine.search_assets(query)
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        logger.error(f"Search API error: {e}")
        return jsonify({'status': 'error', 'results': []}), 500

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'authenticated': session.get('authenticated', False)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)