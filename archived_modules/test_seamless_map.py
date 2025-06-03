"""
Test the seamless fleet map with authentic GAUGE data
"""

from flask import Flask, render_template, jsonify
from seamless_fleet_engine import seamless_fleet_engine

app = Flask(__name__)

@app.route('/')
def test_fleet_map():
    """Test seamless fleet map with authentic data"""
    try:
        categories = seamless_fleet_engine.get_category_filters()
        status_summary = seamless_fleet_engine.get_status_summary()
        assets = seamless_fleet_engine.get_all_assets_for_map()
        
        print(f"Loaded {len(assets)} authentic assets from GAUGE API")
        print(f"Categories: {[c['name'] for c in categories]}")
        print(f"Status summary: {status_summary}")
        
        return render_template('seamless_fleet_map.html', 
                             categories=categories,
                             status_summary=status_summary)
    except Exception as e:
        print(f"Error: {e}")
        return f"Error loading fleet map: {e}"

@app.route('/api/fleet/assets')
def api_fleet_assets():
    """API endpoint for all fleet assets"""
    try:
        assets = seamless_fleet_engine.get_all_assets_for_map()
        return jsonify({
            'status': 'success',
            'assets': assets,
            'count': len(assets),
            'timestamp': '2025-05-31T07:24:00Z'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'assets': [],
            'count': 0
        }), 500

@app.route('/api/fleet/categories')
def api_fleet_categories():
    """API endpoint for available categories"""
    try:
        categories = seamless_fleet_engine.get_category_filters()
        return jsonify({
            'status': 'success',
            'categories': categories
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'categories': []
        }), 500

@app.route('/api/fleet/search')
def api_fleet_search():
    """API endpoint for asset search"""
    from flask import request
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify({'results': []})
        
        results = seamless_fleet_engine.search_assets(query)
        return jsonify({
            'status': 'success',
            'results': results,
            'query': query
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'results': [],
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)