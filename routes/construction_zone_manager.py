"""
Construction Zone Manager for TRAXOVO

This module provides routes for managing authentic construction job data,
parent zones, subzones, and attendance validation using real project data.
"""
import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from utils.multi_zone_processor import MultiZoneProcessor

logger = logging.getLogger(__name__)

construction_zones_bp = Blueprint('construction_zones', __name__, url_prefix='/construction-zones')

# Configuration
UPLOAD_FOLDER = 'uploads/construction_data'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def ensure_upload_folder():
    """Ensure upload folder exists"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@construction_zones_bp.route('/')
@login_required
def dashboard():
    """Construction zones management dashboard"""
    processor = MultiZoneProcessor()
    zone_structure = processor.load_zone_structure()
    
    # Calculate statistics
    parent_zones_count = len(zone_structure.get('parent_zones', {}))
    total_subzones = len(zone_structure.get('subzone_index', {}))
    
    return render_template('construction_zones/dashboard.html',
                         zone_structure=zone_structure,
                         parent_zones_count=parent_zones_count,
                         total_subzones=total_subzones,
                         last_updated=zone_structure.get('last_updated', 'Never'))

@construction_zones_bp.route('/upload-job-data', methods=['GET', 'POST'])
@login_required
def upload_job_data():
    """Upload authentic construction job CSV/Excel data"""
    if request.method == 'POST':
        ensure_upload_folder()
        
        # Check if file was uploaded
        if 'job_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['job_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)
            if filename:  # Check if filename is not empty after securing
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Process authentic construction data
                processor = MultiZoneProcessor()
                try:
                    if filename.lower().endswith('.csv'):
                        zone_structure = processor.process_construction_csv(filepath)
                    else:
                        # For Excel files, convert to CSV or process directly
                        zone_structure = processor.process_construction_csv(filepath)
                    
                    parent_zones = len(zone_structure.get('parent_zones', {}))
                    subzones = len(zone_structure.get('subzone_index', {}))
                    
                    if parent_zones > 0:
                        flash(f'Successfully processed {parent_zones} parent zones with {subzones} subzones from authentic job data', 'success')
                    else:
                        flash('No valid construction zones found in the uploaded file', 'warning')
                    
                    # Clean up uploaded file
                    os.remove(filepath)
                    
                    return redirect(url_for('construction_zones.dashboard'))
                    
                except Exception as e:
                    logger.error(f"Error processing construction data: {e}")
                    flash(f'Error processing authentic job data: {str(e)}', 'error')
                    
                    # Clean up uploaded file
                    if os.path.exists(filepath):
                        os.remove(filepath)
            else:
                flash('Invalid filename after security check', 'error')
        else:
            flash('Invalid file type. Please upload CSV or Excel files only.', 'error')
    
    return render_template('construction_zones/upload.html')

@construction_zones_bp.route('/parent-zone/<zone_id>')
@login_required
def parent_zone_detail(zone_id):
    """Show details for a specific parent zone"""
    processor = MultiZoneProcessor()
    parent_zone = processor.get_parent_zone(zone_id)
    
    if not parent_zone:
        flash(f'Parent zone {zone_id} not found in authentic data', 'error')
        return redirect(url_for('construction_zones.dashboard'))
    
    return render_template('construction_zones/parent_zone_detail.html',
                         zone_id=zone_id,
                         parent_zone=parent_zone)

@construction_zones_bp.route('/subzone/<subzone_key>')
@login_required
def subzone_detail(subzone_key):
    """Show details for a specific subzone"""
    processor = MultiZoneProcessor()
    parent_zone_id, subzone_data = processor.get_subzone(subzone_key)
    
    if not subzone_data:
        flash(f'Subzone {subzone_key} not found in authentic data', 'error')
        return redirect(url_for('construction_zones.dashboard'))
    
    return render_template('construction_zones/subzone_detail.html',
                         subzone_key=subzone_key,
                         parent_zone_id=parent_zone_id,
                         subzone_data=subzone_data)

@construction_zones_bp.route('/api/zone-structure')
@login_required
def api_zone_structure():
    """API endpoint to get current zone structure"""
    processor = MultiZoneProcessor()
    zone_structure = processor.load_zone_structure()
    return jsonify(zone_structure)

@construction_zones_bp.route('/api/validate-gps', methods=['POST'])
@login_required
def api_validate_gps():
    """API endpoint to validate GPS coordinates against authentic zones"""
    data = request.get_json()
    
    if not data or 'zone_id' not in data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Missing required fields: zone_id, latitude, longitude'}), 400
    
    try:
        processor = MultiZoneProcessor()
        
        zone_id = data['zone_id']
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        subzone_id = data.get('subzone_id')
        
        result = processor.validate_gps_in_zone(zone_id, latitude, longitude, subzone_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error validating GPS coordinates: {e}")
        return jsonify({'error': str(e)}), 500

@construction_zones_bp.route('/api/parent-zones')
@login_required
def api_parent_zones():
    """API endpoint to get list of parent zones"""
    processor = MultiZoneProcessor()
    zone_structure = processor.load_zone_structure()
    parent_zones = zone_structure.get('parent_zones', {})
    
    # Return simplified parent zone list
    zones_list = []
    for zone_id, zone_data in parent_zones.items():
        zones_list.append({
            'zone_id': zone_id,
            'zone_name': zone_data.get('zone_name'),
            'total_subzones': zone_data.get('total_subzones', 0),
            'primary_address': zone_data.get('primary_address'),
            'center_coordinates': zone_data.get('center_coordinates')
        })
    
    return jsonify(zones_list)

@construction_zones_bp.route('/attendance-validation')
@login_required
def attendance_validation():
    """Attendance validation dashboard using authentic zone data"""
    processor = MultiZoneProcessor()
    zone_structure = processor.load_zone_structure()
    
    return render_template('construction_zones/attendance_validation.html',
                         zone_structure=zone_structure)