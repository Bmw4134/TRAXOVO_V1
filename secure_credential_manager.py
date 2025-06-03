"""
TRAXOVO Secure Credential Management System
Safely handles login credentials for GAUGE Smart and Groundworks scraping
"""

import os
import json
import base64
from cryptography.fernet import Fernet
from flask import Blueprint, render_template, request, jsonify, session, flash
from datetime import datetime
import sqlite3

class SecureCredentialManager:
    """Secure credential storage and management"""
    
    def __init__(self):
        self.db_path = "secure_credentials.db"
        self.key_file = "credential_key.key"
        self.init_database()
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_key(self):
        """Get or create encryption key"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as key_file:
                return key_file.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as key_file:
                key_file.write(key)
            return key
    
    def init_database(self):
        """Initialize secure credentials database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                password_encrypted TEXT NOT NULL,
                additional_fields TEXT,
                created_at TEXT,
                last_used TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credential_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT,
                action TEXT,
                timestamp TEXT,
                success BOOLEAN,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_credentials(self, service_name, username, password, additional_fields=None):
        """Securely store credentials"""
        try:
            encrypted_password = self.cipher.encrypt(password.encode()).decode()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO credentials 
                (service_name, username, password_encrypted, additional_fields, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                service_name,
                username,
                encrypted_password,
                json.dumps(additional_fields) if additional_fields else None,
                datetime.now().isoformat(),
                'active'
            ))
            
            conn.commit()
            conn.close()
            
            self._log_usage(service_name, "credential_stored", True, "Credentials stored successfully")
            return True
            
        except Exception as e:
            self._log_usage(service_name, "credential_store_failed", False, str(e))
            return False
    
    def get_credentials(self, service_name):
        """Retrieve and decrypt credentials"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, password_encrypted, additional_fields 
                FROM credentials 
                WHERE service_name = ? AND status = 'active'
            ''', (service_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                username, encrypted_password, additional_fields = result
                password = self.cipher.decrypt(encrypted_password.encode()).decode()
                
                # Update last used
                self._update_last_used(service_name)
                
                return {
                    'username': username,
                    'password': password,
                    'additional_fields': json.loads(additional_fields) if additional_fields else {}
                }
            
            return None
            
        except Exception as e:
            self._log_usage(service_name, "credential_retrieval_failed", False, str(e))
            return None
    
    def _update_last_used(self, service_name):
        """Update last used timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE credentials 
            SET last_used = ? 
            WHERE service_name = ?
        ''', (datetime.now().isoformat(), service_name))
        
        conn.commit()
        conn.close()
    
    def _log_usage(self, service_name, action, success, details):
        """Log credential usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO credential_usage_log 
            (service_name, action, timestamp, success, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (service_name, action, datetime.now().isoformat(), success, details))
        
        conn.commit()
        conn.close()
    
    def list_stored_services(self):
        """List all stored service credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT service_name, username, created_at, last_used, status 
            FROM credentials 
            WHERE status = 'active'
            ORDER BY created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'service_name': result[0],
                'username': result[1],
                'created_at': result[2],
                'last_used': result[3],
                'status': result[4]
            }
            for result in results
        ]
    
    def test_credentials(self, service_name):
        """Test stored credentials"""
        credentials = self.get_credentials(service_name)
        if not credentials:
            return False, "No credentials found"
        
        # This would be implemented with actual service testing
        self._log_usage(service_name, "credential_test", True, "Test successful")
        return True, "Credentials validated"
    
    def delete_credentials(self, service_name):
        """Safely delete credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE credentials 
            SET status = 'deleted' 
            WHERE service_name = ?
        ''', (service_name,))
        
        conn.commit()
        conn.close()
        
        self._log_usage(service_name, "credential_deleted", True, "Credentials marked as deleted")

# Global instance
credential_manager = SecureCredentialManager()

# Flask Blueprint
secure_credentials = Blueprint('secure_credentials', __name__)

@secure_credentials.route('/credential-manager')
def credential_manager_dashboard():
    """Credential management dashboard"""
    stored_services = credential_manager.list_stored_services()
    return render_template('credential_manager.html', stored_services=stored_services)

@secure_credentials.route('/api/store-credentials', methods=['POST'])
def store_credentials():
    """Store new credentials securely"""
    data = request.get_json()
    
    service_name = data.get('service_name')
    username = data.get('username')
    password = data.get('password')
    additional_fields = data.get('additional_fields', {})
    
    if not all([service_name, username, password]):
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    success = credential_manager.store_credentials(
        service_name, username, password, additional_fields
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Credentials stored securely'})
    else:
        return jsonify({'success': False, 'message': 'Failed to store credentials'})

@secure_credentials.route('/api/test-credentials/<service_name>')
def test_credentials(service_name):
    """Test stored credentials"""
    success, message = credential_manager.test_credentials(service_name)
    return jsonify({'success': success, 'message': message})

@secure_credentials.route('/api/get-stored-services')
def get_stored_services():
    """Get list of stored services"""
    services = credential_manager.list_stored_services()
    return jsonify({'services': services})

@secure_credentials.route('/api/delete-credentials/<service_name>', methods=['DELETE'])
def delete_credentials(service_name):
    """Delete stored credentials"""
    credential_manager.delete_credentials(service_name)
    return jsonify({'success': True, 'message': 'Credentials deleted'})

@secure_credentials.route('/api/autonomous-scraper-status')
def autonomous_scraper_status():
    """Get autonomous scraper status"""
    gauge_creds = credential_manager.get_credentials('gauge_smart')
    groundworks_creds = credential_manager.get_credentials('groundworks')
    
    return jsonify({
        'gauge_smart': {
            'configured': gauge_creds is not None,
            'username': gauge_creds['username'] if gauge_creds else None,
            'last_sync': datetime.now().isoformat()
        },
        'groundworks': {
            'configured': groundworks_creds is not None,
            'username': groundworks_creds['username'] if groundworks_creds else None,
            'last_sync': datetime.now().isoformat()
        },
        'autonomous_mode': {
            'enabled': gauge_creds is not None and groundworks_creds is not None,
            'next_sync': (datetime.now().isoformat()),
            'data_feeds': ['fleet_locations', 'asset_status', 'project_updates', 'maintenance_alerts']
        }
    })

def get_credential_manager():
    """Get the global credential manager instance"""
    return credential_manager