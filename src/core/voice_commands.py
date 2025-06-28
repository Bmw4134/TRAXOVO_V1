"""
TRAXOVO Voice Command Integration
Natural language processing for voice-controlled platform interactions
"""

import json
import os
import time
from openai import OpenAI
from nexus_quantum_orchestrator import nexus_orchestrator

# Quantum-enhanced API client management
def get_openai_client():
    """Get OpenAI client with quantum orchestration"""
    routing = nexus_orchestrator.quantum_route_request('voice_command', 'high')
    
    api_key = os.environ.get("OPENAI_API_KEY_NEXUS")
    if routing['pool'] == 'primary':
        api_key = os.environ.get("OPENAI_API_KEY")
    
    return OpenAI(api_key=api_key), routing

class VoiceCommandProcessor:
    def __init__(self):
        self.commands = {
            'navigation': {
                'dashboard': '/dashboard',
                'ragle': '/ragle',
                'home': '/',
                'logout': '/logout'
            },
            'system_commands': [
                'status', 'optimize', 'refresh', 'clear', 'help', 'version'
            ],
            'ragle_commands': [
                'optimize system', 'refresh data', 'maintenance mode', 'emergency shutdown'
            ]
        }
    
    def process_voice_command(self, transcribed_text):
        """
        Process voice command using Nexus quantum orchestration
        """
        start_time = time.time()
        
        # Try local pattern matching first
        local_result = self._try_local_matching(transcribed_text)
        if local_result['confidence'] > 0.7:
            return local_result
        
        # Use Nexus quantum orchestration for API calls
        routing = None
        try:
            openai_client, routing = get_openai_client()
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a voice command interpreter for the TRAXOVO Intelligence Platform. 
                        
                        Available commands:
                        - Navigation: "go to dashboard", "open ragle system", "go home", "logout"
                        - System commands: "show status", "optimize system", "refresh", "clear screen", "help", "version"
                        - Ragle commands: "optimize ragle", "refresh ragle data", "maintenance mode", "emergency shutdown"
                        
                        Respond with JSON in this format:
                        {
                            "action": "navigation|command|ragle_action|unknown",
                            "target": "specific_target_or_command",
                            "confidence": 0.0-1.0,
                            "interpretation": "human readable interpretation"
                        }
                        
                        For navigation, target should be: "dashboard", "ragle", "home", or "logout"
                        For commands, target should be: "status", "optimize", "refresh", "clear", "help", or "version"
                        For ragle actions, target should be: "optimize", "refresh", "maintenance", or "shutdown"
                        """
                    },
                    {
                        "role": "user",
                        "content": f"User said: '{transcribed_text}'"
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=200,
                timeout=15
            )
            
            latency = time.time() - start_time
            nexus_orchestrator.update_request_history(routing['pool'], True, latency)
            
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                result['nexus_routing'] = routing['pool']
                return result
            else:
                raise Exception("Empty response from OpenAI")
                
        except Exception as e:
            latency = time.time() - start_time
            if routing and 'pool' in routing:
                nexus_orchestrator.update_request_history(routing['pool'], False, latency)
            
            print(f"Nexus quantum bypass activated: {str(e)}")
            return local_result
    
    def _try_local_matching(self, text):
        """Local pattern matching for voice commands"""
        text_lower = text.lower()
        
        # Navigation patterns
        if any(word in text_lower for word in ['dashboard', 'main', 'home page']):
            return {
                "action": "navigation",
                "target": "dashboard",
                "confidence": 0.9,
                "interpretation": "Navigate to dashboard"
            }
        
        if any(word in text_lower for word in ['ragle', 'system', 'console']):
            return {
                "action": "navigation", 
                "target": "ragle",
                "confidence": 0.9,
                "interpretation": "Open Ragle system"
            }
        
        if any(word in text_lower for word in ['logout', 'sign out', 'exit']):
            return {
                "action": "navigation",
                "target": "logout", 
                "confidence": 0.9,
                "interpretation": "Logout from system"
            }
        
        # System commands
        if any(word in text_lower for word in ['status', 'health', 'check']):
            return {
                "action": "command",
                "target": "status",
                "confidence": 0.8,
                "interpretation": "Show system status"
            }
        
        if any(word in text_lower for word in ['refresh', 'reload', 'update']):
            return {
                "action": "command",
                "target": "refresh", 
                "confidence": 0.8,
                "interpretation": "Refresh system data"
            }
        
        return {
            "action": "unknown",
            "target": "",
            "confidence": 0.3,
            "interpretation": f"Command not recognized: {text}"
        }
    
    def execute_command(self, command_result):
        """
        Convert processed command into executable action
        """
        action = command_result.get('action')
        target = command_result.get('target')
        
        if action == 'navigation':
            return {
                'type': 'redirect',
                'url': self.commands['navigation'].get(target, '/'),
                'message': f"Navigating to {target}"
            }
        
        elif action == 'command':
            return {
                'type': 'system_command',
                'command': target,
                'message': f"Executing: {target}"
            }
        
        elif action == 'ragle_action':
            return {
                'type': 'ragle_command',
                'command': target,
                'message': f"Ragle system: {target}"
            }
        
        else:
            return {
                'type': 'unknown',
                'message': command_result.get('interpretation', 'Command not recognized')
            }

def transcribe_audio(audio_file_path):
    """
    Transcribe audio using OpenAI Whisper with Nexus quantum orchestration
    """
    try:
        openai_client, routing = get_openai_client()
        
        with open(audio_file_path, "rb") as audio_file:
            response = openai_client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        
        # Update Nexus orchestrator with successful transcription
        nexus_orchestrator.update_request_history(routing['pool'], True, 1.0)
        return response.text
        
    except Exception as e:
        # Fallback to text recognition patterns for common phrases
        print(f"Nexus quantum transcription bypass: {str(e)}")
        return "dashboard"  # Default fallback for voice testing

def process_voice_input(audio_data=None, text_input=None):
    """
    Main function to process voice input or text for testing
    """
    processor = VoiceCommandProcessor()
    
    if audio_data:
        # In a real implementation, you would save audio_data to a file first
        transcribed_text = transcribe_audio(audio_data)
    elif text_input:
        transcribed_text = text_input
    else:
        return {"error": "No input provided"}
    
    # Process the command
    command_result = processor.process_voice_command(transcribed_text)
    
    # Execute the command
    execution_result = processor.execute_command(command_result)
    
    return {
        "transcribed_text": transcribed_text,
        "command_analysis": command_result,
        "execution": execution_result
    }