"""
Adaptive Refresh Rate Optimizer for Dashboard Performance
Dynamically adjusts refresh rates based on data load, user activity, and system performance
"""

import time
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RefreshConfig:
    """Configuration for adaptive refresh rates"""
    component_name: str
    base_refresh_rate: int  # seconds
    min_refresh_rate: int   # fastest possible
    max_refresh_rate: int   # slowest fallback
    priority: int           # 1=critical, 5=low priority
    data_complexity: float  # 0.1=simple, 1.0=complex

class AdaptiveRefreshOptimizer:
    """Intelligent refresh rate management for optimal dashboard performance"""
    
    def __init__(self):
        self.refresh_configs = self._initialize_refresh_configs()
        self.performance_metrics = {}
        self.user_activity_tracker = {}
        self.current_refresh_rates = {}
        self.last_optimization = datetime.now()
        
    def _initialize_refresh_configs(self):
        """Define refresh configurations for each dashboard component"""
        return {
            'gauge_api_assets': RefreshConfig(
                component_name='gauge_api_assets',
                base_refresh_rate=15,  # 15 seconds for GPS tracking
                min_refresh_rate=10,   # Fastest: 10 seconds
                max_refresh_rate=60,   # Slowest: 1 minute
                priority=1,            # Critical priority
                data_complexity=0.8    # High complexity (717 assets)
            ),
            'fleet_metrics': RefreshConfig(
                component_name='fleet_metrics',
                base_refresh_rate=30,  # 30 seconds for fleet summary
                min_refresh_rate=15,
                max_refresh_rate=120,
                priority=2,
                data_complexity=0.6
            ),
            'asset_depreciation': RefreshConfig(
                component_name='asset_depreciation',
                base_refresh_rate=300,  # 5 minutes for depreciation
                min_refresh_rate=60,
                max_refresh_rate=1800,  # 30 minutes max
                priority=3,
                data_complexity=0.4
            ),
            'attendance_data': RefreshConfig(
                component_name='attendance_data',
                base_refresh_rate=45,   # 45 seconds for attendance
                min_refresh_rate=30,
                max_refresh_rate=300,
                priority=2,
                data_complexity=0.7
            ),
            'billing_analytics': RefreshConfig(
                component_name='billing_analytics',
                base_refresh_rate=180,  # 3 minutes for billing
                min_refresh_rate=60,
                max_refresh_rate=600,   # 10 minutes max
                priority=3,
                data_complexity=0.5
            ),
            'ai_insights': RefreshConfig(
                component_name='ai_insights',
                base_refresh_rate=120,  # 2 minutes for AI analysis
                min_refresh_rate=60,
                max_refresh_rate=900,   # 15 minutes max
                priority=4,
                data_complexity=0.9
            )
        }
    
    def track_user_activity(self, user_id: str, activity_type: str):
        """Track user activity to optimize refresh rates"""
        current_time = datetime.now()
        
        if user_id not in self.user_activity_tracker:
            self.user_activity_tracker[user_id] = {
                'last_activity': current_time,
                'activity_count': 0,
                'active_components': set(),
                'session_start': current_time
            }
        
        self.user_activity_tracker[user_id]['last_activity'] = current_time
        self.user_activity_tracker[user_id]['activity_count'] += 1
        
        # Track which components user is actively viewing
        if activity_type.startswith('view_'):
            component = activity_type.replace('view_', '')
            self.user_activity_tracker[user_id]['active_components'].add(component)
    
    def measure_component_performance(self, component_name: str, execution_time: float, data_size: int):
        """Measure and store component performance metrics"""
        current_time = datetime.now()
        
        if component_name not in self.performance_metrics:
            self.performance_metrics[component_name] = {
                'execution_times': [],
                'data_sizes': [],
                'error_count': 0,
                'success_count': 0,
                'last_measured': current_time
            }
        
        metrics = self.performance_metrics[component_name]
        metrics['execution_times'].append(execution_time)
        metrics['data_sizes'].append(data_size)
        metrics['success_count'] += 1
        metrics['last_measured'] = current_time
        
        # Keep only last 50 measurements for rolling average
        if len(metrics['execution_times']) > 50:
            metrics['execution_times'] = metrics['execution_times'][-50:]
            metrics['data_sizes'] = metrics['data_sizes'][-50:]
    
    def record_component_error(self, component_name: str):
        """Record component error for performance analysis"""
        if component_name not in self.performance_metrics:
            self.performance_metrics[component_name] = {
                'execution_times': [],
                'data_sizes': [],
                'error_count': 0,
                'success_count': 0,
                'last_measured': datetime.now()
            }
        
        self.performance_metrics[component_name]['error_count'] += 1
    
    def calculate_optimal_refresh_rate(self, component_name: str) -> int:
        """Calculate optimal refresh rate based on performance and activity"""
        if component_name not in self.refresh_configs:
            return 60  # Default fallback
        
        config = self.refresh_configs[component_name]
        base_rate = config.base_refresh_rate
        
        # Start with base rate
        optimal_rate = base_rate
        
        # Adjust based on performance metrics
        if component_name in self.performance_metrics:
            metrics = self.performance_metrics[component_name]
            
            # Calculate average execution time
            if metrics['execution_times']:
                avg_execution_time = sum(metrics['execution_times']) / len(metrics['execution_times'])
                
                # If component is slow, increase refresh rate
                if avg_execution_time > 2.0:  # 2 seconds threshold
                    optimal_rate = min(optimal_rate * 1.5, config.max_refresh_rate)
                elif avg_execution_time < 0.5:  # Fast component
                    optimal_rate = max(optimal_rate * 0.8, config.min_refresh_rate)
            
            # Adjust based on error rate
            total_attempts = metrics['success_count'] + metrics['error_count']
            if total_attempts > 0:
                error_rate = metrics['error_count'] / total_attempts
                if error_rate > 0.1:  # More than 10% errors
                    optimal_rate = min(optimal_rate * 2, config.max_refresh_rate)
        
        # Adjust based on user activity
        active_users = self._count_active_users()
        if active_users == 0:
            # No active users - slow down non-critical components
            if config.priority > 2:
                optimal_rate = min(optimal_rate * 3, config.max_refresh_rate)
        elif active_users > 5:
            # High user load - optimize critical components
            if config.priority <= 2:
                optimal_rate = max(optimal_rate * 0.7, config.min_refresh_rate)
        
        # Adjust based on data complexity
        complexity_factor = 1 + (config.data_complexity - 0.5)
        optimal_rate = int(optimal_rate * complexity_factor)
        
        # Ensure within bounds
        optimal_rate = max(config.min_refresh_rate, min(optimal_rate, config.max_refresh_rate))
        
        return optimal_rate
    
    def _count_active_users(self) -> int:
        """Count users active in the last 5 minutes"""
        current_time = datetime.now()
        active_threshold = current_time - timedelta(minutes=5)
        
        active_count = 0
        for user_data in self.user_activity_tracker.values():
            if user_data['last_activity'] > active_threshold:
                active_count += 1
        
        return active_count
    
    def optimize_all_refresh_rates(self):
        """Optimize refresh rates for all components"""
        current_time = datetime.now()
        
        # Only optimize every 30 seconds to avoid overhead
        if current_time - self.last_optimization < timedelta(seconds=30):
            return self.current_refresh_rates
        
        self.last_optimization = current_time
        
        for component_name in self.refresh_configs.keys():
            optimal_rate = self.calculate_optimal_refresh_rate(component_name)
            self.current_refresh_rates[component_name] = optimal_rate
        
        return self.current_refresh_rates
    
    def get_refresh_rate(self, component_name: str) -> int:
        """Get current optimal refresh rate for a component"""
        if component_name not in self.current_refresh_rates:
            self.current_refresh_rates[component_name] = self.calculate_optimal_refresh_rate(component_name)
        
        return self.current_refresh_rates[component_name]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        active_users = self._count_active_users()
        
        summary = {
            'active_users': active_users,
            'total_components': len(self.refresh_configs),
            'optimized_components': len(self.current_refresh_rates),
            'last_optimization': self.last_optimization.isoformat(),
            'component_status': {}
        }
        
        for component_name, config in self.refresh_configs.items():
            current_rate = self.current_refresh_rates.get(component_name, config.base_refresh_rate)
            
            status = {
                'current_refresh_rate': current_rate,
                'base_refresh_rate': config.base_refresh_rate,
                'priority': config.priority,
                'optimization_factor': current_rate / config.base_refresh_rate
            }
            
            if component_name in self.performance_metrics:
                metrics = self.performance_metrics[component_name]
                status.update({
                    'avg_execution_time': sum(metrics['execution_times']) / len(metrics['execution_times']) if metrics['execution_times'] else 0,
                    'success_rate': metrics['success_count'] / (metrics['success_count'] + metrics['error_count']) if (metrics['success_count'] + metrics['error_count']) > 0 else 1.0,
                    'total_executions': metrics['success_count'] + metrics['error_count']
                })
            
            summary['component_status'][component_name] = status
        
        return summary
    
    def force_component_refresh(self, component_name: str):
        """Force immediate refresh of a component (resets to minimum rate temporarily)"""
        if component_name in self.refresh_configs:
            config = self.refresh_configs[component_name]
            self.current_refresh_rates[component_name] = config.min_refresh_rate
            logger.info(f"Forced refresh for {component_name} - rate set to {config.min_refresh_rate}s")

# Global optimizer instance
refresh_optimizer = AdaptiveRefreshOptimizer()

def get_refresh_optimizer():
    """Get the global refresh optimizer"""
    return refresh_optimizer