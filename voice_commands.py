"""
TRAXOVO Voice Command Integration
Natural language processing for voice-controlled platform interactions
"""

import json
import os
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
        Process voice command using OpenAI GPT-4o for natural language understanding
        """
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
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
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
            else:
                raise Exception("Empty response from OpenAI")
            return result
            
        except Exception as e:
            return {
                "action": "error",
                "target": None,
                "confidence": 0.0,
                "interpretation": f"Failed to process command: {str(e)}"
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
    Transcribe audio using OpenAI Whisper
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = openai_client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return response.text
    except Exception as e:
        raise Exception(f"Failed to transcribe audio: {e}")

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