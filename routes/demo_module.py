"""
Demo Module - Phase 4 QA Modular Extensibility Test

This module tests true modular extensibility with dashboard + edit views
following the exact same styling and navigation patterns as other modules.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
import logging

logger = logging.getLogger(__name__)

# Create blueprint
demo_bp = Blueprint('demo_module', __name__, url_prefix='/demo-module')

@demo_bp.route('/')
def dashboard():
    """Demo module dashboard view"""
    logger.info("Demo module dashboard accessed")
    
    # Sample data for demonstration
    demo_data = {
        'total_items': 42,
        'active_items': 38,
        'pending_items': 4,
        'last_update': '2025-05-27 18:45:00'
    }
    
    return render_template('demo_module/dashboard.html', 
                         demo_data=demo_data,
                         title="Demo Module")

@demo_bp.route('/edit/<int:item_id>')
def edit_item(item_id):
    """Demo module edit view"""
    logger.info(f"Demo module edit view accessed for item {item_id}")
    
    # Sample item data
    item_data = {
        'id': item_id,
        'name': f'Demo Item {item_id}',
        'status': 'active',
        'description': f'This is a demonstration item #{item_id} for testing modular extensibility.',
        'created_date': '2025-05-27',
        'category': 'Test'
    }
    
    return render_template('demo_module/edit.html', 
                         item=item_data,
                         title=f"Edit Demo Item {item_id}")

@demo_bp.route('/save', methods=['POST'])
def save_item():
    """Demo module save functionality"""
    logger.info("Demo module save action triggered")
    
    # Process form data (demonstration only)
    item_name = request.form.get('name', '')
    item_status = request.form.get('status', 'active')
    
    flash(f'Demo item "{item_name}" saved successfully!', 'success')
    return redirect(url_for('demo_module.dashboard'))

# Register blueprint info for auto-discovery
BLUEPRINT_INFO = {
    'name': 'Demo Module',
    'description': 'Demonstration module for testing modular extensibility',
    'category': 'Testing',
    'icon': 'fas fa-flask',
    'url': '/demo-module/',
    'order': 999
}