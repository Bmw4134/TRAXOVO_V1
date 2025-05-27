"""
TRAXOVO Authentication Routes

Secure login/logout system with rate limiting and CSRF protection.
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import check_password_hash
from app import limiter

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

class LoginForm(FlaskForm):
    """Secure login form with CSRF protection"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class AdminCreateForm(FlaskForm):
    """Admin user creation form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Create Admin User')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Rate limiting for login attempts
def login():
    """Secure login with rate limiting"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        try:
            from models.user import User
            
            # Find user by username or email
            user = User.query.filter(
                (User.username == form.username.data) | 
                (User.email == form.username.data)
            ).first()
            
            if user and user.check_password(form.password.data):
                # Update last login
                user.last_login = datetime.utcnow()
                
                # Log successful login
                logger.info(f"Successful login for user: {user.username}")
                
                # Login user with Flask-Login
                login_user(user, remember=form.remember_me.data)
                
                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('index')
                
                flash(f"Welcome back, {user.username}!", "success")
                return redirect(next_page)
            else:
                # Log failed login attempt
                logger.warning(f"Failed login attempt for: {form.username.data}")
                flash("Invalid username or password", "danger")
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash("An error occurred during login. Please try again.", "danger")
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Secure logout with session cleanup"""
    username = current_user.username if current_user.is_authenticated else "Unknown"
    
    # Clear session data
    session.clear()
    
    # Logout user
    logout_user()
    
    logger.info(f"User logged out: {username}")
    flash("You have been logged out successfully.", "info")
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/create-admin', methods=['GET', 'POST'])
@limiter.limit("3 per hour")  # Strict rate limiting for admin creation
def create_admin():
    """Create initial admin user (only if no admins exist)"""
    try:
        from models.user import User
        from app import db
        
        # Check if any admin users exist
        admin_exists = User.query.filter_by(is_admin=True).first()
        if admin_exists:
            flash("Admin user already exists. Please contact your administrator.", "warning")
            return redirect(url_for('auth.login'))
        
        form = AdminCreateForm()
        
        if form.validate_on_submit():
            if form.password.data != form.confirm_password.data:
                flash("Passwords do not match.", "danger")
                return render_template('auth/create_admin.html', form=form)
            
            # Create admin user
            admin_user = User(
                username=form.username.data,
                email=form.email.data,
                is_admin=True,
                first_name="Admin",
                last_name="User"
            )
            admin_user.set_password(form.password.data)
            
            db.session.add(admin_user)
            db.session.commit()
            
            logger.info(f"Admin user created: {admin_user.username}")
            flash("Admin user created successfully! Please log in.", "success")
            return redirect(url_for('auth.login'))
        
        return render_template('auth/create_admin.html', form=form)
        
    except Exception as e:
        logger.error(f"Admin creation error: {str(e)}")
        flash("An error occurred creating admin user.", "danger")
        return redirect(url_for('auth.login'))

@auth_bp.route('/status')
def auth_status():
    """Authentication status endpoint for debugging"""
    return {
        'authenticated': current_user.is_authenticated,
        'user': current_user.username if current_user.is_authenticated else None,
        'is_admin': current_user.is_admin if current_user.is_authenticated else False
    }