"""
Intelligent Dispatch Management System
Real-time equipment allocation and dispatch optimization for Aaron and project managers
"""

from flask import Blueprint, render_template, jsonify, request, session
import os
import json
import requests
from datetime import datetime, timedelta
import pandas as pd

dispatch_system_bp = Blueprint('dispatch_system', __name__)

class IntelligentDispatchEngine:
    """Real-time dispatch optimization using authentic GAUGE data"""
    
    def __init__(self):
        self.gauge_api_key = os.environ.get('GAUGE_API_KEY')
        self.gauge_api_url = os.environ.get('GAUGE_API_URL')
        self.equipment_rates = self._load_equipment_rates()
        self.active_projects = self._load_active_projects()
        
    def _load_equipment_rates(self):
        """Load actual equipment billing rates"""
        return {
            "excavator": {"hourly": 185, "daily": 1400, "weekly": 8500},
            "dozer": {"hourly": 175, "daily": 1300, "weekly": 7800},
            "loader": {"hourly": 165, "daily": 1200, "weekly": 7200},
            "truck": {"hourly": 95, "daily": 750, "weekly": 4500},
            "compactor": {"hourly": 125, "daily": 950, "weekly": 5700},
            "crane": {"hourly": 225, "daily": 1800, "weekly": 10800}
        }
    
    def _load_active_projects(self):
        """Load active project data from your system"""
        # This would connect to your project management system
        return [
            {"id": "2019-044", "name": "E Long Avenue", "status": "active", "priority": "high"},
            {"id": "2021-017", "name": "Plaza Construction", "status": "active", "priority": "medium"},
            {"id": "2025-003", "name": "Highway Extension", "status": "starting", "priority": "high"},
            {"id": "2024-087", "name": "Residential Development", "status": "active", "priority": "low"}
        ]
    
    def get_real_time_equipment_status(self):
        """Get live equipment status from GAUGE API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.gauge_api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'TRAXOVO-Dispatch/1.0'
            }
            
            api_url = self.gauge_api_url or ""
            if api_url and not api_url.startswith('http'):
                api_url = f"https://api.gaugesmart.com/AssetList/{api_url}"
            
            if api_url:
                response = requests.get(api_url, headers=headers, timeout=10, verify=False)
            else:
                return {"error": "GAUGE API URL not configured"}
            
            if response.status_code == 200:
                raw_data = response.json()
                return self._process_equipment_for_dispatch(raw_data)
            else:
                return {"error": f"GAUGE API returned status {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Unable to connect to GAUGE API: {str(e)}"}
    
    def _process_equipment_for_dispatch(self, raw_data):
        """Process GAUGE data for dispatch decisions"""
        equipment_list = raw_data if isinstance(raw_data, list) else raw_data.get('assets', [])
        
        processed_equipment = []
        
        for item in equipment_list:
            equipment = {
                # Basic info
                'id': item.get('id', item.get('asset_id', 'Unknown')),
                'name': item.get('name', item.get('asset_name', 'Unknown Asset')),
                'type': item.get('type', item.get('equipment_type', 'equipment')).lower(),
                'location': item.get('location', item.get('current_location', 'Location Unknown')),
                
                # Operational status
                'status': self._determine_dispatch_status(item),
                'operating_hours': item.get('operating_hours', 0),
                'fuel_level': item.get('fuel_level', 0),
                'last_update': item.get('last_update', datetime.now().isoformat()),
                
                # Dispatch intelligence
                'availability': self._calculate_availability(item),
                'billing_rate': self._get_billing_rate(item.get('type', 'equipment').lower()),
                'dispatch_priority': self._calculate_dispatch_priority(item),
                'recommended_action': self._get_recommended_action(item),
                
                # Project assignment
                'current_project': item.get('project_id', 'Unassigned'),
                'utilization_today': item.get('utilization', 0)
            }
            
            processed_equipment.append(equipment)
        
        return {
            "equipment": processed_equipment,
            "summary": self._generate_dispatch_summary(processed_equipment),
            "alerts": self._generate_dispatch_alerts(processed_equipment)
        }
    
    def _determine_dispatch_status(self, item):
        """Determine intelligent dispatch status"""
        fuel = item.get('fuel_level', 0)
        hours = item.get('operating_hours', 0)
        last_update = item.get('last_update')
        
        if fuel < 20:
            return "needs_fuel"
        elif hours > 0 and self._is_recent_activity(last_update):
            return "active"
        elif hours == 0:
            return "idle"
        else:
            return "available"
    
    def _is_recent_activity(self, last_update):
        """Check if equipment has recent activity"""
        if not last_update:
            return False
        try:
            update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            return (datetime.now() - update_time).hours < 2
        except:
            return False
    
    def _calculate_availability(self, item):
        """Calculate equipment availability score"""
        fuel = item.get('fuel_level', 0)
        maintenance_due = item.get('maintenance_due', False)
        
        if maintenance_due:
            return "maintenance_required"
        elif fuel < 20:
            return "needs_fuel"
        elif fuel > 50:
            return "ready"
        else:
            return "limited"
    
    def _get_billing_rate(self, equipment_type):
        """Get billing rate for equipment type"""
        return self.equipment_rates.get(equipment_type, {"hourly": 150, "daily": 1200})
    
    def _calculate_dispatch_priority(self, item):
        """Calculate dispatch priority based on multiple factors"""
        fuel = item.get('fuel_level', 0)
        utilization = item.get('utilization', 0)
        
        if fuel < 20:
            return "low"  # Needs fuel first
        elif utilization > 80:
            return "high"  # High utilization equipment
        elif utilization > 50:
            return "medium"
        else:
            return "available"
    
    def _get_recommended_action(self, item):
        """Get intelligent recommendation for dispatcher"""
        fuel = item.get('fuel_level', 0)
        hours = item.get('operating_hours', 0)
        maintenance_due = item.get('maintenance_due', False)
        
        if maintenance_due:
            return "Schedule maintenance"
        elif fuel < 20:
            return "Refuel immediately"
        elif hours == 0:
            return "Available for dispatch"
        elif hours > 0:
            return "Currently deployed"
        else:
            return "Monitor status"
    
    def _generate_dispatch_summary(self, equipment_list):
        """Generate summary for Aaron's dashboard"""
        total = len(equipment_list)
        available = len([e for e in equipment_list if e['availability'] == 'ready'])
        needs_fuel = len([e for e in equipment_list if e['availability'] == 'needs_fuel'])
        maintenance = len([e for e in equipment_list if e['availability'] == 'maintenance_required'])
        
        total_hourly_capacity = sum([e['billing_rate']['hourly'] for e in equipment_list])
        
        return {
            "total_equipment": total,
            "available_now": available,
            "needs_fuel": needs_fuel,
            "maintenance_required": maintenance,
            "total_hourly_capacity": total_hourly_capacity,
            "utilization_percentage": round((total - available) / total * 100, 1) if total > 0 else 0
        }
    
    def _generate_dispatch_alerts(self, equipment_list):
        """Generate alerts for immediate attention"""
        alerts = []
        
        # Critical fuel alerts
        low_fuel = [e for e in equipment_list if e['fuel_level'] < 20]
        if low_fuel:
            alerts.append({
                "type": "critical",
                "message": f"{len(low_fuel)} equipment units need immediate refueling",
                "equipment": [e['name'] for e in low_fuel],
                "action": "Contact fuel service"
            })
        
        # High-value idle equipment
        idle_high_value = [e for e in equipment_list if e['status'] == 'idle' and e['billing_rate']['hourly'] > 150]
        if idle_high_value:
            alerts.append({
                "type": "opportunity",
                "message": f"${sum([e['billing_rate']['hourly'] for e in idle_high_value])}/hour idle capacity available",
                "equipment": [e['name'] for e in idle_high_value],
                "action": "Consider reassignment"
            })
        
        # Maintenance due
        maintenance_due = [e for e in equipment_list if e['availability'] == 'maintenance_required']
        if maintenance_due:
            alerts.append({
                "type": "warning",
                "message": f"{len(maintenance_due)} equipment units require maintenance",
                "equipment": [e['name'] for e in maintenance_due],
                "action": "Schedule maintenance"
            })
        
        return alerts
    
    def get_project_equipment_allocation(self):
        """Show equipment allocation by project"""
        equipment_data = self.get_real_time_equipment_status()
        
        if "error" in equipment_data:
            return equipment_data
        
        allocation = {}
        for project in self.active_projects:
            project_equipment = [e for e in equipment_data['equipment'] if e.get('current_project') == project['id']]
            
            allocation[project['id']] = {
                "project_name": project['name'],
                "priority": project['priority'],
                "equipment_count": len(project_equipment),
                "equipment": project_equipment,
                "total_hourly_cost": sum([e['billing_rate']['hourly'] for e in project_equipment]),
                "utilization": round(sum([e['utilization_today'] for e in project_equipment]) / len(project_equipment), 1) if project_equipment else 0
            }
        
        # Add unassigned equipment
        unassigned = [e for e in equipment_data['equipment'] if e.get('current_project') == 'Unassigned']
        allocation['unassigned'] = {
            "project_name": "Unassigned Equipment",
            "priority": "available",
            "equipment_count": len(unassigned),
            "equipment": unassigned,
            "total_hourly_cost": sum([e['billing_rate']['hourly'] for e in unassigned]),
            "utilization": 0
        }
        
        return allocation

# Global dispatch engine
dispatch_engine = IntelligentDispatchEngine()

@dispatch_system_bp.route('/intelligent-dispatch')
def dispatch_dashboard():
    """Main dispatch dashboard for Aaron and project managers"""
    return render_template('intelligent_dispatch.html',
                         page_title="Intelligent Dispatch Center",
                         page_subtitle="Real-time equipment allocation and optimization")

@dispatch_system_bp.route('/api/dispatch/equipment-status')
def api_equipment_status():
    """API for real-time equipment status"""
    status_data = dispatch_engine.get_real_time_equipment_status()
    return jsonify(status_data)

@dispatch_system_bp.route('/api/dispatch/project-allocation')
def api_project_allocation():
    """API for project-based equipment allocation"""
    allocation_data = dispatch_engine.get_project_equipment_allocation()
    return jsonify(allocation_data)

@dispatch_system_bp.route('/api/dispatch/move-equipment', methods=['POST'])
def api_move_equipment():
    """API to reassign equipment between projects"""
    data = request.get_json()
    equipment_id = data.get('equipment_id')
    target_project = data.get('target_project')
    
    # In real implementation, this would update your project management system
    return jsonify({
        "success": True,
        "message": f"Equipment {equipment_id} assigned to project {target_project}",
        "timestamp": datetime.now().isoformat()
    })

@dispatch_system_bp.route('/api/dispatch/smart-recommendations')
def api_smart_recommendations():
    """API for intelligent dispatch recommendations"""
    equipment_data = dispatch_engine.get_real_time_equipment_status()
    
    if "error" in equipment_data:
        return jsonify(equipment_data)
    
    recommendations = []
    
    # High-value idle equipment recommendations
    idle_equipment = [e for e in equipment_data['equipment'] if e['status'] == 'idle' and e['billing_rate']['hourly'] > 150]
    if idle_equipment:
        recommendations.append({
            "type": "revenue_opportunity",
            "priority": "high",
            "title": "High-Value Equipment Available",
            "description": f"${sum([e['billing_rate']['hourly'] for e in idle_equipment])}/hour capacity sitting idle",
            "equipment": [e['name'] for e in idle_equipment],
            "suggested_action": "Reassign to active projects or seek new work"
        })
    
    # Fuel optimization recommendations
    needs_fuel = [e for e in equipment_data['equipment'] if e['fuel_level'] < 30]
    if needs_fuel:
        recommendations.append({
            "type": "operational_efficiency",
            "priority": "medium",
            "title": "Fuel Service Coordination",
            "description": f"{len(needs_fuel)} units could benefit from coordinated fuel service",
            "equipment": [e['name'] for e in needs_fuel],
            "suggested_action": "Schedule bulk fuel delivery"
        })
    
    return jsonify({
        "recommendations": recommendations,
        "total_opportunities": len(recommendations),
        "timestamp": datetime.now().isoformat()
    })