#!/usr/bin/env python3
"""
Create a test user for TRAXORA system
"""
import os
from flask import Flask
from datetime import datetime

# Create Flask app with minimal config
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Import db after app initialization
from db import db
db.init_app(app)

# Import User model
from models.user import User

# Create app context
with app.app_context():
    # Check if test user already exists
    test_user = User.query.filter_by(username='test').first()
    
    if test_user:
        print(f"Test user already exists: {test_user.username} / {test_user.email}")
        # Update password
        test_user.set_password('test123')
        db.session.commit()
        print("Password reset to: test123")
    else:
        # Create a new test user
        user = User(
            username='test',
            email='test@traxora.com',
            is_admin=True,
            first_name='Test',
            last_name='User',
            last_login=datetime.utcnow()
        )
        user.set_password('test123')
        
        # Add to database
        db.session.add(user)
        db.session.commit()
        
        print(f"Created test user: test@traxora.com / test123")

print("You can now log in with username 'test' and password 'test123'")