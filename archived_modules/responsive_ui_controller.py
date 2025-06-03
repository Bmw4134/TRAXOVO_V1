"""
Responsive UI Controller - Desktop/Mobile View Toggle
Advanced responsive design with device-specific optimizations
"""

from flask import Blueprint, render_template, jsonify, request, session

responsive_ui_bp = Blueprint('responsive_ui', __name__)

@responsive_ui_bp.route('/api/toggle-view-mode')
def toggle_view_mode():
    """Toggle between desktop and mobile view modes"""
    current_mode = session.get('view_mode', 'auto')
    
    if current_mode == 'desktop':
        new_mode = 'mobile'
    elif current_mode == 'mobile':
        new_mode = 'auto'
    else:
        new_mode = 'desktop'
    
    session['view_mode'] = new_mode
    
    return jsonify({
        'view_mode': new_mode,
        'message': f'Switched to {new_mode} view mode'
    })

@responsive_ui_bp.route('/api/ui-status')
def ui_status():
    """Get current UI configuration and status"""
    return jsonify({
        'view_mode': session.get('view_mode', 'auto'),
        'mobile_optimized': True,
        'desktop_optimized': True,
        'features': {
            'collapsible_sidebar': True,
            'touch_friendly_controls': True,
            'adaptive_charts': True,
            'smart_navigation': True
        }
    })