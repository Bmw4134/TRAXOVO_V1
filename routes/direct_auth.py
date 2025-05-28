from flask import Blueprint, request, session, redirect, url_for, render_template_string
from flask_wtf.csrf import csrf_exempt

auth_bp = Blueprint('auth', __name__)

DIRECT_LOGIN_PAGE = '''<!DOCTYPE html>
<html data-bs-theme="dark">
<head>
    <title>TRAXOVO Fleet Management</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
            min-height: 100vh; 
            color: #ffffff; 
        }
        .login-card { 
            background: rgba(33, 37, 41, 0.95); 
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
        }
        .form-control { 
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #ffffff; 
        }
        .form-control:focus {
            background-color: rgba(255, 255, 255, 0.15);
            border-color: #0d6efd;
            color: #ffffff;
        }
    </style>
</head>
<body>
    <div class="container-fluid d-flex align-items-center justify-content-center min-vh-100">
        <div class="row w-100 justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="card login-card">
                    <div class="card-body p-5">
                        <div class="text-center mb-4">
                            <h1 class="text-primary mb-2">TRAXOVO</h1>
                            <p class="text-muted">Multi-Division Fleet Management</p>
                            <small class="text-success">DFW • WTX • HOU</small>
                        </div>
                        
                        {% if error %}
                        <div class="alert alert-danger">{{ error }}</div>
                        {% endif %}
                        
                        <form method="POST" action="/auth/direct-login">
                            <div class="mb-3">
                                <label class="form-label text-white">Username</label>
                                <input type="text" name="username" class="form-control" value="admin" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-white">Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="remember" id="remember">
                                    <label class="form-check-label text-white" for="remember">
                                        Remember Me (30 days)
                                    </label>
                                </div>
                            </div>
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary btn-lg">Access Dashboard</button>
                            </div>
                        </form>
                        
                        <div class="text-center mt-4">
                            <small class="text-success">✅ GPS Assets: 657 Trackable</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

@auth_bp.route('/direct-login', methods=['GET', 'POST'])
@csrf_exempt
def direct_login():
    if request.method == 'GET':
        return render_template_string(DIRECT_LOGIN_PAGE)
    
    username = request.form.get('username')
    password = request.form.get('password')

    if username == "admin" and password == "TRAXOVO_Fleet_2025!@#":
        session['user'] = username
        session['authenticated'] = True
        return redirect('/')

    return render_template_string(DIRECT_LOGIN_PAGE, error="Invalid credentials")

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/auth/direct-login')