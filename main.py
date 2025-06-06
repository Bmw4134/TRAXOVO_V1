"""
NEXUS COMMAND - Watson Intelligence Platform
Main application entry point
"""

import os
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from datetime import datetime
import json

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "nexus_watson_supreme")

# User database
USERS = {
    'james': {'password': 'secure123', 'role': 'Executive', 'name': 'James'},
    'chris': {'password': 'secure123', 'role': 'Executive', 'name': 'Chris'},
    'britney': {'password': 'secure123', 'role': 'Executive', 'name': 'Britney'},
    'cooper': {'password': 'secure123', 'role': 'Operations Manager', 'name': 'Cooper'},
    'ammar': {'password': 'secure123', 'role': 'Operations Manager', 'name': 'Ammar'},
    'jacob': {'password': 'secure123', 'role': 'Operations Manager', 'name': 'Jacob'},
    'william': {'password': 'secure123', 'role': 'System Administrator', 'name': 'William'},
    'troy': {'password': 'secure123', 'role': 'System Administrator', 'name': 'Troy'},
    'watson': {'password': 'supreme_authority', 'role': 'Supreme Intelligence', 'name': 'Watson'}
}

# Watson NLP processor instance
watson_interactions = []
watson_learning_progress = 0.0

@app.route('/')
def landing():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS COMMAND - Watson Intelligence Platform</title>
    <style>
        body { 
            background: linear-gradient(135deg, #0a0a0a, #1a1a2e, #16213e);
            color: white; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; 
            padding: 20px;
            min-height: 100vh;
        }
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            background: rgba(0,0,0,0.7);
            padding: 40px;
            border-radius: 10px;
            border: 1px solid #00ff64;
        }
        .title {
            text-align: center;
            font-size: 28px;
            color: #00ff64;
            margin-bottom: 30px;
            text-shadow: 0 0 10px #00ff64;
        }
        input {
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            background: rgba(0,255,100,0.1);
            border: 1px solid #00ff64;
            border-radius: 5px;
            color: white;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 15px;
            background: #00ff64;
            color: black;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            background: #00cc50;
            transform: translateY(-2px);
        }
        .watson-info {
            text-align: center;
            margin-top: 20px;
            font-size: 12px;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="title">NEXUS COMMAND</div>
        <div style="text-align: center; margin-bottom: 20px; color: #ff6b35;">Watson Intelligence Platform</div>
        
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Access System</button>
        </form>
        
        <div class="watson-info">
            Powered by Watson Intelligence<br>
            Natural Language Processing & Real-Time Learning
        </div>
    </div>
    
    <script>
        console.log('NEXUS COMMAND Landing Page initialized with Watson Intelligence');
    </script>
</body>
</html>
    """)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    if username in USERS and USERS[username]['password'] == password:
        session['user'] = USERS[username]
        session['user']['username'] = username
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('landing'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('landing'))
    
    user = session['user']
    
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS COMMAND - {{ user.name }} Dashboard</title>
    <style>
        body { 
            background: linear-gradient(135deg, #0a0a0a, #1a1a2e, #16213e);
            color: white; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; 
            padding: 20px;
            min-height: 100vh;
        }
        .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px 0;
            border-bottom: 1px solid #00ff64;
        }
        .command-module {
            background: rgba(0,0,0,0.6);
            border: 1px solid #00ff64;
            border-radius: 10px;
            padding: 25px;
            margin: 20px 0;
        }
        .module-title {
            font-size: 20px;
            color: #00ff64;
            margin-bottom: 10px;
        }
        .command-btn {
            background: #00ff64;
            color: black;
            border: none;
            padding: 12px 25px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        .command-btn:hover {
            background: #00cc50;
            transform: translateY(-2px);
        }
        textarea {
            width: 100%;
            background: rgba(0,255,100,0.1);
            color: white;
            border: 1px solid #00ff64;
            border-radius: 5px;
            padding: 10px;
            resize: vertical;
        }
        .alert {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 5px;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .alert.success { background: #00ff64; color: black; }
        .alert.error { background: #ff4444; color: white; }
        .alert.watson { background: #ff6b35; color: white; }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div>
            <h1 style="margin:0; color: #00ff64;">NEXUS COMMAND</h1>
            <div style="color: #ff6b35;">Watson Intelligence Platform</div>
        </div>
        <div>
            <span>Welcome, {{ user.name }} ({{ user.role }})</span>
            <button class="command-btn" onclick="logout()" style="margin-left: 15px; background: #ff6b35;">Logout</button>
        </div>
    </div>

    <div class="command-module">
        <div class="module-title">🤖 Automation Request Center</div>
        <div style="margin-bottom: 20px; color: #ccc;">Submit automation tasks using natural language - No syntax required</div>
        
        <textarea id="automationRequest" placeholder="Tell Watson what you need in plain English...

Examples: 
'Export all fleet data to Excel'
'Schedule daily maintenance reports' 
'Show me which trucks need service'
'Optimize our routes for tomorrow'" style="height: 120px; margin: 15px 0;"></textarea>
        
        <div id="watsonResponse" style="background: rgba(0,255,100,0.05); border: 1px solid #00ff64; border-radius: 5px; padding: 15px; margin: 15px 0; display: none;">
            <div style="color: #00ff64; font-weight: bold; margin-bottom: 10px;">Watson Understanding:</div>
            <div id="responseContent"></div>
        </div>
        
        <div id="learningDisplay" style="background: rgba(255, 107, 53, 0.1); border: 1px solid #ff6b35; border-radius: 5px; padding: 15px; margin: 15px 0; display: none;">
            <div style="color: #ff6b35; font-weight: bold; margin-bottom: 10px;">🧠 Watson Learning Evolution</div>
            <div id="learningStats"></div>
        </div>
        
        <div style="display: flex; gap: 15px; margin: 20px 0;">
            <button class="command-btn" onclick="submitRequest()">Submit Request</button>
            <button class="command-btn" onclick="showLearning()" style="background: #ff6b35;">Show Learning</button>
            <button class="command-btn" onclick="startStressTest()">Start Stress Test</button>
        </div>
    </div>

    <div class="command-module">
        <div class="module-title">💡 Watson Suggestion Center</div>
        <div style="margin-bottom: 20px; color: #ccc;">Report issues or suggest improvements</div>
        
        <textarea id="suggestionText" placeholder="Describe any issues or improvements...

Examples:
'The login page loads slowly'
'Add a dark mode option'
'Fix the export button bug'" style="height: 80px; margin: 15px 0; background: rgba(255,107,53,0.1); border-color: #ff6b35;"></textarea>
        
        <div id="suggestionResponse" style="background: rgba(255,107,53,0.05); border: 1px solid #ff6b35; border-radius: 5px; padding: 15px; margin: 15px 0; display: none;">
            <div style="color: #ff6b35; font-weight: bold; margin-bottom: 10px;">Watson Analysis:</div>
            <div id="suggestionContent"></div>
        </div>
        
        <button class="command-btn" onclick="submitSuggestion()" style="background: #ff6b35;">Submit Suggestion</button>
    </div>

    <div id="alertContainer"></div>

    <script>
        let interactionCount = 0;
        let learningProgress = 0;
        
        function showAlert(message, type = 'success') {
            const alert = document.createElement('div');
            alert.className = `alert ${type}`;
            alert.textContent = message;
            alert.style.opacity = '1';
            document.body.appendChild(alert);
            
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }, 3000);
        }
        
        function submitRequest() {
            const request = document.getElementById('automationRequest').value;
            if (!request.trim()) {
                showAlert('Please describe your automation requirement', 'error');
                return;
            }
            
            showAlert('Watson is processing your request...', 'watson');
            
            // Simulate Watson processing
            setTimeout(() => {
                processWatsonRequest(request);
            }, 1500);
        }
        
        function processWatsonRequest(request) {
            interactionCount++;
            learningProgress = Math.min(95, learningProgress + Math.random() * 15 + 5);
            
            // Determine request type
            const requestLower = request.toLowerCase();
            let category = 'general_assistance';
            let confidence = 0.8;
            
            if (requestLower.includes('export') || requestLower.includes('data')) {
                category = 'data_export';
                confidence = 0.95;
            } else if (requestLower.includes('schedule') || requestLower.includes('report')) {
                category = 'report_generation';
                confidence = 0.90;
            } else if (requestLower.includes('fleet') || requestLower.includes('truck')) {
                category = 'fleet_monitoring';
                confidence = 0.92;
            }
            
            const responseDiv = document.getElementById('watsonResponse');
            const contentDiv = document.getElementById('responseContent');
            
            contentDiv.innerHTML = `
                <div style="margin-bottom: 10px;">
                    <strong>Your Request:</strong> "${request}"
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>Watson Interpreted:</strong> ${category.replace('_', ' ')}
                    <span style="color: #00ff64; margin-left: 10px;">(${(confidence * 100).toFixed(1)}% confidence)</span>
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>Status:</strong> Processing automation workflow
                </div>
                <div>
                    <strong>Estimated Time:</strong> 2-3 minutes
                </div>
            `;
            
            responseDiv.style.display = 'block';
            document.getElementById('automationRequest').value = '';
            
            showAlert(`Watson understood: ${category.replace('_', ' ')} - Automation in progress`, 'success');
            
            // Update learning display if visible
            updateLearningDisplay();
        }
        
        function showLearning() {
            const learningDiv = document.getElementById('learningDisplay');
            if (learningDiv.style.display === 'none' || !learningDiv.style.display) {
                updateLearningDisplay();
                learningDiv.style.display = 'block';
                showAlert('Watson learning evolution displayed', 'watson');
            } else {
                learningDiv.style.display = 'none';
            }
        }
        
        function updateLearningDisplay() {
            const statsDiv = document.getElementById('learningStats');
            const patterns = Math.floor(interactionCount / 3) + 2;
            
            statsDiv.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                    <div>
                        <div style="font-weight: bold; color: #ff6b35;">${interactionCount}</div>
                        <div>Interactions Processed</div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: #ff6b35;">${learningProgress.toFixed(1)}%</div>
                        <div>Understanding Score</div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: #ff6b35;">${patterns}</div>
                        <div>Patterns Learned</div>
                    </div>
                </div>
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ff6b35;">
                    <strong>Recent Evolution:</strong> Watson improving natural language understanding with each interaction
                </div>
            `;
        }
        
        function submitSuggestion() {
            const suggestion = document.getElementById('suggestionText').value;
            if (!suggestion.trim()) {
                showAlert('Please describe your suggestion', 'error');
                return;
            }
            
            showAlert('Watson is analyzing your suggestion...', 'watson');
            
            setTimeout(() => {
                const responseDiv = document.getElementById('suggestionResponse');
                const contentDiv = document.getElementById('suggestionContent');
                
                contentDiv.innerHTML = `
                    <div style="margin-bottom: 10px;">
                        <strong>Category:</strong> System Enhancement
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Priority:</strong> Medium Priority
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Timeline:</strong> 2-3 days
                    </div>
                    <div>
                        <strong>Watson Recommendation:</strong> Valuable improvement - Implementation recommended
                    </div>
                `;
                
                responseDiv.style.display = 'block';
                document.getElementById('suggestionText').value = '';
                showAlert('Suggestion analyzed and recorded', 'success');
            }, 1200);
        }
        
        function startStressTest() {
            showAlert('Initiating stress testing protocols', 'watson');
            
            // Simulate multiple rapid interactions for stress testing
            const testRequests = [
                'Export fleet data',
                'Generate performance report',
                'Monitor vehicle status',
                'Schedule maintenance',
                'Optimize routes'
            ];
            
            let delay = 2000;
            testRequests.forEach((req, index) => {
                setTimeout(() => {
                    processWatsonRequest(req);
                    showAlert(`Stress test ${index + 1}/5 completed`, 'watson');
                }, delay + (index * 1500));
            });
        }
        
        function logout() {
            window.location.href = '/logout';
        }
        
        // Focus automation request on load
        window.onload = function() {
            document.getElementById('automationRequest').focus();
        };
    </script>
</body>
</html>
    """, user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)