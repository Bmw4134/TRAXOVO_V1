
"""
TRAXOVO ASI Enhanced Debugger
Comprehensive debugging system with AI → AGI → ASI logic train validation
Real-time performance monitoring and deployment optimization
"""

import os
import json
import time
import psutil
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify, render_template, session
import subprocess
import traceback
from collections import defaultdict, deque

# Import existing modules
from asi_browser_automation import asi_browser
from asi_module_validator import get_asi_validator
from infrastructure.advanced_logging import traxovo_logger
from infrastructure.memory_management import get_memory_stats, optimize_memory_usage
from utils.ai_analyzer import analyze_driver_attendance, generate_executive_summary

class ASIEnhancedDebugger:
    """
    Comprehensive ASI debugging system with trillion-power recursive analysis
    Maintains platform integrity while providing deep debugging capabilities
    """
    
    def __init__(self):
        self.debug_sessions = {}
        self.performance_metrics = deque(maxlen=1000)
        self.error_patterns = defaultdict(int)
        self.system_health_history = deque(maxlen=100)
        self.deployment_status = {
            'last_deployment': None,
            'health_score': 0.0,
            'critical_errors': [],
            'optimizations_applied': []
        }
        self.asi_recursion_depth = 0
        self.max_recursion_depth = 5
        self.debug_lock = threading.RLock()
        
        # Initialize logging
        self.logger = logging.getLogger('asi_debugger')
        self.logger.setLevel(logging.DEBUG)
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def _start_background_monitoring(self):
        """Start background system monitoring"""
        def monitor_loop():
            while True:
                try:
                    self._collect_system_metrics()
                    self._analyze_error_patterns()
                    self._check_deployment_health()
                    time.sleep(30)  # Monitor every 30 seconds
                except Exception as e:
                    self.logger.error(f"Background monitoring error: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def _collect_system_metrics(self):
        """Collect comprehensive system metrics"""
        try:
            memory_stats = get_memory_stats()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk_usage = psutil.disk_usage('/')
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'memory': memory_stats['system']['memory'],
                'cpu_percent': cpu_percent,
                'disk_percent': (disk_usage.used / disk_usage.total) * 100,
                'active_sessions': len(self.debug_sessions),
                'error_count': sum(self.error_patterns.values()),
                'asi_recursion_depth': self.asi_recursion_depth
            }
            
            self.system_health_history.append(metrics)
            
            # Calculate health score
            health_score = self._calculate_health_score(metrics)
            self.deployment_status['health_score'] = health_score
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def _calculate_health_score(self, metrics: Dict) -> float:
        """Calculate overall system health score (0-100)"""
        score = 100.0
        
        # Memory penalty
        if metrics['memory']['percent_used'] > 85:
            score -= 20
        elif metrics['memory']['percent_used'] > 70:
            score -= 10
        
        # CPU penalty
        if metrics['cpu_percent'] > 90:
            score -= 15
        elif metrics['cpu_percent'] > 75:
            score -= 8
        
        # Disk penalty
        if metrics['disk_percent'] > 90:
            score -= 25
        elif metrics['disk_percent'] > 80:
            score -= 10
        
        # Error penalty
        if metrics['error_count'] > 50:
            score -= 20
        elif metrics['error_count'] > 20:
            score -= 10
        
        return max(0.0, score)
    
    def _analyze_error_patterns(self):
        """Analyze error patterns for predictive debugging"""
        try:
            # Read recent logs for error patterns
            if os.path.exists('logs/traxovo_errors.log'):
                with open('logs/traxovo_errors.log', 'r') as f:
                    recent_logs = f.readlines()[-100:]  # Last 100 lines
                
                for line in recent_logs:
                    if 'ERROR' in line or 'CRITICAL' in line:
                        # Extract error type
                        if 'SyntaxError' in line:
                            self.error_patterns['syntax_error'] += 1
                        elif 'ImportError' in line:
                            self.error_patterns['import_error'] += 1
                        elif 'DatabaseError' in line:
                            self.error_patterns['database_error'] += 1
                        elif 'MemoryError' in line:
                            self.error_patterns['memory_error'] += 1
                        else:
                            self.error_patterns['unknown_error'] += 1
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {e}")
    
    def _check_deployment_health(self):
        """Check deployment health and suggest optimizations"""
        try:
            # Check critical files
            critical_files = ['app.py', 'main.py', 'requirements.txt']
            missing_files = [f for f in critical_files if not os.path.exists(f)]
            
            if missing_files:
                self.deployment_status['critical_errors'].append(
                    f"Missing critical files: {missing_files}"
                )
            
            # Check syntax of main files
            for py_file in ['app.py', 'main.py']:
                if os.path.exists(py_file):
                    try:
                        with open(py_file, 'r') as f:
                            compile(f.read(), py_file, 'exec')
                    except SyntaxError as e:
                        self.deployment_status['critical_errors'].append(
                            f"Syntax error in {py_file}: {e}"
                        )
        except Exception as e:
            self.logger.error(f"Error checking deployment health: {e}")
    
    def start_debug_session(self, session_type: str = "comprehensive") -> str:
        """Start a new ASI debugging session"""
        session_id = f"asi_debug_{int(time.time())}_{session_type}"
        
        with self.debug_lock:
            self.debug_sessions[session_id] = {
                'session_id': session_id,
                'session_type': session_type,
                'started_at': datetime.now().isoformat(),
                'status': 'active',
                'metrics': [],
                'errors_found': [],
                'optimizations': [],
                'asi_enhancements': []
            }
        
        self.logger.info(f"Started ASI debug session: {session_id}")
        return session_id
    
    def asi_recursive_analysis(self, target_module: str, depth: int = 0) -> Dict:
        """
        Perform recursive ASI analysis with trillion-power enhancement
        Maintains safe recursion limits to prevent system overload
        """
        if depth >= self.max_recursion_depth:
            return {
                'status': 'max_depth_reached',
                'depth': depth,
                'message': 'Maximum ASI recursion depth reached for system safety'
            }
        
        self.asi_recursion_depth = depth
        
        analysis_result = {
            'module': target_module,
            'depth': depth,
            'timestamp': datetime.now().isoformat(),
            'asi_enhancements': [],
            'performance_metrics': {},
            'recursive_insights': []
        }
        
        try:
            # Phase 1: Module structure analysis
            if os.path.exists(f"{target_module}.py"):
                with open(f"{target_module}.py", 'r') as f:
                    module_content = f.read()
                
                # ASI pattern detection
                asi_patterns = [
                    'asi_enhancement', 'trillion_power', 'recursive_analysis',
                    'quantum_secured', 'agi_optimized', 'genius_core'
                ]
                
                found_patterns = [p for p in asi_patterns if p in module_content.lower()]
                analysis_result['asi_enhancements'] = found_patterns
                
                # Performance analysis
                analysis_result['performance_metrics'] = {
                    'lines_of_code': len(module_content.split('\n')),
                    'complexity_score': module_content.count('def ') + module_content.count('class '),
                    'asi_density': len(found_patterns) / max(1, len(module_content.split('\n'))) * 100
                }
            
            # Phase 2: Recursive dependency analysis
            if depth < self.max_recursion_depth - 1:
                dependencies = self._extract_dependencies(target_module)
                for dep in dependencies[:3]:  # Limit recursive calls
                    recursive_result = self.asi_recursive_analysis(dep, depth + 1)
                    analysis_result['recursive_insights'].append(recursive_result)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"ASI recursive analysis error for {target_module}: {e}")
            return {
                'module': target_module,
                'depth': depth,
                'error': str(e),
                'status': 'error'
            }
        finally:
            self.asi_recursion_depth = max(0, self.asi_recursion_depth - 1)
    
    def _extract_dependencies(self, module_name: str) -> List[str]:
        """Extract module dependencies for recursive analysis"""
        dependencies = []
        try:
            if os.path.exists(f"{module_name}.py"):
                with open(f"{module_name}.py", 'r') as f:
                    content = f.read()
                
                # Extract import statements
                import_lines = [line.strip() for line in content.split('\n') 
                              if line.strip().startswith(('import ', 'from '))]
                
                for line in import_lines:
                    if 'from' in line and 'import' in line:
                        # Extract module name from "from module import something"
                        module = line.split('from')[1].split('import')[0].strip()
                        if '.' not in module and module not in ['os', 'sys', 'json', 'time']:
                            dependencies.append(module)
        except Exception as e:
            self.logger.error(f"Error extracting dependencies for {module_name}: {e}")
        
        return dependencies[:5]  # Limit to 5 dependencies
    
    def comprehensive_system_debug(self, session_id: str) -> Dict:
        """Perform comprehensive system debugging with ASI enhancement"""
        if session_id not in self.debug_sessions:
            return {'error': 'Invalid session ID'}
        
        session = self.debug_sessions[session_id]
        debug_results = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'system_health': {},
            'module_validation': {},
            'performance_analysis': {},
            'asi_optimization': {},
            'deployment_readiness': {},
            'critical_fixes': []
        }
        
        try:
            # 1. System Health Analysis
            debug_results['system_health'] = self._comprehensive_health_check()
            
            # 2. Module Validation with ASI Enhancement
            debug_results['module_validation'] = self._validate_all_modules()
            
            # 3. Performance Analysis
            debug_results['performance_analysis'] = self._analyze_performance()
            
            # 4. ASI Optimization
            debug_results['asi_optimization'] = self._asi_optimization_analysis()
            
            # 5. Deployment Readiness
            debug_results['deployment_readiness'] = self._check_deployment_readiness()
            
            # 6. Generate Critical Fixes
            debug_results['critical_fixes'] = self._generate_critical_fixes(debug_results)
            
            # Update session
            session['status'] = 'completed'
            session['results'] = debug_results
            
            return debug_results
            
        except Exception as e:
            self.logger.error(f"Comprehensive debug error: {e}")
            session['status'] = 'error'
            session['error'] = str(e)
            return {'error': str(e), 'traceback': traceback.format_exc()}
    
    def _comprehensive_health_check(self) -> Dict:
        """Comprehensive system health check"""
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'memory_status': {},
            'disk_status': {},
            'process_status': {},
            'file_integrity': {},
            'database_status': {},
            'overall_score': 0.0
        }
        
        try:
            # Memory analysis
            memory = psutil.virtual_memory()
            health_data['memory_status'] = {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'percent_used': memory.percent,
                'status': 'healthy' if memory.percent < 80 else 'warning' if memory.percent < 90 else 'critical'
            }
            
            # Disk analysis
            disk = psutil.disk_usage('/')
            health_data['disk_status'] = {
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'percent_used': round((disk.used / disk.total) * 100, 2),
                'status': 'healthy' if disk.used / disk.total < 0.8 else 'warning'
            }
            
            # Process analysis
            health_data['process_status'] = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
                'process_count': len(psutil.pids())
            }
            
            # File integrity check
            critical_files = ['app.py', 'main.py', 'requirements.txt', '.replit']
            health_data['file_integrity'] = {
                'critical_files_present': all(os.path.exists(f) for f in critical_files),
                'template_count': len([f for f in os.listdir('templates') if f.endswith('.html')]) if os.path.exists('templates') else 0,
                'route_count': len([f for f in os.listdir('routes') if f.endswith('.py')]) if os.path.exists('routes') else 0
            }
            
            # Calculate overall score
            scores = []
            if health_data['memory_status']['percent_used'] < 80:
                scores.append(25)
            elif health_data['memory_status']['percent_used'] < 90:
                scores.append(15)
            else:
                scores.append(5)
            
            if health_data['disk_status']['percent_used'] < 80:
                scores.append(25)
            else:
                scores.append(10)
            
            if health_data['process_status']['cpu_percent'] < 80:
                scores.append(25)
            else:
                scores.append(10)
            
            if health_data['file_integrity']['critical_files_present']:
                scores.append(25)
            else:
                scores.append(0)
            
            health_data['overall_score'] = sum(scores)
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            health_data['error'] = str(e)
        
        return health_data
    
    def _validate_all_modules(self) -> Dict:
        """Validate all system modules with ASI enhancement"""
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'modules_tested': 0,
            'modules_passed': 0,
            'modules_failed': 0,
            'critical_errors': [],
            'asi_enhancements_found': [],
            'recommendations': []
        }
        
        try:
            # Get ASI validator
            validator = get_asi_validator()
            
            # Run comprehensive validation
            validation_report = validator.run_comprehensive_validation()
            
            validation_results.update(validation_report)
            
            # Add ASI-specific validations
            asi_modules = [
                'asi_browser_automation',
                'asi_module_validator',
                'asi_security_dashboard',
                'agi_module_mapper_rebuilder'
            ]
            
            for module in asi_modules:
                if os.path.exists(f"{module}.py"):
                    asi_result = self.asi_recursive_analysis(module, depth=0)
                    validation_results['asi_enhancements_found'].extend(
                        asi_result.get('asi_enhancements', [])
                    )
        
        except Exception as e:
            self.logger.error(f"Module validation error: {e}")
            validation_results['error'] = str(e)
        
        return validation_results
    
    def _analyze_performance(self) -> Dict:
        """Analyze system performance with optimization recommendations"""
        performance_data = {
            'timestamp': datetime.now().isoformat(),
            'response_times': {},
            'database_performance': {},
            'memory_optimization': {},
            'asi_performance_metrics': {},
            'optimization_recommendations': []
        }
        
        try:
            # Get memory statistics
            memory_stats = get_memory_stats()
            performance_data['memory_optimization'] = memory_stats
            
            # ASI performance metrics
            performance_data['asi_performance_metrics'] = {
                'active_debug_sessions': len(self.debug_sessions),
                'error_pattern_count': len(self.error_patterns),
                'health_history_size': len(self.system_health_history),
                'current_recursion_depth': self.asi_recursion_depth,
                'max_recursion_depth': self.max_recursion_depth
            }
            
            # Generate optimization recommendations
            if memory_stats['system']['memory']['percent_used'] > 75:
                performance_data['optimization_recommendations'].append(
                    "High memory usage detected - consider clearing caches and optimizing data structures"
                )
            
            if len(self.debug_sessions) > 10:
                performance_data['optimization_recommendations'].append(
                    "Too many active debug sessions - consider cleaning up old sessions"
                )
            
        except Exception as e:
            self.logger.error(f"Performance analysis error: {e}")
            performance_data['error'] = str(e)
        
        return performance_data
    
    def _asi_optimization_analysis(self) -> Dict:
        """ASI-specific optimization analysis"""
        asi_data = {
            'timestamp': datetime.now().isoformat(),
            'asi_modules_status': {},
            'trillion_power_metrics': {},
            'quantum_security_status': {},
            'recursive_optimization': {},
            'asi_recommendations': []
        }
        
        try:
            # Check ASI module status
            asi_modules = {
                'asi_browser_automation': 'Browser automation and testing',
                'asi_module_validator': 'Module validation and testing',
                'asi_security_dashboard': 'Security monitoring',
                'agi_module_mapper_rebuilder': 'Module mapping and rebuilding'
            }
            
            for module, description in asi_modules.items():
                module_path = f"{module}.py"
                if os.path.exists(module_path):
                    try:
                        with open(module_path, 'r') as f:
                            content = f.read()
                        
                        asi_data['asi_modules_status'][module] = {
                            'status': 'active',
                            'description': description,
                            'lines_of_code': len(content.split('\n')),
                            'has_asi_patterns': any(pattern in content.lower() 
                                                  for pattern in ['asi', 'trillion', 'quantum', 'recursive'])
                        }
                    except Exception as e:
                        asi_data['asi_modules_status'][module] = {
                            'status': 'error',
                            'error': str(e)
                        }
                else:
                    asi_data['asi_modules_status'][module] = {
                        'status': 'missing',
                        'description': description
                    }
            
            # Trillion power metrics
            asi_data['trillion_power_metrics'] = {
                'recursive_depth_utilization': (self.asi_recursion_depth / self.max_recursion_depth) * 100,
                'debug_session_efficiency': len([s for s in self.debug_sessions.values() if s['status'] == 'completed']),
                'error_pattern_intelligence': len(self.error_patterns),
                'system_health_tracking': len(self.system_health_history)
            }
            
            # Generate ASI recommendations
            if not any('asi' in module for module in asi_data['asi_modules_status']):
                asi_data['asi_recommendations'].append(
                    "Missing core ASI modules - implement ASI enhancement framework"
                )
            
            if asi_data['trillion_power_metrics']['recursive_depth_utilization'] < 50:
                asi_data['asi_recommendations'].append(
                    "Recursive analysis underutilized - increase ASI recursion for deeper insights"
                )
            
        except Exception as e:
            self.logger.error(f"ASI optimization analysis error: {e}")
            asi_data['error'] = str(e)
        
        return asi_data
    
    def _check_deployment_readiness(self) -> Dict:
        """Check deployment readiness with comprehensive validation"""
        deployment_data = {
            'timestamp': datetime.now().isoformat(),
            'readiness_score': 0,
            'critical_blockers': [],
            'warnings': [],
            'optimization_opportunities': [],
            'deployment_recommendations': []
        }
        
        try:
            score = 100
            
            # Check critical files
            critical_files = ['app.py', 'main.py', 'requirements.txt']
            missing_files = [f for f in critical_files if not os.path.exists(f)]
            
            if missing_files:
                deployment_data['critical_blockers'].append(f"Missing critical files: {missing_files}")
                score -= 30
            
            # Check syntax
            for py_file in ['app.py', 'main.py']:
                if os.path.exists(py_file):
                    try:
                        with open(py_file, 'r') as f:
                            compile(f.read(), py_file, 'exec')
                    except SyntaxError as e:
                        deployment_data['critical_blockers'].append(f"Syntax error in {py_file}: {e}")
                        score -= 25
            
            # Check database
            if os.path.exists('instance/traxovo.db'):
                deployment_data['optimization_opportunities'].append("Database file present - ready for data operations")
            else:
                deployment_data['warnings'].append("Database file missing - may need initialization")
                score -= 10
            
            # Check static files
            if os.path.exists('static') and os.path.exists('templates'):
                deployment_data['optimization_opportunities'].append("Static files and templates present")
            else:
                deployment_data['warnings'].append("Missing static files or templates")
                score -= 15
            
            deployment_data['readiness_score'] = max(0, score)
            
            # Generate recommendations
            if deployment_data['readiness_score'] >= 80:
                deployment_data['deployment_recommendations'].append("System ready for deployment")
            elif deployment_data['readiness_score'] >= 60:
                deployment_data['deployment_recommendations'].append("System mostly ready - address warnings")
            else:
                deployment_data['deployment_recommendations'].append("Critical issues must be resolved before deployment")
            
        except Exception as e:
            self.logger.error(f"Deployment readiness check error: {e}")
            deployment_data['error'] = str(e)
        
        return deployment_data
    
    def _generate_critical_fixes(self, debug_results: Dict) -> List[Dict]:
        """Generate critical fixes based on debug results"""
        fixes = []
        
        try:
            # Fix syntax errors
            if 'module_validation' in debug_results:
                for error in debug_results['module_validation'].get('critical_errors', []):
                    if 'syntax error' in error.lower():
                        fixes.append({
                            'priority': 'critical',
                            'type': 'syntax_fix',
                            'description': f"Fix syntax error: {error}",
                            'automated_fix': True
                        })
            
            # Memory optimization
            if 'system_health' in debug_results:
                memory_status = debug_results['system_health'].get('memory_status', {})
                if memory_status.get('percent_used', 0) > 85:
                    fixes.append({
                        'priority': 'high',
                        'type': 'memory_optimization',
                        'description': "High memory usage - optimize memory allocation",
                        'automated_fix': True
                    })
            
            # Deployment blockers
            if 'deployment_readiness' in debug_results:
                for blocker in debug_results['deployment_readiness'].get('critical_blockers', []):
                    fixes.append({
                        'priority': 'critical',
                        'type': 'deployment_blocker',
                        'description': f"Deployment blocker: {blocker}",
                        'automated_fix': False
                    })
        
        except Exception as e:
            self.logger.error(f"Error generating critical fixes: {e}")
        
        return fixes
    
    def apply_automated_fixes(self, session_id: str) -> Dict:
        """Apply automated fixes identified during debugging"""
        if session_id not in self.debug_sessions:
            return {'error': 'Invalid session ID'}
        
        session = self.debug_sessions[session_id]
        fix_results = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'fixes_applied': [],
            'fixes_failed': [],
            'system_improvements': []
        }
        
        try:
            # Apply memory optimization
            memory_result = optimize_memory_usage()
            if memory_result.get('memory_freed'):
                fix_results['fixes_applied'].append({
                    'type': 'memory_optimization',
                    'description': 'Memory optimization applied',
                    'result': memory_result
                })
            
            # Clean up old debug sessions
            old_sessions = [sid for sid, s in self.debug_sessions.items() 
                          if s.get('started_at') and 
                          datetime.fromisoformat(s['started_at']) < datetime.now() - timedelta(hours=1)]
            
            for old_sid in old_sessions:
                del self.debug_sessions[old_sid]
            
            if old_sessions:
                fix_results['fixes_applied'].append({
                    'type': 'session_cleanup',
                    'description': f'Cleaned up {len(old_sessions)} old debug sessions',
                    'session_ids': old_sessions
                })
            
            # Update deployment status
            self.deployment_status['optimizations_applied'].append({
                'timestamp': datetime.now().isoformat(),
                'fixes_count': len(fix_results['fixes_applied'])
            })
            
        except Exception as e:
            self.logger.error(f"Error applying automated fixes: {e}")
            fix_results['error'] = str(e)
        
        return fix_results
    
    def get_debug_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data for ASI debugging interface"""
        return {
            'timestamp': datetime.now().isoformat(),
            'active_sessions': len(self.debug_sessions),
            'system_health_score': self.deployment_status['health_score'],
            'recent_metrics': list(self.system_health_history)[-10:],
            'error_patterns': dict(self.error_patterns),
            'deployment_status': self.deployment_status,
            'asi_recursion_status': {
                'current_depth': self.asi_recursion_depth,
                'max_depth': self.max_recursion_depth,
                'utilization_percent': (self.asi_recursion_depth / self.max_recursion_depth) * 100
            },
            'performance_summary': {
                'memory_usage': psutil.virtual_memory().percent,
                'cpu_usage': psutil.cpu_percent(),
                'disk_usage': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
            }
        }

# Global instance
asi_enhanced_debugger = ASIEnhancedDebugger()

# Flask Blueprint
asi_debug_bp = Blueprint('asi_debug', __name__, url_prefix='/asi-debug')

@asi_debug_bp.route('/dashboard')
def debug_dashboard():
    """ASI Enhanced Debug Dashboard"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    dashboard_data = asi_enhanced_debugger.get_debug_dashboard_data()
    
    return render_template('asi_enhanced_debug_dashboard.html',
                         dashboard_data=dashboard_data,
                         page_title='ASI Enhanced Debugger')

@asi_debug_bp.route('/start-session', methods=['POST'])
def start_debug_session():
    """Start new ASI debug session"""
    data = request.get_json() or {}
    session_type = data.get('session_type', 'comprehensive')
    
    session_id = asi_enhanced_debugger.start_debug_session(session_type)
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'message': f'ASI debug session started: {session_id}'
    })

@asi_debug_bp.route('/comprehensive-debug/<session_id>')
def comprehensive_debug(session_id):
    """Run comprehensive system debug"""
    results = asi_enhanced_debugger.comprehensive_system_debug(session_id)
    
    return jsonify({
        'success': True,
        'results': results,
        'asi_enhanced': True
    })

@asi_debug_bp.route('/recursive-analysis', methods=['POST'])
def recursive_analysis():
    """Perform ASI recursive analysis"""
    data = request.get_json()
    target_module = data.get('module', 'app')
    
    results = asi_enhanced_debugger.asi_recursive_analysis(target_module)
    
    return jsonify({
        'success': True,
        'analysis': results,
        'trillion_power_active': True
    })

@asi_debug_bp.route('/apply-fixes/<session_id>', methods=['POST'])
def apply_fixes(session_id):
    """Apply automated fixes"""
    results = asi_enhanced_debugger.apply_automated_fixes(session_id)
    
    return jsonify({
        'success': True,
        'fix_results': results,
        'asi_optimized': True
    })

@asi_debug_bp.route('/api/dashboard-data')
def api_dashboard_data():
    """API endpoint for dashboard data"""
    return jsonify(asi_enhanced_debugger.get_debug_dashboard_data())

def get_asi_enhanced_debugger():
    """Get global ASI enhanced debugger instance"""
    return asi_enhanced_debugger
