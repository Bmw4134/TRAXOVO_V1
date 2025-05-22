"""
TRAXORA | React File Upload Route

This module provides the route for the modern React-based file upload interface.
"""
from flask import Blueprint, render_template

# Create blueprint
react_upload_bp = Blueprint('react_upload', __name__, url_prefix='/react-upload')

@react_upload_bp.route('/', methods=['GET'])
def index():
    """Render the React file upload interface"""
    return render_template('react_upload/index.html')