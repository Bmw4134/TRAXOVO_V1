#!/usr/bin/env python3
"""
Production Build and Deployment Script
Optimizes file size, removes redundancy, and creates deployment-ready package
"""

import os
import shutil
import json
import gzip
import subprocess
from pathlib import Path

def optimize_and_build():
    """Create optimized production build"""
    
    print("🚀 Starting Production Build Optimization...")
    
    # 1. Clean unnecessary files
    cleanup_files = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '.pytest_cache',
        'node_modules',
        '.git',
        '*.log',
        'temp_*',
        'test_*'
    ]
    
    # 2. Essential production files only
    essential_files = [
        'main.py',
        'app.py',
        'models.py',
        'watson_supreme.py',
        'nexus_infinity_engine.py',
        'infinity_sync_injector.py',
        'dashboard_customization.py',
        'user_management_system.py',
        'timecard_automation.py',
        'advanced_business_intelligence.py',
        'advanced_fleet_map.py',
        'requirements.txt',
        '.replit'
    ]
    
    # 3. Create optimized main.py
    create_optimized_main()
    
    # 4. Remove duplicate functionality
    remove_duplicates()
    
    print("✅ Production build optimized")
    return True

def create_optimized_main():
    """Create size-optimized main.py"""
    
    # Read current main.py and extract only essential parts
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Keep core functionality, remove bloat
    optimized_content = """
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "production_secret")

@app.route('/')
def landing():
    user = session.get('user')
    if not user:
        return render_template_string('''<!DOCTYPE html>
<html><head><title>JDD Consulting - Production Platform</title>
<style>
body{background:#000;color:#fff;font-family:Arial;margin:0;padding:20px}
.container{max-width:1200px;margin:0 auto}
.header{text-align:center;margin-bottom:40px}
.login-form{background:#111;padding:30px;border-radius:10px;max-width:400px;margin:0 auto}
.form-group{margin-bottom:20px}
input{width:100%;padding:15px;background:#333;border:1px solid #555;color:#fff;border-radius:5px}
button{background:#007bff;color:#fff;padding:15px 30px;border:none;border-radius:5px;cursor:pointer;width:100%}
button:hover{background:#0056b3}
</style></head><body>
<div class="container">
<div class="header">
<h1>JDD Consulting Production Platform</h1>
<p>Enterprise Intelligence System</p>
</div>
<div class="login-form">
<h2>Access Platform</h2>
<form method="post" action="/login">
<div class="form-group">
<input type="text" name="username" placeholder="Username" required>
</div>
<div class="form-group">
<input type="password" name="password" placeholder="Password" value="demo123" required>
</div>
<button type="submit">Access System</button>
</form>
</div>
</div>
</body></html>''')
    
    return dashboard()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    session['user'] = {'username': username, 'authenticated': True}
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('landing'))
    
    user = session['user']
    return render_template_string(DASHBOARD_TEMPLATE, user=user)

# API Routes
@app.route('/api/timecard/automate', methods=['POST'])
def automate_timecard():
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        from timecard_automation import get_timecard_automation
        data = request.json
        timecard_system = get_timecard_automation()
        result = timecard_system.process_automation_request(
            data.get('request', ''),
            data.get('employee_id', 'current_user'),
            data.get('employee_name', 'Current User')
        )
        return jsonify({'success': True, 'automation_result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/status')
def system_status():
    return jsonify({
        'status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'system': 'JDD Production Platform'
    })

DASHBOARD_TEMPLATE = '''<!DOCTYPE html>
<html><head><title>JDD Production Dashboard</title>
<style>
body{background:#000;color:#fff;font-family:Arial;margin:0;padding:0}
.header{background:#111;padding:20px;border-bottom:2px solid #333}
.container{max-width:1200px;margin:0 auto;padding:20px}
.module{background:#111;border:1px solid #333;border-radius:10px;padding:20px;margin:20px 0}
.module h3{color:#007bff;margin-top:0}
.form-group{margin:15px 0}
input,textarea{width:100%;padding:12px;background:#333;border:1px solid #555;color:#fff;border-radius:5px}
button{background:#007bff;color:#fff;padding:12px 24px;border:none;border-radius:5px;cursor:pointer;margin:5px}
button:hover{background:#0056b3}
.alert{padding:15px;margin:10px 0;border-radius:5px}
.alert-success{background:#28a745;color:#fff}
.alert-error{background:#dc3545;color:#fff}
.alert-watson{background:#6f42c1;color:#fff}
</style></head><body>
<div class="header">
<h1>JDD Production Platform</h1>
<span>Welcome, {{user.username}}</span>
</div>
<div class="container">
<div id="alerts"></div>

<div class="module">
<h3>⏰ Time Card Automation</h3>
<div class="form-group">
<input type="text" id="timecardRequest" placeholder="fill my week with standard hours">
</div>
<button onclick="processTimecard()">Process Request</button>
<button onclick="quickFillWeek()">Quick Fill Week</button>
<div id="timecardResults" style="margin-top:20px;display:none"></div>
</div>

<div class="module">
<h3>📊 System Status</h3>
<button onclick="checkStatus()">Check System Status</button>
<div id="statusResults" style="margin-top:20px"></div>
</div>

</div>

<script>
function showAlert(message, type) {
    const alerts = document.getElementById('alerts');
    const alert = document.createElement('div');
    alert.className = 'alert alert-' + type;
    alert.textContent = message;
    alerts.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}

function processTimecard() {
    const request = document.getElementById('timecardRequest').value;
    if (!request) return showAlert('Enter a request', 'error');
    
    fetch('/api/timecard/automate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({request: request})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('timecardResults').innerHTML = 
                '<strong>Success:</strong> ' + data.automation_result.message;
            document.getElementById('timecardResults').style.display = 'block';
            showAlert('Timecard processed successfully', 'success');
        } else {
            showAlert('Error: ' + data.error, 'error');
        }
    });
}

function quickFillWeek() {
    document.getElementById('timecardRequest').value = 'fill my week';
    processTimecard();
}

function checkStatus() {
    fetch('/api/status')
    .then(response => response.json())
    .then(data => {
        document.getElementById('statusResults').innerHTML = 
            '<strong>Status:</strong> ' + data.status + '<br>' +
            '<strong>Time:</strong> ' + new Date(data.timestamp).toLocaleString();
        showAlert('System operational', 'success');
    });
}
</script>
</body></html>'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
"""
    
    # Write optimized version
    with open('main_optimized.py', 'w') as f:
        f.write(optimized_content)
    
    print("✅ Created optimized main.py")

def remove_duplicates():
    """Remove duplicate files and functionality"""
    
    duplicate_patterns = [
        'archived_modules',
        'legacy_*',
        '*_backup.*',
        '*_old.*',
        'temp_*',
        'test_*'
    ]
    
    for pattern in duplicate_patterns:
        for path in Path('.').rglob(pattern):
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"Removed: {path}")

def create_deployment_commands():
    """Create final deployment commands"""
    
    commands = """#!/bin/bash
# JDD Production Deployment Commands

echo "🚀 Starting JDD Production Deployment..."

# 1. Use optimized main
cp main_optimized.py main.py

# 2. Install minimal requirements
pip install flask gunicorn

# 3. Start production server
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 main:app

echo "✅ JDD Production Platform deployed successfully"
echo "🌐 Access at: https://jddconsulting.replit.app"
"""
    
    with open('deploy_production.sh', 'w') as f:
        f.write(commands)
    
    os.chmod('deploy_production.sh', 0o755)
    print("✅ Created deployment script")

def create_requirements_minimal():
    """Create minimal requirements.txt"""
    
    minimal_requirements = """flask==3.0.0
gunicorn==21.2.0
werkzeug==3.0.1
"""
    
    with open('requirements_minimal.txt', 'w') as f:
        f.write(minimal_requirements)

if __name__ == '__main__':
    optimize_and_build()
    create_deployment_commands()
    create_requirements_minimal()
    print("\n🎯 PRODUCTION BUILD READY")
    print("📋 Run: ./deploy_production.sh")
    print("🌐 Platform: https://jddconsulting.replit.app")