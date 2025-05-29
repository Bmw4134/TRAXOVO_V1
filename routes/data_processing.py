
"""
Data Processing Routes for TRAXOVO
Handles sequential processing of all data files
"""

from flask import Blueprint, jsonify, render_template
from utils.sequential_file_processor import sequential_processor
import logging

logger = logging.getLogger(__name__)

data_processing_bp = Blueprint('data_processing', __name__)

@data_processing_bp.route('/process-all-data')
def process_all_data():
    """Process all data files sequentially"""
    try:
        results = sequential_processor.process_all_files()
        return jsonify({
            'status': 'success',
            'message': 'All files processed successfully',
            'results': results
        })
    except Exception as e:
        logger.error(f"Data processing error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@data_processing_bp.route('/data-processing-dashboard')
def data_processing_dashboard():
    """Data processing dashboard"""
    return render_template('data_processing/dashboard.html')

@data_processing_bp.route('/processing-status')
def processing_status():
    """Get processing status"""
    try:
        import os
        cache_dir = 'data_cache'
        
        status = {
            'cache_files': [],
            'processed_files': 0,
            'last_update': None
        }
        
        if os.path.exists(cache_dir):
            cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.json')]
            status['cache_files'] = cache_files
            status['processed_files'] = len(cache_files)
            
            if cache_files:
                latest_file = max(cache_files, key=lambda f: os.path.getmtime(os.path.join(cache_dir, f)))
                status['last_update'] = os.path.getmtime(os.path.join(cache_dir, latest_file))
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
