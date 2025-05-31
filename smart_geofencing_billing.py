"""
Smart Geofencing & Billing System
Intelligent geofence management with equipment rate capture and billing optimization
"""

from flask import Blueprint, render_template, jsonify, request, session
import os
import json
import math
from datetime import datetime, timedelta
import requests

geofencing_billing_bp = Blueprint('geofencing_billing', __name__)

class SmartGeofencingEngine:
    """Intelligent geofencing with billing integration"""
    
    def __init__(self):
        self.gauge_api_key = os.environ.get('GAUGE_API_KEY')
        self.gauge_api_url = os.environ.get('GAUGE_API_URL')
        self.project_geofences = self._load_project_geofences()
        self.equipment_rates = self._load_comprehensive_equipment_rates()
        
    def _load_project_geofences(self):
        """Load project geofences with smart buffer zones"""
        return {
            "2019-044": {
                "name": "E Long Avenue",
                "center_lat": 32.7767,
                "center_lng": -96.7970,
                "radius_meters": 500,
                "buffer_zone_meters": 150,  # Smart buffer for edge cases
                "billing_active": True,
                "hourly_rates": {"standard": 185, "overtime": 277.50}
            },
            "2021-017": {
                "name": "Plaza Construction", 
                "center_lat": 32.7555,
                "center_lng": -96.8100,
                "radius_meters": 300,
                "buffer_zone_meters": 100,
                "billing_active": True,
                "hourly_rates": {"standard": 175, "overtime": 262.50}
            },
            "2025-003": {
                "name": "Highway Extension",
                "center_lat": 32.8000,
                "center_lng": -96.7500,
                "radius_meters": 800,
                "buffer_zone_meters": 200,
                "billing_active": True,
                "hourly_rates": {"standard": 195, "overtime": 292.50}
            }
        }
    
    def _load_comprehensive_equipment_rates(self):
        """Load comprehensive equipment rates including pre-Tomi equipment"""
        return {
            # Current standardized rates
            "excavator": {
                "hourly": 185,
                "daily": 1480,
                "weekly": 8880,
                "monthly": 35520,
                "acquisition_cost": 450000,
                "depreciation_monthly": 3750
            },
            "dozer": {
                "hourly": 175,
                "daily": 1400,
                "weekly": 8400,
                "monthly": 33600,
                "acquisition_cost": 380000,
                "depreciation_monthly": 3167
            },
            "loader": {
                "hourly": 165,
                "daily": 1320,
                "weekly": 7920,
                "monthly": 31680,
                "acquisition_cost": 320000,
                "depreciation_monthly": 2667
            },
            "truck": {
                "hourly": 95,
                "daily": 760,
                "weekly": 4560,
                "monthly": 18240,
                "acquisition_cost": 180000,
                "depreciation_monthly": 1500
            },
            "compactor": {
                "hourly": 125,
                "daily": 1000,
                "weekly": 6000,
                "monthly": 24000,
                "acquisition_cost": 250000,
                "depreciation_monthly": 2083
            },
            
            # Pre-Tomi legacy equipment (need cost capture)
            "legacy_excavator": {
                "hourly": 165,  # Lower rate due to age
                "daily": 1320,
                "weekly": 7920,
                "monthly": 31680,
                "acquisition_cost": 0,  # Need historical data
                "depreciation_monthly": 0,  # Need calculation
                "notes": "Requires historical cost analysis"
            },
            "legacy_dozer": {
                "hourly": 155,
                "daily": 1240,
                "weekly": 7440,
                "monthly": 29760,
                "acquisition_cost": 0,
                "depreciation_monthly": 0,
                "notes": "Requires historical cost analysis"
            }
        }
    
    def get_real_time_geofence_status(self):
        """Get real-time equipment locations with smart geofence analysis"""
        try:
            headers = {
                'Authorization': f'Bearer {self.gauge_api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'TRAXOVO-Geofence/1.0'
            }
            
            api_url = self.gauge_api_url
            if not api_url.startswith('http'):
                api_url = f"https://api.gaugesmart.com/AssetList/{api_url}"
            
            response = requests.get(api_url, headers=headers, timeout=10, verify=False)
            
            if response.status_code == 200:
                raw_data = response.json()
                return self._process_geofence_data(raw_data)
            else:
                return {"error": f"GAUGE API returned status {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Unable to connect to GAUGE API: {str(e)}"}
    
    def _process_geofence_data(self, raw_data):
        """Process equipment locations with intelligent geofence logic"""
        equipment_list = raw_data if isinstance(raw_data, list) else raw_data.get('assets', [])
        
        geofence_analysis = []
        billing_summary = {"total_billable_hours": 0, "total_revenue": 0, "projects": {}}
        
        for item in equipment_list:
            lat = item.get('latitude', item.get('lat'))
            lng = item.get('longitude', item.get('lng', item.get('lon')))
            
            if not lat or not lng:
                continue
                
            equipment_analysis = {
                'id': item.get('id', item.get('asset_id', 'Unknown')),
                'name': item.get('name', item.get('asset_name', 'Unknown Asset')),
                'type': item.get('type', item.get('equipment_type', 'equipment')),
                'latitude': lat,
                'longitude': lng,
                'location_status': self._analyze_smart_location(lat, lng),
                'billing_status': self._calculate_billing_status(item, lat, lng),
                'last_update': item.get('last_update', datetime.now().isoformat())
            }
            
            geofence_analysis.append(equipment_analysis)
            
            # Update billing summary
            if equipment_analysis['billing_status']['billable']:
                project_id = equipment_analysis['location_status']['assigned_project']
                if project_id not in billing_summary['projects']:
                    billing_summary['projects'][project_id] = {
                        'name': self.project_geofences[project_id]['name'],
                        'equipment_count': 0,
                        'billable_hours': 0,
                        'revenue': 0
                    }
                
                billing_summary['projects'][project_id]['equipment_count'] += 1
                billing_summary['projects'][project_id]['billable_hours'] += equipment_analysis['billing_status']['hours_today']
                billing_summary['projects'][project_id]['revenue'] += equipment_analysis['billing_status']['revenue_today']
                
                billing_summary['total_billable_hours'] += equipment_analysis['billing_status']['hours_today']
                billing_summary['total_revenue'] += equipment_analysis['billing_status']['revenue_today']
        
        return {
            "equipment_locations": geofence_analysis,
            "billing_summary": billing_summary,
            "geofence_alerts": self._generate_geofence_alerts(geofence_analysis),
            "rate_optimization": self._analyze_rate_optimization()
        }
    
    def _analyze_smart_location(self, lat, lng):
        """Intelligent location analysis with buffer zones"""
        for project_id, geofence in self.project_geofences.items():
            distance = self._calculate_distance(
                lat, lng, 
                geofence['center_lat'], geofence['center_lng']
            )
            
            # Check primary geofence
            if distance <= geofence['radius_meters']:
                return {
                    "status": "inside_geofence",
                    "assigned_project": project_id,
                    "project_name": geofence['name'],
                    "distance_from_center": round(distance, 1),
                    "confidence": "high"
                }
            
            # Check smart buffer zone
            elif distance <= geofence['radius_meters'] + geofence['buffer_zone_meters']:
                return {
                    "status": "buffer_zone",
                    "assigned_project": project_id,
                    "project_name": geofence['name'],
                    "distance_from_center": round(distance, 1),
                    "confidence": "medium",
                    "note": "Equipment near project site - verify billing manually"
                }
        
        return {
            "status": "outside_all_geofences",
            "assigned_project": None,
            "project_name": "Unassigned",
            "confidence": "high",
            "note": "Equipment not assigned to any project"
        }
    
    def _calculate_distance(self, lat1, lng1, lat2, lng2):
        """Calculate distance between two coordinates in meters"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng/2) * math.sin(delta_lng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _calculate_billing_status(self, equipment, lat, lng):
        """Calculate billing status with smart geofence logic"""
        location_status = self._analyze_smart_location(lat, lng)
        equipment_type = equipment.get('type', 'equipment').lower()
        
        # Get equipment rate
        rate_info = self.equipment_rates.get(equipment_type, self.equipment_rates.get('legacy_' + equipment_type, {'hourly': 150}))
        
        # Determine billability
        billable = False
        billing_rate = 0
        hours_today = 0
        
        if location_status['status'] in ['inside_geofence', 'buffer_zone']:
            project_id = location_status['assigned_project']
            if project_id and self.project_geofences[project_id]['billing_active']:
                billable = True
                billing_rate = rate_info['hourly']
                hours_today = equipment.get('operating_hours_today', 8)  # Default 8 hours
        
        return {
            "billable": billable,
            "billing_rate": billing_rate,
            "hours_today": hours_today,
            "revenue_today": billing_rate * hours_today,
            "rate_source": "legacy" if equipment_type.startswith('legacy_') else "current",
            "needs_rate_review": rate_info.get('acquisition_cost', 0) == 0
        }
    
    def _generate_geofence_alerts(self, equipment_analysis):
        """Generate alerts for geofence and billing issues"""
        alerts = []
        
        # Buffer zone equipment needing verification
        buffer_equipment = [e for e in equipment_analysis if e['location_status']['status'] == 'buffer_zone']
        if buffer_equipment:
            alerts.append({
                "type": "billing_verification",
                "priority": "medium",
                "message": f"{len(buffer_equipment)} equipment units in buffer zones need billing verification",
                "equipment": [e['name'] for e in buffer_equipment],
                "action": "Manually verify project assignment and billing status"
            })
        
        # Equipment needing rate review
        rate_review_needed = [e for e in equipment_analysis if e['billing_status']['needs_rate_review']]
        if rate_review_needed:
            alerts.append({
                "type": "rate_analysis",
                "priority": "high",
                "message": f"{len(rate_review_needed)} equipment units need historical cost analysis",
                "equipment": [e['name'] for e in rate_review_needed],
                "action": "Update equipment acquisition costs and depreciation rates"
            })
        
        # Unassigned billable equipment
        unassigned = [e for e in equipment_analysis if e['location_status']['status'] == 'outside_all_geofences']
        if unassigned:
            revenue_loss = sum([self.equipment_rates.get(e['type'], {'hourly': 150})['hourly'] * 8 for e in unassigned])
            alerts.append({
                "type": "revenue_opportunity",
                "priority": "high",
                "message": f"${revenue_loss}/day potential revenue from unassigned equipment",
                "equipment": [e['name'] for e in unassigned],
                "action": "Assign to active projects or seek new work"
            })
        
        return alerts
    
    def _analyze_rate_optimization(self):
        """Analyze equipment rate optimization opportunities"""
        optimization_opportunities = []
        
        # Legacy equipment rate gaps
        legacy_equipment = {k: v for k, v in self.equipment_rates.items() if k.startswith('legacy_')}
        for equipment_type, rate_info in legacy_equipment.items():
            if rate_info['acquisition_cost'] == 0:
                optimization_opportunities.append({
                    "type": "missing_cost_data",
                    "equipment_type": equipment_type,
                    "current_rate": rate_info['hourly'],
                    "recommendation": "Research historical acquisition cost to set proper depreciation and rate",
                    "priority": "high"
                })
        
        # Rate comparison opportunities
        optimization_opportunities.append({
            "type": "rate_benchmarking",
            "recommendation": "Compare rates with industry standards and competitor pricing",
            "potential_impact": "10-15% rate optimization possible",
            "priority": "medium"
        })
        
        return optimization_opportunities

# Global geofencing engine
geofencing_engine = SmartGeofencingEngine()

@geofencing_billing_bp.route('/smart-geofencing')
def geofencing_dashboard():
    """Smart geofencing and billing dashboard"""
    return render_template('smart_geofencing.html',
                         page_title="Smart Geofencing & Billing",
                         page_subtitle="Intelligent location tracking with billing optimization")

@geofencing_billing_bp.route('/api/geofence/status')
def api_geofence_status():
    """API for real-time geofence status"""
    status_data = geofencing_engine.get_real_time_geofence_status()
    return jsonify(status_data)

@geofencing_billing_bp.route('/api/geofence/expand-zone', methods=['POST'])
def api_expand_geofence():
    """API to expand geofence buffer zone"""
    data = request.get_json()
    project_id = data.get('project_id')
    new_buffer_meters = data.get('buffer_meters', 200)
    
    if project_id in geofencing_engine.project_geofences:
        geofencing_engine.project_geofences[project_id]['buffer_zone_meters'] = new_buffer_meters
        
        return jsonify({
            "success": True,
            "message": f"Buffer zone expanded to {new_buffer_meters} meters for {project_id}",
            "new_buffer": new_buffer_meters
        })
    
    return jsonify({"success": False, "error": "Project not found"})

@geofencing_billing_bp.route('/api/equipment-rates')
def api_equipment_rates():
    """API for equipment rate management"""
    return jsonify({
        "rates": geofencing_engine.equipment_rates,
        "rate_optimization": geofencing_engine._analyze_rate_optimization(),
        "timestamp": datetime.now().isoformat()
    })

@geofencing_billing_bp.route('/api/update-equipment-rate', methods=['POST'])
def api_update_equipment_rate():
    """API to update equipment rates"""
    data = request.get_json()
    equipment_type = data.get('equipment_type')
    rate_data = data.get('rate_data')
    
    if equipment_type in geofencing_engine.equipment_rates:
        geofencing_engine.equipment_rates[equipment_type].update(rate_data)
        
        return jsonify({
            "success": True,
            "message": f"Rates updated for {equipment_type}",
            "updated_rates": geofencing_engine.equipment_rates[equipment_type]
        })
    
    return jsonify({"success": False, "error": "Equipment type not found"})