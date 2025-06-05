"""
Working TRAXOVO Dashboard - Direct Routes
Bypasses all complex routing and JavaScript issues
"""

from flask import Flask

app = Flask(__name__)

@app.route('/dashboard')
def clean_dashboard():
    """Clean working dashboard without JavaScript dependencies"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>TRAXOVO Dashboard</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #000, #1a1a2e); color: white; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: rgba(0,0,0,0.8); border: 2px solid #00ff88; border-radius: 15px; padding: 30px; }
        .header { text-align: center; margin-bottom: 30px; padding: 20px; background: rgba(0,255,136,0.1); border-radius: 10px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: rgba(0,0,0,0.6); border: 1px solid #00ff88; border-radius: 10px; padding: 20px; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,255,136,0.3); }
        .card-title { color: #00ff88; font-size: 1.2em; margin-bottom: 10px; font-weight: bold; }
        .card-desc { color: #ccc; margin-bottom: 15px; }
        .btn { background: #00ff88; color: #000; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; display: block; text-align: center; }
        .btn:hover { background: #00cc70; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>TRAXOVO Intelligence Platform</h1>
            <h2>Construction Intelligence Dashboard</h2>
            <p>Comprehensive operational intelligence and fleet management</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <div class="card-title">Master Brain Intelligence</div>
                <div class="card-desc">Core AI intelligence and decision-making system</div>
                <a href="/master-brain" target="_blank" class="btn">Access Dashboard</a>
            </div>
            
            <div class="card">
                <div class="card-title">Fleet Operations</div>
                <div class="card-desc">Fort Worth fleet management with GAUGE API</div>
                <a href="/gauge-assets" target="_blank" class="btn">View Fleet Data</a>
            </div>
            
            <div class="card">
                <div class="card-title">Failure Analysis</div>
                <div class="card-desc">Equipment failure prediction and maintenance</div>
                <a href="/failure-analysis" target="_blank" class="btn">Analyze Equipment</a>
            </div>
            
            <div class="card">
                <div class="card-title">Dashboard Customization</div>
                <div class="card-desc">Personalized dashboard layouts</div>
                <a href="/dashboard-customizer" target="_blank" class="btn">Customize Dashboards</a>
            </div>
            
            <div class="card">
                <div class="card-title">GitHub DWC Sync</div>
                <div class="card-desc">Repository synchronization control</div>
                <a href="/github-sync" target="_blank" class="btn">Sync Repositories</a>
            </div>
            
            <div class="card">
                <div class="card-title">KAIZEN TRD System</div>
                <div class="card-desc">Total Replication Dashboard automation</div>
                <a href="/trd" target="_blank" class="btn">Access TRD</a>
            </div>
            
            <div class="card">
                <div class="card-title">BMI Intelligence Sweep</div>
                <div class="card-desc">Business intelligence analysis</div>
                <a href="/bmi/sweep" target="_blank" class="btn">Run BMI Sweep</a>
            </div>
            
            <div class="card">
                <div class="card-title">Watson Command Console</div>
                <div class="card-desc">AI command and control interface</div>
                <a href="/watson/console" target="_blank" class="btn">Open Console</a>
            </div>
            
            <div class="card">
                <div class="card-title">User Management</div>
                <div class="card-desc">Role-based access control</div>
                <a href="/role-management" target="_blank" class="btn">Manage Users</a>
            </div>
            
            <div class="card">
                <div class="card-title">Watson Force Render</div>
                <div class="card-desc">DOM injection and visibility control</div>
                <a href="/watson/force-render" target="_blank" class="btn">Force Render</a>
            </div>
            
            <div class="card">
                <div class="card-title">System Inspector</div>
                <div class="card-desc">Module inspection and debugging</div>
                <a href="/bare-bones-inspector" target="_blank" class="btn">Inspect System</a>
            </div>
            
            <div class="card">
                <div class="card-title">Internal Integration</div>
                <div class="card-desc">Repository integration controls</div>
                <a href="/internal-repos" target="_blank" class="btn">Open Integration</a>
            </div>
        </div>
    </div>
</body>
</html>'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)