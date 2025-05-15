"""
Fuel Management Module

This module handles the parsing and analysis of fuel transaction data,
primarily from WEX fuel card reports.
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user

from utils.file_processor import process_file, get_all_processors
from utils.fuel_processor import (
    process_wex_file, 
    generate_mpg_report, 
    generate_refueling_report,
    get_latest_fuel_data
)

fuel_bp = Blueprint('fuel', __name__, url_prefix='/fuel')
logger = logging.getLogger(__name__)

@fuel_bp.route('/')
@login_required
def index():
    """Render the fuel management dashboard"""
    return render_template('fuel/index.html', 
                          title="Fuel Management",
                          latest_data=get_latest_fuel_data())

@fuel_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle fuel data file uploads"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file:
            try:
                # Create uploads directory if it doesn't exist
                uploads_dir = os.path.join(current_app.root_path, 'uploads')
                if not os.path.exists(uploads_dir):
                    os.makedirs(uploads_dir)
                
                # Save the file
                file_path = os.path.join(uploads_dir, file.filename)
                file.save(file_path)
                
                # Process the file
                result = process_file(file_path, processor_type='fuel')
                
                if result['status'] == 'success':
                    flash(f'File processed successfully: {result["message"]}', 'success')
                    return redirect(url_for('fuel.index'))
                else:
                    flash(f'Error processing file: {result["message"]}', 'danger')
            except Exception as e:
                logger.error(f"Error processing fuel file: {e}")
                flash(f'Error processing file: {str(e)}', 'danger')
        
    return render_template('fuel/upload.html', 
                          title="Upload Fuel Data",
                          processors=get_all_processors(type='fuel'))

@fuel_bp.route('/mpg')
@login_required
def mpg_analysis():
    """Render MPG analysis page"""
    return render_template('fuel/mpg.html', 
                          title="MPG Analysis")

@fuel_bp.route('/mpg/report', methods=['POST'])
@login_required
def generate_mpg():
    """Generate MPG report based on date range"""
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')
    
    if not start_date or not end_date:
        flash('Please provide valid start and end dates', 'danger')
        return redirect(url_for('fuel.mpg_analysis'))
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        report = generate_mpg_report(start_date, end_date)
        
        if report['status'] == 'success':
            return send_file(report['file_path'], 
                           mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           as_attachment=True,
                           download_name=f'mpg_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.xlsx')
        else:
            flash(f'Error generating MPG report: {report["message"]}', 'danger')
            return redirect(url_for('fuel.mpg_analysis'))
    except Exception as e:
        logger.error(f"Error generating MPG report: {e}")
        flash(f'Error generating MPG report: {str(e)}', 'danger')
        return redirect(url_for('fuel.mpg_analysis'))

@fuel_bp.route('/refueling')
@login_required
def refueling_analysis():
    """Render job site refueling analysis page"""
    return render_template('fuel/refueling.html', 
                          title="Job Site Refueling Analysis")

@fuel_bp.route('/refueling/report', methods=['POST'])
@login_required
def generate_refueling():
    """Generate job site refueling report"""
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')
    
    if not start_date or not end_date:
        flash('Please provide valid start and end dates', 'danger')
        return redirect(url_for('fuel.refueling_analysis'))
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        report = generate_refueling_report(start_date, end_date)
        
        if report['status'] == 'success':
            return send_file(report['file_path'], 
                           mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           as_attachment=True,
                           download_name=f'refueling_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.xlsx')
        else:
            flash(f'Error generating refueling report: {report["message"]}', 'danger')
            return redirect(url_for('fuel.refueling_analysis'))
    except Exception as e:
        logger.error(f"Error generating refueling report: {e}")
        flash(f'Error generating refueling report: {str(e)}', 'danger')
        return redirect(url_for('fuel.refueling_analysis'))

@fuel_bp.route('/api/fuel_transactions')
@login_required
def api_fuel_transactions():
    """API endpoint to get fuel transaction data"""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    if not start_date or not end_date:
        return jsonify({'status': 'error', 'message': 'Missing required date parameters'})
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get fuel transactions from database
        from models import FuelTransaction
        transactions = FuelTransaction.query.filter(
            FuelTransaction.transaction_date.between(start_date, end_date)
        ).order_by(FuelTransaction.transaction_date.desc()).all()
        
        # Convert to list of dictionaries
        transaction_data = []
        for tx in transactions:
            transaction_data.append({
                'id': tx.id,
                'asset_id': tx.asset_id,
                'asset_identifier': tx.asset.asset_identifier if tx.asset else 'Unknown',
                'driver': tx.driver,
                'transaction_date': tx.transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
                'gallons': tx.gallons,
                'fuel_type': tx.fuel_type,
                'location': tx.location,
                'odometer': tx.odometer,
                'price_per_gallon': tx.price_per_gallon,
                'total_amount': tx.total_amount,
                'card_number': tx.card_number
            })
        
        return jsonify({
            'status': 'success',
            'transactions': transaction_data
        })
    except Exception as e:
        logger.error(f"Error fetching fuel transactions: {e}")
        return jsonify({'status': 'error', 'message': str(e)})