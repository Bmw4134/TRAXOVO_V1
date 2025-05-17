"""
Historical Data Analysis Routes

This module provides routes for accessing and visualizing historical
PM allocation data, generating trend analysis, and forecasting.
"""

from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
import pandas as pd
import logging
import json
from datetime import datetime
from pathlib import Path
import os

from utils.historical_tracker import HistoricalDataTracker

# Set up number formatting filter for templates
def format_number(value):
    """Format a number with commas as thousands separators"""
    try:
        return "{:,}".format(value)
    except (ValueError, TypeError):
        return value

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
historical_bp = Blueprint('historical', __name__, url_prefix='/historical')

# Register custom template filters
@historical_bp.app_template_filter('format_number')
def format_number_filter(value):
    return format_number(value)

@historical_bp.route('/')
# Temporarily remove login requirement for testing
# @login_required
def historical_dashboard():
    """Display historical data dashboard"""
    # Import and generate sample data for testing
    from utils.sample_data import generate_sample_data
    import logging
    
    # Generate sample data if needed
    logging.info("Generating sample data for historical analysis")
    generate_sample_data()
    
    # Create tracker and get history
    tracker = HistoricalDataTracker(use_db=False)  # Explicitly use file-based storage
    
    # Get the last 6 months of history
    history = tracker.get_allocation_history(months=6)
    
    # Generate summary report
    summary = tracker.generate_summary_report(months=6)
    
    # Extract key metrics for display
    metrics = {
        'total_records': summary.get('total_equipment_count', 0),
        'total_jobs': summary.get('total_job_count', 0),
        'months_analyzed': summary.get('months_analyzed', 0)
    }
    
    # Extract trend indicators
    trends = summary.get('trend_indicators', {})
    
    # Extract forecasts
    forecasts = summary.get('forecasts', {})
    
    # Get chart path if available
    chart_path = summary.get('chart_path')
    
    # Get top equipment and jobs
    top_equipment = summary.get('top_equipment', [])[:5]  # Top 5
    top_jobs = summary.get('top_jobs', [])[:5]  # Top 5
    
    return render_template('historical/dashboard.html',
                          metrics=metrics,
                          trends=trends,
                          forecasts=forecasts,
                          top_equipment=top_equipment,
                          top_jobs=top_jobs,
                          chart_path=chart_path,
                          history=history)

@historical_bp.route('/equipment/<equipment_id>')
# Temporarily remove login requirement for testing
# @login_required
def equipment_trend(equipment_id):
    """Display trend analysis for a specific equipment"""
    tracker = HistoricalDataTracker()
    
    # Generate trend analysis for this equipment
    trend_data = tracker.generate_equipment_usage_trend(equipment_id=equipment_id)
    
    # Equipment details (could be fetched from database if available)
    equipment_details = {
        'id': equipment_id,
        'type': 'Unknown',  # Would be fetched from database
        'status': 'Active'  # Would be fetched from database
    }
    
    return render_template('historical/equipment_trend.html',
                          equipment=equipment_details,
                          trend_data=trend_data)

@historical_bp.route('/job/<job_number>')
# Temporarily remove login requirement for testing
# @login_required
def job_trend(job_number):
    """Display trend analysis for a specific job"""
    tracker = HistoricalDataTracker()
    
    # Generate trend analysis for this job
    trend_data = tracker.generate_equipment_usage_trend(job_number=job_number)
    
    # Job details (could be fetched from database if available)
    job_details = {
        'number': job_number,
        'name': 'Unknown',  # Would be fetched from database
        'status': 'Active'  # Would be fetched from database
    }
    
    return render_template('historical/job_trend.html',
                          job=job_details,
                          trend_data=trend_data)

@historical_bp.route('/add-data', methods=['POST'])
@login_required
def add_historical_data():
    """Add historical data manually or from processed files"""
    tracker = HistoricalDataTracker()
    
    try:
        data = request.json
        month_year = data.get('month_year')
        allocation_data = data.get('data')
        metadata = data.get('metadata', {})
        
        success = tracker.add_allocation_data(month_year, allocation_data, metadata)
        
        if success:
            return jsonify({'status': 'success', 'message': f'Data for {month_year} added successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to add data'}), 500
            
    except Exception as e:
        logger.error(f"Error adding historical data: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@historical_bp.route('/compare-months', methods=['GET'])
@login_required
def compare_months():
    """Compare data between two months"""
    tracker = HistoricalDataTracker()
    
    month1 = request.args.get('month1')
    month2 = request.args.get('month2')
    
    if not month1 or not month2:
        return jsonify({'status': 'error', 'message': 'Two months must be specified'}), 400
    
    try:
        # Get history data
        history = tracker.get_allocation_history()
        
        if month1 not in history or month2 not in history:
            return jsonify({'status': 'error', 'message': 'One or both months not found in history'}), 404
            
        # Extract data for each month
        data1 = history[month1]['data']
        data2 = history[month2]['data']
        
        # Convert to DataFrames for easier comparison
        df1 = pd.DataFrame(data1)
        df2 = pd.DataFrame(data2)
        
        # Compare equipment counts
        equipment_count1 = len(df1['equipment_id'].unique()) if 'equipment_id' in df1.columns else 0
        equipment_count2 = len(df2['equipment_id'].unique()) if 'equipment_id' in df2.columns else 0
        
        # Compare job counts
        job_count1 = len(df1['job_number'].unique()) if 'job_number' in df1.columns else 0
        job_count2 = len(df2['job_number'].unique()) if 'job_number' in df2.columns else 0
        
        # Compare total amounts
        total_amount1 = df1['amount'].sum() if 'amount' in df1.columns else 0
        total_amount2 = df2['amount'].sum() if 'amount' in df2.columns else 0
        
        # Calculate changes
        equipment_change = equipment_count2 - equipment_count1
        job_change = job_count2 - job_count1
        amount_change = total_amount2 - total_amount1
        amount_change_pct = (amount_change / total_amount1 * 100) if total_amount1 > 0 else 0
        
        comparison = {
            'month1': month1,
            'month2': month2,
            'equipment_count1': equipment_count1,
            'equipment_count2': equipment_count2,
            'equipment_change': equipment_change,
            'job_count1': job_count1,
            'job_count2': job_count2,
            'job_change': job_change,
            'total_amount1': total_amount1,
            'total_amount2': total_amount2,
            'amount_change': amount_change,
            'amount_change_pct': amount_change_pct
        }
        
        return jsonify({'status': 'success', 'comparison': comparison})
        
    except Exception as e:
        logger.error(f"Error comparing months: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@historical_bp.route('/export/<format>')
@login_required
def export_history(format):
    """Export historical data in specified format"""
    tracker = HistoricalDataTracker()
    
    try:
        # Get all history
        history = tracker.get_allocation_history(months=12)  # Last 12 months
        
        if format == 'json':
            # Create a JSON file
            output_file = Path('exports') / f'history_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            os.makedirs(output_file.parent, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(history, f, indent=2)
                
            return send_file(output_file, as_attachment=True)
            
        elif format == 'csv':
            # Create a CSV file with flattened data
            output_file = Path('exports') / f'history_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            os.makedirs(output_file.parent, exist_ok=True)
            
            # Flatten the nested structure
            flattened_data = []
            for month, record in history.items():
                for item in record.get('data', []):
                    item['month'] = month
                    flattened_data.append(item)
                    
            # Convert to DataFrame and save as CSV
            df = pd.DataFrame(flattened_data)
            df.to_csv(output_file, index=False)
            
            return send_file(output_file, as_attachment=True)
            
        elif format == 'excel':
            # Create an Excel file with multiple sheets
            output_file = Path('exports') / f'history_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            os.makedirs(output_file.parent, exist_ok=True)
            
            with pd.ExcelWriter(output_file) as writer:
                # Summary sheet
                summary = tracker.generate_summary_report()
                summary_df = pd.DataFrame({
                    'Metric': ['Total Equipment', 'Total Jobs', 'Months Analyzed'],
                    'Value': [
                        summary.get('total_equipment_count', 0),
                        summary.get('total_job_count', 0),
                        summary.get('months_analyzed', 0)
                    ]
                })
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Monthly sheets
                for month, record in history.items():
                    # Convert record data to DataFrame
                    month_df = pd.DataFrame(record.get('data', []))
                    if not month_df.empty:
                        # Clean sheet name (remove special characters)
                        sheet_name = month.replace(' ', '_')[:31]  # Excel limits sheet names to 31 chars
                        month_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return send_file(output_file, as_attachment=True)
            
        else:
            return jsonify({'status': 'error', 'message': f'Unsupported format: {format}'}), 400
            
    except Exception as e:
        logger.error(f"Error exporting history: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def register_blueprint(app):
    """Register the historical blueprint with the app"""
    app.register_blueprint(historical_bp)
    logger.info('Registered historical analysis blueprint')
    return historical_bp