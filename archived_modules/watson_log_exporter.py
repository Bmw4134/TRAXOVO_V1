"""
TRAXOVO Watson Login Log Exporter & Simulated User Testing Engine
Captures real user interactions for continuous improvement and automated testing
"""
import json
import time
from datetime import datetime
from flask import request, session
import logging

class WatsonLogExporter:
    """Export Watson login logs and user interaction data for analysis"""
    
    def __init__(self):
        self.log_file = "watson_interactions.json"
        self.session_data = {}
        self.interaction_patterns = []
        
    def capture_watson_login(self, username, login_time, success=True):
        """Capture Watson-specific login events"""
        
        login_event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'watson_login',
            'username': username,
            'login_time_ms': login_time,
            'success': success,
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr,
            'session_id': session.get('session_id', '')
        }
        
        self._append_to_log(login_event)
        return login_event
    
    def capture_user_interaction(self, page, action, element=None, load_time=None):
        """Capture detailed user interactions for HBA training"""
        
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'user_interaction',
            'page': page,
            'action': action,
            'element': element,
            'load_time_ms': load_time,
            'session_id': session.get('session_id', ''),
            'device_type': self._detect_device_type(),
            'viewport': {
                'width': request.headers.get('sec-ch-viewport-width'),
                'height': request.headers.get('sec-ch-viewport-height')
            }
        }
        
        self._append_to_log(interaction)
        self.interaction_patterns.append(interaction)
        return interaction
    
    def capture_performance_metric(self, endpoint, response_time, status_code):
        """Capture performance metrics for optimization"""
        
        metric = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'performance_metric',
            'endpoint': endpoint,
            'response_time_ms': response_time,
            'status_code': status_code,
            'session_id': session.get('session_id', '')
        }
        
        self._append_to_log(metric)
        return metric
    
    def export_watson_logs(self, start_date=None, end_date=None):
        """Export Watson logs for analysis"""
        
        try:
            with open(self.log_file, 'r') as f:
                all_logs = [json.loads(line) for line in f]
            
            # Filter by date range if provided
            if start_date or end_date:
                filtered_logs = []
                for log in all_logs:
                    log_date = datetime.fromisoformat(log['timestamp'])
                    if start_date and log_date < start_date:
                        continue
                    if end_date and log_date > end_date:
                        continue
                    filtered_logs.append(log)
                all_logs = filtered_logs
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_events': len(all_logs),
                'events': all_logs,
                'summary': self._generate_log_summary(all_logs)
            }
            
            export_filename = f"watson_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return export_filename
            
        except Exception as e:
            logging.error(f"Error exporting Watson logs: {e}")
            return None
    
    def _append_to_log(self, event):
        """Append event to log file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logging.error(f"Error writing to log: {e}")
    
    def _detect_device_type(self):
        """Detect device type from user agent"""
        user_agent = request.headers.get('User-Agent', '').lower()
        
        if 'mobile' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        else:
            return 'desktop'
    
    def _generate_log_summary(self, logs):
        """Generate summary statistics from logs"""
        
        summary = {
            'total_events': len(logs),
            'watson_logins': len([l for l in logs if l['event_type'] == 'watson_login']),
            'user_interactions': len([l for l in logs if l['event_type'] == 'user_interaction']),
            'performance_metrics': len([l for l in logs if l['event_type'] == 'performance_metric']),
            'device_breakdown': {},
            'page_views': {},
            'average_response_times': {}
        }
        
        # Analyze device types
        for log in logs:
            if 'device_type' in log:
                device = log['device_type']
                summary['device_breakdown'][device] = summary['device_breakdown'].get(device, 0) + 1
        
        # Analyze page views
        for log in logs:
            if log['event_type'] == 'user_interaction' and 'page' in log:
                page = log['page']
                summary['page_views'][page] = summary['page_views'].get(page, 0) + 1
        
        return summary

class SimulatedUserTesting:
    """Create simulated users to test various login paths and workflows"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_users = [
            {'username': 'tester', 'password': 'tester', 'type': 'standard'},
            {'username': 'watson', 'password': 'watson_pass', 'type': 'watson_admin'},
            {'username': 'mobile_user', 'password': 'mobile123', 'type': 'mobile_focused'}
        ]
        self.test_scenarios = []
        
    def create_test_scenarios(self):
        """Define comprehensive test scenarios"""
        
        scenarios = [
            {
                'name': 'Standard Login Flow',
                'user_type': 'standard',
                'steps': [
                    {'action': 'visit', 'target': '/login'},
                    {'action': 'login', 'credentials': 'tester/tester'},
                    {'action': 'navigate', 'target': '/dashboard'},
                    {'action': 'view', 'target': '/fleet-map'},
                    {'action': 'logout'}
                ]
            },
            {
                'name': 'Watson Admin Workflow',
                'user_type': 'watson_admin',
                'steps': [
                    {'action': 'visit', 'target': '/login'},
                    {'action': 'login', 'credentials': 'watson/watson_pass'},
                    {'action': 'navigate', 'target': '/legacy-timekeeping'},
                    {'action': 'export', 'target': 'attendance_data'},
                    {'action': 'navigate', 'target': '/executive-intelligence'},
                    {'action': 'logout'}
                ]
            },
            {
                'name': 'Mobile User Journey',
                'user_type': 'mobile_focused',
                'device': 'mobile',
                'steps': [
                    {'action': 'visit', 'target': '/login'},
                    {'action': 'login', 'credentials': 'mobile_user/mobile123'},
                    {'action': 'swipe', 'direction': 'right'},
                    {'action': 'navigate', 'target': '/attendance-matrix'},
                    {'action': 'touch', 'element': 'asset_card'},
                    {'action': 'logout'}
                ]
            },
            {
                'name': 'Performance Stress Test',
                'user_type': 'load_tester',
                'concurrent_users': 10,
                'steps': [
                    {'action': 'rapid_login', 'repeat': 5},
                    {'action': 'api_calls', 'endpoints': ['/api/fleet-assets', '/api/enterprise-intelligence']},
                    {'action': 'page_switching', 'pages': ['/dashboard', '/billing', '/asset-manager']}
                ]
            }
        ]
        
        self.test_scenarios = scenarios
        return scenarios
    
    def execute_simulated_testing(self):
        """Execute all simulated user test scenarios"""
        
        test_results = {
            'test_timestamp': datetime.now().isoformat(),
            'scenarios_executed': 0,
            'total_interactions': 0,
            'performance_metrics': {},
            'issues_detected': [],
            'success_rate': 0
        }
        
        for scenario in self.test_scenarios:
            try:
                scenario_result = self._execute_scenario(scenario)
                test_results['scenarios_executed'] += 1
                test_results['total_interactions'] += len(scenario['steps'])
                
                # Track performance
                if 'response_times' in scenario_result:
                    test_results['performance_metrics'][scenario['name']] = scenario_result['response_times']
                
                # Track issues
                if scenario_result.get('issues'):
                    test_results['issues_detected'].extend(scenario_result['issues'])
                    
            except Exception as e:
                test_results['issues_detected'].append({
                    'scenario': scenario['name'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # Calculate success rate
        successful_scenarios = test_results['scenarios_executed'] - len(test_results['issues_detected'])
        test_results['success_rate'] = (successful_scenarios / len(self.test_scenarios)) * 100 if self.test_scenarios else 0
        
        return test_results
    
    def _execute_scenario(self, scenario):
        """Execute individual test scenario"""
        
        import requests
        session = requests.Session()
        
        scenario_result = {
            'scenario_name': scenario['name'],
            'steps_completed': 0,
            'response_times': [],
            'issues': []
        }
        
        for step in scenario['steps']:
            try:
                start_time = time.time()
                
                if step['action'] == 'visit':
                    response = session.get(f"{self.base_url}{step['target']}")
                    
                elif step['action'] == 'login':
                    # Simulate login POST
                    username, password = step['credentials'].split('/')
                    response = session.post(f"{self.base_url}/login", data={
                        'username': username,
                        'password': password
                    })
                    
                elif step['action'] == 'navigate':
                    response = session.get(f"{self.base_url}{step['target']}")
                    
                response_time = (time.time() - start_time) * 1000
                scenario_result['response_times'].append({
                    'step': step['action'],
                    'time_ms': round(response_time, 2)
                })
                
                scenario_result['steps_completed'] += 1
                
            except Exception as e:
                scenario_result['issues'].append({
                    'step': step['action'],
                    'error': str(e)
                })
        
        return scenario_result

# Global instances
watson_logger = WatsonLogExporter()
simulated_tester = SimulatedUserTesting()

def initialize_watson_logging():
    """Initialize Watson logging system"""
    watson_logger.create_test_scenarios()
    return watson_logger

def run_simulated_user_tests():
    """Run comprehensive simulated user testing"""
    simulated_tester.create_test_scenarios()
    return simulated_tester.execute_simulated_testing()