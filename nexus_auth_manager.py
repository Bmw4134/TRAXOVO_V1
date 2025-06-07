"""
NEXUS Authentication & Access Control Manager
Multi-level access with stress testing user management
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import session
import sqlite3

class NexusAuthManager:
    """Enterprise authentication with role-based access control"""
    
    def __init__(self):
        self.db_path = "nexus_auth.db"
        self.admin_user_id = "nexus_admin_primary"
        self.stress_test_users = []
        self.setup_auth_database()
        
    def setup_auth_database(self):
        """Initialize authentication database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                access_level TEXT NOT NULL,
                created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                login_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                access_level TEXT NOT NULL,
                created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                success BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create admin user if not exists
        cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = ?', (self.admin_user_id,))
        if cursor.fetchone()[0] == 0:
            admin_password_hash = self._hash_password("nexus_admin_2025")
            cursor.execute('''
                INSERT INTO users (user_id, username, password_hash, role, access_level)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.admin_user_id, "NEXUS Admin", admin_password_hash, "admin", "full_nexus_access"))
        
        conn.commit()
        conn.close()
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = "nexus_enterprise_salt_2025"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def create_stress_test_users(self, count: int = 10) -> List[Dict[str, str]]:
        """Create multiple stress test users with limited access"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stress_users = []
        
        for i in range(1, count + 1):
            user_id = f"stress_test_user_{i:03d}"
            username = f"Stress Test User {i}"
            password = f"stress{i:03d}"
            password_hash = self._hash_password(password)
            
            # Check if user already exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = ?', (user_id,))
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO users (user_id, username, password_hash, role, access_level)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, password_hash, "stress_tester", "preview_only"))
                
                stress_users.append({
                    'user_id': user_id,
                    'username': username,
                    'password': password,
                    'access_level': 'preview_only'
                })
        
        conn.commit()
        conn.close()
        
        self.stress_test_users = stress_users
        return stress_users
    
    def authenticate_user(self, username: str, password: str, ip_address: str = "", user_agent: str = "") -> Dict[str, Any]:
        """Authenticate user and create session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self._hash_password(password)
        
        cursor.execute('''
            SELECT user_id, username, role, access_level, status 
            FROM users 
            WHERE (username = ? OR user_id = ?) AND password_hash = ?
        ''', (username, username, password_hash))
        
        user = cursor.fetchone()
        
        if user and user[4] == 'active':  # status check
            user_id, username, role, access_level, status = user
            
            # Create session
            import uuid
            session_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO sessions (session_id, user_id, role, access_level, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, role, access_level, ip_address, user_agent))
            
            # Update login count and last login
            cursor.execute('''
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
                WHERE user_id = ?
            ''', (user_id,))
            
            # Log access
            cursor.execute('''
                INSERT INTO access_logs (user_id, action, resource, ip_address)
                VALUES (?, ?, ?, ?)
            ''', (user_id, "login", "authentication", ip_address))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'session_id': session_id,
                'user_id': user_id,
                'username': username,
                'role': role,
                'access_level': access_level
            }
        else:
            # Log failed attempt
            cursor.execute('''
                INSERT INTO access_logs (user_id, action, resource, ip_address, success)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, "login_failed", "authentication", ip_address, False))
            
            conn.commit()
            conn.close()
            
            return {
                'success': False,
                'error': 'Invalid credentials or account disabled'
            }
    
    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate active session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, role, access_level, created_timestamp
            FROM sessions 
            WHERE session_id = ? AND status = 'active'
        ''', (session_id,))
        
        session_data = cursor.fetchone()
        
        if session_data:
            user_id, role, access_level, created = session_data
            
            # Update last activity
            cursor.execute('''
                UPDATE sessions 
                SET last_activity = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (session_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'valid': True,
                'user_id': user_id,
                'role': role,
                'access_level': access_level
            }
        else:
            conn.close()
            return {'valid': False}
    
    def check_nexus_access(self, session_id: str) -> bool:
        """Check if user has NEXUS Intelligence access"""
        session_data = self.validate_session(session_id)
        
        if session_data.get('valid'):
            access_level = session_data.get('access_level')
            return access_level == 'full_nexus_access'
        
        return False
    
    def check_preview_access(self, session_id: str) -> bool:
        """Check if user has preview access"""
        session_data = self.validate_session(session_id)
        
        if session_data.get('valid'):
            access_level = session_data.get('access_level')
            return access_level in ['preview_only', 'full_nexus_access']
        
        return False
    
    def logout_user(self, session_id: str) -> bool:
        """Logout user and invalidate session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions 
            SET status = 'logged_out'
            WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def get_stress_test_credentials(self) -> List[Dict[str, str]]:
        """Get all stress test user credentials"""
        if not self.stress_test_users:
            self.stress_test_users = self.create_stress_test_users(15)
        
        return self.stress_test_users
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get authentication system statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "active"')
        total_users = cursor.fetchone()[0]
        
        # Active sessions
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE status = "active"')
        active_sessions = cursor.fetchone()[0]
        
        # Role distribution
        cursor.execute('SELECT role, COUNT(*) FROM users WHERE status = "active" GROUP BY role')
        role_stats = dict(cursor.fetchall())
        
        # Recent logins (last 24 hours)
        cursor.execute('''
            SELECT COUNT(*) FROM access_logs 
            WHERE action = "login" AND timestamp > datetime('now', '-24 hours')
        ''')
        recent_logins = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_sessions': active_sessions,
            'role_distribution': role_stats,
            'recent_logins_24h': recent_logins,
            'admin_access_users': role_stats.get('admin', 0),
            'stress_test_users': role_stats.get('stress_tester', 0)
        }

# Global auth manager
nexus_auth = NexusAuthManager()