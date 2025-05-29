#!/usr/bin/env python3
"""
Executive User Creation Script for TRAXOVO
Creates admin accounts for William Rather and Troy Ragle
"""

from app import app, db
from models.user import User
from datetime import datetime

def create_executive_users():
    """Create executive user accounts with admin privileges"""
    
    with app.app_context():
        # Create William Rather account
        william = User.query.filter_by(username='Rather').first()
        if not william:
            william = User(
                username='Rather',
                email='Wrather@ragleinc.com',
                first_name='William',
                last_name='Rather',
                is_admin=True,
                created_at=datetime.utcnow()
            )
            william.set_password('Executive2025!')
            db.session.add(william)
            print("✓ Created William Rather account (Rather/Executive2025!)")
        else:
            print("✓ William Rather account already exists")
        
        # Create Troy Ragle account
        troy = User.query.filter_by(username='Ragle').first()
        if not troy:
            troy = User(
                username='Ragle',
                email='Tragle@ragleinc.com',
                first_name='Troy',
                last_name='Ragle',
                is_admin=True,
                created_at=datetime.utcnow()
            )
            troy.set_password('Executive2025!')
            db.session.add(troy)
            print("✓ Created Troy Ragle account (Ragle/Executive2025!)")
        else:
            print("✓ Troy Ragle account already exists")
        
        # Commit changes
        try:
            db.session.commit()
            print("\n🎯 Executive accounts created successfully!")
            print("Users can now log in with their credentials.")
            print("Password reset functionality is available through the login page.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating users: {e}")

if __name__ == '__main__':
    create_executive_users()