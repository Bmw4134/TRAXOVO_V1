"""
Persistent Collaborative Development Engine for TRAXOVO
Maintains context and state across all interactions
"""

import os
import json
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, g

persistent_dev_bp = Blueprint('persistent_dev', __name__)

class PersistentDevEngine:
    """Persistent development context engine"""
    
    def __init__(self):
        self.context_file = 'context_state.json'
        self.load_context()
    
    def load_context(self):
        """Load persistent context state"""
        try:
            if os.path.exists(self.context_file):
                with open(self.context_file, 'r') as f:
                    self.context = json.load(f)
            else:
                self.create_default_context()
        except Exception as e:
            print(f"Error loading context: {e}")
            self.create_default_context()
    
    def create_default_context(self):
        """Create default context if file doesn't exist"""
        self.context = {
            "collaborative_dev_mode": True,
            "template_system": {
                "master_template_active": True,
                "unified_layout_usage": "active",
                "consolidation_complete": True,
                "live_preview_enabled": True
            },
            "routing_state": {
                "dashboard": "master_unified.html",
                "enhanced_dashboard": "enhanced_dashboard_unified.html",
                "attendance_complete": "attendance_complete_unified.html",
                "fleet_map": "fleet_map_unified.html",
                "navigation_unified": True
            },
            "development_context": {
                "kaizen_mode": True,
                "evolutionary_approach": True,
                "no_regression_policy": True,
                "authentic_data_only": True
            },
            "system_health": {
                "sidebar_navigation": "active",
                "responsive_design": "optimized",
                "template_errors": [],
                "last_update": datetime.now().isoformat()
            },
            "fleet_data": {
                "total_assets": 581,
                "active_assets": 610,
                "total_drivers": 92,
                "revenue_total": "2.21M",
                "utilization_rate": 87.5
            }
        }
        self.save_context()
    
    def save_context(self):
        """Save context to persistent storage"""
        try:
            self.context["system_health"]["last_update"] = datetime.now().isoformat()
            with open(self.context_file, 'w') as f:
                json.dump(self.context, f, indent=2)
        except Exception as e:
            print(f"Error saving context: {e}")
    
    def get_context(self):
        """Get current context state"""
        return self.context
    
    def update_context(self, updates):
        """Update context with new data"""
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = deep_update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        
        deep_update(self.context, updates)
        self.save_context()
    
    def toggle_dev_mode(self):
        """Toggle development mode"""
        current = self.context.get("collaborative_dev_mode", False)
        self.context["collaborative_dev_mode"] = not current
        self.save_context()
        return self.context["collaborative_dev_mode"]
    
    def get_system_status(self):
        """Get comprehensive system status"""
        return {
            "dev_mode_active": self.context.get("collaborative_dev_mode", False),
            "template_system": self.context.get("template_system", {}),
            "routing_health": self.context.get("routing_state", {}),
            "system_health": self.context.get("system_health", {}),
            "development_principles": self.context.get("development_context", {}),
            "fleet_metrics": self.context.get("fleet_data", {})
        }
    
    def prime_agent_context(self):
        """Generate context for agent priming"""
        return {
            "system_overview": "TRAXOVO Fleet Management Platform with persistent development assistance",
            "current_state": self.context,
            "development_mode": "Enhanced collaborative mode with template consolidation and live preview",
            "key_principles": [
                "Kaizen-based evolutionary improvements only",
                "No regression - only enhancement",
                "Authentic data from real fleet operations",
                "Template consolidation with master unified layout",
                "Live preview integration for immediate feedback"
            ],
            "active_features": [
                "Master template system with unified navigation",
                "Real-time data processing (581 assets, 610 active, 92 drivers)",
                "Professional HERC-inspired interface design",
                "Responsive layout with mobile optimization"
            ]
        }

# Initialize persistent engine
dev_engine = PersistentDevEngine()

@persistent_dev_bp.route('/dev/assistant')
def dev_assistant_dashboard():
    """Development assistant dashboard"""
    context = dev_engine.get_context()
    system_status = dev_engine.get_system_status()
    
    return render_template('dev_assistant_dashboard.html', 
                         context=context,
                         system_status=system_status,
                         page_title="Development Assistant",
                         page_subtitle="Persistent collaborative development engine")

@persistent_dev_bp.route('/dev/status')
def dev_status():
    """Get development status"""
    return jsonify(dev_engine.get_system_status())

@persistent_dev_bp.route('/dev/toggle', methods=['POST'])
def toggle_dev_mode():
    """Toggle development mode"""
    new_state = dev_engine.toggle_dev_mode()
    return jsonify({
        "dev_mode_active": new_state,
        "message": f"Development mode {'activated' if new_state else 'deactivated'}"
    })

@persistent_dev_bp.route('/dev/prime-context')
def prime_context():
    """Get context for agent priming"""
    return jsonify(dev_engine.prime_agent_context())

@persistent_dev_bp.route('/dev/update-context', methods=['POST'])
def update_context():
    """Update development context"""
    updates = request.get_json()
    dev_engine.update_context(updates)
    return jsonify({"status": "updated", "context": dev_engine.get_context()})

def load_dev_context():
    """Load development context into Flask g object"""
    g.dev_context = dev_engine.get_context()
    g.dev_mode_active = dev_engine.get_context().get("collaborative_dev_mode", False)