"""
File Organizer Routes

This module provides routes for the intelligent file organizer functionality
that categorizes and organizes CSV and Excel files using machine learning techniques.
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
import os
import json
from utils.smart_file_organizer import organize_files, SmartFileOrganizer
import logging

# Configure logging
logger = logging.getLogger(__name__)

file_organizer = Blueprint('file_organizer', __name__, url_prefix='/file-organizer')

@file_organizer.route('/')
def index():
    """Display the file organizer dashboard"""
    return render_template('file_organizer/index.html')

@file_organizer.route('/scan', methods=['POST'])
def scan_files():
    """Scan files in the source directory and return metadata"""
    source_dir = request.form.get('source_dir', 'attached_assets')
    
    try:
        organizer = SmartFileOrganizer(source_dir)
        metadata = organizer.scan_files()
        
        # Convert to serializable format
        result = {
            'status': 'success',
            'file_count': len(metadata),
            'files': [
                {
                    'path': path,
                    'filename': meta['filename'],
                    'size': meta['size'],
                    'modified': meta['modified']
                }
                for path, meta in metadata.items()
            ][:100]  # Limit to first 100 for performance
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error scanning files: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@file_organizer.route('/analyze', methods=['POST'])
def analyze_files():
    """Analyze files and categorize them"""
    source_dir = request.form.get('source_dir', 'attached_assets')
    
    try:
        organizer = SmartFileOrganizer(source_dir)
        organizer.scan_files()
        metadata = organizer.analyze_files()
        
        # Convert to serializable format
        categories = {}
        for path, meta in metadata.items():
            category = meta['category'] or 'uncategorized'
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                'path': path,
                'filename': meta['filename'],
                'date': meta['date']
            })
        
        result = {
            'status': 'success',
            'categories': {
                category: len(files) 
                for category, files in categories.items()
            },
            'sample_files': {
                category: files[:5]  # First 5 files of each category
                for category, files in categories.items()
            }
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error analyzing files: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@file_organizer.route('/organize', methods=['POST'])
def organize():
    """Organize files into a structured directory"""
    source_dir = request.form.get('source_dir', 'attached_assets')
    target_dir = request.form.get('target_dir', 'organized_data')
    create_symlinks = request.form.get('create_symlinks', 'false').lower() == 'true'
    
    try:
        # Run the organization process
        report = organize_files(
            source_dir=source_dir,
            target_dir=target_dir,
            create_symlinks=create_symlinks
        )
        
        flash(f"Successfully organized {report['total_files']} files into {len(report['categories'])} categories", "success")
        return jsonify({
            'status': 'success',
            'report': report
        })
    except Exception as e:
        logger.error(f"Error organizing files: {str(e)}")
        flash(f"Error organizing files: {str(e)}", "error")
        return jsonify({'status': 'error', 'message': str(e)})

@file_organizer.route('/report')
def view_report():
    """View the organization report"""
    report_path = os.path.join('organized_data', 'organization_report.json')
    
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            report = json.load(f)
        return render_template('file_organizer/report.html', report=report)
    else:
        flash("No organization report found. Please run the organizer first.", "warning")
        return redirect(url_for('file_organizer.index'))