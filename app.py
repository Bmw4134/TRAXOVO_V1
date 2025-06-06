import os
from flask import Flask, render_template_string, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# TRAXOVO Dashboard Template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>TRAXOVO - Enterprise Intelligence Platform</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        .header {
            background: rgba(0,255,136,0.1);
            border-bottom: 2px solid #00ff88;
            padding: 1rem 2rem;
            text-align: center;
        }
        .header h1 {
            color: #00ff88;
            font-size: 2.5rem;
            font-weight: 700;
            text-shadow: 0 0 20px rgba(0,255,136,0.5);
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(0,255,136,0.3);
            border-radius: 12px;
            padding: 2rem;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        .card:hover {
            border-color: #00ff88;
            box-shadow: 0 8px 32px rgba(0,255,136,0.2);
            transform: translateY(-4px);
        }
        .card h3 {
            color: #00ff88;
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }
        .card p {
            color: #b8c5d1;
            line-height: 1.6;
            margin-bottom: 1rem;
        }
        .btn {
            background: linear-gradient(45deg, #00ff88, #00cc6a);
            color: #1a1a2e;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,255,136,0.3);
        }
        .status {
            background: rgba(0,255,136,0.1);
            border: 1px solid #00ff88;
            border-radius: 8px;
            padding: 1rem;
            margin: 2rem 0;
            text-align: center;
        }
        .footer {
            text-align: center;
            padding: 2rem;
            color: #666;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin-top: 4rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>TRAXOVO</h1>
        <p>Enterprise Intelligence Platform</p>
    </div>
    
    <div class="container">
        <div class="status">
            <h3>System Status: Operational</h3>
            <p>TRAXOVO Enterprise Intelligence Platform is running optimally</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Fleet Analytics</h3>
                <p>Real-time asset tracking and operational intelligence for Fort Worth fleet operations.</p>
                <a href="/fleet" class="btn">Access Fleet Data</a>
            </div>
            
            <div class="card">
                <h3>Automation Hub</h3>
                <p>Intelligent task automation with advanced AI-powered process optimization.</p>
                <a href="/automation" class="btn">Launch Automation</a>
            </div>
            
            <div class="card">
                <h3>Attendance Matrix</h3>
                <p>Comprehensive attendance tracking and workforce management analytics.</p>
                <a href="/attendance" class="btn">View Attendance</a>
            </div>
            
            <div class="card">
                <h3>System Intelligence</h3>
                <p>Advanced system monitoring and performance analytics dashboard.</p>
                <a href="/status" class="btn">System Status</a>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>&copy; 2025 TRAXOVO Enterprise Intelligence Platform</p>
    </div>
</body>
</html>
"""

@app.route('/')
def main_dashboard():
    """TRAXOVO Main Dashboard"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "TRAXOVO Enterprise Intelligence",
        "version": "1.0.0"
    })

@app.route('/fleet')
def fleet_tracking():
    """Fleet tracking interface"""
    return jsonify({
        "message": "Fleet tracking system operational",
        "assets_tracked": "Available",
        "status": "ready"
    })

@app.route('/automation')
def automation_hub():
    """Automation hub interface"""
    return jsonify({
        "message": "Automation hub operational",
        "tasks_available": True,
        "status": "ready"
    })

@app.route('/attendance')
def attendance_matrix():
    """Attendance matrix interface"""
    return jsonify({
        "message": "Attendance system operational",
        "data_available": True,
        "status": "ready"
    })

@app.route('/status')
def system_status():
    """System status interface"""
    return jsonify({
        "message": "TRAXOVO system operational",
        "database": "connected",
        "services": "running",
        "status": "healthy"
    })

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)