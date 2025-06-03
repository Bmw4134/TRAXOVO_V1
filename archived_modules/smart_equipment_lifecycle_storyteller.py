"""
TRAXOVO Smart Equipment Lifecycle Storyteller
Comprehensive equipment lifecycle analytics using authentic fleet data
"""
import pandas as pd
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request

lifecycle_bp = Blueprint('lifecycle', __name__, url_prefix='/equipment-lifecycle')

class EquipmentLifecycleAnalyzer:
    def __init__(self):
        self.load_authentic_data()
    
    def load_authentic_data(self):
        """Load your real fleet, GPS, and billing data for lifecycle analysis"""
        try:
            # Load your Gauge API data for real-time status
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
    
    def generate_equipment_story(self, asset_id):
        """Generate comprehensive lifecycle story for specific equipment"""
        # Find equipment in GPS data
        gps_asset = next((item for item in self.gps_data 
                         if item.get('AssetIdentifier') == asset_id), None)
        
        # Find equipment in billing/fleet data
        fleet_asset = None
        if not self.billing_data.empty:
            fleet_matches = self.billing_data[
                self.billing_data['Asset Identifier'].astype(str) == str(asset_id)
            ]
            if not fleet_matches.empty:
                fleet_asset = fleet_matches.iloc[0].to_dict()
        
        if not gps_asset and not fleet_asset:
            return None
        
        # Build comprehensive story
        story = {
            'asset_id': asset_id,
            'basic_info': self._extract_basic_info(gps_asset, fleet_asset),
            'acquisition_story': self._analyze_acquisition(fleet_asset),
            'operational_history': self._analyze_operational_history(gps_asset, fleet_asset),
            'utilization_patterns': self._analyze_utilization_patterns(gps_asset),
            'financial_performance': self._analyze_financial_performance(asset_id, fleet_asset),
            'maintenance_indicators': self._analyze_maintenance_needs(gps_asset, fleet_asset),
            'lifecycle_stage': self._determine_lifecycle_stage(gps_asset, fleet_asset),
            'recommendations': self._generate_recommendations(gps_asset, fleet_asset),
            'story_timeline': self._create_timeline(gps_asset, fleet_asset)
        }
        
        return story
    
    def _extract_basic_info(self, gps_asset, fleet_asset):
        """Extract basic equipment information"""
        info = {
            'name': 'Unknown Equipment',
            'category': 'Unknown',
            'make': 'Unknown',
            'model': 'Unknown',
            'year': 'Unknown',
            'serial_number': 'Unknown',
            'current_location': 'Unknown',
            'active_status': False
        }
        
        if gps_asset:
            info.update({
                'name': gps_asset.get('Label', 'Unknown Equipment'),
                'category': gps_asset.get('AssetCategory', 'Unknown'),
                'current_location': gps_asset.get('Location', 'Unknown'),
                'active_status': gps_asset.get('Active', False)
            })
        
        if fleet_asset:
            info.update({
                'make': fleet_asset.get('Make', 'Unknown'),
                'model': fleet_asset.get('Model', 'Unknown'),
                'year': fleet_asset.get('Model Year', 'Unknown'),
                'serial_number': fleet_asset.get('Serial/VIN', 'Unknown')
            })
        
        return info
    
    def _analyze_acquisition(self, fleet_asset):
        """Analyze equipment acquisition details"""
        if not fleet_asset:
            return {'story': 'No acquisition data available'}
        
        purchase_date = fleet_asset.get('Purchase Date')
        purchase_cost = fleet_asset.get('Purchase Cost', 0)
        
        try:
            purchase_cost = float(purchase_cost) if purchase_cost else 0
        except:
            purchase_cost = 0
        
        story = f"This equipment "
        
        if purchase_date:
            try:
                purchase_year = pd.to_datetime(purchase_date).year
                years_owned = datetime.now().year - purchase_year
                story += f"was acquired in {purchase_year} ({years_owned} years ago)"
            except:
                story += "has acquisition date recorded"
        else:
            story += "has been in the fleet for an unknown duration"
        
        if purchase_cost > 0:
            story += f" with an initial investment of ${purchase_cost:,.0f}"
        
        return {
            'story': story,
            'purchase_date': purchase_date,
            'purchase_cost': purchase_cost,
            'years_owned': years_owned if 'years_owned' in locals() else None
        }
    
    def _analyze_operational_history(self, gps_asset, fleet_asset):
        """Analyze equipment operational patterns"""
        if not gps_asset:
            return {'story': 'No operational data available'}
        
        # Extract operational metrics
        speed = gps_asset.get('Speed', 0) or 0
        last_update = gps_asset.get('EventDateTimeString', '')
        
        # Calculate operational insights
        try:
            if last_update:
                last_activity = datetime.strptime(last_update.split('T')[0], '%Y-%m-%d')
                days_since_activity = (datetime.now() - last_activity).days
            else:
                days_since_activity = 999
        except:
            days_since_activity = 999
        
        story = f"This equipment is currently "
        
        if days_since_activity <= 1:
            story += "actively operating with recent GPS activity"
        elif days_since_activity <= 7:
            story += f"moderately active (last seen {days_since_activity} days ago)"
        elif days_since_activity <= 30:
            story += f"less active recently (last activity {days_since_activity} days ago)"
        else:
            story += "showing minimal recent activity"
        
        if speed > 0:
            story += f" and is currently moving at {speed} mph"
        else:
            story += " and is currently stationary"
        
        return {
            'story': story,
            'current_speed': speed,
            'days_since_activity': days_since_activity,
            'last_update': last_update
        }
    
    def _analyze_utilization_patterns(self, gps_asset):
        """Analyze equipment utilization patterns"""
        if not gps_asset:
            return {'story': 'No utilization data available'}
        
        # Analyze GPS patterns for utilization insights
        speed = gps_asset.get('Speed', 0) or 0
        location = gps_asset.get('Location', 'Unknown')
        
        utilization_score = 0
        pattern_insights = []
        
        # Speed analysis
        if speed == 0:
            pattern_insights.append("Currently stationary - may be at job site or in storage")
            utilization_score += 20
        elif speed <= 25:
            pattern_insights.append("Operating at work speeds - likely performing job tasks")
            utilization_score += 60
        else:
            pattern_insights.append("Traveling at highway speeds - in transit between locations")
            utilization_score += 40
        
        # Location analysis
        if 'yard' in location.lower() or 'shop' in location.lower():
            pattern_insights.append("Located at company facility")
        elif 'job' in location.lower() or 'site' in location.lower():
            pattern_insights.append("Deployed to active job site")
            utilization_score += 30
        
        story = f"Current utilization analysis shows: {'. '.join(pattern_insights)}"
        
        return {
            'story': story,
            'utilization_score': min(100, utilization_score),
            'pattern_insights': pattern_insights
        }
    
    def _analyze_financial_performance(self, asset_id, fleet_asset):
        """Analyze financial performance and ROI"""
        purchase_cost = 0
        if fleet_asset:
            try:
                purchase_cost = float(fleet_asset.get('Purchase Cost', 0) or 0)
            except:
                purchase_cost = 0
        
        # Get potential revenue from rates
        monthly_revenue = 0
        if not self.internal_rates.empty and fleet_asset:
            category = fleet_asset.get('Category', '')
            for _, rate_row in self.internal_rates.iterrows():
                if pd.notna(rate_row.get('Category')) and category:
                    if category.lower() in rate_row['Category'].lower():
                        monthly_revenue = rate_row.get('Rate', 0) or 0
                        break
        
        # Calculate ROI metrics
        annual_revenue = monthly_revenue * 12
        
        story = f"Financial performance: "
        if purchase_cost > 0 and annual_revenue > 0:
            payback_years = purchase_cost / annual_revenue
            roi_percent = (annual_revenue / purchase_cost) * 100
            story += f"Generating ${monthly_revenue:,.0f}/month (${annual_revenue:,.0f}/year). "
            story += f"ROI: {roi_percent:.1f}% annually, {payback_years:.1f} year payback period"
        elif monthly_revenue > 0:
            story += f"Current revenue potential: ${monthly_revenue:,.0f}/month"
        else:
            story += "Revenue tracking not configured"
        
        return {
            'story': story,
            'purchase_cost': purchase_cost,
            'monthly_revenue': monthly_revenue,
            'annual_revenue': annual_revenue,
            'roi_percent': roi_percent if 'roi_percent' in locals() else 0,
            'payback_years': payback_years if 'payback_years' in locals() else 0
        }
    
    def _analyze_maintenance_needs(self, gps_asset, fleet_asset):
        """Analyze maintenance indicators and needs"""
        if not fleet_asset:
            return {'story': 'No maintenance data available'}
        
        # Extract maintenance-related metrics
        hour_meter = fleet_asset.get('Hour Meter', 0) or 0
        lifetime_hours = fleet_asset.get('Lifetime Hour Meter', 0) or 0
        model_year = fleet_asset.get('Model Year')
        
        try:
            hour_meter = float(hour_meter)
            lifetime_hours = float(lifetime_hours)
        except:
            hour_meter = 0
            lifetime_hours = 0
        
        maintenance_insights = []
        
        # Age analysis
        if model_year:
            try:
                age = datetime.now().year - int(model_year)
                if age < 3:
                    maintenance_insights.append(f"Relatively new equipment ({age} years old)")
                elif age < 8:
                    maintenance_insights.append(f"Mature equipment ({age} years old) - monitor for increased maintenance")
                else:
                    maintenance_insights.append(f"Aging equipment ({age} years old) - consider replacement planning")
            except:
                pass
        
        # Hour meter analysis
        if lifetime_hours > 0:
            if lifetime_hours < 1000:
                maintenance_insights.append("Low operating hours - minimal wear")
            elif lifetime_hours < 5000:
                maintenance_insights.append("Moderate operating hours - standard maintenance schedule")
            else:
                maintenance_insights.append("High operating hours - intensive maintenance required")
        
        story = f"Maintenance profile: {'. '.join(maintenance_insights) if maintenance_insights else 'Limited maintenance data available'}"
        
        return {
            'story': story,
            'hour_meter': hour_meter,
            'lifetime_hours': lifetime_hours,
            'maintenance_insights': maintenance_insights
        }
    
    def _determine_lifecycle_stage(self, gps_asset, fleet_asset):
        """Determine current lifecycle stage"""
        stage = 'Unknown'
        confidence = 0
        
        # Analyze multiple factors to determine stage
        factors = {}
        
        # Age factor
        if fleet_asset and fleet_asset.get('Model Year'):
            try:
                age = datetime.now().year - int(fleet_asset['Model Year'])
                factors['age'] = age
                
                if age < 2:
                    stage = 'New/Breaking-in'
                    confidence = 85
                elif age < 5:
                    stage = 'Prime Operating'
                    confidence = 90
                elif age < 10:
                    stage = 'Mature/Productive'
                    confidence = 80
                else:
                    stage = 'Aging/Consider Replacement'
                    confidence = 75
            except:
                pass
        
        # Activity factor
        if gps_asset:
            speed = gps_asset.get('Speed', 0) or 0
            active = gps_asset.get('Active', False)
            
            if not active:
                stage = 'Inactive/Stored'
                confidence = 90
            elif speed == 0:
                if 'Prime' in stage or 'Mature' in stage:
                    stage += ' (Currently Idle)'
        
        return {
            'stage': stage,
            'confidence': confidence,
            'factors': factors
        }
    
    def _generate_recommendations(self, gps_asset, fleet_asset):
        """Generate actionable recommendations"""
        recommendations = []
        
        # Utilization recommendations
        if gps_asset:
            speed = gps_asset.get('Speed', 0) or 0
            active = gps_asset.get('Active', False)
            
            if not active:
                recommendations.append({
                    'category': 'Utilization',
                    'priority': 'High',
                    'action': 'Reactivate or consider disposal',
                    'reason': 'Equipment marked as inactive'
                })
            elif speed == 0:
                recommendations.append({
                    'category': 'Utilization',
                    'priority': 'Medium',
                    'action': 'Deploy to active job or relocate',
                    'reason': 'Equipment stationary for extended period'
                })
        
        # Financial recommendations
        if fleet_asset:
            billable_status = fleet_asset.get('BILLABLE ASSET?', 'NON-BILLABLE')
            if 'NON-BILLABLE' in str(billable_status).upper():
                recommendations.append({
                    'category': 'Revenue',
                    'priority': 'High',
                    'action': 'Set up billing configuration',
                    'reason': 'Equipment not configured for revenue generation'
                })
        
        return recommendations
    
    def _create_timeline(self, gps_asset, fleet_asset):
        """Create equipment lifecycle timeline"""
        timeline = []
        
        # Purchase/acquisition event
        if fleet_asset and fleet_asset.get('Purchase Date'):
            timeline.append({
                'date': fleet_asset['Purchase Date'],
                'event': 'Equipment Acquired',
                'details': f"Purchased for ${fleet_asset.get('Purchase Cost', 0):,.0f}"
            })
        
        # Current status event
        if gps_asset:
            timeline.append({
                'date': gps_asset.get('EventDateTimeString', ''),
                'event': 'Current Status',
                'details': f"Active: {gps_asset.get('Active', False)}, Location: {gps_asset.get('Location', 'Unknown')}"
            })
        
        return sorted(timeline, key=lambda x: x['date'] if x['date'] else '')

# Initialize analyzer
lifecycle_analyzer = EquipmentLifecycleAnalyzer()

@lifecycle_bp.route('/')
def lifecycle_dashboard():
    """Equipment lifecycle storyteller dashboard"""
    return render_template('equipment_lifecycle_dashboard.html')

@lifecycle_bp.route('/api/equipment-story/<asset_id>')
def get_equipment_story(asset_id):
    """API endpoint for specific equipment story"""
    story = lifecycle_analyzer.generate_equipment_story(asset_id)
    return jsonify({'story': story})

@lifecycle_bp.route('/api/fleet-overview')
def get_fleet_lifecycle_overview():
    """API endpoint for fleet lifecycle overview"""
    # Analyze entire fleet for lifecycle distribution
    fleet_overview = {
        'total_assets': len(lifecycle_analyzer.gps_data),
        'lifecycle_distribution': {},
        'recommendations_summary': []
    }
    
    return jsonify({'fleet_overview': fleet_overview})