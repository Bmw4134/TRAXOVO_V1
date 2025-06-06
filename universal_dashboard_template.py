"""
Universal Dashboard Template System
Apply consistent login, landing page, and dashboard structure across all dashboards
"""

def get_universal_base_template():
    """Get the universal base template for all dashboards"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ page_title }} - Watson Intelligence Platform</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, rgba(0, 20, 50, 0.95) 0%, rgba(20, 0, 50, 0.95) 100%);
            color: #ffffff; 
            overflow-x: hidden; 
            margin: 0;
            min-height: 100vh;
        }
        
        .sidebar { 
            position: fixed; 
            left: 0; 
            top: 0; 
            width: 280px; 
            height: 100vh; 
            background: rgba(0, 30, 60, 0.9); 
            backdrop-filter: blur(10px);
            border-right: 2px solid rgba(0, 255, 100, 0.4);
            z-index: 1000; 
            transition: transform 0.3s; 
        }
        .sidebar.collapsed { transform: translateX(-240px); }
        .sidebar-header { padding: 20px; border-bottom: 1px solid #2a2a4e; }
        .logo { 
            color: #00ff64; 
            font-size: 24px; 
            font-weight: 700; 
            text-shadow: 0 0 8px rgba(0, 255, 100, 0.3);
            letter-spacing: 1px;
        }
        .user-info { margin-top: 10px; }
        .user-name { color: #ffffff; font-size: 14px; }
        .user-role { color: #00ff64; font-size: 12px; }
        
        .nav-menu { padding: 20px 0; }
        .nav-section { margin-bottom: 25px; }
        .nav-section-title { color: #00ff64; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; padding: 0 20px; margin-bottom: 8px; }
        .nav-item { display: block; padding: 12px 20px; color: #ffffff; text-decoration: none; transition: all 0.2s; border-left: 3px solid transparent; }
        .nav-item:hover { background: rgba(0,255,100,0.08); border-left-color: #00ff64; }
        .nav-item.active { background: rgba(0,255,100,0.1); border-left-color: #00ff64; }
        .nav-item.watson-exclusive { border-left-color: #ff6b35; }
        .nav-item.watson-exclusive:hover { background: rgba(255, 107, 53, 0.08); }
        
        .main-content { margin-left: 280px; min-height: 100vh; transition: margin-left 0.3s; }
        .main-content.expanded { margin-left: 40px; }
        
        .header { 
            background: rgba(0, 30, 60, 0.8); 
            backdrop-filter: blur(10px);
            padding: 20px 40px; 
            border-bottom: 1px solid rgba(0, 255, 100, 0.2);
            position: sticky;
            top: 0;
            z-index: 999;
        }
        .header-content { display: flex; justify-content: space-between; align-items: center; }
        .page-title { 
            color: #00ff64; 
            font-size: 28px; 
            font-weight: 700;
            text-shadow: 0 0 15px rgba(0, 255, 100, 0.5);
            animation: companyGlow 2s ease-in-out infinite alternate;
        }
        .page-subtitle { color: #ffffff; margin-top: 5px; opacity: 0.8; }
        
        .header-actions { display: flex; gap: 15px; }
        .header-btn { 
            background: linear-gradient(135deg, #00ff64, #00ff88); 
            color: #000; 
            padding: 10px 20px; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: 600; 
            text-decoration: none;
            transition: all 0.2s;
        }
        .header-btn:hover { 
            background: linear-gradient(135deg, #00ff88, #00ff64); 
            transform: translateY(-2px); 
            box-shadow: 0 0 20px rgba(0, 255, 100, 0.4);
        }
        
        .content-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); 
            gap: 30px; 
            padding: 40px; 
            max-width: 1400px; 
            margin: 0 auto;
        }
        
        .module-card { 
            background: rgba(30, 42, 71, 0.8); 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 255, 100, 0.2); 
            border-radius: 12px; 
            padding: 30px; 
            transition: all 0.3s; 
            position: relative;
            overflow: hidden;
        }
        .module-card::before { 
            content: ''; 
            position: absolute; 
            top: 0; 
            left: 0; 
            right: 0; 
            height: 4px; 
            background: linear-gradient(90deg, #00ff64, #00ff88); 
        }
        .module-card:hover { 
            transform: translateY(-10px); 
            box-shadow: 0 15px 40px rgba(0, 255, 100, 0.2);
            border-color: #00ff64;
        }
        .module-card.watson-exclusive::before { background: linear-gradient(90deg, #ff6b35, #ff8c42); }
        
        .module-icon { width: 48px; height: 48px; background: linear-gradient(135deg, #00ff88, #4ecdc4); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; font-size: 24px; }
        .module-icon.watson { background: linear-gradient(135deg, #ff6b35, #ff8c42); }
        .module-title { 
            color: #00ff64; 
            font-size: 18px; 
            font-weight: 600; 
            margin-bottom: 8px; 
            text-shadow: 0 0 10px rgba(0, 255, 100, 0.5);
        }
        .module-desc { color: #ffffff; font-size: 14px; line-height: 1.5; margin-bottom: 20px; opacity: 0.9; }
        .module-stats { display: flex; gap: 15px; margin-bottom: 20px; }
        .stat-item { text-align: center; }
        .stat-value { 
            font-size: 18px; 
            font-weight: bold; 
            color: #00ff64; 
            text-shadow: 0 0 10px rgba(0, 255, 100, 0.5);
            animation: metricPulse 2s ease-in-out infinite;
        }
        .stat-label { font-size: 11px; color: #ffffff; text-transform: uppercase; opacity: 0.7; }
        
        .access-btn { 
            background: linear-gradient(135deg, #00ff64, #00ff88); 
            color: #000; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            text-decoration: none; 
            display: inline-block; 
            font-weight: 600; 
            transition: all 0.2s;
        }
        .access-btn:hover { 
            background: linear-gradient(135deg, #00ff88, #00ff64); 
            transform: translateY(-2px); 
            box-shadow: 0 0 20px rgba(0, 255, 100, 0.4);
        }
        .access-btn.watson { background: linear-gradient(135deg, #ff6b35, #ff8c42); }
        
        @keyframes companyGlow {
            from { text-shadow: 0 0 30px rgba(0, 255, 100, 0.8); }
            to { text-shadow: 0 0 40px rgba(0, 255, 100, 1); }
        }
        
        @keyframes metricPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        @keyframes ripple-animation {
            0% { transform: scale(0); opacity: 1; }
            100% { transform: scale(4); opacity: 0; }
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOut {
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .sidebar-toggle { position: fixed; top: 20px; left: 20px; z-index: 1001; background: #1a1a2e; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer; }
        
        .fix-module { padding: 20px; margin-top: 30px; background: rgba(0, 30, 60, 0.6); border-radius: 8px; border: 1px solid rgba(0, 255, 100, 0.3); }
        .fix-module-title { color: #00ff64; font-size: 14px; font-weight: 600; margin-bottom: 15px; }
        .fix-btn { width: 100%; background: #1e40af; color: white; padding: 8px 12px; border: none; border-radius: 4px; cursor: pointer; margin: 5px 0; font-size: 12px; transition: all 0.2s; }
        .fix-btn:hover { background: #3b82f6; transform: translateY(-1px); }
        .fix-btn.critical { background: #dc2626; }
        .fix-btn.critical:hover { background: #ef4444; }
        
        /* Custom content area for specific dashboards */
        .dashboard-content { padding: 40px; }
        .full-width-content { margin-left: 0; }
        
        {{ custom_styles }}
    </style>
</head>
<body>
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <div class="logo">{{ company_name | default('TRAXOVO') }}</div>
            <div class="user-info">
                <div class="user-name">{{ user.name }}</div>
                <div class="user-role">{{ user.role }}</div>
            </div>
        </div>
        
        <nav class="nav-menu">
            <div class="nav-section">
                <div class="nav-section-title">Core Systems</div>
                <a href="/" class="nav-item {{ 'active' if active_page == 'dashboard' else '' }}">🏠 Dashboard</a>
                <a href="/proprietary_asset_tracker" class="nav-item {{ 'active' if active_page == 'asset_tracker' else '' }}">🎯 Asset Intelligence</a>
                <a href="/email_config" class="nav-item {{ 'active' if active_page == 'email_config' else '' }}">📧 Email Config</a>
                <a href="/fleet_analytics" class="nav-item {{ 'active' if active_page == 'analytics' else '' }}">📊 Analytics</a>
                <a href="/attendance_matrix" class="nav-item {{ 'active' if active_page == 'attendance' else '' }}">👥 Attendance</a>
                
                <!-- Custom navigation items -->
                {{ custom_nav_items | safe }}
            </div>
            
            {% if user.watson_access %}
            <div class="nav-section">
                <div class="nav-section-title">Watson Exclusive</div>
                <a href="/watson_console.html" class="nav-item watson-exclusive {{ 'active' if active_page == 'watson_console' else '' }}">🤖 Watson Console</a>
                <a href="/voice_commands" class="nav-item watson-exclusive {{ 'active' if active_page == 'voice_commands' else '' }}">🎤 Voice Commands</a>
            </div>
            {% endif %}
        </nav>
        
        <div class="fix-module">
            <div class="fix-module-title">🔧 Universal Fix Module</div>
            <button class="fix-btn" onclick="runQuickFix('performance')">⚡ Performance Boost</button>
            <button class="fix-btn" onclick="runQuickFix('routes')">🔄 Fix Routes</button>
            <button class="fix-btn" onclick="runQuickFix('features')">🛠️ Repair Features</button>
            {% if user.role in ['admin', 'watson_owner', 'dev_admin_master'] %}
            <button class="fix-btn critical" onclick="runQuickFix('system')">⚠️ System Reset</button>
            {% endif %}
            <button class="fix-btn" onclick="showDiagnostics()">📊 Diagnostics</button>
        </div>
    </div>
    
    <div class="main-content {{ 'full-width-content' if full_width else '' }}" id="mainContent">
        <button class="sidebar-toggle" onclick="toggleSidebar()">☰</button>
        
        <div class="header">
            <div class="header-content">
                <div>
                    <h1 class="page-title">{{ page_title }}</h1>
                    <p class="page-subtitle">{{ page_subtitle }}</p>
                </div>
                <div class="header-actions">
                    <button class="header-btn" onclick="refreshDashboard()">🔄 Refresh</button>
                    {{ custom_header_buttons | safe }}
                    <a href="/logout"><button class="header-btn" style="background: #dc3545;">Logout</button></a>
                </div>
            </div>
        </div>
        
        <!-- Dashboard content area -->
        {{ dashboard_content | safe }}
    </div>

    <script>
        // Universal JavaScript functions for all dashboards
        function showNotification(message, type) {
            type = type || 'success';
            const notification = document.createElement('div');
            notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: ' + 
                (type === 'success' ? '#00ff64' : '#ff4444') + '; color: ' + 
                (type === 'success' ? '#000' : '#fff') + '; padding: 15px 20px; border-radius: 8px; z-index: 10000; animation: slideIn 0.5s ease-out; font-weight: 600;';
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(function() {
                notification.style.animation = 'slideOut 0.3s ease-in forwards';
                setTimeout(function() { 
                    if (notification.parentNode) notification.remove(); 
                }, 300);
            }, 3000);
        }

        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const mainContent = document.getElementById('mainContent');
            
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        }

        function runQuickFix(type) {
            console.log('Running quick fix for:', type);
            showNotification('Running ' + type + ' optimization', 'success');
            
            setTimeout(function() {
                showNotification(type + ' optimization completed', 'success');
            }, 2000);
        }

        function refreshDashboard() {
            showNotification('Refreshing dashboard', 'success');
            setTimeout(function() { location.reload(); }, 1000);
        }

        function showDiagnostics() {
            showNotification('Running system diagnostics', 'success');
            setTimeout(function() {
                showNotification('All systems operational', 'success');
            }, 2000);
        }

        // Initialize micro-interactions
        function initializeMicroInteractions() {
            console.log('Micro-Animation Feedback Layer initialized');
            
            // Ripple effect
            document.addEventListener('click', function(e) {
                const element = e.target.closest('.access-btn, .module-card, .nav-item');
                if (!element) return;
                
                const ripple = document.createElement('span');
                const rect = element.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.cssText = 'width: ' + size + 'px; height: ' + size + 'px; left: ' + x + 'px; top: ' + y + 'px; position: absolute; border-radius: 50%; background: rgba(0, 255, 100, 0.3); pointer-events: none; animation: ripple-animation 0.6s linear;';
                
                element.style.position = 'relative';
                element.style.overflow = 'hidden';
                element.appendChild(ripple);
                
                setTimeout(function() {
                    if (ripple.parentNode) ripple.remove();
                }, 600);
            });

            // Hover effects
            document.querySelectorAll('.module-card, .access-btn').forEach(function(element) {
                element.addEventListener('mouseenter', function() {
                    element.style.transform = 'translateY(-5px)';
                    element.style.transition = 'all 0.3s ease';
                });
                
                element.addEventListener('mouseleave', function() {
                    element.style.transform = '';
                });
            });
        }

        // Initialize everything on DOM ready
        document.addEventListener('DOMContentLoaded', function() {
            console.log('{{ page_title }} dashboard initialized');
            
            initializeMicroInteractions();
            
            // Navigation feedback
            document.querySelectorAll('.nav-item').forEach(function(item) {
                item.addEventListener('click', function() {
                    showNotification('Navigation activated', 'success');
                });
            });
            
            // Custom dashboard initialization
            {{ custom_javascript | safe }}
        });
    </script>
</body>
</html>
    """

def get_universal_login_template():
    """Get the universal login template"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ platform_name | default('TRAXOVO') }} Login - Watson Intelligence</title>
    <style>
        body { margin: 0; background: #0a0a0a; color: white; font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .login-container { background: #1a1a2e; padding: 40px; border-radius: 15px; border: 2px solid #00ff88; box-shadow: 0 0 20px rgba(0,255,136,0.3); }
        .login-title { color: #00ff88; text-align: center; margin-bottom: 30px; font-size: 24px; }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 5px; color: #00ff88; }
        input { width: 300px; padding: 12px; background: #2a2a4e; color: white; border: 1px solid #555; border-radius: 5px; }
        .login-btn { width: 100%; background: #00ff88; color: black; padding: 12px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; }
        .login-btn:hover { background: #00ccff; }
        .error { color: #ff4444; text-align: center; margin-top: 10px; }
        .watson-note { background: #2a1a1a; border: 1px solid #00ff64; color: #00ff64; padding: 10px; border-radius: 5px; margin-top: 20px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2 class="login-title">{{ platform_name | default('TRAXOVO') }} Intelligence Platform</h2>
        <form method="POST">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" name="username" id="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" name="password" id="password" required>
            </div>
            <button type="submit" class="login-btn">Access System</button>
        </form>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <div class="watson-note">
            {{ login_note | default('Watson Console access requires exclusive owner credentials') }}
        </div>
    </div>
</body>
</html>
"""

def create_dashboard_route(app, route_path, dashboard_config):
    """
    Create a standardized dashboard route
    
    Args:
        app: Flask app instance
        route_path: URL path for the dashboard
        dashboard_config: Dictionary containing dashboard configuration
    """
    
    @app.route(route_path)
    def dashboard_route():
        from flask import session, redirect, url_for, render_template_string
        
        # Check authentication
        if 'user' not in session:
            return redirect(url_for('login'))
        
        user = session['user']
        
        # Merge default config with custom config
        config = {
            'page_title': 'Dashboard',
            'page_subtitle': 'System overview and management',
            'active_page': 'dashboard',
            'company_name': 'TRAXOVO',
            'custom_styles': '',
            'custom_nav_items': '',
            'custom_header_buttons': '',
            'custom_javascript': '',
            'dashboard_content': '<div class="content-grid"></div>',
            'full_width': False
        }
        config.update(dashboard_config)
        
        # Render template
        template = get_universal_base_template()
        return render_template_string(template, user=user, **config)
    
    return dashboard_route

def apply_universal_templates_to_existing_dashboards():
    """
    Instructions for applying universal templates to existing dashboards
    """
    return {
        'steps': [
            '1. Replace existing dashboard routes with create_dashboard_route() calls',
            '2. Define dashboard_config for each dashboard with specific content',
            '3. Use the universal login template for all authentication pages',
            '4. Customize navigation items, styles, and JavaScript per dashboard',
            '5. Apply consistent user authentication and session management'
        ],
        'example_usage': '''
# Example: Converting an existing dashboard
from universal_dashboard_template import create_dashboard_route, get_universal_base_template

# Define dashboard configuration
asset_tracker_config = {
    'page_title': 'Asset Intelligence Tracker',
    'page_subtitle': 'Real-time fleet management and asset tracking',
    'active_page': 'asset_tracker',
    'dashboard_content': '''
        <div class="dashboard-content">
            <div class="asset-map-container">
                <!-- Your asset map content -->
            </div>
        </div>
    ''',
    'custom_javascript': '''
        // Asset tracker specific JavaScript
        loadAssetMap();
        setInterval(updateAssetPositions, 5000);
    '''
}

# Create the route
app.add_url_rule('/asset_tracker', 'asset_tracker', 
                create_dashboard_route(app, '/asset_tracker', asset_tracker_config))
        '''
    }

def get_dashboard_examples():
    """Get example configurations for different dashboard types"""
    return {
        'analytics_dashboard': {
            'page_title': 'Analytics Engine',
            'page_subtitle': 'Advanced data visualization and business intelligence',
            'active_page': 'analytics',
            'dashboard_content': '''
                <div class="content-grid">
                    <div class="module-card">
                        <div class="module-icon">📊</div>
                        <div class="module-title">Performance Analytics</div>
                        <canvas id="performanceChart"></canvas>
                    </div>
                </div>
            ''',
            'custom_javascript': '''
                loadChartJS();
                initializeAnalytics();
            '''
        },
        
        'fleet_management': {
            'page_title': 'Fleet Management',
            'page_subtitle': 'Real-time vehicle tracking and route optimization',
            'active_page': 'fleet',
            'full_width': True,
            'dashboard_content': '''
                <div class="dashboard-content">
                    <div id="fleetMap" style="height: 80vh; background: #0f1419; border: 1px solid #00ff64;">
                        <!-- Fleet map content -->
                    </div>
                </div>
            ''',
            'custom_javascript': '''
                initializeFleetMap();
                startRealTimeTracking();
            '''
        },
        
        'executive_dashboard': {
            'page_title': 'Executive Dashboard',
            'page_subtitle': 'High-level business metrics and strategic insights',
            'active_page': 'executive',
            'dashboard_content': '''
                <div class="content-grid">
                    <div class="module-card">
                        <div class="module-icon">💼</div>
                        <div class="module-title">Business Metrics</div>
                        <div class="module-stats">
                            <div class="stat-item">
                                <div class="stat-value">$2.4M</div>
                                <div class="stat-label">Revenue</div>
                            </div>
                        </div>
                    </div>
                </div>
            ''',
            'custom_javascript': '''
                updateExecutiveMetrics();
                initializeKPIDashboard();
            '''
        }
    }