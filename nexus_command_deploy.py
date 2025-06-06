"""
NEXUS COMMAND Complete Deployment Script
Resolves all issues and deploys working platform
"""

import os
import subprocess
import time

def kill_existing_processes():
    """Kill any existing processes on port 5000"""
    try:
        # Use fuser to kill processes on port 5000
        subprocess.run(['fuser', '-k', '5000/tcp'], capture_output=True)
        time.sleep(2)
    except:
        pass
    
    try:
        # Alternative method using netstat and kill
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if ':5000 ' in line and 'LISTEN' in line:
                parts = line.split()
                if len(parts) > 6:
                    pid_info = parts[6]
                    if '/' in pid_info:
                        pid = pid_info.split('/')[0]
                        try:
                            subprocess.run(['kill', '-9', pid], capture_output=True)
                        except:
                            pass
    except:
        pass

def create_nexus_main():
    """Create the main NEXUS COMMAND application file"""
    nexus_main_content = '''"""
NEXUS COMMAND - Intelligence Platform
Complete deployment with error-free JavaScript
"""

import os
from datetime import datetime
from flask import Flask, request, session, redirect, url_for, jsonify, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'nexus-command-2025')

# User authentication
users = {
    'troy': {'password': 'troy2025', 'role': 'exec', 'name': 'Troy'},
    'william': {'password': 'william2025', 'role': 'exec', 'name': 'William'},
    'james': {'password': 'james2025', 'role': 'exec', 'name': 'James'},
    'chris': {'password': 'chris2025', 'role': 'exec', 'name': 'Chris'},
    'admin': {'password': 'admin123', 'role': 'admin', 'name': 'Administrator'},
    'ops': {'password': 'ops123', 'role': 'ops', 'name': 'Operations'}
}

watson_access = {
    'watson': {
        'password': 'proprietary_watson_2025', 
        'role': 'dev_admin_master',
        'watson_access': True,
        'name': 'Watson Dev Admin Master'
    }
}

@app.route('/')
def home():
    if 'user' not in session:
        return render_template_string(landing_template)
    
    user = session['user']
    return render_template_string(dashboard_template, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in watson_access and watson_access[username]['password'] == password:
            session['user'] = watson_access[username]
            return redirect(url_for('home'))
        
        if username in users and users[username]['password'] == password:
            session['user'] = users[username]
            return redirect(url_for('home'))
        
        return render_template_string(login_template, error="Invalid credentials")
    
    return render_template_string(login_template)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/fleet/data')
def get_fleet_data():
    return jsonify({
        'assets': 717,
        'active': 684,
        'zones': 5,
        'status': 'operational'
    })

landing_template = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS COMMAND - Intelligence Platform</title>
    <style>
        body { margin: 0; background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%); color: white; font-family: Arial; height: 100vh; display: flex; align-items: center; justify-content: center; }
        .landing { text-align: center; }
        .logo { font-size: 48px; color: #00ff64; margin-bottom: 20px; text-shadow: 0 0 20px rgba(0,255,100,0.5); }
        .tagline { font-size: 24px; margin-bottom: 40px; opacity: 0.8; }
        .login-btn { background: #00ff64; color: black; padding: 15px 30px; border: none; border-radius: 8px; font-size: 18px; cursor: pointer; text-decoration: none; display: inline-block; }
        .login-btn:hover { background: #00ff88; }
    </style>
</head>
<body>
    <div class="landing">
        <h1 class="logo">NEXUS COMMAND</h1>
        <p class="tagline">Intelligent Operations Command Center</p>
        <a href="/login" class="login-btn">Access Platform</a>
    </div>
</body>
</html>
"""

login_template = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS COMMAND Login</title>
    <style>
        body { margin: 0; background: #0a0a0a; color: white; font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .login-container { background: #1a1a2e; padding: 40px; border-radius: 15px; border: 2px solid #00ff64; }
        .login-title { color: #00ff64; text-align: center; margin-bottom: 30px; font-size: 24px; }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 5px; color: #00ff64; }
        input { width: 300px; padding: 12px; background: #2a2a4e; color: white; border: 1px solid #555; border-radius: 5px; }
        .login-btn { width: 100%; background: #00ff64; color: black; padding: 12px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; }
        .error { color: #ff4444; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2 class="login-title">NEXUS COMMAND</h2>
        <form method="POST">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="login-btn">Access System</button>
        </form>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
    </div>
</body>
</html>
"""

dashboard_template = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS COMMAND - Dashboard</title>
    <style>
        body { margin: 0; background: linear-gradient(135deg, rgba(0, 20, 50, 0.95) 0%, rgba(20, 0, 50, 0.95) 100%); color: white; font-family: Arial; min-height: 100vh; }
        .header { background: rgba(0, 30, 60, 0.9); padding: 20px 40px; border-bottom: 2px solid #00ff64; display: flex; justify-content: space-between; align-items: center; }
        .logo { color: #00ff64; font-size: 28px; font-weight: bold; }
        .user-info { color: white; }
        .nav { background: rgba(0, 30, 60, 0.7); padding: 15px 40px; }
        .nav-item { color: white; text-decoration: none; margin-right: 30px; padding: 10px 15px; border-radius: 5px; transition: all 0.3s; }
        .nav-item:hover { background: rgba(0, 255, 100, 0.2); }
        .content { padding: 40px; display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 30px; max-width: 1200px; margin: 0 auto; }
        .module { background: rgba(30, 42, 71, 0.8); border: 1px solid rgba(0, 255, 100, 0.3); border-radius: 12px; padding: 30px; transition: all 0.3s; }
        .module:hover { transform: translateY(-5px); border-color: #00ff64; }
        .module-title { color: #00ff64; font-size: 20px; margin-bottom: 10px; }
        .module-desc { opacity: 0.8; margin-bottom: 20px; }
        .btn { background: #00ff64; color: black; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn:hover { background: #00ff88; }
        .logout-btn { background: #dc3545; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">NEXUS COMMAND</div>
        <div class="user-info">
            {{ user.name }} ({{ user.role }})
            <a href="/logout" class="btn logout-btn" style="margin-left: 20px;">Logout</a>
        </div>
    </div>
    
    <nav class="nav">
        <a href="/" class="nav-item">Command Center</a>
        <a href="/fleet" class="nav-item">Fleet Operations</a>
        <a href="/analytics" class="nav-item">Analytics Engine</a>
        <a href="/assets" class="nav-item">Asset Intelligence</a>
    </nav>
    
    <div class="content">
        <div class="module">
            <div class="module-title">Executive Dashboard</div>
            <div class="module-desc">Strategic command center for executive decision-making</div>
            <div style="margin: 20px 0;">
                <div style="display: flex; gap: 20px;">
                    <div style="text-align: center;">
                        <div style="font-size: 24px; color: #00ff64;">717</div>
                        <div style="font-size: 12px;">Assets</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 24px; color: #00ff64;">99.5%</div>
                        <div style="font-size: 12px;">Uptime</div>
                    </div>
                </div>
            </div>
            <a href="#" class="btn">Launch Dashboard</a>
        </div>
        
        <div class="module">
            <div class="module-title">Fleet Management</div>
            <div class="module-desc">Real-time fleet command and asset intelligence</div>
            <div style="margin: 20px 0;">
                <div style="display: flex; gap: 20px;">
                    <div style="text-align: center;">
                        <div style="font-size: 24px; color: #00ff64;">684</div>
                        <div style="font-size: 12px;">Active</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 24px; color: #00ff64;">5</div>
                        <div style="font-size: 12px;">Zones</div>
                    </div>
                </div>
            </div>
            <a href="#" class="btn">Fleet Command</a>
        </div>
        
        <div class="module">
            <div class="module-title">Analytics Engine</div>
            <div class="module-desc">Advanced data intelligence and predictive analytics</div>
            <div style="margin: 20px 0;">
                <div style="height: 100px; background: rgba(0, 255, 100, 0.1); border: 1px solid #00ff64; border-radius: 5px; display: flex; align-items: center; justify-content: center;">
                    Performance Chart
                </div>
            </div>
            <a href="#" class="btn">View Analytics</a>
        </div>
        
        {% if user.watson_access %}
        <div class="module" style="border-color: #ff6b35;">
            <div class="module-title" style="color: #ff6b35;">Watson Console</div>
            <div class="module-desc">Exclusive Watson dev admin master access</div>
            <div style="margin: 20px 0;">
                <div style="color: #ff6b35; font-weight: bold;">{{ user.role.upper() }}</div>
                <div style="font-size: 12px;">Access Level</div>
            </div>
            <a href="#" class="btn" style="background: #ff6b35;">Master Console</a>
        </div>
        {% endif %}
    </div>
    
    <script>
        console.log('NEXUS COMMAND platform operational');
        
        function showNotification(message) {
            const notification = document.createElement('div');
            notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #00ff64; color: black; padding: 15px 20px; border-radius: 8px; z-index: 10000;';
            notification.textContent = message;
            document.body.appendChild(notification);
            setTimeout(() => notification.remove(), 3000);
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            showNotification('NEXUS COMMAND system initialized');
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
'''
    
    with open('nexus_main.py', 'w') as f:
        f.write(nexus_main_content)

def deploy_nexus_command():
    """Complete NEXUS COMMAND deployment"""
    
    print("NEXUS COMMAND DEPLOYMENT")
    print("=" * 40)
    
    # Kill existing processes
    print("1. Clearing port 5000...")
    kill_existing_processes()
    
    # Create main application
    print("2. Creating NEXUS COMMAND application...")
    create_nexus_main()
    
    # Update main entry point
    print("3. Updating main entry point...")
    with open('main.py', 'w') as f:
        f.write("""from nexus_main import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
""")
    
    print("4. NEXUS COMMAND platform ready for deployment")
    print("\nLogin Credentials:")
    print("James: james / james2025")
    print("Chris: chris / chris2025")
    print("Watson: watson / proprietary_watson_2025")
    
    return True

if __name__ == "__main__":
    deploy_nexus_command()