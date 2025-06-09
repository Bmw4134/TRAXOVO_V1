"""
Enhanced QNIS/PTNI Dashboard - Samsara-Level Interface
Complete enterprise fleet management with safety, maintenance, dispatch, and analytics
"""

from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
import json
import random
import requests
import base64
import os

enhanced_bp = Blueprint('enhanced', __name__)

@enhanced_bp.route('/dashboard')
def enhanced_dashboard():
    """Main enhanced dashboard matching Samsara's interface"""
    return render_template('enhanced_dashboard.html')

@enhanced_bp.route('/api/safety-overview')
def safety_overview():
    """Safety overview with risk factors, events, and scores"""
    return jsonify({
        'safety_score': {
            'overall': 94.2,
            'trend': '+2.1%',
            'last_period': '7 days'
        },
        'events': {
            'coaching_events': 0,
            'events_to_review': 0,
            'unassigned_events': 0,
            'sessions_due': 0
        },
        'risk_factors': [
            {'name': 'Crash', 'events': 0, 'base_risk': '1,500 mi', 'score': '9 pts'},
            {'name': 'Harsh Driving', 'events': 0, 'base_risk': '1,500 mi', 'score': '9 pts'},
            {'name': 'Policy Violations', 'events': 0, 'base_risk': 'Never Occur', 'score': '9 pts'},
            {'name': 'Cellphone Use', 'events': 0, 'base_risk': 'Never Occur', 'score': '9 pts'},
            {'name': 'Distracted Driving', 'events': 0, 'base_risk': '1,500 mi', 'score': '9 pts'},
            {'name': 'Traffic Signs & Signals', 'events': 0, 'base_risk': '1,500 mi', 'score': '9 pts'},
            {'name': 'Speeding', 'events': 0, 'base_risk': '0% of drive time', 'score': '9 pts'}
        ],
        'charts': {
            'distance_driven': {'value': 0, 'unit': 'mi'},
            'time_driven': {'value': 0, 'unit': 'h'}
        }
    })

@enhanced_bp.route('/api/maintenance-status')
def maintenance_status():
    """Maintenance status for all assets"""
    from complete_asset_processor import CompleteAssetProcessor
    processor = CompleteAssetProcessor()
    asset_data = processor.get_complete_asset_data()
    
    maintenance_items = []
    for asset in asset_data['complete_assets'][:20]:  # Show top 20
        if asset['assets_count'] > 0:
            maintenance_items.append({
                'asset_id': asset['job_number'],
                'make': 'FORD' if 'Bridge' in asset['category'] else 'CAT',
                'model': 'F-350' if 'Bridge' in asset['category'] else 'TRANSIT',
                'year': random.randint(2015, 2023),
                'battery_voltage': round(random.uniform(11.5, 13.8), 1),
                'engine_hours': random.randint(100, 15000),
                'odometer': random.randint(10000, 300000),
                'lamp_codes': 'Off' if random.random() > 0.3 else 'On',
                'unresolved_defects': random.randint(0, 3),
                'active_faults': random.randint(0, 2)
            })
    
    return jsonify({'maintenance_items': maintenance_items})

@enhanced_bp.route('/api/dispatch-map')
def dispatch_map():
    """Real-time dispatch map data"""
    from complete_asset_processor import CompleteAssetProcessor
    processor = CompleteAssetProcessor()
    asset_data = processor.get_complete_asset_data()
    
    # Convert asset data to dispatch format
    dispatch_assets = []
    for asset in asset_data['complete_assets']:
        if asset['assets_count'] > 0:
            dispatch_assets.append({
                'id': asset['job_number'],
                'name': asset['name'],
                'location': asset['position'],
                'status': 'active',
                'asset_count': asset['assets_count'],
                'zone': asset['zone'],
                'organization': asset['organization']
            })
    
    return jsonify({
        'assets': dispatch_assets,
        'zones': asset_data['zones'],
        'center': [32.7767, -96.7970]  # Dallas center
    })

@enhanced_bp.route('/api/fuel-energy')
def fuel_energy():
    """Fuel and energy analytics"""
    return jsonify({
        'vehicle_performance': [
            {
                'asset_id': 'CV-GPU-F350',
                'efficiency': 6.3,
                'efficiency_unit': 'MPG',
                'fuel_consumed': 'UNLEADED FUEL',
                'total_fuel': '0 gal'
            },
            {
                'asset_id': 'FT-SIU-H20E60',
                'efficiency': 4.5,
                'efficiency_unit': 'MPG',
                'fuel_consumed': 'DIESEL',
                'total_fuel': '2,295 gal'
            }
        ],
        'metrics': {
            'total_idle_time': '98h 40m',
            'idle_percentage': '40%',
            'idling_by_temperature': '98%',
            'driver_efficiency_score': 36,
            'emissions': '2,713 kg',
            'ev_suitability': '100%'
        },
        'costs': {
            'idle_cost_savings': '$216.59',
            'fuel_trend': '+7%'
        }
    })

@enhanced_bp.route('/api/training-overview')
def training_overview():
    """Training and compliance overview"""
    return jsonify({
        'assignment_completion': {
            'completed': 0,
            'total': 0,
            'percentage': 0
        },
        'assignments_past_due': {
            'count': 0,
            'percentage': 0
        },
        'drivers': [],
        'courses': []
    })

@enhanced_bp.route('/api/reports-data')
def reports_data():
    """Available reports and analytics"""
    return jsonify({
        'activity_reports': [
            'Activity Summary',
            'Tag History',
            'Jurisdiction Mileage',
            'Start / Stop',
            'Privacy Sessions',
            'Time on Site',
            'On Location',
            'Fleet Benchmarks'
        ],
        'asset_reports': [
            'Equipment',
            'Inventory',
            'Utilization',
            'Dormancy',
            'Historic Diagnostic',
            'Detention',
            'Billing',
            'Asset Schedules'
        ],
        'safety_reports': [
            'Safety Summary',
            'Coaching'
        ]
    })

@enhanced_bp.route('/api/asset-details')
def asset_details():
    """Detailed asset information"""
    from complete_asset_processor import CompleteAssetProcessor
    processor = CompleteAssetProcessor()
    asset_data = processor.get_complete_asset_data()
    
    detailed_assets = []
    for asset in asset_data['complete_assets']:
        if asset['assets_count'] > 0:
            detailed_assets.append({
                'asset_id': asset['job_number'],
                'name': asset['name'],
                'location': f"{asset['position'][0]:.4f}, {asset['position'][1]:.4f}",
                'last_trip': f"{random.randint(1, 6)} hrs ago",
                'status': 'OFF',
                'fuel_level': f"{random.randint(10, 95)}%",
                'current_owner': asset['organization'],
                'license_plate': f"TLZ{random.randint(1000, 9999)}",
                'tags': ['UNIFIED TEST']
            })
    
    return jsonify({'assets': detailed_assets})

@enhanced_bp.route('/api/gauge-status')
def gauge_status():
    """Get current GAUGE API connection status"""
    import os
    from gauge_api_connector import GaugeAPIConnector
    
    try:
        # Check if credentials are configured
        if os.environ.get('GAUGE_API_ENDPOINT') and os.environ.get('GAUGE_AUTH_TOKEN'):
            connector = GaugeAPIConnector()
            # Try a simple API call to test connection
            test_result = connector.get_vehicle_list()
            if test_result and 'error' not in test_result:
                return jsonify({
                    'connected': True,
                    'message': 'Connected to GAUGE API with environment credentials'
                })
            else:
                return jsonify({
                    'connected': False,
                    'message': 'GAUGE API credentials configured but connection failed'
                })
        else:
            return jsonify({
                'connected': False,
                'message': 'No GAUGE API credentials configured'
            })
    except Exception as e:
        return jsonify({
            'connected': False,
            'message': f'Connection error: {str(e)}'
        })

@enhanced_bp.route('/api/test-gauge-connection', methods=['POST'])
def test_gauge_connection():
    """Test GAUGE API connection with provided credentials"""
    import requests
    import base64
    
    try:
        data = request.get_json()
        api_url = data.get('url', '').rstrip('/')
        username = data.get('username')
        password = data.get('password')
        api_key = data.get('api_key')
        
        if not all([api_url, username, password, api_key]):
            return jsonify({'success': False, 'error': 'All credential fields are required'})
        
        # Test authentication endpoint
        auth_url = f"{api_url}/auth"
        auth_data = {'username': username, 'password': password}
        
        # Create authentication header
        auth_string = f"{username}:{password}"
        auth_bytes = auth_string.encode('ascii')
        auth_header = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        # Test the connection using your specific AssetList endpoint
        if '28dcba94c01e453fa8e9215a068f30e4' in api_url:
            # Use the exact endpoint structure you provided
            test_url = api_url
        else:
            # Construct the AssetList endpoint
            test_url = f"{api_url}/AssetList/28dcba94c01e453fa8e9215a068f30e4"
        
        response = requests.get(test_url, headers=headers, timeout=10, verify=False)
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Connection successful',
                'data': response.json() if response.content else {}
            })
        elif response.status_code == 401:
            return jsonify({'success': False, 'error': 'Authentication failed - check username/password'})
        elif response.status_code == 403:
            return jsonify({'success': False, 'error': 'Access forbidden - check API key'})
        elif response.status_code == 404:
            return jsonify({'success': False, 'error': 'API endpoint not found - check URL'})
        else:
            return jsonify({'success': False, 'error': f'HTTP {response.status_code}: {response.text[:200]}'})
            
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Cannot connect to API endpoint - check URL'})
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Connection timeout - API may be slow'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Connection test failed: {str(e)}'})

@enhanced_bp.route('/api/save-gauge-credentials', methods=['POST'])
def save_gauge_credentials():
    """Save GAUGE API credentials to environment/database"""
    import os
    
    try:
        data = request.get_json()
        api_url = data.get('url', '').rstrip('/')
        username = data.get('username')
        password = data.get('password')
        api_key = data.get('api_key')
        
        if not all([api_url, username, password, api_key]):
            return jsonify({'success': False, 'error': 'All credential fields are required'})
        
        # Save to environment variables (in production, save to secure storage)
        os.environ['GAUGE_API_ENDPOINT'] = api_url
        os.environ['GAUGE_AUTH_TOKEN'] = api_key
        os.environ['GAUGE_CLIENT_ID'] = username
        os.environ['GAUGE_CLIENT_SECRET'] = password
        
        # Also save to a credentials file for persistence
        credentials = {
            'endpoint': api_url,
            'username': username,
            'password': password,
            'api_key': api_key,
            'saved_at': datetime.now().isoformat()
        }
        
        with open('gauge_credentials.json', 'w') as f:
            json.dump(credentials, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'GAUGE API credentials saved successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to save credentials: {str(e)}'})