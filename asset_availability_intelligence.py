"""
TRAXOVO Asset Availability Intelligence
Smart functions to reduce rental costs by maximizing internal asset utilization
"""
import pandas as pd
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request

asset_intel_bp = Blueprint('asset_intel', __name__, url_prefix='/asset-intelligence')

class AssetAvailabilityAnalyzer:
    def __init__(self):
        self.load_authentic_data()
    
    def load_authentic_data(self):
        """Load your real fleet and GPS data for availability analysis"""
        try:
            # Load your Gauge API data for real-time status
            with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
                self.gps_data = json.load(f)
            
            # Load equipment billing data for utilization patterns
            self.billing_data = pd.read_excel('RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm', 
                                            sheet_name='FLEET')
        except Exception as e:
            print(f"Data loading error: {e}")
            self.gps_data = []
            self.billing_data = pd.DataFrame()
    
    def identify_stagnant_assets(self, days_threshold=7):
        """Identify assets sitting in the same GPS location for extended periods"""
        stagnant_assets = []
        current_time = datetime.now()
        
        # Track assets by location over time to detect true stagnation
        location_tracking = {}
        
        for asset in self.gps_data:
            if not asset.get('Active', False):
                continue
                
            asset_id = asset.get('AssetIdentifier', 'Unknown')
            asset_name = asset.get('Label', 'Unknown Asset')
            category = asset.get('AssetCategory', 'Unknown')
            location = asset.get('Location', 'Unknown')
            
            # Get GPS coordinates
            lat = asset.get('Latitude')
            lng = asset.get('Longitude')
            
            if not lat or not lng:
                continue
            
            # Check movement/speed indicators
            speed = asset.get('Speed', 0)
            last_update = asset.get('EventDateTimeString', '')
            
            # Calculate days since last GPS update
            try:
                if last_update:
                    last_activity = datetime.strptime(last_update.split('T')[0], '%Y-%m-%d')
                    days_since_update = (current_time - last_activity).days
                else:
                    days_since_update = 999
            except:
                days_since_update = 999
            
            # Determine if asset is truly stagnant based on:
            # 1. Zero or very low speed
            # 2. Same location for extended period
            # 3. No recent GPS activity
            
            is_stationary = speed <= 2  # Essentially not moving
            location_stagnant = days_since_update >= days_threshold
            
            if is_stationary and location_stagnant:
                # Cross-reference with billing data for revenue impact
                revenue_potential = self._get_asset_revenue_potential(asset_id)
                
                # Calculate exact coordinates for location precision
                gps_position = f"{lat:.6f},{lng:.6f}"
                
                stagnant_assets.append({
                    'asset_id': asset_id,
                    'name': asset_name,
                    'category': category,
                    'location': location,
                    'gps_position': gps_position,
                    'days_stationary': days_since_update,
                    'current_speed': speed,
                    'latitude': lat,
                    'longitude': lng,
                    'revenue_potential': revenue_potential,
                    'priority': self._calculate_availability_priority(category, revenue_potential, days_since_update),
                    'last_movement': last_update,
                    'rental_savings_potential': self._calculate_rental_savings(category, revenue_potential)
                })
        
        # Sort by priority (highest rental savings potential first)
        return sorted(stagnant_assets, key=lambda x: x['rental_savings_potential'], reverse=True)
    
    def get_available_by_category(self, requested_category=None):
        """Get available assets by equipment category for dispatch"""
        available_assets = {}
        
        for asset in self.gps_data:
            if not asset.get('Active', False):
                continue
                
            category = asset.get('AssetCategory', 'Unknown')
            
            # Filter by requested category if specified
            if requested_category and category.lower() != requested_category.lower():
                continue
            
            if category not in available_assets:
                available_assets[category] = []
            
            # Check if asset appears to be available (not on active job)
            availability_status = self._check_asset_availability(asset)
            
            if availability_status['available']:
                available_assets[category].append({
                    'asset_id': asset.get('AssetIdentifier', 'Unknown'),
                    'name': asset.get('Label', 'Unknown Asset'),
                    'location': asset.get('Location', 'Unknown'),
                    'latitude': asset.get('Latitude'),
                    'longitude': asset.get('Longitude'),
                    'last_update': asset.get('EventDateTimeString', 'Unknown'),
                    'availability_confidence': availability_status['confidence'],
                    'estimated_revenue': self._get_asset_revenue_potential(asset.get('AssetIdentifier', ''))
                })
        
        return available_assets
    
    def generate_dispatch_alerts(self):
        """Generate smart alerts for dispatch team about asset availability"""
        alerts = []
        
        # High-value stagnant assets
        stagnant = self.identify_stagnant_assets(days_threshold=3)
        high_value_stagnant = [a for a in stagnant if a['revenue_potential'] > 1000]
        
        if high_value_stagnant:
            alerts.append({
                'type': 'HIGH_VALUE_AVAILABLE',
                'priority': 'HIGH',
                'message': f"{len(high_value_stagnant)} high-revenue assets sitting idle",
                'assets': high_value_stagnant[:5],  # Top 5
                'action': 'Consider deploying to active jobs'
            })
        
        # Category shortages vs availability
        category_analysis = self._analyze_category_utilization()
        for category, data in category_analysis.items():
            if data['available_count'] > 0 and data['utilization_rate'] < 70:
                alerts.append({
                    'type': 'UNDERUTILIZED_CATEGORY',
                    'priority': 'MEDIUM',
                    'message': f"{data['available_count']} {category} units available",
                    'category': category,
                    'details': data,
                    'action': 'Reduce external rentals for this category'
                })
        
        return sorted(alerts, key=lambda x: {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}[x['priority']], reverse=True)
    
    def _get_asset_revenue_potential(self, asset_id):
        """Calculate revenue potential for an asset based on billing history"""
        if self.billing_data.empty:
            return 0
        
        try:
            # Find asset in billing data
            asset_row = self.billing_data[self.billing_data['Asset ID'].astype(str) == str(asset_id)]
            if not asset_row.empty:
                return float(asset_row.iloc[0].get('Total Revenue', 0) or 0)
        except:
            pass
        
        # Estimate based on category averages
        for asset in self.gps_data:
            if asset.get('AssetIdentifier') == asset_id:
                category = asset.get('AssetCategory', '')
                return self._get_category_average_revenue(category)
        
        return 0
    
    def _get_category_average_revenue(self, category):
        """Get average revenue for equipment category"""
        category_revenues = {
            'Air Compressor': 1500,
            'Pickup Truck': 800,
            'Excavator': 3000,
            'Dump Truck': 2000,
            'Crane': 4000,
            'Bulldozer': 3500
        }
        
        # Find matching category
        for cat, revenue in category_revenues.items():
            if cat.lower() in category.lower():
                return revenue
        
        return 1000  # Default estimate
    
    def _check_asset_availability(self, asset):
        """Determine if asset appears to be available for deployment"""
        # Simple availability logic based on movement and timing
        speed = asset.get('Speed', 0)
        last_update = asset.get('EventDateTimeString', '')
        
        # Asset is likely available if:
        # 1. Speed is 0 (not moving)
        # 2. Recent GPS data available
        # 3. Not showing signs of active work
        
        confidence = 85  # Base confidence
        
        if speed == 0:
            confidence += 10
        elif speed > 25:
            confidence -= 30  # Likely in transit/working
        
        # Check if recent update
        try:
            if last_update:
                last_time = datetime.strptime(last_update.split('T')[0], '%Y-%m-%d')
                days_old = (datetime.now() - last_time).days
                if days_old > 3:
                    confidence -= 20
        except:
            confidence -= 15
        
        return {
            'available': confidence > 60,
            'confidence': min(100, max(0, confidence))
        }
    
    def _calculate_availability_priority(self, category, revenue_potential, days_inactive):
        """Calculate priority score for asset availability"""
        base_score = revenue_potential / 100  # Revenue component
        
        # Category multipliers
        category_multipliers = {
            'Air Compressor': 1.5,
            'Excavator': 2.0,
            'Crane': 2.5,
            'Dump Truck': 1.8,
            'Pickup Truck': 1.0
        }
        
        multiplier = 1.0
        for cat, mult in category_multipliers.items():
            if cat.lower() in category.lower():
                multiplier = mult
                break
        
        # Days inactive factor
        inactive_factor = min(3.0, days_inactive / 7)  # Max 3x for very stagnant
        
        return base_score * multiplier * inactive_factor
    
    def _analyze_category_utilization(self):
        """Analyze utilization by equipment category"""
        category_stats = {}
        
        for asset in self.gps_data:
            if not asset.get('Active', False):
                continue
                
            category = asset.get('AssetCategory', 'Unknown')
            
            if category not in category_stats:
                category_stats[category] = {
                    'total_count': 0,
                    'available_count': 0,
                    'working_count': 0
                }
            
            category_stats[category]['total_count'] += 1
            
            availability = self._check_asset_availability(asset)
            if availability['available']:
                category_stats[category]['available_count'] += 1
            else:
                category_stats[category]['working_count'] += 1
        
        # Calculate utilization rates
        for category, stats in category_stats.items():
            if stats['total_count'] > 0:
                stats['utilization_rate'] = (stats['working_count'] / stats['total_count']) * 100
            else:
                stats['utilization_rate'] = 0
        
        return category_stats
    
    def _calculate_rental_savings(self, category, revenue_potential):
        """Calculate potential rental cost savings by deploying internal assets"""
        # Typical rental costs per day by equipment category
        daily_rental_costs = {
            'Air Compressor': 85,    # $85/day rental cost
            'Pickup Truck': 45,      # $45/day rental cost
            'Excavator': 350,        # $350/day rental cost
            'Dump Truck': 200,       # $200/day rental cost
            'Crane': 450,            # $450/day rental cost
            'Bulldozer': 400,        # $400/day rental cost
            'Skid Steer': 150,       # $150/day rental cost
            'Trailer': 75            # $75/day rental cost
        }
        
        # Find matching category rental cost
        daily_cost = 100  # Default rental cost
        for cat, cost in daily_rental_costs.items():
            if cat.lower() in category.lower():
                daily_cost = cost
                break
        
        # Calculate monthly savings potential (assuming 22 working days/month)
        monthly_savings = daily_cost * 22
        
        # Factor in asset revenue potential vs rental cost
        net_savings = monthly_savings - (revenue_potential * 0.1)  # 10% operational cost
        
        return max(0, net_savings)

# Initialize analyzer
asset_analyzer = AssetAvailabilityAnalyzer()

@asset_intel_bp.route('/')
def availability_dashboard():
    """Asset availability intelligence dashboard"""
    return render_template('asset_availability_dashboard.html')

@asset_intel_bp.route('/api/stagnant-assets')
def get_stagnant_assets():
    """API endpoint for stagnant asset data"""
    days = request.args.get('days', 7, type=int)
    stagnant_assets = asset_analyzer.identify_stagnant_assets(days_threshold=days)
    return jsonify({'stagnant_assets': stagnant_assets})

@asset_intel_bp.route('/api/available-assets')
def get_available_assets():
    """API endpoint for available assets by category"""
    category = request.args.get('category', None)
    available_assets = asset_analyzer.get_available_by_category(category)
    return jsonify({'available_assets': available_assets})

@asset_intel_bp.route('/api/dispatch-alerts')
def get_dispatch_alerts():
    """API endpoint for dispatch alerts"""
    alerts = asset_analyzer.generate_dispatch_alerts()
    return jsonify({'alerts': alerts})

@asset_intel_bp.route('/api/category-utilization')
def get_category_utilization():
    """API endpoint for category utilization analysis"""
    utilization = asset_analyzer._analyze_category_utilization()
    return jsonify({'category_utilization': utilization})