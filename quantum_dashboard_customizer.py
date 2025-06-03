"""
Quantum Dashboard Customizer
Real-time dashboard layout and component customization system
"""

from flask import jsonify, request
import json
from datetime import datetime

class QuantumDashboardCustomizer:
    """
    Manages customizable dashboard layouts and component visibility
    """
    
    def __init__(self):
        self.layout_presets = {
            "executive": {
                "name": "Executive Presentation",
                "description": "Clean, high-level metrics for board presentations",
                "components": {
                    "palette_selector": False,
                    "consciousness_display": True,
                    "excellence_metrics": True,
                    "quantum_insights": True,
                    "breakthrough_button": True,
                    "autonomous_feed": True,
                    "decision_matrix": False,
                    "neural_network": False
                },
                "grid_columns": 2,
                "component_size": "large"
            },
            "technical": {
                "name": "Technical Deep Dive",
                "description": "Full technical display with all components",
                "components": {
                    "palette_selector": True,
                    "consciousness_display": True,
                    "excellence_metrics": True,
                    "quantum_insights": True,
                    "breakthrough_button": True,
                    "autonomous_feed": True,
                    "decision_matrix": True,
                    "neural_network": True
                },
                "grid_columns": 3,
                "component_size": "medium"
            },
            "demonstration": {
                "name": "Live Demonstration",
                "description": "Optimized for real-time demos with key features",
                "components": {
                    "palette_selector": True,
                    "consciousness_display": True,
                    "excellence_metrics": True,
                    "quantum_insights": False,
                    "breakthrough_button": True,
                    "autonomous_feed": True,
                    "decision_matrix": False,
                    "neural_network": True
                },
                "grid_columns": 2,
                "component_size": "large"
            },
            "minimal": {
                "name": "Minimal Clean",
                "description": "Simplified view focusing on core metrics",
                "components": {
                    "palette_selector": False,
                    "consciousness_display": True,
                    "excellence_metrics": True,
                    "quantum_insights": False,
                    "breakthrough_button": True,
                    "autonomous_feed": False,
                    "decision_matrix": False,
                    "neural_network": False
                },
                "grid_columns": 1,
                "component_size": "extra-large"
            },
            "autonomous_focus": {
                "name": "Autonomous Systems Focus",
                "description": "Highlights autonomous capabilities and savings",
                "components": {
                    "palette_selector": False,
                    "consciousness_display": True,
                    "excellence_metrics": False,
                    "quantum_insights": True,
                    "breakthrough_button": False,
                    "autonomous_feed": True,
                    "decision_matrix": False,
                    "neural_network": False
                },
                "grid_columns": 2,
                "component_size": "large"
            }
        }
        
        self.current_layout = "technical"
        
        self.component_definitions = {
            "palette_selector": {
                "title": "Color Palette Selector",
                "category": "customization",
                "priority": 1
            },
            "consciousness_display": {
                "title": "Quantum Consciousness",
                "category": "core",
                "priority": 10
            },
            "excellence_metrics": {
                "title": "Excellence Metrics",
                "category": "core", 
                "priority": 9
            },
            "quantum_insights": {
                "title": "Quantum Insights",
                "category": "analytics",
                "priority": 8
            },
            "breakthrough_button": {
                "title": "Excellence Mode Button",
                "category": "controls",
                "priority": 7
            },
            "autonomous_feed": {
                "title": "Live Autonomous Actions",
                "category": "automation",
                "priority": 6
            },
            "decision_matrix": {
                "title": "Decision Matrix",
                "category": "analytics",
                "priority": 5
            },
            "neural_network": {
                "title": "Neural Network Visualization",
                "category": "visualization",
                "priority": 4
            }
        }
        
    def get_layout_presets(self):
        """Get all available layout presets"""
        return self.layout_presets
        
    def set_layout(self, layout_name):
        """Set the active layout preset"""
        if layout_name in self.layout_presets:
            self.current_layout = layout_name
            return {
                "success": True,
                "layout": self.layout_presets[layout_name],
                "message": f"Switched to {self.layout_presets[layout_name]['name']} layout"
            }
        else:
            return {
                "success": False,
                "message": "Layout preset not found"
            }
            
    def get_current_layout(self):
        """Get the currently active layout"""
        return self.layout_presets[self.current_layout]
        
    def create_custom_layout(self, layout_data):
        """Create a custom layout configuration"""
        custom_name = f"custom_{int(datetime.now().timestamp())}"
        
        self.layout_presets[custom_name] = {
            "name": layout_data.get("name", "Custom Layout"),
            "description": layout_data.get("description", "User-created layout"),
            "components": layout_data.get("components", {}),
            "grid_columns": layout_data.get("grid_columns", 2),
            "component_size": layout_data.get("component_size", "medium"),
            "custom": True
        }
        
        return {
            "success": True,
            "layout_id": custom_name,
            "layout": self.layout_presets[custom_name]
        }
        
    def toggle_component(self, component_name):
        """Toggle visibility of a specific component"""
        current = self.layout_presets[self.current_layout]
        if component_name in current["components"]:
            current["components"][component_name] = not current["components"][component_name]
            return {
                "success": True,
                "component": component_name,
                "visible": current["components"][component_name]
            }
        else:
            return {
                "success": False,
                "message": "Component not found"
            }
            
    def get_component_visibility_css(self):
        """Generate CSS for component visibility based on current layout"""
        layout = self.layout_presets[self.current_layout]
        css_rules = []
        
        for component, visible in layout["components"].items():
            display = "block" if visible else "none"
            css_rules.append(f".component-{component.replace('_', '-')} {{ display: {display} !important; }}")
            
        # Grid layout rules
        grid_columns = layout.get("grid_columns", 2)
        css_rules.append(f".main-grid {{ grid-template-columns: repeat({grid_columns}, 1fr); }}")
        
        # Component sizing
        size = layout.get("component_size", "medium")
        size_map = {
            "small": "300px",
            "medium": "400px", 
            "large": "500px",
            "extra-large": "600px"
        }
        min_height = size_map.get(size, "400px")
        css_rules.append(f".quantum-card {{ min-height: {min_height}; }}")
        
        return "\n".join(css_rules)

# Global customizer instance
_dashboard_customizer = None

def get_dashboard_customizer():
    """Get the global dashboard customizer instance"""
    global _dashboard_customizer
    if _dashboard_customizer is None:
        _dashboard_customizer = QuantumDashboardCustomizer()
    return _dashboard_customizer

def api_layout_presets():
    """API endpoint to get all layout presets"""
    customizer = get_dashboard_customizer()
    return jsonify({
        "presets": customizer.get_layout_presets(),
        "current": customizer.current_layout
    })

def api_set_layout():
    """API endpoint to set layout preset"""
    customizer = get_dashboard_customizer()
    data = request.get_json()
    layout_name = data.get("layout_name")
    
    result = customizer.set_layout(layout_name)
    return jsonify(result)

def api_toggle_component():
    """API endpoint to toggle component visibility"""
    customizer = get_dashboard_customizer()
    data = request.get_json()
    component_name = data.get("component_name")
    
    result = customizer.toggle_component(component_name)
    return jsonify(result)

def api_custom_layout():
    """API endpoint to create custom layout"""
    customizer = get_dashboard_customizer()
    layout_data = request.get_json()
    
    result = customizer.create_custom_layout(layout_data)
    return jsonify(result)

def api_layout_css():
    """API endpoint to get layout-specific CSS"""
    customizer = get_dashboard_customizer()
    css = customizer.get_component_visibility_css()
    
    return jsonify({
        "css": css,
        "layout": customizer.get_current_layout()
    })

def integrate_dashboard_customizer_routes(app):
    """Integrate dashboard customizer routes with the main Flask app"""
    
    @app.route('/api/layout_presets')
    def layout_presets():
        return api_layout_presets()
    
    @app.route('/api/set_layout', methods=['POST'])
    def set_layout():
        return api_set_layout()
    
    @app.route('/api/toggle_component', methods=['POST'])
    def toggle_component():
        return api_toggle_component()
    
    @app.route('/api/custom_layout', methods=['POST']) 
    def custom_layout():
        return api_custom_layout()
    
    @app.route('/api/layout_css')
    def layout_css():
        return api_layout_css()