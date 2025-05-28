"""
Simple Direct Login - No CSRF Required
"""
from flask import Blueprint, request, redirect, url_for, flash, render_template_string
from flask_login import login_user, current_user
import logging

logger = logging.getLogger(__name__)

simple_login_bp = Blueprint('simple_login', __name__)

SIMPLE_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRAXOVO Login</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh; color: #ffffff; 
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
                        </div>
                        
                        {% if error %}
                        <div class="alert alert-danger">{{ error }}</div>
                        {% endif %}
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">Username</label>
                                <input type="text" name="username" class="form-control" value="admin" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="remember" id="remember">
                                    <label class="form-check-label" for="remember">Remember Me (30 days)</label>
                                </div>
                            </div>
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary btn-lg">Login to TRAXOVO</button>
                            </div>
                        </form>
                        
                        <div class="text-center mt-4">
                            <small class="text-success">GPS Assets Online: 716 Active</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

@simple_login_bp.route('/simple-login', methods=['GET', 'POST'])
def simple_login():
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
                logger.info(f"Successful login for user: {user.username}")
                return redirect('/')
            else:
                error = "Invalid username or password"
                logger.warning(f"Failed login attempt for: {username}")
                
        except Exception as e:
            error = "Login error occurred"
            logger.error(f"Login error: {str(e)}")
    
    return render_template_string(SIMPLE_LOGIN_TEMPLATE, error=error)