from flask import Flask, request, session, redirect, render_template_string
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traxovo_secret")

# Complete working dashboard
DASHBOARD = '''<!DOCTYPE html>
<html data-bs-theme="dark">
<head>
    <title>TRAXOVO Fleet Management</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-primary">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">TRAXOVO Fleet Management</span>
            <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
        </div>
    </nav>
    
    <div class="container-fluid p-4">
        <div class="row mb-4">
            <div class="col-md-2">
                <div class="card bg-success">
                    <div class="card-body text-center text-white">
                        <h2>657</h2>
                        <p class="mb-0">GPS Assets</p>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card bg-info">
                    <div class="card-body text-center text-white">
                        <h2>52</h2>
                        <p class="mb-0">Job Sites</p>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card bg-warning">
                    <div class="card-body text-center text-dark">
                        <h2>3</h2>
                        <p class="mb-0">Companies</p>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card bg-secondary">
                    <div class="card-body text-center text-white">
                        <h2>3</h2>
                        <p class="mb-0">Divisions</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5>System Status</h5>
                        <span class="badge bg-success">Online</span>
                        <span class="badge bg-success">API Connected</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5>Companies</h5>
                    </div>
                    <div class="card-body">
                        <div class="list-group list-group-flush">
                            <div class="list-group-item d-flex justify-content-between">
                                <span>🏗️ Ragle Inc</span>
                                <span class="badge bg-success">Active</span>
                            </div>
                            <div class="list-group-item d-flex justify-content-between">
                                <span>🔧 Select Maintenance</span>
                                <span class="badge bg-success">Active</span>
                            </div>
                            <div class="list-group-item d-flex justify-content-between">
                                <span>⚡ Unified Specialties</span>
                                <span class="badge bg-success">Active</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5>Geographic Divisions</h5>
                    </div>
                    <div class="card-body">
                        <div class="list-group list-group-flush">
                            <div class="list-group-item d-flex justify-content-between">
                                <span>📍 DIV 2 (DFW)</span>
                                <span class="badge bg-success">219 Assets</span>
                            </div>
                            <div class="list-group-item d-flex justify-content-between">
                                <span>📍 DIV 3 (WTX)</span>
                                <span class="badge bg-success">219 Assets</span>
                            </div>
                            <div class="list-group-item d-flex justify-content-between">
                                <span>📍 DIV 4 (HOU)</span>
                                <span class="badge bg-success">219 Assets</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-warning text-dark">
                        <h5>Quick Actions</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <button class="btn btn-primary">Daily Driver Reports</button>
                            <button class="btn btn-info">Equipment Billing</button>
                            <button class="btn btn-success">GPS Tracking</button>
                            <button class="btn btn-secondary">Work Zone Analysis</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

LOGIN = '''<!DOCTYPE html>
<html data-bs-theme="dark">
<head>
    <title>TRAXOVO Login</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; }
        .login-card { background: rgba(33, 37, 41, 0.95); border: 1px solid rgba(255, 255, 255, 0.1); }
        .form-control { background-color: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); color: white; }
    </style>
</head>
<body>
    <div class="container-fluid d-flex align-items-center justify-content-center min-vh-100">
        <div class="col-md-4">
            <div class="card login-card">
                <div class="card-body p-5">
                    <h1 class="text-primary text-center mb-2">TRAXOVO</h1>
                    <p class="text-center text-muted mb-4">Fleet Management Portal</p>
                    <div class="text-center mb-4">
                        <small class="text-success">Ragle Inc • Select Maintenance • Unified Specialties</small>
                    </div>
                    
                    <form method="POST" action="/login">
                        <div class="mb-3">
                            <input type="text" name="username" class="form-control" value="admin" placeholder="Username">
                        </div>
                        <div class="mb-3">
                            <input type="password" name="password" class="form-control" placeholder="Password">
                        </div>
                        <button type="submit" class="btn btn-primary w-100 btn-lg">Access Dashboard</button>
                    </form>
                    
                    <div class="text-center mt-4">
                        <small class="text-success">✅ 657 GPS Assets Online</small>
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
    
    return render_template_string(LOGIN)

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