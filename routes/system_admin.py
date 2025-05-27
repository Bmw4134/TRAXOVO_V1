"""
System Administration Module
User management, system configuration, and administrative tasks
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import json
import os
import logging
from datetime import datetime, timedelta

system_admin_bp = Blueprint('system_admin', __name__)
logger = logging.getLogger(__name__)

@system_admin_bp.route('/system-admin')
def system_admin_dashboard():
    """System administration dashboard"""
    try:
        return render_template('system_admin.html')
    except Exception as e:
        logger.error(f"Error loading system admin: {e}")
        flash('Error loading system administration', 'error')
        return redirect(url_for('index'))

@system_admin_bp.route('/system-admin/users')
def user_management():
    """User management interface"""
    try:
        return render_template('user_management.html')
    except Exception as e:
        logger.error(f"Error loading user management: {e}")
        flash('Error loading user management', 'error')
        return redirect(url_for('system_admin.system_admin_dashboard'))

@system_admin_bp.route('/system-admin/configuration')
def system_configuration():
    """System configuration interface"""
    try:
        return render_template('system_configuration.html')
    except Exception as e:
        logger.error(f"Error loading system configuration: {e}")
        flash('Error loading system configuration', 'error')
        return redirect(url_for('system_admin.system_admin_dashboard'))