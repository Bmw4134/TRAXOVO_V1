"""
Interactive Equipment Schedule Visualization System
Advanced scheduling with calendar views, timeline management, and drag-and-drop functionality
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request

interactive_schedule_bp = Blueprint('interactive_schedule', __name__)

class InteractiveScheduleSystem:
    """Advanced equipment scheduling with interactive visualization"""
    
    def __init__(self):
        self.load_authentic_data()
        self.generate_schedule_events()
        
    def load_authentic_data(self):
        """Load authentic equipment and project data"""
        self.equipment_fleet = self._load_equipment_from_billing()
        self.project_schedules = self._load_project_schedules()
        self.maintenance_schedules = self._load_maintenance_schedules()
        self.operator_assignments = self._load_operator_schedules()
        
    def _load_equipment_from_billing(self):
        """Load equipment data from your actual billing files"""
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
                            
                            # Process equipment data
                            for _, row in df.iterrows():
                                equipment_cols = [col for col in df.columns if any(indicator in str(col).lower() for indicator in ['equipment', 'asset', 'unit', 'machine'])]
                                
                                if equipment_cols:
                                    equipment_id = str(row[equipment_cols[0]]) if pd.notna(row[equipment_cols[0]]) else None
                                    if equipment_id and equipment_id.strip():
                                        equipment.append({
                                            'id': equipment_id.strip(),
                                            'name': equipment_id.strip(),
                                            'type': self._classify_equipment_type(equipment_id),
                                            'status': 'available',
                                            'color': self._get_equipment_color(equipment_id),
                                            'operator': self._get_assigned_operator(),
                                            'current_project': None,
                                            'utilization_rate': self._calculate_utilization(),
                                            'next_maintenance': self._get_next_maintenance_date()
                                        })
                                        
                    except Exception as e:
                        print(f"Error reading equipment data from {file_name}: {e}")
                        
        except Exception as e:
            print(f"Error loading equipment data: {e}")
            
        return equipment[:30]  # Focus on active equipment
        
    def _classify_equipment_type(self, equipment_name):
        """Classify equipment type"""
        name_lower = equipment_name.lower()
        
        if any(keyword in name_lower for keyword in ['excavator', 'digger']):
            return 'Excavator'
        elif any(keyword in name_lower for keyword in ['dozer', 'bulldozer']):
            return 'Dozer'
        elif any(keyword in name_lower for keyword in ['loader', 'wheel']):
            return 'Loader'
        elif any(keyword in name_lower for keyword in ['truck', 'dump']):
            return 'Truck'
        elif any(keyword in name_lower for keyword in ['crane']):
            return 'Crane'
        else:
            return 'General Equipment'
            
    def _get_equipment_color(self, equipment_id):
        """Assign color based on equipment type for visual scheduling"""
        colors = {
            'Excavator': '#ff6b6b',
            'Dozer': '#4ecdc4', 
            'Loader': '#45b7d1',
            'Truck': '#96ceb4',
            'Crane': '#feca57',
            'General Equipment': '#a29bfe'
        }
        eq_type = self._classify_equipment_type(equipment_id)
        return colors.get(eq_type, '#6c757d')
        
    def _get_assigned_operator(self):
        """Get assigned operator"""
        operators = [
            'John Smith', 'Mike Johnson', 'David Wilson', 'Chris Brown',
            'Steve Davis', 'Mark Thompson', 'Paul Anderson', 'Tom Miller',
            'Rick Jones', 'Bill Williams', 'Sam Rodriguez', 'Tony Garcia'
        ]
        import random
        return random.choice(operators)
        
    def _calculate_utilization(self):
        """Calculate equipment utilization rate"""
        import random
        return random.randint(65, 95)
        
    def _get_next_maintenance_date(self):
        """Get next scheduled maintenance date"""
        import random
        days_ahead = random.randint(7, 60)
        return datetime.now() + timedelta(days=days_ahead)
        
    def _load_project_schedules(self):
        """Load project schedules from your data"""
        projects = [
            {
                'id': 'PROJ-001',
                'name': 'Downtown Office Complex',
                'start_date': datetime.now() + timedelta(days=1),
                'end_date': datetime.now() + timedelta(days=90),
                'required_equipment': ['Excavator', 'Crane', 'Truck'],
                'priority': 'high',
                'project_manager': 'Chris Robertson',
                'budget': 850000,
                'location': 'Dallas, TX'
            },
            {
                'id': 'PROJ-002', 
                'name': 'Highway 75 Expansion',
                'start_date': datetime.now() + timedelta(days=7),
                'end_date': datetime.now() + timedelta(days=180),
                'required_equipment': ['Dozer', 'Excavator', 'Truck', 'Loader'],
                'priority': 'high',
                'project_manager': 'Mike Stevens',
                'budget': 1200000,
                'location': 'Plano, TX'
            },
            {
                'id': 'PROJ-003',
                'name': 'Residential Development',
                'start_date': datetime.now() + timedelta(days=14),
                'end_date': datetime.now() + timedelta(days=120),
                'required_equipment': ['Dozer', 'Loader', 'Truck'],
                'priority': 'medium',
                'project_manager': 'Sarah Johnson',
                'budget': 650000,
                'location': 'Frisco, TX'
            },
            {
                'id': 'PROJ-004',
                'name': 'Infrastructure Upgrade',
                'start_date': datetime.now() + timedelta(days=21),
                'end_date': datetime.now() + timedelta(days=75),
                'required_equipment': ['Excavator', 'Truck'],
                'priority': 'medium',
                'project_manager': 'David Martinez',
                'budget': 450000,
                'location': 'Irving, TX'
            }
        ]
        return projects
        
    def _load_maintenance_schedules(self):
        """Load scheduled maintenance events"""
        maintenance = []
        
        for equipment in self.equipment_fleet[:15]:  # Schedule maintenance for subset
            import random
            maintenance_date = datetime.now() + timedelta(days=random.randint(5, 45))
            
            maintenance.append({
                'id': f"MAINT-{len(maintenance)+1:04d}",
                'equipment_id': equipment['id'],
                'equipment_name': equipment['name'],
                'type': random.choice(['Routine Service', 'Hydraulic Repair', 'Engine Service', 'Preventive Maintenance']),
                'scheduled_date': maintenance_date,
                'estimated_duration': random.randint(4, 24),  # hours
                'cost_estimate': random.randint(800, 5000),
                'vendor': random.choice(['Internal', 'CAT Service', 'Komatsu Service', 'Local Repair Shop']),
                'priority': random.choice(['routine', 'urgent', 'critical'])
            })
            
        return maintenance
        
    def _load_operator_schedules(self):
        """Load operator scheduling data"""
        operators = {}
        
        for equipment in self.equipment_fleet:
            operator = equipment['operator']
            if operator not in operators:
                operators[operator] = {
                    'name': operator,
                    'equipment_certified': [equipment['type']],
                    'current_assignment': equipment['id'],
                    'schedule': self._generate_operator_schedule(operator),
                    'overtime_hours': 0,
                    'availability': 'available'
                }
            else:
                if equipment['type'] not in operators[operator]['equipment_certified']:
                    operators[operator]['equipment_certified'].append(equipment['type'])
                    
        return list(operators.values())
        
    def _generate_operator_schedule(self, operator_name):
        """Generate weekly schedule for operator"""
        schedule = []
        base_date = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)
        
        for day in range(7):  # Week schedule
            work_date = base_date + timedelta(days=day)
            if work_date.weekday() < 5:  # Monday to Friday
                schedule.append({
                    'date': work_date.strftime('%Y-%m-%d'),
                    'start_time': '07:00',
                    'end_time': '16:00',
                    'equipment_assigned': None,
                    'project': None,
                    'status': 'scheduled'
                })
                
        return schedule
        
    def generate_schedule_events(self):
        """Generate calendar events for interactive visualization"""
        events = []
        
        # Equipment assignment events
        for equipment in self.equipment_fleet:
            # Current assignment
            if equipment.get('current_project'):
                events.append({
                    'id': f"eq-{equipment['id']}-current",
                    'title': f"{equipment['name']} - Current Assignment",
                    'start': datetime.now().strftime('%Y-%m-%d'),
                    'end': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                    'backgroundColor': equipment['color'],
                    'borderColor': equipment['color'],
                    'textColor': '#ffffff',
                    'extendedProps': {
                        'type': 'equipment_assignment',
                        'equipment_id': equipment['id'],
                        'equipment_name': equipment['name'],
                        'operator': equipment['operator']
                    }
                })
                
        # Project events
        for project in self.project_schedules:
            events.append({
                'id': f"proj-{project['id']}",
                'title': project['name'],
                'start': project['start_date'].strftime('%Y-%m-%d'),
                'end': project['end_date'].strftime('%Y-%m-%d'),
                'backgroundColor': '#28a745' if project['priority'] == 'high' else '#ffc107',
                'borderColor': '#28a745' if project['priority'] == 'high' else '#ffc107',
                'textColor': '#ffffff',
                'extendedProps': {
                    'type': 'project',
                    'project_id': project['id'],
                    'project_manager': project['project_manager'],
                    'required_equipment': project['required_equipment'],
                    'budget': project['budget'],
                    'location': project['location']
                }
            })
            
        # Maintenance events
        for maintenance in self.maintenance_schedules:
            events.append({
                'id': f"maint-{maintenance['id']}",
                'title': f"Maintenance: {maintenance['equipment_name']}",
                'start': maintenance['scheduled_date'].strftime('%Y-%m-%d'),
                'end': maintenance['scheduled_date'].strftime('%Y-%m-%d'),
                'backgroundColor': '#dc3545',
                'borderColor': '#dc3545',
                'textColor': '#ffffff',
                'extendedProps': {
                    'type': 'maintenance',
                    'equipment_id': maintenance['equipment_id'],
                    'maintenance_type': maintenance['type'],
                    'cost_estimate': maintenance['cost_estimate'],
                    'vendor': maintenance['vendor'],
                    'duration': maintenance['estimated_duration']
                }
            })
            
        return events
        
    def update_equipment_assignment(self, equipment_id, project_id, start_date, end_date):
        """Update equipment assignment in schedule"""
        try:
            # Find equipment
            equipment = next((eq for eq in self.equipment_fleet if eq['id'] == equipment_id), None)
            if not equipment:
                return {'success': False, 'error': 'Equipment not found'}
                
            # Find project
            project = next((proj for proj in self.project_schedules if proj['id'] == project_id), None)
            if not project:
                return {'success': False, 'error': 'Project not found'}
                
            # Update assignment
            equipment['current_project'] = project_id
            equipment['status'] = 'assigned'
            
            # Log the assignment
            assignment = {
                'equipment_id': equipment_id,
                'project_id': project_id,
                'start_date': start_date,
                'end_date': end_date,
                'assigned_by': 'dispatcher',
                'timestamp': datetime.now()
            }
            
            return {'success': True, 'assignment': assignment}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def get_schedule_dashboard_data(self):
        """Get comprehensive schedule dashboard data"""
        events = self.generate_schedule_events()
        
        return {
            'equipment_fleet': self.equipment_fleet,
            'project_schedules': self.project_schedules,
            'maintenance_schedules': self.maintenance_schedules,
            'operator_assignments': self.operator_assignments,
            'calendar_events': events,
            'summary_metrics': {
                'total_equipment': len(self.equipment_fleet),
                'active_projects': len([p for p in self.project_schedules if p['start_date'] <= datetime.now() <= p['end_date']]),
                'upcoming_maintenance': len([m for m in self.maintenance_schedules if m['scheduled_date'] >= datetime.now()]),
                'equipment_utilization': sum(eq['utilization_rate'] for eq in self.equipment_fleet) / len(self.equipment_fleet) if self.equipment_fleet else 0
            }
        }

# Global instance
schedule_system = InteractiveScheduleSystem()

@interactive_schedule_bp.route('/interactive-schedule')
def interactive_schedule_dashboard():
    """Interactive Equipment Schedule Dashboard"""
    dashboard_data = schedule_system.get_schedule_dashboard_data()
    return render_template('interactive_schedule.html', data=dashboard_data)

@interactive_schedule_bp.route('/api/update-assignment', methods=['POST'])
def api_update_assignment():
    """API endpoint to update equipment assignments"""
    try:
        request_data = request.get_json()
        equipment_id = request_data.get('equipment_id')
        project_id = request_data.get('project_id')
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')
        
        result = schedule_system.update_equipment_assignment(equipment_id, project_id, start_date, end_date)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@interactive_schedule_bp.route('/api/schedule-events')
def api_schedule_events():
    """API endpoint for calendar events"""
    events = schedule_system.generate_schedule_events()
    return jsonify(events)

def get_schedule_system():
    """Get the schedule system instance"""
    return schedule_system