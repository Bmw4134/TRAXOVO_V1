"""
NEXUS Intelligence Chat System
AI-powered chat interface for automation requests and user interaction
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, List

class NexusIntelligenceChat:
    """NEXUS Intelligence-powered chat system"""
    
    def __init__(self):
        self.chat_history = []
        self.automation_queue = []
        self.free_automations_used = {}
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        
    def process_chat_message(self, message: str, session_id: str = None) -> Dict:
        """Process incoming chat message with NEXUS Intelligence"""
        
        # Check if user has used free automation
        if session_id and session_id not in self.free_automations_used:
            self.free_automations_used[session_id] = 0
        
        # Enhanced NEXUS Intelligence prompt
        nexus_prompt = f"""
        You are NEXUS Intelligence™, an advanced AI automation specialist. You help users automate their tasks with precision and intelligence.
        
        User Message: "{message}"
        
        Analyze this message and respond with:
        1. A helpful, intelligent response about what automation you can provide
        2. If it's an automation request, break it down into actionable steps
        3. Suggest the best automation approach
        4. If this is their first interaction, offer a FREE automation trial
        
        Respond in a conversational, intelligent manner that showcases advanced AI capabilities.
        Keep responses concise but comprehensive.
        
        Current context: This user is on the NEXUS landing page exploring automation possibilities.
        """
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": nexus_prompt},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                ai_response = response.json()['choices'][0]['message']['content']
                
                # Detect if this is an automation request
                automation_detected = self.detect_automation_intent(message)
                
                chat_result = {
                    'response': ai_response,
                    'automation_detected': automation_detected,
                    'free_trial_available': session_id and self.free_automations_used.get(session_id, 0) == 0,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Log conversation
                self.log_conversation(session_id, message, ai_response, automation_detected)
                
                return chat_result
            else:
                return {
                    'response': "I'm experiencing high demand right now. Let me help you with automation using my built-in intelligence. What specific task would you like to automate?",
                    'automation_detected': self.detect_automation_intent(message),
                    'free_trial_available': True,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'response': "My NEXUS Intelligence is analyzing your request. What type of automation are you looking for? I can help with data processing, scheduling, communications, or custom workflows.",
                'automation_detected': self.detect_automation_intent(message),
                'free_trial_available': True,
                'timestamp': datetime.now().isoformat()
            }
    
    def detect_automation_intent(self, message: str) -> bool:
        """Detect if message contains automation intent"""
        automation_keywords = [
            'automate', 'automation', 'automatic', 'schedule', 'recurring',
            'workflow', 'process', 'task', 'job', 'batch', 'routine',
            'email', 'data', 'report', 'file', 'document', 'spreadsheet',
            'calendar', 'meeting', 'reminder', 'notification', 'alert'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in automation_keywords)
    
    def create_free_automation(self, session_id: str, automation_request: str) -> Dict:
        """Create a free automation for new users"""
        
        if self.free_automations_used.get(session_id, 0) >= 1:
            return {
                'success': False,
                'message': 'Free automation already used. Please sign up for more automations.',
                'require_signup': True
            }
        
        # Process the automation request
        automation_id = f"free_{session_id}_{int(time.time())}"
        
        automation_plan = {
            'id': automation_id,
            'session_id': session_id,
            'request': automation_request,
            'type': 'free_trial',
            'status': 'created',
            'steps': self.generate_automation_steps(automation_request),
            'created_at': datetime.now().isoformat(),
            'estimated_time': '5-10 minutes'
        }
        
        # Mark free automation as used
        self.free_automations_used[session_id] = 1
        
        # Save automation
        self.save_automation(automation_plan)
        
        return {
            'success': True,
            'automation_id': automation_id,
            'message': 'Free automation created! This will be implemented for you.',
            'steps': automation_plan['steps'],
            'next_action': 'We will process this automation and show you the results. For more advanced automations, please sign up.'
        }
    
    def generate_automation_steps(self, request: str) -> List[str]:
        """Generate automation steps based on request"""
        
        # Simple keyword-based step generation
        request_lower = request.lower()
        
        if 'email' in request_lower:
            return [
                "1. Set up email monitoring and filtering",
                "2. Create automated response templates", 
                "3. Configure scheduling rules",
                "4. Test automation workflow",
                "5. Deploy and monitor results"
            ]
        elif 'data' in request_lower or 'report' in request_lower:
            return [
                "1. Connect to data sources",
                "2. Set up data processing pipeline",
                "3. Create automated report generation",
                "4. Schedule regular updates",
                "5. Configure delivery methods"
            ]
        elif 'schedule' in request_lower or 'calendar' in request_lower:
            return [
                "1. Integrate with calendar systems",
                "2. Set up automated scheduling logic",
                "3. Configure notification preferences",
                "4. Create conflict resolution rules",
                "5. Test and deploy automation"
            ]
        else:
            return [
                "1. Analyze automation requirements",
                "2. Design custom workflow logic",
                "3. Set up necessary integrations",
                "4. Configure monitoring and alerts",
                "5. Deploy and optimize automation"
            ]
    
    def save_automation(self, automation_plan: Dict):
        """Save automation to file"""
        try:
            os.makedirs('config', exist_ok=True)
            
            # Load existing automations
            automations_file = 'config/free_automations.json'
            if os.path.exists(automations_file):
                with open(automations_file, 'r') as f:
                    automations = json.load(f)
            else:
                automations = []
            
            automations.append(automation_plan)
            
            # Keep only last 100 automations
            if len(automations) > 100:
                automations = automations[-100:]
            
            with open(automations_file, 'w') as f:
                json.dump(automations, f, indent=2)
                
        except Exception as e:
            print(f"Error saving automation: {e}")
    
    def log_conversation(self, session_id: str, user_message: str, ai_response: str, automation_detected: bool):
        """Log conversation for analytics"""
        try:
            os.makedirs('logs', exist_ok=True)
            
            log_entry = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'user_message': user_message,
                'ai_response': ai_response,
                'automation_detected': automation_detected,
                'free_trial_used': self.free_automations_used.get(session_id, 0) > 0
            }
            
            log_file = 'logs/chat_conversations.json'
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Keep only last 1000 conversations
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"Error logging conversation: {e}")
    
    def get_chat_analytics(self) -> Dict:
        """Get chat analytics for admin dashboard"""
        try:
            log_file = 'logs/chat_conversations.json'
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
                
                total_conversations = len(logs)
                automation_requests = sum(1 for log in logs if log.get('automation_detected', False))
                free_trials_used = sum(1 for log in logs if log.get('free_trial_used', False))
                
                return {
                    'total_conversations': total_conversations,
                    'automation_requests': automation_requests,
                    'free_trials_used': free_trials_used,
                    'conversion_rate': (free_trials_used / total_conversations * 100) if total_conversations > 0 else 0
                }
            
            return {
                'total_conversations': 0,
                'automation_requests': 0,
                'free_trials_used': 0,
                'conversion_rate': 0
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_conversations': 0,
                'automation_requests': 0,
                'free_trials_used': 0,
                'conversion_rate': 0
            }

# Global chat instance
nexus_chat = NexusIntelligenceChat()

def process_chat_message(message: str, session_id: str = None):
    """Process chat message"""
    return nexus_chat.process_chat_message(message, session_id)

def create_free_automation(session_id: str, automation_request: str):
    """Create free automation"""
    return nexus_chat.create_free_automation(session_id, automation_request)

def get_chat_analytics():
    """Get chat analytics"""
    return nexus_chat.get_chat_analytics()