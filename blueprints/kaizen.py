"""
Kaizen Blueprint

This Flask Blueprint provides routes for:
1. Displaying system health metrics
2. Viewing and managing improvement suggestions
3. Reviewing asset-employee mappings
4. Monitoring system performance
"""

import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from utils.kaizen import (
    calculate_system_health, get_latest_health_score, 
    get_improvement_suggestions, process_asset_identifiers,
    extract_employee_from_asset, update_employee_asset_mapping
)

# Create Blueprint
kaizen_bp = Blueprint('kaizen', __name__, url_prefix='/kaizen')

@kaizen_bp.route('/')
@login_required
def index():
    """Kaizen Dashboard"""
    # Get latest health score
    health_score = get_latest_health_score()
    
    # Get improvement suggestions
    suggestions = get_improvement_suggestions(limit=5)
    
    return render_template(
        'kaizen/index.html',
        title="Kaizen Dashboard",
        health_score=health_score,
        suggestions=suggestions
    )

@kaizen_bp.route('/health')
@login_required
def health():
    """System Health Metrics"""
    # Get latest health score
    health_score = get_latest_health_score()
    
    # Get health history
    history = get_health_history()
    
    return render_template(
        'kaizen/health.html',
        title="System Health",
        health_score=health_score,
        history=history
    )

@kaizen_bp.route('/suggestions')
@login_required
def suggestions():
    """Improvement Suggestions"""
    # Get query parameters
    implemented = request.args.get('implemented', 'false') == 'true'
    limit = request.args.get('limit', '50')
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 50
    
    # Get suggestions
    suggestions = get_improvement_suggestions(limit=limit, implemented=implemented)
    
    return render_template(
        'kaizen/suggestions.html',
        title="Improvement Suggestions",
        suggestions=suggestions,
        implemented=implemented
    )

@kaizen_bp.route('/suggestions/<int:suggestion_id>/implement', methods=['POST'])
@login_required
def implement_suggestion(suggestion_id):
    """Mark a suggestion as implemented"""
    # Check if user is admin
    if not current_user.is_admin:
        flash("You don't have permission to perform this action", "danger")
        return redirect(url_for('kaizen.suggestions'))
    
    # Mark suggestion as implemented
    from utils.kaizen import mark_suggestion_implemented
    success = mark_suggestion_implemented(suggestion_id)
    
    if success:
        flash("Suggestion marked as implemented", "success")
    else:
        flash("Failed to update suggestion", "danger")
    
    return redirect(url_for('kaizen.suggestions'))

@kaizen_bp.route('/mappings')
@login_required
def mappings():
    """Asset-Employee Mappings"""
    # Get query parameters
    confidence = request.args.get('confidence', 'all')
    limit = request.args.get('limit', '100')
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 100
    
    # Get mappings
    from utils.kaizen import get_asset_employee_mappings
    mappings = get_asset_employee_mappings(confidence=confidence, limit=limit)
    
    return render_template(
        'kaizen/mappings.html',
        title="Asset-Employee Mappings",
        mappings=mappings,
        confidence=confidence
    )

@kaizen_bp.route('/refresh', methods=['POST'])
@login_required
def refresh_health():
    """Refresh system health metrics"""
    # Check if user is admin
    if not current_user.is_admin:
        flash("You don't have permission to perform this action", "danger")
        return redirect(url_for('kaizen.index'))
    
    # Recalculate system health
    health_score = calculate_system_health()
    
    flash("System health metrics recalculated", "success")
    return redirect(url_for('kaizen.health'))

@kaizen_bp.route('/api/extract-employee', methods=['POST'])
@login_required
def api_extract_employee():
    """API endpoint to extract employee name from asset identifier"""
    data = request.json
    if not data or 'asset_identifier' not in data:
        return jsonify({'success': False, 'error': 'Missing asset_identifier'}), 400
    
    asset_identifier = data['asset_identifier']
    employee, confidence, method = extract_employee_from_asset(asset_identifier)
    
    return jsonify({
        'success': True,
        'employee_name': employee,
        'confidence_score': confidence,
        'detection_method': method
    })

@kaizen_bp.route('/api/update-mapping', methods=['POST'])
@login_required
def api_update_mapping():
    """API endpoint to update asset-employee mapping"""
    data = request.json
    if not data or 'asset_identifier' not in data or 'employee_name' not in data:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    asset_identifier = data['asset_identifier']
    employee_name = data['employee_name']
    confidence_score = data.get('confidence_score', 1.0)
    detection_method = data.get('detection_method', 'manual')
    
    result = update_employee_asset_mapping(
        asset_identifier,
        employee_name,
        confidence_score,
        detection_method
    )
    
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Update failed'}), 500

def get_health_history(days=30):
    """Get system health history for the specified number of days"""
    try:
        import sqlite3
        from utils.kaizen import KAIZEN_DB_PATH
        
        conn = sqlite3.connect(KAIZEN_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM system_metrics WHERE timestamp >= datetime('now', ?) "
            "ORDER BY timestamp ASC",
            (f'-{days} day',)
        )
        
        rows = cursor.fetchall()
        history = []
        
        for row in rows:
            entry = dict(row)
            if entry.get('metric_details'):
                entry['details'] = json.loads(entry['metric_details'])
            history.append(entry)
        
        conn.close()
        return history
    except Exception as e:
        import logging
        logging.error(f"Error getting health history: {e}")
        return []