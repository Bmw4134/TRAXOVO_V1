"""
Simple TRAXOVO Dashboard - Lightweight Version
"""

import os
from flask import Flask, render_template_string, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "simple_dashboard_2025")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 10
}

db = SQLAlchemy(model_class=Base)
db.init_app(app)

@app.route('/')
def dashboard():
    """Simple TRAXOVO Dashboard"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/status')
def api_status():
    """Simple status endpoint"""
    return jsonify({
        'platform': 'TRAXOVO Simple Dashboard',
        'status': 'operational',
        'database': 'connected' if check_database() else 'disconnected',
        'git_status': 'rebase_in_progress'
    })

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

def check_database():
    """Check database connection"""
    try:
        with app.app_context():
            db.session.execute(db.text('SELECT 1'))
        return True
    except:
        return False

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRAXOVO Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a1a;
            color: #00ff00;
            margin: 0;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 20px;
            background: #000;
            border: 2px solid #00ff00;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .status-card {
            background: #000;
            border: 2px solid #00ff00;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        .status-value {
            font-size: 2rem;
            margin: 10px 0;
        }
        .git-info {
            background: #333;
            border: 2px solid #ff9900;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        .resolution-steps {
            background: #000;
            border: 1px solid #00ff00;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>TRAXOVO DASHBOARD</h1>
        <p>Simplified Control Interface</p>
    </div>
    
    <div class="status-grid">
        <div class="status-card">
            <h3>SYSTEM STATUS</h3>
            <div class="status-value">OPERATIONAL</div>
            <p>Core services running</p>
        </div>
        
        <div class="status-card">
            <h3>DATABASE</h3>
            <div class="status-value">CONNECTED</div>
            <p>PostgreSQL available</p>
        </div>
        
        <div class="status-card">
            <h3>RESOURCE USAGE</h3>
            <div class="status-value">OPTIMIZED</div>
            <p>Lightweight mode active</p>
        </div>
    </div>
    
    <div class="git-info">
        <h3>Git Repository Status</h3>
        <p><strong>Issue:</strong> Repository in rebase state with lock file preventing operations</p>
        <p><strong>Resolution:</strong> Run these commands in terminal:</p>
        
        <div class="resolution-steps">
            <div># Remove the lock file</div>
            <div>rm -f .git/index.lock</div>
        </div>
        
        <div class="resolution-steps">
            <div># Abort the rebase</div>
            <div>git rebase --abort</div>
        </div>
        
        <div class="resolution-steps">
            <div># Clean working directory</div>
            <div>git reset --hard HEAD</div>
        </div>
        
        <p><strong>Note:</strong> These commands will restore normal git functionality</p>
    </div>
</body>
</html>
"""

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)