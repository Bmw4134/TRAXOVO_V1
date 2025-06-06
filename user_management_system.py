"""
User Management System
Complete user list, authentication, and role management for NEXUS COMMAND
"""

import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class User:
    """User data structure"""
    user_id: str
    username: str
    email: str
    full_name: str
    role: str
    department: str
    access_level: int
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []

class UserManagementSystem:
    """Complete user management for NEXUS COMMAND platform"""
    
    def __init__(self):
        self.users_file = "nexus_users.json"
        self.sessions_file = "nexus_sessions.json"
        self.users = {}
        self.active_sessions = {}
        self._initialize_users()
        
    def _initialize_users(self):
        """Initialize user database with executive team and operational users"""
        
        # Load existing users or create default set
        if os.path.exists(self.users_file):
            self._load_users_from_file()
        else:
            self._create_default_users()
            self._save_users_to_file()
    
    def _create_default_users(self):
        """Create default user set for NEXUS COMMAND platform"""
        
        default_users = [
            # Executive Team
            {
                'user_id': 'james_exec',
                'username': 'james',
                'email': 'james@nexuscommand.com',
                'full_name': 'James Anderson',
                'role': 'Chief Executive Officer',
                'department': 'Executive',
                'access_level': 10,
                'permissions': ['all_access', 'executive_dashboard', 'financial_data', 'user_management']
            },
            {
                'user_id': 'chris_exec',
                'username': 'chris',
                'email': 'chris@nexuscommand.com',
                'full_name': 'Chris Williams',
                'role': 'Chief Technology Officer',
                'department': 'Technology',
                'access_level': 10,
                'permissions': ['all_access', 'system_admin', 'technical_data', 'platform_control']
            },
            {
                'user_id': 'britney_exec',
                'username': 'britney',
                'email': 'britney@nexuscommand.com',
                'full_name': 'Britney Johnson',
                'role': 'Chief Operations Officer',
                'department': 'Operations',
                'access_level': 9,
                'permissions': ['operations_control', 'fleet_management', 'optimization_tools', 'reporting']
            },
            {
                'user_id': 'cooper_exec',
                'username': 'cooper',
                'email': 'cooper@nexuscommand.com',
                'full_name': 'Cooper Davis',
                'role': 'Chief Financial Officer',
                'department': 'Finance',
                'access_level': 9,
                'permissions': ['financial_control', 'trading_access', 'roi_analysis', 'budget_management']
            },
            
            # Senior Management
            {
                'user_id': 'ammar_mgmt',
                'username': 'ammar',
                'email': 'ammar@nexuscommand.com',
                'full_name': 'Ammar Hassan',
                'role': 'Director of Analytics',
                'department': 'Analytics',
                'access_level': 8,
                'permissions': ['analytics_access', 'data_visualization', 'business_intelligence', 'reporting']
            },
            {
                'user_id': 'jacob_mgmt',
                'username': 'jacob',
                'email': 'jacob@nexuscommand.com',
                'full_name': 'Jacob Miller',
                'role': 'Director of Engineering',
                'department': 'Engineering',
                'access_level': 8,
                'permissions': ['engineering_control', 'system_optimization', 'workflow_management', 'technical_support']
            },
            {
                'user_id': 'william_mgmt',
                'username': 'william',
                'email': 'william@nexuscommand.com',
                'full_name': 'William Thompson',
                'role': 'Director of Security',
                'department': 'Security',
                'access_level': 8,
                'permissions': ['security_control', 'user_management', 'audit_access', 'compliance_monitoring']
            },
            {
                'user_id': 'troy_mgmt',
                'username': 'troy',
                'email': 'troy@nexuscommand.com',
                'full_name': 'Troy Martinez',
                'role': 'Director of Fleet Operations',
                'department': 'Fleet',
                'access_level': 7,
                'permissions': ['fleet_control', 'asset_tracking', 'route_optimization', 'maintenance_scheduling']
            },
            
            # Operational Staff
            {
                'user_id': 'sarah_ops',
                'username': 'sarah',
                'email': 'sarah@nexuscommand.com',
                'full_name': 'Sarah Connor',
                'role': 'Senior Analyst',
                'department': 'Analytics',
                'access_level': 6,
                'permissions': ['data_analysis', 'reporting', 'dashboard_access']
            },
            {
                'user_id': 'mike_ops',
                'username': 'mike',
                'email': 'mike@nexuscommand.com',
                'full_name': 'Michael Rodriguez',
                'role': 'Fleet Coordinator',
                'department': 'Fleet',
                'access_level': 5,
                'permissions': ['fleet_monitoring', 'dispatch_control', 'basic_reporting']
            },
            {
                'user_id': 'lisa_ops',
                'username': 'lisa',
                'email': 'lisa@nexuscommand.com',
                'full_name': 'Lisa Chen',
                'role': 'Financial Analyst',
                'department': 'Finance',
                'access_level': 6,
                'permissions': ['financial_analysis', 'cost_tracking', 'budget_reporting']
            },
            {
                'user_id': 'david_ops',
                'username': 'david',
                'email': 'david@nexuscommand.com',
                'full_name': 'David Brown',
                'role': 'System Administrator',
                'department': 'Technology',
                'access_level': 7,
                'permissions': ['system_monitoring', 'user_support', 'maintenance_access']
            }
        ]
        
        # Create User objects and store
        for user_data in default_users:
            user = User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                role=user_data['role'],
                department=user_data['department'],
                access_level=user_data['access_level'],
                permissions=user_data['permissions'],
                created_at=datetime.now().isoformat()
            )
            self.users[user.user_id] = user
    
    def _load_users_from_file(self):
        """Load users from JSON file"""
        
        try:
            with open(self.users_file, 'r') as f:
                users_data = json.load(f)
            
            for user_data in users_data:
                user = User(**user_data)
                self.users[user.user_id] = user
                
        except Exception as e:
            print(f"Error loading users: {e}")
            self._create_default_users()
    
    def _save_users_to_file(self):
        """Save users to JSON file"""
        
        try:
            users_data = [asdict(user) for user in self.users.values()]
            
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get complete user list with all details"""
        
        users_list = []
        
        for user in self.users.values():
            user_info = {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'department': user.department,
                'access_level': user.access_level,
                'permissions': user.permissions,
                'is_active': user.is_active,
                'created_at': user.created_at,
                'last_login': user.last_login
            }
            users_list.append(user_info)
        
        # Sort by access level (highest first), then by department
        users_list.sort(key=lambda x: (-x['access_level'], x['department'], x['full_name']))
        
        return users_list
    
    def get_users_by_department(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get users organized by department"""
        
        departments = {}
        
        for user in self.users.values():
            if user.department not in departments:
                departments[user.department] = []
            
            user_info = {
                'user_id': user.user_id,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'access_level': user.access_level,
                'is_active': user.is_active,
                'last_login': user.last_login
            }
            departments[user.department].append(user_info)
        
        # Sort users within each department by access level
        for dept in departments:
            departments[dept].sort(key=lambda x: -x['access_level'])
        
        return departments
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user details by username"""
        
        for user in self.users.values():
            if user.username.lower() == username.lower():
                return {
                    'user_id': user.user_id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'department': user.department,
                    'access_level': user.access_level,
                    'permissions': user.permissions,
                    'is_active': user.is_active,
                    'created_at': user.created_at,
                    'last_login': user.last_login
                }
        
        return None
    
    def get_executives_list(self) -> List[Dict[str, Any]]:
        """Get executive team members"""
        
        executives = []
        
        for user in self.users.values():
            if user.access_level >= 9:  # Executive level
                exec_info = {
                    'user_id': user.user_id,
                    'full_name': user.full_name,
                    'role': user.role,
                    'department': user.department,
                    'email': user.email,
                    'access_level': user.access_level
                }
                executives.append(exec_info)
        
        executives.sort(key=lambda x: -x['access_level'])
        return executives
    
    def authenticate_user(self, username: str, create_session: bool = True) -> Optional[Dict[str, Any]]:
        """Authenticate user and create session"""
        
        user_data = self.get_user_by_username(username)
        
        if user_data and user_data['is_active']:
            # Update last login
            user = self.users[user_data['user_id']]
            user.last_login = datetime.now().isoformat()
            self._save_users_to_file()
            
            if create_session:
                session_id = f"session_{user_data['user_id']}_{int(time.time())}"
                self.active_sessions[session_id] = {
                    'user_id': user_data['user_id'],
                    'username': username,
                    'created_at': datetime.now().isoformat(),
                    'last_activity': datetime.now().isoformat()
                }
                
                user_data['session_id'] = session_id
            
            return user_data
        
        return None
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        
        total_users = len(self.users)
        active_users = sum(1 for user in self.users.values() if user.is_active)
        
        departments_count = {}
        access_levels_count = {}
        
        for user in self.users.values():
            # Department stats
            if user.department not in departments_count:
                departments_count[user.department] = 0
            departments_count[user.department] += 1
            
            # Access level stats
            if user.access_level not in access_levels_count:
                access_levels_count[user.access_level] = 0
            access_levels_count[user.access_level] += 1
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'departments': departments_count,
            'access_levels': access_levels_count,
            'active_sessions': len(self.active_sessions),
            'last_updated': datetime.now().isoformat()
        }
    
    def add_user(self, user_data: Dict[str, Any]) -> str:
        """Add new user to the system"""
        
        user_id = f"{user_data['username']}_user_{int(time.time())}"
        
        new_user = User(
            user_id=user_id,
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data['full_name'],
            role=user_data['role'],
            department=user_data['department'],
            access_level=user_data.get('access_level', 3),
            permissions=user_data.get('permissions', []),
            created_at=datetime.now().isoformat()
        )
        
        self.users[user_id] = new_user
        self._save_users_to_file()
        
        return user_id
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user information"""
        
        if user_id in self.users:
            user = self.users[user_id]
            
            for field, value in updates.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            self._save_users_to_file()
            return True
        
        return False

def get_user_management_system():
    """Get user management system instance"""
    if not hasattr(get_user_management_system, 'instance'):
        get_user_management_system.instance = UserManagementSystem()
    return get_user_management_system.instance