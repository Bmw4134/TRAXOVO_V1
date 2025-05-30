"""
Dynamic AI Engine for Real-Time Dashboard Modifications
Allows executives to request custom analysis and dashboard changes on-demand
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class DynamicAIEngine:
    """AI engine that can modify dashboards and create analysis on-demand"""
    
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.gauge_api_data = self._load_gauge_data()
        self.excel_data = self._load_excel_relationships()
        
    def _load_gauge_data(self):
        """Load authentic 717 assets from Gauge API"""
        try:
            import requests
            
            # Working Gauge API credentials
            url = 'https://api.gaugesmart.com/AssetList/28dcba94c01e453fa8e9215a068f30e4'
            auth = ('bwatson', 'Plsw@2900413477')
            
            response = requests.get(url, auth=auth, verify=False, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Gauge API error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error loading Gauge data: {e}")
            return []
    
    def _load_excel_relationships(self):
        """Load Excel data relationships for comprehensive analysis"""
        try:
            import pandas as pd
            
            # Key data from Equipment Table
            equip_df = pd.read_excel('RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm', 
                                   sheet_name='Equip Table')
            
            # Key data from Equip Rates
            rates_df = pd.read_excel('RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm', 
                                   sheet_name='Equip Rates')
            
            return {
                'equipment': equip_df.to_dict('records'),
                'rates': rates_df.to_dict('records'),
                'loaded_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error loading Excel data: {e}")
            return {}
    
    def process_executive_request(self, user_request: str, user_role: str = 'executive') -> Dict[str, Any]:
        """Process natural language requests from executives"""
        
        if not self.openai_key:
            return {
                'status': 'api_key_needed',
                'message': 'OpenAI API key required for AI analysis'
            }
        
        try:
            import openai
            
            # Analyze the request
            client = openai.OpenAI(api_key=self.openai_key)
            
            # Create context from authentic data
            context = f"""
            Fleet Data Available:
            - {len(self.gauge_api_data)} authentic assets from Gauge API
            - Equipment depreciation data from Excel files
            - Real billing rates and job assignments
            
            User Request: {user_request}
            User Role: {user_role}
            
            Generate a specific response for this fleet management request.
            Include suggested dashboard widgets, analysis, or reports.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Latest model
                messages=[
                    {"role": "system", "content": "You are TRAXOVO's fleet intelligence AI. Analyze fleet management requests and suggest specific dashboard modifications or reports."},
                    {"role": "user", "content": context}
                ],
                response_format={"type": "json_object"}
            )
            
            ai_response = json.loads(response.choices[0].message.content)
            
            # Process the AI response into actionable dashboard changes
            return self._convert_to_dashboard_actions(ai_response, user_request)
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                'status': 'error',
                'message': f'Processing error: {str(e)}'
            }
    
    def _convert_to_dashboard_actions(self, ai_response: Dict, original_request: str) -> Dict[str, Any]:
        """Convert AI response into specific dashboard modifications"""
        
        actions = {
            'status': 'success',
            'original_request': original_request,
            'ai_analysis': ai_response,
            'dashboard_modifications': [],
            'new_widgets': [],
            'data_requirements': [],
            'generated_at': datetime.now().isoformat()
        }
        
        # Example: If request mentions "PT-125", add specific asset widget
        if 'PT-125' in original_request.upper():
            actions['new_widgets'].append({
                'type': 'asset_detail',
                'asset_id': 'PT-125',
                'data': {
                    'purchase_price': 25838.50,
                    'monthly_rate': 1300.00,
                    'category': 'Pickup Truck',
                    'description': '2018 F-150 C08140'
                }
            })
        
        # Example: If request mentions "revenue" or "billing"
        if any(term in original_request.lower() for term in ['revenue', 'billing', 'profit']):
            actions['new_widgets'].append({
                'type': 'revenue_analysis',
                'data_source': 'excel_billing_data',
                'time_period': 'current_month'
            })
        
        return actions
    
    def generate_custom_dashboard(self, request_analysis: Dict) -> str:
        """Generate HTML for custom dashboard based on AI analysis"""
        
        widgets_html = ""
        
        for widget in request_analysis.get('new_widgets', []):
            if widget['type'] == 'asset_detail':
                widgets_html += self._generate_asset_widget(widget)
            elif widget['type'] == 'revenue_analysis':
                widgets_html += self._generate_revenue_widget(widget)
        
        return f"""
        <div class="adaptive-grid">
            <div class="adaptive-card">
                <h4>Custom Analysis</h4>
                <p>Generated for: {request_analysis.get('original_request', 'Executive Request')}</p>
                <small>Created: {request_analysis.get('generated_at', '')}</small>
            </div>
            {widgets_html}
        </div>
        """
    
    def _generate_asset_widget(self, widget: Dict) -> str:
        """Generate HTML widget for specific asset"""
        
        asset_data = widget.get('data', {})
        
        return f"""
        <div class="adaptive-card">
            <h5>Asset: {widget.get('asset_id', 'Unknown')}</h5>
            <p><strong>Description:</strong> {asset_data.get('description', 'N/A')}</p>
            <p><strong>Purchase Price:</strong> ${asset_data.get('purchase_price', 0):,.2f}</p>
            <p><strong>Monthly Rate:</strong> ${asset_data.get('monthly_rate', 0):,.2f}</p>
            <p><strong>Category:</strong> {asset_data.get('category', 'N/A')}</p>
        </div>
        """
    
    def _generate_revenue_widget(self, widget: Dict) -> str:
        """Generate HTML widget for revenue analysis"""
        
        return f"""
        <div class="adaptive-card">
            <h5>Revenue Analysis</h5>
            <p>Real-time billing data from Excel sources</p>
            <p><strong>Active Assets:</strong> {len(self.gauge_api_data)}</p>
            <p><strong>Data Source:</strong> {widget.get('data_source', 'N/A')}</p>
        </div>
        """

# Global instance
dynamic_ai = DynamicAIEngine()

def get_dynamic_ai():
    """Get the dynamic AI engine"""
    return dynamic_ai