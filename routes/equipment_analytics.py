"""
Equipment Analytics Routes for TRAXOVO
Web interface for equipment utilization and cost analysis
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, session, send_file
import logging
import os
from datetime import datetime
import json
import pandas as pd
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

@equipment_analytics_bp.route('/api/fleet-utilization')
def api_fleet_utilization():
    """API endpoint for Fleet Utilization data"""
    try:
        processor = get_equipment_analytics_processor()

        # Check if fleet utilization data is loaded
        if processor.fleet_utilization is not None:
            utilization_data = processor.fleet_utilization

            # Process the data for API response
            summary = {
                'total_assets': len(utilization_data),
                'columns': list(utilization_data.columns),
                'sample_data': utilization_data.head(10).to_dict('records') if len(utilization_data) > 0 else []
            }

            # Extract monthly utilization columns
            monthly_cols = [col for col in utilization_data.columns if any(month in str(col) for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May']) and '-25' in str(col)]

            if monthly_cols:
                summary['monthly_columns'] = monthly_cols
                summary['utilization_summary'] = {}

                for col in monthly_cols:
                    if col in utilization_data.columns:
                        numeric_data = pd.to_numeric(utilization_data[col], errors='coerce')
                        summary['utilization_summary'][col] = {
                            'total_hours': numeric_data.sum(),
                            'avg_hours': numeric_data.mean(),
                            'assets_used': (numeric_data > 0).sum()
                        }

            return jsonify(summary)
        else:
            return jsonify({'error': 'Fleet Utilization data not loaded'}), 404

    except Exception as e:
        logger.error(f"Error getting fleet utilization data: {e}")
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

@equipment_analytics_bp.route('/upload-fleet-utilization', methods=['POST'])
def upload_fleet_utilization():
    """Handle Fleet Utilization report upload and processing"""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('equipment_analytics.dashboard'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('equipment_analytics.dashboard'))

    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            # Save uploaded file with timestamp
            os.makedirs('uploads', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"fleet_utilization_gauge_{timestamp}.xlsx"
            filepath = os.path.join('uploads', filename)
            file.save(filepath)

            # Process the Fleet Utilization data (handles 2-sheet structure)
            from utils.equipment_analytics_processor import process_fleet_utilization_report
            utilization_data = process_fleet_utilization_report(filepath)

            if 'error' in utilization_data:
                flash(f'❌ Error processing Fleet Utilization: {utilization_data["error"]}', 'error')
                return redirect(url_for('equipment_analytics.dashboard'))

            # Success message with key metrics
            success_msg = (f'🎯 GAUGE FLEET UTILIZATION PROCESSED SUCCESSFULLY!\n'
                          f'📊 {utilization_data["total_assets"]} Total Assets\n'
                          f'🟢 {utilization_data["active_assets"]} Active Assets\n'
                          f'🔴 {utilization_data["idle_assets"]} Idle Assets\n'
                          f'⚡ {utilization_data["avg_utilization"]:.1f}% Average Utilization\n'
                          f'🏆 {len(utilization_data["top_performers"])} Top Performers (>75%)\n'
                          f'⚠️ {len(utilization_data["underutilized_assets"])} Underutilized (<25%)')

            flash(success_msg, 'success')

            # Store processed data for dashboard display and analytics
            session['fleet_utilization_data'] = utilization_data

            # Also save to file for persistence
            output_file = os.path.join('uploads', f'fleet_utilization_processed_{timestamp}.json')
            with open(output_file, 'w') as f:
                json.dump(utilization_data, f, indent=2, default=str)

            logger.info(f"Fleet Utilization data saved to: {output_file}")

        except Exception as e:
            error_msg = f'❌ Error processing Fleet Utilization report: {str(e)}'
            flash(error_msg, 'error')
            logger.error(error_msg)
    else:
        flash('Please upload an Excel file (.xlsx or .xls)', 'error')

    return redirect(url_for('equipment_analytics.dashboard'))

@equipment_analytics_bp.route('/fleet-utilization-details')
def fleet_utilization_details():
    """Display detailed Fleet Utilization analytics"""
    utilization_data = session.get('fleet_utilization_data')

    if not utilization_data:
        flash('No Fleet Utilization data available. Please upload a report first.', 'warning')
        return redirect(url_for('equipment_analytics.dashboard'))

    # Prepare data for detailed view
    category_summary = utilization_data.get('summary_by_category', {})
    top_performers = utilization_data.get('top_performers', [])[:10]  # Top 10
    underutilized = utilization_data.get('underutilized_assets', [])[:10]  # Bottom 10

    return render_template('equipment_analytics/fleet_utilization_details.html',
                         utilization_data=utilization_data,
                         category_summary=category_summary,
                         top_performers=top_performers,
                         underutilized=underutilized)

@equipment_analytics_bp.route('/export-fleet-utilization')
def export_fleet_utilization():
    """Export Fleet Utilization data to CSV"""
    utilization_data = session.get('fleet_utilization_data')

    if not utilization_data:
        flash('No Fleet Utilization data to export', 'error')
        return redirect(url_for('equipment_analytics.dashboard'))

    try:
        # Create DataFrame from asset details
        df = pd.DataFrame(utilization_data['asset_details'])

        # Add summary information
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_filename = f'fleet_utilization_export_{timestamp}.csv'
        export_path = os.path.join('static', 'exports', export_filename)

        # Ensure exports directory exists
        os.makedirs(os.path.dirname(export_path), exist_ok=True)

        # Save CSV
        df.to_csv(export_path, index=False)

        flash(f'✅ Fleet Utilization data exported to {export_filename}', 'success')

        # Return file for download
        return send_file(export_path, as_attachment=True, download_name=export_filename)

    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'error')
        return redirect(url_for('equipment_analytics.dashboard'))