"""
TRAXOVO Enterprise User Management System
Organizational hierarchy, role-based access control, and cross-department collaboration
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    DIRECTOR = "director"
    FOREMAN = "foreman"
    OPERATOR = "operator"
    VIEWER = "viewer"

class Organization(Enum):
    RAGLE_INC = "ragle_inc"
    SELECT_MAINTENANCE = "select_maintenance"
    SOUTHERN_SOURCING = "southern_sourcing"
    UNIFIED_SPECIALTIES = "unified_specialties"

class Department(Enum):
    EQUIPMENT = "equipment"
    OPERATIONS = "operations"
    MAINTENANCE = "maintenance"
    ADMINISTRATION = "administration"
    SOURCING = "sourcing"
    SPECIALTIES = "specialties"

@dataclass
class UserProfile:
    """Complete enterprise user profile"""
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    organization: str
    department: str
    role: str
    permissions: Dict[str, bool]
    database_access: List[str]
    cross_department_access: List[str]
    puppeteer_permissions: Dict[str, bool]
    created_date: str
    last_login: str
    active: bool

@dataclass
class CrossDepartmentRequest:
    """Request for cross-department collaboration"""
    id: str
    requester_id: str
    target_department: str
    target_user_id: Optional[str]
    request_type: str  # "access", "collaboration", "data_request"
    description: str
    priority: str
    status: str
    created_date: str
    approved_by: Optional[str]
    approval_date: Optional[str]

class TRAXOVOEnterpriseUserManager:
    """
    Enterprise-grade user management with organizational hierarchy
    """
    
    def __init__(self):
        self.users_file = "enterprise_users.json"
        self.requests_file = "cross_department_requests.json"
        self.users = self._load_users()
        self.cross_dept_requests = self._load_requests()
        self._initialize_default_users()
    
    def _load_users(self) -> List[UserProfile]:
        """Load users from file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    return [UserProfile(**user) for user in data]
            except Exception:
                return []
        return []
    
    def _load_requests(self) -> List[CrossDepartmentRequest]:
        """Load cross-department requests from file"""
        if os.path.exists(self.requests_file):
            try:
                with open(self.requests_file, 'r') as f:
                    data = json.load(f)
                    return [CrossDepartmentRequest(**req) for req in data]
            except Exception:
                return []
        return []
    
    def _save_users(self):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump([asdict(user) for user in self.users], f, indent=2)
    
    def _save_requests(self):
        """Save requests to file"""
        with open(self.requests_file, 'w') as f:
            json.dump([asdict(req) for req in self.cross_dept_requests], f, indent=2)
    
    def _initialize_default_users(self):
        """Initialize default organizational users"""
        default_users = [
            # Watson - AI/AGI Development Lead
            {
                "id": "watson",
                "username": "watson", 
                "email": "watson@traxovo.ai",
                "first_name": "Watson",
                "last_name": "AI",
                "organization": "ragle_inc",
                "department": "administration",
                "role": "admin",
                "permissions": self._get_admin_permissions(),
                "database_access": ["all"],
                "cross_department_access": ["all"],
                "puppeteer_permissions": {"reactive_changes": True, "data_collection": True}
            },
            # Leadership Team with Puppeteer Access
            {
                "id": "troy",
                "username": "troy",
                "email": "tsmith@ragleinc.com",
                "first_name": "Troy",
                "last_name": "Smith", 
                "organization": "ragle_inc",
                "department": "operations",
                "role": "director",
                "permissions": self._get_director_permissions(),
                "database_access": ["ragle_inc", "select_maintenance"],
                "cross_department_access": ["equipment", "maintenance", "operations"],
                "puppeteer_permissions": {"reactive_changes": True, "data_collection": True}
            },
            {
                "id": "william",
                "username": "william",
                "email": "william@ragleinc.com",
                "first_name": "William",
                "last_name": "Johnson",
                "organization": "ragle_inc", 
                "department": "operations",
                "role": "director",
                "permissions": self._get_director_permissions(),
                "database_access": ["ragle_inc", "unified_specialties"],
                "cross_department_access": ["equipment", "operations", "specialties"],
                "puppeteer_permissions": {"reactive_changes": True, "data_collection": True}
            },
            # Equipment Team
            {
                "id": "chris",
                "username": "chris",
                "email": "chris@ragleinc.com", 
                "first_name": "Chris",
                "last_name": "Equipment",
                "organization": "ragle_inc",
                "department": "equipment",
                "role": "operator",
                "permissions": self._get_operator_permissions(),
                "database_access": ["ragle_inc"],
                "cross_department_access": ["maintenance"],
                "puppeteer_permissions": {"reactive_changes": False, "data_collection": True}
            },
            {
                "id": "clint_mize",
                "username": "cmize",
                "email": "cmize@ragleinc.com",
                "first_name": "Clint",
                "last_name": "Mize",
                "organization": "ragle_inc",
                "department": "equipment", 
                "role": "director",
                "permissions": self._get_director_permissions(),
                "database_access": ["ragle_inc", "select_maintenance"],
                "cross_department_access": ["maintenance", "operations"],
                "puppeteer_permissions": {"reactive_changes": False, "data_collection": True}
            },
            # Field Team
            {
                "id": "michael_hammond", 
                "username": "mhammonds",
                "email": "mhammonds@ragleinc.com",
                "first_name": "Michael",
                "last_name": "Hammond",
                "organization": "ragle_inc",
                "department": "operations",
                "role": "foreman",
                "permissions": self._get_foreman_permissions(),
                "database_access": ["ragle_inc"],
                "cross_department_access": ["equipment"],
                "puppeteer_permissions": {"reactive_changes": False, "data_collection": True}
            },
            # Operations Team
            {
                "id": "cooper",
                "username": "cooper",
                "email": "cooper@ragleinc.com",
                "first_name": "Cooper", 
                "last_name": "Operations",
                "organization": "ragle_inc",
                "department": "operations",
                "role": "operator",
                "permissions": self._get_operator_permissions(),
                "database_access": ["ragle_inc"],
                "cross_department_access": ["equipment"],
                "puppeteer_permissions": {"reactive_changes": False, "data_collection": True}
            },
            {
                "id": "sebastian",
                "username": "sebastian",
                "email": "sebastian@ragleinc.com", 
                "first_name": "Sebastian",
                "last_name": "Operations",
                "organization": "ragle_inc",
                "department": "operations",
                "role": "operator",
                "permissions": self._get_operator_permissions(),
                "database_access": ["ragle_inc"],
                "cross_department_access": ["equipment"],
                "puppeteer_permissions": {"reactive_changes": False, "data_collection": True}
            },
            {
                "id": "ammar",
                "username": "ammar",
                "email": "ammar@ragleinc.com",
                "first_name": "Ammar",
                "last_name": "Operations", 
                "organization": "ragle_inc",
                "department": "operations",
                "role": "operator",
                "permissions": self._get_operator_permissions(),
                "database_access": ["ragle_inc"],
                "cross_department_access": ["equipment"],
                "puppeteer_permissions": {"reactive_changes": False, "data_collection": True}
            },
            {
                "id": "brittany",
                "username": "brittany",
                "email": "brittany@ragleinc.com",
                "first_name": "Brittany",
                "last_name": "Administration",
                "organization": "ragle_inc",
                "department": "administration",
                "role": "operator", 
                "permissions": self._get_operator_permissions(),
                "database_access": ["ragle_inc"],
                "cross_department_access": ["operations"],
                "puppeteer_permissions": {"reactive_changes": False, "data_collection": True}
            }
        ]
        
        # Add users that don't already exist
        existing_ids = [user.id for user in self.users]
        for user_data in default_users:
            if user_data["id"] not in existing_ids:
                user_data["created_date"] = datetime.now().isoformat()
                user_data["last_login"] = ""
                user_data["active"] = True
                self.users.append(UserProfile(**user_data))
        
        self._save_users()
    
    def get_user_database_access(self, user_id: str) -> List[str]:
        """Get databases a user can access based on their profile"""
        user = self.get_user_by_id(user_id)
        if not user:
            return []
        
        return user.database_access
    
    def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        """Get user by ID"""
        for user in self.users:
            if user.id == user_id:
                return user
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserProfile]:
        """Authenticate user login"""
        # In production, verify password hash
        user = next((u for u in self.users if u.username == username and u.active), None)
        if user:
            user.last_login = datetime.now().isoformat()
            self._save_users()
        return user
    
    def create_cross_department_request(self, requester_id: str, target_department: str, 
                                      request_type: str, description: str, 
                                      priority: str = "medium") -> str:
        """Create cross-department collaboration request"""
        request_id = f"req_{int(datetime.now().timestamp())}"
        
        request = CrossDepartmentRequest(
            id=request_id,
            requester_id=requester_id,
            target_department=target_department,
            target_user_id=None,
            request_type=request_type,
            description=description,
            priority=priority,
            status="pending",
            created_date=datetime.now().isoformat(),
            approved_by=None,
            approval_date=None
        )
        
        self.cross_dept_requests.append(request)
        self._save_requests()
        
        return request_id
    
    def approve_cross_department_request(self, request_id: str, approver_id: str) -> bool:
        """Approve cross-department request"""
        request = next((r for r in self.cross_dept_requests if r.id == request_id), None)
        if not request:
            return False
        
        approver = self.get_user_by_id(approver_id)
        if not approver or approver.role not in ["admin", "director"]:
            return False
        
        request.status = "approved"
        request.approved_by = approver_id
        request.approval_date = datetime.now().isoformat()
        
        self._save_requests()
        return True
    
    def get_pending_requests_for_department(self, department: str) -> List[Dict]:
        """Get pending requests for a specific department"""
        pending = [r for r in self.cross_dept_requests 
                  if r.target_department == department and r.status == "pending"]
        return [asdict(req) for req in pending]
    
    def get_user_permissions(self, user_id: str) -> Dict[str, bool]:
        """Get comprehensive user permissions"""
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        
        return {
            **user.permissions,
            "database_access": user.database_access,
            "cross_department_access": user.cross_department_access,
            "puppeteer_reactive": user.puppeteer_permissions.get("reactive_changes", False),
            "puppeteer_data": user.puppeteer_permissions.get("data_collection", False)
        }
    
    def _get_admin_permissions(self) -> Dict[str, bool]:
        """Get admin role permissions"""
        return {
            "view_all_data": True,
            "edit_all_data": True,
            "manage_users": True,
            "approve_requests": True,
            "system_administration": True,
            "cross_organization_access": True
        }
    
    def _get_director_permissions(self) -> Dict[str, bool]:
        """Get director role permissions"""
        return {
            "view_department_data": True,
            "edit_department_data": True,
            "manage_department_users": True,
            "approve_department_requests": True,
            "cross_department_collaboration": True,
            "equipment_management": True
        }
    
    def _get_foreman_permissions(self) -> Dict[str, bool]:
        """Get foreman role permissions"""
        return {
            "view_project_data": True,
            "edit_project_data": True,
            "manage_crew": True,
            "equipment_operation": True,
            "maintenance_requests": True
        }
    
    def _get_operator_permissions(self) -> Dict[str, bool]:
        """Get operator role permissions"""
        return {
            "view_assigned_data": True,
            "edit_assigned_data": True,
            "equipment_operation": True,
            "basic_reporting": True
        }
    
    def get_organization_analytics(self) -> Dict[str, Any]:
        """Get comprehensive organizational analytics"""
        analytics = {
            "total_users": len(self.users),
            "active_users": len([u for u in self.users if u.active]),
            "by_organization": {},
            "by_department": {},
            "by_role": {},
            "cross_dept_requests": {
                "total": len(self.cross_dept_requests),
                "pending": len([r for r in self.cross_dept_requests if r.status == "pending"]),
                "approved": len([r for r in self.cross_dept_requests if r.status == "approved"])
            },
            "puppeteer_enabled": len([u for u in self.users if u.puppeteer_permissions.get("data_collection", False)])
        }
        
        # Break down by organization
        for org in Organization:
            org_users = [u for u in self.users if u.organization == org.value]
            analytics["by_organization"][org.value] = len(org_users)
        
        # Break down by department
        for dept in Department:
            dept_users = [u for u in self.users if u.department == dept.value]
            analytics["by_department"][dept.value] = len(dept_users)
        
        # Break down by role
        for role in UserRole:
            role_users = [u for u in self.users if u.role == role.value]
            analytics["by_role"][role.value] = len(role_users)
        
        return analytics

# Global instance
enterprise_user_manager = TRAXOVOEnterpriseUserManager()

def get_enterprise_user_manager():
    """Get the global enterprise user manager instance"""
    return enterprise_user_manager