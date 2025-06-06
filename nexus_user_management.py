"""
NEXUS User Management System
Comprehensive user accounts, password reset, and authentication
"""

import os
import json
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List

class NexusUserManager:
    """Complete user management system for NEXUS platform"""
    
    def __init__(self):
        self.users_file = "config/nexus_users.json"
        self.reset_tokens_file = "config/password_reset_tokens.json"
        self.ensure_config_directory()
        self.initialize_users()
    
    def ensure_config_directory(self):
        """Ensure config directory exists"""
        os.makedirs("config", exist_ok=True)
    
    def initialize_users(self):
        """Initialize default users if file doesn't exist"""
        if not os.path.exists(self.users_file):
            default_users = {
                "nexus_admin": {
                    "password_hash": self.hash_password("nexus2025"),
                    "role": "admin",
                    "permissions": ["user_management", "system_admin", "trading", "automation"],
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "email": "admin@nexus-intelligence.com",
                    "phone": "817-995-3894",
                    "status": "active"
                },
                "nexus_demo": {
                    "password_hash": self.hash_password("demo2025"),
                    "role": "user",
                    "permissions": ["basic_access", "demo_features"],
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "email": "demo@nexus-intelligence.com",
                    "phone": None,
                    "status": "active"
                },
                "automation_manager": {
                    "password_hash": self.hash_password("automation2025"),
                    "role": "manager",
                    "permissions": ["automation", "trading", "user_view"],
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "email": "automation@nexus-intelligence.com",
                    "phone": None,
                    "status": "active"
                },
                "trading_specialist": {
                    "password_hash": self.hash_password("trading2025"),
                    "role": "specialist",
                    "permissions": ["trading", "market_data", "analytics"],
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "email": "trading@nexus-intelligence.com",
                    "phone": None,
                    "status": "active"
                },
                "mobile_user": {
                    "password_hash": self.hash_password("mobile2025"),
                    "role": "mobile",
                    "permissions": ["mobile_terminal", "voice_commands", "basic_access"],
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "email": "mobile@nexus-intelligence.com",
                    "phone": None,
                    "status": "active"
                }
            }
            
            self.save_users(default_users)
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = "nexus_intelligence_2025"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def load_users(self) -> Dict:
        """Load users from file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_users(self, users_data: Dict):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(users_data, f, indent=2)
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Authenticate user login"""
        users = self.load_users()
        
        if username not in users:
            return {"success": False, "message": "Invalid username"}
        
        user_data = users[username]
        
        if user_data["status"] != "active":
            return {"success": False, "message": "Account disabled"}
        
        password_hash = self.hash_password(password)
        
        if password_hash != user_data["password_hash"]:
            return {"success": False, "message": "Invalid password"}
        
        # Update last login
        users[username]["last_login"] = datetime.now().isoformat()
        self.save_users(users)
        
        return {
            "success": True,
            "user": {
                "username": username,
                "role": user_data["role"],
                "permissions": user_data["permissions"],
                "email": user_data["email"]
            }
        }
    
    def generate_reset_token(self, username: str) -> str:
        """Generate password reset token"""
        users = self.load_users()
        
        if username not in users:
            return None
        
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        
        # Load existing tokens
        try:
            with open(self.reset_tokens_file, 'r') as f:
                tokens = json.load(f)
        except FileNotFoundError:
            tokens = {}
        
        tokens[token] = {
            "username": username,
            "expires_at": expires_at,
            "used": False
        }
        
        # Save tokens
        with open(self.reset_tokens_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        return token
    
    def reset_password(self, token: str, new_password: str) -> Dict:
        """Reset password using token"""
        try:
            with open(self.reset_tokens_file, 'r') as f:
                tokens = json.load(f)
        except FileNotFoundError:
            return {"success": False, "message": "Invalid token"}
        
        if token not in tokens:
            return {"success": False, "message": "Invalid token"}
        
        token_data = tokens[token]
        
        if token_data["used"]:
            return {"success": False, "message": "Token already used"}
        
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now() > expires_at:
            return {"success": False, "message": "Token expired"}
        
        # Update password
        username = token_data["username"]
        users = self.load_users()
        
        if username not in users:
            return {"success": False, "message": "User not found"}
        
        users[username]["password_hash"] = self.hash_password(new_password)
        self.save_users(users)
        
        # Mark token as used
        tokens[token]["used"] = True
        with open(self.reset_tokens_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        return {"success": True, "message": "Password reset successfully"}
    
    def get_all_users(self) -> List[Dict]:
        """Get all users for admin panel"""
        users = self.load_users()
        user_list = []
        
        for username, data in users.items():
            user_list.append({
                "username": username,
                "role": data["role"],
                "email": data["email"],
                "status": data["status"],
                "last_login": data["last_login"],
                "created_at": data["created_at"]
            })
        
        return user_list
    
    def create_user(self, username: str, password: str, role: str, email: str, permissions: List[str]) -> Dict:
        """Create new user"""
        users = self.load_users()
        
        if username in users:
            return {"success": False, "message": "Username already exists"}
        
        users[username] = {
            "password_hash": self.hash_password(password),
            "role": role,
            "permissions": permissions,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "email": email,
            "phone": None,
            "status": "active"
        }
        
        self.save_users(users)
        
        return {"success": True, "message": "User created successfully"}
    
    def update_user_status(self, username: str, status: str) -> Dict:
        """Update user status (active/disabled)"""
        users = self.load_users()
        
        if username not in users:
            return {"success": False, "message": "User not found"}
        
        users[username]["status"] = status
        self.save_users(users)
        
        return {"success": True, "message": f"User status updated to {status}"}

# Global user manager instance
user_manager = NexusUserManager()

def authenticate_user(username: str, password: str):
    """Authenticate user login"""
    return user_manager.authenticate_user(username, password)

def generate_reset_token(username: str):
    """Generate password reset token"""
    return user_manager.generate_reset_token(username)

def reset_password(token: str, new_password: str):
    """Reset password using token"""
    return user_manager.reset_password(token, new_password)

def get_all_users():
    """Get all users"""
    return user_manager.get_all_users()

def create_user(username: str, password: str, role: str, email: str, permissions: List[str]):
    """Create new user"""
    return user_manager.create_user(username, password, role, email, permissions)

def get_user_login_info():
    """Get consolidated user login information"""
    return {
        "primary_accounts": [
            {
                "username": "nexus_admin",
                "password": "nexus2025",
                "role": "Administrator",
                "description": "Full system access, user management, all features",
                "phone": "817-995-3894"
            },
            {
                "username": "nexus_demo", 
                "password": "demo2025",
                "role": "Demo User",
                "description": "Basic access, demo features, limited permissions"
            },
            {
                "username": "automation_manager",
                "password": "automation2025", 
                "role": "Automation Manager",
                "description": "Automation workflows, trading access, user viewing"
            },
            {
                "username": "trading_specialist",
                "password": "trading2025",
                "role": "Trading Specialist", 
                "description": "Trading features, market data, analytics dashboard"
            },
            {
                "username": "mobile_user",
                "password": "mobile2025",
                "role": "Mobile User",
                "description": "Mobile terminal, voice commands, basic access"
            }
        ],
        "password_reset": {
            "available": True,
            "method": "Username lookup + secure token",
            "token_expiry": "1 hour",
            "admin_override": "Available via nexus_admin account"
        },
        "emergency_access": {
            "admin_phone": "817-995-3894",
            "emergency_reset": "Contact admin for immediate password reset",
            "backup_access": "Database direct access if needed"
        }
    }