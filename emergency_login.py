from flask import Flask, request, session, redirect, render_template_string
import os
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config['WTF_CSRF_ENABLED'] = False
app.secret_key = os.environ.get("SESSION_SECRET", "emergency_secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

LOGIN_FORM = '''<!DOCTYPE html>
<html data-bs-theme="dark">
<head>
    <title>TRAXOVO Login</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; }
        .login-card { background: rgba(33, 37, 41, 0.95); border: 1px solid rgba(255, 255, 255, 0.1); }
        .form-control { background-color: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); color: white; }
    </style>
</head>
<body>
    <div class="container-fluid d-flex align-items-center justify-content-center min-vh-100">
        <div class="col-md-4">
            <div class="card login-card">
                <div class="card-body p-5">
                    <h1 class="text-primary text-center mb-4">TRAXOVO</h1>
                    <p class="text-center text-muted mb-4">Ragle Inc • Select Maintenance • Unified Specialties</p>
                    
                    <form method="POST" action="/login">
                        <div class="mb-3">
                            <input type="text" name="username" class="form-control" value="admin" placeholder="Username">
                        </div>
                        <div class="mb-3">
                            <input type="password" name="password" class="form-control" placeholder="Password">
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Access Dashboard</button>
                    </form>
                    
                    <div class="text-center mt-3">
                        <small class="text-success">GPS Assets: 657 Active</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

DASHBOARD = '''<!DOCTYPE html>
<html data-bs-theme="dark">
<head>
    <title>TRAXOVO Dashboard</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
</head>
<body>
    <div class="container-fluid p-4">
        <h1 class="text-primary mb-4">TRAXOVO Fleet Management</h1>
        <div class="row">
            <div class="col-md-3">
                <div class="card">
                    <div class="card-body text-center">
                        <h3 class="text-success">657</h3>
                        <p>GPS Assets</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card">
                    <div class="card-body text-center">
                        <h3 class="text-info">52</h3>
                        <p>Job Sites</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5>Multi-Company Operations</h5>
                        <ul>
                            <li>Ragle Inc</li>
                            <li>Select Maintenance</li>
                            <li>Unified Specialties</li>
                        </ul>
                        <h5>Divisions</h5>
                        <ul>
                            <li>DIV 2 (DFW)</li>
                            <li>DIV 3 (WTX)</li>
                            <li>DIV 4 (HOU)</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == "admin" and password == "TRAXOVO_Fleet_2025!@#":
            session['authenticated'] = True
            session['user'] = username
            return redirect('/')
            
    return render_template_string(LOGIN_FORM)

@app.route('/')
def dashboard():
    if 'authenticated' not in session:
        return redirect('/login')
    
    return render_template_string(DASHBOARD)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)