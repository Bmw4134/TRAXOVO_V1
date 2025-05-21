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

@historical_bp.route('/equipment-lifecycle')
# Temporarily remove login requirement for testing
# @login_required
def equipment_lifecycle():
    """Display interactive timeline visualization for equipment lifecycle"""
    tracker = HistoricalDataTracker(use_db=False)
    
    # Get the job list for filter dropdown
    job_list = [
        {"job_number": "2023-032", "name": "Highway 83 Expansion"},
        {"job_number": "2023-034", "name": "River Crossing Bridge"},
        {"job_number": "2024-016", "name": "Commercial Plaza Foundation"},
        {"job_number": "2024-019", "name": "Matagorda County Drainage"},
        {"job_number": "2024-025", "name": "Municipal Water Treatment Plant"},
        {"job_number": "2024-030", "name": "Warehouse Development Site"}
    ]
    
    # Get history and preprocess for timeline
    history = tracker.get_allocation_history(months=12)
    
    # Generate timeline data from the history
    timeline_data = []
    equipment_groups = []
    
    # Track unique equipment for groups
    equipment_ids = set()
    equipment_types = {}
    
    # Generate sample maintenance events
    maintenance_events = {
        "EX-65": [{"date": "2025-01-15", "type": "Scheduled Maintenance", "description": "Oil change and filter replacement"}],
        "LD-45": [{"date": "2025-02-03", "type": "Repair", "description": "Hydraulic line replacement"}],
        "DZ-31": [{"date": "2025-03-10", "type": "Inspection", "description": "Annual safety inspection and certification"}]
    }
    
    # Process each month's data
    item_id = 1
    for month, record in history.items():
        allocation_data = record.get('data', [])
        
        # Calculate month start/end dates
        month_parts = month.split()
        if len(month_parts) == 2:
            month_name = month_parts[0]
            year = month_parts[1]
            
            # Convert month name to number
            month_num = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
                         "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}
            
            if month_name in month_num:
                month_start = f"{year}-{month_num[month_name]:02d}-01"
                
                # Calculate end date (simplified)
                if month_num[month_name] == 12:
                    month_end = f"{int(year)+1}-01-01"
                else:
                    month_end = f"{year}-{month_num[month_name]+1:02d}-01"
                
                # Process each allocation record
                for item in allocation_data:
                    equipment_id = item.get('equipment_id')
                    if equipment_id:
                        # Add to unique equipment set
                        equipment_ids.add(equipment_id)
                        
                        # Store equipment type
                        equipment_types[equipment_id] = item.get('equipment_type', 'Unknown')
                        
                        # Create timeline item for this allocation
                        job_number = item.get('job_number', 'No Job')
                        job_name = item.get('job_name', '')
                        days = item.get('days', 0)
                        amount = item.get('amount', 0)
                        cost_code = item.get('cost_code', 'Unknown')
                        
                        # Create a timeline item
                        timeline_item = {
                            'id': str(item_id),
                            'group': equipment_id,
                            'start': month_start,
                            'end': month_end,
                            'content': job_number,
                            'equipment': equipment_id,
                            'equipmentType': item.get('equipment_type', 'Unknown'),
                            'jobNumber': job_number,
                            'jobName': job_name,
                            'days': days,
                            'amount': amount,
                            'costCode': cost_code,
                            'title': f"{equipment_id} - {job_number}<br>Days: {days}<br>Amount: ${amount:,.2f}"
                        }
                        
                        # Add job-specific styling
                        if "2023-032" in job_number:
                            timeline_item['style'] = "background-color: #4e73df; color: white;"
                        elif "2023-034" in job_number:
                            timeline_item['style'] = "background-color: #1cc88a; color: white;"
                        elif "2024-016" in job_number:
                            timeline_item['style'] = "background-color: #36b9cc; color: white;"
                        elif "2024-019" in job_number:
                            timeline_item['style'] = "background-color: #f6c23e; color: black;"
                        elif "2024-025" in job_number:
                            timeline_item['style'] = "background-color: #e74a3b; color: white;"
                        elif "2024-030" in job_number:
                            timeline_item['style'] = "background-color: #6f42c1; color: white;"
                        
                        # Add to the timeline data
                        timeline_data.append(timeline_item)
                        item_id += 1
    
    # Add maintenance events as markers
    for equipment_id, events in maintenance_events.items():
        for event in events:
            timeline_data.append({
                'id': str(item_id),
                'group': equipment_id,
                'start': event['date'],
                'content': '🔧',  # Wrench emoji as a visual indicator
                'type': 'point',  # Display as a point marker
                'title': f"{event['type']}<br>{event['description']}",
                'equipment': equipment_id,
                'maintenanceEvent': True,
                'eventType': event['type'],
                'eventDescription': event['description']
            })
            item_id += 1
    
    # Create timeline groups (one per equipment)
    for equipment_id in equipment_ids:
        equipment_groups.append({
            'id': equipment_id,
            'content': equipment_id,
            'title': equipment_types.get(equipment_id, 'Unknown')
        })
    
    # Sort equipment groups alphabetically
    equipment_groups.sort(key=lambda x: x['id'])
    
    # Add additional data for equipment details panel
    for item in timeline_data:
        if 'maintenanceEvent' not in item:  # Skip maintenance events
            equipment_id = item['equipment']
            
            # Aggregate data for this equipment across all months
            equipment_items = [i for i in timeline_data if i.get('equipment') == equipment_id and 'maintenanceEvent' not in i]
            
            # Calculate totals
            total_days = sum(i.get('days', 0) for i in equipment_items)
            total_amount = sum(i.get('amount', 0) for i in equipment_items)
            
            # Calculate utilization rate (simple version)
            total_possible_days = len(equipment_items) * 30  # Approximate
            utilization_rate = round((total_days / total_possible_days) * 100 if total_possible_days > 0 else 0)
            
            # Job allocation
            job_allocation = {}
            for i in equipment_items:
                job_num = i.get('jobNumber')
                if job_num:
                    if job_num not in job_allocation:
                        job_allocation[job_num] = {
                            'days': 0,
                            'amount': 0,
                            'name': i.get('jobName', '')
                        }
                    job_allocation[job_num]['days'] += i.get('days', 0)
                    job_allocation[job_num]['amount'] += i.get('amount', 0)
            
            # Calculate percentages
            for job in job_allocation:
                percentage = round((job_allocation[job]['days'] / total_days) * 100) if total_days > 0 else 0
                job_allocation[job]['percentage'] = percentage
            
            # Cost code distribution
            cost_codes = {}
            for i in equipment_items:
                code = i.get('costCode')
                if code:
                    amount = i.get('amount', 0)
                    if code in cost_codes:
                        cost_codes[code] += amount
                    else:
                        cost_codes[code] = amount
            
            # Monthly trend data
            monthly_trend = {}
            for i in equipment_items:
                # Extract month from start date
                start_date = i.get('start', '')
                if start_date:
                    parts = start_date.split('-')
                    if len(parts) >= 2:
                        month_num = int(parts[1])
                        year = parts[0]
                        
                        # Convert month number to name
                        month_names = ["January", "February", "March", "April", "May", "June",
                                      "July", "August", "September", "October", "November", "December"]
                        
                        if 1 <= month_num <= 12:
                            month_year = f"{month_names[month_num-1]} {year}"
                            
                            if month_year not in monthly_trend:
                                monthly_trend[month_year] = {'days': 0, 'amount': 0}
                            
                            monthly_trend[month_year]['days'] += i.get('days', 0)
                            monthly_trend[month_year]['amount'] += i.get('amount', 0)
            
            # Add the aggregated data to the item
            item['totalDays'] = total_days
            item['totalAmount'] = total_amount
            item['utilizationRate'] = utilization_rate
            item['jobAllocation'] = job_allocation
            item['costCodes'] = cost_codes
            item['monthlyTrend'] = monthly_trend
    
    # Default date range
    start_date = "2024-11-01"  # November 2024
    end_date = "2025-04-30"    # April 2025
    
    return render_template('historical/equipment_lifecycle.html',
                          timeline_data=timeline_data,
                          equipment_groups=equipment_groups,
                          jobs=job_list,
                          start_date=start_date,
                          end_date=end_date)

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
@historical_analysis_bp.route('/')
def index():
    """Handler for /"""
    try:
        # Add your route handler logic here
        return render_template('historical_analysis/index.html')
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return render_template('error.html', error=str(e)), 500

@historical_analysis_bp.route('/equipment/<equipment_id>')
def equipment_<equipment_id>():
    """Handler for /equipment/<equipment_id>"""
    try:
        # Add your route handler logic here
        return render_template('historical_analysis/equipment_<equipment_id>.html')
    except Exception as e:
        logger.error(f"Error in equipment_<equipment_id>: {e}")
        return render_template('error.html', error=str(e)), 500

@historical_analysis_bp.route('/job/<job_number>')
def job_<job_number>():
    """Handler for /job/<job_number>"""
    try:
        # Add your route handler logic here
        return render_template('historical_analysis/job_<job_number>.html')
    except Exception as e:
        logger.error(f"Error in job_<job_number>: {e}")
        return render_template('error.html', error=str(e)), 500

@historical_analysis_bp.route('/equipment-lifecycle')
def equipment_lifecycle():
    """Handler for /equipment-lifecycle"""
    try:
        # Add your route handler logic here
        return render_template('historical_analysis/equipment_lifecycle.html')
    except Exception as e:
        logger.error(f"Error in equipment_lifecycle: {e}")
        return render_template('error.html', error=str(e)), 500

@historical_analysis_bp.route('/add-data')
def add_data():
    """Handler for /add-data"""
    try:
        # Add your route handler logic here
        return render_template('historical_analysis/add_data.html')
    except Exception as e:
        logger.error(f"Error in add_data: {e}")
        return render_template('error.html', error=str(e)), 500

@historical_analysis_bp.route('/compare-months')
def compare_months():
    """Handler for /compare-months"""
    try:
        # Add your route handler logic here
        return render_template('historical_analysis/compare_months.html')
    except Exception as e:
        logger.error(f"Error in compare_months: {e}")
        return render_template('error.html', error=str(e)), 500

@historical_analysis_bp.route('/export/<format>')
def export_<format>():
    """Handler for /export/<format>"""
    try:
        # Add your route handler logic here
        return render_template('historical_analysis/export_<format>.html')
    except Exception as e:
        logger.error(f"Error in export_<format>: {e}")
        return render_template('error.html', error=str(e)), 500
