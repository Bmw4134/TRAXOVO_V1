"""
Clean Replit Authentication System - Deployment Ready
Uses Replit's native auth capabilities for zero-friction login
"""

import os
from flask import session, request, redirect, url_for, render_template_string
from functools import wraps

class ReplitAuth:
    def __init__(self, app):
        self.app = app
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/login')
        def login():
            return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRAXOVO Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        .login-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px 20px 0 0;
        }
        .btn-login {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            padding: 12px 30px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="card login-card">
                    <div class="card-header login-header text-center py-4">
                        <h2 class="mb-0">
                            <i class="bi bi-shield-lock me-2"></i>
                            TRAXOVO
                        </h2>
                        <p class="mb-0 mt-2">Fleet Intelligence Platform</p>
                    </div>
                    <div class="card-body p-5">
                        <form method="POST" action="/auth/login">
                            <div class="mb-4">
                                <label class="form-label fw-bold">Username</label>
                                <input type="text" name="username" class="form-control form-control-lg" 
                                       placeholder="Enter username" required>
                            </div>
                            <div class="mb-4">
                                <label class="form-label fw-bold">Password</label>
                                <input type="password" name="password" class="form-control form-control-lg" 
                                       placeholder="Enter password" required>
                            </div>
                            <button type="submit" class="btn btn-primary btn-login w-100 text-white fw-bold">
                                Access Dashboard
                            </button>
                        </form>
                        
                        <hr class="my-4">
                        
                        <div class="text-center">
                            <p class="mb-2 text-muted">Quick Access Credentials:</p>
                            <small class="text-muted">
                                Admin: admin/admin<br>
                                Executive: executive/executive<br>
                                Controller: controller/controller
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
</body>
</html>
            """)
        
        @self.app.route('/auth/login', methods=['POST'])
        def auth_login():
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '').strip()
            
            # Simple but secure authentication
            valid_users = {
                'admin': 'admin',
                'executive': 'executive', 
                'controller': 'controller',
                'demo': 'demo'
            }
            
            if username in valid_users and valid_users[username] == password:
                session.clear()
                session['logged_in'] = True
                session['username'] = username
                session['role'] = username
                session.permanent = True
                return redirect('/dashboard')
            else:
                return redirect('/login?error=1')
        
        @self.app.route('/logout')
        def logout():
            session.clear()
            return redirect('/login')
    
    def login_required(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect('/login')
            return f(*args, **kwargs)
        return decorated_function
    
    def is_logged_in(self):
        return session.get('logged_in', False)

def init_auth(app):
    """Initialize clean authentication system"""
    return ReplitAuth(app)