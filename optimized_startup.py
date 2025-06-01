"""
TRAXOVO Optimized Startup Configuration
Target: Reduce startup from 15-20s to under 5s
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

# Minimal app initialization
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Optimized database configuration  
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
    "pool_size": 5,  # Reduced from default
    "max_overflow": 10
}

db = SQLAlchemy(app, model_class=Base)

# Minimal user model
class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

# Lazy initialization flags
_db_initialized = False
_security_initialized = False
_blueprints_loaded = False

def init_security():
    """Initialize security components only when needed"""
    global _security_initialized
    if _security_initialized:
        return
    
    try:
        from flask_talisman import Talisman
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        from flask_wtf.csrf import CSRFProtect
        
        Talisman(app, force_https=False)
        limiter = Limiter(app, key_func=get_remote_address, default_limits=["1000 per hour"])
        csrf = CSRFProtect(app)
        _security_initialized = True
    except Exception as e:
        print(f"Security initialization warning: {e}")

def init_database():
    """Initialize database only when needed"""
    global _db_initialized
    if _db_initialized:
        return
        
    with app.app_context():
        db.create_all()
        _db_initialized = True

def load_blueprints():
    """Load blueprints only when first accessed"""
    global _blueprints_loaded
    if _blueprints_loaded:
        return
    
    # Only essential blueprints for core functionality
    essential_blueprints = [
        ('routes.pdf_export_routes', 'pdf_export_bp', None),
        ('blueprints.api', 'api_bp', '/api'),
        ('blueprints.dashboard', 'dashboard_bp', '/dashboard')
    ]
    
    for module_name, blueprint_name, url_prefix in essential_blueprints:
        try:
            module = __import__(module_name, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            if url_prefix:
                app.register_blueprint(blueprint, url_prefix=url_prefix)
            else:
                app.register_blueprint(blueprint)
        except (ImportError, AttributeError):
            pass
    
    _blueprints_loaded = True

@app.before_request
def lazy_initialization():
    """Initialize components on first request"""
    if not _db_initialized:
        init_database()
    if not _security_initialized:
        init_security()
    if not _blueprints_loaded:
        load_blueprints()

# Import main routes
from app import *