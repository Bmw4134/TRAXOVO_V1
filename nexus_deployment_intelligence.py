"""
NEXUS Deployment Intelligence
Analyzing deployment bottlenecks and brain connection issues
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple

class NexusDeploymentIntelligence:
    """Intelligence analysis for deployment optimization and brain connectivity"""
    
    def __init__(self):
        self.project_root = Path('.')
        self.analysis_results = {}
        
    def analyze_deployment_bottlenecks(self) -> Dict[str, Any]:
        """Comprehensive analysis of deployment issues"""
        
        # 1. File size analysis
        file_analysis = self._analyze_file_sizes()
        
        # 2. Repository structure analysis
        repo_analysis = self._analyze_repository_structure()
        
        # 3. Hidden function analysis
        hidden_functions = self._identify_hidden_functions()
        
        # 4. Brain connection analysis
        brain_connectivity = self._analyze_brain_connectivity()
        
        # 5. Deployment optimization recommendations
        optimization_plan = self._generate_optimization_plan(
            file_analysis, repo_analysis, hidden_functions, brain_connectivity
        )
        
        return {
            'file_size_analysis': file_analysis,
            'repository_analysis': repo_analysis,
            'hidden_functions': hidden_functions,
            'brain_connectivity': brain_connectivity,
            'optimization_plan': optimization_plan,
            'deployment_status': self._assess_deployment_readiness()
        }
    
    def _analyze_file_sizes(self) -> Dict[str, Any]:
        """Analyze file sizes and identify large files"""
        try:
            # Get total project size
            total_size = sum(f.stat().st_size for f in self.project_root.rglob('*') if f.is_file())
            total_size_gb = total_size / (1024**3)
            
            # Find large files
            large_files = []
            for file_path in self.project_root.rglob('*'):
                if file_path.is_file():
                    size_mb = file_path.stat().st_size / (1024**2)
                    if size_mb > 10:  # Files larger than 10MB
                        large_files.append({
                            'path': str(file_path),
                            'size_mb': round(size_mb, 2),
                            'type': file_path.suffix,
                            'is_essential': self._is_essential_file(file_path)
                        })
            
            # Sort by size
            large_files.sort(key=lambda x: x['size_mb'], reverse=True)
            
            return {
                'total_size_gb': round(total_size_gb, 2),
                'is_oversized': total_size_gb > 10,
                'large_files': large_files[:20],  # Top 20 largest files
                'non_essential_large_files': [f for f in large_files if not f['is_essential']],
                'total_large_files': len(large_files)
            }
            
        except Exception as e:
            return {'error': str(e), 'total_size_gb': 0, 'large_files': []}
    
    def _analyze_repository_structure(self) -> Dict[str, Any]:
        """Analyze repository structure for optimization"""
        
        # Count files by type
        file_types = {}
        module_count = 0
        config_files = 0
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                file_types[suffix] = file_types.get(suffix, 0) + 1
                
                if suffix == '.py':
                    module_count += 1
                elif file_path.name.startswith('.nexus') or file_path.name.endswith('.config'):
                    config_files += 1
        
        # Identify redundant directories
        redundant_dirs = self._find_redundant_directories()
        
        # Check for duplicate functionality
        duplicate_modules = self._find_duplicate_modules()
        
        return {
            'total_files': sum(file_types.values()),
            'python_modules': module_count,
            'config_files': config_files,
            'file_types': file_types,
            'redundant_directories': redundant_dirs,
            'duplicate_modules': duplicate_modules,
            'optimization_potential': len(redundant_dirs) + len(duplicate_modules)
        }
    
    def _identify_hidden_functions(self) -> Dict[str, Any]:
        """Identify unused or hidden functions that could be removed"""
        
        unused_functions = []
        nexus_modules = []
        
        # Scan Python files for function definitions
        for py_file in self.project_root.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Count function definitions
                import re
                functions = re.findall(r'def\s+(\w+)\s*\(', content)
                classes = re.findall(r'class\s+(\w+)\s*[\(:]', content)
                
                if 'nexus' in str(py_file).lower():
                    nexus_modules.append({
                        'file': str(py_file),
                        'functions': len(functions),
                        'classes': len(classes),
                        'lines': len(content.splitlines())
                    })
                
                # Check for unused imports
                imports = re.findall(r'import\s+(\w+)', content)
                unused_imports = self._find_unused_imports(content, imports)
                
                if unused_imports:
                    unused_functions.append({
                        'file': str(py_file),
                        'unused_imports': unused_imports
                    })
                    
            except Exception:
                continue
        
        return {
            'nexus_modules': nexus_modules,
            'total_nexus_functions': sum(m['functions'] for m in nexus_modules),
            'unused_imports': unused_functions,
            'removable_functions': self._identify_removable_functions()
        }
    
    def _analyze_brain_connectivity(self) -> Dict[str, Any]:
        """Analyze brain system connectivity issues"""
        
        # Check for brain connection files
        brain_files = []
        for pattern in ['*brain*', '*kaizen*', '*traxovo*', '*dwc*']:
            brain_files.extend(list(self.project_root.rglob(pattern)))
        
        # Check NEXUS integration status
        nexus_integration_files = [
            'nexus_replit_integration.py',
            'nexus_brain_hub_integration.py',
            'nexus_enterprise_rebrand.py'
        ]
        
        integration_status = {}
        for file_name in nexus_integration_files:
            file_path = self.project_root / file_name
            integration_status[file_name] = {
                'exists': file_path.exists(),
                'size_kb': round(file_path.stat().st_size / 1024, 2) if file_path.exists() else 0
            }
        
        # Identify missing connections
        missing_connections = self._identify_missing_brain_connections()
        
        return {
            'brain_files_found': len(brain_files),
            'brain_files': [str(f) for f in brain_files],
            'nexus_integration_status': integration_status,
            'missing_connections': missing_connections,
            'connection_bottlenecks': self._identify_connection_bottlenecks()
        }
    
    def _generate_optimization_plan(self, file_analysis, repo_analysis, 
                                  hidden_functions, brain_connectivity) -> Dict[str, Any]:
        """Generate comprehensive optimization plan"""
        
        optimizations = []
        size_reduction_potential = 0
        
        # File size optimizations
        if file_analysis.get('non_essential_large_files'):
            for file_info in file_analysis['non_essential_large_files'][:10]:
                optimizations.append({
                    'type': 'file_removal',
                    'target': file_info['path'],
                    'size_reduction_mb': file_info['size_mb'],
                    'action': f"Remove {file_info['path']} ({file_info['size_mb']}MB)"
                })
                size_reduction_potential += file_info['size_mb']
        
        # Repository structure optimizations
        if repo_analysis.get('redundant_directories'):
            for redundant_dir in repo_analysis['redundant_directories']:
                optimizations.append({
                    'type': 'directory_cleanup',
                    'target': redundant_dir,
                    'action': f"Consolidate or remove redundant directory: {redundant_dir}"
                })
        
        # Function cleanup optimizations
        if hidden_functions.get('unused_imports'):
            optimizations.append({
                'type': 'code_cleanup',
                'target': 'unused_imports',
                'action': "Remove unused imports across modules"
            })
        
        # Brain connectivity optimizations
        if brain_connectivity.get('missing_connections'):
            for missing in brain_connectivity['missing_connections']:
                optimizations.append({
                    'type': 'brain_connection',
                    'target': missing,
                    'action': f"Establish missing brain connection: {missing}"
                })
        
        return {
            'optimizations': optimizations,
            'total_optimizations': len(optimizations),
            'potential_size_reduction_mb': round(size_reduction_potential, 2),
            'priority_actions': self._prioritize_optimizations(optimizations),
            'deployment_strategy': self._recommend_deployment_strategy(file_analysis)
        }
    
    def _is_essential_file(self, file_path: Path) -> bool:
        """Determine if a file is essential for deployment"""
        essential_patterns = [
            'app_executive.py',
            'main.py',
            'nexus_replit_integration.py',
            'nexus_brain_hub_integration.py',
            'requirements.txt',
            'pyproject.toml'
        ]
        
        non_essential_patterns = [
            '.git/',
            '__pycache__/',
            '.backup',
            'test_',
            'debug_',
            'logs/',
            'backups/'
        ]
        
        file_str = str(file_path)
        
        # Check non-essential patterns first
        for pattern in non_essential_patterns:
            if pattern in file_str:
                return False
        
        # Check essential patterns
        for pattern in essential_patterns:
            if pattern in file_str:
                return True
        
        # Python files in main directory are generally essential
        if file_path.suffix == '.py' and '/' not in str(file_path.relative_to(self.project_root)):
            return True
        
        return False
    
    def _find_redundant_directories(self) -> List[str]:
        """Find redundant directories"""
        redundant = []
        
        # Common redundant directory patterns
        redundant_patterns = [
            'backups',
            'old',
            'backup',
            'temp',
            'tmp',
            'test',
            'debug',
            'logs'
        ]
        
        for dir_path in self.project_root.rglob('*'):
            if dir_path.is_dir():
                dir_name = dir_path.name.lower()
                if any(pattern in dir_name for pattern in redundant_patterns):
                    redundant.append(str(dir_path))
        
        return redundant
    
    def _find_duplicate_modules(self) -> List[Dict[str, str]]:
        """Find potentially duplicate modules"""
        duplicates = []
        
        # Look for similar named files
        py_files = list(self.project_root.rglob('*.py'))
        
        for i, file1 in enumerate(py_files):
            for file2 in py_files[i+1:]:
                if self._files_are_similar(file1.name, file2.name):
                    duplicates.append({
                        'file1': str(file1),
                        'file2': str(file2),
                        'similarity': 'name_similar'
                    })
        
        return duplicates
    
    def _files_are_similar(self, name1: str, name2: str) -> bool:
        """Check if two filenames are similar"""
        # Simple similarity check
        base1 = name1.replace('.py', '').lower()
        base2 = name2.replace('.py', '').lower()
        
        # Check for common patterns
        if base1 in base2 or base2 in base1:
            return len(base1) > 5 and len(base2) > 5  # Avoid flagging short names
        
        return False
    
    def _find_unused_imports(self, content: str, imports: List[str]) -> List[str]:
        """Find unused imports in a file"""
        unused = []
        
        for imp in imports:
            # Simple check - if import name doesn't appear elsewhere in file
            if content.count(imp) == 1:  # Only appears in import statement
                unused.append(imp)
        
        return unused
    
    def _identify_removable_functions(self) -> List[Dict[str, str]]:
        """Identify functions that could be removed"""
        removable = []
        
        # Common patterns for removable functions
        removable_patterns = [
            'test_',
            'debug_',
            'old_',
            'backup_',
            'temp_',
            'unused_'
        ]
        
        for py_file in self.project_root.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                import re
                functions = re.findall(r'def\s+(\w+)\s*\(', content)
                
                for func in functions:
                    if any(pattern in func.lower() for pattern in removable_patterns):
                        removable.append({
                            'file': str(py_file),
                            'function': func,
                            'reason': 'pattern_match'
                        })
                        
            except Exception:
                continue
        
        return removable
    
    def _identify_missing_brain_connections(self) -> List[str]:
        """Identify missing brain system connections"""
        missing = []
        
        expected_connections = [
            'kaizen_gpt_integration',
            'traxovo_unified_dashboard_sync',
            'dwc_dashboard_connection',
            'external_brain_hub_relay'
        ]
        
        # Check if integration files exist
        for connection in expected_connections:
            if not any(connection in str(f) for f in self.project_root.rglob('*.py')):
                missing.append(connection)
        
        return missing
    
    def _identify_connection_bottlenecks(self) -> List[str]:
        """Identify brain connection bottlenecks"""
        bottlenecks = []
        
        # Check for common bottleneck indicators
        if not (self.project_root / 'nexus_brain_hub_integration.py').exists():
            bottlenecks.append('Missing brain hub integration module')
        
        if not (self.project_root / 'nexus_replit_integration.py').exists():
            bottlenecks.append('Missing Replit integration for persistence')
        
        # Check for oversized files that could slow deployment
        try:
            for file_path in self.project_root.rglob('*.py'):
                if file_path.stat().st_size > 50 * 1024 * 1024:  # 50MB
                    bottlenecks.append(f'Oversized module: {file_path.name}')
        except Exception:
            pass
        
        return bottlenecks
    
    def _prioritize_optimizations(self, optimizations: List[Dict]) -> List[Dict]:
        """Prioritize optimizations by impact"""
        priority_order = {
            'file_removal': 1,
            'directory_cleanup': 2,
            'brain_connection': 3,
            'code_cleanup': 4
        }
        
        return sorted(optimizations, 
                     key=lambda x: (priority_order.get(x['type'], 5), 
                                   -x.get('size_reduction_mb', 0)))
    
    def _recommend_deployment_strategy(self, file_analysis: Dict) -> Dict[str, Any]:
        """Recommend deployment strategy based on analysis"""
        
        if file_analysis.get('total_size_gb', 0) > 10:
            return {
                'strategy': 'selective_deployment',
                'approach': 'Deploy only essential modules first, then sync additional components',
                'phases': [
                    'Core NEXUS modules (app_executive.py, nexus_replit_integration.py)',
                    'Brain hub integration (nexus_brain_hub_integration.py)',
                    'Enterprise modules (data_connectors.py, automation_engine.py)',
                    'Additional features and optimizations'
                ]
            }
        else:
            return {
                'strategy': 'full_deployment',
                'approach': 'Deploy complete system with current optimization',
                'phases': ['Complete deployment with current configuration']
            }
    
    def _assess_deployment_readiness(self) -> Dict[str, Any]:
        """Assess overall deployment readiness"""
        
        essential_files = [
            'app_executive.py',
            'main.py',
            'nexus_replit_integration.py'
        ]
        
        readiness_score = 0
        missing_essentials = []
        
        for file_name in essential_files:
            if (self.project_root / file_name).exists():
                readiness_score += 1
            else:
                missing_essentials.append(file_name)
        
        readiness_percentage = (readiness_score / len(essential_files)) * 100
        
        return {
            'readiness_percentage': round(readiness_percentage, 1),
            'status': 'ready' if readiness_percentage >= 80 else 'needs_optimization',
            'missing_essentials': missing_essentials,
            'deployment_blocking_issues': self._identify_blocking_issues()
        }
    
    def _identify_blocking_issues(self) -> List[str]:
        """Identify issues that block deployment"""
        blocking_issues = []
        
        # Check for common blocking issues
        if not (self.project_root / 'app_executive.py').exists():
            blocking_issues.append('Missing main application file (app_executive.py)')
        
        if not (self.project_root / 'main.py').exists():
            blocking_issues.append('Missing entry point file (main.py)')
        
        # Check for syntax errors in main files
        main_files = ['app_executive.py', 'main.py', 'nexus_replit_integration.py']
        for file_name in main_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, file_name, 'exec')
                except SyntaxError as e:
                    blocking_issues.append(f'Syntax error in {file_name}: {e}')
                except Exception:
                    pass
        
        return blocking_issues

def run_nexus_deployment_intelligence():
    """Run comprehensive deployment intelligence analysis"""
    
    print("NEXUS Deployment Intelligence Analysis")
    print("Identifying deployment bottlenecks and brain connection issues...")
    
    intelligence = NexusDeploymentIntelligence()
    analysis = intelligence.analyze_deployment_bottlenecks()
    
    print(f"\nFILE SIZE ANALYSIS:")
    print(f"Total Project Size: {analysis['file_size_analysis']['total_size_gb']} GB")
    print(f"Is Oversized: {analysis['file_size_analysis']['is_oversized']}")
    print(f"Large Files Found: {analysis['file_size_analysis']['total_large_files']}")
    
    print(f"\nREPOSITORY STRUCTURE:")
    print(f"Total Files: {analysis['repository_analysis']['total_files']}")
    print(f"Python Modules: {analysis['repository_analysis']['python_modules']}")
    print(f"Optimization Potential: {analysis['repository_analysis']['optimization_potential']} items")
    
    print(f"\nBRAIN CONNECTIVITY:")
    print(f"Brain Files Found: {analysis['brain_connectivity']['brain_files_found']}")
    print(f"Missing Connections: {len(analysis['brain_connectivity']['missing_connections'])}")
    print(f"Connection Bottlenecks: {len(analysis['brain_connectivity']['connection_bottlenecks'])}")
    
    print(f"\nOPTIMIZATION PLAN:")
    print(f"Total Optimizations: {analysis['optimization_plan']['total_optimizations']}")
    print(f"Potential Size Reduction: {analysis['optimization_plan']['potential_size_reduction_mb']} MB")
    
    print(f"\nDEPLOYMENT READINESS:")
    print(f"Readiness Score: {analysis['deployment_status']['readiness_percentage']}%")
    print(f"Status: {analysis['deployment_status']['status']}")
    
    # Show priority actions
    if analysis['optimization_plan']['priority_actions']:
        print(f"\nPRIORITY ACTIONS:")
        for i, action in enumerate(analysis['optimization_plan']['priority_actions'][:5], 1):
            print(f"{i}. {action['action']}")
    
    # Show blocking issues
    if analysis['deployment_status']['deployment_blocking_issues']:
        print(f"\nBLOCKING ISSUES:")
        for issue in analysis['deployment_status']['deployment_blocking_issues']:
            print(f"- {issue}")
    
    return analysis

if __name__ == "__main__":
    analysis_result = run_nexus_deployment_intelligence()