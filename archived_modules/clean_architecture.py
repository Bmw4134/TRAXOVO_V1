"""
TRAXOVO Clean Architecture Implementation
Based on JDD Enterprise success patterns for role-based dashboards
"""

from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
import json
import os

# Role-based dashboard blueprint
role_dashboard_bp = Blueprint('role_dashboard', __name__, url_prefix='/dashboard')

class RoleBasedDashboard:
    """Clean dashboard architecture based on JDD patterns"""
    
    def __init__(self):
        self.roles = {
            'vp': {
                'title': 'VP Operations Dashboard',
                'metrics': ['revenue', 'utilization', 'strategic_kpis'],
                'widgets': ['executive_summary', 'revenue_analytics', 'strategic_planning']
            },
            'controller': {
                'title': 'Controller Dashboard', 
                'metrics': ['billing_accuracy', 'cost_analysis', 'financial_reports'],
                'widgets': ['financial_reports', 'cost_analysis', 'audit_trails']
            },
            'equipment': {
                'title': 'Equipment Team Dashboard',
                'metrics': ['asset_utilization', 'maintenance_status', 'operational_efficiency'],
                'widgets': ['asset_management', 'maintenance_tracking', 'utilization_reports']
            },
            'estimating': {
                'title': 'Estimating Team Dashboard',
                'metrics': ['project_estimates', 'cost_modeling', 'bid_success_rate'],
                'widgets': ['project_estimates', 'cost_modeling', 'bid_analysis']
            }
        }
    
    def get_clean_metrics(self, role='vp'):
        """Get focused metrics for specific role - JDD pattern"""
        if role not in self.roles:
            role = 'vp'
            
        return {
            'monthly_operations': '$605K+',
            'fleet_utilization': '89.2%', 
            'tracked_assets': '717',
            'billing_accuracy': '94.7%',
            'role_specific': self.roles[role]['metrics']
        }
    
    def get_role_widgets(self, role='vp'):
        """Get widgets for specific role - clean JDD approach"""
        if role not in self.roles:
            role = 'vp'
        return self.roles[role]['widgets']

@role_dashboard_bp.route('/')
@login_required
def clean_dashboard():
    """Main dashboard with JDD-style role-based view"""
    user_role = getattr(current_user, 'role', 'vp')
    dashboard = RoleBasedDashboard()
    
    return render_template('dashboard/clean_dashboard.html',
                         metrics=dashboard.get_clean_metrics(user_role),
                         widgets=dashboard.get_role_widgets(user_role),
                         role=user_role,
                         title=dashboard.roles.get(user_role, {}).get('title', 'TRAXOVO Dashboard'))

@role_dashboard_bp.route('/api/metrics/<role>')
@login_required  
def api_clean_metrics(role):
    """Clean API endpoint for role-specific metrics"""
    dashboard = RoleBasedDashboard()
    return jsonify(dashboard.get_clean_metrics(role))

def register_clean_architecture(app):
    """Register the clean architecture with the app"""
    app.register_blueprint(role_dashboard_bp)
    return role_dashboard_bp