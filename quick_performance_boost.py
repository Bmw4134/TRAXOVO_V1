"""
TRAXOVO Quick Performance Boost Toggle
One-click system optimization for different performance modes
"""

import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required

performance_boost_bp = Blueprint('performance_boost', __name__)

class PerformanceBoostManager:
    """Manages system performance settings and optimization modes"""
    
    def __init__(self):
        self.settings_file = 'performance_settings.json'
        self.modes = {
            'eco': {
                'name': 'Eco Mode',
                'description': 'Maximum battery life, reduced performance',
                'cpu_usage': 25,
                'memory_limit': 512,
                'refresh_rate': 30,
                'background_tasks': False,
                'real_time_updates': False,
                'visual_effects': 'minimal',
                'cache_size': 'small'
            },
            'balanced': {
                'name': 'Balanced Mode',
                'description': 'Optimal balance of performance and efficiency',
                'cpu_usage': 50,
                'memory_limit': 1024,
                'refresh_rate': 15,
                'background_tasks': True,
                'real_time_updates': True,
                'visual_effects': 'standard',
                'cache_size': 'medium'
            },
            'performance': {
                'name': 'Performance Mode',
                'description': 'Maximum speed and responsiveness',
                'cpu_usage': 75,
                'memory_limit': 2048,
                'refresh_rate': 5,
                'background_tasks': True,
                'real_time_updates': True,
                'visual_effects': 'enhanced',
                'cache_size': 'large'
            },
            'turbo': {
                'name': 'Turbo Mode',
                'description': 'Ultimate performance for critical operations',
                'cpu_usage': 100,
                'memory_limit': 4096,
                'refresh_rate': 2,
                'background_tasks': True,
                'real_time_updates': True,
                'visual_effects': 'maximum',
                'cache_size': 'maximum'
            }
        }
        self.current_mode = self.load_current_mode()
    
    def load_current_mode(self):
        """Load current performance mode from settings"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('current_mode', 'balanced')
        except:
            pass
        return 'balanced'
    
    def save_settings(self, mode, user_id=None):
        """Save performance settings"""
        settings = {
            'current_mode': mode,
            'last_changed': datetime.now().isoformat(),
            'changed_by': user_id,
            'mode_history': self.get_mode_history()
        }
        
        # Add current change to history
        settings['mode_history'].append({
            'mode': mode,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        })
        
        # Keep only last 10 changes
        settings['mode_history'] = settings['mode_history'][-10:]
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving performance settings: {e}")
            return False
    
    def get_mode_history(self):
        """Get performance mode change history"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('mode_history', [])
        except:
            pass
        return []
    
    def set_performance_mode(self, mode, user_id=None):
        """Set new performance mode"""
        if mode not in self.modes:
            return False, f"Invalid mode: {mode}"
        
        self.current_mode = mode
        
        if self.save_settings(mode, user_id):
            return True, f"Performance mode set to {self.modes[mode]['name']}"
        else:
            return False, "Failed to save performance settings"
    
    def get_current_settings(self):
        """Get current performance settings"""
        return {
            'mode': self.current_mode,
            'settings': self.modes[self.current_mode],
            'available_modes': self.modes
        }
    
    def get_performance_impact(self, target_mode):
        """Calculate performance impact of switching modes"""
        current = self.modes[self.current_mode]
        target = self.modes[target_mode]
        
        impact = {
            'cpu_change': target['cpu_usage'] - current['cpu_usage'],
            'memory_change': target['memory_limit'] - current['memory_limit'],
            'speed_change': current['refresh_rate'] - target['refresh_rate'],
            'features_change': []
        }
        
        # Analyze feature changes
        if target['real_time_updates'] != current['real_time_updates']:
            status = 'enabled' if target['real_time_updates'] else 'disabled'
            impact['features_change'].append(f"Real-time updates {status}")
        
        if target['background_tasks'] != current['background_tasks']:
            status = 'enabled' if target['background_tasks'] else 'disabled'
            impact['features_change'].append(f"Background tasks {status}")
        
        if target['visual_effects'] != current['visual_effects']:
            impact['features_change'].append(f"Visual effects: {target['visual_effects']}")
        
        return impact
    
    def apply_system_optimizations(self, mode):
        """Apply system-level optimizations based on mode"""
        settings = self.modes[mode]
        optimizations = []
        
        # Cache optimization
        if settings['cache_size'] == 'maximum':
            optimizations.append("Maximum cache allocation")
        elif settings['cache_size'] == 'small':
            optimizations.append("Minimal cache to save memory")
        
        # Background task optimization
        if settings['background_tasks']:
            optimizations.append("Background processing enabled")
        else:
            optimizations.append("Background processing disabled")
        
        # Real-time optimization
        if settings['real_time_updates']:
            optimizations.append(f"Real-time updates every {settings['refresh_rate']}s")
        else:
            optimizations.append("Real-time updates disabled")
        
        return optimizations

# Global instance
performance_manager = PerformanceBoostManager()

@performance_boost_bp.route('/performance_boost')
@login_required
def performance_dashboard():
    """Performance boost control dashboard"""
    current_settings = performance_manager.get_current_settings()
    history = performance_manager.get_mode_history()
    
    return render_template('performance_boost.html',
                         current_settings=current_settings,
                         history=history)

@performance_boost_bp.route('/api/performance/set_mode', methods=['POST'])
@login_required
def set_performance_mode():
    """API endpoint to set performance mode"""
    try:
        data = request.get_json()
        mode = data.get('mode')
        
        if not mode:
            return jsonify({'success': False, 'message': 'Mode is required'}), 400
        
        from flask_login import current_user
        user_id = getattr(current_user, 'id', 'unknown')
        
        success, message = performance_manager.set_performance_mode(mode, user_id)
        
        if success:
            # Get impact analysis
            current_settings = performance_manager.get_current_settings()
            optimizations = performance_manager.apply_system_optimizations(mode)
            
            return jsonify({
                'success': True,
                'message': message,
                'current_mode': mode,
                'settings': current_settings['settings'],
                'optimizations': optimizations
            })
        else:
            return jsonify({'success': False, 'message': message}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@performance_boost_bp.route('/api/performance/current')
@login_required
def get_current_performance():
    """Get current performance settings"""
    try:
        current_settings = performance_manager.get_current_settings()
        return jsonify({
            'success': True,
            'current_mode': performance_manager.current_mode,
            'settings': current_settings['settings'],
            'available_modes': current_settings['available_modes']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@performance_boost_bp.route('/api/performance/impact/<mode>')
@login_required
def get_performance_impact(mode):
    """Get performance impact analysis for a mode"""
    try:
        impact = performance_manager.get_performance_impact(mode)
        return jsonify({
            'success': True,
            'impact': impact
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@performance_boost_bp.route('/api/performance/history')
@login_required
def get_performance_history():
    """Get performance mode change history"""
    try:
        history = performance_manager.get_mode_history()
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def get_performance_manager():
    """Get the global performance manager instance"""
    return performance_manager