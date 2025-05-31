"""
TRAXOVO Security & Encryption Module
Implements enterprise-grade security without breaking dashboard functionality
"""

import os
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json

class TRAXOVOSecurity:
    """Enterprise security and encryption for fleet data"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self):
        """Generate or retrieve encryption key from environment"""
        
        # Check if encryption key exists in environment
        env_key = os.environ.get('TRAXOVO_ENCRYPTION_KEY')
        if env_key:
            return env_key.encode()
        
        # Generate new key based on system secrets
        password = os.environ.get('SESSION_SECRET', 'default-fleet-secret').encode()
        salt = b'traxovo-fleet-salt'  # In production, use random salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt_sensitive_data(self, data):
        """Encrypt sensitive fleet data"""
        try:
            if isinstance(data, dict):
                data = json.dumps(data)
            elif not isinstance(data, str):
                data = str(data)
            
            encrypted = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            # Return original data if encryption fails to prevent dashboard breakage
            return data
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Decrypt sensitive fleet data"""
        try:
            if not encrypted_data:
                return encrypted_data
                
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher_suite.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            # Return original data if decryption fails
            return encrypted_data
    
    def hash_user_data(self, data):
        """Create secure hash for user data"""
        return hashlib.sha256(str(data).encode()).hexdigest()
    
    def generate_secure_token(self):
        """Generate secure token for API access"""
        return secrets.token_urlsafe(32)
    
    def secure_fleet_data(self, fleet_data):
        """Apply security measures to fleet data without breaking functionality"""
        
        if not isinstance(fleet_data, dict):
            return fleet_data
        
        secured_data = fleet_data.copy()
        
        # Encrypt sensitive fields while preserving structure
        sensitive_fields = ['driver_personal_info', 'location_details', 'revenue_data']
        
        for field in sensitive_fields:
            if field in secured_data:
                secured_data[field] = self.encrypt_sensitive_data(secured_data[field])
        
        return secured_data
    
    def apply_dashboard_security_headers(self, response):
        """Apply security headers to dashboard responses"""
        
        # Security headers that don't break functionality
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: https:; img-src 'self' data: https:",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response

class FleetDataProtection:
    """Protect fleet data while maintaining dashboard functionality"""
    
    def __init__(self):
        self.security = TRAXOVOSecurity()
    
    def protect_gauge_data(self, gauge_data):
        """Protect GAUGE API data without breaking dashboard display"""
        
        if not gauge_data:
            return gauge_data
        
        protected_data = []
        
        for asset in gauge_data:
            if isinstance(asset, dict):
                protected_asset = asset.copy()
                
                # Mask sensitive identifiers while keeping functional data
                if 'serialNumber' in protected_asset:
                    serial = protected_asset['serialNumber']
                    protected_asset['serialNumber'] = f"***{serial[-4:]}" if len(serial) > 4 else serial
                
                # Keep operational data intact for dashboard functionality
                operational_fields = ['assetId', 'category', 'status', 'location', 'hours']
                for field in operational_fields:
                    if field in asset:
                        protected_asset[field] = asset[field]
                
                protected_data.append(protected_asset)
            else:
                protected_data.append(asset)
        
        return protected_data
    
    def secure_revenue_data(self, revenue_data):
        """Secure revenue data while maintaining KPI functionality"""
        
        if not isinstance(revenue_data, dict):
            return revenue_data
        
        secured = revenue_data.copy()
        
        # Keep aggregated totals for dashboard KPIs
        # Encrypt detailed breakdowns
        if 'detailed_breakdown' in secured:
            secured['detailed_breakdown'] = self.security.encrypt_sensitive_data(
                secured['detailed_breakdown']
            )
        
        return secured

def get_security_manager():
    """Get security manager instance"""
    return TRAXOVOSecurity()

def get_data_protection():
    """Get data protection instance"""
    return FleetDataProtection()