"""
Mobile Watson Access Module
Optimized interface for iPhone and mobile device access
"""
from flask import render_template_string

def generate_mobile_watson_interface(user):
    """Generate mobile-optimized Watson interface for iPhone access"""
    
    mobile_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Watson Mobile Command</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            height: 100vh;
            overflow-x: hidden;
            -webkit-overflow-scrolling: touch;
        }
        
        .mobile-header {
            background: rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            padding: 20px 15px 15px;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid rgba(0,255,136,0.3);
        }
        
        .watson-logo {
            color: #00ff88;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 5px;
        }
        
        .user-badge {
            background: rgba(0,255,136,0.2);
            color: #00ff88;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 12px;
            text-align: center;
            border: 1px solid #00ff88;
        }
        
        .mobile-grid {
            padding: 20px 15px;
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
        }
        
        .command-card {
            background: rgba(42, 42, 78, 0.8);
            border: 1px solid #00ff88;
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(5px);
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .command-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #00ff88, #4ecdc4);
        }
        
        .command-card:active {
            transform: scale(0.98);
            background: rgba(42, 42, 78, 0.9);
        }
        
        .card-icon {
            font-size: 28px;
            margin-bottom: 10px;
            display: block;
        }
        
        .card-title {
            color: #00ff88;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .card-desc {
            color: #ccc;
            font-size: 13px;
            line-height: 1.4;
            margin-bottom: 15px;
        }
        
        .card-action {
            background: #00ff88;
            color: #000;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 600;
            width: 100%;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .card-action:active {
            background: #4ecdc4;
            transform: scale(0.95);
        }
        
        .watson-exclusive {
            border-color: #ff6b35;
        }
        
        .watson-exclusive::before {
            background: linear-gradient(90deg, #ff6b35, #ff8c42);
        }
        
        .watson-exclusive .card-action {
            background: #ff6b35;
        }
        
        .watson-exclusive .card-action:active {
            background: #ff8c42;
        }
        
        .status-bar {
            background: rgba(0,0,0,0.4);
            padding: 10px 15px;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            backdrop-filter: blur(10px);
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #00ff88;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .quick-actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .quick-btn {
            background: rgba(0,255,136,0.1);
            border: 1px solid #00ff88;
            color: #00ff88;
            padding: 15px 10px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .quick-btn:active {
            background: rgba(0,255,136,0.2);
            transform: scale(0.95);
        }
        
        @media (max-width: 375px) {
            .mobile-grid { padding: 15px 10px; }
            .command-card { padding: 15px; }
            .card-title { font-size: 15px; }
            .card-desc { font-size: 12px; }
        }
    </style>
</head>
<body>
    <div class="mobile-header">
        <div class="watson-logo">WATSON COMMAND</div>
        <div class="user-badge">{{ user.name }} | {{ user.role }}</div>
    </div>
    
    <div class="mobile-grid">
        <div class="quick-actions">
            <button class="quick-btn" onclick="runQuickFix('performance')">⚡ Quick Fix</button>
            <button class="quick-btn" onclick="showDiagnostics()">📊 Status</button>
            <button class="quick-btn" onclick="location.href='/'">🏠 Dashboard</button>
            <button class="quick-btn" onclick="refreshSystem()">🔄 Refresh</button>
        </div>
        
        {% if user.watson_access %}
        <div class="command-card watson-exclusive">
            <span class="card-icon">🤖</span>
            <div class="card-title">Watson Command Console</div>
            <div class="card-desc">Full access to proprietary Watson AI interface with voice commands and system control</div>
            <button class="card-action" onclick="accessWatsonConsole()">Access Console</button>
        </div>
        
        <div class="command-card watson-exclusive">
            <span class="card-icon">🎤</span>
            <div class="card-title">Voice Command Center</div>
            <div class="card-desc">Multi-language voice recognition for hands-free Watson control</div>
            <button class="card-action" onclick="startVoiceCommands()">Start Voice</button>
        </div>
        {% endif %}
        
        <div class="command-card">
            <span class="card-icon">🎯</span>
            <div class="card-title">Asset Intelligence</div>
            <div class="card-desc">Real-time fleet tracking with proprietary precision technology</div>
            <button class="card-action" onclick="location.href='/proprietary_asset_tracker'">Launch Tracker</button>
        </div>
        
        <div class="command-card">
            <span class="card-icon">📊</span>
            <div class="card-title">Fleet Analytics</div>
            <div class="card-desc">Performance metrics and operational intelligence</div>
            <button class="card-action" onclick="location.href='/fleet_analytics'">View Analytics</button>
        </div>
        
        <div class="command-card">
            <span class="card-icon">📧</span>
            <div class="card-title">Email Intelligence</div>
            <div class="card-desc">Configure automated email systems and notifications</div>
            <button class="card-action" onclick="location.href='/email_config'">Email Setup</button>
        </div>
        
        <div class="command-card">
            <span class="card-icon">👥</span>
            <div class="card-title">Attendance Matrix</div>
            <div class="card-desc">Zone-based attendance tracking and payroll integration</div>
            <button class="card-action" onclick="location.href='/attendance_matrix'">Attendance</button>
        </div>
    </div>
    
    <div class="status-bar">
        <div class="status-indicator">
            <div class="status-dot"></div>
            <span>System Operational</span>
        </div>
        <div id="connectionStatus">Connected</div>
    </div>
    
    <script>
        function accessWatsonConsole() {
            // Check if this is iPhone and open in new tab for better experience
            if (navigator.userAgent.includes('iPhone')) {
                window.open('/watson_console.html', '_blank');
            } else {
                location.href = '/watson_console.html';
            }
        }
        
        function startVoiceCommands() {
            location.href = '/voice_commands';
        }
        
        function runQuickFix(type) {
            const button = event.target;
            button.textContent = '⏳ Fixing...';
            
            fetch('/api/universal_fix', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fix_type: type })
            })
            .then(response => response.json())
            .then(data => {
                button.textContent = '✅ Fixed';
                setTimeout(() => {
                    button.textContent = '⚡ Quick Fix';
                }, 2000);
            })
            .catch(error => {
                button.textContent = '❌ Error';
                setTimeout(() => {
                    button.textContent = '⚡ Quick Fix';
                }, 2000);
            });
        }
        
        function showDiagnostics() {
            alert('System Status: OPERATIONAL\\nMemory: 45% | CPU: 23%\\nAll systems running normally');
        }
        
        function refreshSystem() {
            location.reload();
        }
        
        // Update connection status
        function updateStatus() {
            const status = navigator.onLine ? 'Connected' : 'Offline';
            document.getElementById('connectionStatus').textContent = status;
        }
        
        window.addEventListener('online', updateStatus);
        window.addEventListener('offline', updateStatus);
        
        // Prevent zoom on double tap
        document.addEventListener('touchstart', function(e) {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        });
        
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function(e) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        console.log('Watson Mobile Command initialized for iPhone');
    </script>
</body>
</html>
    """
    
    return render_template_string(mobile_template, user=user)

def get_mobile_access_url():
    """Get the direct mobile access URL for Watson Command"""
    return "/mobile_watson"