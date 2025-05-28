"""
Quick Access Route - Bypass for Demo
"""
from flask import Blueprint, redirect, url_for, session
from flask_login import login_user
from models import User

quick_access_bp = Blueprint('quick_access', __name__)

@quick_access_bp.route('/demo-access')
def demo_access():
    """Quick demo access bypass"""
    # Create or get demo user
    demo_user = User.query.filter_by(username='demo').first()
    if not demo_user:
        from app import db
        demo_user = User(username='demo', email='demo@traxovo.com')
        db.session.add(demo_user)
        db.session.commit()
    
    # Log in the demo user
    login_user(demo_user)
    session['user_id'] = demo_user.id
    
    return redirect(url_for('index'))