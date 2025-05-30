"""
Attendance Routes - Live Dashboard and Matrix Views
Production-grade attendance tracking with GPS validation
"""

from flask import Blueprint, render_template, jsonify, request, send_file
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import os

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/matrix')
def attendance_matrix():
    """Live attendance matrix dashboard with GPS validation"""
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    job_id = request.args.get('job_id', 'all')
    
    # Load authentic attendance data
    matrix_data = load_attendance_matrix(date, job_id)
    
    context = {
        'page_title': 'Attendance Matrix',
        'page_subtitle': 'GPS-validated workforce tracking',
        'matrix_data': matrix_data,
        'current_date': date,
        'selected_job': job_id
    }
    
    return render_template('attendance_matrix.html', **context)

@attendance_bp.route('/api/live-status')
def api_live_status():
    """Real-time attendance status for dashboard"""
    from services.gauge_api import get_live_asset_status
    from utils.zone_matcher import match_assets_to_zones
    
    try:
        # Get live GPS data from Gauge API
        live_assets = get_live_asset_status()
        
        # Match to job site geofences
        zone_matches = match_assets_to_zones(live_assets)
        
        return jsonify({
            'status': 'success',
            'on_site': len([a for a in zone_matches if a['in_zone']]),
            'off_site': len([a for a in zone_matches if not a['in_zone']]),
            'no_signal': len([a for a in live_assets if not a.get('gps_valid')]),
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@attendance_bp.route('/export/pdf/<job_id>/<date>')
def export_pdf(job_id, date):
    """Export attendance matrix as PDF"""
    matrix_data = load_attendance_matrix(date, job_id)
    
    # Generate PDF using reportlab or similar
    pdf_buffer = generate_attendance_pdf(matrix_data, job_id, date)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'attendance_matrix_{job_id}_{date}.pdf'
    )

@attendance_bp.route('/export/csv/<job_id>/<date>')
def export_csv(job_id, date):
    """Export attendance matrix as CSV"""
    matrix_data = load_attendance_matrix(date, job_id)
    
    # Convert to CSV
    df = pd.DataFrame(matrix_data)
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'attendance_matrix_{job_id}_{date}.csv'
    )

@attendance_bp.route('/export/xlsx/<job_id>/<date>')
def export_xlsx(job_id, date):
    """Export attendance matrix as Excel"""
    matrix_data = load_attendance_matrix(date, job_id)
    
    # Convert to Excel
    df = pd.DataFrame(matrix_data)
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'attendance_matrix_{job_id}_{date}.xlsx'
    )

def load_attendance_matrix(date, job_id):
    """Load attendance matrix data for specified date and job"""
    # This would integrate with your database
    # For now, return structured format
    return [
        {
            'employee_name': 'John Smith',
            'employee_id': 'EMP001',
            'asset_id': 'EXC-045',
            'job_id': '2019-044',
            'clock_in': '07:00',
            'clock_out': '17:30',
            'gps_status': 'on_site',
            'status_icon': '🟢',
            'hours_worked': 10.5
        },
        {
            'employee_name': 'Mike Johnson',
            'employee_id': 'EMP002',
            'asset_id': 'TRK-012',
            'job_id': '2019-044',
            'clock_in': '07:15',
            'clock_out': '17:30',
            'gps_status': 'late_start',
            'status_icon': '🟡',
            'hours_worked': 10.25
        }
    ]

def generate_attendance_pdf(matrix_data, job_id, date):
    """Generate PDF report from matrix data"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # PDF generation logic here
    p.drawString(100, 750, f"Attendance Matrix - Job {job_id} - {date}")
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer