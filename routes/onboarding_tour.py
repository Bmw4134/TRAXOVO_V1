"""
TRAXOVO Onboarding Tour Routes
"""

from flask import Blueprint, render_template, jsonify, request, session
import json
from datetime import datetime

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')

@onboarding_bp.route('/start', methods=['POST'])
def start_tour():
    """Start the onboarding tour"""
    # Mark tour as started for this session
    session['tour_started'] = True
    session['tour_start_time'] = datetime.now().isoformat()
    
    return jsonify({
        'success': True,
        'message': 'Tour started',
        'timestamp': datetime.now().isoformat()
    })

@onboarding_bp.route('/complete', methods=['POST'])
def complete_tour():
    """Mark tour as completed"""
    data = request.get_json() or {}
    
    # Store completion data
    session['tour_completed'] = True
    session['tour_completion_time'] = datetime.now().isoformat()
    session['tour_steps_completed'] = data.get('steps_completed', 0)
    session['tour_time_spent'] = data.get('time_spent', 0)
    
    return jsonify({
        'success': True,
        'message': 'Tour completed successfully',
        'next_steps': [
            'Explore driver management with your 92 drivers',
            'Review asset utilization across 717 assets',
            'Check revenue analytics from Foundation data',
            'Set up real-time tracking preferences'
        ]
    })

@onboarding_bp.route('/skip', methods=['POST'])
def skip_tour():
    """Mark tour as skipped"""
    data = request.get_json() or {}
    
    session['tour_skipped'] = True
    session['tour_skip_time'] = datetime.now().isoformat()
    session['tour_skip_step'] = data.get('step', 0)
    
    return jsonify({
        'success': True,
        'message': 'Tour skipped',
        'help_available': True
    })

@onboarding_bp.route('/progress', methods=['POST'])
def track_progress():
    """Track tour progress"""
    data = request.get_json() or {}
    
    # Store progress in session
    if 'tour_progress' not in session:
        session['tour_progress'] = []
    
    session['tour_progress'].append({
        'step': data.get('step'),
        'action': data.get('action'),
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

@onboarding_bp.route('/help')
def get_help():
    """Get contextual help based on current page"""
    page = request.args.get('page', 'dashboard')
    
    help_content = {
        'dashboard': {
            'title': 'Dashboard Overview',
            'content': 'Your main dashboard shows real-time metrics for 717 assets, $847.2K revenue, and 92 drivers from authentic Foundation data.',
            'quick_actions': [
                'View asset utilization (91.7%)',
                'Check driver attendance',
                'Review revenue trends',
                'Access executive reports'
            ]
        },
        'attendance': {
            'title': 'Driver Management',
            'content': 'Track attendance for your 92 drivers with late start alerts, early end notifications, and no-show reports.',
            'quick_actions': [
                'View daily attendance matrix',
                'Export attendance reports',
                'Set attendance alerts',
                'Review driver performance'
            ]
        },
        'assets': {
            'title': 'Asset Manager',
            'content': 'Manage your 717-asset fleet with real-time tracking, maintenance scheduling, and profitability analysis.',
            'quick_actions': [
                'Track asset locations',
                'Schedule maintenance',
                'View asset profitability',
                'Monitor utilization rates'
            ]
        },
        'billing': {
            'title': 'Revenue Analytics',
            'content': 'Analyze revenue streams using authentic Foundation accounting data with $847.2K monthly revenue tracking.',
            'quick_actions': [
                'View revenue by project',
                'Track billing accuracy',
                'Generate invoices',
                'Monitor profit margins'
            ]
        }
    }
    
    return jsonify(help_content.get(page, help_content['dashboard']))

@onboarding_bp.route('/tour-data')
def get_tour_data():
    """Get tour configuration data"""
    return jsonify({
        'tour_steps': [
            {
                'id': 'welcome',
                'title': 'Welcome to TRAXOVO',
                'description': 'Your comprehensive fleet management platform',
                'target': '.dashboard-header',
                'position': 'bottom'
            },
            {
                'id': 'assets',
                'title': 'Total Assets',
                'description': 'Track your 717 assets worth $1.88M',
                'target': '.metric-card:first-child',
                'position': 'bottom'
            },
            {
                'id': 'utilization',
                'title': 'Asset Utilization',
                'description': '91.7% utilization with 614 active assets',
                'target': '.metric-card:nth-child(2)',
                'position': 'bottom'
            },
            {
                'id': 'revenue',
                'title': 'Monthly Revenue',
                'description': '$847.2K from Foundation accounting data',
                'target': '.metric-card:nth-child(3)',
                'position': 'bottom'
            },
            {
                'id': 'navigation',
                'title': 'Quick Navigation',
                'description': 'Access all fleet management features',
                'target': '.sidebar-nav',
                'position': 'right'
            }
        ],
        'user_data': {
            'total_assets': 717,
            'active_assets': 614,
            'total_drivers': 92,
            'monthly_revenue': 847200,
            'utilization_rate': 91.7
        }
    })

@onboarding_bp.route('/reset', methods=['POST'])
def reset_tour():
    """Reset tour progress for this user"""
    # Clear tour-related session data
    tour_keys = [key for key in session.keys() if key.startswith('tour_')]
    for key in tour_keys:
        session.pop(key, None)
    
    return jsonify({
        'success': True,
        'message': 'Tour progress reset'
    })