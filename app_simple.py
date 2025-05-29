"""
TRAXOVO Fleet Management System - Simplified Bootstrap
Production-ready application with executive authentication
"""

import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traxovo-fleet-2025")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

db = SQLAlchemy(app, model_class=Base)

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth_login'

# User model
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expires = db.Column(db.DateTime)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_id(self):
        return str(self.id)
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/auth/login', methods=['GET', 'POST'])
def auth_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/auth/logout')
@login_required
def auth_logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth_login'))

@app.route('/')
@login_required
def index():
    """TRAXOVO Executive Dashboard"""
    return render_template('index.html', 
                         current_user=current_user,
                         last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/fleet-manager-dashboard')
@login_required
def fleet_manager_dashboard():
    """Fleet Manager Portal for Chris Robertson"""
    return render_template('fleet_manager_dashboard.html')

@app.route('/financial-forecasting')
@login_required  
def financial_forecasting():
    """Executive Financial Forecasting"""
    return render_template('financial_forecasting.html')

@app.route('/intake-form')
@login_required
def intake_form():
    """Equipment Report with Photo Upload"""
    return render_template('intake_form.html')

@app.route('/time-logger')
@login_required
def time_logger():
    """Time Logger with Job Zone Tracking"""
    return render_template('time_logger.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Create tables
with app.app_context():
    try:
        db.create_all()
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)