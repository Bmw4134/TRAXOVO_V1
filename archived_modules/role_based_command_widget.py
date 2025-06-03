"""
Role-Based Command Widget System
Personalized floating command interface that adapts to user roles and permissions
"""

class RoleBasedCommandWidget:
    """Generates personalized command widgets based on user role and permissions"""
    
    def __init__(self):
        self.user_roles = {
            "executive": {
                "title": "Executive Command Center",
                "color_scheme": "linear-gradient(135deg, #2d1b69, #ffd700)",
                "icon": "fa-crown",
                "commands": [
                    {"name": "Executive Dashboard", "route": "/dashboard", "icon": "fa-chart-line"},
                    {"name": "Quantum ASI Status", "route": "/quantum_asi_dashboard", "icon": "fa-atom"},
                    {"name": "Financial Analytics", "route": "/agi_analytics", "icon": "fa-dollar-sign"},
                    {"name": "Security Audit", "route": "/board_security_audit", "icon": "fa-shield-alt"},
                    {"name": "Fleet Overview", "route": "/fleet_management", "icon": "fa-truck"},
                    {"name": "Performance Metrics", "route": "/predictive_analytics", "icon": "fa-chart-bar"}
                ]
            },
            "operations": {
                "title": "Operations Command Hub",
                "color_scheme": "linear-gradient(135deg, #1a4870, #00d4ff)",
                "icon": "fa-cogs",
                "commands": [
                    {"name": "Fleet Management", "route": "/fleet_management", "icon": "fa-truck"},
                    {"name": "Asset Lifecycle", "route": "/agi_asset_lifecycle", "icon": "fa-wrench"},
                    {"name": "Maintenance Schedule", "route": "/maintenance_dashboard", "icon": "fa-tools"},
                    {"name": "Driver Management", "route": "/driver_dashboard", "icon": "fa-users"},
                    {"name": "Route Optimization", "route": "/route_optimizer", "icon": "fa-route"},
                    {"name": "Automated Reports", "route": "/automated_reports", "icon": "fa-file-alt"}
                ]
            },
            "admin": {
                "title": "System Administration",
                "color_scheme": "linear-gradient(135deg, #dc2626, #ef4444)",
                "icon": "fa-user-shield",
                "commands": [
                    {"name": "User Management", "route": "/enterprise_users", "icon": "fa-users-cog"},
                    {"name": "System Monitor", "route": "/technical_testing", "icon": "fa-server"},
                    {"name": "Puppeteer Control", "route": "/puppeteer_control_center", "icon": "fa-robot"},
                    {"name": "Security Settings", "route": "/security_config", "icon": "fa-lock"},
                    {"name": "Database Admin", "route": "/database_admin", "icon": "fa-database"},
                    {"name": "API Management", "route": "/api_management", "icon": "fa-code"}
                ]
            },
            "analyst": {
                "title": "Analytics Workspace",
                "color_scheme": "linear-gradient(135deg, #059669, #10b981)",
                "icon": "fa-chart-pie",
                "commands": [
                    {"name": "AGI Analytics", "route": "/agi_analytics", "icon": "fa-brain"},
                    {"name": "Data Visualization", "route": "/data_viz", "icon": "fa-chart-area"},
                    {"name": "Predictive Models", "route": "/predictive_analytics", "icon": "fa-crystal-ball"},
                    {"name": "Report Builder", "route": "/report_builder", "icon": "fa-file-chart"},
                    {"name": "KPI Dashboard", "route": "/kpi_dashboard", "icon": "fa-tachometer-alt"},
                    {"name": "Data Sources", "route": "/data_sources", "icon": "fa-database"}
                ]
            },
            "technician": {
                "title": "Technician Toolkit",
                "color_scheme": "linear-gradient(135deg, #ea580c, #f97316)",
                "icon": "fa-tools",
                "commands": [
                    {"name": "Work Orders", "route": "/work_orders", "icon": "fa-clipboard-list"},
                    {"name": "Asset Status", "route": "/asset_status", "icon": "fa-truck"},
                    {"name": "Maintenance Log", "route": "/maintenance_log", "icon": "fa-wrench"},
                    {"name": "Parts Inventory", "route": "/parts_inventory", "icon": "fa-box"},
                    {"name": "Diagnostic Tools", "route": "/diagnostics", "icon": "fa-stethoscope"},
                    {"name": "Mobile Scanner", "route": "/mobile_scanner", "icon": "fa-qrcode"}
                ]
            }
        }
    
    def generate_widget_html(self, user_role="executive", username="User"):
        """Generate HTML for role-based command widget"""
        if user_role not in self.user_roles:
            user_role = "executive"
        
        role_config = self.user_roles[user_role]
        
        return f'''
<div id="roleBasedCommandWidget" class="role-command-widget {user_role}-theme">
    <div class="widget-header">
        <div class="role-indicator">
            <i class="fas {role_config['icon']} me-2"></i>
            <span class="role-title">{role_config['title']}</span>
        </div>
        <div class="user-info">
            <span class="username">{username}</span>
            <button class="btn-toggle" onclick="toggleCommandWidget()">
                <i class="fas fa-chevron-down"></i>
            </button>
        </div>
    </div>
    
    <div class="widget-content" id="widgetContent">
        <div class="quick-actions">
            {self._generate_command_buttons(role_config['commands'])}
        </div>
        
        <div class="widget-footer">
            <div class="status-indicators">
                <span class="status-item">
                    <i class="fas fa-circle text-success"></i>
                    GAUGE API Live
                </span>
                <span class="status-item">
                    <i class="fas fa-circle text-info"></i>
                    Quantum Active
                </span>
            </div>
        </div>
    </div>
</div>

<style>
.role-command-widget {{
    position: fixed;
    top: 20px;
    right: 20px;
    width: 320px;
    background: {role_config['color_scheme']};
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    z-index: 9999;
    color: white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}}

.widget-header {{
    padding: 15px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.role-indicator {{
    display: flex;
    align-items: center;
    font-weight: 600;
    font-size: 0.9rem;
}}

.user-info {{
    display: flex;
    align-items: center;
    gap: 10px;
}}

.username {{
    font-size: 0.8rem;
    opacity: 0.9;
}}

.btn-toggle {{
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    padding: 5px;
    border-radius: 50%;
    transition: all 0.3s ease;
}}

.btn-toggle:hover {{
    background: rgba(255, 255, 255, 0.2);
}}

.widget-content {{
    padding: 20px;
    max-height: 400px;
    overflow-y: auto;
}}

.quick-actions {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 20px;
}}

.command-btn {{
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 12px 8px;
    color: white;
    text-decoration: none;
    text-align: center;
    font-size: 0.75rem;
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
}}

.command-btn:hover {{
    background: rgba(255, 255, 255, 0.2);
    color: white;
    text-decoration: none;
    transform: translateY(-2px);
}}

.command-btn i {{
    font-size: 1.2rem;
    margin-bottom: 5px;
}}

.widget-footer {{
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    padding-top: 15px;
}}

.status-indicators {{
    display: flex;
    justify-content: space-around;
    font-size: 0.7rem;
}}

.status-item {{
    display: flex;
    align-items: center;
    gap: 5px;
}}

/* Responsive adjustments */
@media (max-width: 768px) {{
    .role-command-widget {{
        width: 280px;
        right: 10px;
        top: 10px;
    }}
    
    .quick-actions {{
        grid-template-columns: 1fr;
    }}
}}

/* Role-specific themes */
.executive-theme {{
    background: linear-gradient(135deg, #2d1b69, #ffd700);
}}

.operations-theme {{
    background: linear-gradient(135deg, #1a4870, #00d4ff);
}}

.admin-theme {{
    background: linear-gradient(135deg, #dc2626, #ef4444);
}}

.analyst-theme {{
    background: linear-gradient(135deg, #059669, #10b981);
}}

.technician-theme {{
    background: linear-gradient(135deg, #ea580c, #f97316);
}}
</style>

<script>
function toggleCommandWidget() {{
    const content = document.getElementById('widgetContent');
    const toggle = document.querySelector('.btn-toggle i');
    
    if (content.style.display === 'none') {{
        content.style.display = 'block';
        toggle.className = 'fas fa-chevron-down';
    }} else {{
        content.style.display = 'none';
        toggle.className = 'fas fa-chevron-up';
    }}
}}

// Auto-hide after inactivity
let widgetTimeout;
function resetWidgetTimeout() {{
    clearTimeout(widgetTimeout);
    widgetTimeout = setTimeout(() => {{
        const content = document.getElementById('widgetContent');
        if (content && content.style.display !== 'none') {{
            content.style.display = 'none';
            document.querySelector('.btn-toggle i').className = 'fas fa-chevron-up';
        }}
    }}, 30000); // Auto-hide after 30 seconds
}}

document.addEventListener('mousemove', resetWidgetTimeout);
document.addEventListener('click', resetWidgetTimeout);
</script>
'''
    
    def _generate_command_buttons(self, commands):
        """Generate command buttons HTML"""
        buttons_html = ""
        for cmd in commands:
            buttons_html += f'''
            <a href="{cmd['route']}" class="command-btn">
                <i class="fas {cmd['icon']}"></i>
                <span>{cmd['name']}</span>
            </a>
            '''
        return buttons_html
    
    def get_user_role_from_session(self, session):
        """Determine user role from session data"""
        if 'role' in session:
            return session['role']
        elif 'username' in session:
            username = session['username'].lower()
            if 'admin' in username:
                return 'admin'
            elif 'ops' in username or 'operations' in username:
                return 'operations'
            elif 'tech' in username or 'technician' in username:
                return 'technician'
            elif 'analyst' in username:
                return 'analyst'
            else:
                return 'executive'
        return 'executive'

def get_role_widget():
    """Get role-based widget generator"""
    return RoleBasedCommandWidget()