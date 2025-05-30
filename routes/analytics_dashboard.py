"""
TRAXOVO Analytics Dashboard
Unified analytics routing that prevents legacy dashboard conflicts
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import logging

analytics_dashboard_bp = Blueprint('analytics_dashboard', __name__)

@analytics_dashboard_bp.route('/analytics-dashboard')
def analytics_dashboard():
    """Main analytics dashboard - unified routing"""
    module = request.args.get('module', 'overview')
    return render_template('analytics_dashboard.html', module=module)

@analytics_dashboard_bp.route('/billing-consolidation')
def billing_consolidation():
    """Billing consolidation module"""
    return render_template('analytics_dashboard.html', module='billing')

@analytics_dashboard_bp.route('/revenue-analytics')
def revenue_analytics():
    """Revenue analytics module"""
    return render_template('analytics_dashboard.html', module='revenue')

@analytics_dashboard_bp.route('/asset-profit')
def asset_profit():
    """Enhanced asset profitability - static chart version"""
    return render_template('asset_profit_static.html')

# API endpoints for stable data
@analytics_dashboard_bp.route('/api/static-profit-data')
def static_profit_data():
    """Static profit data - no real-time updates"""
    return jsonify({
        'total_profit': '$144K',
        'top_performers': 3,
        'underperformers': 2,
        'avg_margin': '59.0%',
        'top_assets': [
            {'id': 'CAT 002', 'profit': '$35000', 'roi': '131.5%'},
            {'id': 'DOZ 012', 'profit': '$33000', 'roi': '139.9%'},
            {'id': 'EXC 001', 'profit': '$26700', 'roi': '144.8%'}
        ],
        'under_assets': [
            {'id': 'GRD 018', 'profit': '$8900', 'roi': '143.8%'},
            {'id': 'TRK 045', 'profit': '$27940', 'roi': '116.2%'}
        ]
    })