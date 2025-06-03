"""
Intelligent Intake Form System for Mechanics and Fleet Management
Advanced form with asset lookup, predictive issue detection, and automated routing
"""

import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
import re

intake_form_bp = Blueprint('intake_form', __name__)

class IntelligentIntakeSystem:
    """Smart intake form system with asset intelligence and predictive routing"""
    
    def __init__(self):
        self.load_asset_data()
        self.load_maintenance_history()
        self.common_issues = self._load_common_issues()
        
    def load_asset_data(self):
        """Load authentic asset data from billing records"""
        try:
            # Load from authentic billing data
            billing_df = pd.read_excel('RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm')
            
            # Extract asset information
            self.assets = []
            for _, row in billing_df.iterrows():
                if pd.notna(row.get('Equipment Type')) and pd.notna(row.get('Division/Job')):
                    asset_info = {
                        'equipment_type': str(row.get('Equipment Type', '')),
                        'division': str(row.get('Division/Job', '')),
                        'units': float(row.get('UNITS', 0)),
                        'equipment_amount': float(row.get('Equipment Amount', 0)),
                        'active': row.get('UNITS', 0) > 0
                    }
                    self.assets.append(asset_info)
                    
            logging.info(f"Loaded {len(self.assets)} asset records for intake form")
            
        except Exception as e:
            logging.error(f"Error loading asset data: {e}")
            self.assets = []
            
    def load_maintenance_history(self):
        """Load maintenance history patterns"""
        # Simulate maintenance patterns based on asset types
        self.maintenance_patterns = {
            'Excavator': {
                'common_issues': ['Hydraulic leak', 'Track wear', 'Engine overheating', 'Boom cylinder issues'],
                'avg_hours_between_service': 250,
                'critical_components': ['Hydraulic system', 'Tracks', 'Engine', 'Boom']
            },
            'Dozer': {
                'common_issues': ['Track tension', 'Blade wear', 'Transmission issues', 'Final drive problems'],
                'avg_hours_between_service': 300,
                'critical_components': ['Tracks', 'Blade', 'Transmission', 'Final drives']
            },
            'Loader': {
                'common_issues': ['Bucket wear', 'Lift arm hydraulics', 'Tire replacement', 'Engine performance'],
                'avg_hours_between_service': 200,
                'critical_components': ['Bucket', 'Hydraulics', 'Tires', 'Engine']
            },
            'Truck': {
                'common_issues': ['Brake system', 'Tire wear', 'Engine maintenance', 'Transmission service'],
                'avg_hours_between_service': 500,
                'critical_components': ['Brakes', 'Tires', 'Engine', 'Transmission']
            },
            'Crane': {
                'common_issues': ['Wire rope wear', 'Boom hydraulics', 'Outrigger problems', 'Load block issues'],
                'avg_hours_between_service': 150,
                'critical_components': ['Wire rope', 'Hydraulics', 'Outriggers', 'Load block']
            }
        }
        
    def _load_common_issues(self):
        """Load common equipment issues database"""
        return {
            'Hydraulic': [
                'Hydraulic fluid leak',
                'Slow hydraulic operation',
                'Hydraulic pump failure',
                'Cylinder seal failure',
                'Overheating hydraulic system'
            ],
            'Engine': [
                'Engine overheating',
                'Poor fuel economy',
                'Hard starting',
                'Excessive smoke',
                'Loss of power'
            ],
            'Electrical': [
                'Battery not charging',
                'Lights not working',
                'Instrument panel issues',
                'Starter problems',
                'Alternator failure'
            ],
            'Mechanical': [
                'Unusual noise',
                'Vibration',
                'Gear shifting problems',
                'Brake issues',
                'Steering problems'
            ],
            'Tracks/Tires': [
                'Track tension issues',
                'Tire wear',
                'Track pad replacement',
                'Wheel bearing problems',
                'Alignment issues'
            ]
        }
        
    def get_asset_suggestions(self, search_term):
        """Get asset suggestions based on search term"""
        suggestions = []
        search_lower = search_term.lower()
        
        for asset in self.assets:
            if (search_lower in asset['equipment_type'].lower() or 
                search_lower in asset['division'].lower()):
                suggestions.append({
                    'equipment_type': asset['equipment_type'],
                    'division': asset['division'],
                    'status': 'Active' if asset['active'] else 'Inactive',
                    'utilization': f"{asset['units']:.1f} units"
                })
                
        return suggestions[:10]  # Return top 10 matches
        
    def predict_issue_category(self, description):
        """Predict issue category based on description"""
        description_lower = description.lower()
        
        # Score each category
        category_scores = {}
        for category, issues in self.common_issues.items():
            score = 0
            for issue in issues:
                # Count keyword matches
                issue_words = issue.lower().split()
                for word in issue_words:
                    if word in description_lower:
                        score += 1
                        
            category_scores[category] = score
            
        # Return category with highest score
        if category_scores:
            best_category = max(category_scores.keys(), key=lambda x: category_scores[x])
            confidence = category_scores[best_category] / max(1, len(description.split()))
            return {
                'category': best_category,
                'confidence': min(1.0, confidence),
                'suggested_issues': self.common_issues.get(best_category, [])
            }
            
        return {'category': 'General', 'confidence': 0.0, 'suggested_issues': []}
        
    def calculate_priority(self, equipment_type, issue_category, description):
        """Calculate issue priority based on equipment and issue type"""
        priority_score = 0
        
        # Equipment criticality
        critical_equipment = ['Crane', 'Excavator', 'Dozer']
        if any(eq in equipment_type for eq in critical_equipment):
            priority_score += 3
            
        # Issue severity keywords
        high_severity_keywords = ['leak', 'smoke', 'overheating', 'failure', 'broken', 'emergency']
        medium_severity_keywords = ['slow', 'noise', 'vibration', 'wear']
        
        description_lower = description.lower()
        for keyword in high_severity_keywords:
            if keyword in description_lower:
                priority_score += 2
                
        for keyword in medium_severity_keywords:
            if keyword in description_lower:
                priority_score += 1
                
        # Safety-related issues
        safety_keywords = ['brake', 'steering', 'safety', 'accident', 'injury']
        for keyword in safety_keywords:
            if keyword in description_lower:
                priority_score += 4
                
        # Determine priority level
        if priority_score >= 6:
            return 'Emergency'
        elif priority_score >= 4:
            return 'High'
        elif priority_score >= 2:
            return 'Medium'
        else:
            return 'Low'
            
    def route_ticket(self, equipment_type, issue_category, priority):
        """Determine routing for maintenance ticket"""
        routing = {
            'department': 'Maintenance',
            'estimated_hours': 2,
            'required_skills': [],
            'parts_likely_needed': [],
            'next_steps': []
        }
        
        # Route based on equipment type and issue
        if issue_category == 'Hydraulic':
            routing['required_skills'] = ['Hydraulic systems', 'Seal replacement']
            routing['parts_likely_needed'] = ['Hydraulic seals', 'Hydraulic fluid', 'Filters']
            routing['estimated_hours'] = 4
            
        elif issue_category == 'Engine':
            routing['required_skills'] = ['Engine diagnostics', 'Mechanical repair']
            routing['parts_likely_needed'] = ['Engine oil', 'Filters', 'Belts']
            routing['estimated_hours'] = 6
            
        elif issue_category == 'Electrical':
            routing['required_skills'] = ['Electrical diagnostics', 'Wiring']
            routing['parts_likely_needed'] = ['Fuses', 'Relays', 'Wiring']
            routing['estimated_hours'] = 3
            
        elif issue_category == 'Tracks/Tires':
            routing['required_skills'] = ['Track/tire service', 'Alignment']
            routing['parts_likely_needed'] = ['Track pads', 'Tires', 'Bearings']
            routing['estimated_hours'] = 5
            
        # Adjust for priority
        if priority == 'Emergency':
            routing['next_steps'].append('Immediate response required')
            routing['estimated_hours'] *= 0.5  # Rush job
        elif priority == 'High':
            routing['next_steps'].append('Schedule within 24 hours')
        elif priority == 'Medium':
            routing['next_steps'].append('Schedule within 3 days')
        else:
            routing['next_steps'].append('Schedule within 1 week')
            
        return routing
        
    def generate_work_order_number(self):
        """Generate unique work order number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        return f"WO-{timestamp}"
        
    def save_intake_record(self, form_data):
        """Save intake form submission"""
        try:
            # Create work order record
            work_order = {
                'work_order_number': self.generate_work_order_number(),
                'timestamp': datetime.now().isoformat(),
                'submitted_by': form_data.get('submitted_by', 'Unknown'),
                'equipment_type': form_data.get('equipment_type'),
                'division': form_data.get('division'),
                'issue_description': form_data.get('issue_description'),
                'issue_category': form_data.get('predicted_category'),
                'priority': form_data.get('calculated_priority'),
                'routing_info': form_data.get('routing'),
                'contact_info': form_data.get('contact_info'),
                'location': form_data.get('location'),
                'status': 'Submitted'
            }
            
            # In a real system, this would save to database
            # For now, log the work order
            logging.info(f"Work order created: {work_order['work_order_number']}")
            
            return work_order
            
        except Exception as e:
            logging.error(f"Error saving intake record: {e}")
            return None

@intake_form_bp.route('/intake-form')
@login_required
def intake_form():
    """Display intelligent intake form"""
    intake_system = IntelligentIntakeSystem()
    
    # Get unique equipment types and divisions from authentic data
    equipment_types = list(set([asset['equipment_type'] for asset in intake_system.assets if asset['equipment_type']]))
    divisions = list(set([asset['division'] for asset in intake_system.assets if asset['division']]))
    
    return render_template('intake_form.html',
                         equipment_types=sorted(equipment_types),
                         divisions=sorted(divisions),
                         common_issues=intake_system.common_issues,
                         page_title="Equipment Intake Form")

@intake_form_bp.route('/api/asset-suggestions')
@login_required
def get_asset_suggestions():
    """API endpoint for asset suggestions"""
    search_term = request.args.get('q', '')
    intake_system = IntelligentIntakeSystem()
    suggestions = intake_system.get_asset_suggestions(search_term)
    return jsonify({'suggestions': suggestions})

@intake_form_bp.route('/api/predict-issue', methods=['POST'])
@login_required
def predict_issue():
    """API endpoint for issue prediction"""
    data = request.get_json()
    description = data.get('description', '')
    
    intake_system = IntelligentIntakeSystem()
    prediction = intake_system.predict_issue_category(description)
    
    return jsonify(prediction)

@intake_form_bp.route('/api/calculate-priority', methods=['POST'])
@login_required
def calculate_priority():
    """API endpoint for priority calculation"""
    data = request.get_json()
    equipment_type = data.get('equipment_type', '')
    issue_category = data.get('issue_category', '')
    description = data.get('description', '')
    
    intake_system = IntelligentIntakeSystem()
    priority = intake_system.calculate_priority(equipment_type, issue_category, description)
    routing = intake_system.route_ticket(equipment_type, issue_category, priority)
    
    return jsonify({
        'priority': priority,
        'routing': routing
    })

@intake_form_bp.route('/submit-intake', methods=['POST'])
@login_required
def submit_intake():
    """Submit intake form"""
    try:
        intake_system = IntelligentIntakeSystem()
        
        # Get form data
        form_data = {
            'submitted_by': current_user.get_id() if current_user.is_authenticated else 'Anonymous',
            'equipment_type': request.form.get('equipment_type'),
            'division': request.form.get('division'),
            'issue_description': request.form.get('issue_description'),
            'contact_info': request.form.get('contact_info'),
            'location': request.form.get('location'),
            'predicted_category': request.form.get('predicted_category'),
            'calculated_priority': request.form.get('calculated_priority'),
            'routing': json.loads(request.form.get('routing_info', '{}'))
        }
        
        # Save work order
        work_order = intake_system.save_intake_record(form_data)
        
        if work_order:
            flash(f"Work order {work_order['work_order_number']} created successfully!", 'success')
            return redirect(url_for('intake_form.work_order_confirmation', 
                                  work_order_number=work_order['work_order_number']))
        else:
            flash('Error creating work order. Please try again.', 'error')
            return redirect(url_for('intake_form.intake_form'))
            
    except Exception as e:
        logging.error(f"Error submitting intake form: {e}")
        flash('Error submitting form. Please try again.', 'error')
        return redirect(url_for('intake_form.intake_form'))

@intake_form_bp.route('/work-order/<work_order_number>')
@login_required
def work_order_confirmation(work_order_number):
    """Display work order confirmation"""
    return render_template('work_order_confirmation.html',
                         work_order_number=work_order_number,
                         page_title="Work Order Confirmation")

@intake_form_bp.route('/mechanic-dashboard')
@login_required
def mechanic_dashboard():
    """Mechanic dashboard for managing work orders"""
    # In a real system, this would load from database
    sample_work_orders = [
        {
            'work_order_number': 'WO-202505291345',
            'equipment_type': 'Excavator',
            'division': 'DFW',
            'priority': 'High',
            'issue_category': 'Hydraulic',
            'description': 'Hydraulic fluid leak from boom cylinder',
            'status': 'Assigned',
            'estimated_hours': 4,
            'created': '2025-05-29 13:45'
        },
        {
            'work_order_number': 'WO-202505291320',
            'equipment_type': 'Dozer',
            'division': 'HOU',
            'priority': 'Medium',
            'issue_category': 'Mechanical',
            'description': 'Unusual noise from transmission',
            'status': 'In Progress',
            'estimated_hours': 6,
            'created': '2025-05-29 13:20'
        }
    ]
    
    return render_template('mechanic_dashboard.html',
                         work_orders=sample_work_orders,
                         page_title="Mechanic Dashboard")

def get_intake_system():
    """Get intake system instance"""
    return IntelligentIntakeSystem()