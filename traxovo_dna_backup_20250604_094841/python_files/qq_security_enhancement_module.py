"""
QQ Security Enhancement Module
Advanced security measures for TRAXOVO production deployment
"""

import os
import hashlib
import secrets
import logging
from functools import wraps
from flask import request, abort, session
from werkzeug.security import check_password_hash, generate_password_hash
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TRAXOVOSecurityEnforcer:
    """Advanced security enforcement for TRAXOVO"""
    
    def __init__(self):
        self.blocked_ips = set()
        self.rate_limits = {}
        self.security_patterns = self._load_security_patterns()
        
    def _load_security_patterns(self):
        """Load security threat patterns"""
        return {
            'sql_injection': [
                r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)",
                r"(\b--\b|\b/\*|\*/)",
                r"(\bOR\b.*=.*\bOR\b|\bAND\b.*=.*\bAND\b)"
            ],
            'xss_patterns': [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>.*?</iframe>"
            ],
            'path_traversal': [
                r"\.\./",
                r"\.\.\\",
                r"/etc/passwd",
                r"/proc/",
                r"\\windows\\system32"
            ]
        }
    
    def validate_input(self, input_data, input_type="general"):
        """Comprehensive input validation"""
        if not input_data:
            return True
        
        input_str = str(input_data).lower()
        
        # Check for SQL injection patterns
        for pattern in self.security_patterns['sql_injection']:
            if re.search(pattern, input_str, re.IGNORECASE):
                logger.warning(f"SQL injection attempt detected: {pattern}")
                return False
        
        # Check for XSS patterns
        for pattern in self.security_patterns['xss_patterns']:
            if re.search(pattern, input_str, re.IGNORECASE):
                logger.warning(f"XSS attempt detected: {pattern}")
                return False
        
        # Check for path traversal
        for pattern in self.security_patterns['path_traversal']:
            if re.search(pattern, input_str, re.IGNORECASE):
                logger.warning(f"Path traversal attempt detected: {pattern}")
                return False
        
        return True
    
    def sanitize_input(self, input_data):
        """Sanitize input data"""
        if not input_data:
            return input_data
        
        if isinstance(input_data, str):
            # Remove potentially dangerous characters
            sanitized = re.sub(r'[<>"\';\\&]', '', input_data)
            # Limit length
            sanitized = sanitized[:1000]  # Max 1000 characters
            return sanitized.strip()
        
        return input_data
    
    def check_rate_limit(self, client_ip, endpoint, limit=100, window=3600):
        """Check rate limiting for client IP and endpoint"""
        current_time = int(time.time())
        key = f"{client_ip}:{endpoint}"
        
        if key not in self.rate_limits:
            self.rate_limits[key] = []
        
        # Remove old requests outside the window
        self.rate_limits[key] = [
            timestamp for timestamp in self.rate_limits[key]
            if current_time - timestamp < window
        ]
        
        # Check if limit exceeded
        if len(self.rate_limits[key]) >= limit:
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            return False
        
        # Add current request
        self.rate_limits[key].append(current_time)
        return True

def security_required(f):
    """Security decorator for enhanced input validation"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        security_enforcer = get_security_enforcer()
        
        # Get client IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Check rate limiting
        if not security_enforcer.check_rate_limit(client_ip, request.endpoint):
            abort(429)  # Too Many Requests
        
        # Validate all form data
        if request.form:
            for key, value in request.form.items():
                if not security_enforcer.validate_input(value):
                    logger.warning(f"Invalid input detected in form field {key}")
                    abort(400)  # Bad Request
        
        # Validate JSON data
        if request.is_json and request.get_json():
            json_data = request.get_json()
            for key, value in json_data.items():
                if not security_enforcer.validate_input(value):
                    logger.warning(f"Invalid input detected in JSON field {key}")
                    abort(400)
        
        # Validate query parameters
        for key, value in request.args.items():
            if not security_enforcer.validate_input(value):
                logger.warning(f"Invalid input detected in query parameter {key}")
                abort(400)
        
        return f(*args, **kwargs)
    
    return decorated_function

def sanitize_form_data(form_data):
    """Sanitize form data"""
    security_enforcer = get_security_enforcer()
    sanitized_data = {}
    
    for key, value in form_data.items():
        sanitized_data[key] = security_enforcer.sanitize_input(value)
    
    return sanitized_data

def generate_secure_token():
    """Generate cryptographically secure token"""
    return secrets.token_urlsafe(32)

def hash_password(password):
    """Hash password securely"""
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

def verify_password(password, password_hash):
    """Verify password against hash"""
    return check_password_hash(password_hash, password)

def generate_csrf_token():
    """Generate CSRF token for forms"""
    if 'csrf_token' not in session:
        session['csrf_token'] = generate_secure_token()
    return session['csrf_token']

def validate_csrf_token(token):
    """Validate CSRF token"""
    return token and session.get('csrf_token') == token

def secure_filename(filename):
    """Ensure filename is secure"""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Limit length
    filename = filename[:100]
    
    # Ensure it's not empty
    if not filename or filename == '.':
        filename = 'upload'
    
    return filename

def encrypt_sensitive_data(data, key=None):
    """Basic encryption for sensitive data"""
    if key is None:
        key = os.environ.get('ENCRYPTION_KEY', 'default-key-change-in-production')
    
    # Simple encryption - in production, use proper encryption library
    key_hash = hashlib.sha256(key.encode()).digest()
    data_bytes = data.encode() if isinstance(data, str) else data
    
    # XOR encryption (for demonstration - use proper encryption in production)
    encrypted = bytearray()
    for i, byte in enumerate(data_bytes):
        encrypted.append(byte ^ key_hash[i % len(key_hash)])
    
    return encrypted.hex()

def decrypt_sensitive_data(encrypted_data, key=None):
    """Decrypt sensitive data"""
    if key is None:
        key = os.environ.get('ENCRYPTION_KEY', 'default-key-change-in-production')
    
    try:
        key_hash = hashlib.sha256(key.encode()).digest()
        encrypted_bytes = bytes.fromhex(encrypted_data)
        
        decrypted = bytearray()
        for i, byte in enumerate(encrypted_bytes):
            decrypted.append(byte ^ key_hash[i % len(key_hash)])
        
        return decrypted.decode()
    except:
        return None

class DatabaseSecurityManager:
    """Database security management"""
    
    @staticmethod
    def escape_sql_value(value):
        """Escape SQL values to prevent injection"""
        if value is None:
            return 'NULL'
        
        if isinstance(value, str):
            # Escape single quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        
        if isinstance(value, (int, float)):
            return str(value)
        
        return str(value)
    
    @staticmethod
    def validate_table_name(table_name):
        """Validate table name to prevent injection"""
        # Allow only alphanumeric characters and underscores
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            return table_name
        
        raise ValueError(f"Invalid table name: {table_name}")
    
    @staticmethod
    def validate_column_name(column_name):
        """Validate column name to prevent injection"""
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name):
            return column_name
        
        raise ValueError(f"Invalid column name: {column_name}")

# Global security enforcer instance
_security_enforcer = None

def get_security_enforcer():
    """Get global security enforcer instance"""
    global _security_enforcer
    if _security_enforcer is None:
        _security_enforcer = TRAXOVOSecurityEnforcer()
    return _security_enforcer

def initialize_security_module():
    """Initialize security module"""
    logger.info("TRAXOVO Security Enhancement Module initialized")
    return get_security_enforcer()

# Security configuration check
def validate_security_configuration():
    """Validate security configuration"""
    issues = []
    
    # Check for required environment variables
    required_secrets = ['SESSION_SECRET', 'DATABASE_URL']
    for secret in required_secrets:
        if not os.environ.get(secret):
            issues.append(f"Missing required secret: {secret}")
    
    # Check session secret strength
    session_secret = os.environ.get('SESSION_SECRET', '')
    if len(session_secret) < 32:
        issues.append("SESSION_SECRET should be at least 32 characters long")
    
    # Check if running in debug mode in production
    if os.environ.get('FLASK_ENV') == 'production' and os.environ.get('DEBUG', '').lower() == 'true':
        issues.append("Debug mode should be disabled in production")
    
    return issues

if __name__ == "__main__":
    # Run security configuration validation
    issues = validate_security_configuration()
    if issues:
        print("Security Configuration Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Security configuration validated successfully")