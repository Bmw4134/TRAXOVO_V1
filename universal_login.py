"""
Universal Login System for TRAXOVO
Simple access with task automation request form for stress testing
"""

from datetime import datetime
from app import db
from models_clean import PlatformData
import json

class UniversalLogin:
    """Simple login system for collecting user automation requests"""
    
    def __init__(self):
        self.basic_credentials = {
            'user': 'demo2025',
            'tester': 'test2025', 
            'beta': 'beta2025',
            'guest': 'guest2025',
            'trial': 'trial2025'
        }
    
    def authenticate_universal(self, username, password):
        """Universal authentication for stress testing"""
        
        # Check basic credentials
        if username in self.basic_credentials:
            if self.basic_credentials[username] == password:
                return {
                    'authenticated': True,
                    'user_type': 'universal',
                    'username': username,
                    'access_level': 'basic'
                }
        
        # Check existing admin credentials
        admin_accounts = {
            'admin': 'admin2025',
            'troy': 'troy2025', 
            'william': 'william2025',
            'executive': 'executive2025',
            'watson': 'watson2025',
            'demo': 'demo2025'
        }
        
        if username in admin_accounts:
            if admin_accounts[username] == password:
                return {
                    'authenticated': True,
                    'user_type': 'admin',
                    'username': username,
                    'access_level': 'full'
                }
        
        return {'authenticated': False}
    
    def save_automation_request(self, username, request_data):
        """Save user automation request for analysis"""
        
        try:
            automation_request = {
                'username': username,
                'task_title': request_data.get('task_title', ''),
                'task_description': request_data.get('task_description', ''),
                'task_category': request_data.get('task_category', 'general'),
                'priority_level': request_data.get('priority_level', 'medium'),
                'expected_frequency': request_data.get('expected_frequency', 'daily'),
                'data_sources_needed': request_data.get('data_sources_needed', []),
                'automation_complexity': request_data.get('automation_complexity', 'simple'),
                'business_impact': request_data.get('business_impact', ''),
                'current_manual_process': request_data.get('current_manual_process', ''),
                'success_criteria': request_data.get('success_criteria', ''),
                'submission_time': datetime.utcnow().isoformat(),
                'user_agent': request_data.get('user_agent', ''),
                'ip_address': request_data.get('ip_address', '')
            }
            
            # Store in database
            requests_record = PlatformData.query.filter_by(data_type='automation_requests').first()
            
            if requests_record:
                existing_requests = requests_record.data_content.get('requests', [])
                existing_requests.append(automation_request)
                requests_record.data_content = {'requests': existing_requests}
                requests_record.updated_at = datetime.utcnow()
            else:
                requests_record = PlatformData(
                    data_type='automation_requests',
                    data_content={'requests': [automation_request]}
                )
                db.session.add(requests_record)
            
            db.session.commit()
            
            return {
                'status': 'success',
                'message': 'Automation request submitted successfully',
                'request_id': len(requests_record.data_content['requests'])
            }
            
        except Exception as e:
            return {
                'status': 'error', 
                'message': f'Failed to save request: {str(e)}'
            }
    
    def get_automation_requests(self, username=None):
        """Get automation requests for analysis"""
        
        try:
            requests_record = PlatformData.query.filter_by(data_type='automation_requests').first()
            
            if not requests_record:
                return {'requests': [], 'total': 0}
            
            all_requests = requests_record.data_content.get('requests', [])
            
            # Filter by username if specified
            if username:
                filtered_requests = [r for r in all_requests if r.get('username') == username]
            else:
                filtered_requests = all_requests
            
            return {
                'requests': filtered_requests,
                'total': len(filtered_requests),
                'categories': self._analyze_request_categories(all_requests),
                'priority_distribution': self._analyze_priority_distribution(all_requests)
            }
            
        except Exception as e:
            return {'error': f'Failed to retrieve requests: {str(e)}'}
    
    def _analyze_request_categories(self, requests):
        """Analyze request categories for insights"""
        
        categories = {}
        for request in requests:
            category = request.get('task_category', 'general')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        return categories
    
    def _analyze_priority_distribution(self, requests):
        """Analyze priority distribution"""
        
        priorities = {}
        for request in requests:
            priority = request.get('priority_level', 'medium')
            if priority not in priorities:
                priorities[priority] = 0
            priorities[priority] += 1
        
        return priorities
    
    def generate_stress_test_analytics(self):
        """Generate analytics from stress test data"""
        
        try:
            requests_data = self.get_automation_requests()
            
            if requests_data.get('total', 0) == 0:
                return {
                    'message': 'No stress test data available yet',
                    'recommendations': ['Deploy universal login system', 'Collect user feedback']
                }
            
            requests = requests_data['requests']
            
            # Analyze common patterns
            common_tasks = {}
            data_source_requests = {}
            complexity_levels = {}
            
            for request in requests:
                # Task patterns
                task_title = request.get('task_title', '').lower()
                for word in task_title.split():
                    if len(word) > 3:  # Filter meaningful words
                        common_tasks[word] = common_tasks.get(word, 0) + 1
                
                # Data source analysis
                for source in request.get('data_sources_needed', []):
                    data_source_requests[source] = data_source_requests.get(source, 0) + 1
                
                # Complexity analysis
                complexity = request.get('automation_complexity', 'simple')
                complexity_levels[complexity] = complexity_levels.get(complexity, 0) + 1
            
            # Generate development recommendations
            recommendations = []
            
            # Top requested data sources
            if data_source_requests:
                top_data_source = max(data_source_requests, key=data_source_requests.get)
                recommendations.append(f"Prioritize {top_data_source} integration - {data_source_requests[top_data_source]} requests")
            
            # Complexity distribution insights
            if complexity_levels.get('complex', 0) > complexity_levels.get('simple', 0):
                recommendations.append("Focus on advanced automation capabilities - users need complex workflows")
            else:
                recommendations.append("Prioritize simple automation tools - users prefer straightforward solutions")
            
            # Common task patterns
            if common_tasks:
                top_task_word = max(common_tasks, key=common_tasks.get)
                recommendations.append(f"Build specialized tools for '{top_task_word}' tasks - mentioned {common_tasks[top_task_word]} times")
            
            return {
                'total_requests': len(requests),
                'common_task_patterns': dict(sorted(common_tasks.items(), key=lambda x: x[1], reverse=True)[:10]),
                'requested_data_sources': dict(sorted(data_source_requests.items(), key=lambda x: x[1], reverse=True)),
                'complexity_distribution': complexity_levels,
                'development_recommendations': recommendations,
                'priority_insights': requests_data.get('priority_distribution', {}),
                'category_insights': requests_data.get('categories', {})
            }
            
        except Exception as e:
            return {'error': f'Analytics generation failed: {str(e)}'}

# Global universal login instance
universal_login = UniversalLogin()

def authenticate_user(username, password):
    """Authenticate user with universal system"""
    return universal_login.authenticate_universal(username, password)

def save_user_automation_request(username, request_data):
    """Save automation request"""
    return universal_login.save_automation_request(username, request_data)

def get_stress_test_analytics():
    """Get stress test analytics"""
    return universal_login.generate_stress_test_analytics()

def get_user_requests(username=None):
    """Get automation requests"""
    return universal_login.get_automation_requests(username)