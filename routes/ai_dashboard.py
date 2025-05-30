"""
AI-Powered Dynamic Dashboard Routes
Enables real-time dashboard modifications based on executive requests
"""

from flask import Blueprint, request, jsonify, render_template_string
from services.dynamic_ai_engine import get_dynamic_ai
from services.authentic_data_engine import get_authentic_engine
import logging

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai_dashboard', __name__, url_prefix='/ai')

@ai_bp.route('/request', methods=['POST'])
def process_ai_request():
    """Process natural language requests from executives"""
    
    try:
        data = request.get_json()
        user_request = data.get('request', '')
        user_role = data.get('role', 'executive')
        
        if not user_request:
            return jsonify({'error': 'Request text required'}), 400
        
        # Process through AI engine
        ai_engine = get_dynamic_ai()
        result = ai_engine.process_executive_request(user_request, user_role)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI request processing error: {e}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/dashboard/<request_id>')
def custom_dashboard(request_id):
    """Generate custom dashboard based on AI analysis"""
    
    try:
        # For now, generate a sample custom dashboard
        ai_engine = get_dynamic_ai()
        authentic_engine = get_authentic_engine()
        
        # Get real data
        gauge_assets = len(ai_engine.gauge_api_data)
        dashboard_metrics = authentic_engine.get_dashboard_metrics()
        
        custom_html = f"""
        <div class="container-fluid adaptive-container">
            <h2>Custom AI-Generated Dashboard</h2>
            <div class="adaptive-grid">
                <div class="adaptive-card">
                    <h4>Authentic Fleet Data</h4>
                    <p><strong>Total Assets:</strong> {gauge_assets}</p>
                    <p><strong>Data Source:</strong> Gauge API + Excel</p>
                </div>
                <div class="adaptive-card">
                    <h4>PT-125 Details</h4>
                    <p><strong>Asset:</strong> 2018 F-150 C08140</p>
                    <p><strong>Purchase Price:</strong> $25,838.50</p>
                    <p><strong>Monthly Rate:</strong> $1,300.00</p>
                </div>
                <div class="adaptive-card">
                    <h4>Fleet Metrics</h4>
                    <p><strong>Status:</strong> {dashboard_metrics.get('status', 'Loading...')}</p>
                    <p><strong>Active Assets:</strong> {dashboard_metrics.get('active_assets', 0)}</p>
                </div>
            </div>
        </div>
        """
        
        return render_template_string(custom_html)
        
    except Exception as e:
        logger.error(f"Custom dashboard error: {e}")
        return f"Dashboard generation error: {e}", 500

@ai_bp.route('/metrics')
def real_time_metrics():
    """Get real-time metrics from authentic sources"""
    
    try:
        authentic_engine = get_authentic_engine()
        ai_engine = get_dynamic_ai()
        
        metrics = {
            'gauge_api_assets': len(ai_engine.gauge_api_data),
            'dashboard_data': authentic_engine.get_dashboard_metrics(),
            'asset_breakdown': authentic_engine.get_asset_breakdown(),
            'excel_data_available': bool(ai_engine.excel_data),
            'timestamp': 'real-time'
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Real-time metrics error: {e}")
        return jsonify({'error': str(e)}), 500