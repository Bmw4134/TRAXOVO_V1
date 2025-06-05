"""
Role-Based User Management System
Comprehensive user creation with guided visual walkthrough and access control
"""

import json
import os
import time
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dataclasses import dataclass
import hashlib
import secrets

@dataclass
class UserRole:
    """Data class for user role definitions"""
    role_id: str
    role_name: str
    display_name: str
    description: str
    dashboard_access: List[str]
    module_permissions: Dict[str, str]  # module_name: permission_level
    system_privileges: List[str]
    color_scheme: str

@dataclass
class SystemUser:
    """Data class for system user"""
    user_id: str
    username: str
    email: str
    fingerprint: str
    role: UserRole
    access_scopes: List[str]
    module_visibility: Dict[str, bool]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool

class RoleBasedUserManager:
    """
    Comprehensive role-based user management system
    Handles user creation, role assignment, and access control
    """
    
    def __init__(self):
        self.db_path = "role_based_users.db"
        self.watson_sync_enabled = True
        self.predefined_roles = self._initialize_predefined_roles()
        self.system_modules = self._initialize_system_modules()
        self.dashboard_definitions = self._initialize_dashboard_definitions()
        self.initialize_database()
    
    def _initialize_predefined_roles(self) -> Dict[str, UserRole]:
        """Initialize predefined user roles with comprehensive access definitions"""
        return {
            "admin": UserRole(
                role_id="admin",
                role_name="administrator",
                display_name="System Administrator",
                description="Full system access with all privileges and module control",
                dashboard_access=[
                    "master_brain_dashboard",
                    "trillion_scale_simulation",
                    "github_dwc_sync",
                    "gauge_fleet_operations",
                    "kaizen_trd_system",
                    "bmi_intelligence_sweep",
                    "watson_command_console",
                    "failure_analysis",
                    "dashboard_customization",
                    "internal_repositories",
                    "bare_bones_inspector",
                    "role_user_management",
                    "system_monitoring",
                    "security_center"
                ],
                module_permissions={
                    "master_brain_intelligence": "full_access",
                    "trillion_scale_simulation": "full_access",
                    "github_dwc_synchronization": "full_access",
                    "gauge_api_fleet_processor": "full_access",
                    "kaizen_trd_system": "full_access",
                    "bmi_intelligence_sweep": "full_access",
                    "watson_command_console": "full_access",
                    "internal_repository_integration": "full_access",
                    "failure_analysis": "full_access",
                    "dashboard_customization": "full_access",
                    "bare_bones_inspector": "full_access",
                    "productivity_nudges": "full_access",
                    "authentic_fleet_data": "full_access"
                },
                system_privileges=[
                    "create_users",
                    "modify_roles",
                    "system_configuration",
                    "data_export",
                    "security_settings",
                    "watson_unlock",
                    "trd_override",
                    "module_activation"
                ],
                color_scheme="#ff0000"
            ),
            
            "ops": UserRole(
                role_id="ops",
                role_name="operations",
                display_name="Operations Manager",
                description="Operations dashboards with fleet management and monitoring access",
                dashboard_access=[
                    "gauge_fleet_operations",
                    "failure_analysis",
                    "dashboard_customization",
                    "master_brain_dashboard",
                    "productivity_nudges"
                ],
                module_permissions={
                    "gauge_api_fleet_processor": "full_access",
                    "authentic_fleet_data": "full_access",
                    "failure_analysis": "full_access",
                    "dashboard_customization": "full_access",
                    "master_brain_intelligence": "read_only",
                    "productivity_nudges": "full_access",
                    "github_dwc_synchronization": "read_only",
                    "trillion_scale_simulation": "read_only"
                },
                system_privileges=[
                    "fleet_management",
                    "operational_reports",
                    "dashboard_customization",
                    "data_visualization"
                ],
                color_scheme="#00ff88"
            ),
            
            "exec": UserRole(
                role_id="exec",
                role_name="executive",
                display_name="Executive User",
                description="Executive dashboards with high-level analytics and strategic insights",
                dashboard_access=[
                    "master_brain_dashboard",
                    "trillion_scale_simulation",
                    "dashboard_customization",
                    "productivity_nudges"
                ],
                module_permissions={
                    "master_brain_intelligence": "read_only",
                    "trillion_scale_simulation": "read_only",
                    "dashboard_customization": "full_access",
                    "productivity_nudges": "read_only",
                    "gauge_api_fleet_processor": "summary_only",
                    "failure_analysis": "summary_only"
                },
                system_privileges=[
                    "executive_reports",
                    "strategic_analytics",
                    "dashboard_customization",
                    "high_level_metrics"
                ],
                color_scheme="#0088ff"
            ),
            
            "viewer": UserRole(
                role_id="viewer",
                role_name="viewer",
                display_name="Data Viewer",
                description="Read-only access to select dashboards and basic data visualization",
                dashboard_access=[
                    "gauge_fleet_operations",
                    "dashboard_customization"
                ],
                module_permissions={
                    "gauge_api_fleet_processor": "read_only",
                    "authentic_fleet_data": "read_only",
                    "dashboard_customization": "limited_access",
                    "productivity_nudges": "read_only"
                },
                system_privileges=[
                    "view_dashboards",
                    "basic_reports"
                ],
                color_scheme="#888888"
            )
        }
    
    def _initialize_system_modules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize system module definitions"""
        return {
            "master_brain_intelligence": {
                "name": "Master Brain Intelligence",
                "description": "Core AI intelligence and decision-making system",
                "route": "/master-brain",
                "permission_levels": ["full_access", "read_only", "denied"]
            },
            "trillion_scale_simulation": {
                "name": "Trillion Scale Intelligence Simulation",
                "description": "Advanced simulation and predictive modeling",
                "route": "/api/trillion-simulation",
                "permission_levels": ["full_access", "read_only", "denied"]
            },
            "github_dwc_synchronization": {
                "name": "GitHub DWC Synchronization",
                "description": "Repository synchronization and version control",
                "route": "/github-sync",
                "permission_levels": ["full_access", "read_only", "denied"]
            },
            "gauge_api_fleet_processor": {
                "name": "GAUGE API Fleet Processor",
                "description": "Fleet management and asset tracking",
                "route": "/gauge-assets",
                "permission_levels": ["full_access", "read_only", "summary_only", "denied"]
            },
            "kaizen_trd_system": {
                "name": "KAIZEN TRD System",
                "description": "Total Replication Dashboard system",
                "route": "/trd",
                "permission_levels": ["full_access", "read_only", "denied"]
            },
            "bmi_intelligence_sweep": {
                "name": "BMI Intelligence Sweep",
                "description": "Business model intelligence analysis",
                "route": "/bmi/sweep",
                "permission_levels": ["full_access", "read_only", "denied"]
            },
            "watson_command_console": {
                "name": "Watson Command Console",
                "description": "AI command and control interface",
                "route": "/watson/console",
                "permission_levels": ["full_access", "denied"]
            },
            "failure_analysis": {
                "name": "Failure Analysis Dashboard",
                "description": "Equipment failure analysis and prediction",
                "route": "/failure-analysis",
                "permission_levels": ["full_access", "read_only", "summary_only", "denied"]
            },
            "dashboard_customization": {
                "name": "Dashboard Customization",
                "description": "Personalized dashboard configuration",
                "route": "/dashboard-customizer",
                "permission_levels": ["full_access", "limited_access", "denied"]
            },
            "internal_repository_integration": {
                "name": "Internal Repository Integration",
                "description": "Internal system integration and management",
                "route": "/internal-repos",
                "permission_levels": ["full_access", "read_only", "denied"]
            },
            "bare_bones_inspector": {
                "name": "Bare Bones Inspector",
                "description": "System inspection and debugging tools",
                "route": "/bare-bones-inspector",
                "permission_levels": ["full_access", "read_only", "denied"]
            },
            "productivity_nudges": {
                "name": "Productivity Nudges",
                "description": "AI-powered productivity recommendations",
                "route": "/productivity-nudges",
                "permission_levels": ["full_access", "read_only", "denied"]
            },
            "authentic_fleet_data": {
                "name": "Authentic Fleet Data",
                "description": "Real-time Fort Worth fleet operations data",
                "route": "/authentic-fleet",
                "permission_levels": ["full_access", "read_only", "summary_only", "denied"]
            }
        }
    
    def _initialize_dashboard_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize dashboard definitions with access requirements"""
        return {
            "master_brain_dashboard": {
                "name": "Master Brain Dashboard",
                "description": "Central intelligence and decision-making interface",
                "route": "/master-brain",
                "required_modules": ["master_brain_intelligence"],
                "optional_modules": ["trillion_scale_simulation", "watson_command_console"]
            },
            "trillion_scale_simulation": {
                "name": "Trillion Scale Simulation",
                "description": "Advanced predictive modeling and simulation",
                "route": "/api/trillion-simulation",
                "required_modules": ["trillion_scale_simulation"],
                "optional_modules": ["master_brain_intelligence"]
            },
            "github_dwc_sync": {
                "name": "GitHub DWC Sync",
                "description": "Repository synchronization dashboard",
                "route": "/github-sync",
                "required_modules": ["github_dwc_synchronization"],
                "optional_modules": []
            },
            "gauge_fleet_operations": {
                "name": "GAUGE Fleet Operations",
                "description": "Fleet management and monitoring dashboard",
                "route": "/gauge-assets",
                "required_modules": ["gauge_api_fleet_processor", "authentic_fleet_data"],
                "optional_modules": ["failure_analysis", "productivity_nudges"]
            },
            "kaizen_trd_system": {
                "name": "KAIZEN TRD System",
                "description": "Total Replication Dashboard interface",
                "route": "/trd",
                "required_modules": ["kaizen_trd_system"],
                "optional_modules": ["bmi_intelligence_sweep"]
            },
            "bmi_intelligence_sweep": {
                "name": "BMI Intelligence Sweep",
                "description": "Business model intelligence dashboard",
                "route": "/bmi/sweep",
                "required_modules": ["bmi_intelligence_sweep"],
                "optional_modules": ["master_brain_intelligence"]
            },
            "watson_command_console": {
                "name": "Watson Command Console",
                "description": "AI command and control center",
                "route": "/watson/console",
                "required_modules": ["watson_command_console"],
                "optional_modules": ["master_brain_intelligence", "kaizen_trd_system"]
            },
            "failure_analysis": {
                "name": "Failure Analysis Dashboard",
                "description": "Equipment failure analysis and prediction",
                "route": "/failure-analysis",
                "required_modules": ["failure_analysis"],
                "optional_modules": ["gauge_api_fleet_processor", "authentic_fleet_data"]
            },
            "dashboard_customization": {
                "name": "Dashboard Customization",
                "description": "Personalized dashboard configuration",
                "route": "/dashboard-customizer",
                "required_modules": ["dashboard_customization"],
                "optional_modules": []
            },
            "internal_repositories": {
                "name": "Internal Repositories",
                "description": "Internal system integration dashboard",
                "route": "/internal-repos",
                "required_modules": ["internal_repository_integration"],
                "optional_modules": ["github_dwc_synchronization"]
            },
            "bare_bones_inspector": {
                "name": "Bare Bones Inspector",
                "description": "System inspection and debugging interface",
                "route": "/bare-bones-inspector",
                "required_modules": ["bare_bones_inspector"],
                "optional_modules": []
            },
            "role_user_management": {
                "name": "Role & User Management",
                "description": "User and role administration dashboard",
                "route": "/role-management",
                "required_modules": [],
                "optional_modules": []
            }
        }
    
    def initialize_database(self):
        """Initialize user management database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                fingerprint TEXT UNIQUE NOT NULL,
                role_id TEXT NOT NULL,
                access_scopes TEXT NOT NULL,
                module_visibility TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (role_id) REFERENCES roles (role_id)
            )
        ''')
        
        # Roles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                role_id TEXT PRIMARY KEY,
                role_name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT NOT NULL,
                dashboard_access TEXT NOT NULL,
                module_permissions TEXT NOT NULL,
                system_privileges TEXT NOT NULL,
                color_scheme TEXT NOT NULL
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                login_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Access audit table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_audit (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                resource_accessed TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN NOT NULL,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize predefined roles in database
        self._store_predefined_roles()
    
    def _store_predefined_roles(self):
        """Store predefined roles in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for role_id, role in self.predefined_roles.items():
            cursor.execute('''
                INSERT OR REPLACE INTO roles 
                (role_id, role_name, display_name, description, dashboard_access, 
                 module_permissions, system_privileges, color_scheme)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                role.role_id,
                role.role_name,
                role.display_name,
                role.description,
                json.dumps(role.dashboard_access),
                json.dumps(role.module_permissions),
                json.dumps(role.system_privileges),
                role.color_scheme
            ))
        
        conn.commit()
        conn.close()
    
    def generate_user_fingerprint(self, username: str, email: str) -> str:
        """Generate unique user fingerprint"""
        fingerprint_data = f"{username}_{email}_{secrets.token_hex(8)}_{int(time.time())}"
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
        return fingerprint.upper()
    
    def create_user(self, username: str, email: str, role_id: str, 
                   custom_access_scopes: List[str] = None,
                   custom_module_visibility: Dict[str, bool] = None) -> Dict[str, Any]:
        """Create new user with role-based access"""
        
        try:
            # Validate role exists
            if role_id not in self.predefined_roles:
                return {
                    "success": False,
                    "error": f"Invalid role: {role_id}",
                    "available_roles": list(self.predefined_roles.keys())
                }
            
            role = self.predefined_roles[role_id]
            
            # Generate user ID and fingerprint
            user_id = f"user_{int(time.time())}_{secrets.token_hex(4)}"
            fingerprint = self.generate_user_fingerprint(username, email)
            
            # Set access scopes (custom or role default)
            access_scopes = custom_access_scopes or role.dashboard_access
            
            # Set module visibility (custom or role default)
            if custom_module_visibility is None:
                module_visibility = {
                    module: permission != "denied" 
                    for module, permission in role.module_permissions.items()
                }
            else:
                module_visibility = custom_module_visibility
            
            # Create user object
            user = SystemUser(
                user_id=user_id,
                username=username,
                email=email,
                fingerprint=fingerprint,
                role=role,
                access_scopes=access_scopes,
                module_visibility=module_visibility,
                created_at=datetime.now(),
                last_login=None,
                is_active=True
            )
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, email, fingerprint, role_id, access_scopes, 
                 module_visibility, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.user_id,
                user.username,
                user.email,
                user.fingerprint,
                user.role.role_id,
                json.dumps(user.access_scopes),
                json.dumps(user.module_visibility),
                user.created_at.isoformat(),
                user.is_active
            ))
            
            conn.commit()
            conn.close()
            
            # Sync with Watson core memory ring if enabled
            if self.watson_sync_enabled:
                self._sync_user_to_watson_core(user)
            
            return {
                "success": True,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "fingerprint": user.fingerprint,
                    "role": {
                        "role_id": user.role.role_id,
                        "display_name": user.role.display_name,
                        "description": user.role.description,
                        "color_scheme": user.role.color_scheme
                    },
                    "access_scopes": user.access_scopes,
                    "module_visibility": user.module_visibility,
                    "created_at": user.created_at.isoformat()
                },
                "dashboard_access": self._generate_dashboard_access_preview(user),
                "module_permissions": self._generate_module_permissions_preview(user)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create user: {str(e)}"
            }
    
    def _sync_user_to_watson_core(self, user: SystemUser):
        """Sync user to Watson core memory ring"""
        try:
            # Import Watson bootstrap if available
            from permissions_bootstrap import watson_bootstrap
            
            user_data = {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "fingerprint": user.fingerprint,
                "role_id": user.role.role_id,
                "access_scopes": user.access_scopes,
                "module_visibility": user.module_visibility,
                "system_privileges": user.role.system_privileges
            }
            
            # Add to Watson intelligence core
            watson_bootstrap.watson_intelligence_core[f"user_{user.user_id}"] = user_data
            
        except ImportError:
            # Watson bootstrap not available, skip sync
            pass
    
    def _generate_dashboard_access_preview(self, user: SystemUser) -> Dict[str, Any]:
        """Generate dashboard access preview for user"""
        dashboard_preview = {}
        
        for dashboard_id in user.access_scopes:
            if dashboard_id in self.dashboard_definitions:
                dashboard = self.dashboard_definitions[dashboard_id]
                
                # Check if user has access to required modules
                has_required_access = all(
                    user.module_visibility.get(module, False) and 
                    user.role.module_permissions.get(module, "denied") != "denied"
                    for module in dashboard["required_modules"]
                )
                
                dashboard_preview[dashboard_id] = {
                    "name": dashboard["name"],
                    "description": dashboard["description"],
                    "route": dashboard["route"],
                    "access_granted": has_required_access,
                    "required_modules": dashboard["required_modules"],
                    "permission_level": "full" if has_required_access else "restricted"
                }
        
        return dashboard_preview
    
    def _generate_module_permissions_preview(self, user: SystemUser) -> Dict[str, Any]:
        """Generate module permissions preview for user"""
        module_preview = {}
        
        for module_id, visible in user.module_visibility.items():
            if module_id in self.system_modules and visible:
                module = self.system_modules[module_id]
                permission_level = user.role.module_permissions.get(module_id, "denied")
                
                module_preview[module_id] = {
                    "name": module["name"],
                    "description": module["description"],
                    "route": module["route"],
                    "permission_level": permission_level,
                    "visible": visible,
                    "available_actions": self._get_module_actions(module_id, permission_level)
                }
        
        return module_preview
    
    def _get_module_actions(self, module_id: str, permission_level: str) -> List[str]:
        """Get available actions for module based on permission level"""
        actions_map = {
            "full_access": ["view", "create", "edit", "delete", "export", "configure"],
            "read_only": ["view", "export"],
            "summary_only": ["view_summary"],
            "limited_access": ["view", "limited_edit"],
            "denied": []
        }
        
        return actions_map.get(permission_level, [])
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users with their roles and permissions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.*, r.display_name, r.description, r.color_scheme
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.role_id
            ORDER BY u.created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                "user_id": row[0],
                "username": row[1],
                "email": row[2],
                "fingerprint": row[3],
                "role_id": row[4],
                "role_display_name": row[10],
                "role_description": row[11],
                "role_color": row[12],
                "access_scopes": json.loads(row[5]),
                "module_visibility": json.loads(row[6]),
                "created_at": row[7],
                "last_login": row[8],
                "is_active": bool(row[9])
            })
        
        conn.close()
        return users
    
    def get_user_summary_table(self) -> Dict[str, Any]:
        """Generate comprehensive user summary table"""
        users = self.get_all_users()
        
        summary = {
            "total_users": len(users),
            "users_by_role": {},
            "dashboard_access_summary": {},
            "module_permissions_summary": {},
            "user_table": []
        }
        
        # Count users by role
        for user in users:
            role_id = user["role_id"]
            summary["users_by_role"][role_id] = summary["users_by_role"].get(role_id, 0) + 1
        
        # Generate detailed user table
        for user in users:
            accessible_dashboards = len(user["access_scopes"])
            visible_modules = sum(1 for visible in user["module_visibility"].values() if visible)
            
            summary["user_table"].append({
                "username": user["username"],
                "email": user["email"],
                "role": user["role_display_name"],
                "role_color": user["role_color"],
                "fingerprint": user["fingerprint"],
                "dashboards_accessible": accessible_dashboards,
                "modules_visible": visible_modules,
                "created_at": user["created_at"],
                "status": "Active" if user["is_active"] else "Inactive"
            })
        
        return summary


# Global user manager instance
user_manager = RoleBasedUserManager()

def create_user_management_routes(app):
    """Add user management routes to Flask app"""
    
    @app.route('/role-management')
    def role_management_interface():
        """Main role and user management interface"""
        return render_template_string(ROLE_MANAGEMENT_TEMPLATE)
    
    @app.route('/api/roles')
    def get_available_roles():
        """Get all available roles"""
        roles = []
        for role_id, role in user_manager.predefined_roles.items():
            roles.append({
                "role_id": role.role_id,
                "role_name": role.role_name,
                "display_name": role.display_name,
                "description": role.description,
                "color_scheme": role.color_scheme,
                "dashboard_count": len(role.dashboard_access),
                "module_count": len([p for p in role.module_permissions.values() if p != "denied"])
            })
        return jsonify({"roles": roles})
    
    @app.route('/api/users/create', methods=['POST'])
    def create_new_user():
        """Create a new user"""
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        role_id = data.get('role_id')
        custom_access_scopes = data.get('custom_access_scopes')
        custom_module_visibility = data.get('custom_module_visibility')
        
        if not all([username, email, role_id]):
            return jsonify({
                "success": False,
                "error": "Username, email, and role_id are required"
            }), 400
        
        result = user_manager.create_user(
            username=username,
            email=email,
            role_id=role_id,
            custom_access_scopes=custom_access_scopes,
            custom_module_visibility=custom_module_visibility
        )
        
        return jsonify(result)
    
    @app.route('/api/users')
    def get_all_users():
        """Get all users"""
        users = user_manager.get_all_users()
        return jsonify({"users": users})
    
    @app.route('/api/users/summary')
    def get_user_summary():
        """Get user summary table"""
        summary = user_manager.get_user_summary_table()
        return jsonify(summary)
    
    @app.route('/api/system/modules')
    def get_system_modules():
        """Get all system modules"""
        return jsonify({"modules": user_manager.system_modules})
    
    @app.route('/api/system/dashboards')
    def get_system_dashboards():
        """Get all system dashboards"""
        return jsonify({"dashboards": user_manager.dashboard_definitions})
    
    @app.route('/guided-user-creation')
    def guided_user_creation():
        """Guided user creation walkthrough"""
        return render_template_string(GUIDED_USER_CREATION_TEMPLATE)


# Template for role management interface
ROLE_MANAGEMENT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Role & User Management - TRAXOVO</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #000000, #1a1a2e);
            color: #ffffff;
            padding: 20px;
            line-height: 1.6;
        }
        .management-container {
            max-width: 1600px;
            margin: 0 auto;
            background: rgba(0,0,0,0.8);
            border: 2px solid #00ff88;
            border-radius: 15px;
            padding: 30px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0,255,136,0.1);
            border-radius: 10px;
        }
        .action-buttons {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            justify-content: center;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
        }
        .btn-primary { background: #00ff88; color: #000; }
        .btn-secondary { background: #0088ff; color: #fff; }
        .btn-danger { background: #ff4444; color: #fff; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
        
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        .content-section {
            background: rgba(0,0,0,0.6);
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
        }
        .section-title {
            color: #00ff88;
            border-bottom: 2px solid #00ff88;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .users-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .users-table th,
        .users-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }
        .users-table th {
            background: rgba(0,255,136,0.2);
            color: #00ff88;
        }
        .role-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .status-active { color: #00ff88; }
        .status-inactive { color: #ff4444; }
        
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: rgba(0,255,136,0.1);
            border: 1px solid #00ff88;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #00ff88;
        }
        .stat-label {
            font-size: 0.9em;
            color: #ccc;
        }
    </style>
</head>
<body>
    <div class="management-container">
        <div class="header">
            <h1>🎭 Role & User Management</h1>
            <h2>TRAXOVO User Administration Center</h2>
            <p>Comprehensive role-based access control and user management</p>
        </div>
        
        <div class="action-buttons">
            <a href="/guided-user-creation" class="btn btn-primary">👤 Guided User Creation</a>
            <button onclick="refreshUserData()" class="btn btn-secondary">🔄 Refresh Data</button>
            <button onclick="exportUserSummary()" class="btn btn-secondary">📊 Export Summary</button>
        </div>
        
        <div id="summaryStats" class="summary-stats">
            <!-- Summary stats will be loaded here -->
        </div>
        
        <div class="content-grid">
            <div class="content-section">
                <h3 class="section-title">Available Roles</h3>
                <div id="rolesContainer">
                    <!-- Roles will be loaded here -->
                </div>
            </div>
            
            <div class="content-section">
                <h3 class="section-title">System Modules</h3>
                <div id="modulesContainer">
                    <!-- Modules will be loaded here -->
                </div>
            </div>
        </div>
        
        <div class="content-section">
            <h3 class="section-title">User Management Table</h3>
            <div id="usersTableContainer">
                <!-- Users table will be loaded here -->
            </div>
        </div>
    </div>
    
    <script>
        async function loadRoles() {
            try {
                const response = await fetch('/api/roles');
                const data = await response.json();
                
                const container = document.getElementById('rolesContainer');
                container.innerHTML = data.roles.map(role => `
                    <div style="background: rgba(0,0,0,0.8); border: 1px solid ${role.color_scheme}; border-radius: 8px; padding: 15px; margin-bottom: 10px;">
                        <h4 style="color: ${role.color_scheme};">${role.display_name}</h4>
                        <p style="font-size: 0.9em; color: #ccc;">${role.description}</p>
                        <div style="margin-top: 10px; font-size: 0.8em;">
                            <span style="color: #00ff88;">Dashboards: ${role.dashboard_count}</span> | 
                            <span style="color: #0088ff;">Modules: ${role.module_count}</span>
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading roles:', error);
            }
        }
        
        async function loadModules() {
            try {
                const response = await fetch('/api/system/modules');
                const data = await response.json();
                
                const container = document.getElementById('modulesContainer');
                container.innerHTML = Object.values(data.modules).map(module => `
                    <div style="background: rgba(0,0,0,0.8); border: 1px solid #00ff88; border-radius: 8px; padding: 10px; margin-bottom: 8px;">
                        <h5 style="color: #00ff88;">${module.name}</h5>
                        <p style="font-size: 0.8em; color: #ccc;">${module.description}</p>
                        <span style="font-size: 0.7em; color: #888;">${module.route}</span>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading modules:', error);
            }
        }
        
        async function loadUserSummary() {
            try {
                const response = await fetch('/api/users/summary');
                const data = await response.json();
                
                // Load summary stats
                const statsContainer = document.getElementById('summaryStats');
                statsContainer.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-number">${data.total_users}</div>
                        <div class="stat-label">Total Users</div>
                    </div>
                    ${Object.entries(data.users_by_role).map(([role, count]) => `
                        <div class="stat-card">
                            <div class="stat-number">${count}</div>
                            <div class="stat-label">${role.toUpperCase()} Users</div>
                        </div>
                    `).join('')}
                `;
                
                // Load users table
                const tableContainer = document.getElementById('usersTableContainer');
                tableContainer.innerHTML = `
                    <table class="users-table">
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Fingerprint</th>
                                <th>Dashboards</th>
                                <th>Modules</th>
                                <th>Status</th>
                                <th>Created</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.user_table.map(user => `
                                <tr>
                                    <td>${user.username}</td>
                                    <td>${user.email}</td>
                                    <td><span class="role-badge" style="background-color: ${user.role_color}; color: #000;">${user.role}</span></td>
                                    <td style="font-family: monospace; font-size: 0.8em;">${user.fingerprint}</td>
                                    <td>${user.dashboards_accessible}</td>
                                    <td>${user.modules_visible}</td>
                                    <td class="${user.status === 'Active' ? 'status-active' : 'status-inactive'}">${user.status}</td>
                                    <td style="font-size: 0.8em;">${new Date(user.created_at).toLocaleDateString()}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
                
            } catch (error) {
                console.error('Error loading user summary:', error);
            }
        }
        
        async function refreshUserData() {
            await Promise.all([loadRoles(), loadModules(), loadUserSummary()]);
        }
        
        async function exportUserSummary() {
            try {
                const response = await fetch('/api/users/summary');
                const data = await response.json();
                
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `traxovo_user_summary_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (error) {
                console.error('Error exporting user summary:', error);
            }
        }
        
        // Load initial data
        document.addEventListener('DOMContentLoaded', refreshUserData);
    </script>
</body>
</html>
'''

# Template for guided user creation
GUIDED_USER_CREATION_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Guided User Creation - TRAXOVO</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #000000, #1a1a2e);
            color: #ffffff;
            padding: 20px;
            line-height: 1.6;
        }
        .creation-container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(0,0,0,0.8);
            border: 2px solid #00ff88;
            border-radius: 15px;
            padding: 30px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0,255,136,0.1);
            border-radius: 10px;
        }
        .step-indicator {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }
        .step {
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 20px;
            background: rgba(255,255,255,0.1);
            border: 1px solid #333;
        }
        .step.active {
            background: #00ff88;
            color: #000;
            font-weight: bold;
        }
        .step.completed {
            background: #0088ff;
            color: #fff;
        }
        
        .form-section {
            background: rgba(0,0,0,0.6);
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #00ff88;
            font-weight: bold;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #333;
            border-radius: 5px;
            background: rgba(0,0,0,0.8);
            color: #fff;
        }
        .form-group input:focus,
        .form-group select:focus {
            border-color: #00ff88;
            outline: none;
        }
        
        .role-preview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .role-card {
            border: 2px solid #333;
            border-radius: 10px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .role-card:hover {
            border-color: #00ff88;
            transform: translateY(-2px);
        }
        .role-card.selected {
            border-color: #00ff88;
            background: rgba(0,255,136,0.1);
        }
        
        .access-preview {
            background: rgba(0,0,0,0.8);
            border: 1px solid #00ff88;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            margin: 5px;
            transition: all 0.3s ease;
        }
        .btn-primary { background: #00ff88; color: #000; }
        .btn-secondary { background: #0088ff; color: #fff; }
        .btn-success { background: #28a745; color: #fff; }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { 
            opacity: 0.5; 
            cursor: not-allowed; 
            transform: none; 
        }
        
        .creation-result {
            background: rgba(0,255,136,0.1);
            border: 2px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="creation-container">
        <div class="header">
            <h1>👤 Guided User Creation</h1>
            <h2>TRAXOVO User Setup Walkthrough</h2>
            <p>Step-by-step user creation with role assignment and access preview</p>
        </div>
        
        <div class="step-indicator">
            <div class="step active" id="step1">Step 1: Basic Info</div>
            <div class="step" id="step2">Step 2: Role Selection</div>
            <div class="step" id="step3">Step 3: Access Preview</div>
            <div class="step" id="step4">Step 4: Confirmation</div>
        </div>
        
        <form id="userCreationForm">
            <!-- Step 1: Basic Information -->
            <div id="section1" class="form-section">
                <h3>Basic User Information</h3>
                <div class="form-group">
                    <label for="username">Username *</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="email">Email Address *</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <button type="button" class="btn btn-primary" onclick="nextStep(1)">Next: Role Selection</button>
            </div>
            
            <!-- Step 2: Role Selection -->
            <div id="section2" class="form-section" style="display: none;">
                <h3>Role Selection</h3>
                <p>Select the appropriate role for this user:</p>
                <div id="roleOptions" class="role-preview">
                    <!-- Role options will be loaded here -->
                </div>
                <input type="hidden" id="selectedRole" name="role_id">
                <div style="margin-top: 20px;">
                    <button type="button" class="btn btn-secondary" onclick="previousStep(2)">Previous</button>
                    <button type="button" class="btn btn-primary" onclick="nextStep(2)" id="roleNextBtn" disabled>Next: Access Preview</button>
                </div>
            </div>
            
            <!-- Step 3: Access Preview -->
            <div id="section3" class="form-section" style="display: none;">
                <h3>Access Preview</h3>
                <div id="accessPreview">
                    <!-- Access preview will be loaded here -->
                </div>
                <div style="margin-top: 20px;">
                    <button type="button" class="btn btn-secondary" onclick="previousStep(3)">Previous</button>
                    <button type="button" class="btn btn-primary" onclick="nextStep(3)">Next: Confirmation</button>
                </div>
            </div>
            
            <!-- Step 4: Confirmation -->
            <div id="section4" class="form-section" style="display: none;">
                <h3>Confirmation</h3>
                <div id="confirmationPreview">
                    <!-- Confirmation details will be loaded here -->
                </div>
                <div style="margin-top: 20px;">
                    <button type="button" class="btn btn-secondary" onclick="previousStep(4)">Previous</button>
                    <button type="button" class="btn btn-success" onclick="createUser()">Create User</button>
                </div>
            </div>
        </form>
        
        <div id="creationResult" class="creation-result" style="display: none;">
            <!-- Creation result will be shown here -->
        </div>
    </div>
    
    <script>
        let currentStep = 1;
        let availableRoles = [];
        let selectedRoleData = null;
        
        async function loadRoles() {
            try {
                const response = await fetch('/api/roles');
                const data = await response.json();
                availableRoles = data.roles;
                
                const container = document.getElementById('roleOptions');
                container.innerHTML = availableRoles.map(role => `
                    <div class="role-card" onclick="selectRole('${role.role_id}')">
                        <h4 style="color: ${role.color_scheme};">${role.display_name}</h4>
                        <p style="margin: 10px 0; color: #ccc;">${role.description}</p>
                        <div style="font-size: 0.8em;">
                            <span style="color: #00ff88;">📊 ${role.dashboard_count} Dashboards</span><br>
                            <span style="color: #0088ff;">🔧 ${role.module_count} Modules</span>
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading roles:', error);
            }
        }
        
        function selectRole(roleId) {
            // Remove previous selection
            document.querySelectorAll('.role-card').forEach(card => {
                card.classList.remove('selected');
            });
            
            // Add selection to clicked card
            event.target.closest('.role-card').classList.add('selected');
            
            // Store selected role
            document.getElementById('selectedRole').value = roleId;
            selectedRoleData = availableRoles.find(role => role.role_id === roleId);
            
            // Enable next button
            document.getElementById('roleNextBtn').disabled = false;
        }
        
        function nextStep(step) {
            if (step === 1) {
                const username = document.getElementById('username').value;
                const email = document.getElementById('email').value;
                
                if (!username || !email) {
                    alert('Please fill in all required fields');
                    return;
                }
            }
            
            if (step === 2) {
                if (!selectedRoleData) {
                    alert('Please select a role');
                    return;
                }
                loadAccessPreview();
            }
            
            if (step === 3) {
                loadConfirmationPreview();
            }
            
            // Hide current section
            document.getElementById(`section${step}`).style.display = 'none';
            document.getElementById(`step${step}`).classList.remove('active');
            document.getElementById(`step${step}`).classList.add('completed');
            
            // Show next section
            currentStep = step + 1;
            document.getElementById(`section${currentStep}`).style.display = 'block';
            document.getElementById(`step${currentStep}`).classList.add('active');
        }
        
        function previousStep(step) {
            // Hide current section
            document.getElementById(`section${step}`).style.display = 'none';
            document.getElementById(`step${step}`).classList.remove('active');
            
            // Show previous section
            currentStep = step - 1;
            document.getElementById(`section${currentStep}`).style.display = 'block';
            document.getElementById(`step${currentStep}`).classList.remove('completed');
            document.getElementById(`step${currentStep}`).classList.add('active');
        }
        
        function loadAccessPreview() {
            if (!selectedRoleData) return;
            
            const container = document.getElementById('accessPreview');
            container.innerHTML = `
                <h4>Dashboard Access for ${selectedRoleData.display_name}</h4>
                <div class="access-preview">
                    <h5>Accessible Dashboards (${selectedRoleData.dashboard_count})</h5>
                    <ul style="list-style: none; padding: 0;">
                        ${selectedRoleData.dashboard_count > 0 ? 
                            '• Master Brain Dashboard<br>• Fleet Operations<br>• Dashboard Customization<br>• And more...' :
                            'No dashboard access'
                        }
                    </ul>
                </div>
                
                <div class="access-preview">
                    <h5>Module Permissions (${selectedRoleData.module_count})</h5>
                    <ul style="list-style: none; padding: 0;">
                        ${selectedRoleData.module_count > 0 ? 
                            '• Fleet Data: Full Access<br>• Analytics: Read Only<br>• Configuration: Limited<br>• And more...' :
                            'No module access'
                        }
                    </ul>
                </div>
            `;
        }
        
        function loadConfirmationPreview() {
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            
            const container = document.getElementById('confirmationPreview');
            container.innerHTML = `
                <h4>User Creation Summary</h4>
                <div class="access-preview">
                    <p><strong>Username:</strong> ${username}</p>
                    <p><strong>Email:</strong> ${email}</p>
                    <p><strong>Role:</strong> <span style="color: ${selectedRoleData.color_scheme};">${selectedRoleData.display_name}</span></p>
                    <p><strong>Description:</strong> ${selectedRoleData.description}</p>
                </div>
                
                <div class="access-preview">
                    <h5>What happens when you create this user:</h5>
                    <ul style="padding-left: 20px;">
                        <li>Unique user fingerprint will be generated</li>
                        <li>Role-based dashboard access will be configured</li>
                        <li>Module permissions will be assigned</li>
                        <li>User will be synced to Watson core memory ring</li>
                        <li>Access audit trail will be initialized</li>
                    </ul>
                </div>
            `;
        }
        
        async function createUser() {
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const roleId = document.getElementById('selectedRole').value;
            
            try {
                const response = await fetch('/api/users/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: username,
                        email: email,
                        role_id: roleId
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Hide form sections
                    document.querySelectorAll('.form-section').forEach(section => {
                        section.style.display = 'none';
                    });
                    
                    // Show success result
                    const resultContainer = document.getElementById('creationResult');
                    resultContainer.innerHTML = `
                        <h3 style="color: #00ff88;">✓ User Created Successfully!</h3>
                        
                        <div style="background: rgba(0,0,0,0.8); padding: 15px; border-radius: 8px; margin: 15px 0;">
                            <h4>User Details:</h4>
                            <p><strong>Username:</strong> ${result.user.username}</p>
                            <p><strong>Email:</strong> ${result.user.email}</p>
                            <p><strong>User ID:</strong> ${result.user.user_id}</p>
                            <p><strong>Fingerprint:</strong> <code style="background: rgba(0,255,136,0.2); padding: 2px 4px; border-radius: 3px;">${result.user.fingerprint}</code></p>
                            <p><strong>Role:</strong> <span style="color: ${result.user.role.color_scheme};">${result.user.role.display_name}</span></p>
                        </div>
                        
                        <div style="background: rgba(0,0,0,0.8); padding: 15px; border-radius: 8px; margin: 15px 0;">
                            <h4>Access Summary:</h4>
                            <p><strong>Dashboard Access:</strong> ${result.user.access_scopes.length} dashboards</p>
                            <p><strong>Module Visibility:</strong> ${Object.values(result.user.module_visibility).filter(v => v).length} modules visible</p>
                        </div>
                        
                        <div style="margin-top: 20px;">
                            <button class="btn btn-primary" onclick="window.location.href='/role-management'">Return to Management</button>
                            <button class="btn btn-secondary" onclick="location.reload()">Create Another User</button>
                        </div>
                    `;
                    resultContainer.style.display = 'block';
                    
                    // Update step indicator
                    document.getElementById('step4').classList.remove('active');
                    document.getElementById('step4').classList.add('completed');
                    
                } else {
                    alert(`Error creating user: ${result.error}`);
                }
                
            } catch (error) {
                alert(`Error creating user: ${error.message}`);
            }
        }
        
        // Load initial data
        document.addEventListener('DOMContentLoaded', loadRoles);
    </script>
</body>
</html>
'''

def render_template_string(template_string):
    """Simple template renderer"""
    return template_string


if __name__ == "__main__":
    # Test user creation
    print("Testing role-based user management system...")
    
    # Create test users
    test_users = [
        {"username": "admin_user", "email": "admin@traxovo.com", "role_id": "admin"},
        {"username": "ops_manager", "email": "ops@traxovo.com", "role_id": "ops"},
        {"username": "exec_viewer", "email": "exec@traxovo.com", "role_id": "exec"},
        {"username": "data_viewer", "email": "viewer@traxovo.com", "role_id": "viewer"}
    ]
    
    for test_user in test_users:
        result = user_manager.create_user(**test_user)
        print(f"Created user {test_user['username']}: {result['success']}")
        if result['success']:
            print(f"  Fingerprint: {result['user']['fingerprint']}")
    
    # Print user summary
    summary = user_manager.get_user_summary_table()
    print(f"\nUser Summary: {summary['total_users']} total users")
    for user in summary['user_table']:
        print(f"  {user['username']} ({user['role']}) - {user['dashboards_accessible']} dashboards, {user['modules_visible']} modules")