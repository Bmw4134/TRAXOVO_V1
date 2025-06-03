"""
QQ Unified Authentication Platform
Single consolidated login system with dummy-proof interface
All authentication methods unified into one cohesive system
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import session, request, redirect, url_for, render_template, flash
from functools import wraps

class QQUnifiedAuth:
    """Unified authentication platform for all TRAXOVO access"""
    
    def __init__(self):
        self.auth_db = 'qq_unified_auth.db'
        self.initialize_unified_database()
        self.session_timeout = 3600  # 1 hour
        
    def initialize_unified_database(self):
        """Initialize unified authentication database"""
        conn = sqlite3.connect(self.auth_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unified_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                user_type TEXT NOT NULL,
                access_level TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES unified_users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES unified_users (id)
            )
        ''')
        
        # Create default users if they don't exist
        self._create_default_users(cursor)
        
        conn.commit()
        conn.close()
    
    def _create_default_users(self, cursor):
        """Create default users for all access types"""
        default_users = [
            {
                'username': 'watson',
                'password': 'Btpp@1513',
                'user_type': 'quantum_admin',
                'access_level': 'full'
            },
            {
                'username': 'executive',
                'password': 'Executive2025',
                'user_type': 'executive',
                'access_level': 'executive'
            },
            {
                'username': 'demo',
                'password': 'demo123',
                'user_type': 'demo_user',
                'access_level': 'demo'
            },
            {
                'username': 'stress_test',
                'password': 'test123',
                'user_type': 'stress_test',
                'access_level': 'stress_test'
            },
            {
                'username': 'troy',
                'password': 'Troy2025',
                'user_type': 'executive',
                'access_level': 'executive'
            },
            {
                'username': 'william',
                'password': 'William2025',
                'user_type': 'executive',
                'access_level': 'executive'
            },
            {
                'username': 'chris',
                'password': 'Chris2025',
                'user_type': 'executive',
                'access_level': 'executive'
            }
        ]
        
        for user in default_users:
            password_hash = self._hash_password(user['password'])
            cursor.execute('''
                INSERT OR IGNORE INTO unified_users 
                (username, password_hash, user_type, access_level)
                VALUES (?, ?, ?, ?)
            ''', (user['username'], password_hash, user['user_type'], user['access_level']))
    
    def _hash_password(self, password: str) -> str:
        """Hash password for secure storage"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user against unified database"""
        conn = sqlite3.connect(self.auth_db)
        cursor = conn.cursor()
        
        password_hash = self._hash_password(password)
        
        cursor.execute('''
            SELECT id, username, user_type, access_level, is_active
            FROM unified_users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            user_data = {
                'id': user[0],
                'username': user[1],
                'user_type': user[2],
                'access_level': user[3],
                'is_active': user[4]
            }
            
            # Update last login
            cursor.execute('''
                UPDATE unified_users SET last_login = ? WHERE id = ?
            ''', (datetime.now(), user[0]))
            
            # Log access
            self._log_user_action(cursor, user[0], 'login', request.remote_addr if request else 'unknown')
            
            conn.commit()
            conn.close()
            
            return user_data
        
        conn.close()
        return None
    
    def create_session(self, user_data: Dict[str, Any]) -> str:
        """Create secure session for authenticated user"""
        session_token = hashlib.sha256(f"{user_data['id']}{datetime.now()}".encode()).hexdigest()
        expires_at = datetime.now() + timedelta(seconds=self.session_timeout)
        
        conn = sqlite3.connect(self.auth_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_data['id'], session_token, expires_at))
        
        conn.commit()
        conn.close()
        
        # Store in Flask session
        session['qq_user_id'] = user_data['id']
        session['qq_username'] = user_data['username']
        session['qq_user_type'] = user_data['user_type']
        session['qq_access_level'] = user_data['access_level']
        session['qq_session_token'] = session_token
        session['qq_authenticated'] = True
        session.permanent = True
        
        return session_token
    
    def validate_session(self) -> Optional[Dict[str, Any]]:
        """Validate current session"""
        if not session.get('qq_authenticated'):
            return None
        
        session_token = session.get('qq_session_token')
        user_id = session.get('qq_user_id')
        
        if not session_token or not user_id:
            return None
        
        conn = sqlite3.connect(self.auth_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, expires_at FROM user_sessions 
            WHERE session_token = ? AND user_id = ?
        ''', (session_token, user_id))
        
        session_data = cursor.fetchone()
        
        if session_data and datetime.fromisoformat(session_data[1]) > datetime.now():
            conn.close()
            return {
                'id': session.get('qq_user_id'),
                'username': session.get('qq_username'),
                'user_type': session.get('qq_user_type'),
                'access_level': session.get('qq_access_level')
            }
        
        # Session expired or invalid
        self.logout_user()
        conn.close()
        return None
    
    def logout_user(self):
        """Logout current user"""
        session_token = session.get('qq_session_token')
        
        if session_token:
            conn = sqlite3.connect(self.auth_db)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
            conn.commit()
            conn.close()
        
        # Clear Flask session
        for key in list(session.keys()):
            if key.startswith('qq_'):
                session.pop(key)
    
    def require_login(self, access_levels: List[str] = None):
        """Decorator requiring authentication with optional access level check"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user = self.validate_session()
                
                if not user:
                    return redirect(url_for('qq_unified_login'))
                
                if access_levels and user['access_level'] not in access_levels:
                    flash('Access denied: Insufficient privileges')
                    return redirect(url_for('qq_unified_login'))
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def _log_user_action(self, cursor, user_id: int, action: str, ip_address: str):
        """Log user action"""
        user_agent = request.headers.get('User-Agent', 'unknown') if request else 'unknown'
        cursor.execute('''
            INSERT INTO access_logs (user_id, action, ip_address, user_agent)
            VALUES (?, ?, ?, ?)
        ''', (user_id, action, ip_address, user_agent))
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        return self.validate_session()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.validate_session() is not None
    
    def get_access_level(self) -> Optional[str]:
        """Get current user access level"""
        user = self.validate_session()
        return user['access_level'] if user else None

# Global unified auth instance
qq_auth = QQUnifiedAuth()

def create_unified_login_template():
    """Create unified login template"""
    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRAXOVO QQ Unified Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: #00ff88;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .login-container {
            background: rgba(0, 0, 0, 0.9);
            padding: 40px;
            border: 2px solid #00ff88;
            border-radius: 15px;
            text-align: center;
            max-width: 450px;
            width: 100%;
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .login-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #00ff88, #00cc66, #00ff88);
            animation: glow 2s ease-in-out infinite;
        }
        
        @keyframes glow {
            0%, 100% { opacity: 0.7; }
            50% { opacity: 1; }
        }
        
        .logo {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 0 0 15px #00ff88;
        }
        
        .subtitle {
            color: #88ffaa;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .login-form {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .input-group {
            position: relative;
        }
        
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 15px;
            background: rgba(0, 255, 136, 0.1);
            border: 2px solid transparent;
            color: #00ff88;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #00ff88;
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
            background: rgba(0, 255, 136, 0.15);
        }
        
        .login-button {
            background: linear-gradient(45deg, #00ff88, #00cc66);
            color: #000;
            padding: 15px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            font-family: 'Courier New', monospace;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s ease;
        }
        
        .login-button:hover {
            background: linear-gradient(45deg, #00cc66, #00aa55);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 255, 136, 0.4);
        }
        
        .access-levels {
            margin-top: 30px;
            padding: 20px;
            background: rgba(0, 255, 136, 0.05);
            border-radius: 8px;
            border: 1px solid rgba(0, 255, 136, 0.2);
        }
        
        .access-level {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            font-size: 12px;
            color: #88ffaa;
        }
        
        .error-message {
            color: #ff6666;
            margin-top: 15px;
            padding: 10px;
            background: rgba(255, 102, 102, 0.1);
            border-radius: 5px;
            border: 1px solid rgba(255, 102, 102, 0.3);
        }
        
        .quantum-indicator {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 12px;
            height: 12px;
            background: #00ff88;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 0.6; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.2); }
            100% { opacity: 0.6; transform: scale(1); }
        }
        
        @media (max-width: 480px) {
            .login-container {
                padding: 30px 20px;
                margin: 10px;
            }
            
            .logo {
                font-size: 24px;
            }
            
            input[type="text"], input[type="password"], .login-button {
                font-size: 14px;
                padding: 12px;
            }
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="quantum-indicator"></div>
        
        <div class="logo">🚀 TRAXOVO</div>
        <div class="subtitle">QQ Unified Authentication Platform</div>
        
        <form method="POST" class="login-form">
            <div class="input-group">
                <input type="text" name="username" placeholder="Username" required autofocus>
            </div>
            
            <div class="input-group">
                <input type="password" name="password" placeholder="Password" required>
            </div>
            
            <button type="submit" class="login-button">Access TRAXOVO</button>
        </form>
        
        {% if error %}
        <div class="error-message">{{ error }}</div>
        {% endif %}
        
        <div class="access-levels">
            <div style="color: #00ff88; font-weight: bold; margin-bottom: 10px;">Access Levels</div>
            <div class="access-level">
                <span>Executive:</span>
                <span>troy / william / executive</span>
            </div>
            <div class="access-level">
                <span>Quantum Admin:</span>
                <span>watson</span>
            </div>
            <div class="access-level">
                <span>Demo Access:</span>
                <span>demo</span>
            </div>
            <div class="access-level">
                <span>Stress Test:</span>
                <span>stress_test</span>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    os.makedirs('templates', exist_ok=True)
    with open('templates/qq_unified_login.html', 'w') as f:
        f.write(template_content)

def create_unified_routes():
    """Create unified authentication routes"""
    routes_content = '''
# QQ Unified Authentication Routes
from qq_unified_authentication_platform import qq_auth, create_unified_login_template

# Create login template
create_unified_login_template()

@app.route('/login', methods=['GET', 'POST'])
@app.route('/qq-login', methods=['GET', 'POST'])
@app.route('/unified-login', methods=['GET', 'POST'])
def qq_unified_login():
    """Unified login for all user types"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('qq_unified_login.html', error='Username and password required')
        
        user_data = qq_auth.authenticate_user(username, password)
        
        if user_data:
            qq_auth.create_session(user_data)
            
            # Redirect based on user type
            if user_data['access_level'] in ['executive', 'quantum_admin']:
                return redirect(url_for('quantum_dashboard'))
            elif user_data['access_level'] == 'demo':
                return redirect(url_for('demo_direct'))
            else:
                return redirect(url_for('quantum_dashboard'))
        else:
            return render_template('qq_unified_login.html', error='Invalid credentials')
    
    # If already authenticated, redirect to dashboard
    if qq_auth.is_authenticated():
        return redirect(url_for('quantum_dashboard'))
    
    return render_template('qq_unified_login.html')

@app.route('/logout')
@app.route('/qq-logout')
def qq_unified_logout():
    """Unified logout"""
    qq_auth.logout_user()
    return redirect(url_for('qq_unified_login'))

# Update main index route
@app.route('/')
def index():
    """Main landing page with unified authentication"""
    if qq_auth.is_authenticated():
        user = qq_auth.get_user_info()
        if user and user['access_level'] in ['executive', 'quantum_admin']:
            return redirect(url_for('quantum_dashboard'))
        else:
            return redirect(url_for('quantum_dashboard'))
    
    return redirect(url_for('qq_unified_login'))

# Authentication decorator for protected routes
def require_auth(access_levels=None):
    """Simplified authentication decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = qq_auth.validate_session()
            if not user:
                return redirect(url_for('qq_unified_login'))
            
            if access_levels and user['access_level'] not in access_levels:
                flash('Access denied: Insufficient privileges')
                return redirect(url_for('qq_unified_login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
'''
    
    return routes_content

def main():
    """Initialize unified authentication platform"""
    create_unified_login_template()
    routes = create_unified_routes()
    
    print("QQ Unified Authentication Platform initialized")
    print("- Single login for all user types")
    print("- Cohesive authentication system")
    print("- Dummy-proof interface created")
    
    return {
        'status': 'initialized',
        'template': 'templates/qq_unified_login.html',
        'routes': 'ready_for_integration',
        'users_created': 6,
        'access_levels': ['executive', 'quantum_admin', 'demo', 'stress_test']
    }

if __name__ == "__main__":
    main()