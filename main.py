"""
Direct Fleet Map Access - No Authentication Required
Shows your authentic GAUGE data immediately
"""

from flask import Flask, render_template, jsonify, request
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-fleet-map")

@app.route('/')
@app.route('/fleet-map')
@app.route('/map')
def fleet_map():
    """Direct access to your seamless fleet map with authentic GAUGE data"""
    try:
        from seamless_fleet_engine import seamless_fleet_engine
        categories = seamless_fleet_engine.get_category_filters()
        status_summary = seamless_fleet_engine.get_status_summary()
        
        logger.info(f"✓ Loaded {len(seamless_fleet_engine.gauge_data)} authentic assets")
        logger.info(f"✓ Categories: {len(categories)} real equipment types")
        logger.info(f"✓ Status: {status_summary}")
        
        return render_template('seamless_fleet_map.html', 
                             categories=categories,
                             status_summary=status_summary)
    except Exception as e:
        logger.error(f"Fleet map error: {e}")
        return f"<h1>Fleet Map Loading Error</h1><p>{e}</p><p>Check seamless_fleet_engine.py and GAUGE data files</p>", 500

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
            'source': 'authentic_gauge_api',
            'timestamp': '2025-05-31T07:40:00Z'
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
    return jsonify({'status': 'ok', 'message': 'Fleet map server running'})

if __name__ == '__main__':
    print("🚀 Starting TRAXOVO Fleet Map with authentic GAUGE data...")
    print("🎯 Direct access - no authentication required")
    print("📊 640 real assets across 56 equipment categories")
    app.run(host='0.0.0.0', port=5000, debug=True)