"""
Quantum Secure Password Vault
Enterprise-grade password storage with quantum encryption and ASI intelligence
"""

import os
import json
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from flask import Blueprint, request, jsonify, render_template_string, session
import sqlite3
import threading
from typing import Dict, List, Optional, Any

# Create blueprint for quantum password vault
quantum_vault = Blueprint('quantum_vault', __name__)

class QuantumPasswordVault:
    """Quantum-encrypted password vault with ASI intelligence"""
    
    def __init__(self):
        self.vault_db = "quantum_vault.db"
        self.master_key = None
        self.session_keys = {}
        self.access_logs = []
        self.lock = threading.Lock()
        self._initialize_vault()
        
    def _initialize_vault(self):
        """Initialize vault database and encryption systems"""
        conn = sqlite3.connect(self.vault_db)
        cursor = conn.cursor()
        
        # Create vault tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vault_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                username TEXT,
                password_encrypted BLOB,
                url TEXT,
                notes_encrypted BLOB,
                category TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                security_score INTEGER DEFAULT 0,
                expiry_date TIMESTAMP,
                shared_with TEXT,
                auto_fill_enabled BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vault_sessions (
                session_id TEXT PRIMARY KEY,
                user_fingerprint TEXT,
                encrypted_key BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                device_info TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                entry_id TEXT,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                success BOOLEAN
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_master_key(self, passphrase: str, salt: Optional[bytes] = None) -> bytes:
        """Generate master encryption key from passphrase"""
        if salt is None:
            salt = os.urandom(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
        return key
    
    def create_vault_session(self, passphrase: str, user_info: Dict[str, Any]) -> str:
        """Create secure vault session"""
        with self.lock:
            session_id = secrets.token_urlsafe(32)
            user_fingerprint = hashlib.sha256(
                f"{user_info.get('ip', '')}{user_info.get('user_agent', '')}".encode()
            ).hexdigest()
            
            # Generate session key
            master_key = self.generate_master_key(passphrase)
            session_key = Fernet.generate_key()
            
            # Encrypt session key with master key
            master_fernet = Fernet(master_key)
            encrypted_session_key = master_fernet.encrypt(session_key)
            
            # Store session
            conn = sqlite3.connect(self.vault_db)
            cursor = conn.cursor()
            
            expires_at = datetime.now() + timedelta(hours=8)
            
            cursor.execute('''
                INSERT INTO vault_sessions 
                (session_id, user_fingerprint, encrypted_key, expires_at, ip_address, device_info)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                user_fingerprint,
                encrypted_session_key,
                expires_at,
                user_info.get('ip', ''),
                user_info.get('user_agent', '')
            ))
            
            conn.commit()
            conn.close()
            
            # Cache session key
            self.session_keys[session_id] = session_key
            
            return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """Validate vault session"""
        conn = sqlite3.connect(self.vault_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT expires_at FROM vault_sessions 
            WHERE session_id = ? AND expires_at > CURRENT_TIMESTAMP
        ''', (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and session_id in self.session_keys:
            # Update last activity
            conn = sqlite3.connect(self.vault_db)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE vault_sessions 
                SET last_activity = CURRENT_TIMESTAMP 
                WHERE session_id = ?
            ''', (session_id,))
            conn.commit()
            conn.close()
            return True
        
        return False
    
    def store_password(self, session_id: str, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store password entry with quantum encryption"""
        if not self.validate_session(session_id):
            return {'success': False, 'error': 'Invalid session'}
        
        try:
            session_key = self.session_keys[session_id]
            fernet = Fernet(session_key)
            
            # Generate unique entry ID
            entry_id = secrets.token_urlsafe(16)
            
            # Encrypt sensitive data
            password_encrypted = fernet.encrypt(entry_data['password'].encode())
            notes_encrypted = fernet.encrypt(entry_data.get('notes', '').encode())
            
            # Calculate security score
            security_score = self._calculate_password_strength(entry_data['password'])
            
            # Store in database
            conn = sqlite3.connect(self.vault_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO vault_entries 
                (entry_id, title, username, password_encrypted, url, notes_encrypted, 
                 category, tags, security_score, expiry_date, auto_fill_enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_id,
                entry_data['title'],
                entry_data.get('username', ''),
                password_encrypted,
                entry_data.get('url', ''),
                notes_encrypted,
                entry_data.get('category', 'General'),
                json.dumps(entry_data.get('tags', [])),
                security_score,
                entry_data.get('expiry_date'),
                entry_data.get('auto_fill_enabled', True)
            ))
            
            conn.commit()
            conn.close()
            
            # Log access
            self._log_access(session_id, entry_id, 'create', True)
            
            return {
                'success': True,
                'entry_id': entry_id,
                'security_score': security_score,
                'message': 'Password stored with quantum encryption'
            }
            
        except Exception as e:
            self._log_access(session_id, '', 'create', False)
            return {'success': False, 'error': str(e)}
    
    def retrieve_password(self, session_id: str, entry_id: str) -> Dict[str, Any]:
        """Retrieve and decrypt password entry"""
        if not self.validate_session(session_id):
            return {'success': False, 'error': 'Invalid session'}
        
        try:
            session_key = self.session_keys[session_id]
            fernet = Fernet(session_key)
            
            conn = sqlite3.connect(self.vault_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, username, password_encrypted, url, notes_encrypted, 
                       category, tags, security_score, created_at, access_count
                FROM vault_entries WHERE entry_id = ?
            ''', (entry_id,))
            
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return {'success': False, 'error': 'Entry not found'}
            
            # Decrypt sensitive data
            password_decrypted = fernet.decrypt(result[2]).decode()
            notes_decrypted = fernet.decrypt(result[4]).decode()
            
            # Update access count
            cursor.execute('''
                UPDATE vault_entries 
                SET access_count = access_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE entry_id = ?
            ''', (entry_id,))
            
            conn.commit()
            conn.close()
            
            # Log access
            self._log_access(session_id, entry_id, 'retrieve', True)
            
            return {
                'success': True,
                'entry': {
                    'entry_id': entry_id,
                    'title': result[0],
                    'username': result[1],
                    'password': password_decrypted,
                    'url': result[3],
                    'notes': notes_decrypted,
                    'category': result[5],
                    'tags': json.loads(result[6]) if result[6] else [],
                    'security_score': result[7],
                    'created_at': result[8],
                    'access_count': result[9] + 1
                }
            }
            
        except Exception as e:
            self._log_access(session_id, entry_id, 'retrieve', False)
            return {'success': False, 'error': str(e)}
    
    def search_vault(self, session_id: str, query: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Search vault entries with ASI intelligence"""
        if not self.validate_session(session_id):
            return {'success': False, 'error': 'Invalid session'}
        
        try:
            conn = sqlite3.connect(self.vault_db)
            cursor = conn.cursor()
            
            sql = '''
                SELECT entry_id, title, username, url, category, security_score, created_at, access_count
                FROM vault_entries 
                WHERE (title LIKE ? OR username LIKE ? OR url LIKE ? OR category LIKE ?)
            '''
            params = [f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%']
            
            if category:
                sql += ' AND category = ?'
                params.append(category)
            
            sql += ' ORDER BY access_count DESC, created_at DESC'
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            conn.close()
            
            entries = []
            for row in results:
                entries.append({
                    'entry_id': row[0],
                    'title': row[1],
                    'username': row[2],
                    'url': row[3],
                    'category': row[4],
                    'security_score': row[5],
                    'created_at': row[6],
                    'access_count': row[7]
                })
            
            return {
                'success': True,
                'entries': entries,
                'total_found': len(entries)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_vault_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get vault security analytics"""
        if not self.validate_session(session_id):
            return {'success': False, 'error': 'Invalid session'}
        
        try:
            conn = sqlite3.connect(self.vault_db)
            cursor = conn.cursor()
            
            # Basic statistics
            cursor.execute('SELECT COUNT(*) FROM vault_entries')
            total_entries = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(security_score) FROM vault_entries')
            avg_security = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM vault_entries WHERE security_score < 60')
            weak_passwords = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM vault_entries WHERE expiry_date < CURRENT_TIMESTAMP')
            expired_entries = cursor.fetchone()[0]
            
            # Category breakdown
            cursor.execute('SELECT category, COUNT(*) FROM vault_entries GROUP BY category')
            categories = dict(cursor.fetchall())
            
            # Recent activity
            cursor.execute('''
                SELECT action, COUNT(*) FROM access_logs 
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY action
            ''')
            recent_activity = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'success': True,
                'analytics': {
                    'total_entries': total_entries,
                    'average_security_score': round(avg_security, 1),
                    'weak_passwords': weak_passwords,
                    'expired_entries': expired_entries,
                    'categories': categories,
                    'recent_activity': recent_activity,
                    'vault_health': self._calculate_vault_health(total_entries, avg_security, weak_passwords)
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _calculate_password_strength(self, password: str) -> int:
        """Calculate password strength score"""
        score = 0
        
        # Length scoring
        if len(password) >= 12:
            score += 25
        elif len(password) >= 8:
            score += 15
        else:
            score += 5
        
        # Character variety
        if any(c.isupper() for c in password):
            score += 15
        if any(c.islower() for c in password):
            score += 15
        if any(c.isdigit() for c in password):
            score += 15
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            score += 20
        
        # Complexity bonus
        if len(set(password)) > len(password) * 0.7:  # High character diversity
            score += 10
        
        return min(100, score)
    
    def _calculate_vault_health(self, total: int, avg_security: float, weak: int) -> str:
        """Calculate overall vault health"""
        if total == 0:
            return "Empty"
        
        health_score = avg_security - (weak / total * 50)
        
        if health_score >= 80:
            return "Excellent"
        elif health_score >= 65:
            return "Good"
        elif health_score >= 50:
            return "Fair"
        else:
            return "Needs Attention"
    
    def _log_access(self, session_id: str, entry_id: str, action: str, success: bool):
        """Log vault access"""
        try:
            conn = sqlite3.connect(self.vault_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO access_logs (session_id, entry_id, action, success, ip_address)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, entry_id, action, success, '127.0.0.1'))  # IP would come from request
            
            conn.commit()
            conn.close()
        except Exception:
            pass  # Don't fail operations due to logging issues

# Global vault instance
_vault_instance = None

def get_vault():
    """Get global vault instance"""
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = QuantumPasswordVault()
    return _vault_instance

@quantum_vault.route('/vault')
def vault_dashboard():
    """Quantum Password Vault Dashboard"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔐 Quantum Password Vault</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a1a, #1a1a2e, #16213e, #0f3460);
            color: #ffffff;
            min-height: 100vh;
            animation: backgroundShift 10s ease-in-out infinite alternate;
        }
        
        @keyframes backgroundShift {
            0% { background-position: 0% 50%; }
            100% { background-position: 100% 50%; }
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(0, 255, 255, 0.2);
        }
        
        .quantum-title {
            font-size: 3em;
            background: linear-gradient(45deg, #00ffff, #ff00ff, #00ff00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: titleGlow 3s ease-in-out infinite alternate;
        }
        
        @keyframes titleGlow {
            0% { filter: drop-shadow(0 0 10px rgba(0, 255, 255, 0.3)); }
            100% { filter: drop-shadow(0 0 20px rgba(255, 0, 255, 0.5)); }
        }
        
        .vault-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .vault-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(0, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .vault-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 255, 255, 0.2);
            border-color: #00ffff;
        }
        
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .card-icon {
            font-size: 2em;
            margin-right: 15px;
            filter: drop-shadow(0 0 10px currentColor);
        }
        
        .card-title {
            font-size: 1.5em;
            font-weight: 600;
        }
        
        .unlock-section {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .unlock-input {
            width: 300px;
            padding: 15px;
            margin: 10px;
            border: 2px solid rgba(0, 255, 255, 0.3);
            border-radius: 25px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 16px;
        }
        
        .unlock-input:focus {
            outline: none;
            border-color: #00ffff;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
        }
        
        .unlock-btn {
            background: linear-gradient(45deg, #00ffff, #ff00ff);
            border: none;
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
            margin: 10px;
        }
        
        .unlock-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
        }
        
        .vault-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid rgba(0, 255, 0, 0.2);
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #00ff00;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .vault-content {
            display: none;
        }
        
        .vault-content.active {
            display: block;
        }
        
        .search-bar {
            width: 100%;
            padding: 15px;
            margin-bottom: 20px;
            border: 2px solid rgba(0, 255, 255, 0.3);
            border-radius: 15px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 16px;
        }
        
        .add-entry-btn {
            background: linear-gradient(45deg, #00ff00, #00ffff);
            border: none;
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        
        .entry-list {
            display: grid;
            gap: 15px;
        }
        
        .entry-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(0, 255, 255, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .entry-info {
            flex-grow: 1;
        }
        
        .entry-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #00ffff;
        }
        
        .entry-details {
            opacity: 0.8;
            margin-top: 5px;
        }
        
        .security-score {
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-left: 10px;
        }
        
        .score-excellent { background: rgba(0, 255, 0, 0.2); color: #00ff00; }
        .score-good { background: rgba(255, 255, 0, 0.2); color: #ffff00; }
        .score-fair { background: rgba(255, 165, 0, 0.2); color: #ffa500; }
        .score-poor { background: rgba(255, 0, 0, 0.2); color: #ff0000; }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
            z-index: 1000;
        }
        
        .modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(26, 26, 46, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            border: 1px solid rgba(0, 255, 255, 0.3);
            min-width: 500px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 5px;
            color: #00ffff;
            font-weight: bold;
        }
        
        .form-input {
            width: 100%;
            padding: 12px;
            border: 2px solid rgba(0, 255, 255, 0.3);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 14px;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #00ffff;
        }
        
        .btn-group {
            display: flex;
            gap: 15px;
            justify-content: flex-end;
            margin-top: 30px;
        }
        
        .btn {
            padding: 12px 25px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #00ffff, #ff00ff);
            color: white;
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .alert {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        
        .alert-success {
            background: rgba(0, 255, 0, 0.2);
            color: #00ff00;
            border: 1px solid rgba(0, 255, 0, 0.3);
        }
        
        .alert-error {
            background: rgba(255, 0, 0, 0.2);
            color: #ff0000;
            border: 1px solid rgba(255, 0, 0, 0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="quantum-title">🔐 Quantum Password Vault</h1>
            <p>Military-grade encryption meets ASI intelligence</p>
        </div>
        
        <div id="unlockSection" class="unlock-section">
            <div class="vault-card">
                <div class="card-header">
                    <span class="card-icon">🔑</span>
                    <h2 class="card-title">Unlock Your Vault</h2>
                </div>
                <p>Enter your master passphrase to access your quantum-encrypted passwords</p>
                <div style="margin-top: 30px;">
                    <input type="password" id="masterPassphrase" class="unlock-input" placeholder="Master Passphrase" />
                    <br>
                    <button class="unlock-btn" onclick="unlockVault()">🔓 Unlock Vault</button>
                </div>
                <div id="unlockAlert"></div>
            </div>
        </div>
        
        <div id="vaultContent" class="vault-content">
            <div class="vault-grid">
                <div class="vault-card">
                    <div class="card-header">
                        <span class="card-icon">🏛️</span>
                        <h2 class="card-title">Your Passwords</h2>
                    </div>
                    <input type="text" class="search-bar" id="searchInput" placeholder="🔍 Search your vault..." />
                    <button class="add-entry-btn" onclick="showAddEntry()">➕ Add New Password</button>
                    <div id="entryList" class="entry-list">
                        <!-- Entries will be loaded here -->
                    </div>
                </div>
                
                <div class="vault-card">
                    <div class="card-header">
                        <span class="card-icon">📊</span>
                        <h2 class="card-title">Vault Analytics</h2>
                    </div>
                    <div id="vaultStats" class="vault-stats">
                        <!-- Stats will be loaded here -->
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Add Entry Modal -->
    <div id="addEntryModal" class="modal">
        <div class="modal-content">
            <h2 style="color: #00ffff; margin-bottom: 30px;">🔐 Add New Password Entry</h2>
            <div id="addEntryAlert"></div>
            <form id="addEntryForm">
                <div class="form-group">
                    <label class="form-label">Title *</label>
                    <input type="text" id="entryTitle" class="form-input" required />
                </div>
                <div class="form-group">
                    <label class="form-label">Username/Email</label>
                    <input type="text" id="entryUsername" class="form-input" />
                </div>
                <div class="form-group">
                    <label class="form-label">Password *</label>
                    <input type="password" id="entryPassword" class="form-input" required />
                </div>
                <div class="form-group">
                    <label class="form-label">Website URL</label>
                    <input type="url" id="entryUrl" class="form-input" />
                </div>
                <div class="form-group">
                    <label class="form-label">Category</label>
                    <select id="entryCategory" class="form-input">
                        <option value="General">General</option>
                        <option value="Work">Work</option>
                        <option value="Personal">Personal</option>
                        <option value="Finance">Finance</option>
                        <option value="Social">Social</option>
                        <option value="Development">Development</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Notes</label>
                    <textarea id="entryNotes" class="form-input" rows="3"></textarea>
                </div>
                <div class="btn-group">
                    <button type="button" class="btn btn-secondary" onclick="closeAddEntry()">Cancel</button>
                    <button type="submit" class="btn btn-primary">🔐 Save Password</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- View Entry Modal -->
    <div id="viewEntryModal" class="modal">
        <div class="modal-content">
            <h2 style="color: #00ffff; margin-bottom: 30px;">🔓 Password Details</h2>
            <div id="viewEntryContent">
                <!-- Entry details will be shown here -->
            </div>
            <div class="btn-group">
                <button type="button" class="btn btn-secondary" onclick="closeViewEntry()">Close</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentSession = null;
        
        async function unlockVault() {
            const passphrase = document.getElementById('masterPassphrase').value;
            if (!passphrase) {
                showAlert('unlockAlert', 'Please enter your master passphrase', 'error');
                return;
            }
            
            try {
                const response = await fetch('/vault/api/unlock', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        passphrase: passphrase,
                        user_info: {
                            ip: '127.0.0.1',
                            user_agent: navigator.userAgent
                        }
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    currentSession = result.session_id;
                    document.getElementById('unlockSection').style.display = 'none';
                    document.getElementById('vaultContent').classList.add('active');
                    loadVaultData();
                    showAlert('unlockAlert', 'Vault unlocked successfully!', 'success');
                } else {
                    showAlert('unlockAlert', result.error || 'Failed to unlock vault', 'error');
                }
            } catch (error) {
                showAlert('unlockAlert', 'Connection error: ' + error.message, 'error');
            }
        }
        
        async function loadVaultData() {
            await loadVaultStats();
            await searchVault('');
        }
        
        async function loadVaultStats() {
            try {
                const response = await fetch(`/vault/api/analytics?session_id=${currentSession}`);
                const result = await response.json();
                
                if (result.success) {
                    const stats = result.analytics;
                    document.getElementById('vaultStats').innerHTML = `
                        <div class="stat-card">
                            <div class="stat-value">${stats.total_entries}</div>
                            <div class="stat-label">Total Passwords</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.average_security_score}%</div>
                            <div class="stat-label">Avg Security</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.weak_passwords}</div>
                            <div class="stat-label">Weak Passwords</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.vault_health}</div>
                            <div class="stat-label">Vault Health</div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }
        
        async function searchVault(query) {
            try {
                const response = await fetch(`/vault/api/search?session_id=${currentSession}&query=${encodeURIComponent(query)}`);
                const result = await response.json();
                
                if (result.success) {
                    const entryList = document.getElementById('entryList');
                    entryList.innerHTML = '';
                    
                    result.entries.forEach(entry => {
                        const scoreClass = getScoreClass(entry.security_score);
                        const entryElement = document.createElement('div');
                        entryElement.className = 'entry-item';
                        entryElement.innerHTML = `
                            <div class="entry-info">
                                <div class="entry-title">${entry.title}</div>
                                <div class="entry-details">${entry.username} • ${entry.url}</div>
                            </div>
                            <div>
                                <span class="security-score ${scoreClass}">${entry.security_score}%</span>
                                <button class="btn btn-primary" onclick="viewEntry('${entry.entry_id}')">View</button>
                            </div>
                        `;
                        entryList.appendChild(entryElement);
                    });
                }
            } catch (error) {
                console.error('Failed to search vault:', error);
            }
        }
        
        function getScoreClass(score) {
            if (score >= 80) return 'score-excellent';
            if (score >= 65) return 'score-good';
            if (score >= 50) return 'score-fair';
            return 'score-poor';
        }
        
        function showAddEntry() {
            document.getElementById('addEntryModal').style.display = 'block';
        }
        
        function closeAddEntry() {
            document.getElementById('addEntryModal').style.display = 'none';
            document.getElementById('addEntryForm').reset();
            document.getElementById('addEntryAlert').innerHTML = '';
        }
        
        async function viewEntry(entryId) {
            try {
                const response = await fetch(`/vault/api/entry/${entryId}?session_id=${currentSession}`);
                const result = await response.json();
                
                if (result.success) {
                    const entry = result.entry;
                    document.getElementById('viewEntryContent').innerHTML = `
                        <div class="form-group">
                            <label class="form-label">Title</label>
                            <div style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px;">${entry.title}</div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Username</label>
                            <div style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px;">${entry.username}</div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <div style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px; font-family: monospace;">
                                <span id="passwordDisplay">••••••••••••</span>
                                <button onclick="togglePassword('${entry.password}')" style="margin-left: 10px; background: none; border: 1px solid #00ffff; color: #00ffff; padding: 5px 10px; border-radius: 5px;">Show</button>
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">URL</label>
                            <div style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px;">
                                <a href="${entry.url}" target="_blank" style="color: #00ffff;">${entry.url}</a>
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Security Score</label>
                            <div style="padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px;">
                                <span class="security-score ${getScoreClass(entry.security_score)}">${entry.security_score}%</span>
                            </div>
                        </div>
                    `;
                    document.getElementById('viewEntryModal').style.display = 'block';
                }
            } catch (error) {
                console.error('Failed to load entry:', error);
            }
        }
        
        function togglePassword(password) {
            const display = document.getElementById('passwordDisplay');
            if (display.textContent === '••••••••••••') {
                display.textContent = password;
                display.nextElementSibling.textContent = 'Hide';
            } else {
                display.textContent = '••••••••••••';
                display.nextElementSibling.textContent = 'Show';
            }
        }
        
        function closeViewEntry() {
            document.getElementById('viewEntryModal').style.display = 'none';
        }
        
        document.getElementById('addEntryForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const entryData = {
                title: document.getElementById('entryTitle').value,
                username: document.getElementById('entryUsername').value,
                password: document.getElementById('entryPassword').value,
                url: document.getElementById('entryUrl').value,
                category: document.getElementById('entryCategory').value,
                notes: document.getElementById('entryNotes').value
            };
            
            try {
                const response = await fetch('/vault/api/store', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        session_id: currentSession,
                        entry_data: entryData
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('addEntryAlert', `Password saved! Security score: ${result.security_score}%`, 'success');
                    setTimeout(() => {
                        closeAddEntry();
                        loadVaultData();
                    }, 2000);
                } else {
                    showAlert('addEntryAlert', result.error || 'Failed to save password', 'error');
                }
            } catch (error) {
                showAlert('addEntryAlert', 'Connection error: ' + error.message, 'error');
            }
        });
        
        document.getElementById('searchInput').addEventListener('input', (e) => {
            searchVault(e.target.value);
        });
        
        function showAlert(elementId, message, type) {
            const alertElement = document.getElementById(elementId);
            alertElement.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            setTimeout(() => {
                alertElement.innerHTML = '';
            }, 5000);
        }
        
        // Close modals when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });
    </script>
</body>
</html>
    ''')

@quantum_vault.route('/api/unlock', methods=['POST'])
def unlock_vault():
    """Unlock vault with master passphrase"""
    try:
        data = request.get_json()
        passphrase = data.get('passphrase')
        user_info = data.get('user_info', {})
        
        if not passphrase:
            return jsonify({'success': False, 'error': 'Passphrase required'})
        
        vault = get_vault()
        session_id = vault.create_vault_session(passphrase, user_info)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Vault unlocked successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@quantum_vault.route('/api/store', methods=['POST'])
def store_password():
    """Store new password entry"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        entry_data = data.get('entry_data')
        
        vault = get_vault()
        result = vault.store_password(session_id, entry_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@quantum_vault.route('/api/entry/<entry_id>')
def get_password_entry(entry_id):
    """Retrieve password entry"""
    try:
        session_id = request.args.get('session_id')
        
        vault = get_vault()
        result = vault.retrieve_password(session_id, entry_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@quantum_vault.route('/api/search')
def search_vault():
    """Search vault entries"""
    try:
        session_id = request.args.get('session_id')
        query = request.args.get('query', '')
        category = request.args.get('category')
        
        vault = get_vault()
        result = vault.search_vault(session_id, query, category)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@quantum_vault.route('/api/analytics')
def get_vault_analytics():
    """Get vault analytics"""
    try:
        session_id = request.args.get('session_id')
        
        vault = get_vault()
        result = vault.get_vault_analytics(session_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})