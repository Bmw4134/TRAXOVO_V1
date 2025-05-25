"""
Updated routes to register the file organizer blueprint.
"""

from routes.file_organizer_routes import file_organizer
import os
import json
import logging
from flask import jsonify

logger = logging.getLogger(__name__)

def register_file_organizer_blueprint(app):
    """Register the file organizer blueprint with the Flask app"""
    app.register_blueprint(file_organizer)
    logger.info("File Organizer blueprint registered successfully")
    
    # Add routes for quick organize
    @file_organizer.route('/quick-organize', methods=['POST'])
    def quick_organize():
        """Run the quick file organizer script"""
        from flask import request, flash, redirect, url_for
        import subprocess
        import sys
        
        source_dir = request.form.get('source_dir', 'attached_assets')
        target_dir = request.form.get('target_dir', 'weekly_report_files')
        
        try:
            # Run the quick file organizer script
            result = subprocess.run(
                [sys.executable, 'quick_file_organizer.py'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output to get the categories
            categories = {}
            for line in result.stdout.split('\n'):
                if line.startswith('- ') and ': ' in line:
                    parts = line.strip('- ').split(': ')
                    if len(parts) == 2:
                        category, count = parts
                        categories[category] = int(count.split(' ')[0])
            
            # Read summary file if it exists
            summary_path = os.path.join(target_dir, 'report_files_summary.txt')
            file_count = 0
            if os.path.exists(summary_path):
                with open(summary_path, 'r') as f:
                    for line in f:
                        if line.startswith('Weekly Report Files Organized:'):
                            try:
                                file_count = int(line.split(':')[1].strip())
                            except:
                                file_count = 0
            
            # Return success response
            return jsonify({
                'status': 'success',
                'message': 'Files organized successfully',
                'file_count': file_count,
                'categories': categories,
                'target_dir': target_dir
            })
        except Exception as e:
            logger.error(f"Error during quick organization: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
            
    return app