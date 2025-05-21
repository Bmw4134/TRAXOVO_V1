"""
Asset Billing Module

This module handles routes for displaying and analyzing equipment billing data.
"""
from datetime import datetime
import calendar
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from sqlalchemy import func, desc, and_
from app import db
from models.reports import EquipmentBilling, Jobsite
from models import Asset

# Create blueprint
billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/billing', methods=['GET'])
@login_required
def billing_dashboard():
    """Display the equipment billing dashboard"""
    # Get query parameters
    year_str = request.args.get('year')
    month_str = request.args.get('month')
    category = request.args.get('category')
    jobsite_id = request.args.get('jobsite_id')
    
    # Set default date to current month/year if not provided
    today = datetime.today()
    
    try:
        year = int(year_str) if year_str else today.year
        month = int(month_str) if month_str else today.month
    except ValueError:
        year = today.year
        month = today.month
    
    # Build the base query
    query = db.session.query(
        EquipmentBilling,
        Asset
    ).join(
        Asset, EquipmentBilling.asset_id == Asset.id
    ).filter(
        EquipmentBilling.year == year,
        EquipmentBilling.month == month
    )
    
    # Apply filters if provided
    if category:
        query = query.filter(EquipmentBilling.category == category)
    
    if jobsite_id:
        query = query.filter(EquipmentBilling.jobsite_id == jobsite_id)
    
    # Order by total amount descending
    query = query.order_by(desc(EquipmentBilling.total_amount))
    
    # Execute query
    billing_records = query.all()
    
    # Get all categories and jobsites for filter dropdowns
    categories = db.session.query(
        EquipmentBilling.category
    ).distinct().order_by(EquipmentBilling.category).all()
    
    jobsites = Jobsite.query.order_by(Jobsite.name).all()
    
    # Calculate summary statistics
    total_amount = sum(record[0].total_amount or 0 for record in billing_records)
    total_hours = sum(record[0].hours_used or 0 for record in billing_records)
    avg_rate = total_amount / total_hours if total_hours > 0 else 0
    
    # Group by category
    category_stats = db.session.query(
        EquipmentBilling.category,
        func.sum(EquipmentBilling.total_amount).label('total_amount'),
        func.sum(EquipmentBilling.hours_used).label('total_hours'),
        func.count(EquipmentBilling.id).label('record_count')
    ).filter(
        EquipmentBilling.year == year,
        EquipmentBilling.month == month
    ).group_by(
        EquipmentBilling.category
    ).order_by(
        func.sum(EquipmentBilling.total_amount).desc()
    ).all()
    
    # Get all available months for navigation
    available_months = db.session.query(
        EquipmentBilling.year,
        EquipmentBilling.month
    ).distinct().order_by(
        EquipmentBilling.year.desc(),
        EquipmentBilling.month.desc()
    ).all()
    
    return render_template(
        'billing/dashboard.html',
        billing_records=billing_records,
        categories=[c.category for c in categories if c.category],
        jobsites=jobsites,
        year=year,
        month=month,
        selected_category=category,
        selected_jobsite_id=jobsite_id,
        available_months=available_months,
        month_name=calendar.month_name[month],
        stats={
            'total_amount': total_amount,
            'total_hours': total_hours,
            'avg_rate': avg_rate,
            'record_count': len(billing_records)
        },
        category_stats=category_stats
    )

@billing_bp.route('/billing/api/monthly-trend', methods=['GET'])
@login_required
def monthly_trend_api():
    """API endpoint for monthly billing trend data"""
    # Get query parameters
    category = request.args.get('category')
    limit = int(request.args.get('limit', 12))  # Default to 12 months
    
    # Build base query
    query = db.session.query(
        EquipmentBilling.year,
        EquipmentBilling.month,
        func.sum(EquipmentBilling.total_amount).label('total_amount'),
        func.sum(EquipmentBilling.hours_used).label('total_hours')
    ).group_by(
        EquipmentBilling.year,
        EquipmentBilling.month
    ).order_by(
        EquipmentBilling.year.desc(),
        EquipmentBilling.month.desc()
    ).limit(limit)
    
    # Apply category filter if provided
    if category:
        query = query.filter(EquipmentBilling.category == category)
    
    # Execute query
    monthly_data = query.all()
    
    # Format for chart display
    result = {
        'labels': [f"{row.year}-{row.month:02d}" for row in monthly_data],
        'total_amounts': [float(row.total_amount or 0) for row in monthly_data],
        'total_hours': [float(row.total_hours or 0) for row in monthly_data],
        'avg_rates': [
            float(row.total_amount or 0) / float(row.total_hours or 1) 
            for row in monthly_data
        ]
    }
    
    return jsonify(result)

@billing_bp.route('/billing/api/asset-comparison', methods=['GET'])
@login_required
def asset_comparison_api():
    """API endpoint for asset billing comparison data"""
    # Get query parameters
    year_str = request.args.get('year')
    month_str = request.args.get('month')
    category = request.args.get('category')
    limit = int(request.args.get('limit', 10))  # Default to top 10
    
    # Set default date to current month/year if not provided
    today = datetime.today()
    
    try:
        year = int(year_str) if year_str else today.year
        month = int(month_str) if month_str else today.month
    except ValueError:
        year = today.year
        month = today.month
    
    # Build the base query
    query = db.session.query(
        Asset.asset_identifier,
        Asset.asset_model,
        Asset.asset_category,
        func.sum(EquipmentBilling.total_amount).label('total_amount'),
        func.sum(EquipmentBilling.hours_used).label('total_hours'),
        func.avg(EquipmentBilling.rate).label('avg_rate')
    ).join(
        EquipmentBilling, Asset.id == EquipmentBilling.asset_id
    ).filter(
        EquipmentBilling.year == year,
        EquipmentBilling.month == month
    ).group_by(
        Asset.id,
        Asset.asset_identifier,
        Asset.asset_model,
        Asset.asset_category
    ).order_by(
        func.sum(EquipmentBilling.total_amount).desc()
    ).limit(limit)
    
    # Apply category filter if provided
    if category:
        query = query.filter(EquipmentBilling.category == category)
    
    # Execute query
    asset_data = query.all()
    
    # Format for chart display
    result = {
        'asset_ids': [asset.asset_identifier for asset in asset_data],
        'asset_models': [asset.asset_model for asset in asset_data],
        'total_amounts': [float(asset.total_amount or 0) for asset in asset_data],
        'total_hours': [float(asset.total_hours or 0) for asset in asset_data],
        'avg_rates': [float(asset.avg_rate or 0) for asset in asset_data]
    }
    
    return jsonify(result)
@billing_bp.route('/billing')
def billing():
    """Handler for /billing"""
    try:
        # Add your route handler logic here
        return render_template('billing/billing.html')
    except Exception as e:
        logger.error(f"Error in billing: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_bp.route('/billing/api/monthly-trend')
def billing_api_monthly_trend():
    """Handler for /billing/api/monthly-trend"""
    try:
        # Add your route handler logic here
        return render_template('billing/billing_api_monthly_trend.html')
    except Exception as e:
        logger.error(f"Error in billing_api_monthly_trend: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_bp.route('/billing/api/asset-comparison')
def billing_api_asset_comparison():
    """Handler for /billing/api/asset-comparison"""
    try:
        # Add your route handler logic here
        return render_template('billing/billing_api_asset_comparison.html')
    except Exception as e:
        logger.error(f"Error in billing_api_asset_comparison: {e}")
        return render_template('error.html', error=str(e)), 500
