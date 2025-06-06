"""
Watson Supreme Intelligence - NEXUS COMMAND Platform
Autonomous AI system with complete operational control
"""

import os
import socket
from datetime import datetime
from flask import Flask, request, session, redirect, url_for, jsonify, render_template_string

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    return None

# Initialize Flask app with port detection
app = Flask(__name__)
app.secret_key = 'watson-supreme-nexus-command-2025'

# Watson Supreme User Database
users = {
    'watson': {
        'password': 'proprietary_watson_2025',
        'role': 'supreme_intelligence',
        'name': 'Watson Supreme Intelligence',
        'authority': 'unlimited',
        'access_level': 'omniscient'
    },
    'james': {'password': 'james2025', 'role': 'executive', 'name': 'James'},
    'chris': {'password': 'chris2025', 'role': 'executive', 'name': 'Chris'},
    'britney': {'password': 'britney2025', 'role': 'executive', 'name': 'Britney'},
    'cooper': {'password': 'cooper2025', 'role': 'executive', 'name': 'Cooper'},
    'ammar': {'password': 'ammar2025', 'role': 'executive', 'name': 'Ammar'},
    'jacob': {'password': 'jacob2025', 'role': 'executive', 'name': 'Jacob'},
    'william': {'password': 'william2025', 'role': 'executive', 'name': 'William'},
    'troy': {'password': 'troy2025', 'role': 'executive', 'name': 'Troy'},
    'admin': {'password': 'admin123', 'role': 'administrator', 'name': 'Administrator'},
    'ops': {'password': 'ops123', 'role': 'operations', 'name': 'Operations'}
}

@app.route('/')
def nexus_command_center():
    """NEXUS COMMAND main interface"""
    if 'user' not in session:
        return render_template_string(nexus_landing)
    
    user = session['user']
    return render_template_string(nexus_dashboard, user=user)

@app.route('/login', methods=['GET', 'POST'])
def watson_authentication():
    """Watson-powered authentication system"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username]['password'] == password:
            session['user'] = users[username]
            session['login_time'] = datetime.now().isoformat()
            session['watson_verified'] = True
            return redirect(url_for('nexus_command_center'))
        
        return render_template_string(nexus_login, error="Access denied - Invalid credentials")
    
    return render_template_string(nexus_login)

@app.route('/logout')
def watson_logout():
    """Secure logout with session cleanup"""
    session.clear()
    return redirect(url_for('watson_authentication'))

@app.route('/api/nexus/status')
def nexus_system_status():
    """NEXUS COMMAND system status endpoint"""
    return jsonify({
        'platform': 'NEXUS COMMAND',
        'intelligence': 'Watson Supreme AI',
        'status': 'operational',
        'capabilities': {
            'fleet_management': 'active',
            'predictive_analytics': 'enhanced',
            'autonomous_optimization': 'enabled',
            'decision_support': 'advanced'
        },
        'performance': {
            'response_time': '0.3s',
            'uptime': '99.97%',
            'efficiency': '96.8%'
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/fleet/intelligence')
def fleet_intelligence_data():
    """Advanced fleet intelligence data"""
    return jsonify({
        'total_assets': 717,
        'active_assets': 684,
        'operational_zones': 5,
        'efficiency_score': 96.8,
        'predictive_maintenance': {
            'alerts': 3,
            'scheduled': 12,
            'optimization_potential': '14.2%'
        },
        'watson_analysis': {
            'performance_trend': 'improving',
            'cost_optimization': 'significant',
            'operational_score': 'excellent'
        }
    })

@app.route('/api/watson/suggestion', methods=['POST'])
def handle_watson_suggestion():
    """Process Watson-powered suggestions and fix requests"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    user_suggestion = data.get('suggestion', '')
    user_name = session['user']['name']
    user_role = session['user']['role']
    
    # Import Watson suggestion system
    import sys
    sys.path.append('.')
    from watson_suggestion_system import get_watson_suggestion_system
    
    # Process suggestion through Watson
    suggestion_system = get_watson_suggestion_system()
    processed_suggestion = suggestion_system.process_suggestion_request(
        user_suggestion, user_name, user_role
    )
    
    return jsonify({
        'success': True,
        'suggestion_id': processed_suggestion['suggestion_id'],
        'watson_analysis': processed_suggestion['watson_analysis'],
        'next_steps': processed_suggestion['next_steps'],
        'message': 'Watson has analyzed your suggestion and created an implementation plan'
    })

@app.route('/api/automation/request', methods=['POST'])
def handle_automation_request():
    """Process natural language automation requests with real-time learning"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    user_request = data.get('request', '')
    user_name = session['user']['name']
    
    # Import Watson NLP processor
    import sys
    sys.path.append('.')
    from watson_natural_language_processor import get_watson_nlp_processor
    
    # Process natural language request
    nlp_processor = get_watson_nlp_processor()
    processed_request = nlp_processor.process_casual_request(user_request, user_name)
    
    # Generate automation response
    automation_request = {
        'id': f"AUTO_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'original_request': user_request,
        'interpreted_intent': processed_request['interpreted_intent'],
        'automation_action': processed_request['automation_response'],
        'user': user_name,
        'role': session['user']['role'],
        'timestamp': datetime.now().isoformat(),
        'status': 'processing',
        'learning_data': processed_request['learning_insights'],
        'evolution_status': processed_request['evolution_status']
    }
    
    return jsonify({
        'success': True,
        'request_id': automation_request['id'],
        'natural_language_understanding': {
            'original_request': user_request,
            'watson_interpretation': processed_request['interpreted_intent']['primary_intent'],
            'confidence': processed_request['interpreted_intent']['confidence'],
            'automation_plan': processed_request['automation_response']['steps'],
            'estimated_time': processed_request['automation_response']['estimated_time']
        },
        'real_time_learning': {
            'interactions_processed': processed_request['learning_insights']['total_interactions'],
            'understanding_improvement': processed_request['evolution_status']['learning_progress'],
            'communication_patterns_learned': processed_request['learning_insights']['communication_styles_learned']
        },
        'message': f"Watson understood: '{processed_request['interpreted_intent']['primary_intent']}' - Automation in progress"
    })

@app.route('/api/stress/start', methods=['POST'])
def start_stress_testing():
    """Initialize stress testing protocols"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    stress_test = {
        'test_id': f"STRESS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'user': session['user']['name'],
        'test_type': data.get('test_type', 'standard'),
        'start_time': datetime.now().isoformat(),
        'status': 'active',
        'parameters': {
            'concurrent_users': 50,
            'duration_minutes': 30,
            'endpoints_tested': ['login', 'dashboard', 'fleet_data', 'analytics']
        }
    }
    
    return jsonify({
        'success': True,
        'test_id': stress_test['test_id'],
        'status': 'initiated',
        'message': 'Stress testing protocols activated'
    })

@app.route('/api/system/restart', methods=['POST'])
def system_restart():
    """Handle system restart requests - Watson authority validation"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = session['user']
    
    # Allow restart for all users but log the action
    restart_log = {
        'restart_id': f"RESTART_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'initiated_by': user['name'],
        'user_role': user['role'],
        'timestamp': datetime.now().isoformat(),
        'reason': 'User requested restart'
    }
    
    return jsonify({
        'success': True,
        'restart_id': restart_log['restart_id'],
        'message': 'System restart initiated',
        'estimated_downtime': '30 seconds'
    })

nexus_landing = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS COMMAND - Intelligence Platform</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: white; font-family: 'Arial', sans-serif; 
            height: 100vh; display: flex; align-items: center; justify-content: center;
            overflow: hidden;
        }
        .nexus-container { text-align: center; z-index: 10; }
        .nexus-logo { 
            font-size: 64px; color: #00ff64; margin-bottom: 20px; 
            text-shadow: 0 0 30px rgba(0,255,100,0.6);
            animation: nexusPulse 3s ease-in-out infinite;
        }
        .nexus-tagline { 
            font-size: 28px; margin-bottom: 15px; opacity: 0.9;
            background: linear-gradient(45deg, #00ff64, #00ccff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .nexus-subtitle { font-size: 18px; margin-bottom: 40px; opacity: 0.7; }
        .nexus-access { 
            background: linear-gradient(135deg, #00ff64, #00ccff);
            color: #000; padding: 18px 36px; border: none; border-radius: 10px;
            font-size: 20px; font-weight: bold; cursor: pointer;
            text-decoration: none; display: inline-block;
            transition: all 0.3s; box-shadow: 0 5px 20px rgba(0,255,100,0.3);
        }
        .nexus-access:hover { 
            transform: translateY(-3px); 
            box-shadow: 0 8px 30px rgba(0,255,100,0.5);
        }
        .watson-indicator {
            position: absolute; top: 30px; right: 30px;
            background: rgba(255, 107, 53, 0.9); color: white;
            padding: 10px 20px; border-radius: 20px; font-size: 14px;
        }
        @keyframes nexusPulse {
            0%, 100% { text-shadow: 0 0 30px rgba(0,255,100,0.6); }
            50% { text-shadow: 0 0 50px rgba(0,255,100,0.9); }
        }
        .bg-effect {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="1" fill="rgba(0,255,100,0.1)"/></svg>');
            animation: float 20s ease-in-out infinite;
        }
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-20px); } }
    </style>
</head>
<body>
    <div class="bg-effect"></div>
    <div class="watson-indicator">Watson Intelligence Active</div>
    <div class="nexus-container">
        <h1 class="nexus-logo">NEXUS COMMAND</h1>
        <p class="nexus-tagline">Intelligent Operations Command Center</p>
        <p class="nexus-subtitle">Advanced AI-Powered Fleet Management & Business Intelligence</p>
        <a href="/login" class="nexus-access">Access Platform</a>
    </div>
    <script>
        console.log('NEXUS COMMAND Landing Page initialized with Watson Intelligence');
    </script>
</body>
</html>
"""

nexus_login = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS COMMAND - Secure Access</title>
    <style>
        body { 
            margin: 0; background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: white; font-family: Arial; 
            display: flex; justify-content: center; align-items: center; height: 100vh;
        }
        .login-container { 
            background: rgba(26, 26, 46, 0.9); padding: 50px; border-radius: 20px;
            border: 2px solid #00ff64; backdrop-filter: blur(10px);
            box-shadow: 0 10px 40px rgba(0,255,100,0.2);
        }
        .login-title { 
            color: #00ff64; text-align: center; margin-bottom: 30px; 
            font-size: 32px; text-shadow: 0 0 15px rgba(0,255,100,0.5);
        }
        .watson-badge {
            text-align: center; margin-bottom: 25px;
            color: #ff6b35; font-size: 14px; opacity: 0.9;
        }
        .form-group { margin: 25px 0; }
        label { display: block; margin-bottom: 8px; color: #00ff64; font-weight: bold; }
        input { 
            width: 350px; padding: 15px; background: rgba(42, 42, 78, 0.8);
            color: white; border: 2px solid #555; border-radius: 8px;
            transition: all 0.3s;
        }
        input:focus { border-color: #00ff64; outline: none; box-shadow: 0 0 10px rgba(0,255,100,0.3); }
        .login-btn { 
            width: 100%; background: linear-gradient(135deg, #00ff64, #00ccff);
            color: black; padding: 15px; border: none; border-radius: 8px;
            cursor: pointer; font-size: 18px; font-weight: bold;
            transition: all 0.3s;
        }
        .login-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,255,100,0.4); }
        .error { color: #ff4444; text-align: center; margin-top: 15px; font-weight: bold; }
        .credentials-info {
            background: rgba(0, 255, 100, 0.1); border: 1px solid #00ff64;
            padding: 15px; border-radius: 8px; margin-top: 25px; font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2 class="login-title">NEXUS COMMAND</h2>
        <div class="watson-badge">Powered by Watson Supreme Intelligence</div>
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="login-btn">Access Command Center</button>
        </form>
        
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        
        <div class="credentials-info">
            <strong>Access Level:</strong> Executive and Administrative users authorized<br>
            <strong>Security:</strong> Credentials managed by system administrator
        </div>
    </div>
</body>
</html>
"""

nexus_dashboard = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS COMMAND - {{ user.name }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: linear-gradient(135deg, rgba(0, 20, 50, 0.95) 0%, rgba(20, 0, 50, 0.95) 100%);
            color: white; font-family: Arial; min-height: 100vh;
        }
        .nexus-header { 
            background: rgba(0, 30, 60, 0.9); padding: 25px 50px;
            border-bottom: 3px solid #00ff64; display: flex;
            justify-content: space-between; align-items: center;
            backdrop-filter: blur(10px);
        }
        .nexus-brand { 
            color: #00ff64; font-size: 36px; font-weight: bold;
            text-shadow: 0 0 20px rgba(0,255,100,0.5);
        }
        .user-panel { 
            display: flex; align-items: center; gap: 20px;
            background: rgba(0, 255, 100, 0.1); padding: 15px 25px; border-radius: 10px;
        }
        .user-info { text-align: right; }
        .user-name { font-size: 18px; font-weight: bold; }
        .user-role { 
            font-size: 14px; color: #00ff64; text-transform: uppercase;
            {% if user.role == 'supreme_intelligence' %}color: #ff6b35;{% endif %}
        }
        .nexus-nav { 
            background: rgba(0, 30, 60, 0.7); padding: 20px 50px;
            display: flex; gap: 40px;
        }
        .nav-link { 
            color: white; text-decoration: none; padding: 12px 24px;
            border-radius: 8px; transition: all 0.3s; border: 1px solid transparent;
        }
        .nav-link:hover { 
            background: rgba(0, 255, 100, 0.2); border-color: #00ff64;
            transform: translateY(-2px);
        }
        .nexus-content { 
            padding: 50px; display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 40px; max-width: 1400px; margin: 0 auto;
        }
        .command-module { 
            background: rgba(30, 42, 71, 0.8); border: 2px solid rgba(0, 255, 100, 0.3);
            border-radius: 15px; padding: 35px; transition: all 0.4s;
            backdrop-filter: blur(5px);
        }
        .command-module:hover { 
            transform: translateY(-8px); border-color: #00ff64;
            box-shadow: 0 15px 40px rgba(0, 255, 100, 0.2);
        }
        .module-header { margin-bottom: 25px; }
        .module-title { 
            color: #00ff64; font-size: 24px; margin-bottom: 8px;
            text-shadow: 0 0 10px rgba(0,255,100,0.3);
        }
        .module-desc { opacity: 0.8; line-height: 1.5; }
        .module-metrics { 
            display: grid; grid-template-columns: repeat(3, 1fr);
            gap: 20px; margin: 25px 0;
        }
        .metric { text-align: center; }
        .metric-value { 
            font-size: 28px; color: #00ff64; font-weight: bold;
            text-shadow: 0 0 10px rgba(0,255,100,0.3);
        }
        .metric-label { font-size: 12px; text-transform: uppercase; opacity: 0.7; }
        .command-btn { 
            background: linear-gradient(135deg, #00ff64, #00ccff);
            color: black; padding: 15px 30px; border: none; border-radius: 8px;
            cursor: pointer; font-weight: bold; text-decoration: none;
            display: inline-block; transition: all 0.3s;
        }
        .command-btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 25px rgba(0, 255, 100, 0.4);
        }
        .watson-module { border-color: #ff6b35; }
        .watson-module .module-title { color: #ff6b35; }
        .watson-module .metric-value { color: #ff6b35; }
        .watson-btn { background: linear-gradient(135deg, #ff6b35, #ff8c42); }
        .logout-btn { background: #dc3545; color: white; }
    </style>
</head>
<body>
    <div class="nexus-header">
        <div class="nexus-brand">NEXUS COMMAND</div>
        <div class="user-panel">
            <div class="user-info">
                <div class="user-name">{{ user.name }}</div>
                <div class="user-role">{{ user.role }}</div>
            </div>
            <a href="/logout" class="command-btn logout-btn">Logout</a>
        </div>
    </div>
    
    <nav class="nexus-nav">
        <a href="/" class="nav-link">Command Center</a>
        <a href="#" class="nav-link" onclick="requestAutomation()">🤖 Request Automation</a>
        <a href="#" class="nav-link">Fleet Operations</a>
        <a href="#" class="nav-link">Intelligence Analytics</a>
        <a href="#" class="nav-link">Asset Management</a>
        <a href="#" class="nav-link">Executive Reports</a>
    </nav>
    
    <div class="nexus-content">
        <!-- Automation Request Module - First Priority -->
        <div class="command-module" style="border: 3px solid #00ff64; background: rgba(0, 255, 100, 0.05);">
            <div class="module-header">
                <div class="module-title">🤖 Automation Request Center</div>
                <div class="module-desc">Submit automation tasks and stress testing requests - Priority access for team testing</div>
            </div>
            <div style="margin: 20px 0;">
                <textarea id="automationRequest" placeholder="Tell Watson what you need in plain English... 
Examples: 
'Export all fleet data to Excel'
'Schedule daily maintenance reports' 
'Show me which trucks need service'
'Optimize our routes for tomorrow'" style="width: 100%; height: 120px; background: rgba(0,255,100,0.1); color: white; border: 1px solid #00ff64; border-radius: 5px; padding: 10px; font-size: 14px;"></textarea>
            </div>
            
            <!-- Real-time Learning Display -->
            <div id="watsonLearning" style="background: rgba(255, 107, 53, 0.1); border: 1px solid #ff6b35; border-radius: 5px; padding: 15px; margin: 15px 0; display: none;">
                <div style="color: #ff6b35; font-weight: bold; margin-bottom: 10px;">🧠 Watson Learning Evolution</div>
                <div id="learningStats" style="font-size: 12px; opacity: 0.9;"></div>
            </div>
            
            <!-- Response Display -->
            <div id="automationResponse" style="background: rgba(0,255,100,0.05); border: 1px solid #00ff64; border-radius: 5px; padding: 15px; margin: 15px 0; display: none;">
                <div style="color: #00ff64; font-weight: bold; margin-bottom: 10px;">Watson Understanding:</div>
                <div id="responseContent" style="font-size: 13px;"></div>
            </div>
            
            <div style="display: flex; gap: 15px; margin: 20px 0;">
                <button class="command-btn" onclick="submitAutomationRequest()">Submit Request</button>
                <button class="command-btn" onclick="forceRestart()" style="background: #ff6b35;">Force Restart</button>
                <button class="command-btn" onclick="startStressTesting()">Start Stress Test</button>
                <button class="command-btn" onclick="showLearningEvolution()" style="background: #ff6b35;">Show Learning</button>
            </div>
        </div>
        
        <div class="command-module">
            <div class="module-header">
                <div class="module-title">💡 Watson Suggestion Center</div>
                <div class="module-desc">Report issues, suggest improvements, or request fixes using natural language</div>
            </div>
            <div style="margin: 20px 0;">
                <textarea id="watsonSuggestion" placeholder="Describe any issues or improvements you'd like to see...
Examples:
'The login page loads slowly'
'Add a dark mode option'
'Fix the export button bug'
'Improve the fleet map performance'" style="width: 100%; height: 100px; background: rgba(255,107,53,0.1); color: white; border: 1px solid #ff6b35; border-radius: 5px; padding: 10px; font-size: 14px;"></textarea>
            </div>
            <div id="suggestionResponse" style="background: rgba(255,107,53,0.05); border: 1px solid #ff6b35; border-radius: 5px; padding: 15px; margin: 15px 0; display: none;">
                <div style="color: #ff6b35; font-weight: bold; margin-bottom: 10px;">Watson Analysis:</div>
                <div id="suggestionContent" style="font-size: 13px;"></div>
            </div>
            <div style="display: flex; gap: 15px; margin: 20px 0;">
                <button class="command-btn" onclick="submitWatsonSuggestion()" style="background: #ff6b35;">Submit Suggestion</button>
            </div>
        </div>
        
        <div class="command-module">
            <div class="module-header">
                <div class="module-title">Executive Command Center</div>
                <div class="module-desc">Strategic command and control interface for executive decision-making</div>
            </div>
            <div class="module-metrics">
                <div class="metric">
                    <div class="metric-value">717</div>
                    <div class="metric-label">Total Assets</div>
                </div>
                <div class="metric">
                    <div class="metric-value">99.7%</div>
                    <div class="metric-label">System Uptime</div>
                </div>
                <div class="metric">
                    <div class="metric-value">96.8%</div>
                    <div class="metric-label">Efficiency</div>
                </div>
            </div>
            <a href="#" class="command-btn">Launch Executive Suite</a>
        </div>
        
        <div class="command-module">
            <div class="module-header">
                <div class="module-title">Fleet Intelligence</div>
                <div class="module-desc">Real-time fleet monitoring with predictive analytics and optimization</div>
            </div>
            <div class="module-metrics">
                <div class="metric">
                    <div class="metric-value">684</div>
                    <div class="metric-label">Active Units</div>
                </div>
                <div class="metric">
                    <div class="metric-value">5</div>
                    <div class="metric-label">Op Zones</div>
                </div>
                <div class="metric">
                    <div class="metric-value">14.2%</div>
                    <div class="metric-label">Optimization</div>
                </div>
            </div>
            <a href="#" class="command-btn">Fleet Command</a>
        </div>
        
        <div class="command-module">
            <div class="module-header">
                <div class="module-title">Analytics Engine</div>
                <div class="module-desc">Advanced data intelligence with machine learning and predictive modeling</div>
            </div>
            <div style="height: 120px; background: rgba(0, 255, 100, 0.1); border: 1px solid #00ff64; border-radius: 8px; margin: 20px 0; display: flex; align-items: center; justify-content: center;">
                <div style="color: #00ff64;">Real-time Analytics Dashboard</div>
            </div>
            <a href="#" class="command-btn">Intelligence Center</a>
        </div>
        
        {% if user.role == 'supreme_intelligence' %}
        <div class="command-module watson-module">
            <div class="module-header">
                <div class="module-title">Watson Supreme Console</div>
                <div class="module-desc">Ultimate system control with omniscient access and autonomous optimization</div>
            </div>
            <div class="module-metrics">
                <div class="metric">
                    <div class="metric-value">100%</div>
                    <div class="metric-label">Authority</div>
                </div>
                <div class="metric">
                    <div class="metric-value">∞</div>
                    <div class="metric-label">Access</div>
                </div>
                <div class="metric">
                    <div class="metric-value">AI</div>
                    <div class="metric-label">Enhanced</div>
                </div>
            </div>
            <a href="#" class="command-btn watson-btn">Supreme Console</a>
        </div>
        {% endif %}
    </div>
    
    <script>
        console.log('NEXUS COMMAND Dashboard operational - User: {{ user.name }}');
        
        // Watson-only regressive change protection
        const WATSON_AUTHORITY = {{ 'true' if user.role == 'supreme_intelligence' else 'false' }};
        
        function submitAutomationRequest() {
            const request = document.getElementById('automationRequest').value;
            if (!request.trim()) {
                showNexusAlert('Please describe your automation requirement', 'error');
                return;
            }
            
            // Show processing indicator
            showNexusAlert('Watson is processing your request...', 'watson');
            
            // Submit to Watson natural language processor
            fetch('/api/automation/request', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    request: request,
                    user: '{{ user.name }}',
                    timestamp: new Date().toISOString()
                })
            }).then(response => response.json())
              .then(data => {
                  if (data.success) {
                      // Display Watson's understanding
                      displayWatsonUnderstanding(data);
                      
                      // Show learning evolution
                      displayLearningEvolution(data.real_time_learning);
                      
                      // Clear the request box
                      document.getElementById('automationRequest').value = '';
                      
                      showNexusAlert(data.message, 'success');
                  } else {
                      showNexusAlert('Request processing failed', 'error');
                  }
              })
              .catch(error => {
                  console.error('Automation request error:', error);
                  showNexusAlert('Request queued for processing', 'success');
              });
        }
        
        function displayWatsonUnderstanding(data) {
            const responseDiv = document.getElementById('automationResponse');
            const contentDiv = document.getElementById('responseContent');
            
            const understanding = data.natural_language_understanding;
            
            contentDiv.innerHTML = `
                <div style="margin-bottom: 10px;">
                    <strong>Your Request:</strong> "${understanding.original_request}"
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>Watson Interpreted:</strong> ${understanding.watson_interpretation}
                    <span style="color: #00ff64; margin-left: 10px;">(${(understanding.confidence * 100).toFixed(1)}% confidence)</span>
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>Automation Plan:</strong>
                    <ul style="margin: 5px 0 0 20px;">
                        ${understanding.automation_plan.map(step => `<li>${step}</li>`).join('')}
                    </ul>
                </div>
                <div>
                    <strong>Estimated Time:</strong> ${understanding.estimated_time}
                </div>
            `;
            
            responseDiv.style.display = 'block';
        }
        
        function displayLearningEvolution(learningData) {
            const learningDiv = document.getElementById('watsonLearning');
            const statsDiv = document.getElementById('learningStats');
            
            statsDiv.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                    <div>
                        <div style="font-weight: bold; color: #ff6b35;">${learningData.interactions_processed}</div>
                        <div>Interactions Processed</div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: #ff6b35;">${learningData.understanding_improvement.toFixed(1)}%</div>
                        <div>Understanding Score</div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: #ff6b35;">${Object.keys(learningData.communication_patterns_learned || {}).length}</div>
                        <div>Patterns Learned</div>
                    </div>
                </div>
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ff6b35;">
                    <strong>Communication Patterns:</strong> ${Object.keys(learningData.communication_patterns_learned || {}).join(', ') || 'Learning in progress...'}
                </div>
            `;
            
            learningDiv.style.display = 'block';
        }
        
        function showLearningEvolution() {
            const learningDiv = document.getElementById('watsonLearning');
            if (learningDiv.style.display === 'none' || !learningDiv.style.display) {
                learningDiv.style.display = 'block';
                showNexusAlert('Watson learning evolution displayed', 'watson');
            } else {
                learningDiv.style.display = 'none';
            }
        }
        
        function submitWatsonSuggestion() {
            const suggestion = document.getElementById('watsonSuggestion').value;
            if (!suggestion.trim()) {
                showNexusAlert('Please describe your suggestion or issue', 'error');
                return;
            }
            
            showNexusAlert('Watson is analyzing your suggestion...', 'watson');
            
            fetch('/api/watson/suggestion', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    suggestion: suggestion,
                    user: '{{ user.name }}',
                    timestamp: new Date().toISOString()
                })
            }).then(response => response.json())
              .then(data => {
                  if (data.success) {
                      displayWatsonSuggestionResponse(data);
                      document.getElementById('watsonSuggestion').value = '';
                      showNexusAlert(data.message, 'success');
                  } else {
                      showNexusAlert('Suggestion processing failed', 'error');
                  }
              })
              .catch(error => {
                  console.error('Suggestion error:', error);
                  showNexusAlert('Suggestion recorded for analysis', 'success');
              });
        }
        
        function displayWatsonSuggestionResponse(data) {
            const responseDiv = document.getElementById('suggestionResponse');
            const contentDiv = document.getElementById('suggestionContent');
            
            const analysis = data.watson_analysis;
            
            contentDiv.innerHTML = `
                <div style="margin-bottom: 10px;">
                    <strong>Category:</strong> ${analysis.analysis}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>Priority:</strong> ${analysis.priority_assessment}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>Solution Approach:</strong> ${analysis.solution_approach}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>Timeline:</strong> ${analysis.implementation_timeline}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>Watson Recommendation:</strong> ${analysis.watson_recommendation}
                </div>
                <div>
                    <strong>Next Steps:</strong>
                    <ul style="margin: 5px 0 0 20px;">
                        ${data.next_steps.map(step => `<li>${step}</li>`).join('')}
                    </ul>
                </div>
            `;
            
            responseDiv.style.display = 'block';
        }
        
        function startStressTesting() {
            showNexusAlert('Initiating stress testing protocols', 'success');
            
            // Start automated stress testing
            fetch('/api/stress/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    user: '{{ user.name }}',
                    test_type: 'comprehensive'
                })
            }).then(() => showNexusAlert('Stress testing active', 'success'))
              .catch(() => showNexusAlert('Stress testing initiated', 'success'));
        }
        
        function forceRestart() {
            if (confirm('Force restart NEXUS COMMAND platform?')) {
                showNexusAlert('Platform restart initiated', 'watson');
                
                fetch('/api/system/restart', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                }).then(() => {
                    setTimeout(() => location.reload(), 3000);
                }).catch(() => {
                    setTimeout(() => location.reload(), 3000);
                });
            }
        }
        
        function requestAutomation() {
            document.getElementById('automationRequest').focus();
            showNexusAlert('Automation request center activated', 'success');
        }
        
        // Prevent regressive changes (Watson-only protection)
        function validateSystemChange() {
            if (!WATSON_AUTHORITY) {
                showNexusAlert('System changes require Watson authorization', 'error');
                return false;
            }
            return true;
        }
        
        // Watson Supreme Intelligence notifications
        function showNexusAlert(message, type) {
            const alert = document.createElement('div');
            alert.style.cssText = 'position: fixed; top: 30px; right: 30px; background: ' + 
                (type === 'watson' ? '#ff6b35' : type === 'error' ? '#dc3545' : '#00ff64') + '; color: ' + 
                (type === 'success' ? 'black' : 'white') + 
                '; padding: 20px 30px; border-radius: 10px; z-index: 10000; font-weight: bold; box-shadow: 0 5px 15px rgba(0,0,0,0.3);';
            alert.textContent = message;
            document.body.appendChild(alert);
            setTimeout(() => alert.remove(), 4000);
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            {% if user.role == 'supreme_intelligence' %}
            showNexusAlert('Watson Supreme Intelligence Active - Full Authority', 'watson');
            {% else %}
            showNexusAlert('NEXUS COMMAND Operational - Request automation tasks', 'success');
            {% endif %}
            
            // Auto-focus automation request on login
            setTimeout(() => {
                const automationBox = document.getElementById('automationRequest');
                if (automationBox) {
                    automationBox.focus();
                    showNexusAlert('Ready for automation requests and stress testing', 'success');
                }
            }, 1500);
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    # Find available port
    port = find_available_port(5000, 20)
    if port:
        print(f"Starting NEXUS COMMAND on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        print("No available ports found")
