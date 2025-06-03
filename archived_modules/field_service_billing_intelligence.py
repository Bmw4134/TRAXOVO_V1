"""
TRAXOVO Field Service & Heavy Haul Billing Intelligence
Capture missed revenue from mechanics, semi trucks, and labor operations
"""
import pandas as pd
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request

field_billing_bp = Blueprint('field_billing', __name__, url_prefix='/field-service-billing')

class FieldServiceBillingAnalyzer:
    def __init__(self):
        self.load_authentic_data()
    
    def load_authentic_data(self):
        """Load your real fleet, GPS, and billing data for service analysis"""
        try:
            # Load your Gauge API data for real-time tracking
            with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
                self.gps_data = json.load(f)
            
            # Load equipment billing data
            self.billing_data = pd.read_excel('RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm', 
                                            sheet_name='FLEET')
            
            # Load your internal equipment rates
            self.internal_rates = pd.read_excel('RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm', 
                                              sheet_name='Equip Rates')
            
        except Exception as e:
            print(f"Data loading error: {e}")
            self.gps_data = []
            self.billing_data = pd.DataFrame()
            self.internal_rates = pd.DataFrame()
    
    def identify_unbilled_service_assets(self):
        """Identify field service and heavy haul assets that may be missing billing"""
        service_assets = []
        
        for asset in self.gps_data:
            if not asset.get('Active', False):
                continue
                
            asset_id = asset.get('AssetIdentifier', 'Unknown')
            asset_name = asset.get('Label', 'Unknown Asset')
            category = asset.get('AssetCategory', 'Unknown')
            location = asset.get('Location', 'Unknown')
            
            # Identify service vehicles and heavy haul equipment
            is_service_vehicle = self._is_service_vehicle(category, asset_name)
            is_heavy_haul = self._is_heavy_haul_equipment(category, asset_name)
            
            if is_service_vehicle or is_heavy_haul:
                # Check billing status
                billing_status = self._check_billing_status(asset_id)
                
                # Calculate potential revenue
                potential_revenue = self._calculate_service_revenue_potential(
                    category, asset_name, is_service_vehicle, is_heavy_haul
                )
                
                # Analyze GPS patterns for billable activity
                activity_analysis = self._analyze_gps_activity(asset)
                
                service_assets.append({
                    'asset_id': asset_id,
                    'name': asset_name,
                    'category': category,
                    'location': location,
                    'latitude': asset.get('Latitude'),
                    'longitude': asset.get('Longitude'),
                    'is_service_vehicle': is_service_vehicle,
                    'is_heavy_haul': is_heavy_haul,
                    'billing_status': billing_status,
                    'potential_monthly_revenue': potential_revenue,
                    'activity_analysis': activity_analysis,
                    'priority_score': self._calculate_billing_priority(
                        potential_revenue, billing_status, activity_analysis
                    )
                })
        
        # Sort by priority (highest missed revenue first)
        return sorted(service_assets, key=lambda x: x['priority_score'], reverse=True)
    
    def _is_service_vehicle(self, category, name):
        """Identify mechanic trucks and service vehicles"""
        service_indicators = [
            'mechanic', 'service', 'maintenance', 'repair', 'tech',
            'field service', 'mobile service', 'utility'
        ]
        
        text_to_check = f"{category} {name}".lower()
        return any(indicator in text_to_check for indicator in service_indicators)
    
    def _is_heavy_haul_equipment(self, category, name):
        """Identify semi trucks and heavy haul equipment"""
        heavy_haul_indicators = [
            'semi', 'truck tractor', 'heavy haul', 'lowboy', 'trailer',
            'transport', 'hauler', 'tractor', 'big rig'
        ]
        
        text_to_check = f"{category} {name}".lower()
        return any(indicator in text_to_check for indicator in heavy_haul_indicators)
    
    def _check_billing_status(self, asset_id):
        """Check if asset has recent billing activity"""
        if self.billing_data.empty:
            return {'status': 'unknown', 'last_billed': None, 'revenue': 0}
        
        # Find asset in billing data
        try:
            asset_billing = self.billing_data[
                self.billing_data['Asset Identifier'].astype(str) == str(asset_id)
            ]
            
            if not asset_billing.empty:
                # Check if marked as billable
                billable_status = asset_billing.iloc[0].get('BILLABLE ASSET?', 'NON-BILLABLE')
                
                return {
                    'status': 'billable' if 'BILLABLE' in str(billable_status).upper() else 'non-billable',
                    'billable_flag': billable_status,
                    'revenue': 0  # Would need time-based billing data for actual revenue
                }
        except:
            pass
        
        return {'status': 'not_found', 'last_billed': None, 'revenue': 0}
    
    def _calculate_service_revenue_potential(self, category, name, is_service, is_heavy_haul):
        """Calculate potential monthly revenue for service vehicles"""
        base_rates = {
            'mechanic_truck': 4500,      # $4,500/month for field mechanic
            'service_vehicle': 3200,     # $3,200/month for service calls
            'semi_truck': 5500,          # $5,500/month for heavy haul
            'lowboy_trailer': 3000,      # $3,000/month for transport
            'maintenance_truck': 3800    # $3,800/month for maintenance ops
        }
        
        # Determine service type and rate
        if is_service:
            if 'mechanic' in name.lower() or 'mechanic' in category.lower():
                return base_rates['mechanic_truck']
            else:
                return base_rates['service_vehicle']
        
        if is_heavy_haul:
            if 'semi' in name.lower() or 'tractor' in category.lower():
                return base_rates['semi_truck']
            elif 'trailer' in name.lower() or 'lowboy' in name.lower():
                return base_rates['lowboy_trailer']
        
        return base_rates['maintenance_truck']
    
    def _analyze_gps_activity(self, asset):
        """Analyze GPS patterns to identify billable service activity"""
        speed = asset.get('Speed') or 0
        speed = float(speed) if speed is not None else 0
        last_update = asset.get('EventDateTimeString', '')
        
        # Calculate activity indicators
        activity_score = 0
        
        # Movement indicates active use
        if speed > 0:
            activity_score += 30
        if speed > 25:  # Highway speeds suggest transport/haul work
            activity_score += 40
        
        # Recent GPS data indicates active monitoring
        try:
            if last_update:
                last_time = datetime.strptime(last_update.split('T')[0], '%Y-%m-%d')
                days_old = (datetime.now() - last_time).days
                if days_old <= 1:
                    activity_score += 20
                elif days_old <= 7:
                    activity_score += 10
        except:
            pass
        
        return {
            'activity_score': min(100, activity_score),
            'current_speed': speed,
            'last_update_days': days_old if 'days_old' in locals() else 999,
            'likely_billable': activity_score > 40
        }
    
    def _calculate_billing_priority(self, revenue_potential, billing_status, activity):
        """Calculate priority score for billing optimization"""
        priority = 0
        
        # Revenue potential component (40% of score)
        priority += (revenue_potential / 100) * 0.4
        
        # Billing status component (35% of score)
        if billing_status['status'] == 'non-billable':
            priority += 35  # High priority - should be billable
        elif billing_status['status'] == 'not_found':
            priority += 25  # Medium priority - needs setup
        
        # Activity component (25% of score)
        priority += activity['activity_score'] * 0.25
        
        return priority
    
    def generate_billing_opportunities(self):
        """Generate actionable billing opportunities for management"""
        service_assets = self.identify_unbilled_service_assets()
        opportunities = []
        
        # High-value unbilled assets
        high_value_unbilled = [a for a in service_assets 
                              if a['potential_monthly_revenue'] > 3000 and 
                              a['billing_status']['status'] != 'billable']
        
        if high_value_unbilled:
            total_missed_revenue = sum(a['potential_monthly_revenue'] for a in high_value_unbilled)
            opportunities.append({
                'type': 'HIGH_VALUE_UNBILLED',
                'priority': 'CRITICAL',
                'title': f'${total_missed_revenue:,.0f}/month in unbilled high-value assets',
                'count': len(high_value_unbilled),
                'assets': high_value_unbilled[:5],  # Top 5
                'action': 'Update billing status and create service contracts'
            })
        
        # Active service vehicles not marked billable
        active_unbilled = [a for a in service_assets 
                          if a['activity_analysis']['likely_billable'] and 
                          a['billing_status']['status'] != 'billable']
        
        if active_unbilled:
            opportunities.append({
                'type': 'ACTIVE_UNBILLED_SERVICES',
                'priority': 'HIGH',
                'title': f'{len(active_unbilled)} active service vehicles not billing',
                'assets': active_unbilled[:10],
                'action': 'Set up time tracking and service billing'
            })
        
        # Semi trucks and heavy haul analysis
        heavy_haul_assets = [a for a in service_assets if a['is_heavy_haul']]
        if heavy_haul_assets:
            total_haul_potential = sum(a['potential_monthly_revenue'] for a in heavy_haul_assets)
            opportunities.append({
                'type': 'HEAVY_HAUL_REVENUE',
                'priority': 'HIGH',
                'title': f'${total_haul_potential:,.0f}/month heavy haul potential',
                'count': len(heavy_haul_assets),
                'assets': heavy_haul_assets,
                'action': 'Implement transport billing and job tracking'
            })
        
        return opportunities
    
    def get_service_vehicle_summary(self):
        """Get summary of service vehicles and billing status"""
        service_assets = self.identify_unbilled_service_assets()
        
        summary = {
            'total_service_assets': len(service_assets),
            'mechanic_trucks': len([a for a in service_assets if a['is_service_vehicle']]),
            'heavy_haul_equipment': len([a for a in service_assets if a['is_heavy_haul']]),
            'billable_count': len([a for a in service_assets if a['billing_status']['status'] == 'billable']),
            'non_billable_count': len([a for a in service_assets if a['billing_status']['status'] == 'non-billable']),
            'total_revenue_potential': sum(a['potential_monthly_revenue'] for a in service_assets),
            'missed_revenue': sum(a['potential_monthly_revenue'] for a in service_assets 
                                if a['billing_status']['status'] != 'billable')
        }
        
        return summary

# Initialize analyzer
field_service_analyzer = FieldServiceBillingAnalyzer()

@field_billing_bp.route('/')
def field_service_dashboard():
    """Field service and heavy haul billing dashboard"""
    return render_template('field_service_billing_dashboard.html')

@field_billing_bp.route('/api/unbilled-assets')
def get_unbilled_service_assets():
    """API endpoint for unbilled service assets"""
    assets = field_service_analyzer.identify_unbilled_service_assets()
    return jsonify({'unbilled_assets': assets})

@field_billing_bp.route('/api/billing-opportunities')
def get_billing_opportunities():
    """API endpoint for billing opportunities"""
    opportunities = field_service_analyzer.generate_billing_opportunities()
    return jsonify({'opportunities': opportunities})

@field_billing_bp.route('/api/service-summary')
def get_service_summary():
    """API endpoint for service vehicle summary"""
    summary = field_service_analyzer.get_service_vehicle_summary()
    return jsonify({'summary': summary})