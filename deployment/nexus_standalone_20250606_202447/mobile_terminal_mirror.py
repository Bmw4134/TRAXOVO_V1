"""
NEXUS Mobile Terminal Mirror
Real-time iPhone AI input/output mirroring with voice+text injection
"""

import os
import json
import time
import asyncio
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
import speech_recognition as sr
import logging

class MobileTerminalMirror:
    """Real-time iPhone terminal mirroring system"""
    
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.active_sessions = {}
        self.terminal_buffer = []
        self.voice_recognizer = sr.Recognizer()
        self.setup_routes()
        
    def setup_routes(self):
        """Setup mobile terminal routes"""
        
        @self.app.route('/mobile-terminal')
        def mobile_terminal():
            """Mobile-optimized terminal interface"""
            return render_template_string(self.get_mobile_terminal_html())
        
        @self.app.route('/api/mobile/voice-input', methods=['POST'])
        def process_voice_input():
            """Process voice input from mobile device"""
            try:
                audio_data = request.files.get('audio')
                session_id = request.form.get('session_id', f'mobile_{int(time.time())}')
                
                if audio_data:
                    # Process voice input
                    text_result = self.process_voice_to_text(audio_data)
                    
                    # Log and relay to AI system
                    self.log_mobile_input(session_id, 'voice', text_result)
                    ai_response = self.relay_to_ai_system(text_result, session_id)
                    
                    # Broadcast to connected terminals
                    self.socketio.emit('mobile_voice_input', {
                        'session_id': session_id,
                        'input_type': 'voice',
                        'text': text_result,
                        'ai_response': ai_response,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    return jsonify({
                        'success': True,
                        'transcribed_text': text_result,
                        'ai_response': ai_response
                    })
                
                return jsonify({'success': False, 'error': 'No audio data received'})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/mobile/text-input', methods=['POST'])
        def process_text_input():
            """Process text input from mobile device"""
            try:
                data = request.get_json()
                text_input = data.get('text', '')
                session_id = data.get('session_id', f'mobile_{int(time.time())}')
                
                # Log and relay to AI system
                self.log_mobile_input(session_id, 'text', text_input)
                ai_response = self.relay_to_ai_system(text_input, session_id)
                
                # Broadcast to connected terminals
                self.socketio.emit('mobile_text_input', {
                    'session_id': session_id,
                    'input_type': 'text',
                    'text': text_input,
                    'ai_response': ai_response,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                return jsonify({
                    'success': True,
                    'ai_response': ai_response
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/mobile/terminal-status')
        def get_terminal_status():
            """Get current terminal status"""
            return jsonify({
                'active_sessions': len(self.active_sessions),
                'terminal_buffer_size': len(self.terminal_buffer),
                'last_activity': self.get_last_activity(),
                'ai_relay_status': self.check_ai_relay_status()
            })
    
    def process_voice_to_text(self, audio_file):
        """Convert voice audio to text"""
        try:
            # Save temporary audio file
            temp_path = f"/tmp/voice_input_{int(time.time())}.wav"
            audio_file.save(temp_path)
            
            # Process with speech recognition
            with sr.AudioFile(temp_path) as source:
                audio = self.voice_recognizer.record(source)
                text = self.voice_recognizer.recognize_google(audio)
            
            # Clean up temp file
            os.remove(temp_path)
            
            return text
            
        except Exception as e:
            logging.error(f"Voice processing error: {e}")
            return f"[Voice processing error: {str(e)}]"
    
    def relay_to_ai_system(self, text_input, session_id):
        """Relay input to AI system and get response"""
        try:
            from nexus_infinity_core import NexusInfinityCore
            
            nexus_core = NexusInfinityCore()
            
            # Process through NEXUS AI system
            ai_result = nexus_core.process_autonomous_command(text_input, session_id)
            
            return ai_result.get('response', 'AI processing complete')
            
        except Exception as e:
            logging.error(f"AI relay error: {e}")
            return f"[AI relay error: {str(e)}]"
    
    def log_mobile_input(self, session_id, input_type, content):
        """Log mobile input to database"""
        try:
            from app_nexus import db, PlatformData
            
            log_entry = PlatformData()
            log_entry.data_type = 'mobile_terminal_log'
            log_entry.data_content = {
                'session_id': session_id,
                'input_type': input_type,
                'content': content,
                'timestamp': datetime.utcnow().isoformat(),
                'device_type': 'mobile'
            }
            
            db.session.add(log_entry)
            db.session.commit()
            
            # Add to terminal buffer
            self.terminal_buffer.append({
                'session_id': session_id,
                'type': input_type,
                'content': content,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Keep buffer size manageable
            if len(self.terminal_buffer) > 1000:
                self.terminal_buffer = self.terminal_buffer[-500:]
            
        except Exception as e:
            logging.error(f"Logging error: {e}")
    
    def get_last_activity(self):
        """Get timestamp of last activity"""
        if self.terminal_buffer:
            return self.terminal_buffer[-1]['timestamp']
        return None
    
    def check_ai_relay_status(self):
        """Check AI relay system status"""
        try:
            from nexus_core import get_trinity_sync_status
            sync_status = get_trinity_sync_status()
            return sync_status.get('trinity_sync_achieved', False)
        except:
            return False
    
    def get_mobile_terminal_html(self):
        """Generate mobile-optimized terminal HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS Mobile Terminal</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            background: #000;
            color: #00ff00;
            padding: 10px;
            min-height: 100vh;
            font-size: 14px;
        }
        .header {
            text-align: center;
            padding: 15px 0;
            border-bottom: 1px solid #00ff00;
            margin-bottom: 15px;
        }
        .header h1 {
            font-size: 18px;
            color: #00ff00;
            text-shadow: 0 0 10px #00ff00;
        }
        .terminal {
            background: #111;
            border: 1px solid #00ff00;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            height: 300px;
            overflow-y: auto;
            font-size: 12px;
        }
        .input-section {
            background: #111;
            border: 1px solid #00ff00;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .input-group {
            margin-bottom: 15px;
        }
        .input-group input, .input-group textarea {
            width: 100%;
            padding: 12px;
            background: #222;
            border: 1px solid #00ff00;
            color: #00ff00;
            border-radius: 4px;
            font-family: inherit;
            font-size: 14px;
        }
        .input-group textarea {
            height: 80px;
            resize: vertical;
        }
        .btn {
            background: #003300;
            border: 1px solid #00ff00;
            color: #00ff00;
            padding: 12px 20px;
            cursor: pointer;
            border-radius: 4px;
            margin: 5px;
            font-size: 14px;
            width: calc(50% - 10px);
            display: inline-block;
            text-align: center;
        }
        .btn:active {
            background: #00ff00;
            color: #000;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .status-bar {
            background: #111;
            border: 1px solid #00ff00;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 15px;
            font-size: 12px;
        }
        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
            border-left: 2px solid #00ff00;
            padding-left: 10px;
        }
        .voice-input { border-left-color: #ffff00; }
        .text-input { border-left-color: #00ffff; }
        .ai-response { border-left-color: #ff00ff; }
        .recording {
            background: #330000;
            border-color: #ff0000;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .connection-status {
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
        }
        .connected { background: #003300; border: 1px solid #00ff00; }
        .disconnected { background: #330000; border: 1px solid #ff0000; }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">Connecting...</div>
    
    <div class="header">
        <h1>NEXUS MOBILE TERMINAL</h1>
        <p>Real-time AI Input/Output Mirror</p>
    </div>

    <div class="status-bar">
        <div>Session ID: <span id="sessionId">mobile_{{timestamp}}</span></div>
        <div>AI Relay: <span id="aiRelayStatus">Checking...</span></div>
        <div>Last Activity: <span id="lastActivity">--</span></div>
    </div>

    <div class="terminal" id="terminal">
        <div class="log-entry">[{{timestamp}}] NEXUS Mobile Terminal initialized</div>
        <div class="log-entry">[{{timestamp}}] Voice and text input ready</div>
        <div class="log-entry">[{{timestamp}}] AI relay system connected</div>
    </div>

    <div class="input-section">
        <div class="input-group">
            <textarea id="textInput" placeholder="Enter command or question..."></textarea>
        </div>
        <div>
            <button class="btn" onclick="sendTextInput()">Send Text</button>
            <button class="btn" id="voiceBtn" onclick="toggleVoiceRecording()">Start Voice</button>
        </div>
    </div>

    <script>
        const socket = io();
        let isRecording = false;
        let mediaRecorder = null;
        let sessionId = 'mobile_' + Date.now();
        
        document.getElementById('sessionId').textContent = sessionId;

        // Socket connection events
        socket.on('connect', () => {
            updateConnectionStatus(true);
            addLog('Connected to NEXUS relay system', 'system');
        });

        socket.on('disconnect', () => {
            updateConnectionStatus(false);
            addLog('Disconnected from NEXUS relay system', 'system');
        });

        socket.on('mobile_voice_input', (data) => {
            addLog(`Voice: ${data.text}`, 'voice-input');
            addLog(`AI: ${data.ai_response}`, 'ai-response');
            updateLastActivity();
        });

        socket.on('mobile_text_input', (data) => {
            addLog(`Text: ${data.text}`, 'text-input');
            addLog(`AI: ${data.ai_response}`, 'ai-response');
            updateLastActivity();
        });

        function updateConnectionStatus(connected) {
            const status = document.getElementById('connectionStatus');
            if (connected) {
                status.textContent = 'Connected';
                status.className = 'connection-status connected';
            } else {
                status.textContent = 'Disconnected';
                status.className = 'connection-status disconnected';
            }
        }

        function addLog(message, type = '') {
            const terminal = document.getElementById('terminal');
            const timestamp = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            entry.textContent = `[${timestamp}] ${message}`;
            terminal.appendChild(entry);
            terminal.scrollTop = terminal.scrollHeight;
        }

        function updateLastActivity() {
            document.getElementById('lastActivity').textContent = new Date().toLocaleTimeString();
        }

        async function sendTextInput() {
            const textInput = document.getElementById('textInput');
            const text = textInput.value.trim();
            
            if (!text) return;
            
            try {
                addLog(`Sending: ${text}`, 'text-input');
                
                const response = await fetch('/api/mobile/text-input', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: text,
                        session_id: sessionId
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    textInput.value = '';
                    addLog(`AI: ${result.ai_response}`, 'ai-response');
                } else {
                    addLog(`Error: ${result.error}`, 'error');
                }
                
            } catch (error) {
                addLog(`Network error: ${error.message}`, 'error');
            }
        }

        async function toggleVoiceRecording() {
            if (!isRecording) {
                await startVoiceRecording();
            } else {
                stopVoiceRecording();
            }
        }

        async function startVoiceRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                let audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    await sendVoiceInput(audioBlob);
                    
                    // Clean up
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start();
                isRecording = true;
                
                const voiceBtn = document.getElementById('voiceBtn');
                voiceBtn.textContent = 'Stop Voice';
                voiceBtn.classList.add('recording');
                
                addLog('Voice recording started...', 'voice-input');
                
            } catch (error) {
                addLog(`Voice recording error: ${error.message}`, 'error');
            }
        }

        function stopVoiceRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                
                const voiceBtn = document.getElementById('voiceBtn');
                voiceBtn.textContent = 'Start Voice';
                voiceBtn.classList.remove('recording');
                
                addLog('Voice recording stopped, processing...', 'voice-input');
            }
        }

        async function sendVoiceInput(audioBlob) {
            try {
                const formData = new FormData();
                formData.append('audio', audioBlob, 'voice_input.wav');
                formData.append('session_id', sessionId);
                
                const response = await fetch('/api/mobile/voice-input', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    addLog(`Voice → Text: ${result.transcribed_text}`, 'voice-input');
                    addLog(`AI: ${result.ai_response}`, 'ai-response');
                } else {
                    addLog(`Voice processing error: ${result.error}`, 'error');
                }
                
            } catch (error) {
                addLog(`Voice upload error: ${error.message}`, 'error');
            }
        }

        // Auto-refresh status
        setInterval(async () => {
            try {
                const response = await fetch('/api/mobile/terminal-status');
                const status = await response.json();
                
                document.getElementById('aiRelayStatus').textContent = 
                    status.ai_relay_status ? 'Connected' : 'Disconnected';
                
                if (status.last_activity) {
                    document.getElementById('lastActivity').textContent = 
                        new Date(status.last_activity).toLocaleTimeString();
                }
                
            } catch (error) {
                console.error('Status update error:', error);
            }
        }, 10000);

        // Initialize timestamp placeholder
        document.querySelectorAll('[id="timestamp"]').forEach(el => {
            el.textContent = new Date().toLocaleTimeString();
        });
    </script>
</body>
</html>
        """.replace('{{timestamp}}', datetime.utcnow().strftime('%H:%M:%S'))


def setup_mobile_terminal_mirror(app, socketio):
    """Setup mobile terminal mirror in Flask app"""
    return MobileTerminalMirror(app, socketio)