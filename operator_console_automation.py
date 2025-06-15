#!/usr/bin/env python3
"""
DWC Evolution Operator Console - Automation Heartbeat System
Advanced system monitoring and automated recovery capabilities
"""

import json
import time
import threading
from datetime import datetime, timedelta
import requests
import psutil
import os
import subprocess

class OperatorConsoleAutomation:
    def __init__(self):
        self.automation_active = True
        self.heartbeat_interval = 30  # seconds
        self.alert_thresholds = {
            'cpu_max': 85.0,
            'memory_max': 90.0,
            'disk_max': 95.0,
            'response_time_max': 5000  # ms
        }
        self.automation_log = []
        self.last_optimization = None
        
    def log_automation_event(self, event_type, message, details=None):
        """Log automation events with timestamp"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message,
            'details': details or {}
        }
        self.automation_log.append(event)
        print(f"[{event_type}] {message}")
        
        # Keep only last 100 events
        if len(self.automation_log) > 100:
            self.automation_log = self.automation_log[-100:]
    
    def get_system_health_score(self):
        """Calculate comprehensive system health score"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Test application response time
            start_time = time.time()
            try:
                response = requests.get('http://localhost:5000/health', timeout=5)
                response_time = (time.time() - start_time) * 1000
                app_healthy = response.status_code == 200
            except:
                response_time = 5000
                app_healthy = False
            
            # Calculate health score (0-100)
            cpu_score = max(0, 100 - cpu_percent)
            memory_score = max(0, 100 - memory.percent)
            disk_score = max(0, 100 - disk.percent)
            response_score = max(0, 100 - (response_time / 50))  # 50ms = perfect
            app_score = 100 if app_healthy else 0
            
            overall_score = (cpu_score + memory_score + disk_score + response_score + app_score) / 5
            
            return {
                'overall_score': overall_score,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'response_time': response_time,
                'app_healthy': app_healthy,
                'scores': {
                    'cpu': cpu_score,
                    'memory': memory_score,
                    'disk': disk_score,
                    'response': response_score,
                    'application': app_score
                }
            }
        except Exception as e:
            self.log_automation_event('ERROR', f'Health check failed: {str(e)}')
            return {
                'overall_score': 0,
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'response_time': 9999,
                'app_healthy': False,
                'scores': {}
            }
    
    def trigger_system_optimization(self):
        """Automated system optimization"""
        try:
            optimization_actions = []
            
            # Clear system cache
            try:
                subprocess.run(['sync'], check=True)
                optimization_actions.append('System cache cleared')
            except:
                pass
            
            # Clean temporary files
            try:
                temp_dirs = ['/tmp', '/var/tmp']
                for temp_dir in temp_dirs:
                    if os.path.exists(temp_dir):
                        for item in os.listdir(temp_dir):
                            if item.startswith('.tmp'):
                                try:
                                    os.remove(os.path.join(temp_dir, item))
                                except:
                                    pass
                optimization_actions.append('Temporary files cleaned')
            except:
                pass
            
            # Optimize Python garbage collection
            import gc
            collected = gc.collect()
            optimization_actions.append(f'Garbage collection: {collected} objects freed')
            
            self.last_optimization = datetime.now()
            self.log_automation_event('OPTIMIZATION', 'System optimization completed', {
                'actions': optimization_actions,
                'timestamp': self.last_optimization.isoformat()
            })
            
            return True
            
        except Exception as e:
            self.log_automation_event('ERROR', f'Optimization failed: {str(e)}')
            return False
    
    def check_and_respond_to_alerts(self, health_data):
        """Check thresholds and trigger automated responses"""
        alerts_triggered = []
        
        # CPU usage alert
        if health_data['cpu_percent'] > self.alert_thresholds['cpu_max']:
            alerts_triggered.append('HIGH_CPU')
            self.log_automation_event('ALERT', f'High CPU usage: {health_data["cpu_percent"]:.1f}%')
            
        # Memory usage alert
        if health_data['memory_percent'] > self.alert_thresholds['memory_max']:
            alerts_triggered.append('HIGH_MEMORY')
            self.log_automation_event('ALERT', f'High memory usage: {health_data["memory_percent"]:.1f}%')
            
        # Disk usage alert
        if health_data['disk_percent'] > self.alert_thresholds['disk_max']:
            alerts_triggered.append('HIGH_DISK')
            self.log_automation_event('ALERT', f'High disk usage: {health_data["disk_percent"]:.1f}%')
            
        # Response time alert
        if health_data['response_time'] > self.alert_thresholds['response_time_max']:
            alerts_triggered.append('SLOW_RESPONSE')
            self.log_automation_event('ALERT', f'Slow response time: {health_data["response_time"]:.0f}ms')
        
        # Trigger optimization if needed
        if alerts_triggered and (not self.last_optimization or 
                               datetime.now() - self.last_optimization > timedelta(minutes=5)):
            self.trigger_system_optimization()
        
        return alerts_triggered
    
    def validate_ragle_fleet_connectivity(self):
        """Validate RAGLE fleet data connectivity and accuracy"""
        try:
            response = requests.get('http://localhost:5000/api/ragle-fleet-data', timeout=10)
            if response.status_code == 200:
                fleet_data = response.json()
                
                # Validate data structure
                if isinstance(fleet_data, list) and len(fleet_data) > 0:
                    dfw_assets = [a for a in fleet_data if 'DFW' in a.get('asset_id', '')]
                    active_assets = [a for a in fleet_data if a.get('status') == 'ACTIVE']
                    
                    self.log_automation_event('FLEET_CHECK', 'RAGLE fleet data validated', {
                        'total_assets': len(fleet_data),
                        'dfw_assets': len(dfw_assets),
                        'active_assets': len(active_assets)
                    })
                    return True
                else:
                    self.log_automation_event('WARNING', 'RAGLE fleet data empty or invalid')
                    return False
            else:
                self.log_automation_event('ERROR', f'RAGLE fleet API error: {response.status_code}')
                return False
                
        except Exception as e:
            self.log_automation_event('ERROR', f'RAGLE fleet validation failed: {str(e)}')
            return False
    
    def test_ai_capabilities(self):
        """Test AI integration capabilities"""
        try:
            # Test OpenAI integration
            test_data = {'query': 'System health check', 'provider': 'openai'}
            response = requests.post('http://localhost:5000/api/ai-query', 
                                   json=test_data, timeout=30)
            
            if response.status_code == 200:
                self.log_automation_event('AI_CHECK', 'OpenAI integration validated')
                
                # Test Perplexity integration
                test_data['provider'] = 'perplexity'
                response = requests.post('http://localhost:5000/api/ai-query', 
                                       json=test_data, timeout=30)
                
                if response.status_code == 200:
                    self.log_automation_event('AI_CHECK', 'Perplexity integration validated')
                    return True
                else:
                    self.log_automation_event('WARNING', 'Perplexity integration issue')
                    return False
            else:
                self.log_automation_event('WARNING', 'OpenAI integration issue')
                return False
                
        except Exception as e:
            self.log_automation_event('ERROR', f'AI capabilities test failed: {str(e)}')
            return False
    
    def automation_heartbeat(self):
        """Main automation heartbeat loop"""
        self.log_automation_event('STARTUP', 'DWC Evolution automation heartbeat started')
        
        while self.automation_active:
            try:
                # Get system health
                health_data = self.get_system_health_score()
                
                # Check for alerts
                alerts = self.check_and_respond_to_alerts(health_data)
                
                # Periodic validations (every 5 minutes)
                current_time = datetime.now()
                if current_time.minute % 5 == 0 and current_time.second < 30:
                    self.validate_ragle_fleet_connectivity()
                    
                # AI capability test (every 10 minutes)
                if current_time.minute % 10 == 0 and current_time.second < 30:
                    self.test_ai_capabilities()
                
                # Log healthy status
                if health_data['overall_score'] > 80:
                    self.log_automation_event('HEARTBEAT', f'System healthy - Score: {health_data["overall_score"]:.1f}%')
                else:
                    self.log_automation_event('WARNING', f'System degraded - Score: {health_data["overall_score"]:.1f}%')
                
                time.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self.log_automation_event('ERROR', f'Heartbeat error: {str(e)}')
                time.sleep(self.heartbeat_interval)
    
    def start_automation(self):
        """Start automation in background thread"""
        automation_thread = threading.Thread(target=self.automation_heartbeat, daemon=True)
        automation_thread.start()
        return automation_thread
    
    def stop_automation(self):
        """Stop automation system"""
        self.automation_active = False
        self.log_automation_event('SHUTDOWN', 'DWC Evolution automation stopped')
    
    def get_automation_status(self):
        """Get current automation status and recent logs"""
        return {
            'active': self.automation_active,
            'heartbeat_interval': self.heartbeat_interval,
            'last_optimization': self.last_optimization.isoformat() if self.last_optimization else None,
            'recent_logs': self.automation_log[-10:],  # Last 10 events
            'thresholds': self.alert_thresholds
        }

# Global automation instance
operator_console = OperatorConsoleAutomation()

def start_operator_console():
    """Initialize and start operator console automation"""
    return operator_console.start_automation()

def get_console_status():
    """Get operator console status"""
    return operator_console.get_automation_status()

def trigger_manual_optimization():
    """Manually trigger system optimization"""
    return operator_console.trigger_system_optimization()

if __name__ == '__main__':
    # Start automation for testing
    print("Starting DWC Evolution Operator Console...")
    thread = start_operator_console()
    
    try:
        # Run for 2 minutes for testing
        time.sleep(120)
        operator_console.stop_automation()
        print("Operator Console test completed")
    except KeyboardInterrupt:
        operator_console.stop_automation()
        print("Operator Console stopped by user")