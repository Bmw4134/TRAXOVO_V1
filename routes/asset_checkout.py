"""
Asset Check-In/Check-Out System
Employee accountability for open assets like pickup trucks
"""

import pandas as pd
import os
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, request, session
import hashlib

asset_checkout_bp = Blueprint('asset_checkout', __name__)

def get_open_assets():
    """Get list of assets available for check-out"""
    # Process your equipment files to identify open assets
    open_assets = []
    
    try:
        # Load from your authentic equipment files
        equipment_file = 'attached_assets/EQ LIST ALL DETAILS SELECTED 052925.xlsx'
        if os.path.exists(equipment_file):
            df = pd.read_excel(equipment_file, engine='openpyxl')
            
            for idx, row in df.iterrows():
                if pd.notna(row.iloc[0]):
                    asset_id = str(row.iloc[0]).strip()
                    description = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else "Equipment"
                    category = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else "General"
                    
                    # Identify vehicles and mobile equipment
                    if any(keyword in description.upper() for keyword in ['TRUCK', 'PICKUP', 'VAN', 'TRAILER', 'VEHICLE']):
                        open_assets.append({
                            'asset_id': asset_id,
                            'description': description,
                            'category': category,
                            'type': 'vehicle',
                            'status': 'available',
                            'last_checkout': None,
                            'current_user': None
                        })
    except Exception as e:
        print(f"Error loading assets: {e}")
    
    # Add some known vehicle assets if file processing fails
    if not open_assets:
        open_assets = [
            {'asset_id': 'TRK-001', 'description': 'Ford F-150 Pickup', 'category': 'Vehicles', 'type': 'vehicle', 'status': 'available'},
            {'asset_id': 'TRK-002', 'description': 'Chevy Silverado', 'category': 'Vehicles', 'type': 'vehicle', 'status': 'available'},
            {'asset_id': 'VAN-001', 'description': 'Transit Van', 'category': 'Vehicles', 'type': 'vehicle', 'status': 'available'}
        ]
    
    return open_assets

def get_checkout_history():
    """Get checkout history from session storage (in production, use database)"""
    history_file = 'data_cache/checkout_history.json'
    if os.path.exists(history_file):
        try:
            import json
            with open(history_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return []

def save_checkout_record(record):
    """Save checkout record (in production, use database)"""
    history = get_checkout_history()
    record['timestamp'] = datetime.now().isoformat()
    record['id'] = hashlib.md5(f"{record['asset_id']}_{record['timestamp']}".encode()).hexdigest()[:8]
    history.append(record)
    
    # Keep last 100 records
    history = history[-100:]
    
    try:
        import json
        os.makedirs('data_cache', exist_ok=True)
        with open('data_cache/checkout_history.json', 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving checkout record: {e}")
    
    return record

def get_current_checkouts():
    """Get currently checked out assets"""
    history = get_checkout_history()
    current_checkouts = {}
    
    for record in history:
        asset_id = record['asset_id']
        if record['action'] == 'checkout':
            current_checkouts[asset_id] = record
        elif record['action'] == 'checkin' and asset_id in current_checkouts:
            del current_checkouts[asset_id]
    
    return list(current_checkouts.values())

@asset_checkout_bp.route('/asset-checkout')
def asset_checkout_dashboard():
    """Asset checkout dashboard for employees"""
    open_assets = get_open_assets()
    checkout_history = get_checkout_history()
    current_checkouts = get_current_checkouts()
    
    # Update asset status based on checkouts
    checkout_map = {c['asset_id']: c for c in current_checkouts}
    for asset in open_assets:
        if asset['asset_id'] in checkout_map:
            asset['status'] = 'checked_out'
            asset['current_user'] = checkout_map[asset['asset_id']]['employee_name']
            asset['checkout_time'] = checkout_map[asset['asset_id']]['timestamp']
    
    context = {
        'page_title': 'Asset Check-In/Check-Out',
        'open_assets': open_assets,
        'available_count': len([a for a in open_assets if a['status'] == 'available']),
        'checked_out_count': len(current_checkouts),
        'recent_activity': checkout_history[-10:],  # Last 10 activities
        'current_checkouts': current_checkouts
    }
    
    return render_template('asset_checkout_dashboard.html', **context)

@asset_checkout_bp.route('/employee-checkout')
def employee_checkout_portal():
    """Simple employee portal for checking assets in/out"""
    open_assets = get_open_assets()
    current_checkouts = get_current_checkouts()
    
    # Update asset availability
    checkout_map = {c['asset_id']: c for c in current_checkouts}
    available_assets = []
    for asset in open_assets:
        if asset['asset_id'] not in checkout_map:
            available_assets.append(asset)
    
    context = {
        'page_title': 'Employee Asset Portal',
        'available_assets': available_assets,
        'my_checkouts': [c for c in current_checkouts if c.get('employee_name') == session.get('employee_name')],
        'employee_name': session.get('employee_name', '')
    }
    
    return render_template('employee_checkout_portal.html', **context)

@asset_checkout_bp.route('/api/checkout-asset', methods=['POST'])
def checkout_asset():
    """API to check out an asset"""
    data = request.get_json()
    
    required_fields = ['asset_id', 'employee_name', 'purpose']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if asset is available
    current_checkouts = get_current_checkouts()
    if any(c['asset_id'] == data['asset_id'] for c in current_checkouts):
        return jsonify({'error': 'Asset already checked out'}), 400
    
    # Create checkout record
    checkout_record = {
        'action': 'checkout',
        'asset_id': data['asset_id'],
        'employee_name': data['employee_name'],
        'employee_id': data.get('employee_id', ''),
        'purpose': data['purpose'],
        'expected_return': data.get('expected_return', ''),
        'notes': data.get('notes', ''),
        'mileage_out': data.get('mileage_out', ''),
        'fuel_level_out': data.get('fuel_level_out', ''),
        'condition_out': data.get('condition_out', 'Good')
    }
    
    saved_record = save_checkout_record(checkout_record)
    
    # Store employee name in session
    session['employee_name'] = data['employee_name']
    
    return jsonify({
        'success': True,
        'record': saved_record,
        'message': f"Asset {data['asset_id']} checked out successfully"
    })

@asset_checkout_bp.route('/api/checkin-asset', methods=['POST'])
def checkin_asset():
    """API to check in an asset"""
    data = request.get_json()
    
    required_fields = ['asset_id', 'employee_name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify asset is checked out to this employee
    current_checkouts = get_current_checkouts()
    checkout_record = None
    for c in current_checkouts:
        if c['asset_id'] == data['asset_id'] and c['employee_name'] == data['employee_name']:
            checkout_record = c
            break
    
    if not checkout_record:
        return jsonify({'error': 'Asset not checked out to this employee'}), 400
    
    # Calculate usage duration
    checkout_time = datetime.fromisoformat(checkout_record['timestamp'])
    checkin_time = datetime.now()
    usage_duration = str(checkin_time - checkout_time).split('.')[0]  # Remove microseconds
    
    # Create checkin record
    checkin_record = {
        'action': 'checkin',
        'asset_id': data['asset_id'],
        'employee_name': data['employee_name'],
        'employee_id': checkout_record.get('employee_id', ''),
        'usage_duration': usage_duration,
        'mileage_in': data.get('mileage_in', ''),
        'fuel_level_in': data.get('fuel_level_in', ''),
        'condition_in': data.get('condition_in', 'Good'),
        'notes': data.get('notes', ''),
        'issues_reported': data.get('issues_reported', ''),
        'checkout_id': checkout_record.get('id', '')
    }
    
    saved_record = save_checkout_record(checkin_record)
    
    return jsonify({
        'success': True,
        'record': saved_record,
        'usage_duration': usage_duration,
        'message': f"Asset {data['asset_id']} checked in successfully"
    })

@asset_checkout_bp.route('/api/checkout-history')
def get_checkout_history_api():
    """API to get checkout history for admin dashboard"""
    history = get_checkout_history()
    current_checkouts = get_current_checkouts()
    
    # Calculate statistics
    total_checkouts = len([h for h in history if h['action'] == 'checkout'])
    total_checkins = len([h for h in history if h['action'] == 'checkin'])
    active_checkouts = len(current_checkouts)
    
    # Asset utilization stats
    asset_usage = {}
    for record in history:
        asset_id = record['asset_id']
        if asset_id not in asset_usage:
            asset_usage[asset_id] = {'checkouts': 0, 'total_hours': 0}
        
        if record['action'] == 'checkout':
            asset_usage[asset_id]['checkouts'] += 1
    
    return jsonify({
        'history': history,
        'current_checkouts': current_checkouts,
        'statistics': {
            'total_checkouts': total_checkouts,
            'total_checkins': total_checkins,
            'active_checkouts': active_checkouts,
            'completion_rate': (total_checkins / total_checkouts * 100) if total_checkouts > 0 else 0
        },
        'asset_utilization': asset_usage
    })

@asset_checkout_bp.route('/admin/asset-accountability')
def admin_accountability_dashboard():
    """Admin dashboard for asset accountability oversight"""
    history = get_checkout_history()
    current_checkouts = get_current_checkouts()
    open_assets = get_open_assets()
    
    # Calculate metrics
    overdue_checkouts = []
    for checkout in current_checkouts:
        checkout_time = datetime.fromisoformat(checkout['timestamp'])
        hours_out = (datetime.now() - checkout_time).total_seconds() / 3600
        if hours_out > 24:  # Over 24 hours
            checkout['hours_overdue'] = hours_out - 24
            overdue_checkouts.append(checkout)
    
    # Employee usage stats
    employee_stats = {}
    for record in history:
        emp_name = record['employee_name']
        if emp_name not in employee_stats:
            employee_stats[emp_name] = {'checkouts': 0, 'checkins': 0, 'current': 0}
        
        if record['action'] == 'checkout':
            employee_stats[emp_name]['checkouts'] += 1
        else:
            employee_stats[emp_name]['checkins'] += 1
    
    for checkout in current_checkouts:
        emp_name = checkout['employee_name']
        if emp_name in employee_stats:
            employee_stats[emp_name]['current'] += 1
    
    context = {
        'page_title': 'Asset Accountability Dashboard',
        'current_checkouts': current_checkouts,
        'overdue_checkouts': overdue_checkouts,
        'recent_activity': history[-20:],  # Last 20 activities
        'employee_stats': employee_stats,
        'asset_count': len(open_assets),
        'utilization_rate': (len(current_checkouts) / len(open_assets) * 100) if open_assets else 0
    }
    
    return render_template('admin_accountability_dashboard.html', **context)