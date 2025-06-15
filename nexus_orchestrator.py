"""
NEXUS Universal Orchestrator
Seamless integration and communication between all system connectors
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

class NEXUSOrchestrator:
    """Universal orchestrator for seamless connector integration"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.connectors = {}
        self.communication_matrix = {}
        self.health_status = {}
        self.data_flow_map = {}
        self.initialize_connector_network()
    
    def initialize_connector_network(self):
        """Initialize all system connectors and their relationships"""
        self.connectors = {
            'ground_works': {
                'endpoints': [
                    '/api/groundworks/data',
                    '/api/ground-works/projects',
                    '/ground-works-complete'
                ],
                'dependencies': ['ragle_processor', 'asset_manager'],
                'data_types': ['projects', 'assets', 'billing']
            },
            'ragle_processor': {
                'endpoints': [
                    '/api/ragle-daily-hours',
                    '/api/ragle-billing'
                ],
                'dependencies': ['ground_works'],
                'data_types': ['hours', 'quantities', 'billing']
            },
            'api_benchmark': {
                'endpoints': [
                    '/api-performance-benchmark',
                    '/api/benchmark/run/quick',
                    '/api/benchmark/run/standard',
                    '/api/benchmark/run/stress',
                    '/api/benchmark/run/enterprise'
                ],
                'dependencies': ['all_connectors'],
                'data_types': ['performance', 'metrics', 'analytics']
            },
            'troy_dashboard': {
                'endpoints': [
                    '/ultimate-troy-dashboard',
                    '/api/troy/analytics'
                ],
                'dependencies': ['ground_works', 'ragle_processor'],
                'data_types': ['dashboard', 'analytics', 'summaries']
            },
            'asset_manager': {
                'endpoints': [
                    '/api/assets/status',
                    '/api/assets/utilization'
                ],
                'dependencies': ['ground_works'],
                'data_types': ['assets', 'maintenance', 'utilization']
            }
        }
        
        self.establish_communication_matrix()
    
    def establish_communication_matrix(self):
        """Create communication pathways between all connectors"""
        for connector_name, connector_info in self.connectors.items():
            self.communication_matrix[connector_name] = {
                'outbound': [],
                'inbound': [],
                'bidirectional': []
            }
            
            # Establish dependencies
            for dependency in connector_info['dependencies']:
                if dependency == 'all_connectors':
                    self.communication_matrix[connector_name]['inbound'].extend(
                        [c for c in self.connectors.keys() if c != connector_name]
                    )
                elif dependency in self.connectors:
                    self.communication_matrix[connector_name]['inbound'].append(dependency)
                    if dependency not in self.communication_matrix:
                        self.communication_matrix[dependency] = {'outbound': [], 'inbound': [], 'bidirectional': []}
                    self.communication_matrix[dependency]['outbound'].append(connector_name)
    
    def health_check_all_connectors(self) -> Dict:
        """Perform comprehensive health check on all connectors"""
        health_results = {}
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_connector = {}
            
            for connector_name, connector_info in self.connectors.items():
                for endpoint in connector_info['endpoints']:
                    future = executor.submit(self._check_endpoint_health, endpoint)
                    future_to_connector[future] = (connector_name, endpoint)
            
            for future in as_completed(future_to_connector):
                connector_name, endpoint = future_to_connector[future]
                try:
                    health_data = future.result()
                    if connector_name not in health_results:
                        health_results[connector_name] = {'endpoints': {}, 'overall_status': 'healthy'}
                    
                    health_results[connector_name]['endpoints'][endpoint] = health_data
                    
                    if not health_data['healthy']:
                        health_results[connector_name]['overall_status'] = 'degraded'
                        
                except Exception as e:
                    if connector_name not in health_results:
                        health_results[connector_name] = {'endpoints': {}, 'overall_status': 'error'}
                    health_results[connector_name]['endpoints'][endpoint] = {
                        'healthy': False,
                        'error': str(e),
                        'response_time': None
                    }
                    health_results[connector_name]['overall_status'] = 'error'
        
        self.health_status = health_results
        return health_results
    
    def _check_endpoint_health(self, endpoint: str) -> Dict:
        """Check health of individual endpoint"""
        try:
            start_time = datetime.now()
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                'healthy': response.status_code == 200,
                'status_code': response.status_code,
                'response_time': response_time,
                'content_length': len(response.content),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'response_time': None,
                'timestamp': datetime.now().isoformat()
            }
    
    def orchestrate_data_flow(self, source_connector: str, target_connector: str) -> Dict:
        """Orchestrate seamless data flow between connectors"""
        if source_connector not in self.connectors or target_connector not in self.connectors:
            return {'success': False, 'error': 'Invalid connector specified'}
        
        # Get data from source
        source_data = self._fetch_connector_data(source_connector)
        
        # Transform data for target compatibility
        transformed_data = self._transform_data_for_target(source_data, source_connector, target_connector)
        
        # Push data to target
        result = self._push_data_to_target(transformed_data, target_connector)
        
        return {
            'success': result['success'],
            'source': source_connector,
            'target': target_connector,
            'data_points': len(transformed_data) if transformed_data else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def _fetch_connector_data(self, connector_name: str) -> Dict:
        """Fetch data from specified connector"""
        connector_info = self.connectors[connector_name]
        primary_endpoint = connector_info['endpoints'][0]
        
        try:
            response = requests.get(f"{self.base_url}{primary_endpoint}")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logging.error(f"Error fetching data from {connector_name}: {e}")
            return {}
    
    def _transform_data_for_target(self, data: Dict, source: str, target: str) -> Dict:
        """Transform data between different connector formats"""
        transformation_rules = {
            ('ground_works', 'ragle_processor'): self._transform_gw_to_ragle,
            ('ragle_processor', 'ground_works'): self._transform_ragle_to_gw,
            ('ground_works', 'troy_dashboard'): self._transform_gw_to_troy,
            ('api_benchmark', 'troy_dashboard'): self._transform_benchmark_to_troy
        }
        
        transform_func = transformation_rules.get((source, target))
        if transform_func:
            return transform_func(data)
        
        # Default passthrough transformation
        return data
    
    def _transform_gw_to_ragle(self, data: Dict) -> Dict:
        """Transform Ground Works data for RAGLE processor"""
        return {
            'projects': data.get('projects', []),
            'hours_data': self._extract_hours_from_projects(data.get('projects', [])),
            'billing_data': self._extract_billing_from_projects(data.get('projects', []))
        }
    
    def _transform_ragle_to_gw(self, data: Dict) -> Dict:
        """Transform RAGLE data for Ground Works"""
        return {
            'project_hours': data.get('hours_summary', {}),
            'billing_summary': data.get('billing_summary', {}),
            'resource_allocation': data.get('resource_data', {})
        }
    
    def _transform_gw_to_troy(self, data: Dict) -> Dict:
        """Transform Ground Works data for Troy dashboard"""
        return {
            'dashboard_metrics': {
                'total_projects': len(data.get('projects', [])),
                'active_value': sum(p.get('contract_amount', 0) for p in data.get('projects', [])),
                'completion_rate': self._calculate_completion_rate(data.get('projects', []))
            },
            'project_summary': data.get('projects', [])[:10]  # Top 10 projects
        }
    
    def _transform_benchmark_to_troy(self, data: Dict) -> Dict:
        """Transform benchmark data for Troy dashboard"""
        return {
            'performance_metrics': data.get('analytics', {}),
            'system_health': data.get('summary', {}),
            'api_status': data.get('endpoints', {})
        }
    
    def _extract_hours_from_projects(self, projects: List) -> Dict:
        """Extract hours data from project list"""
        total_hours = 0
        project_hours = {}
        
        for project in projects:
            hours = project.get('estimated_hours', 0) or project.get('hours', 0)
            total_hours += hours
            project_hours[project.get('job_number', 'unknown')] = hours
        
        return {
            'total_hours': total_hours,
            'project_breakdown': project_hours
        }
    
    def _extract_billing_from_projects(self, projects: List) -> Dict:
        """Extract billing data from project list"""
        total_amount = 0
        project_billing = {}
        
        for project in projects:
            amount = project.get('contract_amount', 0) or project.get('amount', 0)
            total_amount += amount
            project_billing[project.get('job_number', 'unknown')] = amount
        
        return {
            'total_contract_value': total_amount,
            'project_breakdown': project_billing
        }
    
    def _calculate_completion_rate(self, projects: List) -> float:
        """Calculate overall project completion rate"""
        if not projects:
            return 0.0
        
        completed = sum(1 for p in projects if p.get('status', '').lower() in ['completed', 'near completion'])
        return (completed / len(projects)) * 100
    
    def _push_data_to_target(self, data: Dict, target_connector: str) -> Dict:
        """Push transformed data to target connector"""
        # For now, store in data flow map for tracking
        if target_connector not in self.data_flow_map:
            self.data_flow_map[target_connector] = []
        
        self.data_flow_map[target_connector].append({
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        return {'success': True, 'message': f'Data pushed to {target_connector}'}
    
    def get_system_topology(self) -> Dict:
        """Get complete system topology and communication map"""
        return {
            'connectors': self.connectors,
            'communication_matrix': self.communication_matrix,
            'health_status': self.health_status,
            'data_flows': len(self.data_flow_map),
            'topology_map': self._generate_topology_visualization()
        }
    
    def _generate_topology_visualization(self) -> Dict:
        """Generate visual topology map"""
        nodes = []
        edges = []
        
        for connector_name in self.connectors.keys():
            nodes.append({
                'id': connector_name,
                'label': connector_name.replace('_', ' ').title(),
                'status': self.health_status.get(connector_name, {}).get('overall_status', 'unknown'),
                'endpoints': len(self.connectors[connector_name]['endpoints'])
            })
        
        for connector_name, comm_info in self.communication_matrix.items():
            for target in comm_info['outbound']:
                edges.append({
                    'from': connector_name,
                    'to': target,
                    'type': 'outbound'
                })
            
            for target in comm_info['bidirectional']:
                edges.append({
                    'from': connector_name,
                    'to': target,
                    'type': 'bidirectional'
                })
        
        return {'nodes': nodes, 'edges': edges}
    
    def synchronize_all_connectors(self) -> Dict:
        """Perform full system synchronization"""
        sync_results = {
            'health_check': self.health_check_all_connectors(),
            'data_flows': [],
            'sync_timestamp': datetime.now().isoformat(),
            'total_connectors': len(self.connectors),
            'healthy_connectors': 0,
            'degraded_connectors': 0,
            'error_connectors': 0
        }
        
        # Count connector health
        for connector_name, health_info in sync_results['health_check'].items():
            status = health_info.get('overall_status', 'unknown')
            if status == 'healthy':
                sync_results['healthy_connectors'] += 1
            elif status == 'degraded':
                sync_results['degraded_connectors'] += 1
            else:
                sync_results['error_connectors'] += 1
        
        # Orchestrate critical data flows
        critical_flows = [
            ('ground_works', 'ragle_processor'),
            ('ragle_processor', 'troy_dashboard'),
            ('ground_works', 'troy_dashboard'),
            ('api_benchmark', 'troy_dashboard')
        ]
        
        for source, target in critical_flows:
            flow_result = self.orchestrate_data_flow(source, target)
            sync_results['data_flows'].append(flow_result)
        
        return sync_results

def get_nexus_orchestrator():
    """Get NEXUS orchestrator instance"""
    return NEXUSOrchestrator()