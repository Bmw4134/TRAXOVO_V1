"""
Interactive Quantum UI Color Palette Selector
Real-time customization of quantum dashboard visual intensity and color schemes
"""

from flask import jsonify, request
import json
import os
from datetime import datetime

class QuantumColorPaletteManager:
    """
    Manages dynamic color palettes for quantum UI components
    """
    
    def __init__(self):
        self.palettes = {
            "classic_quantum": {
                "name": "Classic Quantum",
                "description": "Original rainbow quantum effects",
                "primary_colors": ["#00ffff", "#ff00ff", "#ffff00"],
                "background": "radial-gradient(ellipse at center, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%)",
                "intensity": "high",
                "glow_strength": 0.8,
                "animation_speed": "3s"
            },
            "professional_quantum": {
                "name": "Professional Quantum",
                "description": "Toned down for executive presentations",
                "primary_colors": ["#3498db", "#9b59b6", "#2ecc71"],
                "background": "linear-gradient(135deg, #2c3e50 0%, #34495e 100%)",
                "intensity": "medium",
                "glow_strength": 0.4,
                "animation_speed": "5s"
            },
            "cyberpunk": {
                "name": "Cyberpunk",
                "description": "High-tech neon aesthetic",
                "primary_colors": ["#ff0080", "#00ff80", "#8000ff"],
                "background": "radial-gradient(ellipse at center, #000000 0%, #1a0033 50%, #330066 100%)",
                "intensity": "extreme",
                "glow_strength": 1.0,
                "animation_speed": "2s"
            },
            "aurora": {
                "name": "Aurora",
                "description": "Northern lights inspired",
                "primary_colors": ["#00ffaa", "#0080ff", "#aa00ff"],
                "background": "radial-gradient(ellipse at center, #001122 0%, #002244 50%, #003366 100%)",
                "intensity": "high",
                "glow_strength": 0.7,
                "animation_speed": "4s"
            },
            "minimalist": {
                "name": "Minimalist",
                "description": "Clean and subtle effects",
                "primary_colors": ["#4fc3f7", "#ba68c8", "#ffb74d"],
                "background": "linear-gradient(135deg, #263238 0%, #37474f 100%)",
                "intensity": "low",
                "glow_strength": 0.2,
                "animation_speed": "8s"
            }
        }
        
        self.current_palette = "classic_quantum"
        self.custom_settings = {}
        
    def get_all_palettes(self):
        """Get all available color palettes"""
        return self.palettes
    
    def set_palette(self, palette_name):
        """Set the active color palette"""
        if palette_name in self.palettes:
            self.current_palette = palette_name
            return {
                "success": True,
                "palette": self.palettes[palette_name],
                "message": f"Switched to {self.palettes[palette_name]['name']} palette"
            }
        else:
            return {
                "success": False,
                "message": "Palette not found"
            }
    
    def get_current_palette(self):
        """Get the currently active palette"""
        return self.palettes[self.current_palette]
    
    def create_custom_palette(self, palette_data):
        """Create a custom color palette"""
        custom_name = f"custom_{int(datetime.now().timestamp())}"
        
        self.palettes[custom_name] = {
            "name": palette_data.get("name", "Custom Palette"),
            "description": palette_data.get("description", "User-created palette"),
            "primary_colors": palette_data.get("primary_colors", ["#00ffff", "#ff00ff", "#ffff00"]),
            "background": palette_data.get("background", "radial-gradient(ellipse at center, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%)"),
            "intensity": palette_data.get("intensity", "medium"),
            "glow_strength": palette_data.get("glow_strength", 0.5),
            "animation_speed": palette_data.get("animation_speed", "3s"),
            "custom": True
        }
        
        return {
            "success": True,
            "palette_id": custom_name,
            "palette": self.palettes[custom_name]
        }
    
    def generate_css_variables(self, palette_name=None):
        """Generate CSS variables for the specified palette"""
        if not palette_name:
            palette_name = self.current_palette
            
        palette = self.palettes.get(palette_name, self.palettes[self.current_palette])
        
        css_vars = {
            "--quantum-primary-1": palette["primary_colors"][0],
            "--quantum-primary-2": palette["primary_colors"][1],
            "--quantum-primary-3": palette["primary_colors"][2],
            "--quantum-background": palette["background"],
            "--quantum-glow-strength": str(palette["glow_strength"]),
            "--quantum-animation-speed": palette["animation_speed"],
            "--quantum-intensity": palette["intensity"]
        }
        
        return css_vars

# Global palette manager instance
_palette_manager = None

def get_palette_manager():
    """Get the global palette manager instance"""
    global _palette_manager
    if _palette_manager is None:
        _palette_manager = QuantumColorPaletteManager()
    return _palette_manager

def quantum_palette_api_get_palettes():
    """API endpoint to get all available palettes"""
    manager = get_palette_manager()
    return jsonify({
        "palettes": manager.get_all_palettes(),
        "current": manager.current_palette
    })

def quantum_palette_api_set_palette():
    """API endpoint to set active palette"""
    manager = get_palette_manager()
    data = request.get_json()
    palette_name = data.get("palette_name")
    
    result = manager.set_palette(palette_name)
    return jsonify(result)

def quantum_palette_api_create_custom():
    """API endpoint to create custom palette"""
    manager = get_palette_manager()
    palette_data = request.get_json()
    
    result = manager.create_custom_palette(palette_data)
    return jsonify(result)

def quantum_palette_api_get_css():
    """API endpoint to get CSS variables for current palette"""
    manager = get_palette_manager()
    palette_name = request.args.get("palette")
    
    css_vars = manager.generate_css_variables(palette_name)
    return jsonify({
        "css_variables": css_vars,
        "palette": manager.get_current_palette()
    })

def integrate_quantum_palette_routes(app):
    """Integrate quantum palette routes with the main Flask app"""
    
    @app.route('/api/quantum_palettes')
    def api_quantum_palettes():
        return quantum_palette_api_get_palettes()
    
    @app.route('/api/quantum_palette/set', methods=['POST'])
    def api_set_quantum_palette():
        return quantum_palette_api_set_palette()
    
    @app.route('/api/quantum_palette/create', methods=['POST'])
    def api_create_quantum_palette():
        return quantum_palette_api_create_custom()
    
    @app.route('/api/quantum_palette/css')
    def api_quantum_palette_css():
        return quantum_palette_api_get_css()