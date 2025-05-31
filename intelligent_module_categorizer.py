"""
Intelligent Module Categorizer
Organizes all modules into logical categories with dropdown navigation
"""

module_categories = {
    "CORE_OPERATIONS": {
        "title": "Core Operations",
        "icon": "bi-gear-wide-connected",
        "color": "#007bff",
        "main_dashboard": "/dashboard",
        "modules": [
            {"name": "Master Dashboard", "route": "/dashboard", "icon": "bi-speedometer2", "description": "Main operational overview"},
            {"name": "Fleet Map", "route": "/fleet-map", "icon": "bi-map", "description": "Real-time asset tracking"},
            {"name": "Equipment Dispatch", "route": "/equipment-dispatch", "icon": "bi-truck", "description": "Asset deployment management"},
            {"name": "Schedule Manager", "route": "/schedule-manager", "icon": "bi-calendar-event", "description": "Project scheduling"},
            {"name": "Job Sites", "route": "/job-sites", "icon": "bi-building", "description": "Project location management"}
        ]
    },
    
    "ATTENDANCE_SYSTEM": {
        "title": "Attendance & Workforce",
        "icon": "bi-people-fill",
        "color": "#28a745", 
        "main_dashboard": "/attendance-complete",
        "modules": [
            {"name": "Attendance Dashboard", "route": "/attendance-complete", "icon": "bi-clock-history", "description": "Complete attendance overview"},
            {"name": "Attendance Matrix", "route": "/attendance-matrix", "icon": "bi-grid-3x3", "description": "Detailed attendance grid"},
            {"name": "Driver Management", "route": "/driver-management", "icon": "bi-person-gear", "description": "Driver profiles and performance"},
            {"name": "Daily Driver Report", "route": "/daily-driver-report", "icon": "bi-file-earmark-text", "description": "Daily driver analytics"},
            {"name": "Weekly Driver Report", "route": "/weekly-driver-report", "icon": "bi-calendar-week", "description": "Weekly performance summaries"},
            {"name": "Upload Attendance", "route": "/file-upload", "icon": "bi-cloud-upload", "description": "Import attendance data"},
            {"name": "Export Reports", "route": "/export-attendance-matrix/pdf", "icon": "bi-download", "description": "Export attendance reports"}
        ]
    },
    
    "ANALYTICS_INTELLIGENCE": {
        "title": "Analytics & Intelligence", 
        "icon": "bi-graph-up-arrow",
        "color": "#6f42c1",
        "main_dashboard": "/fleet-analytics",
        "modules": [
            {"name": "Fleet Analytics", "route": "/fleet-analytics", "icon": "bi-bar-chart-line", "description": "Comprehensive fleet analysis"},
            {"name": "Asset Profitability", "route": "/asset-profit", "icon": "bi-cash-stack", "description": "Asset ROI analysis"},
            {"name": "Executive Reports", "route": "/executive-reports", "icon": "bi-file-earmark-bar-graph", "description": "Executive-level reporting"},
            {"name": "Project Tracking", "route": "/project-accountability", "icon": "bi-clipboard-data", "description": "Project performance tracking"},
            {"name": "Bleeding Edge Intelligence", "route": "/bleeding-edge-intelligence", "icon": "bi-lightning", "description": "AI-powered insights"},
            {"name": "Smart Intelligence API", "route": "/api/smart-intelligence", "icon": "bi-cpu", "description": "Real-time intelligence data"}
        ]
    },
    
    "FINANCIAL_REVENUE": {
        "title": "Financial & Revenue",
        "icon": "bi-currency-dollar", 
        "color": "#ffc107",
        "main_dashboard": "/billing",
        "modules": [
            {"name": "Revenue Analytics", "route": "/billing", "icon": "bi-graph-up", "description": "Revenue analysis and trends"},
            {"name": "Equipment Billing", "route": "/equipment-billing", "icon": "bi-receipt", "description": "Equipment billing management"},
            {"name": "Executive ROI Presentation", "route": "/executive-roi-presentation", "icon": "bi-presentation", "description": "ROI presentation mode"},
            {"name": "MTD Reports", "route": "/mtd-reports", "icon": "bi-calendar-month", "description": "Month-to-date reporting"}
        ]
    },
    
    "WORKFLOW_AUTOMATION": {
        "title": "Workflow & Automation",
        "icon": "bi-arrow-repeat",
        "color": "#17a2b8",
        "main_dashboard": "/workflow-automation",
        "modules": [
            {"name": "Workflow Automation", "route": "/workflow-automation", "icon": "bi-robot", "description": "Automated workflow processing"},
            {"name": "Workflow Optimization", "route": "/workflow-optimization", "icon": "bi-speedometer", "description": "Process optimization"},
            {"name": "Predictive Maintenance", "route": "/predictive-maintenance", "icon": "bi-wrench", "description": "AI maintenance predictions"},
            {"name": "Interactive Schedule", "route": "/interactive-schedule", "icon": "bi-calendar-check", "description": "Interactive scheduling tools"}
        ]
    },
    
    "SYSTEM_ADMINISTRATION": {
        "title": "System & Administration",
        "icon": "bi-shield-check",
        "color": "#dc3545", 
        "main_dashboard": "/system-admin",
        "modules": [
            {"name": "System Health", "route": "/system-health", "icon": "bi-heart-pulse", "description": "System monitoring"},
            {"name": "User Management", "route": "/system-admin", "icon": "bi-people", "description": "User administration"},
            {"name": "Development Audit", "route": "/dev_audit", "icon": "bi-bug", "description": "Development monitoring"},
            {"name": "Admin Dashboard", "route": "/admin-dashboard", "icon": "bi-shield-lock", "description": "Administrative controls"},
            {"name": "Deployment Dashboard", "route": "/deployment-dashboard", "icon": "bi-cloud-check", "description": "Deployment monitoring"}
        ]
    },
    
    "DATA_INTEGRATION": {
        "title": "Data & Integration",
        "icon": "bi-database",
        "color": "#6c757d",
        "main_dashboard": "/file-upload", 
        "modules": [
            {"name": "File Upload", "route": "/file-upload", "icon": "bi-cloud-upload", "description": "Data import system"},
            {"name": "Industry News", "route": "/industry-news", "icon": "bi-newspaper", "description": "Industry news integration"},
            {"name": "AI Assistant", "route": "/ai-assistant", "icon": "bi-chat-dots", "description": "AI-powered assistance"},
            {"name": "Demo Executive", "route": "/demo-executive", "icon": "bi-play-circle", "description": "Executive demo mode"}
        ]
    }
}

def get_category_structure():
    """Get the complete categorized module structure"""
    return module_categories

def get_modules_by_category(category_key):
    """Get all modules for a specific category"""
    return module_categories.get(category_key, {}).get("modules", [])

def get_category_dashboard(category_key):
    """Get the main dashboard route for a category"""
    return module_categories.get(category_key, {}).get("main_dashboard", "/dashboard")

def find_module_category(route):
    """Find which category a specific route belongs to"""
    for category_key, category_data in module_categories.items():
        for module in category_data.get("modules", []):
            if module["route"] == route:
                return category_key
    return "CORE_OPERATIONS"  # Default category