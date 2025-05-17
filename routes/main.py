"""
Main routes for the SYSTEMSMITH application
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
import os
from pathlib import Path

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@main_bp.route('/assets')
@login_required
def assets():
    """Render the assets page"""
    return render_template('assets.html')

# Add more routes as needed from main.py