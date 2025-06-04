"""
QQ One-Click Deployment Complexity Visualizer
Real-time deployment analysis and optimization visualization
"""

import os
import json
import time
import logging
import psutil
import subprocess
from typing import Dict, Any, List
from datetime import datetime
import sqlite3

class DeploymentComplexityAnalyzer:
    """Analyze and visualize deployment complexity in real-time"""
    
    def __init__(self):
        self.db_path = "qq_deployment_analysis.db"
        self.initialize_database()
        self.deployment_metrics = {}
        self.complexity_factors = {}
        
    def initialize_database(self):
        """Initialize deployment analysis database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deployment_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_count INTEGER,
                    total_size_mb REAL,
                    complexity_score REAL,
                    optimization_level REAL,
                    deployment_time_estimate INTEGER,
                    bundle_efficiency REAL,
                    analysis_data TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optimization_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    optimization_type TEXT,
                    before_size REAL,
                    after_size REAL,
                    performance_gain REAL,
                    status TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
    
    def analyze_project_complexity(self) -> Dict[str, Any]:
        """Analyze current project deployment complexity"""
        try:
            analysis = {
                'file_analysis': self._analyze_file_structure(),
                'dependency_analysis': self._analyze_dependencies(),
                'code_complexity': self._analyze_code_complexity(),
                'optimization_status': self._analyze_optimization_status(),
                'deployment_readiness': self._analyze_deployment_readiness(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Calculate overall complexity score
            complexity_score = self._calculate_complexity_score(analysis)
            analysis['complexity_score'] = complexity_score
            
            # Store analysis
            self._store_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            logging.error(f"Project complexity analysis error: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def _analyze_file_structure(self) -> Dict[str, Any]:
        """Analyze project file structure for deployment complexity"""
        try:
            file_metrics = {
                'python_files': 0,
                'template_files': 0,
                'static_files': 0,
                'config_files': 0,
                'total_size_mb': 0.0,
                'largest_files': []
            }
            
            # Analyze Python files
            for root, dirs, files in os.walk('.'):
                # Skip hidden directories and node_modules
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        file_metrics['total_size_mb'] += file_size / (1024 * 1024)
                        
                        if file.endswith('.py'):
                            file_metrics['python_files'] += 1
                        elif file.endswith('.html'):
                            file_metrics['template_files'] += 1
                        elif file.endswith(('.css', '.js', '.png', '.jpg', '.svg')):
                            file_metrics['static_files'] += 1
                        elif file.endswith(('.json', '.yaml', '.yml', '.toml')):
                            file_metrics['config_files'] += 1
                        
                        # Track largest files
                        if file_size > 100000:  # Files larger than 100KB
                            file_metrics['largest_files'].append({
                                'path': file_path,
                                'size_mb': file_size / (1024 * 1024),
                                'type': self._get_file_type(file)
                            })
                    except OSError:
                        continue
            
            # Sort largest files
            file_metrics['largest_files'].sort(key=lambda x: x['size_mb'], reverse=True)
            file_metrics['largest_files'] = file_metrics['largest_files'][:10]
            
            return file_metrics
            
        except Exception as e:
            logging.error(f"File structure analysis error: {e}")
            return {'error': str(e)}
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies"""
        try:
            dep_analysis = {
                'python_dependencies': 0,
                'heavy_dependencies': [],
                'optimization_candidates': [],
                'dependency_size_estimate': 0.0
            }
            
            # Analyze pyproject.toml
            if os.path.exists('pyproject.toml'):
                with open('pyproject.toml', 'r') as f:
                    content = f.read()
                    # Count dependencies (simple heuristic)
                    dep_analysis['python_dependencies'] = content.count('\n') - content.count('[')
            
            # Known heavy dependencies
            heavy_deps = [
                'tensorflow', 'torch', 'opencv-python', 'pandas', 'numpy',
                'matplotlib', 'plotly', 'scikit-learn', 'selenium', 'playwright'
            ]
            
            for dep in heavy_deps:
                if os.path.exists('pyproject.toml'):
                    with open('pyproject.toml', 'r') as f:
                        if dep in f.read():
                            dep_analysis['heavy_dependencies'].append(dep)
            
            # Estimate total dependency size
            dep_analysis['dependency_size_estimate'] = len(dep_analysis['heavy_dependencies']) * 50  # MB estimate
            
            return dep_analysis
            
        except Exception as e:
            logging.error(f"Dependency analysis error: {e}")
            return {'error': str(e)}
    
    def _analyze_code_complexity(self) -> Dict[str, Any]:
        """Analyze code complexity metrics"""
        try:
            complexity = {
                'total_lines': 0,
                'function_count': 0,
                'class_count': 0,
                'import_count': 0,
                'complexity_hotspots': []
            }
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                lines = content.split('\n')
                                complexity['total_lines'] += len(lines)
                                
                                # Count functions and classes
                                complexity['function_count'] += content.count('def ')
                                complexity['class_count'] += content.count('class ')
                                complexity['import_count'] += content.count('import ')
                                
                                # Identify complexity hotspots
                                if len(lines) > 500:  # Large files
                                    complexity['complexity_hotspots'].append({
                                        'file': file_path,
                                        'lines': len(lines),
                                        'functions': content.count('def '),
                                        'classes': content.count('class ')
                                    })
                        except (OSError, UnicodeDecodeError):
                            continue
            
            complexity['complexity_hotspots'].sort(key=lambda x: x['lines'], reverse=True)
            complexity['complexity_hotspots'] = complexity['complexity_hotspots'][:5]
            
            return complexity
            
        except Exception as e:
            logging.error(f"Code complexity analysis error: {e}")
            return {'error': str(e)}
    
    def _analyze_optimization_status(self) -> Dict[str, Any]:
        """Analyze current optimization status"""
        try:
            optimization = {
                'production_engine_active': False,
                'build_stabilization_active': False,
                'asi_excellence_active': False,
                'lazy_loading_enabled': False,
                'caching_enabled': False,
                'compression_enabled': False,
                'optimization_score': 0.0
            }
            
            # Check for optimization modules
            optimization_files = [
                'qq_production_optimization_engine.py',
                'qq_build_fix_module.py',
                'qq_asi_excellence_visual_fix.py'
            ]
            
            active_optimizations = 0
            for opt_file in optimization_files:
                if os.path.exists(opt_file):
                    active_optimizations += 1
                    if 'production' in opt_file:
                        optimization['production_engine_active'] = True
                    elif 'build_fix' in opt_file:
                        optimization['build_stabilization_active'] = True
                    elif 'asi' in opt_file:
                        optimization['asi_excellence_active'] = True
            
            optimization['optimization_score'] = (active_optimizations / len(optimization_files)) * 100
            
            # Check for additional optimizations in code
            try:
                with open('app_qq_enhanced.py', 'r') as f:
                    content = f.read()
                    if 'lazy_load' in content.lower():
                        optimization['lazy_loading_enabled'] = True
                    if 'cache' in content.lower():
                        optimization['caching_enabled'] = True
                    if 'compress' in content.lower():
                        optimization['compression_enabled'] = True
            except FileNotFoundError:
                pass
            
            return optimization
            
        except Exception as e:
            logging.error(f"Optimization status analysis error: {e}")
            return {'error': str(e)}
    
    def _analyze_deployment_readiness(self) -> Dict[str, Any]:
        """Analyze deployment readiness metrics"""
        try:
            readiness = {
                'estimated_bundle_size_mb': 0.0,
                'estimated_deployment_time_seconds': 0,
                'deployment_complexity': 'MEDIUM',
                'bottlenecks': [],
                'recommendations': []
            }
            
            # Calculate estimated bundle size
            file_analysis = self._analyze_file_structure()
            dep_analysis = self._analyze_dependencies()
            
            total_size = file_analysis.get('total_size_mb', 0) + dep_analysis.get('dependency_size_estimate', 0)
            readiness['estimated_bundle_size_mb'] = total_size
            
            # Estimate deployment time based on size and complexity
            base_time = 15  # Base deployment time
            size_factor = total_size * 0.5  # 0.5 seconds per MB
            complexity_factor = len(file_analysis.get('largest_files', [])) * 2
            
            readiness['estimated_deployment_time_seconds'] = int(base_time + size_factor + complexity_factor)
            
            # Determine complexity level
            if total_size < 50 and readiness['estimated_deployment_time_seconds'] < 30:
                readiness['deployment_complexity'] = 'LOW'
            elif total_size > 200 or readiness['estimated_deployment_time_seconds'] > 60:
                readiness['deployment_complexity'] = 'HIGH'
            else:
                readiness['deployment_complexity'] = 'MEDIUM'
            
            # Identify bottlenecks
            if total_size > 100:
                readiness['bottlenecks'].append('Large project size')
            if len(dep_analysis.get('heavy_dependencies', [])) > 3:
                readiness['bottlenecks'].append('Multiple heavy dependencies')
            if len(file_analysis.get('largest_files', [])) > 5:
                readiness['bottlenecks'].append('Large files present')
            
            # Generate recommendations
            optimization_status = self._analyze_optimization_status()
            if not optimization_status.get('production_engine_active'):
                readiness['recommendations'].append('Enable production optimization engine')
            if not optimization_status.get('caching_enabled'):
                readiness['recommendations'].append('Implement intelligent caching')
            if total_size > 50:
                readiness['recommendations'].append('Consider lazy loading for non-critical components')
            
            return readiness
            
        except Exception as e:
            logging.error(f"Deployment readiness analysis error: {e}")
            return {'error': str(e)}
    
    def _calculate_complexity_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall complexity score (0-100, lower is better)"""
        try:
            score = 0.0
            
            # File structure factor (0-30 points)
            file_analysis = analysis.get('file_analysis', {})
            total_size = file_analysis.get('total_size_mb', 0)
            if total_size > 100:
                score += 30
            elif total_size > 50:
                score += 20
            elif total_size > 20:
                score += 10
            
            # Dependency factor (0-25 points)
            dep_analysis = analysis.get('dependency_analysis', {})
            heavy_deps = len(dep_analysis.get('heavy_dependencies', []))
            score += min(heavy_deps * 5, 25)
            
            # Code complexity factor (0-25 points)
            code_analysis = analysis.get('code_complexity', {})
            total_lines = code_analysis.get('total_lines', 0)
            if total_lines > 10000:
                score += 25
            elif total_lines > 5000:
                score += 15
            elif total_lines > 2000:
                score += 10
            
            # Optimization factor (reduces score by 0-20 points)
            opt_analysis = analysis.get('optimization_status', {})
            opt_score = opt_analysis.get('optimization_score', 0)
            score -= (opt_score / 100) * 20
            
            return max(0, min(100, score))
            
        except Exception as e:
            logging.error(f"Complexity score calculation error: {e}")
            return 50.0  # Default medium complexity
    
    def _store_analysis(self, analysis: Dict[str, Any]):
        """Store analysis results in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            file_analysis = analysis.get('file_analysis', {})
            
            cursor.execute('''
                INSERT INTO deployment_analysis 
                (file_count, total_size_mb, complexity_score, optimization_level, 
                 deployment_time_estimate, bundle_efficiency, analysis_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_analysis.get('python_files', 0) + file_analysis.get('template_files', 0),
                file_analysis.get('total_size_mb', 0),
                analysis.get('complexity_score', 0),
                analysis.get('optimization_status', {}).get('optimization_score', 0),
                analysis.get('deployment_readiness', {}).get('estimated_deployment_time_seconds', 0),
                100 - analysis.get('complexity_score', 50),  # Efficiency inverse of complexity
                json.dumps(analysis)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Analysis storage error: {e}")
    
    def _get_file_type(self, filename: str) -> str:
        """Get file type category"""
        if filename.endswith('.py'):
            return 'Python'
        elif filename.endswith('.html'):
            return 'Template'
        elif filename.endswith('.css'):
            return 'Stylesheet'
        elif filename.endswith('.js'):
            return 'JavaScript'
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.svg')):
            return 'Image'
        else:
            return 'Other'
    
    def get_deployment_visualization_data(self) -> Dict[str, Any]:
        """Get data for deployment complexity visualization"""
        try:
            analysis = self.analyze_project_complexity()
            
            # Prepare visualization data
            viz_data = {
                'complexity_overview': {
                    'score': analysis.get('complexity_score', 50),
                    'level': self._get_complexity_level(analysis.get('complexity_score', 50)),
                    'deployment_time': analysis.get('deployment_readiness', {}).get('estimated_deployment_time_seconds', 30)
                },
                'file_breakdown': {
                    'python_files': analysis.get('file_analysis', {}).get('python_files', 0),
                    'template_files': analysis.get('file_analysis', {}).get('template_files', 0),
                    'static_files': analysis.get('file_analysis', {}).get('static_files', 0),
                    'total_size_mb': analysis.get('file_analysis', {}).get('total_size_mb', 0)
                },
                'optimization_status': analysis.get('optimization_status', {}),
                'bottlenecks': analysis.get('deployment_readiness', {}).get('bottlenecks', []),
                'recommendations': analysis.get('deployment_readiness', {}).get('recommendations', []),
                'largest_files': analysis.get('file_analysis', {}).get('largest_files', []),
                'heavy_dependencies': analysis.get('dependency_analysis', {}).get('heavy_dependencies', []),
                'timestamp': analysis.get('timestamp')
            }
            
            return viz_data
            
        except Exception as e:
            logging.error(f"Visualization data error: {e}")
            return {'error': str(e)}
    
    def _get_complexity_level(self, score: float) -> str:
        """Get complexity level description"""
        if score < 30:
            return 'LOW'
        elif score < 60:
            return 'MEDIUM'
        else:
            return 'HIGH'
    
    def get_historical_analysis(self) -> List[Dict[str, Any]]:
        """Get historical deployment analysis data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, complexity_score, deployment_time_estimate, 
                       bundle_efficiency, optimization_level
                FROM deployment_analysis 
                ORDER BY timestamp DESC 
                LIMIT 20
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            historical_data = []
            for row in results:
                historical_data.append({
                    'timestamp': row[0],
                    'complexity_score': row[1],
                    'deployment_time_estimate': row[2],
                    'bundle_efficiency': row[3],
                    'optimization_level': row[4]
                })
            
            return historical_data
            
        except Exception as e:
            logging.error(f"Historical analysis error: {e}")
            return []

# Global analyzer instance
_deployment_analyzer = None

def get_deployment_analyzer():
    """Get global deployment complexity analyzer instance"""
    global _deployment_analyzer
    if _deployment_analyzer is None:
        _deployment_analyzer = DeploymentComplexityAnalyzer()
    return _deployment_analyzer

def analyze_deployment_complexity():
    """Analyze current deployment complexity"""
    analyzer = get_deployment_analyzer()
    return analyzer.analyze_project_complexity()

def get_deployment_visualization_data():
    """Get deployment visualization data"""
    analyzer = get_deployment_analyzer()
    return analyzer.get_deployment_visualization_data()