"""
Predictive Maintenance Engine
AI-powered maintenance prediction using authentic Gauge API and billing data
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
import logging

predictive_maintenance_bp = Blueprint('predictive_maintenance', __name__)
logger = logging.getLogger(__name__)

class PredictiveMaintenanceEngine:
    """Predictive maintenance using authentic asset data and usage patterns"""
    
    def __init__(self):
        self.gauge_assets = []
        self.activity_data = []
        self.billing_records = []
        self.maintenance_predictions = []
        self.load_authentic_data()
        
    def load_authentic_data(self):
        """Load authentic data from all available sources"""
        try:
            # Load Gauge API data
            gauge_file = 'GAUGE API PULL 1045AM_05.15.2025.json'
            if os.path.exists(gauge_file):
                with open(gauge_file, 'r') as f:
                    self.gauge_assets = json.load(f)
                logger.info(f"Loaded {len(self.gauge_assets)} assets from Gauge API")
            
            # Load activity detail files for usage patterns
            activity_files = [f for f in os.listdir('.') if f.startswith('ActivityDetail') and f.endswith('.csv')]
            for file in activity_files:
                try:
                    df = pd.read_csv(file)
                    self.activity_data.append(df)
                except Exception as e:
                    logger.warning(f"Could not load {file}: {e}")
            
            # Load billing data for maintenance cost analysis
            for billing_file in ['RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm']:
                if os.path.exists(billing_file):
                    try:
                        df = pd.read_excel(billing_file)
                        self.billing_records.append(df)
                    except Exception as e:
                        logger.warning(f"Could not load {billing_file}: {e}")
                        
        except Exception as e:
            logger.error(f"Error loading authentic data: {e}")
    
    def analyze_usage_patterns(self):
        """Analyze equipment usage patterns from authentic activity data"""
        usage_analysis = {}
        
        # Process activity detail data
        for df in self.activity_data:
            if df.empty:
                continue
                
            try:
                # Look for asset/equipment identifiers
                asset_cols = [col for col in df.columns if any(term in col.lower() 
                             for term in ['asset', 'equipment', 'unit', 'id'])]
                
                if not asset_cols:
                    continue
                    
                asset_col = asset_cols[0]
                
                for asset_id in df[asset_col].unique():
                    if pd.isna(asset_id):
                        continue
                        
                    asset_records = df[df[asset_col] == asset_id]
                    
                    # Calculate usage metrics
                    daily_usage = len(asset_records.groupby(asset_records.get('Date', asset_records.index)))
                    total_records = len(asset_records)
                    
                    # Calculate operating hours if time data available
                    time_cols = [col for col in df.columns if any(term in col.lower() 
                                for term in ['time', 'hour', 'duration'])]
                    
                    operating_hours = 0
                    if time_cols:
                        for time_col in time_cols:
                            try:
                                hours = asset_records[time_col].sum()
                                if hours > 0:
                                    operating_hours += hours
                            except:
                                continue
                    
                    usage_analysis[str(asset_id)] = {
                        'daily_usage_frequency': daily_usage,
                        'total_activity_records': total_records,
                        'estimated_operating_hours': operating_hours,
                        'usage_intensity': 'HIGH' if total_records > 100 else 'MEDIUM' if total_records > 30 else 'LOW'
                    }
                    
            except Exception as e:
                logger.warning(f"Error analyzing usage patterns: {e}")
                continue
        
        return usage_analysis
    
    def predict_maintenance_needs(self):
        """Predict maintenance needs based on usage patterns and asset data"""
        usage_patterns = self.analyze_usage_patterns()
        maintenance_predictions = []
        
        for asset in self.gauge_assets:
            try:
                asset_id = str(asset.get('id', asset.get('assetId', 'Unknown')))
                make_model = f"{asset.get('make', '')} {asset.get('model', '')}".strip()
                category = asset.get('category', asset.get('type', 'Equipment'))
                
                # Get usage data for this asset
                usage_data = usage_patterns.get(asset_id, {
                    'daily_usage_frequency': 0,
                    'total_activity_records': 0,
                    'estimated_operating_hours': 0,
                    'usage_intensity': 'LOW'
                })
                
                # Determine maintenance schedule based on equipment type and usage
                if 'excavator' in category.lower():
                    base_interval = 250  # hours
                    critical_components = ['Hydraulic System', 'Engine', 'Tracks', 'Bucket']
                elif 'truck' in category.lower() or 'pickup' in category.lower():
                    base_interval = 500
                    critical_components = ['Engine', 'Transmission', 'Brakes', 'Tires']
                elif 'compactor' in category.lower():
                    base_interval = 200
                    critical_components = ['Drum', 'Engine', 'Hydraulics', 'Vibration System']
                elif 'dozer' in category.lower():
                    base_interval = 300
                    critical_components = ['Engine', 'Transmission', 'Tracks', 'Blade']
                else:
                    base_interval = 250
                    critical_components = ['Engine', 'Hydraulic System', 'Electrical']
                
                # Adjust interval based on usage intensity
                usage_multiplier = {
                    'HIGH': 0.7,    # More frequent maintenance for high usage
                    'MEDIUM': 0.85,
                    'LOW': 1.2
                }.get(usage_data['usage_intensity'], 1.0)
                
                adjusted_interval = int(base_interval * usage_multiplier)
                
                # Estimate current hours (if not available from usage data)
                if usage_data['estimated_operating_hours'] == 0:
                    year = asset.get('year', 2020)
                    age_years = datetime.now().year - year
                    estimated_hours = age_years * 1000  # Assume 1000 hours/year
                else:
                    estimated_hours = usage_data['estimated_operating_hours']
                
                # Calculate maintenance predictions for each component
                component_predictions = []
                for component in critical_components:
                    # Component-specific failure patterns
                    if component == 'Engine':
                        failure_threshold = adjusted_interval * 8
                        risk_factors = ['Oil contamination', 'Overheating', 'Filter clogs']
                    elif component == 'Hydraulic System':
                        failure_threshold = adjusted_interval * 6
                        risk_factors = ['Fluid leaks', 'Pressure loss', 'Seal wear']
                    elif component == 'Tracks' or component == 'Tires':
                        failure_threshold = adjusted_interval * 4
                        risk_factors = ['Wear patterns', 'Tension issues', 'Damage']
                    else:
                        failure_threshold = adjusted_interval * 5
                        risk_factors = ['Normal wear', 'Environmental factors']
                    
                    # Calculate failure probability
                    hours_since_service = estimated_hours % adjusted_interval
                    failure_probability = min((hours_since_service / failure_threshold) * 100, 95)
                    
                    # Determine maintenance urgency
                    if failure_probability >= 80:
                        urgency = 'CRITICAL'
                        recommended_action = 'Schedule immediate inspection'
                    elif failure_probability >= 60:
                        urgency = 'HIGH'
                        recommended_action = 'Schedule maintenance within 1 week'
                    elif failure_probability >= 40:
                        urgency = 'MEDIUM'
                        recommended_action = 'Schedule maintenance within 1 month'
                    else:
                        urgency = 'LOW'
                        recommended_action = 'Continue monitoring'
                    
                    component_predictions.append({
                        'component': component,
                        'failure_probability': round(failure_probability, 1),
                        'urgency': urgency,
                        'risk_factors': risk_factors,
                        'recommended_action': recommended_action
                    })
                
                # Calculate overall asset health score
                avg_failure_prob = sum(cp['failure_probability'] for cp in component_predictions) / len(component_predictions)
                health_score = max(100 - avg_failure_prob, 5)
                
                maintenance_predictions.append({
                    'asset_id': asset_id,
                    'make_model': make_model,
                    'category': category,
                    'estimated_hours': estimated_hours,
                    'usage_intensity': usage_data['usage_intensity'],
                    'health_score': round(health_score, 1),
                    'overall_urgency': max(cp['urgency'] for cp in component_predictions, 
                                         key=lambda x: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].index(x)),
                    'component_predictions': component_predictions,
                    'next_service_interval': adjusted_interval,
                    'predicted_downtime_risk': 'HIGH' if health_score < 40 else 'MEDIUM' if health_score < 70 else 'LOW'
                })
                
            except Exception as e:
                logger.warning(f"Error predicting maintenance for asset {asset_id}: {e}")
                continue
        
        return sorted(maintenance_predictions, key=lambda x: x['health_score'])
    
    def generate_maintenance_alerts(self):
        """Generate immediate maintenance alerts for critical equipment"""
        predictions = self.predict_maintenance_needs()
        alerts = []
        
        for prediction in predictions:
            critical_components = [cp for cp in prediction['component_predictions'] 
                                 if cp['urgency'] in ['CRITICAL', 'HIGH']]
            
            if critical_components:
                alert = {
                    'asset_id': prediction['asset_id'],
                    'make_model': prediction['make_model'],
                    'alert_level': 'CRITICAL' if any(cp['urgency'] == 'CRITICAL' for cp in critical_components) else 'HIGH',
                    'critical_components': [cp['component'] for cp in critical_components],
                    'immediate_actions': [cp['recommended_action'] for cp in critical_components],
                    'health_score': prediction['health_score'],
                    'estimated_downtime_hours': 8 if prediction['health_score'] < 30 else 4,
                    'cost_impact': 'HIGH' if prediction['health_score'] < 40 else 'MEDIUM'
                }
                alerts.append(alert)
        
        return alerts

@predictive_maintenance_bp.route('/predictive-maintenance')
@login_required
def predictive_maintenance_dashboard():
    """Predictive Maintenance Dashboard"""
    engine = PredictiveMaintenanceEngine()
    
    maintenance_predictions = engine.predict_maintenance_needs()
    maintenance_alerts = engine.generate_maintenance_alerts()
    usage_patterns = engine.analyze_usage_patterns()
    
    # Calculate summary metrics
    critical_alerts = len([a for a in maintenance_alerts if a['alert_level'] == 'CRITICAL'])
    high_risk_assets = len([p for p in maintenance_predictions if p['health_score'] < 50])
    total_assets_monitored = len(maintenance_predictions)
    avg_health_score = sum(p['health_score'] for p in maintenance_predictions) / len(maintenance_predictions) if maintenance_predictions else 0
    
    return render_template('predictive_maintenance.html',
                         maintenance_predictions=maintenance_predictions[:20],
                         maintenance_alerts=maintenance_alerts,
                         critical_alerts=critical_alerts,
                         high_risk_assets=high_risk_assets,
                         total_assets_monitored=total_assets_monitored,
                         avg_health_score=round(avg_health_score, 1))

@predictive_maintenance_bp.route('/api/maintenance-predictions')
def get_maintenance_predictions():
    """API endpoint for maintenance predictions"""
    engine = PredictiveMaintenanceEngine()
    predictions = engine.predict_maintenance_needs()
    return jsonify(predictions)

@predictive_maintenance_bp.route('/api/maintenance-alerts')
def get_maintenance_alerts():
    """API endpoint for maintenance alerts"""
    engine = PredictiveMaintenanceEngine()
    alerts = engine.generate_maintenance_alerts()
    return jsonify(alerts)

@predictive_maintenance_bp.route('/api/asset-health/<asset_id>')
def get_asset_health(asset_id):
    """API endpoint for specific asset health details"""
    engine = PredictiveMaintenanceEngine()
    predictions = engine.predict_maintenance_needs()
    
    asset_prediction = next((p for p in predictions if p['asset_id'] == asset_id), None)
    if asset_prediction:
        return jsonify(asset_prediction)
    else:
        return jsonify({'error': 'Asset not found'}), 404