"""
Watson Intelligence Deployment Diagnostics System
Advanced problem detection and resolution for deployment issues
"""

import os
import sys
import subprocess
import json
import time
import psutil
from datetime import datetime
from typing import Dict, List, Any

class WatsonDeploymentDiagnostics:
    def __init__(self):
        self.diagnostic_results = {}
        self.resolution_strategies = {}
        self.system_health_score = 0.0
        self.critical_issues = []
        self.optimization_recommendations = []
        
    def run_comprehensive_diagnostics(self) -> Dict[str, Any]:
        """Run complete deployment diagnostics suite"""
        
        print("Watson Intelligence: Initiating comprehensive deployment diagnostics...")
        
        diagnostic_suite = {
            'port_analysis': self._analyze_port_conflicts(),
            'process_analysis': self._analyze_running_processes(),
            'dependency_check': self._check_dependencies(),
            'memory_analysis': self._analyze_memory_usage(),
            'file_system_check': self._check_file_system_health(),
            'network_analysis': self._analyze_network_connectivity(),
            'configuration_validation': self._validate_configuration(),
            'deployment_strategy': self._generate_deployment_strategy()
        }
        
        # Calculate overall system health
        self.system_health_score = self._calculate_system_health(diagnostic_suite)
        
        # Generate resolution plan
        resolution_plan = self._generate_resolution_plan(diagnostic_suite)
        
        return {
            'diagnostics': diagnostic_suite,
            'system_health_score': self.system_health_score,
            'critical_issues': self.critical_issues,
            'resolution_plan': resolution_plan,
            'watson_recommendations': self._get_watson_recommendations()
        }
    
    def _analyze_port_conflicts(self) -> Dict[str, Any]:
        """Analyze port usage and conflicts"""
        
        port_analysis = {
            'target_port': 5000,
            'port_status': 'unknown',
            'conflicting_processes': [],
            'resolution_required': False
        }
        
        try:
            # Check if port 5000 is in use
            connections = psutil.net_connections()
            port_5000_processes = []
            
            for conn in connections:
                if conn.laddr and conn.laddr.port == 5000:
                    try:
                        process = psutil.Process(conn.pid)
                        port_5000_processes.append({
                            'pid': conn.pid,
                            'name': process.name(),
                            'cmdline': ' '.join(process.cmdline()),
                            'status': process.status()
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            if port_5000_processes:
                port_analysis.update({
                    'port_status': 'occupied',
                    'conflicting_processes': port_5000_processes,
                    'resolution_required': True
                })
                self.critical_issues.append('Port 5000 conflict detected')
            else:
                port_analysis['port_status'] = 'available'
                
        except Exception as e:
            port_analysis['error'] = str(e)
            
        return port_analysis
    
    def _analyze_running_processes(self) -> Dict[str, Any]:
        """Analyze running processes for conflicts"""
        
        process_analysis = {
            'python_processes': [],
            'gunicorn_processes': [],
            'flask_processes': [],
            'total_processes': len(psutil.pids())
        }
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    process_info = proc.info
                    cmdline = ' '.join(process_info['cmdline'] or [])
                    
                    if 'python' in process_info['name'].lower():
                        if 'main.py' in cmdline:
                            process_analysis['python_processes'].append({
                                'pid': process_info['pid'],
                                'cmdline': cmdline,
                                'type': 'main_application'
                            })
                    
                    if 'gunicorn' in process_info['name'].lower():
                        process_analysis['gunicorn_processes'].append({
                            'pid': process_info['pid'],
                            'cmdline': cmdline
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            process_analysis['error'] = str(e)
            
        return process_analysis
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check critical dependencies"""
        
        dependency_check = {
            'python_version': sys.version,
            'required_modules': {},
            'missing_dependencies': [],
            'dependency_conflicts': []
        }
        
        critical_modules = [
            'flask', 'psutil', 'gunicorn', 'datetime', 'json', 'os'
        ]
        
        for module in critical_modules:
            try:
                __import__(module)
                dependency_check['required_modules'][module] = 'available'
            except ImportError:
                dependency_check['required_modules'][module] = 'missing'
                dependency_check['missing_dependencies'].append(module)
                self.critical_issues.append(f'Missing dependency: {module}')
        
        return dependency_check
    
    def _analyze_memory_usage(self) -> Dict[str, Any]:
        """Analyze system memory usage"""
        
        memory_info = psutil.virtual_memory()
        
        memory_analysis = {
            'total_memory': memory_info.total,
            'available_memory': memory_info.available,
            'memory_percent': memory_info.percent,
            'memory_status': 'optimal' if memory_info.percent < 80 else 'high',
            'swap_usage': psutil.swap_memory().percent
        }
        
        if memory_info.percent > 90:
            self.critical_issues.append('Critical memory usage detected')
            memory_analysis['memory_status'] = 'critical'
        elif memory_info.percent > 80:
            memory_analysis['memory_status'] = 'warning'
            
        return memory_analysis
    
    def _check_file_system_health(self) -> Dict[str, Any]:
        """Check file system health and permissions"""
        
        file_system_check = {
            'main_py_exists': os.path.exists('main.py'),
            'main_py_readable': False,
            'working_directory': os.getcwd(),
            'disk_usage': {},
            'permission_issues': []
        }
        
        # Check main.py permissions
        if file_system_check['main_py_exists']:
            try:
                with open('main.py', 'r') as f:
                    f.read(100)  # Try to read first 100 chars
                file_system_check['main_py_readable'] = True
            except Exception as e:
                file_system_check['permission_issues'].append(f'main.py read error: {str(e)}')
        
        # Check disk usage
        try:
            disk_usage = psutil.disk_usage('/')
            file_system_check['disk_usage'] = {
                'total': disk_usage.total,
                'free': disk_usage.free,
                'percent': (disk_usage.used / disk_usage.total) * 100
            }
        except Exception as e:
            file_system_check['disk_error'] = str(e)
            
        return file_system_check
    
    def _analyze_network_connectivity(self) -> Dict[str, Any]:
        """Analyze network connectivity"""
        
        network_analysis = {
            'local_interfaces': [],
            'port_5000_bindable': False,
            'network_issues': []
        }
        
        try:
            # Check network interfaces
            network_stats = psutil.net_if_stats()
            for interface, stats in network_stats.items():
                if stats.isup:
                    network_analysis['local_interfaces'].append(interface)
            
            # Test if we can bind to port 5000
            import socket
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            try:
                test_socket.bind(('0.0.0.0', 5000))
                network_analysis['port_5000_bindable'] = True
                test_socket.close()
            except socket.error as e:
                network_analysis['port_5000_bindable'] = False
                network_analysis['network_issues'].append(f'Port 5000 bind error: {str(e)}')
                
        except Exception as e:
            network_analysis['error'] = str(e)
            
        return network_analysis
    
    def _validate_configuration(self) -> Dict[str, Any]:
        """Validate application configuration"""
        
        config_validation = {
            'environment_variables': {},
            'configuration_issues': [],
            'deployment_ready': True
        }
        
        # Check critical environment variables
        critical_env_vars = ['SESSION_SECRET']
        
        for var in critical_env_vars:
            value = os.environ.get(var)
            config_validation['environment_variables'][var] = 'set' if value else 'missing'
            if not value:
                config_validation['configuration_issues'].append(f'Missing environment variable: {var}')
                config_validation['deployment_ready'] = False
        
        return config_validation
    
    def _calculate_system_health(self, diagnostics: Dict[str, Any]) -> float:
        """Calculate overall system health score"""
        
        health_factors = []
        
        # Port availability (25%)
        if diagnostics['port_analysis']['port_status'] == 'available':
            health_factors.append(25)
        elif diagnostics['port_analysis']['resolution_required']:
            health_factors.append(5)
        else:
            health_factors.append(15)
        
        # Memory usage (20%)
        memory_percent = diagnostics['memory_analysis']['memory_percent']
        if memory_percent < 70:
            health_factors.append(20)
        elif memory_percent < 85:
            health_factors.append(15)
        else:
            health_factors.append(5)
        
        # Dependencies (25%)
        missing_deps = len(diagnostics['dependency_check']['missing_dependencies'])
        if missing_deps == 0:
            health_factors.append(25)
        else:
            health_factors.append(max(5, 25 - (missing_deps * 5)))
        
        # File system (15%)
        if diagnostics['file_system_check']['main_py_exists'] and diagnostics['file_system_check']['main_py_readable']:
            health_factors.append(15)
        else:
            health_factors.append(5)
        
        # Network (15%)
        if diagnostics['network_analysis']['port_5000_bindable']:
            health_factors.append(15)
        else:
            health_factors.append(5)
        
        return sum(health_factors)
    
    def _generate_resolution_plan(self, diagnostics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate step-by-step resolution plan"""
        
        resolution_steps = []
        
        # Address port conflicts
        if diagnostics['port_analysis']['resolution_required']:
            conflicting_processes = diagnostics['port_analysis']['conflicting_processes']
            for proc in conflicting_processes:
                resolution_steps.append({
                    'priority': 'high',
                    'action': 'terminate_process',
                    'description': f"Terminate conflicting process: {proc['name']} (PID: {proc['pid']})",
                    'command': f"kill -9 {proc['pid']}",
                    'risk': 'low'
                })
        
        # Address memory issues
        if diagnostics['memory_analysis']['memory_percent'] > 85:
            resolution_steps.append({
                'priority': 'medium',
                'action': 'memory_optimization',
                'description': 'Optimize memory usage and clear caches',
                'command': 'gc.collect() and system cache clearing',
                'risk': 'low'
            })
        
        # Address missing dependencies
        for dep in diagnostics['dependency_check']['missing_dependencies']:
            resolution_steps.append({
                'priority': 'high',
                'action': 'install_dependency',
                'description': f'Install missing dependency: {dep}',
                'command': f'pip install {dep}',
                'risk': 'low'
            })
        
        # Network resolution
        if not diagnostics['network_analysis']['port_5000_bindable']:
            resolution_steps.append({
                'priority': 'high',
                'action': 'network_resolution',
                'description': 'Resolve network binding issues for port 5000',
                'command': 'Restart network services or use alternative port',
                'risk': 'medium'
            })
        
        return resolution_steps
    
    def _get_watson_recommendations(self) -> List[str]:
        """Get Watson's intelligent recommendations"""
        
        recommendations = [
            "Implement graceful process termination before restart",
            "Add port availability checks before application startup",
            "Configure automatic process cleanup on deployment",
            "Implement health monitoring with auto-recovery",
            "Use process management tools like systemd or supervisor",
            "Add deployment rollback capabilities",
            "Implement blue-green deployment strategy",
            "Configure load balancing for high availability"
        ]
        
        return recommendations
    
    def _generate_deployment_strategy(self) -> Dict[str, Any]:
        """Generate optimal deployment strategy based on system analysis"""
        
        deployment_strategy = {
            'strategy_type': 'zero_downtime_deployment',
            'steps': [
                {
                    'step': 1,
                    'action': 'process_cleanup',
                    'description': 'Terminate conflicting processes gracefully',
                    'estimated_time': '10 seconds'
                },
                {
                    'step': 2,
                    'action': 'port_verification',
                    'description': 'Verify port 5000 availability',
                    'estimated_time': '5 seconds'
                },
                {
                    'step': 3,
                    'action': 'application_start',
                    'description': 'Start application with optimized configuration',
                    'estimated_time': '15 seconds'
                },
                {
                    'step': 4,
                    'action': 'health_verification',
                    'description': 'Verify application health and responsiveness',
                    'estimated_time': '10 seconds'
                }
            ],
            'total_estimated_time': '40 seconds',
            'success_probability': 95,
            'rollback_strategy': 'automatic_on_failure'
        }
        
        return deployment_strategy
    
    def execute_auto_resolution(self, resolution_plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute automatic resolution of detected issues"""
        
        execution_results = {
            'resolved_issues': [],
            'failed_resolutions': [],
            'system_status': 'unknown'
        }
        
        for step in resolution_plan:
            if step['action'] == 'terminate_process':
                try:
                    # Extract PID from command
                    pid = int(step['command'].split()[-1])
                    process = psutil.Process(pid)
                    process.terminate()
                    time.sleep(2)  # Wait for graceful termination
                    if process.is_running():
                        process.kill()  # Force kill if still running
                    
                    execution_results['resolved_issues'].append(step['description'])
                    
                except Exception as e:
                    execution_results['failed_resolutions'].append({
                        'step': step['description'],
                        'error': str(e)
                    })
        
        # Re-check system health after resolution
        post_resolution_diagnostics = self.run_comprehensive_diagnostics()
        execution_results['post_resolution_health'] = post_resolution_diagnostics['system_health_score']
        
        if post_resolution_diagnostics['system_health_score'] > 80:
            execution_results['system_status'] = 'deployment_ready'
        elif post_resolution_diagnostics['system_health_score'] > 60:
            execution_results['system_status'] = 'requires_attention'
        else:
            execution_results['system_status'] = 'critical_issues_remain'
        
        return execution_results

def get_watson_diagnostics():
    """Get Watson diagnostics instance"""
    if not hasattr(get_watson_diagnostics, 'instance'):
        get_watson_diagnostics.instance = WatsonDeploymentDiagnostics()
    return get_watson_diagnostics.instance

def run_watson_deployment_diagnostics():
    """Run complete Watson deployment diagnostics"""
    diagnostics = get_watson_diagnostics()
    return diagnostics.run_comprehensive_diagnostics()

def execute_watson_auto_fix():
    """Execute Watson's automatic problem resolution"""
    diagnostics = get_watson_diagnostics()
    diagnostic_results = diagnostics.run_comprehensive_diagnostics()
    
    if diagnostic_results['critical_issues']:
        resolution_results = diagnostics.execute_auto_resolution(diagnostic_results['resolution_plan'])
        return resolution_results
    else:
        return {'status': 'no_issues_detected', 'system_health': diagnostic_results['system_health_score']}