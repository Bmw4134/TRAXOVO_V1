"""
TRAXOVO Business Intelligence Demo System
Demonstrates advanced autonomous capabilities with real business scenarios
"""
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

class BusinessIntelligenceDemo:
    def __init__(self):
        self.scenarios = {
            'construction': self._generate_construction_data,
            'manufacturing': self._generate_manufacturing_data,
            'logistics': self._generate_logistics_data,
            'retail': self._generate_retail_data
        }
    
    def generate_demo_scenario(self, scenario_type: str = 'construction') -> Dict[str, Any]:
        """Generate comprehensive business intelligence demo"""
        generator = self.scenarios.get(scenario_type, self._generate_construction_data)
        return generator()
    
    def _generate_construction_data(self) -> Dict[str, Any]:
        """Generate construction company intelligence data"""
        # Generate realistic equipment data
        equipment_types = ['Excavator', 'Bulldozer', 'Crane', 'Dump Truck', 'Loader', 'Grader']
        equipment_data = []
        
        for i in range(25):
            equipment = {
                'id': f'EQ-{1000 + i}',
                'type': random.choice(equipment_types),
                'location': random.choice(['Site A - Downtown Project', 'Site B - Highway Extension', 'Site C - Residential Complex', 'Maintenance Yard']),
                'status': random.choice(['Active', 'Idle', 'Maintenance', 'In Transit']),
                'operator': f'Operator {chr(65 + i % 20)}',
                'hours_today': round(random.uniform(2, 10), 1),
                'fuel_level': random.randint(20, 100),
                'maintenance_due': random.randint(0, 500),
                'cost_per_hour': random.randint(75, 200)
            }
            equipment_data.append(equipment)
        
        # Generate project timeline data
        projects = [
            {'name': 'Downtown Office Complex', 'completion': 65, 'budget_used': 72, 'days_remaining': 45},
            {'name': 'Highway Bridge Extension', 'completion': 40, 'budget_used': 38, 'days_remaining': 120},
            {'name': 'Residential Development', 'completion': 85, 'budget_used': 81, 'days_remaining': 30},
            {'name': 'Industrial Warehouse', 'completion': 25, 'budget_used': 22, 'days_remaining': 180}
        ]
        
        # Generate safety incidents
        safety_data = []
        for i in range(8):
            incident = {
                'date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'type': random.choice(['Near Miss', 'First Aid', 'Equipment Damage', 'Safety Violation']),
                'severity': random.choice(['Low', 'Medium', 'High']),
                'location': random.choice(['Site A', 'Site B', 'Site C']),
                'description': 'Safety incident requiring attention and follow-up'
            }
            safety_data.append(incident)
        
        # Advanced analytics insights
        insights = [
            f"Equipment utilization rate: {random.randint(75, 95)}% - Above industry average",
            f"Fuel efficiency improved {random.randint(8, 15)}% over last quarter",
            f"Project delivery predicted {random.randint(3, 8)} days ahead of schedule",
            f"Cost optimization identified: ${random.randint(25000, 75000)} potential savings",
            f"Safety incidents down {random.randint(20, 40)}% compared to last period"
        ]
        
        return {
            'scenario': 'Construction Intelligence Platform',
            'equipment_data': equipment_data,
            'projects': projects,
            'safety_incidents': safety_data,
            'key_insights': insights,
            'real_time_metrics': {
                'active_equipment': len([e for e in equipment_data if e['status'] == 'Active']),
                'total_hours_today': sum(e['hours_today'] for e in equipment_data),
                'fuel_cost_today': sum(e['hours_today'] * 12 for e in equipment_data if e['status'] == 'Active'),
                'projects_on_schedule': len([p for p in projects if p['completion'] >= p['budget_used'] - 5])
            }
        }
    
    def _generate_manufacturing_data(self) -> Dict[str, Any]:
        """Generate manufacturing intelligence data"""
        # Production line data
        production_lines = []
        for i in range(8):
            line = {
                'line_id': f'Line-{i+1}',
                'product': random.choice(['Widget A', 'Widget B', 'Component X', 'Assembly Y']),
                'efficiency': round(random.uniform(75, 98), 1),
                'output_today': random.randint(800, 1500),
                'target_today': random.randint(1000, 1200),
                'downtime_minutes': random.randint(0, 120),
                'quality_rate': round(random.uniform(94, 99.5), 1),
                'operators': random.randint(3, 8)
            }
            production_lines.append(line)
        
        # Quality control data
        quality_issues = []
        for i in range(12):
            issue = {
                'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 72))).strftime('%Y-%m-%d %H:%M'),
                'line': f'Line-{random.randint(1, 8)}',
                'issue_type': random.choice(['Dimensional Variance', 'Surface Defect', 'Material Issue', 'Assembly Error']),
                'severity': random.choice(['Minor', 'Major', 'Critical']),
                'resolution_time': random.randint(15, 180)
            }
            quality_issues.append(issue)
        
        insights = [
            f"Overall equipment effectiveness: {random.randint(82, 94)}%",
            f"Predictive maintenance prevented {random.randint(3, 8)} failures this month",
            f"Quality improvement: {random.randint(2, 6)}% reduction in defects",
            f"Energy consumption optimized - {random.randint(12, 25)}% reduction",
            f"Supply chain efficiency up {random.randint(8, 18)}%"
        ]
        
        return {
            'scenario': 'Manufacturing Intelligence Platform',
            'production_lines': production_lines,
            'quality_issues': quality_issues,
            'key_insights': insights,
            'real_time_metrics': {
                'total_output_today': sum(line['output_today'] for line in production_lines),
                'average_efficiency': round(sum(line['efficiency'] for line in production_lines) / len(production_lines), 1),
                'active_lines': len([line for line in production_lines if line['efficiency'] > 70]),
                'quality_score': round(sum(line['quality_rate'] for line in production_lines) / len(production_lines), 1)
            }
        }
    
    def _generate_logistics_data(self) -> Dict[str, Any]:
        """Generate logistics and fleet intelligence data"""
        # Fleet data
        vehicles = []
        for i in range(18):
            vehicle = {
                'vehicle_id': f'TRK-{200 + i}',
                'driver': f'Driver {chr(65 + i % 15)}',
                'route': random.choice(['Route 1: City Center', 'Route 2: Industrial Zone', 'Route 3: Suburbs', 'Route 4: Highway Corridor']),
                'status': random.choice(['En Route', 'Loading', 'Delivered', 'Return']),
                'miles_today': random.randint(50, 400),
                'fuel_efficiency': round(random.uniform(6.5, 12.5), 1),
                'delivery_progress': random.randint(20, 100),
                'maintenance_score': random.randint(85, 98)
            }
            vehicles.append(vehicle)
        
        # Delivery performance
        deliveries = []
        for i in range(30):
            delivery = {
                'order_id': f'ORD-{5000 + i}',
                'customer': f'Customer {chr(65 + i % 20)}',
                'scheduled_time': (datetime.now() + timedelta(hours=random.randint(-8, 24))).strftime('%H:%M'),
                'actual_time': (datetime.now() + timedelta(hours=random.randint(-8, 24))).strftime('%H:%M'),
                'status': random.choice(['Delivered', 'In Transit', 'Scheduled', 'Delayed']),
                'priority': random.choice(['Standard', 'Express', 'Critical'])
            }
            deliveries.append(delivery)
        
        insights = [
            f"Fleet efficiency: {random.randint(88, 95)}% - Industry leading",
            f"On-time delivery rate: {random.randint(92, 98)}%",
            f"Route optimization saved {random.randint(15, 35)} hours this week",
            f"Fuel costs reduced by {random.randint(8, 18)}% through smart routing",
            f"Customer satisfaction: {random.randint(4.6, 4.9)}/5.0 stars"
        ]
        
        return {
            'scenario': 'Logistics Intelligence Platform',
            'fleet_data': vehicles,
            'deliveries': deliveries,
            'key_insights': insights,
            'real_time_metrics': {
                'active_vehicles': len([v for v in vehicles if v['status'] in ['En Route', 'Loading']]),
                'total_miles_today': sum(v['miles_today'] for v in vehicles),
                'on_time_deliveries': len([d for d in deliveries if d['status'] == 'Delivered']),
                'average_fuel_efficiency': round(sum(v['fuel_efficiency'] for v in vehicles) / len(vehicles), 1)
            }
        }
    
    def _generate_retail_data(self) -> Dict[str, Any]:
        """Generate retail intelligence data"""
        # Store performance
        stores = []
        for i in range(12):
            store = {
                'store_id': f'ST-{100 + i}',
                'location': random.choice(['Downtown', 'Mall', 'Strip Center', 'Standalone']),
                'sales_today': random.randint(8000, 35000),
                'target_today': random.randint(15000, 25000),
                'foot_traffic': random.randint(150, 800),
                'conversion_rate': round(random.uniform(15, 45), 1),
                'staff_count': random.randint(8, 20),
                'avg_transaction': round(random.uniform(35, 150), 2)
            }
            stores.append(store)
        
        # Inventory alerts
        inventory_alerts = []
        products = ['Premium Widget', 'Standard Component', 'Deluxe Assembly', 'Basic Unit', 'Professional Series']
        for i in range(15):
            alert = {
                'product': random.choice(products),
                'store': f'ST-{100 + random.randint(0, 11)}',
                'current_stock': random.randint(5, 50),
                'reorder_level': random.randint(20, 100),
                'alert_type': random.choice(['Low Stock', 'Out of Stock', 'Overstock', 'Slow Moving']),
                'priority': random.choice(['High', 'Medium', 'Low'])
            }
            inventory_alerts.append(alert)
        
        insights = [
            f"Sales performance: {random.randint(105, 125)}% of target",
            f"Inventory turnover improved {random.randint(8, 20)}%",
            f"Customer retention rate: {random.randint(68, 85)}%",
            f"Profit margin optimization: +{random.randint(3, 8)}% increase",
            f"Staff productivity up {random.randint(12, 28)}%"
        ]
        
        return {
            'scenario': 'Retail Intelligence Platform',
            'store_performance': stores,
            'inventory_alerts': inventory_alerts,
            'key_insights': insights,
            'real_time_metrics': {
                'total_sales_today': sum(store['sales_today'] for store in stores),
                'stores_above_target': len([s for s in stores if s['sales_today'] >= s['target_today']]),
                'total_foot_traffic': sum(store['foot_traffic'] for store in stores),
                'average_conversion': round(sum(store['conversion_rate'] for store in stores) / len(stores), 1)
            }
        }
    
    def generate_predictive_analytics(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictive analytics and recommendations"""
        scenario = scenario_data['scenario']
        
        if 'Construction' in scenario:
            return {
                'predictions': [
                    {'metric': 'Project Completion', 'prediction': 'Downtown project will finish 5 days early', 'confidence': 87},
                    {'metric': 'Equipment Utilization', 'prediction': 'Crane utilization will increase 15% next week', 'confidence': 92},
                    {'metric': 'Cost Optimization', 'prediction': '$45,000 savings opportunity identified', 'confidence': 78}
                ],
                'recommendations': [
                    'Reallocate excavator from Site C to Site B for optimal efficiency',
                    'Schedule preventive maintenance for 3 units before failure occurs',
                    'Optimize fuel delivery routes to reduce costs by 12%'
                ]
            }
        elif 'Manufacturing' in scenario:
            return {
                'predictions': [
                    {'metric': 'Production Output', 'prediction': '8% increase in output next quarter', 'confidence': 84},
                    {'metric': 'Quality Issues', 'prediction': 'Line-3 will require attention in 48 hours', 'confidence': 91},
                    {'metric': 'Maintenance', 'prediction': 'Preventive maintenance will prevent 2 breakdowns', 'confidence': 89}
                ],
                'recommendations': [
                    'Adjust Line-5 parameters to increase efficiency by 6%',
                    'Implement quality control enhancement on Lines 2, 4, 7',
                    'Schedule operator training to reduce setup time by 15%'
                ]
            }
        elif 'Logistics' in scenario:
            return {
                'predictions': [
                    {'metric': 'Delivery Performance', 'prediction': 'On-time rate will improve to 96% next month', 'confidence': 88},
                    {'metric': 'Route Optimization', 'prediction': '25 hours savings with new routing algorithm', 'confidence': 93},
                    {'metric': 'Vehicle Maintenance', 'prediction': 'TRK-205 requires service within 500 miles', 'confidence': 86}
                ],
                'recommendations': [
                    'Implement dynamic routing for 18% efficiency gain',
                    'Consolidate deliveries on Route 3 for fuel savings',
                    'Schedule maintenance for 4 vehicles during low-demand period'
                ]
            }
        else:  # Retail
            return {
                'predictions': [
                    {'metric': 'Sales Forecast', 'prediction': '22% sales increase expected next month', 'confidence': 82},
                    {'metric': 'Inventory Optimization', 'prediction': 'Premium Widget will be out of stock in 3 days', 'confidence': 94},
                    {'metric': 'Staff Performance', 'prediction': 'Store ST-105 needs additional staffing', 'confidence': 76}
                ],
                'recommendations': [
                    'Increase inventory levels for top 5 performing products',
                    'Transfer staff from ST-103 to ST-105 for optimal coverage',
                    'Implement cross-selling strategy to increase average transaction by $23'
                ]
            }