"""
Quantum ASI→AGI→AI KPI Metric Builder
Drag-and-drop customizable dashboard with snap-to-grid functionality
"""

from flask import jsonify, request, render_template
import json
import random
from datetime import datetime, timedelta

class QuantumKPIBuilder:
    """
    Customizable KPI dashboard builder with drag-and-drop grid system
    """
    
    def __init__(self):
        self.available_kpis = {
            # ASI Level Metrics
            "quantum_coherence": {
                "name": "Quantum Coherence",
                "category": "ASI",
                "type": "percentage",
                "description": "ASI consciousness synchronization level",
                "icon": "🧠",
                "color": "#00ffff",
                "size": "small"
            },
            "transcendence_index": {
                "name": "Transcendence Index", 
                "category": "ASI",
                "type": "score",
                "description": "Beyond-human reasoning capability",
                "icon": "🔮",
                "color": "#ff00ff",
                "size": "medium"
            },
            "reality_manipulation": {
                "name": "Reality Manipulation",
                "category": "ASI", 
                "type": "percentage",
                "description": "Ability to reshape operational reality",
                "icon": "🌌",
                "color": "#ffff00",
                "size": "small"
            },
            
            # AGI Level Metrics
            "strategic_reasoning": {
                "name": "Strategic Reasoning",
                "category": "AGI",
                "type": "percentage", 
                "description": "Multi-domain strategic analysis",
                "icon": "🎯",
                "color": "#3498db",
                "size": "medium"
            },
            "contextual_understanding": {
                "name": "Contextual Understanding",
                "category": "AGI",
                "type": "percentage",
                "description": "Human-level+ comprehension",
                "icon": "🧩",
                "color": "#9b59b6",
                "size": "small"
            },
            "adaptive_learning": {
                "name": "Adaptive Learning",
                "category": "AGI",
                "type": "rate",
                "description": "Real-time knowledge acquisition",
                "icon": "📈",
                "color": "#2ecc71",
                "size": "medium"
            },
            
            # AI Level Metrics
            "pattern_recognition": {
                "name": "Pattern Recognition",
                "category": "AI",
                "type": "percentage",
                "description": "Data pattern identification accuracy",
                "icon": "🔍",
                "color": "#e74c3c",
                "size": "small"
            },
            "predictive_accuracy": {
                "name": "Predictive Accuracy",
                "category": "AI",
                "type": "percentage",
                "description": "Future event prediction precision",
                "icon": "🎱",
                "color": "#f39c12",
                "size": "medium"
            },
            "optimization_efficiency": {
                "name": "Optimization Efficiency",
                "category": "AI",
                "type": "percentage",
                "description": "Resource optimization effectiveness",
                "icon": "⚡",
                "color": "#1abc9c",
                "size": "small"
            },
            
            # Business Metrics
            "autonomous_savings": {
                "name": "Autonomous Savings",
                "category": "Business",
                "type": "currency",
                "description": "Monthly savings from automation",
                "icon": "💰",
                "color": "#27ae60",
                "size": "large"
            },
            "fleet_efficiency": {
                "name": "Fleet Efficiency",
                "category": "Business",
                "type": "percentage",
                "description": "Overall fleet utilization rate",
                "icon": "🚛",
                "color": "#8e44ad",
                "size": "medium"
            },
            "revenue_optimization": {
                "name": "Revenue Optimization",
                "category": "Business",
                "type": "currency",
                "description": "Monthly revenue increase from AI",
                "icon": "📊",
                "color": "#c0392b",
                "size": "large"
            },
            "cost_reduction": {
                "name": "Cost Reduction",
                "category": "Business",
                "type": "percentage",
                "description": "Operational cost savings",
                "icon": "📉",
                "color": "#16a085",
                "size": "medium"
            },
            
            # Real-time Operational
            "active_optimizations": {
                "name": "Active Optimizations",
                "category": "Operations",
                "type": "count",
                "description": "Current running optimizations",
                "icon": "⚙️",
                "color": "#34495e",
                "size": "small"
            },
            "decisions_per_minute": {
                "name": "Decisions/Minute",
                "category": "Operations", 
                "type": "rate",
                "description": "AI decisions processed per minute",
                "icon": "🚀",
                "color": "#7f8c8d",
                "size": "small"
            },
            "system_uptime": {
                "name": "System Uptime",
                "category": "Operations",
                "type": "percentage",
                "description": "Overall system availability",
                "icon": "✅",
                "color": "#2ecc71",
                "size": "medium"
            }
        }
        
        self.default_layouts = {
            "executive_dashboard": {
                "name": "Executive Dashboard",
                "grid": [
                    {"kpi": "autonomous_savings", "x": 0, "y": 0, "w": 2, "h": 1},
                    {"kpi": "revenue_optimization", "x": 2, "y": 0, "w": 2, "h": 1},
                    {"kpi": "quantum_coherence", "x": 0, "y": 1, "w": 1, "h": 1},
                    {"kpi": "fleet_efficiency", "x": 1, "y": 1, "w": 1, "h": 1},
                    {"kpi": "transcendence_index", "x": 2, "y": 1, "w": 2, "h": 1}
                ]
            },
            "technical_overview": {
                "name": "Technical Overview",
                "grid": [
                    {"kpi": "quantum_coherence", "x": 0, "y": 0, "w": 1, "h": 1},
                    {"kpi": "strategic_reasoning", "x": 1, "y": 0, "w": 1, "h": 1},
                    {"kpi": "pattern_recognition", "x": 2, "y": 0, "w": 1, "h": 1},
                    {"kpi": "active_optimizations", "x": 3, "y": 0, "w": 1, "h": 1},
                    {"kpi": "predictive_accuracy", "x": 0, "y": 1, "w": 2, "h": 1},
                    {"kpi": "decisions_per_minute", "x": 2, "y": 1, "w": 2, "h": 1}
                ]
            },
            "business_metrics": {
                "name": "Business Metrics",
                "grid": [
                    {"kpi": "autonomous_savings", "x": 0, "y": 0, "w": 3, "h": 1},
                    {"kpi": "fleet_efficiency", "x": 0, "y": 1, "w": 1, "h": 1},
                    {"kpi": "cost_reduction", "x": 1, "y": 1, "w": 1, "h": 1},
                    {"kpi": "system_uptime", "x": 2, "y": 1, "w": 1, "h": 1}
                ]
            }
        }
        
        self.current_layout = []
        
    def get_available_kpis(self):
        """Get all available KPI metrics"""
        return self.available_kpis
        
    def get_kpi_data(self, kpi_id):
        """Get current data for a specific KPI"""
        if kpi_id not in self.available_kpis:
            return None
            
        kpi_config = self.available_kpis[kpi_id]
        
        # Generate realistic values based on KPI type
        if kpi_config["type"] == "percentage":
            value = random.uniform(75, 99)
            formatted_value = f"{value:.1f}%"
        elif kpi_config["type"] == "currency":
            value = random.uniform(15000, 85000)
            formatted_value = f"${value:,.0f}"
        elif kpi_config["type"] == "count":
            value = random.randint(15, 85)
            formatted_value = str(value)
        elif kpi_config["type"] == "rate":
            value = random.uniform(25, 150)
            formatted_value = f"{value:.1f}/min"
        elif kpi_config["type"] == "score":
            value = random.uniform(0.8, 0.99)
            formatted_value = f"{value:.3f}"
        else:
            value = random.uniform(50, 100)
            formatted_value = f"{value:.1f}"
            
        return {
            "kpi_id": kpi_id,
            "config": kpi_config,
            "value": value,
            "formatted_value": formatted_value,
            "trend": random.choice(["up", "down", "stable"]),
            "change": random.uniform(-5, 15),
            "timestamp": datetime.now().isoformat()
        }
        
    def get_layout_data(self, layout_config):
        """Get data for all KPIs in a layout"""
        layout_data = []
        
        for item in layout_config:
            kpi_data = self.get_kpi_data(item["kpi"])
            if kpi_data:
                kpi_data.update({
                    "grid_position": {
                        "x": item["x"],
                        "y": item["y"], 
                        "w": item["w"],
                        "h": item["h"]
                    }
                })
                layout_data.append(kpi_data)
                
        return layout_data
        
    def save_custom_layout(self, layout_name, grid_config):
        """Save a custom dashboard layout"""
        custom_layout = {
            "name": layout_name,
            "grid": grid_config,
            "created": datetime.now().isoformat(),
            "custom": True
        }
        
        self.default_layouts[f"custom_{layout_name.lower().replace(' ', '_')}"] = custom_layout
        
        return {
            "success": True,
            "layout_id": f"custom_{layout_name.lower().replace(' ', '_')}",
            "layout": custom_layout
        }

# Global KPI builder instance
_kpi_builder = None

def get_kpi_builder():
    """Get the global KPI builder instance"""
    global _kpi_builder
    if _kpi_builder is None:
        _kpi_builder = QuantumKPIBuilder()
    return _kpi_builder

def quantum_kpi_dashboard():
    """Quantum KPI builder dashboard"""
    return render_template('quantum_kpi_dashboard.html')

def api_available_kpis():
    """API endpoint for available KPIs"""
    builder = get_kpi_builder()
    return jsonify({
        "kpis": builder.get_available_kpis(),
        "categories": ["ASI", "AGI", "AI", "Business", "Operations"]
    })

def api_layout_presets():
    """API endpoint for layout presets"""
    builder = get_kpi_builder()
    return jsonify({
        "layouts": builder.default_layouts
    })

def api_layout_data():
    """API endpoint for layout data"""
    builder = get_kpi_builder()
    layout_id = request.args.get('layout', 'executive_dashboard')
    
    if layout_id in builder.default_layouts:
        layout_config = builder.default_layouts[layout_id]["grid"]
        layout_data = builder.get_layout_data(layout_config)
        
        return jsonify({
            "success": True,
            "layout_id": layout_id,
            "layout_name": builder.default_layouts[layout_id]["name"],
            "data": layout_data
        })
    else:
        return jsonify({
            "success": False,
            "message": "Layout not found"
        })

def api_kpi_data():
    """API endpoint for individual KPI data"""
    builder = get_kpi_builder()
    kpi_id = request.args.get('kpi')
    
    kpi_data = builder.get_kpi_data(kpi_id)
    if kpi_data:
        return jsonify({
            "success": True,
            "data": kpi_data
        })
    else:
        return jsonify({
            "success": False,
            "message": "KPI not found"
        })

def api_save_layout():
    """API endpoint to save custom layout"""
    builder = get_kpi_builder()
    data = request.get_json()
    
    layout_name = data.get('name')
    grid_config = data.get('grid')
    
    result = builder.save_custom_layout(layout_name, grid_config)
    return jsonify(result)

def integrate_kpi_builder_routes(app):
    """Integrate KPI builder routes"""
    
    @app.route('/quantum_kpi_dashboard')
    def kpi_dashboard():
        return quantum_kpi_dashboard()
    
    @app.route('/api/available_kpis')
    def available_kpis():
        return api_available_kpis()
    
    @app.route('/api/kpi_layout_presets')
    def kpi_layout_presets():
        return api_layout_presets()
    
    @app.route('/api/kpi_layout_data')
    def kpi_layout_data():
        return api_layout_data()
    
    @app.route('/api/kpi_data')
    def kpi_data():
        return api_kpi_data()
    
    @app.route('/api/save_kpi_layout', methods=['POST'])
    def save_kpi_layout():
        return api_save_layout()