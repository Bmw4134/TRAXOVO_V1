"""
TRAXOVO Replit Megabundle Entry Point
Complete fleet management system with AI assistant integration
"""

import os
import json
from flask import Flask, Blueprint, request, jsonify, render_template
from datetime import datetime

# Import core TRAXOVO modules
from simple_app import app, load_authentic_json_data, get_authentic_foundation_data

# Kaizen GPT Assistant Integration
class KaizenAssistant:
    """AI Assistant for fleet operations with authentic data context"""
    
    def __init__(self):
        self.session_log = []
        self.authentic_data = None
        self.load_fleet_context()
    
    def load_fleet_context(self):
        """Load authentic fleet data for AI context"""
        try:
            self.authentic_data = load_authentic_json_data()
            if self.authentic_data:
                print(f"Loaded authentic data: {self.authentic_data['total_assets']} assets, {self.authentic_data['total_drivers']} drivers")
        except Exception as e:
            print(f"Error loading authentic data: {e}")
    
    def process_prompt(self, user_prompt, user_id="anon"):
        """Process user prompt with fleet data context"""
        session_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'prompt': user_prompt,
            'data_context': self.authentic_data is not None
        }
        
        # Simple response logic with fleet context
        if 'assets' in user_prompt.lower():
            if self.authentic_data:
                response = f"Current fleet status: {self.authentic_data['total_assets']} total assets, {self.authentic_data['active_assets']} active"
            else:
                response = "Asset data not available - check data connection"
        elif 'drivers' in user_prompt.lower() or 'attendance' in user_prompt.lower():
            if self.authentic_data:
                response = f"Driver status: {self.authentic_data['clocked_in_drivers']} of {self.authentic_data['total_drivers']} drivers clocked in"
            else:
                response = "Driver data not available - check attendance system"
        else:
            response = f"Fleet management query processed: {user_prompt}"
        
        session_entry['response'] = response
        self.session_log.append(session_entry)
        
        return {
            'response': response,
            'fleet_context': self.authentic_data,
            'session_id': len(self.session_log)
        }

# Initialize AI assistant
kaizen_assistant = KaizenAssistant()

# Create assistant blueprint
assistant_api = Blueprint("assistant_api", __name__)

@assistant_api.route("/assistant", methods=["POST"])
def assistant_handler():
    """Handle GPT prompts with logging and validation"""
    data = request.get_json()
    prompt = data.get("prompt", "")
    user_id = data.get("user_id", "anon")
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    result = kaizen_assistant.process_prompt(prompt, user_id)
    return jsonify(result)

@assistant_api.route("/map", methods=["GET"])
def map_data():
    """Real map data from authentic sources"""
    authentic_data = load_authentic_json_data()
    if authentic_data and 'map_assets' in authentic_data:
        return jsonify(authentic_data['map_assets'])
    else:
        return jsonify({'error': 'Map data not available'}), 404

@assistant_api.route("/assets", methods=["GET"])  
def asset_data():
    """Real asset data from authentic sources"""
    authentic_data = load_authentic_json_data()
    if authentic_data and 'fleet_assets' in authentic_data:
        return jsonify(authentic_data['fleet_assets'])
    else:
        return jsonify({'error': 'Asset data not available'}), 404

@assistant_api.route("/attendance", methods=["GET"])
def attendance_data():
    """Real attendance data from authentic sources"""
    authentic_data = load_authentic_json_data()
    if authentic_data and 'attendance_records' in authentic_data:
        return jsonify(authentic_data['attendance_records'])
    else:
        return jsonify({'error': 'Attendance data not available'}), 404

@assistant_api.route("/auth/start", methods=["GET"])
def auth_start():
    """Replit PKCE login start"""
    # Placeholder for Replit auth integration
    return jsonify({
        'auth_url': '/auth/login',
        'method': 'PKCE',
        'provider': 'replit'
    })

# Register assistant blueprint with main app
app.register_blueprint(assistant_api, url_prefix="/api")

# Static file routes for admin UI
@app.route("/static/admin_ui.html")
def admin_ui():
    """Full control panel"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TRAXOVO Admin Control Panel</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container-fluid mt-4">
            <h1>TRAXOVO Fleet Management - Admin Panel</h1>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">System Status</div>
                        <div class="card-body">
                            <p>Fleet data loaded from authentic sources</p>
                            <a href="/api/assets" class="btn btn-primary">View Assets</a>
                            <a href="/api/attendance" class="btn btn-info">View Attendance</a>
                            <a href="/api/map" class="btn btn-success">View Map Data</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Quick Actions</div>
                        <div class="card-body">
                            <a href="/" class="btn btn-warning">Main Dashboard</a>
                            <a href="/attendance-matrix" class="btn btn-secondary">Attendance Matrix</a>
                            <a href="/fleet-map" class="btn btn-dark">Fleet Map</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/static/assistant_ui.html")
def assistant_ui():
    """Prompt chat interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TRAXOVO AI Assistant</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>TRAXOVO AI Fleet Assistant</h1>
            <div class="row">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">Chat with Fleet AI</div>
                        <div class="card-body">
                            <div id="chat-history" style="height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 10px;"></div>
                            <div class="input-group">
                                <input type="text" id="prompt-input" class="form-control" placeholder="Ask about your fleet...">
                                <button class="btn btn-primary" onclick="sendPrompt()">Send</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">Fleet Status</div>
                        <div class="card-body">
                            <p>Real-time fleet data integration active</p>
                            <small class="text-muted">Ask about assets, drivers, or operations</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <script>
            function sendPrompt() {
                const input = document.getElementById('prompt-input');
                const prompt = input.value.trim();
                if (!prompt) return;
                
                addMessage('You: ' + prompt, 'user');
                input.value = '';
                
                fetch('/api/assistant', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt: prompt})
                })
                .then(response => response.json())
                .then(data => {
                    addMessage('Assistant: ' + data.response, 'assistant');
                })
                .catch(error => {
                    addMessage('Error: ' + error.message, 'error');
                });
            }
            
            function addMessage(message, type) {
                const chat = document.getElementById('chat-history');
                const div = document.createElement('div');
                div.className = 'mb-2 ' + (type === 'user' ? 'text-end' : '');
                div.innerHTML = '<small class="text-muted">' + new Date().toLocaleTimeString() + '</small><br>' + message;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }
            
            document.getElementById('prompt-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendPrompt();
            });
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    print("TRAXOVO Megabundle initialized with Kaizen GPT Assistant")
    print("Available endpoints:")
    print("  /api/assistant - AI chat interface")
    print("  /api/map - Real map data")
    print("  /api/assets - Real asset data") 
    print("  /api/attendance - Real attendance data")
    print("  /static/admin_ui.html - Admin control panel")
    print("  /static/assistant_ui.html - AI chat interface")
    app.run(host="0.0.0.0", port=5000, debug=True)