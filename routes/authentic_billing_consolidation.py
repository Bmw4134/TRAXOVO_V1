"""
AUTHENTIC BILLING CONSOLIDATION ROUTE
Complete Jan-April 2025 RAGLE + SELECT billing dashboard
Using all chat history mapping and authentic file data
"""

from flask import Blueprint, render_template, jsonify, request
import logging
from consolidated_billing_processor import ConsolidatedBillingProcessor
import pandas as pd
import os

authentic_billing_bp = Blueprint('authentic_billing', __name__)

@authentic_billing_bp.route('/authentic-billing-dashboard')
def authentic_billing_dashboard():
    """Main authentic billing dashboard with all consolidated data"""
    processor = ConsolidatedBillingProcessor()
    
    # Process all authentic files
    consolidated_metrics = processor.process_authentic_billing_files()
    monthly_breakdown = processor.get_monthly_breakdown()
    
    # Calculate additional insights
    ytd_growth = calculate_ytd_growth(monthly_breakdown)
    company_comparison = calculate_company_comparison(processor)
    
    return render_template('authentic_billing_dashboard.html',
                         metrics=consolidated_metrics,
                         monthly_breakdown=monthly_breakdown,
                         ytd_growth=ytd_growth,
                         company_comparison=company_comparison)

@authentic_billing_bp.route('/api/authentic-billing-data')
def api_authentic_billing_data():
    """API endpoint for authentic billing data"""
    processor = ConsolidatedBillingProcessor()
    consolidated_metrics = processor.process_authentic_billing_files()
    monthly_breakdown = processor.get_monthly_breakdown()
    
    return jsonify({
        'status': 'success',
        'metrics': consolidated_metrics,
        'monthly_breakdown': monthly_breakdown,
        'data_source': 'authentic_files_foundation_aligned'
    })

@authentic_billing_bp.route('/api/revenue-comparison')
def api_revenue_comparison():
    """Compare RAGLE vs SELECT revenue breakdown"""
    processor = ConsolidatedBillingProcessor()
    processor.process_authentic_billing_files()
    
    ragle_total = sum(data['revenue'] for data in processor.ragle_data.values())
    select_total = sum(data['revenue'] for data in processor.select_data.values())
    
    comparison_data = {
        'ragle': {
            'total': ragle_total,
            'percentage': (ragle_total / (ragle_total + select_total)) * 100,
            'assets': processor.consolidated_metrics.get('ragle_assets', 0),
            'monthly_data': {period: data['revenue'] for period, data in processor.ragle_data.items()}
        },
        'select': {
            'total': select_total,
            'percentage': (select_total / (ragle_total + select_total)) * 100,
            'assets': processor.consolidated_metrics.get('select_assets', 0),
            'monthly_data': {period: data['revenue'] for period, data in processor.select_data.items()}
        }
    }
    
    return jsonify(comparison_data)

def calculate_ytd_growth(monthly_breakdown):
    """Calculate year-to-date growth trends"""
    months = ['january_2025', 'february_2025', 'march_2025', 'april_2025']
    
    growth_data = []
    prev_total = 0
    
    for month in months:
        current_total = monthly_breakdown.get(month, {}).get('total', 0)
        
        if prev_total > 0:
            growth_rate = ((current_total - prev_total) / prev_total) * 100
        else:
            growth_rate = 0
        
        growth_data.append({
            'month': month.replace('_2025', '').title(),
            'total': current_total,
            'growth_rate': growth_rate
        })
        
        prev_total = current_total
    
    return growth_data

def calculate_company_comparison(processor):
    """Calculate detailed company performance comparison"""
    ragle_monthly_avg = sum(data['revenue'] for data in processor.ragle_data.values()) / len(processor.ragle_data)
    select_monthly_avg = sum(data['revenue'] for data in processor.select_data.values()) / len(processor.select_data)
    
    ragle_asset_utilization = ragle_monthly_avg / processor.consolidated_metrics.get('ragle_assets', 1)
    select_asset_utilization = select_monthly_avg / processor.consolidated_metrics.get('select_assets', 1)
    
    return {
        'ragle': {
            'monthly_average': ragle_monthly_avg,
            'asset_utilization': ragle_asset_utilization,
            'total_assets': processor.consolidated_metrics.get('ragle_assets', 0)
        },
        'select': {
            'monthly_average': select_monthly_avg,
            'asset_utilization': select_asset_utilization,
            'total_assets': processor.consolidated_metrics.get('select_assets', 0)
        },
        'performance_ratio': ragle_monthly_avg / select_monthly_avg if select_monthly_avg > 0 else 0
    }

# Register blueprint function
def register_authentic_billing_routes(app):
    """Register authentic billing routes with the main app"""
    app.register_blueprint(authentic_billing_bp)
    logging.info("Authentic billing consolidation routes registered")