from flask import Blueprint, request, session, redirect

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/direct-login', methods=['POST'])
def direct_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username == "admin" and password == "TRAXOVO_Fleet_2025!@#":
        session['authenticated'] = True
        session['user'] = username
        return redirect('/')

    return "Login failed", 403

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return '''<!DOCTYPE html>
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
                    
                    <form method="POST" action="/auth/direct-login">
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