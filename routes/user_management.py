"""
TRAXOVO User Management System
Elite user authentication, session management, and admin controls
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
import json

user_mgmt_bp = Blueprint('user_mgmt', __name__)

class SupabaseUserManager:
    """
    Professional user management system connected to Supabase
    """
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable must be set")
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def init_user_tables(self):
        """Initialize user management tables in Supabase"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Users table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS traxovo_users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(50) UNIQUE NOT NULL,
                            email VARCHAR(100) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            role VARCHAR(20) DEFAULT 'user',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_login TIMESTAMP,
                            is_active BOOLEAN DEFAULT true,
                            preferences JSONB DEFAULT '{}',
                            dashboard_config JSONB DEFAULT '{}'
                        )
                    """)
                    
                    # User sessions table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS traxovo_user_sessions (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES traxovo_users(id),
                            session_token VARCHAR(255) UNIQUE NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP NOT NULL,
                            ip_address INET,
                            user_agent TEXT
                        )
                    """)
                    
                    # User activity log
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS traxovo_user_activity (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES traxovo_users(id),
                            action VARCHAR(100) NOT NULL,
                            details JSONB,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            ip_address INET
                        )
                    """)
                    
                    # Dashboard backups
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS traxovo_dashboard_backups (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES traxovo_users(id),
                            backup_name VARCHAR(100) NOT NULL,
                            dashboard_config JSONB NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            is_active BOOLEAN DEFAULT true
                        )
                    """)
                    
                    conn.commit()
                    
            # Create default admin user if none exists
            self.create_default_admin()
            return True
            
        except Exception as e:
            print(f"Error initializing user tables: {e}")
            return False
    
    def create_default_admin(self):
        """Create default admin user"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if admin exists
                    cur.execute("SELECT id FROM traxovo_users WHERE role = 'admin' LIMIT 1")
                    if cur.fetchone():
                        return
                    
                    # Create admin user
                    admin_password = "TRAXOVOAdmin2025!"
                    password_hash = generate_password_hash(admin_password)
                    
                    cur.execute("""
                        INSERT INTO traxovo_users (username, email, password_hash, role)
                        VALUES (%s, %s, %s, %s)
                    """, ('admin', 'admin@traxovo.com', password_hash, 'admin'))
                    
                    conn.commit()
                    print("Default admin user created: admin / TRAXOVOAdmin2025!")
                    
        except Exception as e:
            print(f"Error creating admin user: {e}")
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, username, email, password_hash, role, is_active, dashboard_config
                        FROM traxovo_users 
                        WHERE (username = %s OR email = %s) AND is_active = true
                    """, (username, username))
                    
                    user = cur.fetchone()
                    if user and check_password_hash(user['password_hash'], password):
                        # Update last login
                        cur.execute("""
                            UPDATE traxovo_users 
                            SET last_login = CURRENT_TIMESTAMP 
                            WHERE id = %s
                        """, (user['id'],))
                        
                        # Log activity
                        self.log_user_activity(user['id'], 'login', {'success': True})
                        
                        conn.commit()
                        return dict(user)
                    
                    return None
                    
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    def create_user_session(self, user_id, ip_address=None, user_agent=None):
        """Create secure user session"""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO traxovo_user_sessions 
                        (user_id, session_token, expires_at, ip_address, user_agent)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, session_token, expires_at, ip_address, user_agent))
                    
                    conn.commit()
                    
            return session_token
            
        except Exception as e:
            print(f"Session creation error: {e}")
            return None
    
    def validate_session(self, session_token):
        """Validate user session"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT u.id, u.username, u.email, u.role, u.dashboard_config
                        FROM traxovo_users u
                        JOIN traxovo_user_sessions s ON u.id = s.user_id
                        WHERE s.session_token = %s 
                        AND s.expires_at > CURRENT_TIMESTAMP
                        AND u.is_active = true
                    """, (session_token,))
                    
                    return cur.fetchone()
                    
        except Exception as e:
            print(f"Session validation error: {e}")
            return None
    
    def log_user_activity(self, user_id, action, details=None, ip_address=None):
        """Log user activity"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO traxovo_user_activity 
                        (user_id, action, details, ip_address)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, action, json.dumps(details or {}), ip_address))
                    
                    conn.commit()
                    
        except Exception as e:
            print(f"Activity logging error: {e}")
    
    def save_dashboard_backup(self, user_id, backup_name, dashboard_config):
        """Save dashboard configuration backup"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO traxovo_dashboard_backups 
                        (user_id, backup_name, dashboard_config)
                        VALUES (%s, %s, %s)
                    """, (user_id, backup_name, json.dumps(dashboard_config)))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"Dashboard backup error: {e}")
            return False
    
    def get_dashboard_backups(self, user_id):
        """Get user dashboard backups"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, backup_name, created_at, is_active
                        FROM traxovo_dashboard_backups 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC
                    """, (user_id,))
                    
                    return cur.fetchall()
                    
        except Exception as e:
            print(f"Error getting backups: {e}")
            return []
    
    def restore_dashboard_backup(self, user_id, backup_id):
        """Restore dashboard from backup"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get backup
                    cur.execute("""
                        SELECT dashboard_config 
                        FROM traxovo_dashboard_backups 
                        WHERE id = %s AND user_id = %s
                    """, (backup_id, user_id))
                    
                    backup = cur.fetchone()
                    if not backup:
                        return False
                    
                    # Update user dashboard config
                    cur.execute("""
                        UPDATE traxovo_users 
                        SET dashboard_config = %s 
                        WHERE id = %s
                    """, (backup['dashboard_config'], user_id))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False

# Initialize user manager
user_manager = SupabaseUserManager()

# Routes
@user_mgmt_bp.route('/login')
def login_page():
    """Professional login page"""
    return render_template('login.html')

@user_mgmt_bp.route('/login', methods=['POST'])
def login():
    """Process login"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Username and password required', 'error')
        return redirect(url_for('user_mgmt.login_page'))
    
    user = user_manager.authenticate_user(username, password)
    if user:
        # Create session
        session_token = user_manager.create_user_session(
            user['id'], 
            request.remote_addr, 
            request.headers.get('User-Agent')
        )
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['session_token'] = session_token
        
        flash('Login successful', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid credentials', 'error')
        return redirect(url_for('user_mgmt.login_page'))

@user_mgmt_bp.route('/logout')
def logout():
    """Logout user"""
    if 'user_id' in session:
        user_manager.log_user_activity(session['user_id'], 'logout')
    
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('user_mgmt.login_page'))

@user_mgmt_bp.route('/user-management')
def user_management():
    """User management dashboard"""
    if not session.get('role') == 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('user_management.html')

@user_mgmt_bp.route('/api/dashboard-backup', methods=['POST'])
def save_dashboard_backup():
    """Save dashboard backup"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    backup_name = request.json.get('backup_name')
    dashboard_config = request.json.get('dashboard_config')
    
    success = user_manager.save_dashboard_backup(
        session['user_id'], 
        backup_name, 
        dashboard_config
    )
    
    if success:
        user_manager.log_user_activity(
            session['user_id'], 
            'dashboard_backup_created', 
            {'backup_name': backup_name}
        )
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to save backup'}), 500

@user_mgmt_bp.route('/api/dashboard-backups')
def get_dashboard_backups():
    """Get user dashboard backups"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    backups = user_manager.get_dashboard_backups(session['user_id'])
    return jsonify(backups)

@user_mgmt_bp.route('/api/dashboard-restore/<int:backup_id>', methods=['POST'])
def restore_dashboard_backup(backup_id):
    """Restore dashboard backup"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    success = user_manager.restore_dashboard_backup(session['user_id'], backup_id)
    
    if success:
        user_manager.log_user_activity(
            session['user_id'], 
            'dashboard_backup_restored', 
            {'backup_id': backup_id}
        )
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to restore backup'}), 500

# Initialize on import
try:
    user_manager.init_user_tables()
except Exception as e:
    print(f"User management initialization error: {e}")