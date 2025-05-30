"""
Adaptive Refresh Rate Optimizer for Dashboard Performance
Intelligent refresh management based on user behavior and system metrics
"""

from flask import Blueprint, request, jsonify, session
import logging
from datetime import datetime, timedelta
import time
import psutil
import os

adaptive_refresh_bp = Blueprint('adaptive_refresh', __name__, url_prefix='/adaptive')

class AdaptiveRefreshOptimizer:
    """Intelligent refresh rate optimization engine"""
    
    def __init__(self):
        self.user_sessions = {}
        self.system_metrics = {}
        self.refresh_history = {}
        
    def analyze_optimal_refresh_rate(self, user_id, dashboard_type='executive'):
        """Determine optimal refresh rate based on multiple factors"""
        try:
            # Get user behavior patterns
            user_pattern = self._analyze_user_behavior(user_id)
            
            # Get current system performance
            system_load = self._get_system_performance()
            
            # Get data volatility (how often data actually changes)
            data_volatility = self._analyze_data_volatility(dashboard_type)
            
            # Calculate optimal refresh rate
            optimal_rate = self._calculate_refresh_rate(user_pattern, system_load, data_volatility)
            
            return {
                'recommended_refresh_seconds': optimal_rate,
                'refresh_strategy': self._get_refresh_strategy(optimal_rate),
                'user_behavior_score': user_pattern['activity_score'],
                'system_load_factor': system_load['load_factor'],
                'data_volatility_score': data_volatility['change_frequency'],
                'optimization_reason': self._get_optimization_explanation(user_pattern, system_load, data_volatility)
            }
            
        except Exception as e:
            logging.error(f"Adaptive refresh analysis error: {e}")
            return self._get_conservative_defaults()
    
    def _analyze_user_behavior(self, user_id):
        """Analyze user interaction patterns"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'page_views': 0,
                'manual_refreshes': 0,
                'time_on_dashboard': 0,
                'last_activity': datetime.now(),
                'interaction_frequency': 'low'
            }
        
        session_data = self.user_sessions[user_id]
        
        # Calculate activity score based on recent behavior
        time_since_activity = (datetime.now() - session_data['last_activity']).total_seconds()
        
        if time_since_activity < 300:  # Active in last 5 minutes
            activity_score = 'high'
        elif time_since_activity < 1800:  # Active in last 30 minutes
            activity_score = 'medium'
        else:
            activity_score = 'low'
        
        return {
            'activity_score': activity_score,
            'manual_refresh_rate': session_data['manual_refreshes'],
            'engagement_level': self._calculate_engagement_level(session_data),
            'preferred_update_frequency': self._infer_preferred_frequency(session_data)
        }
    
    def _get_system_performance(self):
        """Get current system performance metrics"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Calculate load factor (0-1, where 1 is high load)
            load_factor = (cpu_usage + memory_usage) / 200
            
            # Determine system health
            if load_factor < 0.5:
                system_health = 'excellent'
            elif load_factor < 0.7:
                system_health = 'good'
            elif load_factor < 0.85:
                system_health = 'moderate'
            else:
                system_health = 'high_load'
            
            return {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'load_factor': load_factor,
                'system_health': system_health,
                'recommendation': self._get_performance_recommendation(system_health)
            }
            
        except Exception as e:
            logging.error(f"System performance check error: {e}")
            return {
                'cpu_usage': 50,
                'memory_usage': 50,
                'load_factor': 0.5,
                'system_health': 'unknown',
                'recommendation': 'conservative_refresh'
            }
    
    def _analyze_data_volatility(self, dashboard_type):
        """Analyze how frequently dashboard data actually changes"""
        volatility_profiles = {
            'executive': {
                'change_frequency': 'low',  # Executive metrics change slowly
                'typical_interval': 3600,   # 1 hour
                'critical_updates': False
            },
            'operations': {
                'change_frequency': 'medium',  # Operational data changes moderately
                'typical_interval': 900,       # 15 minutes
                'critical_updates': True
            },
            'dispatcher': {
                'change_frequency': 'high',   # Dispatch data changes frequently
                'typical_interval': 300,      # 5 minutes
                'critical_updates': True
            },
            'real_time': {
                'change_frequency': 'very_high',  # Real-time requires frequent updates
                'typical_interval': 60,           # 1 minute
                'critical_updates': True
            }
        }
        
        return volatility_profiles.get(dashboard_type, volatility_profiles['executive'])
    
    def _calculate_refresh_rate(self, user_pattern, system_load, data_volatility):
        """Calculate optimal refresh rate in seconds"""
        base_interval = data_volatility['typical_interval']
        
        # Adjust based on user activity
        if user_pattern['activity_score'] == 'high':
            user_multiplier = 0.5  # More frequent updates for active users
        elif user_pattern['activity_score'] == 'medium':
            user_multiplier = 1.0  # Standard rate
        else:
            user_multiplier = 2.0  # Less frequent for inactive users
        
        # Adjust based on system load
        if system_load['load_factor'] < 0.5:
            system_multiplier = 0.8  # Can handle more frequent updates
        elif system_load['load_factor'] < 0.7:
            system_multiplier = 1.0  # Standard rate
        else:
            system_multiplier = 1.5  # Reduce frequency under load
        
        # Calculate final interval
        optimal_interval = base_interval * user_multiplier * system_multiplier
        
        # Apply constraints
        min_interval = 60    # Never refresh more than once per minute
        max_interval = 3600  # Never wait more than 1 hour
        
        return max(min_interval, min(max_interval, int(optimal_interval)))
    
    def _get_refresh_strategy(self, refresh_seconds):
        """Determine the refresh strategy based on interval"""
        if refresh_seconds <= 300:
            return 'aggressive'
        elif refresh_seconds <= 900:
            return 'standard'
        elif refresh_seconds <= 1800:
            return 'conservative'
        else:
            return 'minimal'
    
    def _get_optimization_explanation(self, user_pattern, system_load, data_volatility):
        """Provide explanation for the optimization decision"""
        reasons = []
        
        if user_pattern['activity_score'] == 'high':
            reasons.append("Active user session detected - increasing update frequency")
        elif user_pattern['activity_score'] == 'low':
            reasons.append("Low user activity - reducing update frequency to save resources")
        
        if system_load['load_factor'] > 0.7:
            reasons.append("High system load detected - optimizing for performance")
        elif system_load['load_factor'] < 0.5:
            reasons.append("System running efficiently - can support more frequent updates")
        
        if data_volatility['change_frequency'] == 'low':
            reasons.append("Data changes infrequently - extended intervals appropriate")
        elif data_volatility['change_frequency'] == 'high':
            reasons.append("Volatile data requires frequent monitoring")
        
        return " | ".join(reasons) if reasons else "Standard optimization applied"
    
    def _calculate_engagement_level(self, session_data):
        """Calculate user engagement level"""
        if session_data['manual_refreshes'] > 5:
            return 'high'
        elif session_data['manual_refreshes'] > 2:
            return 'medium'
        else:
            return 'low'
    
    def _infer_preferred_frequency(self, session_data):
        """Infer user's preferred update frequency"""
        if session_data['manual_refreshes'] > 10:
            return 'very_frequent'
        elif session_data['manual_refreshes'] > 5:
            return 'frequent'
        elif session_data['manual_refreshes'] > 2:
            return 'moderate'
        else:
            return 'infrequent'
    
    def _get_performance_recommendation(self, system_health):
        """Get performance-based recommendation"""
        recommendations = {
            'excellent': 'Can support aggressive refresh rates',
            'good': 'Standard refresh rates recommended',
            'moderate': 'Conservative refresh rates advised',
            'high_load': 'Minimal refresh rates to preserve performance'
        }
        return recommendations.get(system_health, 'Standard refresh rates')
    
    def _get_conservative_defaults(self):
        """Return conservative defaults when analysis fails"""
        return {
            'recommended_refresh_seconds': 900,  # 15 minutes
            'refresh_strategy': 'conservative',
            'user_behavior_score': 'unknown',
            'system_load_factor': 0.5,
            'data_volatility_score': 'medium',
            'optimization_reason': 'Using conservative defaults due to analysis limitations'
        }
    
    def track_user_activity(self, user_id, activity_type):
        """Track user activity for behavior analysis"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'page_views': 0,
                'manual_refreshes': 0,
                'time_on_dashboard': 0,
                'last_activity': datetime.now(),
                'interaction_frequency': 'low'
            }
        
        session = self.user_sessions[user_id]
        session['last_activity'] = datetime.now()
        
        if activity_type == 'page_view':
            session['page_views'] += 1
        elif activity_type == 'manual_refresh':
            session['manual_refreshes'] += 1
        elif activity_type == 'dashboard_interaction':
            session['time_on_dashboard'] += 1

# Global optimizer instance
optimizer = AdaptiveRefreshOptimizer()

@adaptive_refresh_bp.route('/api/optimize')
def get_optimization():
    """Get optimized refresh rate for current user and dashboard"""
    try:
        user_id = session.get('user_id', 'anonymous')
        dashboard_type = request.args.get('dashboard_type', 'executive')
        
        # Track this as a page view
        optimizer.track_user_activity(user_id, 'page_view')
        
        # Get optimization recommendation
        optimization = optimizer.analyze_optimal_refresh_rate(user_id, dashboard_type)
        
        return jsonify({
            'status': 'success',
            'optimization': optimization,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'dashboard_type': dashboard_type
        })
        
    except Exception as e:
        logging.error(f"Optimization API error: {e}")
        return jsonify({'error': str(e)}), 500

@adaptive_refresh_bp.route('/api/track-activity', methods=['POST'])
def track_activity():
    """Track user activity for optimization"""
    try:
        data = request.get_json()
        user_id = session.get('user_id', 'anonymous')
        activity_type = data.get('activity_type', 'page_view')
        
        optimizer.track_user_activity(user_id, activity_type)
        
        return jsonify({
            'status': 'success',
            'message': 'Activity tracked',
            'user_id': user_id
        })
        
    except Exception as e:
        logging.error(f"Activity tracking error: {e}")
        return jsonify({'error': str(e)}), 500

@adaptive_refresh_bp.route('/api/system-health')
def get_system_health():
    """Get current system health metrics"""
    try:
        system_metrics = optimizer._get_system_performance()
        
        return jsonify({
            'status': 'success',
            'system_health': system_metrics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"System health check error: {e}")
        return jsonify({'error': str(e)}), 500