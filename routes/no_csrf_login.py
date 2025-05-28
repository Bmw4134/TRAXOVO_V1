"""
Direct Login without any CSRF protection
"""
from flask import Blueprint, request, redirect, render_template_string
from flask_login import login_user, current_user
import logging

logger = logging.getLogger(__name__)

no_csrf_login_bp = Blueprint('no_csrf_login', __name__)

LOGIN_HTML = '''<!DOCTYPE html>
<html data-bs-theme="dark">
<head>
    <title>TRAXOVO Login</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; }
        .login-card { background: rgba(33, 37, 41, 0.95); border: 1px solid rgba(255, 255, 255, 0.1); }
        .form-control { background-color: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); color: #fff; }
    </style>
</head>
<body>
    <div class="container-fluid d-flex align-items-center justify-content-center min-vh-100">
        <div class="col-md-4">
            <div class="card login-card">
                <div class="card-body p-5">
                    <h1 class="text-primary text-center mb-4">TRAXOVO</h1>
                    <p class="text-center text-muted mb-4">Multi-Division Fleet: DFW • WTX • HOU</p>
                    
                    {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
                    
                    <form method="POST">
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
                                <input class="form-check-input" type="checkbox" name="remember">
                                <label class="form-check-label text-white">Remember Me (30 days)</label>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Access Dashboard</button>
                    </form>
                    
                    <div class="text-center mt-4">
                        <small class="text-success">✅ GPS Assets: 657 Trackable</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

@no_csrf_login_bp.route('/direct-login', methods=['GET', 'POST'])
def direct_login():
    """Direct login without CSRF"""
    if current_user.is_authenticated:
        return redirect('/')
    
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        try:
            from models.user import User
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if user and user.check_password(password):
                login_user(user, remember=remember)
                logger.info(f"Direct login successful for: {user.username}")
                return redirect('/')
            else:
                error = "Invalid credentials"
                
        except Exception as e:
            error = "Login failed"
            logger.error(f"Direct login error: {e}")
    
    return render_template_string(LOGIN_HTML, error=error)