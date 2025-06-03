#!/usr/bin/env python3
"""
Quick TRAXOVO Admin Setup Script

Creates the initial admin user bypassing the relationship mapping issues.
"""
import os
import sys
from werkzeug.security import generate_password_hash

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def create_admin_user():
    """Create admin user directly"""
    try:
        with app.app_context():
            # Create tables if they don't exist
            db.create_all()
            
            # Direct SQL insertion to bypass model issues
            admin_exists = db.session.execute(
                "SELECT COUNT(*) FROM users WHERE is_admin = true"
            ).scalar()
            
            if admin_exists > 0:
                print("✅ Admin user already exists!")
                return True
            
            # Create admin user with direct SQL
            password_hash = generate_password_hash("admin123")
            
            db.session.execute("""
                INSERT INTO users (username, email, password_hash, is_admin, first_name, last_name, created_at)
                VALUES (:username, :email, :password_hash, :is_admin, :first_name, :last_name, NOW())
            """, {
                'username': 'admin',
                'email': 'admin@traxovo.com',
                'password_hash': password_hash,
                'is_admin': True,
                'first_name': 'TRAXOVO',
                'last_name': 'Administrator'
            })
            
            db.session.commit()
            
            print("✅ Admin user created successfully!")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Email: admin@traxovo.com")
            print("\n🚀 You can now log in to TRAXOVO!")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 TRAXOVO Admin Setup")
    print("=" * 30)
    
    success = create_admin_user()
    
    if success:
        print("\n✨ Setup complete! Access your secure TRAXOVO system:")
        print("   - Login: /auth/login")
        print("   - Admin Panel: /admin")
        print("   - Secure Attendance: /secure-attendance")
    else:
        print("\n💡 If issues persist, check the database connection.")