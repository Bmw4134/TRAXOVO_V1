"""
NEXUS Core Platform
Automation Request Collection and Development Intelligence
"""

from datetime import datetime
from app import db
from models_clean import PlatformData

class NexusCore:
    """Core automation intelligence platform"""
    
    def __init__(self):
        self.platform_name = "NEXUS"
        self.mission = "Collect automation requests and convert to development insights"
        self.features = [
            "secure_intake_forms",
            "email_distribution", 
            "sms_distribution",
            "development_analytics",
            "user_feedback_collection"
        ]
    
    def get_platform_status(self):
        """Get current platform operational status"""
        
        try:
            # Check intake responses
            responses_record = PlatformData.query.filter_by(data_type='intake_responses').first()
            total_responses = 0
            if responses_record:
                total_responses = len(responses_record.data_content.get('responses', []))
            
            # Check distribution logs
            log_record = PlatformData.query.filter_by(data_type='intake_distribution_log').first()
            total_distributions = 0
            if log_record:
                total_distributions = len(log_record.data_content.get('logs', []))
            
            status = {
                'platform': 'NEXUS',
                'status': 'operational',
                'total_intake_forms_sent': total_distributions,
                'total_responses_collected': total_responses,
                'response_rate': f"{(total_responses/total_distributions*100):.1f}%" if total_distributions > 0 else "0%",
                'development_insights_available': total_responses > 0,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return status
            
        except Exception as e:
            return {
                'platform': 'NEXUS',
                'status': 'error',
                'message': str(e)
            }
    
    def get_automation_categories(self):
        """Get automation request categories from collected data"""
        
        try:
            responses_record = PlatformData.query.filter_by(data_type='intake_responses').first()
            
            if not responses_record:
                return {
                    'categories': [],
                    'message': 'No automation requests collected yet'
                }
            
            responses = responses_record.data_content.get('responses', [])
            
            category_analysis = {}
            priority_analysis = {}
            frequency_analysis = {}
            
            for response in responses:
                response_data = response.get('responses', {})
                
                # Category analysis
                category = response_data.get('task_category', 'other')
                category_analysis[category] = category_analysis.get(category, 0) + 1
                
                # Priority analysis
                priority = response_data.get('priority_level', 'medium')
                priority_analysis[priority] = priority_analysis.get(priority, 0) + 1
                
                # Frequency analysis
                frequency = response_data.get('expected_frequency', 'weekly')
                frequency_analysis[frequency] = frequency_analysis.get(frequency, 0) + 1
            
            return {
                'total_requests': len(responses),
                'categories': category_analysis,
                'priorities': priority_analysis,
                'frequencies': frequency_analysis,
                'top_category': max(category_analysis, key=category_analysis.get) if category_analysis else None,
                'top_priority': max(priority_analysis, key=priority_analysis.get) if priority_analysis else None
            }
            
        except Exception as e:
            return {'error': f'Category analysis failed: {str(e)}'}
    
    def get_development_roadmap(self):
        """Generate development roadmap from automation requests"""
        
        try:
            responses_record = PlatformData.query.filter_by(data_type='intake_responses').first()
            
            if not responses_record:
                return {
                    'roadmap': [],
                    'message': 'Collect automation requests first to generate roadmap'
                }
            
            responses = responses_record.data_content.get('responses', [])
            
            # Analyze requests for development priorities
            feature_requests = {}
            data_source_needs = {}
            complexity_distribution = {}
            
            for response in responses:
                response_data = response.get('responses', {})
                insights = response.get('development_insights', {})
                
                # Count feature requests
                for feature in insights.get('priority_features', []):
                    feature_requests[feature] = feature_requests.get(feature, 0) + 1
                
                # Count data source needs
                for source in response_data.get('data_sources', []):
                    data_source_needs[source] = data_source_needs.get(source, 0) + 1
                
                # Analyze complexity
                task_desc = response_data.get('task_description', '').lower()
                if any(word in task_desc for word in ['complex', 'advanced', 'integration']):
                    complexity_distribution['complex'] = complexity_distribution.get('complex', 0) + 1
                else:
                    complexity_distribution['simple'] = complexity_distribution.get('simple', 0) + 1
            
            # Generate roadmap
            roadmap = []
            
            if feature_requests:
                top_feature = max(feature_requests, key=feature_requests.get)
                roadmap.append({
                    'priority': 1,
                    'item': f'Build {top_feature.replace("_", " ").title()}',
                    'demand': feature_requests[top_feature],
                    'type': 'feature'
                })
            
            if data_source_needs:
                top_data_source = max(data_source_needs, key=data_source_needs.get)
                roadmap.append({
                    'priority': 2,
                    'item': f'Integrate {top_data_source.replace("_", " ").title()} connectivity',
                    'demand': data_source_needs[top_data_source],
                    'type': 'integration'
                })
            
            # Add complexity-based recommendations
            if complexity_distribution.get('complex', 0) > complexity_distribution.get('simple', 0):
                roadmap.append({
                    'priority': 3,
                    'item': 'Develop advanced workflow engine for complex automations',
                    'demand': complexity_distribution['complex'],
                    'type': 'infrastructure'
                })
            else:
                roadmap.append({
                    'priority': 3,
                    'item': 'Focus on simple automation tools for quick wins',
                    'demand': complexity_distribution.get('simple', 0),
                    'type': 'infrastructure'
                })
            
            return {
                'roadmap': roadmap,
                'total_requests_analyzed': len(responses),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Roadmap generation failed: {str(e)}'}
    
    def get_user_feedback_summary(self):
        """Get summary of user feedback for development team"""
        
        try:
            responses_record = PlatformData.query.filter_by(data_type='intake_responses').first()
            
            if not responses_record:
                return {
                    'summary': 'No user feedback collected yet',
                    'action_needed': 'Deploy intake forms to collect feedback'
                }
            
            responses = responses_record.data_content.get('responses', [])
            
            # Extract key feedback themes
            common_tasks = []
            business_impacts = []
            success_criteria = []
            
            for response in responses:
                response_data = response.get('responses', {})
                
                task_title = response_data.get('task_title', '')
                if task_title:
                    common_tasks.append(task_title)
                
                business_impact = response_data.get('business_impact', '')
                if business_impact:
                    business_impacts.append(business_impact)
                
                success = response_data.get('success_criteria', '')
                if success:
                    success_criteria.append(success)
            
            return {
                'total_feedback_items': len(responses),
                'common_automation_requests': common_tasks[:10],  # Top 10
                'business_impact_themes': business_impacts[:5],   # Top 5
                'success_criteria_examples': success_criteria[:5], # Top 5
                'last_response_at': responses[-1].get('submission_time') if responses else None,
                'summary': f'Collected {len(responses)} automation requests from users'
            }
            
        except Exception as e:
            return {'error': f'Feedback summary failed: {str(e)}'}

# Global Nexus instance
nexus = NexusCore()

def get_nexus_status():
    """Get Nexus platform status"""
    return nexus.get_platform_status()

def get_automation_analytics():
    """Get automation request analytics"""
    return nexus.get_automation_categories()

def get_development_roadmap():
    """Get development roadmap"""
    return nexus.get_development_roadmap()

def get_user_feedback():
    """Get user feedback summary"""
    return nexus.get_user_feedback_summary()