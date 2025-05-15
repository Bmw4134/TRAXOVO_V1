"""
Kaizen Module Blueprint

This blueprint provides routes for system self-improvement and optimization processes.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import os
import json
from datetime import datetime
from flask_login import login_required, current_user

from utils.kaizen import (
    calculate_system_health, 
    get_latest_health_score, 
    get_improvement_suggestions,
    mark_suggestion_implemented,
    get_asset_employee_mappings
)

kaizen_bp = Blueprint('kaizen', __name__, url_prefix='/kaizen')

@kaizen_bp.route('/')
@login_required
def index():
    """Render the Kaizen dashboard"""
    # Get latest system health score
    health_score = get_latest_health_score()
    
    # Get improvement suggestions
    pending_suggestions = get_improvement_suggestions(limit=10, implemented=False)
    implemented_suggestions = get_improvement_suggestions(limit=5, implemented=True)
    
    # Get recent health history (for chart)
    # In a real implementation, this would query a database for historical health scores
    history = [
        {
            "timestamp": (datetime.now().replace(day=datetime.now().day-i)).isoformat(),
            "overall_health_score": max(50, min(95, health_score.get('overall_health_score', 75) + (i-3)*2)),
            "data_completeness": max(50, min(95, health_score.get('data_completeness', {}).get('score', 80) + (i-3)*1.5)),
            "file_match_rate": max(50, min(95, health_score.get('file_match_rate', {}).get('score', 70) + (i-3)*2.5)),
            "asset_assignment_accuracy": max(50, min(95, health_score.get('asset_assignment_accuracy', {}).get('score', 65) + (i-3)*3))
        }
        for i in range(7)
    ]
    
    return render_template(
        'kaizen/index.html',
        health_score=health_score,
        pending_suggestions=pending_suggestions,
        implemented_suggestions=implemented_suggestions,
        history=history
    )

@kaizen_bp.route('/health')
@login_required
def health():
    """Render the system health page"""
    # Get latest system health score
    health_score = get_latest_health_score()
    
    # Get recent health history (for chart)
    # In a real implementation, this would query a database for historical health scores
    history = [
        {
            "timestamp": (datetime.now().replace(day=datetime.now().day-i)).isoformat(),
            "overall_health_score": max(50, min(95, health_score.get('overall_health_score', 75) + (i-3)*2)),
            "data_completeness": max(50, min(95, health_score.get('data_completeness', {}).get('score', 80) + (i-3)*1.5)),
            "file_match_rate": max(50, min(95, health_score.get('file_match_rate', {}).get('score', 70) + (i-3)*2.5)),
            "asset_assignment_accuracy": max(50, min(95, health_score.get('asset_assignment_accuracy', {}).get('score', 65) + (i-3)*3))
        }
        for i in range(14)
    ]
    
    return render_template(
        'kaizen/health.html',
        health_score=health_score,
        history=history
    )

@kaizen_bp.route('/refresh', methods=['POST'])
@login_required
def refresh():
    """Recalculate system health metrics"""
    if not current_user.is_admin:
        flash("You don't have permission to perform this action", "danger")
        return redirect(url_for('kaizen.index'))
    
    try:
        # Load assets from file or database
        from utils import load_data
        assets = load_data('data/processed_data.json')
        
        # Calculate system health
        health = calculate_system_health(assets)
        
        flash("System health metrics refreshed successfully", "success")
    except Exception as e:
        flash(f"Failed to refresh system health metrics: {e}", "danger")
    
    return redirect(url_for('kaizen.health'))

@kaizen_bp.route('/suggestions')
@login_required
def suggestions():
    """Render the improvement suggestions page"""
    # Get improvement suggestions
    pending_suggestions = get_improvement_suggestions(limit=100, implemented=False)
    implemented_suggestions = get_improvement_suggestions(limit=100, implemented=True)
    
    return render_template(
        'kaizen/suggestions.html',
        pending_suggestions=pending_suggestions,
        implemented_suggestions=implemented_suggestions
    )

@kaizen_bp.route('/implement/<int:suggestion_id>', methods=['POST'])
@login_required
def implement_suggestion(suggestion_id):
    """Mark a suggestion as implemented"""
    if not current_user.is_admin:
        flash("You don't have permission to perform this action", "danger")
        return redirect(url_for('kaizen.suggestions'))
    
    success = mark_suggestion_implemented(suggestion_id)
    
    if success:
        flash("Suggestion marked as implemented", "success")
    else:
        flash("Failed to mark suggestion as implemented", "danger")
    
    return redirect(url_for('kaizen.suggestions'))

@kaizen_bp.route('/mappings')
@login_required
def mappings():
    """Render the asset-employee mappings page"""
    # Get confidence filter from query string
    confidence = request.args.get('confidence', 'all')
    
    # Get mappings
    mappings = get_asset_employee_mappings(confidence=confidence, limit=100)
    
    # Count mappings by confidence
    high_confidence = len([m for m in mappings if m.get('confidence', 0) >= 0.8])
    medium_confidence = len([m for m in mappings if 0.5 <= m.get('confidence', 0) < 0.8])
    low_confidence = len([m for m in mappings if m.get('confidence', 0) < 0.5])
    
    return render_template(
        'kaizen/mappings.html',
        mappings=mappings,
        current_confidence=confidence,
        high_confidence=high_confidence,
        medium_confidence=medium_confidence,
        low_confidence=low_confidence
    )

@kaizen_bp.route('/api/health')
@login_required
def api_health():
    """API endpoint to get health metrics"""
    health_score = get_latest_health_score()
    return jsonify(health_score)