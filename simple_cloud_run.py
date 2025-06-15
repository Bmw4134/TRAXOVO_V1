#!/usr/bin/env python3
"""
Simple Cloud Run deployment - one command solution
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "nexus_watson_supreme_production")

# User credentials
USERS = {
    'watson': {'password': 'Btpp@1513', 'name': 'Watson Supreme'},
    'demo': {'password': 'demo123', 'name': 'Demo User'}
}

@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Nexus Watson</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea, #764ba2); margin: 0; padding: 100px 0; }
        .login { max-width: 400px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .login h1 { text-align: center; color: #333; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        .form-group input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        .btn { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 5px; cursor: pointer; }
    </style>
    </head>
    <body>
        <div class="login">
            <h1>NEXUS WATSON</h1>
            <form method="POST" action="/login">
                <div class="form-group">
                    <input type="text" name="username" placeholder="Username" required>
                </div>
                <div class="form-group">
                    <input type="password" name="password" placeholder="Password" required>
                </div>
                <button type="submit" class="btn">Access Platform</button>
            </form>
            <p style="text-align: center; margin-top: 20px; color: #666; font-size: 14px;">
                Demo: watson/Btpp@1513 or demo/demo123
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').lower()
    password = request.form.get('password', '')
    
    if username in USERS and USERS[username]['password'] == password:
        session['user'] = {'username': username, 'name': USERS[username]['name']}
        return redirect('/dashboard')
    
    flash('Invalid credentials')
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    
    user = session['user']
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Watson Command Center</title>
    <style>
        body {{ font-family: Arial; background: linear-gradient(135deg, #1a1a2e, #0f3460); color: white; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }}
        .header h1 {{ color: #00ffff; text-shadow: 0 0 10px #00ffff; margin: 0; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; border: 1px solid rgba(0,255,255,0.3); text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #00ffff; }}
        .metric-label {{ color: #ccc; margin-top: 5px; }}
        .export-section {{ background: linear-gradient(135deg, #667eea, #764ba2); padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .export-buttons {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }}
        .export-btn {{ background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 12px 20px; border-radius: 8px; text-decoration: none; text-align: center; display: block; }}
        .export-btn:hover {{ background: rgba(255,255,255,0.3); }}
        .logout {{ position: absolute; top: 20px; right: 20px; background: rgba(255,0,0,0.2); border: 1px solid rgba(255,0,0,0.5); color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; }}
    </style>
    </head>
    <body>
        <a href="/logout" class="logout">Logout</a>
        <div class="container">
            <div class="header">
                <h1>WATSON COMMAND CENTER</h1>
                <p>Welcome, {user['name']} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">97.3%</div>
                    <div class="metric-label">Fleet Efficiency</div>
                </div>
                <div class="metric">
                    <div class="metric-value">47</div>
                    <div class="metric-label">Total Assets</div>
                </div>
                <div class="metric">
                    <div class="metric-value">$347K</div>
                    <div class="metric-label">Cost Savings YTD</div>
                </div>
                <div class="metric">
                    <div class="metric-value">98.7%</div>
                    <div class="metric-label">Quantum Coherence</div>
                </div>
            </div>
            
            <div class="export-section">
                <h3 style="margin: 0 0 15px 0;">Intelligence Export Hub</h3>
                <p style="opacity: 0.8; margin: 0 0 15px 0;">Export data for dashboard integration</p>
                <div class="export-buttons">
                    <a href="/api/export/json" class="export-btn">JSON Export</a>
                    <a href="/api/export/csv" class="export-btn">CSV Export</a>
                    <a href="/api/export/full" class="export-btn">Full Intelligence Data</a>
                    <button onclick="copyApi()" class="export-btn" style="border: none; cursor: pointer;">Copy API URL</button>
                </div>
            </div>
            
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;">
                <h4 style="color: #00ffff; margin-top: 0;">Real-time API Endpoints</h4>
                <ul style="color: #ccc; line-height: 1.6;">
                    <li>/api/status - System status</li>
                    <li>/api/fleet - Fleet data</li>
                    <li>/api/export/full - Complete intelligence</li>
                </ul>
            </div>
        </div>
        
        <script>
            function copyApi() {{
                navigator.clipboard.writeText(window.location.origin + '/api/export/full');
                alert('API URL copied!');
            }}
        </script>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# API Endpoints
@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'operational',
        'quantum_coherence': '98.7%',
        'fleet_efficiency': '97.3%',
        'cost_optimization': '$347,320',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/fleet')
def api_fleet():
    return jsonify({
        'total_assets': 47,
        'operational': 43,
        'maintenance': 3,
        'critical': 1,
        'efficiency': 97.3,
        'cost_savings': 347320,
        'locations': [
            {'id': 'EX-001', 'type': 'Excavator', 'status': 'operational', 'utilization': 94.2},
            {'id': 'DZ-003', 'type': 'Dozer', 'status': 'operational', 'utilization': 87.5},
            {'id': 'GR-002', 'type': 'Grader', 'status': 'operational', 'utilization': 91.3}
        ]
    })

@app.route('/api/export/json')
def export_json():
    data = {
        'fleet_status': {'total_assets': 47, 'operational': 43, 'efficiency': 97.3},
        'financial_metrics': {'cost_savings': 347320, 'roi': 24.8},
        'timestamp': datetime.now().isoformat()
    }
    response = app.response_class(
        response=str(data).replace("'", '"'),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=nexus_export.json'}
    )
    return response

@app.route('/api/export/csv')
def export_csv():
    csv_data = "Category,Metric,Value\nFleet,Total Assets,47\nFleet,Operational,43\nFleet,Efficiency,97.3\nFinancial,Cost Savings,347320"
    response = app.response_class(
        response=csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=nexus_export.csv'}
    )
    return response

@app.route('/api/export/full')
def export_full():
    return jsonify({
        'metadata': {'timestamp': datetime.now().isoformat(), 'version': '2.1.0'},
        'fleet_status': {'total_assets': 47, 'operational': 43, 'efficiency': 97.3},
        'financial_metrics': {'cost_savings': 347320, 'roi': 24.8},
        'performance_kpis': {'quantum_coherence': 98.7, 'uptime': 99.94}
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)