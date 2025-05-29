
"""
Equipment Analytics Routes for TRAXOVO
Web interface for equipment utilization and cost analysis
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
import logging
from utils.equipment_analytics_processor import get_equipment_analytics_processor

logger = logging.getLogger(__name__)

equipment_analytics_bp = Blueprint('equipment_analytics', __name__, url_prefix='/equipment-analytics')

@equipment_analytics_bp.route('/')
def dashboard():
    """Equipment analytics dashboard"""
    try:
        processor = get_equipment_analytics_processor()
        
        # Get analytics data
        utilization_analysis = processor.generate_utilization_analysis()
        cost_efficiency = processor.generate_cost_efficiency_report()
        recommendations = processor.generate_billing_optimization_recommendations()
        
        return render_template('equipment_analytics/dashboard.html',
                             utilization=utilization_analysis,
                             cost_efficiency=cost_efficiency,
                             recommendations=recommendations)
    except Exception as e:
        logger.error(f"Error in equipment analytics dashboard: {e}")
        flash(f'Error loading analytics: {str(e)}', 'danger')
        return redirect(url_for('index'))

@equipment_analytics_bp.route('/api/utilization-data')
def api_utilization_data():
    """API endpoint for utilization data"""
    try:
        processor = get_equipment_analytics_processor()
        utilization_analysis = processor.generate_utilization_analysis()
        return jsonify(utilization_analysis)
    except Exception as e:
        logger.error(f"Error getting utilization data: {e}")
        return jsonify({'error': str(e)}), 500

@equipment_analytics_bp.route('/api/cost-efficiency')
def api_cost_efficiency():
    """API endpoint for cost efficiency data"""
    try:
        processor = get_equipment_analytics_processor()
        cost_efficiency = processor.generate_cost_efficiency_report()
        return jsonify(cost_efficiency)
    except Exception as e:
        logger.error(f"Error getting cost efficiency data: {e}")
        return jsonify({'error': str(e)}), 500

@equipment_analytics_bp.route('/api/recommendations')
def api_recommendations():
    """API endpoint for optimization recommendations"""
    try:
        processor = get_equipment_analytics_processor()
        recommendations = processor.generate_billing_optimization_recommendations()
        return jsonify(recommendations)
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@equipment_analytics_bp.route('/api/maintenance-analytics')
def api_maintenance_analytics():
    """API endpoint for maintenance analytics"""
    try:
        processor = get_equipment_analytics_processor()
        maintenance_data = processor.generate_maintenance_analytics()
        return jsonify(maintenance_data)
    except Exception as e:
        logger.error(f"Error getting maintenance analytics: {e}")
        return jsonify({'error': str(e)}), 500

@equipment_analytics_bp.route('/api/predictive-insights')
def api_predictive_insights():
    """API endpoint for predictive maintenance insights"""
    try:
        processor = get_equipment_analytics_processor()
        insights = processor.generate_predictive_maintenance_insights()
        return jsonify(insights)
    except Exception as e:
        logger.error(f"Error getting predictive insights: {e}")
        return jsonify({'error': str(e)}), 500

@equipment_analytics_bp.route('/export')
def export_analytics():
    """Export analytics data"""
    try:
        processor = get_equipment_analytics_processor()
        dashboard_data, output_file = processor.export_analytics_dashboard_data()
        
        flash(f'Analytics exported to {output_file}', 'success')
        return jsonify({
            'success': True,
            'file': output_file,
            'data': dashboard_data
        })
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        return jsonify({'error': str(e)}), 500
