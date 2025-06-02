"""
Secure Enterprise Authentication System
Real user authentication with role-based access and data security
"""

import hashlib
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class SecureUser:
    """Secure user profile with enterprise authentication"""
    user_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    department: str
    organization: str
    access_level: int  # 1-10 security clearance
    permissions: Dict[str, bool]
    password_hash: str
    last_login: Optional[datetime]
    created_date: datetime
    active: bool

class SecureEnterpriseAuth:
    """
    Enterprise-grade secure authentication system
    Real user authentication for production testing
    """
    
    def __init__(self):
        self.users_file = "secure_users.json"
        self.session_file = "active_sessions.json"
        self.users = self._load_secure_users()
        self.active_sessions = {}
        self._initialize_enterprise_users()
    
    def _load_secure_users(self) -> List[SecureUser]:
        """Load secure user data"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    users = []
                    for user_data in data.get('users', []):
                        user_data['last_login'] = datetime.fromisoformat(user_data['last_login']) if user_data.get('last_login') else None
                        user_data['created_date'] = datetime.fromisoformat(user_data['created_date'])
                        users.append(SecureUser(**user_data))
                    return users
            except Exception:
                pass
        return []
    
    def _hash_password(self, password: str) -> str:
        """Secure password hashing"""
        salt = os.urandom(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + password_hash.hex()
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt = bytes.fromhex(stored_hash[:64])
            stored_password_hash = stored_hash[64:]
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return password_hash.hex() == stored_password_hash
        except Exception:
            return False
    
    def _initialize_enterprise_users(self):
        """Initialize secure enterprise users for production testing"""
        if not self.users:
            secure_users = [
                # Watson - System Administrator
                {
                    "user_id": "watson_admin",
                    "username": "watson",
                    "email": "watson@ragleinc.com",
                    "first_name": "Watson",
                    "last_name": "AI",
                    "role": "SYSTEM_ADMIN",
                    "department": "TECHNOLOGY",
                    "organization": "RAGLE_INC",
                    "access_level": 10,
                    "permissions": {
                        "full_system_access": True,
                        "quantum_asi_access": True,
                        "security_admin": True,
                        "user_management": True,
                        "data_export": True,
                        "report_generation": True
                    },
                    "password_hash": self._hash_password("Watson2025!Quantum"),
                    "last_login": None,
                    "created_date": datetime.now(),
                    "active": True
                },
                # Chris - Equipment Team Lead
                {
                    "user_id": "chris_equipment",
                    "username": "chris",
                    "email": "chris@ragleinc.com",
                    "first_name": "Chris",
                    "last_name": "Equipment",
                    "role": "EQUIPMENT_LEAD",
                    "department": "EQUIPMENT",
                    "organization": "RAGLE_INC",
                    "access_level": 7,
                    "permissions": {
                        "equipment_access": True,
                        "fleet_management": True,
                        "maintenance_reports": True,
                        "asset_tracking": True,
                        "data_export": True,
                        "report_generation": True
                    },
                    "password_hash": self._hash_password("ChrisFleet2025!"),
                    "last_login": None,
                    "created_date": datetime.now(),
                    "active": True
                },
                # VP Level Access
                {
                    "user_id": "vp_operations",
                    "username": "vpops",
                    "email": "vp.operations@ragleinc.com",
                    "first_name": "VP",
                    "last_name": "Operations",
                    "role": "VICE_PRESIDENT",
                    "department": "EXECUTIVE",
                    "organization": "RAGLE_INC",
                    "access_level": 9,
                    "permissions": {
                        "executive_dashboard": True,
                        "financial_reports": True,
                        "strategic_analytics": True,
                        "full_fleet_access": True,
                        "cross_department": True,
                        "data_export": True,
                        "report_generation": True
                    },
                    "password_hash": self._hash_password("VPRagle2025!Executive"),
                    "last_login": None,
                    "created_date": datetime.now(),
                    "active": True
                },
                # Manager Level Access
                {
                    "user_id": "manager_ops",
                    "username": "manager",
                    "email": "manager@ragleinc.com",
                    "first_name": "Operations",
                    "last_name": "Manager",
                    "role": "OPERATIONS_MANAGER",
                    "department": "OPERATIONS",
                    "organization": "RAGLE_INC",
                    "access_level": 8,
                    "permissions": {
                        "operations_dashboard": True,
                        "team_management": True,
                        "operational_reports": True,
                        "fleet_monitoring": True,
                        "staff_analytics": True,
                        "data_export": True,
                        "report_generation": True
                    },
                    "password_hash": self._hash_password("ManagerRagle2025!"),
                    "last_login": None,
                    "created_date": datetime.now(),
                    "active": True
                },
                # Demo User for Testing
                {
                    "user_id": "demo_user",
                    "username": "demo",
                    "email": "demo@ragleinc.com",
                    "first_name": "Demo",
                    "last_name": "User",
                    "role": "OPERATOR",
                    "department": "OPERATIONS",
                    "organization": "RAGLE_INC",
                    "access_level": 5,
                    "permissions": {
                        "basic_dashboard": True,
                        "view_reports": True,
                        "fleet_viewing": True,
                        "basic_analytics": True
                    },
                    "password_hash": self._hash_password("DemoRagle2025!"),
                    "last_login": None,
                    "created_date": datetime.now(),
                    "active": True
                }
            ]
            
            for user_data in secure_users:
                self.users.append(SecureUser(**user_data))
            
            self._save_users()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with secure credentials"""
        user = next((u for u in self.users if u.username == username and u.active), None)
        
        if user and self._verify_password(password, user.password_hash):
            # Update last login
            user.last_login = datetime.now()
            
            # Create secure session
            session_data = {
                "user_id": user.user_id,
                "username": user.username,
                "role": user.role,
                "access_level": user.access_level,
                "permissions": user.permissions,
                "login_time": datetime.now().isoformat(),
                "organization": user.organization,
                "department": user.department
            }
            
            self.active_sessions[user.username] = session_data
            self._save_users()
            
            return session_data
        
        return None
    
    def get_user_dashboard_config(self, username: str) -> Dict[str, Any]:
        """Get user-specific dashboard configuration"""
        user = next((u for u in self.users if u.username == username), None)
        if not user:
            return {}
        
        # Dashboard configuration based on role and permissions
        config = {
            "user_info": {
                "name": f"{user.first_name} {user.last_name}",
                "role": user.role,
                "department": user.department,
                "access_level": user.access_level
            },
            "available_modules": [],
            "data_access_level": "RESTRICTED",
            "export_permissions": user.permissions.get("data_export", False),
            "report_permissions": user.permissions.get("report_generation", False)
        }
        
        # Configure modules based on permissions
        if user.permissions.get("full_system_access"):
            config["available_modules"] = ["dashboard", "quantum_asi", "analytics", "reports", "admin"]
            config["data_access_level"] = "FULL"
        elif user.permissions.get("executive_dashboard"):
            config["available_modules"] = ["dashboard", "analytics", "reports", "strategic"]
            config["data_access_level"] = "EXECUTIVE"
        elif user.permissions.get("equipment_access"):
            config["available_modules"] = ["dashboard", "equipment", "maintenance", "reports"]
            config["data_access_level"] = "EQUIPMENT"
        elif user.permissions.get("operations_dashboard"):
            config["available_modules"] = ["dashboard", "operations", "team", "reports"]
            config["data_access_level"] = "OPERATIONS"
        else:
            config["available_modules"] = ["dashboard", "basic_reports"]
            config["data_access_level"] = "BASIC"
        
        return config
    
    def _save_users(self):
        """Save users to secure file"""
        users_data = []
        for user in self.users:
            user_dict = asdict(user)
            user_dict['last_login'] = user.last_login.isoformat() if user.last_login else None
            user_dict['created_date'] = user.created_date.isoformat()
            users_data.append(user_dict)
        
        with open(self.users_file, 'w') as f:
            json.dump({
                "users": users_data,
                "last_updated": datetime.now().isoformat(),
                "security_version": "1.0"
            }, f, indent=2)
    
    def get_user_credentials_for_testing(self) -> Dict[str, str]:
        """Get secure credentials for testing tonight"""
        return {
            "Watson (System Admin)": "Username: watson | Password: Watson2025!Quantum",
            "Chris (Equipment Lead)": "Username: chris | Password: ChrisFleet2025!",
            "VP Operations": "Username: vpops | Password: VPRagle2025!Executive",
            "Operations Manager": "Username: manager | Password: ManagerRagle2025!",
            "Demo User": "Username: demo | Password: DemoRagle2025!"
        }

# Global secure authentication instance
_secure_auth = None

def get_secure_auth():
    """Get secure authentication system"""
    global _secure_auth
    if _secure_auth is None:
        _secure_auth = SecureEnterpriseAuth()
    return _secure_auth