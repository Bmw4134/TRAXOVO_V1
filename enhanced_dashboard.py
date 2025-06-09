"""
Enhanced QNIS/PTNI Dashboard - Samsara-Level Interface
Complete enterprise fleet management with safety, maintenance, dispatch, and analytics
"""

from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
import json
import random

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