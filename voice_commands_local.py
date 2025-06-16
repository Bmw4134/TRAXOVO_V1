"""
TRAXOVO Voice Command Integration - Local Pattern Matching
Natural language processing for voice-controlled platform interactions without external APIs
"""

import json
import re

class VoiceCommandProcessor:
    def __init__(self):
        self.navigation_patterns = {
            'dashboard': ['dashboard', 'main', 'home', 'go home'],
            'ragle': ['ragle', 'ragle system', 'processing units', 'control center'],
            'attendance': ['attendance', 'attendance matrix', 'time tracking'],
            'equipment': ['equipment', 'billing', 'equipment billing', 'costs'],
            'jobzones': ['job zones', 'zones', 'work areas'],
            'geofences': ['geofences', 'boundaries', 'location tracking']
        }
        
        self.system_patterns = {
            'status': ['status', 'system status', 'show status', 'health check'],
            'help': ['help', 'commands', 'what can you do', 'available commands'],
            'optimize': ['optimize', 'optimize system', 'improve performance'],
            'refresh': ['refresh', 'reload', 'update data'],
            'clear': ['clear', 'clear screen', 'reset display'],
            'version': ['version', 'system version', 'build info']
        }
    
    def process_voice_command(self, transcribed_text):
        """
        Process voice command using local pattern matching
        """
        text_clean = transcribed_text.lower().strip()
        
        # Check navigation commands
        nav_result = self._match_navigation(text_clean)
        if nav_result:
            return nav_result
        
        # Check system commands
        sys_result = self._match_system_command(text_clean)
        if sys_result:
            return sys_result
        
        # Fallback for unrecognized commands
        return {
            'command_analysis': {
                'intent': 'unknown',
                'target': 'unknown',
                'interpretation': f'Command not recognized: {transcribed_text}'
            },
            'execution': {
                'type': 'message',
                'message': f'Command received but not understood: {transcribed_text}'
            }
        }
    
    def _match_navigation(self, text):
        """Match navigation commands"""
        for target, patterns in self.navigation_patterns.items():
            for pattern in patterns:
                if pattern in text or any(word in text for word in pattern.split()):
                    url_map = {
                        'dashboard': '/dashboard',
                        'ragle': '/ragle',
                        'attendance': '/attendance',
                        'equipment': '/equipment',
                        'jobzones': '/jobzones', 
                        'geofences': '/geofences'
                    }
                    
                    return {
                        'command_analysis': {
                            'intent': 'navigation',
                            'target': target,
                            'interpretation': f'Navigate to {target.title()}'
                        },
                        'execution': {
                            'type': 'redirect',
                            'url': url_map[target],
                            'message': f'Opening {target.title()}...'
                        }
                    }
        return None
    
    def _match_system_command(self, text):
        """Match system commands"""
        for command, patterns in self.system_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return {
                        'command_analysis': {
                            'intent': 'system_command',
                            'target': command,
                            'interpretation': f'Execute {command} command'
                        },
                        'execution': {
                            'type': 'system_command',
                            'command': command,
                            'message': f'Executing {command} command...'
                        }
                    }
        return None

def process_voice_input(audio_data=None, text_input=None):
    """
    Main function to process voice input without external APIs
    """
    if text_input:
        processor = VoiceCommandProcessor()
        return processor.process_voice_command(text_input)
    
    return {
        'command_analysis': {
            'intent': 'error',
            'target': 'none',
            'interpretation': 'No text input provided'
        },
        'execution': {
            'type': 'message',
            'message': 'Please provide text input for processing'
        }
    }