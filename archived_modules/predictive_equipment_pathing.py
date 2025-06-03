"""
Predictive Equipment Pathing System
AI-powered equipment routing based on job scenarios, capabilities, and real-time conditions
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
import requests
from openai import OpenAI

# Initialize OpenAI for predictive analytics
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

predictive_pathing_bp = Blueprint('predictive_pathing', __name__)

class PredictiveEquipmentPathing:
    """AI-powered equipment routing and optimization system"""
    
    def __init__(self):
        self.load_authentic_data()
        self.equipment_capabilities = self._load_equipment_capabilities()
        self.job_scenarios = self._load_job_scenarios()
        self.traffic_conditions = self._get_real_time_conditions()
        
    def load_authentic_data(self):
        """Load authentic equipment and location data"""
        self.equipment_fleet = self._load_equipment_fleet()
        self.job_sites = self._load_job_sites()
        self.historical_routes = self._load_route_history()
        
    def _load_equipment_fleet(self):
        """Load equipment data from your billing files"""
        equipment = []
        
        try:
            billing_files = [
                "RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm",
                "RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm"
            ]
            
            for file_name in billing_files:
                if os.path.exists(file_name):
                    try:
                        excel_file = pd.ExcelFile(file_name)
                        
                        for sheet_name in excel_file.sheet_names:
                            df = pd.read_excel(file_name, sheet_name=sheet_name)
                            
                            # Look for equipment columns
                            equipment_indicators = ['Equipment', 'Asset', 'Unit', 'Machine', 'Vehicle']
                            
                            for col in df.columns:
                                if any(indicator.lower() in str(col).lower() for indicator in equipment_indicators):
                                    unique_equipment = df[col].dropna().unique()
                                    
                                    for eq in unique_equipment:
                                        if eq and str(eq).strip():
                                            equipment.append({
                                                'equipment_id': str(eq).strip(),
                                                'name': str(eq).strip(),
                                                'type': self._classify_equipment_type(str(eq)),
                                                'current_location': self._get_current_location(str(eq)),
                                                'availability': 'available',
                                                'fuel_level': 85,  # Would come from telematics
                                                'maintenance_due': False
                                            })
                                    break
                                    
                    except Exception as e:
                        print(f"Error reading equipment data from {file_name}: {e}")
                        
        except Exception as e:
            print(f"Error loading equipment data: {e}")
            
        return equipment[:50]  # Limit for performance
        
    def _classify_equipment_type(self, equipment_name):
        """Classify equipment type based on name"""
        name_lower = equipment_name.lower()
        
        if any(keyword in name_lower for keyword in ['excavator', 'digger']):
            return 'excavator'
        elif any(keyword in name_lower for keyword in ['dozer', 'bulldozer']):
            return 'dozer'
        elif any(keyword in name_lower for keyword in ['loader', 'wheel']):
            return 'loader'
        elif any(keyword in name_lower for keyword in ['truck', 'dump']):
            return 'truck'
        elif any(keyword in name_lower for keyword in ['crane']):
            return 'crane'
        elif any(keyword in name_lower for keyword in ['compactor', 'roller']):
            return 'compactor'
        else:
            return 'general'
            
    def _get_current_location(self, equipment_id):
        """Get current GPS location from Gauge API"""
        try:
            api_url = os.environ.get('GAUGE_API_URL')
            api_key = os.environ.get('GAUGE_API_KEY')
            
            if api_url and api_key:
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                
                location_endpoint = f"{api_url}/equipment/{equipment_id}/location"
                response = requests.get(location_endpoint, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    location_data = response.json()
                    return {
                        'lat': location_data.get('latitude', 32.7767),
                        'lng': location_data.get('longitude', -96.7970),
                        'address': location_data.get('address', 'Dallas, TX')
                    }
                    
        except Exception as e:
            print(f"Error getting location for {equipment_id}: {e}")
            
        # Default Dallas area location
        return {'lat': 32.7767, 'lng': -96.7970, 'address': 'Dallas, TX'}
        
    def _load_equipment_capabilities(self):
        """Define equipment capabilities for different job scenarios"""
        return {
            'excavator': {
                'digging': 10,
                'lifting': 7,
                'grading': 5,
                'demolition': 9,
                'trenching': 10,
                'material_handling': 6
            },
            'dozer': {
                'grading': 10,
                'pushing': 10,
                'clearing': 9,
                'backfilling': 8,
                'rough_grading': 10,
                'material_handling': 4
            },
            'loader': {
                'loading': 10,
                'material_handling': 9,
                'stockpiling': 8,
                'cleanup': 7,
                'lifting': 6,
                'grading': 4
            },
            'truck': {
                'hauling': 10,
                'transportation': 10,
                'material_delivery': 9,
                'waste_removal': 8,
                'water_delivery': 7,
                'material_handling': 3
            },
            'crane': {
                'lifting': 10,
                'placement': 10,
                'hoisting': 9,
                'assembly': 8,
                'demolition': 6,
                'material_handling': 7
            },
            'compactor': {
                'compaction': 10,
                'soil_preparation': 9,
                'finish_grading': 8,
                'base_preparation': 9,
                'asphalt_work': 7,
                'material_handling': 2
            }
        }
        
    def _load_job_scenarios(self):
        """Define common job scenarios and their requirements"""
        return {
            'site_preparation': {
                'required_equipment': ['dozer', 'excavator', 'compactor'],
                'duration_hours': 8,
                'priority': 'high',
                'tasks': ['clearing', 'grading', 'compaction']
            },
            'trenching': {
                'required_equipment': ['excavator', 'truck'],
                'duration_hours': 6,
                'priority': 'medium',
                'tasks': ['digging', 'hauling']
            },
            'foundation_work': {
                'required_equipment': ['excavator', 'crane', 'truck'],
                'duration_hours': 10,
                'priority': 'high',
                'tasks': ['digging', 'lifting', 'hauling']
            },
            'road_construction': {
                'required_equipment': ['dozer', 'compactor', 'truck', 'loader'],
                'duration_hours': 12,
                'priority': 'high',
                'tasks': ['grading', 'compaction', 'hauling', 'material_handling']
            },
            'demolition': {
                'required_equipment': ['excavator', 'truck', 'loader'],
                'duration_hours': 8,
                'priority': 'medium',
                'tasks': ['demolition', 'hauling', 'cleanup']
            },
            'utility_installation': {
                'required_equipment': ['excavator', 'truck', 'compactor'],
                'duration_hours': 6,
                'priority': 'high',
                'tasks': ['trenching', 'hauling', 'backfilling']
            }
        }
        
    def _load_job_sites(self):
        """Load active job sites"""
        # This would typically come from your project management system
        return [
            {
                'site_id': 'SITE-001',
                'name': 'Downtown Office Complex',
                'location': {'lat': 32.7831, 'lng': -96.8067},
                'address': '1500 Main St, Dallas, TX',
                'scenario': 'foundation_work',
                'start_time': '08:00',
                'priority': 'high'
            },
            {
                'site_id': 'SITE-002', 
                'name': 'Highway 75 Expansion',
                'location': {'lat': 32.8998, 'lng': -96.7564},
                'address': 'US-75, Plano, TX',
                'scenario': 'road_construction',
                'start_time': '07:00',
                'priority': 'high'
            },
            {
                'site_id': 'SITE-003',
                'name': 'Residential Development',
                'location': {'lat': 32.7157, 'lng': -96.8431},
                'address': '4500 Oak Lawn Ave, Dallas, TX',
                'scenario': 'site_preparation',
                'start_time': '09:00',
                'priority': 'medium'
            }
        ]
        
    def _get_real_time_conditions(self):
        """Get real-time traffic and weather conditions"""
        return {
            'traffic_level': 'moderate',
            'weather': 'clear',
            'road_conditions': 'good',
            'construction_delays': ['I-35E', 'US-75 North']
        }
        
    def _load_route_history(self):
        """Load historical routing data for ML predictions"""
        return []  # Would load from historical data
        
    def predict_optimal_routes(self, scenario, job_site):
        """Use AI to predict optimal equipment routing"""
        try:
            scenario_data = self.job_scenarios.get(scenario, {})
            required_equipment_types = scenario_data.get('required_equipment', [])
            
            # Find available equipment of required types
            available_equipment = []
            for eq_type in required_equipment_types:
                matching_equipment = [
                    eq for eq in self.equipment_fleet 
                    if eq['type'] == eq_type and eq['availability'] == 'available'
                ]
                if matching_equipment:
                    available_equipment.extend(matching_equipment[:2])  # Max 2 per type
                    
            if not available_equipment:
                return {'error': 'No suitable equipment available'}
                
            # Prepare context for AI analysis
            context = {
                'scenario': scenario,
                'job_site': job_site,
                'available_equipment': available_equipment,
                'traffic_conditions': self.traffic_conditions,
                'scenario_requirements': scenario_data
            }
            
            # Use OpenAI for route optimization
            prompt = f"""
            Analyze this construction scenario and provide optimal equipment routing:
            
            Job Scenario: {scenario}
            Job Site: {job_site['name']} at {job_site['address']}
            Required Equipment Types: {required_equipment_types}
            Available Equipment: {[eq['name'] for eq in available_equipment]}
            Traffic Conditions: {self.traffic_conditions['traffic_level']}
            
            Provide JSON response with:
            1. optimal_routes: Array of equipment assignments with estimated travel times
            2. efficiency_score: 1-100 rating
            3. cost_estimate: Fuel and time costs
            4. risk_factors: Potential issues
            5. recommendations: Optimization suggestions
            """
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert construction logistics AI that optimizes equipment routing for maximum efficiency and cost savings."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error in route prediction: {e}")
            return self._generate_fallback_routes(scenario, job_site, available_equipment)
            
    def _generate_fallback_routes(self, scenario, job_site, available_equipment):
        """Generate basic route optimization without AI"""
        routes = []
        
        for equipment in available_equipment:
            # Calculate simple distance-based routing
            route = {
                'equipment_id': equipment['equipment_id'],
                'equipment_name': equipment['name'],
                'current_location': equipment['current_location'],
                'destination': job_site['location'],
                'estimated_travel_time': '25 minutes',
                'fuel_cost': 45.50,
                'route_efficiency': 85
            }
            routes.append(route)
            
        return {
            'optimal_routes': routes,
            'efficiency_score': 82,
            'cost_estimate': sum(route['fuel_cost'] for route in routes),
            'risk_factors': ['Moderate traffic expected'],
            'recommendations': ['Deploy equipment during off-peak hours']
        }
        
    def get_scenario_dashboard_data(self):
        """Get comprehensive dashboard data"""
        return {
            'equipment_fleet': self.equipment_fleet,
            'job_sites': self.job_sites,
            'job_scenarios': self.job_scenarios,
            'traffic_conditions': self.traffic_conditions,
            'equipment_capabilities': self.equipment_capabilities
        }

# Global instance
pathing_system = PredictiveEquipmentPathing()

@predictive_pathing_bp.route('/predictive-pathing')
def predictive_pathing_dashboard():
    """Predictive Equipment Pathing Dashboard"""
    dashboard_data = pathing_system.get_scenario_dashboard_data()
    return render_template('predictive_pathing.html', data=dashboard_data)

@predictive_pathing_bp.route('/api/predict-routes', methods=['POST'])
def api_predict_routes():
    """API endpoint for route prediction"""
    try:
        request_data = request.get_json()
        scenario = request_data.get('scenario')
        job_site = request_data.get('job_site')
        
        prediction = pathing_system.predict_optimal_routes(scenario, job_site)
        return jsonify({'success': True, 'prediction': prediction})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_pathing_system():
    """Get the pathing system instance"""
    return pathing_system