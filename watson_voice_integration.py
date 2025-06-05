"""
Watson Voice Command Integration
Advanced speech recognition and natural language processing for Watson Console
"""
import json
import os
from datetime import datetime
import speech_recognition as sr
import pyttsx3
import threading
import queue

class WatsonVoiceEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        self.command_queue = queue.Queue()
        self.is_listening = False
        self.supported_languages = ['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE']
        self.current_language = 'en-US'
        
        # Configure TTS
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.8)
        
    def start_listening(self):
        """Start continuous voice recognition"""
        self.is_listening = True
        threading.Thread(target=self._listen_continuously, daemon=True).start()
        return {'status': 'listening_started', 'language': self.current_language}
    
    def stop_listening(self):
        """Stop voice recognition"""
        self.is_listening = False
        return {'status': 'listening_stopped'}
    
    def _listen_continuously(self):
        """Continuous listening thread"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        while self.is_listening:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                try:
                    command = self.recognizer.recognize_google(audio, language=self.current_language)
                    if self._is_watson_command(command):
                        processed_command = self._process_voice_command(command)
                        self.command_queue.put(processed_command)
                except sr.UnknownValueError:
                    pass  # No speech detected
                except sr.RequestError:
                    pass  # API unavailable
            except sr.WaitTimeoutError:
                pass  # Continue listening
    
    def _is_watson_command(self, command):
        """Check if command is directed to Watson"""
        wake_words = ['watson', 'computer', 'system']
        return any(word in command.lower() for word in wake_words)
    
    def _process_voice_command(self, command):
        """Process and categorize voice command"""
        command_lower = command.lower()
        
        # Command categories
        if any(word in command_lower for word in ['analyze', 'analysis', 'diagnostic']):
            return {
                'type': 'analysis',
                'command': command,
                'action': 'system_analysis',
                'timestamp': datetime.now().isoformat()
            }
        elif any(word in command_lower for word in ['deploy', 'deployment', 'launch']):
            return {
                'type': 'deployment',
                'command': command,
                'action': 'deployment_check',
                'timestamp': datetime.now().isoformat()
            }
        elif any(word in command_lower for word in ['monitor', 'status', 'health']):
            return {
                'type': 'monitoring',
                'command': command,
                'action': 'system_monitor',
                'timestamp': datetime.now().isoformat()
            }
        elif any(word in command_lower for word in ['emergency', 'fix', 'repair']):
            return {
                'type': 'emergency',
                'command': command,
                'action': 'emergency_fix',
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'type': 'general',
                'command': command,
                'action': 'general_command',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_pending_commands(self):
        """Get all pending voice commands"""
        commands = []
        while not self.command_queue.empty():
            commands.append(self.command_queue.get())
        return commands
    
    def speak_response(self, text):
        """Convert text to speech"""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            return {'status': 'speech_completed'}
        except Exception as e:
            return {'status': 'speech_failed', 'error': str(e)}
    
    def change_language(self, language_code):
        """Change recognition language"""
        if language_code in self.supported_languages:
            self.current_language = language_code
            return {'status': 'language_changed', 'new_language': language_code}
        else:
            return {'status': 'language_not_supported', 'supported': self.supported_languages}
    
    def get_voice_analytics(self):
        """Get voice system analytics"""
        return {
            'listening_status': self.is_listening,
            'current_language': self.current_language,
            'supported_languages': self.supported_languages,
            'pending_commands': self.command_queue.qsize(),
            'microphone_available': self._check_microphone(),
            'tts_available': self._check_tts(),
            'last_update': datetime.now().isoformat()
        }
    
    def _check_microphone(self):
        """Check if microphone is available"""
        try:
            with self.microphone as source:
                pass
            return True
        except:
            return False
    
    def _check_tts(self):
        """Check if TTS engine is available"""
        try:
            return self.tts_engine is not None
        except:
            return False

# Global voice engine instance
_voice_engine = None

def get_voice_engine():
    """Get global voice engine instance"""
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = WatsonVoiceEngine()
    return _voice_engine

def start_voice_recognition():
    """Start voice recognition"""
    engine = get_voice_engine()
    return engine.start_listening()

def stop_voice_recognition():
    """Stop voice recognition"""
    engine = get_voice_engine()
    return engine.stop_listening()

def get_voice_commands():
    """Get pending voice commands"""
    engine = get_voice_engine()
    return engine.get_pending_commands()

def speak_watson_response(text):
    """Watson text-to-speech response"""
    engine = get_voice_engine()
    return engine.speak_response(text)

def get_voice_analytics():
    """Get voice system analytics"""
    engine = get_voice_engine()
    return engine.get_voice_analytics()

def change_voice_language(language_code):
    """Change voice recognition language"""
    engine = get_voice_engine()
    return engine.change_language(language_code)