"""
TRAXOVO Simple Login System - Quick Fix

This simplified version focuses on getting your beautiful login screen working
without the complex model relationships that are causing startup issues.
"""
import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "traxovo-secure-key-2025"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

db = SQLAlchemy(app, model_class=Base)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simplified User Model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    """Main dashboard - redirect to login if not authenticated"""
    if current_user.is_authenticated:
        return render_template('dashboard_simple.html', user=current_user)
    else:
        return redirect(url_for('login'))

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    """Beautiful TRAXOVO login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login_simple.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login_simple.html')

@app.route('/auth/logout')
@login_required
def logout():
    """Logout and redirect to login page"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/auth/create-admin')
def create_admin():
    """Create admin user if none exists"""
    try:
        admin_exists = User.query.filter_by(is_admin=True).first()
        
        if admin_exists:
            flash('Admin user already exists!', 'info')
            return redirect(url_for('login'))
        
        admin = User(
            username='admin',
            email='admin@traxovo.com',
            first_name='TRAXOVO',
            last_name='Administrator',
            is_admin=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        flash('Admin user created successfully! Username: admin, Password: admin123', 'success')
        return redirect(url_for('login'))
        
    except Exception as e:
        flash(f'Error creating admin user: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/secure-attendance')
@login_required
def secure_attendance():
    """Secure attendance processing page"""
    return render_template('secure_attendance_simple.html', user=current_user)

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'TRAXOVO Simple Login'}

# Create tables and run
with app.app_context():
    try:
        db.create_all()
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)