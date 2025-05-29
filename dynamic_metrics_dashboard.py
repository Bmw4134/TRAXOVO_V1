"""
Dynamic Metrics Dashboard with Interactive Charts
Executive-level visual analytics with drill-down capabilities and time period toggles
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
import json

metrics_bp = Blueprint('dynamic_metrics', __name__)

class DynamicMetricsEngine:
    """Dynamic metrics with time period controls and visual charts"""
    
    def __init__(self):
        self.load_metrics_data()
    
    def load_metrics_data(self):
        """Load comprehensive metrics data"""
        # Generate sample time series data for demonstration
        dates = pd.date_range(start='2024-01-01', end='2025-05-29', freq='D')
        
        self.metrics_data = pd.DataFrame({
            'date': dates,
            'revenue': np.random.normal(85000, 15000, len(dates)).cumsum(),
            'costs': np.random.normal(45000, 8000, len(dates)).cumsum(),
            'utilization': np.random.normal(75, 10, len(dates)),
            'fuel_costs': np.random.normal(12000, 2000, len(dates)),
            'maintenance_costs': np.random.normal(8000, 1500, len(dates)),
            'equipment_efficiency': np.random.normal(82, 8, len(dates)),
            'driver_productivity': np.random.normal(78, 12, len(dates))
        })
        
        # Ensure realistic bounds
        self.metrics_data['utilization'] = np.clip(self.metrics_data['utilization'], 20, 100)
        self.metrics_data['equipment_efficiency'] = np.clip(self.metrics_data['equipment_efficiency'], 40, 100)
        self.metrics_data['driver_productivity'] = np.clip(self.metrics_data['driver_productivity'], 30, 100)
    
    def get_metrics_by_period(self, period='daily', start_date=None, end_date=None):
        """Get metrics aggregated by time period"""
        df = self.metrics_data.copy()
        
        # Filter by date range if provided
        if start_date:
            df = df[df['date'] >= start_date]
        if end_date:
            df = df[df['date'] <= end_date]
        
        # Aggregate by period
        if period == 'weekly':
            df['period'] = df['date'].dt.to_period('W')
            grouped = df.groupby('period').agg({
                'revenue': 'sum',
                'costs': 'sum',
                'utilization': 'mean',
                'fuel_costs': 'sum',
                'maintenance_costs': 'sum',
                'equipment_efficiency': 'mean',
                'driver_productivity': 'mean'
            }).reset_index()
            grouped['period_label'] = grouped['period'].astype(str)
            
        elif period == 'monthly':
            df['period'] = df['date'].dt.to_period('M')
            grouped = df.groupby('period').agg({
                'revenue': 'sum',
                'costs': 'sum',
                'utilization': 'mean',
                'fuel_costs': 'sum',
                'maintenance_costs': 'sum',
                'equipment_efficiency': 'mean',
                'driver_productivity': 'mean'
            }).reset_index()
            grouped['period_label'] = grouped['period'].astype(str)
            
        elif period == 'quarterly':
            df['period'] = df['date'].dt.to_period('Q')
            grouped = df.groupby('period').agg({
                'revenue': 'sum',
                'costs': 'sum',
                'utilization': 'mean',
                'fuel_costs': 'sum',
                'maintenance_costs': 'sum',
                'equipment_efficiency': 'mean',
                'driver_productivity': 'mean'
            }).reset_index()
            grouped['period_label'] = grouped['period'].astype(str)
            
        else:  # daily
            grouped = df.copy()
            grouped['period_label'] = grouped['date'].dt.strftime('%Y-%m-%d')
        
        # Calculate derived metrics
        grouped['profit'] = grouped['revenue'] - grouped['costs']
        grouped['profit_margin'] = (grouped['profit'] / grouped['revenue']) * 100
        grouped['roi'] = (grouped['profit'] / grouped['costs']) * 100
        
        return grouped.to_dict('records')
    
    def get_equipment_forecasts(self, project_duration_months=6):
        """Generate equipment forecasts for new projects"""
        categories = ['Excavators', 'Pickup Trucks', 'Air Compressors', 'Specialty Equipment']
        
        forecasts = []
        for category in categories:
            base_utilization = np.random.uniform(70, 90)
            monthly_trend = np.random.uniform(-2, 3)  # % change per month
            
            monthly_forecasts = []
            for month in range(1, project_duration_months + 1):
                utilization = base_utilization + (monthly_trend * month)
                utilization = np.clip(utilization, 20, 100)
                
                monthly_forecasts.append({
                    'month': month,
                    'utilization': round(utilization, 1),
                    'estimated_revenue': int(np.random.uniform(15000, 45000)),
                    'estimated_costs': int(np.random.uniform(8000, 25000))
                })
            
            forecasts.append({
                'category': category,
                'current_fleet_size': np.random.randint(15, 45),
                'recommended_allocation': np.random.randint(8, 25),
                'confidence_level': round(np.random.uniform(82, 96), 1),
                'monthly_forecasts': monthly_forecasts
            })
        
        return forecasts
    
    def analyze_bid_performance(self):
        """Analyze bid vs actual performance (placeholder for Excel integration)"""
        # This will be enhanced when Excel files are integrated
        bid_analysis = {
            'total_bids_analyzed': 45,
            'win_rate': 68.2,
            'average_margin': 15.7,
            'underpriced_projects': [
                {
                    'project': '2024-089 Highway Expansion',
                    'bid_amount': 485000,
                    'actual_cost': 523000,
                    'variance': -38000,
                    'variance_percent': -7.8
                },
                {
                    'project': '2024-112 Bridge Repair',
                    'bid_amount': 295000,
                    'actual_cost': 318000,
                    'variance': -23000,
                    'variance_percent': -7.8
                }
            ],
            'profitable_projects': [
                {
                    'project': '2024-097 Site Preparation',
                    'bid_amount': 175000,
                    'actual_cost': 145000,
                    'variance': 30000,
                    'variance_percent': 17.1
                }
            ],
            'recommendations': [
                'Increase equipment allocation estimates by 8% for highway projects',
                'Factor in seasonal fuel cost variations',
                'Include 5% contingency for bridge/infrastructure work'
            ]
        }
        
        return bid_analysis

@metrics_bp.route('/dynamic-metrics')
def dynamic_metrics_dashboard():
    """Main dynamic metrics dashboard"""
    engine = DynamicMetricsEngine()
    
    # Get current period metrics
    current_metrics = engine.get_metrics_by_period('monthly')
    
    # Get equipment forecasts
    forecasts = engine.get_equipment_forecasts()
    
    # Get bid analysis
    bid_analysis = engine.analyze_bid_performance()
    
    return render_template('dynamic_metrics_dashboard.html',
                         current_metrics=current_metrics[-6:],  # Last 6 months
                         forecasts=forecasts,
                         bid_analysis=bid_analysis)

@metrics_bp.route('/api/metrics')
def api_metrics():
    """API endpoint for metrics with period filtering"""
    period = request.args.get('period', 'monthly')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    engine = DynamicMetricsEngine()
    metrics = engine.get_metrics_by_period(period, start_date, end_date)
    
    return jsonify({
        'metrics': metrics,
        'period': period,
        'count': len(metrics)
    })

@metrics_bp.route('/api/forecasts')
def api_forecasts():
    """API endpoint for equipment forecasts"""
    duration = int(request.args.get('duration', 6))
    
    engine = DynamicMetricsEngine()
    forecasts = engine.get_equipment_forecasts(duration)
    
    return jsonify({
        'forecasts': forecasts,
        'duration_months': duration
    })

def get_metrics_engine():
    """Get the metrics engine instance"""
    return DynamicMetricsEngine()