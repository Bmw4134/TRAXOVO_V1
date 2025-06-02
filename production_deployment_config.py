"""
TRAXOVO Production Deployment Configuration
Enterprise-grade deployment with ASI → AGI → AI optimization
"""

import os
from datetime import datetime

class ProductionConfig:
    """Production deployment configuration"""
    
    # Core Application Settings
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 30
    }
    
    # Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # GAUGE API Configuration
    GAUGE_API_URL = os.environ.get('GAUGE_API_URL')
    GAUGE_API_KEY = os.environ.get('GAUGE_API_KEY')
    
    # High-Value API Integrations
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    FUEL_API_KEY = os.environ.get('FUEL_API_KEY')
    MACHINERY_TRADER_API_KEY = os.environ.get('MACHINERY_TRADER_API_KEY')
    DOT_COMPLIANCE_API_KEY = os.environ.get('DOT_COMPLIANCE_API_KEY')
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
    
    # Microsoft 365 Integration
    MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID')
    MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET')
    MICROSOFT_TENANT_ID = os.environ.get('MICROSOFT_TENANT_ID')
    
    # Performance Settings
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year for static files
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file upload
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s %(message)s'
    
    @staticmethod
    def init_app(app):
        """Initialize production configuration"""
        
        # Configure logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler(
                'logs/traxovo.log', 
                maxBytes=10240000, 
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('TRAXOVO startup')

class DevelopmentConfig:
    """Development configuration"""
    
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'dev-secret-key'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig:
    """Testing configuration"""
    
    TESTING = True
    SECRET_KEY = 'testing-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_deployment_status():
    """Get current deployment status and readiness"""
    
    required_env_vars = [
        'SESSION_SECRET',
        'DATABASE_URL',
        'GAUGE_API_KEY',
        'GAUGE_API_URL'
    ]
    
    optional_integrations = [
        'OPENWEATHER_API_KEY',
        'GOOGLE_MAPS_API_KEY',
        'MICROSOFT_CLIENT_ID'
    ]
    
    status = {
        "deployment_ready": True,
        "timestamp": datetime.now().isoformat(),
        "required_config": {},
        "optional_integrations": {},
        "deployment_score": 0
    }
    
    # Check required configuration
    for var in required_env_vars:
        configured = bool(os.environ.get(var))
        status["required_config"][var] = "CONFIGURED" if configured else "MISSING"
        if not configured:
            status["deployment_ready"] = False
    
    # Check optional integrations
    for var in optional_integrations:
        configured = bool(os.environ.get(var))
        status["optional_integrations"][var] = "CONFIGURED" if configured else "AVAILABLE"
    
    # Calculate deployment score
    required_score = len([v for v in status["required_config"].values() if v == "CONFIGURED"]) * 25
    optional_score = len([v for v in status["optional_integrations"].values() if v == "CONFIGURED"]) * 5
    status["deployment_score"] = min(100, required_score + optional_score)
    
    return status

if __name__ == "__main__":
    # Display deployment status
    import json
    status = get_deployment_status()
    print(json.dumps(status, indent=2))