"""
Watson Personal Automation System
Comprehensive credential management and auto-login functionality
Based on authentic MEP data for streamlined workflow automation
"""

import json
import csv
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from typing import Dict, List, Any
import re

class WatsonCredentialManager:
    """Manages Watson's authentic credentials for automated workflows"""
    
    def __init__(self):
        self.watson_credentials = self._extract_watson_credentials()
        self.priority_sites = self._identify_priority_sites()
        self.automation_workflows = self._setup_automation_workflows()
    
    def _extract_watson_credentials(self) -> List[Dict[str, str]]:
        """Extract all bwatson@ragleinc.com credentials from MEP file"""
        watson_creds = []
        
        # Read MEP file and extract Watson-specific entries
        try:
            with open('attached_assets/MEP_06.03.2025.md', 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    username = row.get('username', '').lower()
                    if 'bwatson@ragleinc.com' in username or username == 'bwatson':
                        watson_creds.append({
                            'site': row.get('name', ''),
                            'url': row.get('url', ''),
                            'username': row.get('username', ''),
                            'password': row.get('password', ''),
                            'note': row.get('note', ''),
                            'category': self._categorize_site(row.get('name', ''))
                        })
        except Exception as e:
            print(f"Error reading MEP file: {e}")
        
        # Add the critical ones we found in the analysis
        essential_creds = [
            {
                'site': 'Gauge Smart',
                'url': 'https://login.gaugesmart.com/Account/LogOn',
                'username': 'bwatson',
                'password': 'Plsw@2900413477',
                'category': 'fleet_management'
            },
            {
                'site': 'Groundworks (Primary)',
                'url': 'https://groundworks.ragleinc.com/login',
                'username': 'bwatson@ragleinc.com',
                'password': 'Bmw@34774134',
                'category': 'project_management'
            },
            {
                'site': 'Groundworks (SelectMain)',
                'url': 'https://groundworks.selectmain.com/login',
                'username': 'bwatson@ragleinc.com',
                'password': 'Bmw@34774134',
                'category': 'project_management'
            },
            {
                'site': 'Samsara Fleet',
                'url': 'https://cloud.samsara.com/signin',
                'username': 'bwatson@ragleinc.com',
                'password': 'Btpp@1513!',
                'category': 'fleet_management'
            },
            {
                'site': 'Foundation Software',
                'url': 'https://foundationsoftware.onelogin.com/login2/',
                'username': 'bwatson@ragleinc.com',
                'password': 'Btpp@15133477!',
                'category': 'accounting'
            },
            {
                'site': 'Procore',
                'url': 'https://login.procore.com/passwords/edit',
                'username': 'bwatson@ragleinc.com',
                'password': 'Btpp@4134772900',
                'category': 'project_management'
            }
        ]
        
        watson_creds.extend(essential_creds)
        return watson_creds
    
    def _categorize_site(self, site_name: str) -> str:
        """Categorize sites by business function"""
        site_lower = site_name.lower()
        
        if any(keyword in site_lower for keyword in ['gauge', 'samsara', 'fleet', 'geotab']):
            return 'fleet_management'
        elif any(keyword in site_lower for keyword in ['groundworks', 'procore', 'foundation']):
            return 'project_management'
        elif any(keyword in site_lower for keyword in ['chase', 'bank', 'financial']):
            return 'financial'
        elif any(keyword in site_lower for keyword in ['tax', 'irs', 'eftps']):
            return 'compliance'
        elif any(keyword in site_lower for keyword in ['smartsheet', 'office', 'avery']):
            return 'productivity'
        else:
            return 'general'
    
    def _identify_priority_sites(self) -> List[str]:
        """Identify Watson's most critical daily-use sites"""
        return [
            'Gauge Smart',
            'Groundworks (Primary)', 
            'Samsara Fleet',
            'Foundation Software',
            'Procore',
            'TRAXOVO Dashboard'
        ]
    
    def _setup_automation_workflows(self) -> Dict[str, List[str]]:
        """Setup automated workflow sequences"""
        return {
            'morning_startup': [
                'TRAXOVO Dashboard',
                'Gauge Smart',
                'Groundworks (Primary)',
                'Samsara Fleet'
            ],
            'financial_review': [
                'Foundation Software',
                'Chase Banking',
                'EFTPS Tax Portal'
            ],
            'project_management': [
                'Groundworks (Primary)',
                'Procore',
                'Smartsheet'
            ],
            'fleet_monitoring': [
                'Gauge Smart',
                'Samsara Fleet',
                'Geotab'
            ]
        }
    
    def get_credentials_by_category(self, category: str) -> List[Dict[str, str]]:
        """Get credentials filtered by category"""
        return [cred for cred in self.watson_credentials if cred.get('category') == category]
    
    def get_priority_dashboard_data(self) -> Dict[str, Any]:
        """Get priority sites with quick access links"""
        priority_data = {}
        
        for site_name in self.priority_sites:
            matching_creds = [cred for cred in self.watson_credentials if site_name in cred.get('site', '')]
            if matching_creds:
                cred = matching_creds[0]
                priority_data[site_name] = {
                    'url': cred['url'],
                    'username': cred['username'],
                    'category': cred['category'],
                    'last_accessed': 'Today',  # Would be tracked in real implementation
                    'auto_login_available': True
                }
        
        return priority_data
    
    def get_workflow_sequence(self, workflow_name: str) -> List[Dict[str, str]]:
        """Get automated workflow sequence with credentials"""
        if workflow_name not in self.automation_workflows:
            return []
        
        sequence = []
        for site_name in self.automation_workflows[workflow_name]:
            matching_creds = [cred for cred in self.watson_credentials if site_name in cred.get('site', '')]
            if matching_creds:
                sequence.append(matching_creds[0])
        
        return sequence

# Global instance
watson_manager = WatsonCredentialManager()

# Blueprint for Watson automation routes
watson_automation = Blueprint('watson_automation', __name__)

@watson_automation.route('/watson_automation_hub')
def automation_hub():
    """Watson's comprehensive automation hub"""
    priority_sites = watson_manager.get_priority_dashboard_data()
    categories = {
        'fleet_management': watson_manager.get_credentials_by_category('fleet_management'),
        'project_management': watson_manager.get_credentials_by_category('project_management'),
        'financial': watson_manager.get_credentials_by_category('financial'),
        'compliance': watson_manager.get_credentials_by_category('compliance')
    }
    
    return render_template('watson_automation_hub.html', 
                         priority_sites=priority_sites,
                         categories=categories,
                         workflows=watson_manager.automation_workflows.keys())

@watson_automation.route('/watson_quick_access')
def quick_access():
    """Quick access dashboard for Watson's daily sites"""
    return render_template('watson_quick_access.html',
                         sites=watson_manager.get_priority_dashboard_data())

@watson_automation.route('/api/watson_auto_login', methods=['POST'])
def auto_login():
    """API endpoint for automated login sequence"""
    site_name = request.json.get('site_name')
    
    matching_creds = [cred for cred in watson_manager.watson_credentials 
                     if site_name in cred.get('site', '')]
    
    if matching_creds:
        cred = matching_creds[0]
        return jsonify({
            'success': True,
            'url': cred['url'],
            'username': cred['username'],
            'auto_fill_data': {
                'username': cred['username'],
                'password': cred['password']
            }
        })
    
    return jsonify({'success': False, 'error': 'Credentials not found'})

@watson_automation.route('/api/watson_workflow', methods=['POST'])
def execute_workflow():
    """Execute automated workflow sequence"""
    workflow_name = request.json.get('workflow_name')
    sequence = watson_manager.get_workflow_sequence(workflow_name)
    
    return jsonify({
        'workflow_name': workflow_name,
        'sequence': sequence,
        'total_sites': len(sequence)
    })

@watson_automation.route('/watson_credential_manager')
def credential_manager():
    """Comprehensive credential management interface"""
    all_credentials = watson_manager.watson_credentials
    
    # Group by category for better organization
    grouped_creds = {}
    for cred in all_credentials:
        category = cred.get('category', 'general')
        if category not in grouped_creds:
            grouped_creds[category] = []
        grouped_creds[category].append(cred)
    
    return render_template('watson_credential_manager.html',
                         grouped_credentials=grouped_creds,
                         total_credentials=len(all_credentials))

def integrate_watson_automation(app):
    """Integrate Watson automation into main application"""
    app.register_blueprint(watson_automation, url_prefix='/watson_auto')
    
    # Add Watson automation to main navigation
    @app.route('/watson_personal_dashboard')
    def watson_personal_dashboard():
        """Watson's personalized dashboard with automation controls"""
        return redirect(url_for('watson_automation.automation_hub'))
    
    return watson_manager

# Export for integration
__all__ = ['watson_manager', 'integrate_watson_automation']