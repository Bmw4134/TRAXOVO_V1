#!/usr/bin/env python3
"""
Create an admin user for TRAXORA system
"""
import os
import sys
from flask import Flask
from datetime import datetime
from werkzeug.security import generate_password_hash

# Create Flask app with minimal config
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Set up database
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Create app context
with app.app_context():
    # Define User model directly to avoid import issues
    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(64), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(256))
        is_admin = db.Column(db.Boolean, default=False)
        first_name = db.Column(db.String(64))
        last_name = db.Column(db.String(64))
        last_login = db.Column(db.DateTime)
        
        def set_password(self, password):
            self.password_hash = generate_password_hash(password)
        
        def check_password(self, password):
            from werkzeug.security import check_password_hash
            return check_password_hash(self.password_hash, password)
    
    # Create tables if they don't exist
    db.create_all()
    
    # Create admin user
    username = 'admin'
    password = 'admin123'
    
    # Check if user already exists
    admin_user = User.query.filter_by(username=username).first()
    
    if admin_user:
        print(f"Admin user already exists: {admin_user.username} / {admin_user.email}")
        # Update password
        admin_user.set_password(password)
        db.session.commit()
        print(f"Password reset to: {password}")
    else:
        # Create a new admin user
        user = User(
            username=username,
            email='admin@traxora.com',
            is_admin=True,
            first_name='Admin',
            last_name='User',
            last_login=datetime.utcnow()
        )
        user.set_password(password)
        
        # Add to database
        db.session.add(user)
        db.session.commit()
        
        print(f"Created admin user: {username} / {password}")

print(f"You can now log in with username '{username}' and password '{password}'")