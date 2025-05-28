from flask import Flask, request, session, redirect, render_template_string
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traxovo_secret")

# Simple dashboard template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html data-bs-theme="dark">
<head>
    <title>TRAXOVO Dashboard</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
</head>
<body>
    <div class="container-fluid p-4">
        <div class="row mb-4">
            <div class="col">
                <h1 class="text-primary">TRAXOVO Fleet Management</h1>
                <p class="text-muted">Multi-Company Operations Dashboard</p>
            </div>
            <div class="col-auto">
                <a href="/logout" class="btn btn-outline-secondary">Logout</a>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card">
                    <div class="card-body text-center">
                        <h2 class="text-success">657</h2>
                        <p class="mb-0">Active GPS Assets</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card">
                    <div class="card-body text-center">
                        <h2 class="text-info">52</h2>
                        <p class="mb-0">Job Sites</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card">
                    <div class="card-body text-center">
                        <h2 class="text-warning">3</h2>
                        <p class="mb-0">Companies</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card">
                    <div class="card-body text-center">
                        <h2 class="text-primary">3</h2>
                        <p class="mb-0">Divisions</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Companies</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li class="mb-2">🏗️ <strong>Ragle Inc</strong></li>
                            <li class="mb-2">🔧 <strong>Select Maintenance</strong></li>
                            <li class="mb-2">⚡ <strong>Unified Specialties</strong></li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Geographic Divisions</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li class="mb-2">📍 <strong>DIV 2 (DFW)</strong> - Dallas Fort Worth</li>
                            <li class="mb-2">📍 <strong>DIV 3 (WTX)</strong> - West Texas</li>
                            <li class="mb-2">📍 <strong>DIV 4 (HOU)</strong> - Houston</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

LOGIN_HTML = '''
<!DOCTYPE html>
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
                    <h1 class="text-primary text-center mb-4">TRAXOVO</h1>
                    <p class="text-center text-muted mb-4">Fleet Management Portal</p>
                    
                    <form method="POST">
                        <div class="mb-3">
                            <input type="text" name="username" class="form-control" value="admin" placeholder="Username">
                        </div>
                        <div class="mb-3">
                            <input type="password" name="password" class="form-control" placeholder="Password">
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Access Dashboard</button>
                    </form>
                    
                    <div class="text-center mt-4">
                        <small class="text-success">System Ready • 657 Assets Online</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == "admin" and password == "TRAXOVO_Fleet_2025!@#":
            session['authenticated'] = True
            session['user'] = username
            return redirect('/')
    
    return render_template_string(LOGIN_HTML)

@app.route('/')
def dashboard():
    if 'authenticated' not in session:
        return redirect('/login')
    return render_template_string(DASHBOARD_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)