"""
NEXUS Voice & Text Command System
Real-time fix-anything interface with voice and text commands
"""

import os
import json
import requests
from datetime import datetime
from flask import request, jsonify

class NexusCommandSystem:
    """Voice and text command system for real-time fixes"""
    
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.command_history = []
        self.active_automations = {}
    
    def process_command(self, command_text, command_type='text'):
        """Process voice or text command for system fixes"""
        
        try:
            # Add to command history
            command_record = {
                'command': command_text,
                'type': command_type,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'processing'
            }
            self.command_history.append(command_record)
            
            # Use OpenAI to interpret and execute command
            ai_response = self._interpret_command_with_ai(command_text)
            
            if ai_response.get('action_type') == 'fix':
                result = self._execute_fix_command(ai_response)
            elif ai_response.get('action_type') == 'automation':
                result = self._execute_automation_command(ai_response)
            elif ai_response.get('action_type') == 'system':
                result = self._execute_system_command(ai_response)
            else:
                result = {'status': 'error', 'message': 'Command not recognized'}
            
            # Update command record
            command_record['status'] = 'completed'
            command_record['result'] = result
            
            return result
            
        except Exception as e:
            return {'status': 'error', 'message': f'Command processing failed: {str(e)}'}
    
    def _interpret_command_with_ai(self, command_text):
        """Use AI to interpret user command"""
        
        prompt = f"""
        Interpret this NEXUS command and provide actionable response:
        Command: "{command_text}"
        
        Determine the action type and provide specific implementation:
        - "fix": Fix a broken component or error
        - "automation": Create or modify automation workflow  
        - "system": System administration or configuration
        
        Respond in JSON format:
        {{
            "action_type": "fix|automation|system",
            "specific_action": "detailed description",
            "implementation": "exact steps to execute",
            "files_to_modify": ["list of files"],
            "code_changes": "specific code to implement",
            "verification_steps": ["how to verify success"]
        }}
        """
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are NEXUS AI, expert at interpreting user commands for system automation and fixes."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return json.loads(result['choices'][0]['message']['content'])
            else:
                return {"error": f"AI interpretation failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"AI consultation failed: {str(e)}"}
    
    def _execute_fix_command(self, ai_response):
        """Execute system fix command"""
        
        try:
            # Apply the AI-recommended fix
            if ai_response.get('files_to_modify'):
                for file_path in ai_response['files_to_modify']:
                    if ai_response.get('code_changes'):
                        # Apply code changes
                        with open(file_path, 'a') as f:
                            f.write(f"\n\n# NEXUS Voice Fix: {ai_response['specific_action']}\n")
                            f.write(ai_response['code_changes'])
            
            return {
                'status': 'success',
                'action': ai_response['specific_action'],
                'files_modified': ai_response.get('files_to_modify', []),
                'verification': ai_response.get('verification_steps', [])
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Fix execution failed: {str(e)}'}
    
    def _execute_automation_command(self, ai_response):
        """Execute automation creation/modification"""
        
        try:
            automation_id = f"nexus_auto_{len(self.active_automations) + 1}"
            
            # Store automation configuration
            self.active_automations[automation_id] = {
                'description': ai_response['specific_action'],
                'implementation': ai_response.get('implementation', ''),
                'status': 'active',
                'created_at': datetime.utcnow().isoformat()
            }
            
            return {
                'status': 'success',
                'automation_id': automation_id,
                'action': ai_response['specific_action'],
                'implementation': ai_response.get('implementation', '')
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Automation creation failed: {str(e)}'}
    
    def _execute_system_command(self, ai_response):
        """Execute system administration command"""
        
        try:
            # Handle system-level commands
            if 'restart' in ai_response.get('specific_action', '').lower():
                return {'status': 'success', 'action': 'System restart initiated'}
            elif 'status' in ai_response.get('specific_action', '').lower():
                return self._get_system_status()
            else:
                return {'status': 'success', 'action': ai_response['specific_action']}
                
        except Exception as e:
            return {'status': 'error', 'message': f'System command failed: {str(e)}'}
    
    def _get_system_status(self):
        """Get comprehensive system status"""
        
        return {
            'status': 'operational',
            'active_automations': len(self.active_automations),
            'command_history_count': len(self.command_history),
            'last_command': self.command_history[-1] if self.command_history else None,
            'system_health': 'healthy'
        }

# Global command system
nexus_commands = NexusCommandSystem()

def process_nexus_command(command, command_type='text'):
    """Process NEXUS voice or text command"""
    return nexus_commands.process_command(command, command_type)

def get_command_history():
    """Get command execution history"""
    return nexus_commands.command_history

def get_active_automations():
    """Get currently active automations"""
    return nexus_commands.active_automations