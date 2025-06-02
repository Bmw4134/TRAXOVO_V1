"""
Unified Navigation System
Role-based seamless navigation across the entire TRAXOVO platform
"""

from typing import Dict, List, Any, Optional
from secure_enterprise_auth import get_secure_auth

class UnifiedNavigationSystem:
    """
    Intelligent navigation system that adapts to user roles and permissions
    """
    
    def __init__(self):
        self.auth_system = get_secure_auth()
        self.navigation_config = self._initialize_navigation_structure()
    
    def _initialize_navigation_structure(self) -> Dict[str, Any]:
        """Initialize complete navigation structure for all user types"""
        return {
            "SYSTEM_ADMIN": {
                "primary_modules": [
                    {"name": "Dashboard", "route": "/dashboard", "icon": "🏠", "description": "Main intelligence dashboard"},
                    {"name": "Quantum ASI", "route": "/quantum_asi_excellence", "icon": "🧠", "description": "ASI excellence system"},
                    {"name": "Security Audit", "route": "/board_security_audit", "icon": "🔒", "description": "Board-level security monitoring"},
                    {"name": "Analytics Engine", "route": "/agi_analytics", "icon": "📊", "description": "AGI-powered business intelligence"},
                    {"name": "Email Intelligence", "route": "/watson_email_intelligence", "icon": "📧", "description": "Microsoft 365 communication analysis"},
                    {"name": "Dream Alignment", "route": "/watson_dream_alignment", "icon": "🎯", "description": "Goal tracking and achievement"},
                    {"name": "Report Importer", "route": "/automated_reports", "icon": "📄", "description": "Automated report processing"},
                    {"name": "User Management", "route": "/enterprise_users", "icon": "👥", "description": "Enterprise user administration"},
                    {"name": "Asset Lifecycle", "route": "/agi_asset_lifecycle", "icon": "🚛", "description": "AGI asset optimization"}
                ],
                "admin_tools": [
                    {"name": "System Settings", "route": "/admin/settings", "icon": "⚙️"},
                    {"name": "API Management", "route": "/admin/api_keys", "icon": "🔑"},
                    {"name": "Backup Systems", "route": "/admin/backup", "icon": "💾"},
                    {"name": "Performance Monitor", "route": "/technical_testing", "icon": "⚡"}
                ]
            },
            
            "VICE_PRESIDENT": {
                "primary_modules": [
                    {"name": "Executive Dashboard", "route": "/dashboard", "icon": "🏠", "description": "Strategic overview"},
                    {"name": "Financial Analytics", "route": "/agi_analytics", "icon": "💰", "description": "Revenue and cost analysis"},
                    {"name": "Security Status", "route": "/board_security_audit", "icon": "🔒", "description": "Security compliance"},
                    {"name": "Asset Portfolio", "route": "/agi_asset_lifecycle", "icon": "🚛", "description": "Fleet optimization"},
                    {"name": "Strategic Reports", "route": "/automated_reports", "icon": "📊", "description": "Executive reporting"},
                    {"name": "Team Analytics", "route": "/enterprise_users", "icon": "👥", "description": "Organizational insights"},
                    {"name": "Goal Tracking", "route": "/watson_dream_alignment", "icon": "🎯", "description": "Strategic objectives"}
                ],
                "executive_tools": [
                    {"name": "Board Reports", "route": "/executive/board_reports", "icon": "📋"},
                    {"name": "Compliance Dashboard", "route": "/executive/compliance", "icon": "✅"},
                    {"name": "Strategic Planning", "route": "/executive/planning", "icon": "🗺️"}
                ]
            },
            
            "OPERATIONS_MANAGER": {
                "primary_modules": [
                    {"name": "Operations Dashboard", "route": "/dashboard", "icon": "🏠", "description": "Daily operations overview"},
                    {"name": "Fleet Management", "route": "/agi_asset_lifecycle", "icon": "🚛", "description": "Equipment tracking"},
                    {"name": "Team Management", "route": "/enterprise_users", "icon": "👥", "description": "Staff coordination"},
                    {"name": "Analytics", "route": "/agi_analytics", "icon": "📊", "description": "Operational metrics"},
                    {"name": "Reports", "route": "/automated_reports", "icon": "📄", "description": "Daily reporting"},
                    {"name": "Goals", "route": "/watson_dream_alignment", "icon": "🎯", "description": "Team objectives"}
                ],
                "management_tools": [
                    {"name": "Staff Scheduling", "route": "/operations/scheduling", "icon": "📅"},
                    {"name": "Equipment Status", "route": "/operations/equipment", "icon": "🔧"},
                    {"name": "Performance Reports", "route": "/operations/performance", "icon": "📈"}
                ]
            },
            
            "EQUIPMENT_LEAD": {
                "primary_modules": [
                    {"name": "Equipment Dashboard", "route": "/dashboard", "icon": "🏠", "description": "Fleet overview"},
                    {"name": "Asset Management", "route": "/agi_asset_lifecycle", "icon": "🚛", "description": "Equipment lifecycle"},
                    {"name": "Maintenance Analytics", "route": "/agi_analytics", "icon": "🔧", "description": "Maintenance insights"},
                    {"name": "Equipment Reports", "route": "/automated_reports", "icon": "📄", "description": "Fleet reporting"},
                    {"name": "Team Goals", "route": "/watson_dream_alignment", "icon": "🎯", "description": "Equipment objectives"}
                ],
                "equipment_tools": [
                    {"name": "Maintenance Schedule", "route": "/equipment/maintenance", "icon": "🛠️"},
                    {"name": "Asset Tracker", "route": "/equipment/tracking", "icon": "📍"},
                    {"name": "Utilization Reports", "route": "/equipment/utilization", "icon": "⏱️"}
                ]
            },
            
            "OPERATOR": {
                "primary_modules": [
                    {"name": "My Dashboard", "route": "/dashboard", "icon": "🏠", "description": "Personal workspace"},
                    {"name": "My Tasks", "route": "/watson_dream_alignment", "icon": "✅", "description": "Daily objectives"},
                    {"name": "Equipment Status", "route": "/agi_asset_lifecycle", "icon": "🚛", "description": "Equipment info"},
                    {"name": "Reports", "route": "/automated_reports", "icon": "📄", "description": "View reports"}
                ],
                "operator_tools": [
                    {"name": "Time Tracking", "route": "/operator/time", "icon": "⏰"},
                    {"name": "Equipment Check", "route": "/operator/equipment", "icon": "✔️"},
                    {"name": "Issue Reporting", "route": "/operator/issues", "icon": "⚠️"}
                ]
            }
        }
    
    def get_navigation_for_user(self, username: str) -> Dict[str, Any]:
        """Get complete navigation structure for a specific user"""
        config = self.auth_system.get_user_dashboard_config(username)
        
        if not config:
            return self._get_guest_navigation()
        
        user_role = config.get("user_info", {}).get("role", "OPERATOR")
        nav_config = self.navigation_config.get(user_role, self.navigation_config["OPERATOR"])
        
        return {
            "user_info": config.get("user_info", {}),
            "primary_navigation": nav_config.get("primary_modules", []),
            "tools_navigation": self._get_tools_for_role(user_role, nav_config),
            "quick_access": self._get_quick_access_items(user_role),
            "breadcrumbs": self._generate_breadcrumbs(),
            "search_enabled": True,
            "notification_center": True,
            "theme": "professional"
        }
    
    def _get_tools_for_role(self, role: str, nav_config: Dict) -> List[Dict]:
        """Get role-specific tools navigation"""
        if role == "SYSTEM_ADMIN":
            return nav_config.get("admin_tools", [])
        elif role == "VICE_PRESIDENT":
            return nav_config.get("executive_tools", [])
        elif role == "OPERATIONS_MANAGER":
            return nav_config.get("management_tools", [])
        elif role == "EQUIPMENT_LEAD":
            return nav_config.get("equipment_tools", [])
        else:
            return nav_config.get("operator_tools", [])
    
    def _get_quick_access_items(self, role: str) -> List[Dict]:
        """Get quick access shortcuts based on role"""
        base_items = [
            {"name": "Search", "action": "open_search", "hotkey": "Ctrl+K"},
            {"name": "Help", "action": "open_help", "hotkey": "F1"},
            {"name": "Settings", "action": "open_settings", "hotkey": "Ctrl+,"}
        ]
        
        if role in ["SYSTEM_ADMIN", "VICE_PRESIDENT"]:
            base_items.extend([
                {"name": "Export Data", "action": "export_dashboard", "hotkey": "Ctrl+E"},
                {"name": "Security Status", "action": "security_overview", "hotkey": "Ctrl+S"}
            ])
        
        return base_items
    
    def _generate_breadcrumbs(self) -> List[Dict]:
        """Generate intelligent breadcrumb navigation"""
        return [
            {"name": "TRAXOVO", "route": "/", "active": False},
            {"name": "Dashboard", "route": "/dashboard", "active": True}
        ]
    
    def _get_guest_navigation(self) -> Dict[str, Any]:
        """Navigation for non-authenticated users"""
        return {
            "user_info": {"name": "Guest", "role": "VISITOR"},
            "primary_navigation": [
                {"name": "Login", "route": "/login", "icon": "🔑", "description": "Secure login"},
                {"name": "Register", "route": "/register", "icon": "📝", "description": "Create account"},
                {"name": "About", "route": "/about", "icon": "ℹ️", "description": "Learn more"}
            ],
            "tools_navigation": [],
            "quick_access": [
                {"name": "Help", "action": "open_help", "hotkey": "F1"}
            ],
            "breadcrumbs": [{"name": "TRAXOVO", "route": "/", "active": True}],
            "search_enabled": False,
            "notification_center": False,
            "theme": "landing"
        }
    
    def get_mobile_navigation(self, username: str) -> Dict[str, Any]:
        """Get mobile-optimized navigation"""
        full_nav = self.get_navigation_for_user(username)
        
        # Compress navigation for mobile
        return {
            "user_info": full_nav["user_info"],
            "main_menu": full_nav["primary_navigation"][:4],  # Top 4 items
            "overflow_menu": full_nav["primary_navigation"][4:] + full_nav["tools_navigation"],
            "quick_actions": [
                {"name": "Search", "icon": "🔍", "action": "search"},
                {"name": "Menu", "icon": "☰", "action": "toggle_menu"},
                {"name": "Profile", "icon": "👤", "action": "profile"}
            ]
        }

# Global navigation system
_navigation_system = None

def get_navigation_system():
    """Get unified navigation system"""
    global _navigation_system
    if _navigation_system is None:
        _navigation_system = UnifiedNavigationSystem()
    return _navigation_system