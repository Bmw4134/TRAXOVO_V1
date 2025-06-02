"""
Automated Report Import Routes
Intelligence-driven report processing system
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
from automated_report_importer import get_report_importer
from unified_navigation import get_navigation_system
import os
from datetime import datetime

automated_reports_bp = Blueprint('automated_reports', __name__)
report_importer = get_report_importer()
nav_system = get_navigation_system()

def require_auth():
    """Check if user is authenticated"""
    return session.get('authenticated') and not session.get('needs_2fa')

@automated_reports_bp.route('/automated_reports')
def report_dashboard():
    """Automated report processing dashboard"""
    if not require_auth():
        return redirect(url_for('secure_auth.secure_login'))
    
    nav_data = nav_system.get_navigation_for_user(session.get('username'))
    dashboard_data = report_importer.get_processing_dashboard()
    
    return render_template('automated_reports.html', 
                         navigation=nav_data,
                         dashboard_data=dashboard_data)

@automated_reports_bp.route('/api/upload_report', methods=['POST'])
def upload_report():
    """API endpoint for report file upload"""
    if not require_auth():
        return jsonify({"success": False, "error": "Authentication required"})
    
    if 'report_file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})
    
    file = request.files['report_file']
    report_type = request.form.get('report_type')
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"})
    
    if file:
        filename = secure_filename(file.filename)
        file_data = file.read()
        
        # Process the report
        result = report_importer.queue_report_for_import(file_data, filename, report_type)
        
        if result.get('success'):
            return jsonify({
                "success": True,
                "message": f"Report '{filename}' processed successfully",
                "report_type": result.get('report_type'),
                "data_points": result.get('data_points', 0),
                "analytics": result.get('analytics', {}),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Processing failed')
            })

@automated_reports_bp.route('/api/report_status')
def get_report_status():
    """Get current report processing status"""
    if not require_auth():
        return jsonify({"success": False, "error": "Authentication required"})
    
    dashboard_data = report_importer.get_processing_dashboard()
    return jsonify(dashboard_data)

@automated_reports_bp.route('/api/processing_history')
def get_processing_history():
    """Get report processing history"""
    if not require_auth():
        return jsonify({"success": False, "error": "Authentication required"})
    
    return jsonify({
        "history": report_importer.processing_history[-20:],  # Last 20 items
        "total_processed": len(report_importer.processing_history)
    })

@automated_reports_bp.route('/report_analytics/<report_type>')
def report_analytics(report_type):
    """Detailed analytics for specific report type"""
    if not require_auth():
        return redirect(url_for('secure_auth.secure_login'))
    
    nav_data = nav_system.get_navigation_for_user(session.get('username'))
    
    # Filter processing history by report type
    filtered_history = [
        record for record in report_importer.processing_history
        if record.get('report_type') == report_type
    ]
    
    analytics_data = {
        "report_type": report_type,
        "total_processed": len(filtered_history),
        "recent_reports": filtered_history[-10:],
        "success_rate": len([r for r in filtered_history if r.get('status') == 'SUCCESS']) / max(1, len(filtered_history)) * 100
    }
    
    return render_template('report_analytics.html',
                         navigation=nav_data,
                         analytics=analytics_data,
                         report_type=report_type)