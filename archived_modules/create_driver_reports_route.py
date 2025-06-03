"""
TRAXORA Fleet Management System - Driver Reports Dashboard Creator

This script creates a dedicated route for the enhanced driver reports dashboard
that matches the requested UI layout with 4 metric cards (On Time, Late, Early End, Not On Job)
and a collapsible sidebar.
"""
import os
import logging
from flask import Blueprint, render_template, flash

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_driver_reports_blueprint():
    """Create a dedicated blueprint for the driver reports dashboard"""
    # Create a new blueprint with a unique name
    bp = Blueprint('driver_reports_dashboard', __name__, url_prefix='/driver-dashboard')
    
    @bp.route('/')
    def dashboard():
        """Display the driver reports dashboard"""
        try:
            # Sample metrics for demonstration
            metrics = {
                'on_time': 15,
                'late': 8,
                'early_end': 5,
                'not_on_job': 3,
                'avg_late': 17,
                'avg_early_end': 25
            }
            
            # Sample reports
            reports = [
                {
                    'start_date': '2025-05-18',
                    'end_date': '2025-05-24',
                    'date_range': 'May 18 - May 24, 2025',
                    'summary': {
                        'on_time': 15,
                        'late': 8,
                        'early_end': 5,
                        'not_on_job': 3,
                        'total': 31
                    }
                }
            ]
            
            return render_template(
                'driver_reports_dashboard.html',
                metrics=metrics,
                reports=reports
            )
            
        except Exception as e:
            logger.error(f"Error displaying driver reports dashboard: {str(e)}")
            flash(f"Error displaying dashboard: {str(e)}", "danger")
            return render_template('error.html', error=str(e))
    
    return bp