"""
NEXUS Route Consolidation Analysis
Analyzing redundant routes and consolidating into unified modules
"""

import os
import re
import json
from typing import Dict, List, Any, Set
from pathlib import Path

class NexusRouteAnalyzer:
    """Analyze and consolidate Flask routes across modules"""
    
    def __init__(self):
        self.python_files = list(Path('.').glob('*.py'))
        self.routes_found = {}
        self.redundancies = []
        self.consolidation_plan = {}
        
    def analyze_all_routes(self) -> Dict[str, Any]:
        """Comprehensive analysis of all routes in the system"""
        
        # Extract routes from all Python files
        for file_path in self.python_files:
            if 'app' in file_path.name:
                routes = self._extract_routes_from_file(file_path)
                self.routes_found[str(file_path)] = routes
        
        analysis = {
            'route_inventory': self._create_route_inventory(),
            'redundancy_analysis': self._analyze_redundancies(),
            'module_overlap': self._analyze_module_overlap(),
            'consolidation_recommendations': self._generate_consolidation_plan(),
            'unified_architecture': self._design_unified_architecture()
        }
        
        return analysis
    
    def _extract_routes_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract Flask routes from a Python file"""
        
        routes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all @app.route decorators
            route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=\[([^\]]+)\])?\)"
            function_pattern = r"def\s+(\w+)\s*\([^)]*\):"
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                route_match = re.search(route_pattern, line)
                if route_match:
                    route_path = route_match.group(1)
                    methods = route_match.group(2) if route_match.group(2) else "'GET'"
                    
                    # Find the function name in the next few lines
                    function_name = None
                    for j in range(i+1, min(i+5, len(lines))):
                        func_match = re.search(function_pattern, lines[j])
                        if func_match:
                            function_name = func_match.group(1)
                            break
                    
                    routes.append({
                        'path': route_path,
                        'methods': methods,
                        'function': function_name,
                        'line_number': i+1,
                        'category': self._categorize_route(route_path)
                    })
                    
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return routes
    
    def _categorize_route(self, path: str) -> str:
        """Categorize route by its purpose"""
        
        if '/api/' in path:
            if 'nexus' in path:
                return 'nexus_api'
            elif any(term in path for term in ['platform', 'status', 'data']):
                return 'platform_api'
            elif any(term in path for term in ['market', 'trading', 'intelligence']):
                return 'intelligence_api'
            else:
                return 'general_api'
        elif path in ['/', '/index', '/home']:
            return 'landing_pages'
        elif any(term in path for term in ['dashboard', 'admin', 'executive']):
            return 'dashboard_routes'
        elif any(term in path for term in ['auth', 'login', 'logout']):
            return 'authentication'
        elif any(term in path for term in ['health', 'status']):
            return 'health_checks'
        else:
            return 'miscellaneous'
    
    def _create_route_inventory(self) -> Dict[str, Any]:
        """Create comprehensive inventory of all routes"""
        
        all_routes = []
        route_counts = {}
        category_counts = {}
        
        for file_path, routes in self.routes_found.items():
            for route in routes:
                all_routes.append({
                    'file': file_path,
                    'path': route['path'],
                    'function': route['function'],
                    'category': route['category'],
                    'methods': route['methods']
                })
                
                # Count routes by path
                route_counts[route['path']] = route_counts.get(route['path'], 0) + 1
                
                # Count by category
                category_counts[route['category']] = category_counts.get(route['category'], 0) + 1
        
        return {
            'total_routes': len(all_routes),
            'total_files': len(self.routes_found),
            'routes_by_file': {file: len(routes) for file, routes in self.routes_found.items()},
            'route_counts': route_counts,
            'category_distribution': category_counts,
            'all_routes': all_routes
        }
    
    def _analyze_redundancies(self) -> Dict[str, Any]:
        """Analyze route redundancies and conflicts"""
        
        path_duplicates = {}
        function_duplicates = {}
        similar_paths = []
        
        all_routes = []
        for routes in self.routes_found.values():
            all_routes.extend(routes)
        
        # Find duplicate paths
        for route in all_routes:
            path = route['path']
            if path in path_duplicates:
                path_duplicates[path].append(route)
            else:
                path_duplicates[path] = [route]
        
        # Filter to only actual duplicates
        path_duplicates = {path: routes for path, routes in path_duplicates.items() if len(routes) > 1}
        
        # Find duplicate function names
        for route in all_routes:
            func = route['function']
            if func:
                if func in function_duplicates:
                    function_duplicates[func].append(route)
                else:
                    function_duplicates[func] = [route]
        
        function_duplicates = {func: routes for func, routes in function_duplicates.items() if len(routes) > 1}
        
        # Find similar paths (potential consolidation opportunities)
        for i, route1 in enumerate(all_routes):
            for route2 in all_routes[i+1:]:
                if self._paths_are_similar(route1['path'], route2['path']):
                    similar_paths.append({
                        'path1': route1['path'],
                        'path2': route2['path'],
                        'function1': route1['function'],
                        'function2': route2['function'],
                        'consolidation_potential': 'high'
                    })
        
        return {
            'duplicate_paths': path_duplicates,
            'duplicate_functions': function_duplicates,
            'similar_paths': similar_paths,
            'redundancy_score': len(path_duplicates) + len(similar_paths)
        }
    
    def _analyze_module_overlap(self) -> Dict[str, Any]:
        """Analyze overlap between different app modules"""
        
        module_analysis = {}
        
        for file_path, routes in self.routes_found.items():
            filename = Path(file_path).name
            
            # Categorize routes by their purpose
            categories = {}
            for route in routes:
                category = route['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(route['path'])
            
            module_analysis[filename] = {
                'total_routes': len(routes),
                'categories': categories,
                'primary_purpose': max(categories.keys(), key=lambda k: len(categories[k])) if categories else None
            }
        
        # Find overlapping functionalities
        overlaps = []
        files = list(module_analysis.keys())
        
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                common_categories = set(module_analysis[file1]['categories'].keys()) & \
                                 set(module_analysis[file2]['categories'].keys())
                
                if common_categories:
                    overlaps.append({
                        'file1': file1,
                        'file2': file2,
                        'overlapping_categories': list(common_categories),
                        'consolidation_needed': len(common_categories) > 1
                    })
        
        return {
            'module_breakdown': module_analysis,
            'functionality_overlaps': overlaps,
            'consolidation_opportunities': len(overlaps)
        }
    
    def _generate_consolidation_plan(self) -> Dict[str, Any]:
        """Generate plan to consolidate routes"""
        
        # Analyze current structure
        inventory = self._create_route_inventory()
        redundancies = self._analyze_redundancies()
        
        consolidation_plan = {
            'core_api_module': {
                'filename': 'nexus_unified_api.py',
                'purpose': 'Single API module for all NEXUS endpoints',
                'routes_to_consolidate': [
                    '/api/nexus-intelligence',
                    '/api/platform-status',
                    '/api/market-data',
                    '/api/executive-metrics',
                    '/api/self-heal-check',
                    '/api/platform-health'
                ],
                'benefits': 'Unified API interface, consistent error handling, centralized authentication'
            },
            'dashboard_module': {
                'filename': 'nexus_dashboard_routes.py',
                'purpose': 'All dashboard and UI routes',
                'routes_to_consolidate': [
                    '/',
                    '/executive-dashboard',
                    '/nexus-admin',
                    '/trading-interface',
                    '/mobile-terminal'
                ],
                'benefits': 'Consistent UI patterns, shared templates, unified authentication'
            },
            'health_module': {
                'filename': 'nexus_health_routes.py',
                'purpose': 'Health checks and system status',
                'routes_to_consolidate': [
                    '/health-check',
                    '/health',
                    '/api/platform-health'
                ],
                'benefits': 'Centralized monitoring, consistent health reporting'
            },
            'authentication_module': {
                'filename': 'nexus_auth_routes.py',
                'purpose': 'All authentication and security routes',
                'routes_to_consolidate': [
                    '/login',
                    '/logout',
                    '/auth/*'
                ],
                'benefits': 'Security consistency, centralized session management'
            }
        }
        
        # Calculate consolidation impact
        total_routes = inventory['total_routes']
        consolidatable_routes = sum(len(module['routes_to_consolidate']) 
                                  for module in consolidation_plan.values())
        
        return {
            'consolidation_modules': consolidation_plan,
            'impact_analysis': {
                'total_routes': total_routes,
                'consolidatable_routes': consolidatable_routes,
                'reduction_percentage': (consolidatable_routes / total_routes * 100) if total_routes > 0 else 0,
                'files_reducible': len([f for f in self.routes_found.keys() if 'app' in f]) - len(consolidation_plan)
            },
            'implementation_priority': [
                'core_api_module',
                'dashboard_module', 
                'health_module',
                'authentication_module'
            ]
        }
    
    def _design_unified_architecture(self) -> Dict[str, Any]:
        """Design unified architecture for NEXUS routes"""
        
        return {
            'proposed_structure': {
                'nexus_main.py': {
                    'purpose': 'Main application entry point',
                    'responsibilities': ['App initialization', 'Blueprint registration', 'Configuration loading']
                },
                'nexus_api_v1.py': {
                    'purpose': 'Version 1 API endpoints',
                    'responsibilities': ['All /api/v1/* routes', 'API authentication', 'Response formatting']
                },
                'nexus_dashboard.py': {
                    'purpose': 'Dashboard and UI routes',
                    'responsibilities': ['Dashboard rendering', 'UI state management', 'Template routing']
                },
                'nexus_intelligence.py': {
                    'purpose': 'AI and intelligence endpoints',
                    'responsibilities': ['LLM integration', 'Intelligence APIs', 'Chat functionality']
                },
                'nexus_enterprise.py': {
                    'purpose': 'Enterprise-specific features',
                    'responsibilities': ['Company configs', 'Enterprise APIs', 'Business logic']
                }
            },
            'routing_conventions': {
                'api_versioning': 'All APIs under /api/v1/',
                'authentication': 'Consistent @require_auth decorator',
                'error_handling': 'Unified error response format',
                'documentation': 'OpenAPI/Swagger integration'
            },
            'migration_strategy': {
                'phase_1': 'Create unified modules with consolidated routes',
                'phase_2': 'Migrate existing routes to new modules',
                'phase_3': 'Remove redundant files',
                'phase_4': 'Update imports and references'
            }
        }
    
    def _paths_are_similar(self, path1: str, path2: str) -> bool:
        """Check if two paths are similar enough to consolidate"""
        
        # Simple similarity check
        if path1 == path2:
            return False  # Exact duplicates handled separately
        
        # Check for similar patterns
        patterns = [
            (r'/api/\w+-\w+', '/api/*'),  # Similar API patterns
            (r'/\w+-dashboard', '/dashboard'),  # Similar dashboard patterns
            (r'/health.*', '/health'),  # Health check variations
        ]
        
        for pattern, _ in patterns:
            if re.match(pattern, path1) and re.match(pattern, path2):
                return True
        
        return False

def analyze_route_proliferation():
    """Analyze route proliferation and provide consolidation recommendations"""
    
    print("NEXUS Route Consolidation Analysis")
    print("Analyzing route proliferation and redundancies...")
    
    analyzer = NexusRouteAnalyzer()
    analysis = analyzer.analyze_all_routes()
    
    print(f"\nROUTE INVENTORY:")
    inventory = analysis['route_inventory']
    print(f"Total Routes: {inventory['total_routes']}")
    print(f"Total Files: {inventory['total_files']}")
    
    print(f"\nRoutes by File:")
    for file, count in inventory['routes_by_file'].items():
        print(f"  {Path(file).name}: {count} routes")
    
    print(f"\nCategory Distribution:")
    for category, count in inventory['category_distribution'].items():
        print(f"  {category}: {count} routes")
    
    print(f"\nREDUNDANCY ANALYSIS:")
    redundancies = analysis['redundancy_analysis']
    
    if redundancies['duplicate_paths']:
        print(f"Duplicate Paths Found: {len(redundancies['duplicate_paths'])}")
        for path, routes in redundancies['duplicate_paths'].items():
            print(f"  {path}: {len(routes)} implementations")
    
    if redundancies['similar_paths']:
        print(f"Similar Paths: {len(redundancies['similar_paths'])}")
        for similar in redundancies['similar_paths'][:5]:  # Show first 5
            print(f"  {similar['path1']} ≈ {similar['path2']}")
    
    print(f"\nMODULE OVERLAP:")
    overlaps = analysis['module_overlap']
    for overlap in overlaps['functionality_overlaps']:
        print(f"  {overlap['file1']} ↔ {overlap['file2']}: {overlap['overlapping_categories']}")
    
    print(f"\nCONSOLIDATION RECOMMENDATIONS:")
    consolidation = analysis['consolidation_recommendations']
    impact = consolidation['impact_analysis']
    
    print(f"Consolidation Impact:")
    print(f"  Routes reducible: {impact['consolidatable_routes']}/{impact['total_routes']} ({impact['reduction_percentage']:.1f}%)")
    print(f"  Files reducible: {impact['files_reducible']} app files can be consolidated")
    
    print(f"\nRecommended Modules:")
    for module_name, module_info in consolidation['consolidation_modules'].items():
        print(f"  {module_info['filename']}: {len(module_info['routes_to_consolidate'])} routes")
        print(f"    Purpose: {module_info['purpose']}")
    
    print(f"\nIMMEDIATE ACTIONS:")
    print("1. Create nexus_unified_api.py for all API endpoints")
    print("2. Consolidate dashboard routes into nexus_dashboard.py") 
    print("3. Remove redundant app_*.py files")
    print("4. Implement unified authentication and error handling")
    
    # Save detailed analysis
    with open('nexus_route_analysis_report.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    return analysis

if __name__ == "__main__":
    analyze_route_proliferation()