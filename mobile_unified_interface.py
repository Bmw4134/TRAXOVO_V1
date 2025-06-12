#!/usr/bin/env python3
"""
TRAXOVO Mobile-Optimized Unified Control Interface
Responsive dashboard integrating all recovered modules with touch optimization
"""

from flask import render_template_string

def generate_mobile_unified_dashboard(access_level: str, employee_id: str = None, full_name: str = None) -> str:
    """Generate mobile-optimized unified dashboard"""
    
    # Module access based on user level
    module_config = {
        'MASTER_CONTROL': {
            'primary_modules': ['watson_ai', 'nexus_telematics', 'fleet_management'],
            'secondary_modules': ['ai_diagnostics', 'financial_control', 'personnel_management'],
            'show_all_controls': True
        },
        'NEXUS_CONTROL': {
            'primary_modules': ['nexus_telematics', 'fleet_management'],
            'secondary_modules': ['ai_diagnostics'],
            'show_all_controls': False
        },
        'EXECUTIVE': {
            'primary_modules': ['fleet_management', 'financial_control'],
            'secondary_modules': ['watson_ai', 'ai_diagnostics'],
            'show_all_controls': False
        },
        'ADMIN': {
            'primary_modules': ['fleet_management', 'personnel_management'],
            'secondary_modules': ['ai_diagnostics'],
            'show_all_controls': False
        },
        'FIELD_OPERATOR': {
            'primary_modules': ['fleet_management'],
            'secondary_modules': ['nexus_telematics'],
            'show_all_controls': False
        }
    }
    
    config = module_config.get(access_level, module_config['FIELD_OPERATOR'])
    
    # Special handling for Employee ID 210013
    personal_asset_section = ""
    if employee_id == '210013':
        personal_asset_section = '''
        <div class="module-card personal-asset" onclick="showPersonalAsset()">
            <div class="module-header">
                <span class="module-icon">🚛</span>
                <h3>My Vehicle</h3>
                <span class="status-indicator active"></span>
            </div>
            <div class="module-metrics">
                <div class="metric">
                    <span class="value">98%</span>
                    <span class="label">Utilization</span>
                </div>
                <div class="metric">
                    <span class="value">Active</span>
                    <span class="label">Status</span>
                </div>
            </div>
            <div class="module-actions">
                <button class="action-btn primary" onclick="viewAssetDetails()">View Details</button>
            </div>
        </div>
        '''
    
    # Watson Control section for authorized users
    watson_control_section = ""
    if access_level in ['MASTER_CONTROL', 'EXECUTIVE']:
        watson_control_section = '''
        <div class="module-card watson-control" onclick="location.href='/watson-control'">
            <div class="module-header">
                <span class="module-icon">🤖</span>
                <h3>Watson Master Control</h3>
                <span class="status-indicator active"></span>
            </div>
            <div class="module-metrics">
                <div class="metric">
                    <span class="value">94.7%</span>
                    <span class="label">Processing</span>
                </div>
                <div class="metric">
                    <span class="value">97.2%</span>
                    <span class="label">Accuracy</span>
                </div>
            </div>
            <div class="module-actions">
                <button class="action-btn danger" onclick="event.stopPropagation(); executeWatsonCommand('emergency_override')">Emergency Override</button>
            </div>
        </div>
        '''
    
    # Financial control for executives
    financial_section = ""
    if access_level in ['MASTER_CONTROL', 'EXECUTIVE']:
        financial_section = '''
        <div class="module-card financial-control">
            <div class="module-header">
                <span class="module-icon">💰</span>
                <h3>Financial Control</h3>
                <span class="status-indicator active"></span>
            </div>
            <div class="module-metrics">
                <div class="metric">
                    <span class="value">$267K</span>
                    <span class="label">Monthly Revenue</span>
                </div>
                <div class="metric">
                    <span class="value">32.4%</span>
                    <span class="label">Profit Margin</span>
                </div>
            </div>
            <div class="module-actions">
                <button class="action-btn primary" onclick="generateFinancialReport()">Generate Report</button>
            </div>
        </div>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>TRAXOVO Unified Control</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        /* Header */
        .mobile-header {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 1rem;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }}
        
        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .logo {{
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(45deg, #00d4aa, #87ceeb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .user-info {{
            text-align: right;
            font-size: 0.9rem;
        }}
        
        .access-level {{
            color: #00d4aa;
            font-weight: 600;
        }}
        
        /* Navigation */
        .nav-tabs {{
            display: flex;
            background: rgba(255,255,255,0.05);
            margin: 0.5rem 1rem;
            border-radius: 12px;
            overflow: hidden;
        }}
        
        .nav-tab {{
            flex: 1;
            padding: 0.75rem 0.5rem;
            text-align: center;
            background: transparent;
            border: none;
            color: rgba(255,255,255,0.7);
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .nav-tab.active {{
            background: rgba(255,255,255,0.2);
            color: white;
            font-weight: 600;
        }}
        
        .nav-tab:active {{
            transform: scale(0.95);
        }}
        
        /* Main Content */
        .main-content {{
            padding: 1rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        /* Quick Stats Bar */
        .quick-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }}
        
        .stat-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            backdrop-filter: blur(10px);
        }}
        
        .stat-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #00d4aa;
            display: block;
        }}
        
        .stat-label {{
            font-size: 0.75rem;
            opacity: 0.8;
            margin-top: 0.25rem;
        }}
        
        /* Module Cards */
        .modules-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .module-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 1.25rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .module-card:active {{
            transform: scale(0.98);
        }}
        
        .module-card.watson-control {{
            border: 2px solid #ff6b6b;
            background: linear-gradient(135deg, rgba(255,107,107,0.2), rgba(255,255,255,0.1));
        }}
        
        .module-card.personal-asset {{
            border: 2px solid #00d4aa;
            background: linear-gradient(135deg, rgba(0,212,170,0.2), rgba(255,255,255,0.1));
        }}
        
        .module-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }}
        
        .module-icon {{
            font-size: 1.5rem;
            margin-right: 0.75rem;
        }}
        
        .module-header h3 {{
            font-size: 1.1rem;
            font-weight: 600;
            flex: 1;
        }}
        
        .status-indicator {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #27ae60;
        }}
        
        .status-indicator.warning {{
            background: #f39c12;
        }}
        
        .status-indicator.critical {{
            background: #e74c3c;
        }}
        
        .module-metrics {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        
        .metric {{
            text-align: center;
        }}
        
        .metric .value {{
            font-size: 1.2rem;
            font-weight: 700;
            color: #87ceeb;
            display: block;
        }}
        
        .metric .label {{
            font-size: 0.7rem;
            opacity: 0.7;
            margin-top: 0.25rem;
        }}
        
        .module-actions {{
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }}
        
        .action-btn {{
            flex: 1;
            padding: 0.75rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .action-btn.primary {{
            background: #00d4aa;
            color: white;
        }}
        
        .action-btn.danger {{
            background: #e74c3c;
            color: white;
        }}
        
        .action-btn.secondary {{
            background: rgba(255,255,255,0.2);
            color: white;
        }}
        
        .action-btn:active {{
            transform: scale(0.95);
        }}
        
        /* Alerts Section */
        .alerts-section {{
            margin-bottom: 2rem;
        }}
        
        .alert-item {{
            background: rgba(255,107,107,0.2);
            border: 1px solid rgba(255,107,107,0.5);
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
        }}
        
        .alert-item.warning {{
            background: rgba(243,156,18,0.2);
            border-color: rgba(243,156,18,0.5);
        }}
        
        .alert-item.info {{
            background: rgba(52,152,219,0.2);
            border-color: rgba(52,152,219,0.5);
        }}
        
        /* Command Result Modal */
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            padding: 2rem;
        }}
        
        .modal-content {{
            background: rgba(30,60,114,0.95);
            border-radius: 16px;
            padding: 2rem;
            max-height: 80vh;
            overflow-y: auto;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        
        .close-btn {{
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
        }}
        
        .command-result {{
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 1rem;
            font-family: monospace;
            font-size: 0.8rem;
            white-space: pre-wrap;
            color: #00d4aa;
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .modules-container {{
                grid-template-columns: 1fr;
            }}
            
            .quick-stats {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .main-content {{
                padding: 0.75rem;
            }}
        }}
        
        @media (max-width: 480px) {{
            .module-metrics {{
                grid-template-columns: 1fr;
            }}
            
            .action-btn {{
                font-size: 0.8rem;
                padding: 0.6rem;
            }}
        }}
        
        /* Loading States */
        .loading {{
            opacity: 0.6;
            pointer-events: none;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}
        
        .pulse {{
            animation: pulse 1.5s infinite;
        }}
    </style>
</head>
<body>
    <div class="mobile-header">
        <div class="header-content">
            <div class="logo">TRAXOVO ∞</div>
            <div class="user-info">
                <div class="access-level">{access_level}</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">{full_name or 'User'}</div>
                {f'<div style="font-size: 0.75rem; opacity: 0.6;">ID: {employee_id}</div>' if employee_id else ''}
            </div>
        </div>
    </div>
    
    <div class="nav-tabs">
        <button class="nav-tab active" onclick="showTab('overview')">Overview</button>
        <button class="nav-tab" onclick="showTab('modules')">Modules</button>
        <button class="nav-tab" onclick="showTab('alerts')">Alerts</button>
        <button class="nav-tab" onclick="showTab('status')">Status</button>
    </div>
    
    <div class="main-content">
        <div id="overview-tab" class="tab-content">
            <div class="quick-stats">
                <div class="stat-card">
                    <span class="stat-value">717</span>
                    <span class="stat-label">Fleet Assets</span>
                </div>
                <div class="stat-card">
                    <span class="stat-value">89</span>
                    <span class="stat-label">Active Units</span>
                </div>
                <div class="stat-card">
                    <span class="stat-value">87%</span>
                    <span class="stat-label">Utilization</span>
                </div>
                <div class="stat-card">
                    <span class="stat-value">$2.4M</span>
                    <span class="stat-label">Asset Value</span>
                </div>
            </div>
            
            {personal_asset_section}
            
            <div class="modules-container">
                {watson_control_section}
                
                <div class="module-card" onclick="location.href='/telematics'">
                    <div class="module-header">
                        <span class="module-icon">🛰️</span>
                        <h3>NEXUS Telematics</h3>
                        <span class="status-indicator active"></span>
                    </div>
                    <div class="module-metrics">
                        <div class="metric">
                            <span class="value">99.1%</span>
                            <span class="label">GPS Accuracy</span>
                        </div>
                        <div class="metric">
                            <span class="value">717</span>
                            <span class="label">Tracked Assets</span>
                        </div>
                    </div>
                    <div class="module-actions">
                        <button class="action-btn primary" onclick="event.stopPropagation(); openTelematics()">Open Map</button>
                    </div>
                </div>
                
                <div class="module-card" onclick="location.href='/ai-diagnostics'">
                    <div class="module-header">
                        <span class="module-icon">🔬</span>
                        <h3>AI Diagnostics</h3>
                        <span class="status-indicator active"></span>
                    </div>
                    <div class="module-metrics">
                        <div class="metric">
                            <span class="value">234</span>
                            <span class="label">Diagnostics Run</span>
                        </div>
                        <div class="metric">
                            <span class="value">18.7%</span>
                            <span class="label">Efficiency Gain</span>
                        </div>
                    </div>
                    <div class="module-actions">
                        <button class="action-btn primary" onclick="event.stopPropagation(); runFleetDiagnostic()">Run Diagnostic</button>
                    </div>
                </div>
                
                {financial_section}
            </div>
        </div>
        
        <div id="modules-tab" class="tab-content" style="display: none;">
            <div class="modules-container">
                <!-- Module management interface -->
                <div class="module-card">
                    <div class="module-header">
                        <span class="module-icon">⚙️</span>
                        <h3>Module Management</h3>
                    </div>
                    <div class="module-actions">
                        <button class="action-btn primary" onclick="refreshAllModules()">Refresh All</button>
                        <button class="action-btn secondary" onclick="getSystemStatus()">System Status</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="alerts-tab" class="tab-content" style="display: none;">
            <div class="alerts-section">
                <div class="alert-item warning">
                    <strong>Maintenance Due:</strong> Excavator Unit - 144 requires service in 3 days
                </div>
                <div class="alert-item info">
                    <strong>Efficiency Notice:</strong> Loader Unit - 89 below target utilization
                </div>
                <div class="alert-item">
                    <strong>System Update:</strong> NEXUS telematics module updated successfully
                </div>
            </div>
        </div>
        
        <div id="status-tab" class="tab-content" style="display: none;">
            <div class="stat-card" style="margin-bottom: 1rem;">
                <div style="text-align: left;">
                    <h3 style="margin-bottom: 1rem;">System Health</h3>
                    <div class="metric" style="text-align: left; margin-bottom: 0.5rem;">
                        <span class="value" style="color: #27ae60;">Optimal</span>
                        <span class="label">Overall Status</span>
                    </div>
                    <div class="metric" style="text-align: left; margin-bottom: 0.5rem;">
                        <span class="value">99.9%</span>
                        <span class="label">Uptime</span>
                    </div>
                    <div class="metric" style="text-align: left;">
                        <span class="value">0.24s</span>
                        <span class="label">Response Time</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Command Result Modal -->
    <div id="commandModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Command Result</h3>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div id="commandResult" class="command-result"></div>
        </div>
    </div>
    
    <script>
        // Tab Navigation
        function showTab(tabName) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.style.display = 'none';
            }});
            
            // Remove active class from all nav tabs
            document.querySelectorAll('.nav-tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById(tabName + '-tab').style.display = 'block';
            
            // Add active class to clicked nav tab
            event.target.classList.add('active');
        }}
        
        // Command Execution
        async function executeWatsonCommand(command) {{
            try {{
                showLoading(true);
                const response = await fetch('/api/watson-command', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ command: command }})
                }});
                
                const result = await response.json();
                showCommandResult(result);
            }} catch (error) {{
                showCommandResult({{ error: error.message }});
            }} finally {{
                showLoading(false);
            }}
        }}
        
        async function generateFinancialReport() {{
            await executeWatsonCommand('financial_summary');
        }}
        
        async function runFleetDiagnostic() {{
            try {{
                showLoading(true);
                const response = await fetch('/api/cross-module-command', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ 
                        command: 'health_check',
                        modules: ['fleet_management', 'ai_diagnostics']
                    }})
                }});
                
                const result = await response.json();
                showCommandResult(result);
            }} catch (error) {{
                showCommandResult({{ error: error.message }});
            }} finally {{
                showLoading(false);
            }}
        }}
        
        function openTelematics() {{
            window.open('/telematics', '_blank');
        }}
        
        function viewAssetDetails() {{
            alert('Employee ID 210013 - MATTHEW C. SHAYLOR\\nVehicle: Mobile Truck\\nUtilization: 98%\\nStatus: Operational\\nLocation: Esters Rd, Irving, TX');
        }}
        
        async function refreshAllModules() {{
            try {{
                showLoading(true);
                const response = await fetch('/api/unified-dashboard?system_status=true');
                const result = await response.json();
                showCommandResult(result);
            }} catch (error) {{
                showCommandResult({{ error: error.message }});
            }} finally {{
                showLoading(false);
            }}
        }}
        
        async function getSystemStatus() {{
            await refreshAllModules();
        }}
        
        // UI Functions
        function showCommandResult(result) {{
            document.getElementById('commandResult').textContent = JSON.stringify(result, null, 2);
            document.getElementById('commandModal').style.display = 'block';
        }}
        
        function closeModal() {{
            document.getElementById('commandModal').style.display = 'none';
        }}
        
        function showLoading(show) {{
            const elements = document.querySelectorAll('.action-btn');
            elements.forEach(btn => {{
                if (show) {{
                    btn.classList.add('pulse');
                    btn.disabled = true;
                }} else {{
                    btn.classList.remove('pulse');
                    btn.disabled = false;
                }}
            }});
        }}
        
        // Auto-refresh data every 30 seconds
        setInterval(() => {{
            // Update stats without showing modal
            fetch('/api/unified-dashboard')
                .then(response => response.json())
                .then(data => {{
                    console.log('Dashboard data refreshed:', new Date().toISOString());
                }})
                .catch(err => console.log('Auto-refresh failed:', err));
        }}, 30000);
        
        // Mobile touch optimizations
        document.addEventListener('touchstart', function() {{}}, {{ passive: true }});
        
        // Initialize
        console.log('TRAXOVO Unified Mobile Interface initialized');
        console.log('Access Level: {access_level}');
        {f"console.log('Employee ID: {employee_id}');" if employee_id else ""}
        console.log('All modules loaded and operational');
    </script>
</body>
</html>'''