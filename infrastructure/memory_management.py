"""
TRAXOVO Memory Management System
Intelligent caching and resource optimization for enterprise-scale deployment
"""

import os
import gc
import psutil
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from functools import wraps
import pickle
import hashlib
import json

class MemoryCache:
    """Enterprise-grade memory caching with intelligent eviction"""
    
    def __init__(self, max_size_mb: int = 100, ttl_minutes: int = 30):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache = {}
        self.access_times = {}
        self.lock = threading.RLock()
        
    def _get_size(self, obj) -> int:
        """Estimate object size in bytes"""
        try:
            return len(pickle.dumps(obj))
        except:
            return len(str(obj).encode('utf-8'))
    
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired_keys = []
        
        for key, (data, timestamp) in self.cache.items():
            if now - timestamp > self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def _evict_lru(self):
        """Evict least recently used items to free memory"""
        if not self.access_times:
            return
        
        # Sort by access time (oldest first)
        sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])
        
        # Remove oldest 25% of entries
        remove_count = max(1, len(sorted_keys) // 4)
        
        for key, _ in sorted_keys[:remove_count]:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def _get_current_size(self) -> int:
        """Calculate current cache size"""
        total_size = 0
        for key, (data, _) in self.cache.items():
            total_size += self._get_size(data)
        return total_size
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            self._cleanup_expired()
            
            if key in self.cache:
                data, timestamp = self.cache[key]
                self.access_times[key] = datetime.now()
                return data
            
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """Set item in cache with intelligent memory management"""
        with self.lock:
            self._cleanup_expired()
            
            # Check if we need to evict items
            current_size = self._get_current_size()
            new_item_size = self._get_size(value)
            
            if current_size + new_item_size > self.max_size_bytes:
                self._evict_lru()
                
                # If still too large, don't cache
                if self._get_current_size() + new_item_size > self.max_size_bytes:
                    return False
            
            self.cache[key] = (value, datetime.now())
            self.access_times[key] = datetime.now()
            return True
    
    def delete(self, key: str):
        """Remove item from cache"""
        with self.lock:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            return {
                'size_bytes': self._get_current_size(),
                'size_mb': self._get_current_size() / (1024 * 1024),
                'item_count': len(self.cache),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'hit_rate': getattr(self, '_hit_rate', 0.0)
            }

class ResourceMonitor:
    """System resource monitoring and optimization"""
    
    def __init__(self):
        self.memory_threshold = 80  # Percentage
        self.cpu_threshold = 90     # Percentage
        self.monitoring = False
        self.alerts = []
        
    def start_monitoring(self):
        """Start resource monitoring thread"""
        if not self.monitoring:
            self.monitoring = True
            monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._check_memory()
                self._check_cpu()
                self._check_disk_space()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"Resource monitoring error: {e}")
                time.sleep(60)
    
    def _check_memory(self):
        """Check memory usage and trigger cleanup if needed"""
        memory = psutil.virtual_memory()
        
        if memory.percent > self.memory_threshold:
            self._trigger_memory_cleanup()
            self.alerts.append({
                'type': 'memory',
                'level': 'warning',
                'message': f'High memory usage: {memory.percent}%',
                'timestamp': datetime.now()
            })
    
    def _check_cpu(self):
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > self.cpu_threshold:
            self.alerts.append({
                'type': 'cpu',
                'level': 'warning',
                'message': f'High CPU usage: {cpu_percent}%',
                'timestamp': datetime.now()
            })
    
    def _check_disk_space(self):
        """Check disk space usage"""
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        if disk_percent > 85:
            self.alerts.append({
                'type': 'disk',
                'level': 'warning',
                'message': f'Low disk space: {disk_percent:.1f}%',
                'timestamp': datetime.now()
            })
    
    def _trigger_memory_cleanup(self):
        """Trigger memory cleanup procedures"""
        # Force garbage collection
        gc.collect()
        
        # Clear caches
        global gauge_cache, asset_cache
        if 'gauge_cache' in globals():
            gauge_cache.clear()
        if 'asset_cache' in globals():
            asset_cache.clear()
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'memory': {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'percent_used': memory.percent,
                'status': 'warning' if memory.percent > self.memory_threshold else 'ok'
            },
            'cpu': {
                'percent_used': psutil.cpu_percent(interval=1),
                'core_count': psutil.cpu_count(),
                'status': 'warning' if psutil.cpu_percent() > self.cpu_threshold else 'ok'
            },
            'disk': {
                'total_gb': disk.total / (1024**3),
                'free_gb': disk.free / (1024**3),
                'percent_used': (disk.used / disk.total) * 100,
                'status': 'warning' if (disk.used / disk.total) * 100 > 85 else 'ok'
            },
            'alerts': self.alerts[-10:],  # Last 10 alerts
            'timestamp': datetime.now().isoformat()
        }

# Global instances
gauge_cache = MemoryCache(max_size_mb=50, ttl_minutes=15)
asset_cache = MemoryCache(max_size_mb=30, ttl_minutes=30)
resource_monitor = ResourceMonitor()

def cached_gauge_data(cache_key_suffix: str = ""):
    """Decorator for caching GAUGE API responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"gauge_{func.__name__}_{cache_key_suffix}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = gauge_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            gauge_cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator

def cached_asset_data(cache_key_suffix: str = ""):
    """Decorator for caching asset processing results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"asset_{func.__name__}_{cache_key_suffix}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = asset_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            asset_cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator

def optimize_memory_usage():
    """Manual memory optimization trigger"""
    # Force garbage collection
    gc.collect()
    
    # Clear caches if memory is high
    memory = psutil.virtual_memory()
    if memory.percent > 75:
        gauge_cache.clear()
        asset_cache.clear()
        gc.collect()
    
    return {
        'memory_freed': True,
        'cache_cleared': memory.percent > 75,
        'current_memory_percent': psutil.virtual_memory().percent
    }

def get_memory_stats() -> Dict:
    """Get comprehensive memory statistics"""
    return {
        'system': resource_monitor.get_system_status(),
        'gauge_cache': gauge_cache.get_stats(),
        'asset_cache': asset_cache.get_stats(),
        'python_memory': {
            'objects': len(gc.get_objects()),
            'collections': gc.get_stats()
        }
    }

# Start monitoring on import
resource_monitor.start_monitoring()