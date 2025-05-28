
"""
Division Manager Access Module
Role-based dashboards for DFW, Houston, and WTX operations
"""
from flask import Blueprint, render_template, session, redirect, url_for

division_manager_bp = Blueprint('division_manager', __name__)

@division_manager_bp.route('/division-login')
def division_login():
    """Division manager login page"""
    return render_template('division_login.html')

@division_manager_bp.route('/dfw-dashboard')
def dfw_dashboard():
    """DFW Division Manager Dashboard"""
    return render_template('division_dashboard.html', division='DFW')

@division_manager_bp.route('/houston-dashboard')
def houston_dashboard():
    """Houston Division Manager Dashboard"""
    return render_template('division_dashboard.html', division='Houston')

@division_manager_bp.route('/wtx-dashboard')
def wtx_dashboard():
    """West Texas Division Manager Dashboard"""
    return render_template('division_dashboard.html', division='WTX')
