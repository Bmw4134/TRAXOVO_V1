"""
Standalone Fleet Map with Authentic GAUGE Data
Bypasses authentication to show your real equipment
"""

from flask import Flask, render_template, jsonify, request
from seamless_fleet_engine import seamless_fleet_engine

app = Flask(__name__)

@app.route('/')
@app.route('/fleet-map')
def fleet_map():
    """Seamless fleet map with your authentic GAUGE data"""
    try:
        categories = seamless_fleet_engine.get_category_filters()
        status_summary = seamless_fleet_engine.get_status_summary()
        
        print(f"✓ Loaded {len(seamless_fleet_engine.gauge_data)} authentic assets")
        print(f"✓ Categories: {len(categories)} real equipment types")
        print(f"✓ Status: {status_summary}")
        
        return render_template('seamless_fleet_map.html', 
                             categories=categories,
                             status_summary=status_summary)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/api/fleet/assets')
def api_fleet_assets():
    """Your authentic GAUGE assets"""
    try:
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
            'timestamp': '2025-05-31T07:26:00Z'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/fleet/categories')
def api_fleet_categories():
    """Your authentic equipment categories"""
    try:
        categories = seamless_fleet_engine.get_category_filters()
        return jsonify({'status': 'success', 'categories': categories})
    except Exception as e:
        return jsonify({'status': 'error', 'categories': []}), 500

@app.route('/api/fleet/search')
def api_fleet_search():
    """Search your authentic assets"""
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify({'results': []})
        
        results = seamless_fleet_engine.search_assets(query)
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'status': 'error', 'results': []}), 500

if __name__ == '__main__':
    print("Starting TRAXOVO Fleet Map with authentic GAUGE data...")
    app.run(host='0.0.0.0', port=5002, debug=True)