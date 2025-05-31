"""
TRAXOVO Multi-User Architecture
Role-based access control and scalable user management without architectural rewrites
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
import json
import hashlib

class UserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"
    WATSON = "watson"  # Special admin role

class Permission(Enum):
    # Fleet Management
    VIEW_FLEET = "view_fleet"
    MANAGE_ASSETS = "manage_assets"
    VIEW_ANALYTICS = "view_analytics"
    
    # Administrative
    MANAGE_USERS = "manage_users"
    VIEW_SYSTEM_HEALTH = "view_system_health"
    MANAGE_BILLING = "manage_billing"
    
    # Operations
    VIEW_ATTENDANCE = "view_attendance"
    MANAGE_ATTENDANCE = "manage_attendance"
    VIEW_REPORTS = "view_reports"
    GENERATE_REPORTS = "generate_reports"
    
    # Advanced Features
    AI_ASSISTANT = "ai_assistant"
    WORKFLOW_AUTOMATION = "workflow_automation"
    SYSTEM_CONFIGURATION = "system_configuration"

@dataclass
class UserProfile:
    user_id: str
    username: str
    email: str
    role: UserRole
    department: str
    permissions: Set[Permission]
    created_at: datetime
    last_login: Optional[datetime] = None
    active: bool = True
    preferences: Dict = None

class RoleManager:
    """Centralized role and permission management"""
    
    def __init__(self):
        self.role_permissions = self._initialize_role_permissions()
    
    def _initialize_role_permissions(self) -> Dict[UserRole, Set[Permission]]:
        """Define default permissions for each role"""
        return {
            UserRole.WATSON: {  # Full system access
                Permission.VIEW_FLEET,
                Permission.MANAGE_ASSETS,
                Permission.VIEW_ANALYTICS,
                Permission.MANAGE_USERS,
                Permission.VIEW_SYSTEM_HEALTH,
                Permission.MANAGE_BILLING,
                Permission.VIEW_ATTENDANCE,
                Permission.MANAGE_ATTENDANCE,
                Permission.VIEW_REPORTS,
                Permission.GENERATE_REPORTS,
                Permission.AI_ASSISTANT,
                Permission.WORKFLOW_AUTOMATION,
                Permission.SYSTEM_CONFIGURATION
            },
            UserRole.ADMIN: {  # Administrative access
                Permission.VIEW_FLEET,
                Permission.MANAGE_ASSETS,
                Permission.VIEW_ANALYTICS,
                Permission.MANAGE_USERS,
                Permission.MANAGE_BILLING,
                Permission.VIEW_ATTENDANCE,
                Permission.MANAGE_ATTENDANCE,
                Permission.VIEW_REPORTS,
                Permission.GENERATE_REPORTS,
                Permission.AI_ASSISTANT,
                Permission.WORKFLOW_AUTOMATION
            },
            UserRole.MANAGER: {  # Management access
                Permission.VIEW_FLEET,
                Permission.MANAGE_ASSETS,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_ATTENDANCE,
                Permission.MANAGE_ATTENDANCE,
                Permission.VIEW_REPORTS,
                Permission.GENERATE_REPORTS,
                Permission.AI_ASSISTANT
            },
            UserRole.OPERATOR: {  # Operational access
                Permission.VIEW_FLEET,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_ATTENDANCE,
                Permission.VIEW_REPORTS,
                Permission.AI_ASSISTANT
            },
            UserRole.VIEWER: {  # Read-only access
                Permission.VIEW_FLEET,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_ATTENDANCE,
                Permission.VIEW_REPORTS
            }
        }
    
    def get_role_permissions(self, role: UserRole) -> Set[Permission]:
        """Get permissions for a specific role"""
        return self.role_permissions.get(role, set())
    
    def has_permission(self, user_role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission"""
        return permission in self.get_role_permissions(user_role)

class UserSessionManager:
    """Manage user sessions and authentication state"""
    
    def __init__(self):
        self.active_sessions: Dict[str, UserProfile] = {}
        self.session_timeout = timedelta(hours=8)
    
    def create_session(self, user_profile: UserProfile) -> str:
        """Create a new user session"""
        session_id = self._generate_session_id(user_profile.user_id)
        user_profile.last_login = datetime.now()
        self.active_sessions[session_id] = user_profile
        return session_id
    
    def get_user_from_session(self, session_id: str) -> Optional[UserProfile]:
        """Get user profile from session ID"""
        user_profile = self.active_sessions.get(session_id)
        
        if user_profile and self._is_session_valid(user_profile):
            return user_profile
        elif user_profile:
            # Session expired, remove it
            self.active_sessions.pop(session_id, None)
        
        return None
    
    def invalidate_session(self, session_id: str):
        """Invalidate a user session"""
        self.active_sessions.pop(session_id, None)
    
    def _generate_session_id(self, user_id: str) -> str:
        """Generate unique session ID"""
        timestamp = str(datetime.now().timestamp())
        data = f"{user_id}_{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _is_session_valid(self, user_profile: UserProfile) -> bool:
        """Check if session is still valid"""
        if not user_profile.last_login:
            return False
        
        return datetime.now() - user_profile.last_login < self.session_timeout

class DepartmentManager:
    """Manage department-based access and data filtering"""
    
    def __init__(self):
        self.departments = {
            "Operations": {
                "description": "Field Operations and Equipment Management",
                "asset_access": "all",
                "default_role": UserRole.OPERATOR
            },
            "Management": {
                "description": "Executive and Strategic Management",
                "asset_access": "all",
                "default_role": UserRole.MANAGER
            },
            "Accounting": {
                "description": "Financial and Billing Operations",
                "asset_access": "billing_only",
                "default_role": UserRole.VIEWER
            },
            "Maintenance": {
                "description": "Equipment Maintenance and Service",
                "asset_access": "maintenance_only",
                "default_role": UserRole.OPERATOR
            },
            "Administration": {
                "description": "System Administration and IT",
                "asset_access": "all",
                "default_role": UserRole.ADMIN
            }
        }
    
    def get_department_assets(self, department: str, all_assets: List[Dict]) -> List[Dict]:
        """Filter assets based on department access"""
        dept_config = self.departments.get(department, {})
        access_level = dept_config.get("asset_access", "limited")
        
        if access_level == "all":
            return all_assets
        elif access_level == "billing_only":
            # Return only assets with billing data
            return [asset for asset in all_assets if asset.get('BillingRate')]
        elif access_level == "maintenance_only":
            # Return only assets requiring maintenance
            return [asset for asset in all_assets if asset.get('ServiceDue') or asset.get('MaintenanceNeeded')]
        else:
            # Limited access - only active assets
            return [asset for asset in all_assets if asset.get('Active', False)]

# Global instances
role_manager = RoleManager()
session_manager = UserSessionManager()
department_manager = DepartmentManager()

def require_permission(permission: Permission):
    """Decorator to require specific permission for route access"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import session, redirect, url_for, flash
            
            # Get current user from session
            session_id = session.get('session_id')
            if not session_id:
                flash('Authentication required')
                return redirect(url_for('login'))
            
            user_profile = session_manager.get_user_from_session(session_id)
            if not user_profile:
                flash('Session expired')
                return redirect(url_for('login'))
            
            # Check permission
            if not role_manager.has_permission(user_profile.role, permission):
                flash('Access denied - insufficient permissions')
                return redirect(url_for('dashboard'))
            
            # Add user to request context
            kwargs['current_user'] = user_profile
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

def get_current_user() -> Optional[UserProfile]:
    """Get current user profile from session"""
    from flask import session
    
    session_id = session.get('session_id')
    if session_id:
        return session_manager.get_user_from_session(session_id)
    return None

def create_user_profile(user_id: str, username: str, email: str, 
                       role: UserRole, department: str) -> UserProfile:
    """Create a new user profile with appropriate permissions"""
    permissions = role_manager.get_role_permissions(role)
    
    return UserProfile(
        user_id=user_id,
        username=username,
        email=email,
        role=role,
        department=department,
        permissions=permissions,
        created_at=datetime.now(),
        preferences={}
    )

def filter_data_by_user(data: List[Dict], user_profile: UserProfile) -> List[Dict]:
    """Filter data based on user's department and permissions"""
    if user_profile.role in [UserRole.WATSON, UserRole.ADMIN]:
        return data  # Full access
    
    # Apply department-based filtering
    return department_manager.get_department_assets(user_profile.department, data)

def get_user_dashboard_config(user_profile: UserProfile) -> Dict:
    """Get dashboard configuration based on user role and permissions"""
    config = {
        "modules": [],
        "theme": user_profile.preferences.get("theme", "default"),
        "department": user_profile.department,
        "role": user_profile.role.value
    }
    
    # Add modules based on permissions
    if Permission.VIEW_FLEET in user_profile.permissions:
        config["modules"].extend(["fleet_map", "asset_manager"])
    
    if Permission.VIEW_ANALYTICS in user_profile.permissions:
        config["modules"].append("analytics")
    
    if Permission.VIEW_ATTENDANCE in user_profile.permissions:
        config["modules"].append("attendance")
    
    if Permission.VIEW_REPORTS in user_profile.permissions:
        config["modules"].append("reports")
    
    if Permission.MANAGE_BILLING in user_profile.permissions:
        config["modules"].append("billing")
    
    if Permission.AI_ASSISTANT in user_profile.permissions:
        config["modules"].append("ai_assistant")
    
    if Permission.SYSTEM_CONFIGURATION in user_profile.permissions:
        config["modules"].extend(["system_health", "admin_panel"])
    
    return config

def get_system_stats() -> Dict:
    """Get multi-user system statistics"""
    active_users = len([u for u in session_manager.active_sessions.values() if u.active])
    
    role_distribution = {}
    department_distribution = {}
    
    for user in session_manager.active_sessions.values():
        role_distribution[user.role.value] = role_distribution.get(user.role.value, 0) + 1
        department_distribution[user.department] = department_distribution.get(user.department, 0) + 1
    
    return {
        "active_users": active_users,
        "total_sessions": len(session_manager.active_sessions),
        "role_distribution": role_distribution,
        "department_distribution": department_distribution,
        "departments": list(department_manager.departments.keys()),
        "timestamp": datetime.now().isoformat()
    }