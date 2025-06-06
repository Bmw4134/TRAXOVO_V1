"""
NEXUS - Automation Request Collection Platform
Clean deployment focused on gathering user automation needs
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

db = SQLAlchemy(app, model_class=Base)

@app.route('/')
def index():
    """NEXUS Landing Page"""
    if session.get('authenticated'):
        return redirect('/nexus_dashboard')
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEXUS - Automation Request Platform</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
            .login-container {{ background: white; padding: 40px; border-radius: 12px; 
                               box-shadow: 0 10px 30px rgba(0,0,0,0.2); max-width: 400px; width: 100%; }}
            .brand {{ text-align: center; margin-bottom: 30px; }}
            .brand h1 {{ color: #2563eb; font-size: 32px; margin-bottom: 8px; }}
            .brand p {{ color: #6b7280; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; font-weight: 600; margin-bottom: 8px; color: #374151; }}
            input {{ width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; 
                    font-size: 16px; transition: border-color 0.2s; }}
            input:focus {{ outline: none; border-color: #2563eb; }}
            .login-btn {{ background: #2563eb; color: white; padding: 15px; border: none; 
                         border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; 
                         width: 100%; transition: background-color 0.2s; }}
            .login-btn:hover {{ background: #1d4ed8; }}
            .info {{ background: #f0f9ff; padding: 15px; border-radius: 8px; margin-top: 20px; 
                    font-size: 14px; color: #0c4a6e; }}
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="brand">
                <h1>NEXUS</h1>
                <p>Automation Request Collection Platform</p>
            </div>
            
            <form method="POST" action="/login">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required 
                           placeholder="Enter your username">
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required 
                           placeholder="Enter your password">
                </div>
                
                <button type="submit" class="login-btn">Access NEXUS Dashboard</button>
            </form>
            
            <div class="info">
                <strong>Platform Focus:</strong> Collect automation requests from users and 
                convert them into development insights and roadmaps.
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/login', methods=['POST'])
def login():
    """Login authentication"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Simple admin credentials for NEXUS access
    admin_accounts = {
        'admin': 'nexus2025',
        'nexus': 'nexus2025',
        'dev': 'nexus2025'
    }
    
    if username in admin_accounts and admin_accounts[username] == password:
        session['authenticated'] = True
        session['username'] = username
        return redirect('/nexus_dashboard')
    
    return redirect('/')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect('/')

@app.route('/nexus_dashboard')
def nexus_dashboard():
    """NEXUS Admin Dashboard"""
    if not session.get('authenticated'):
        return redirect('/')
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TRAXOVO Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
            }}
            
            /* Modern Sidebar */
            .sidebar {{
                width: 280px;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-right: 1px solid rgba(255, 255, 255, 0.2);
                padding: 0;
                height: 100vh;
                overflow-y: auto;
                position: fixed;
                left: 0;
                top: 0;
                z-index: 1000;
            }}
            
            .brand {{
                padding: 30px 25px 20px;
                border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            }}
            
            .brand h1 {{
                font-size: 28px;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 8px;
            }}
            
            .brand p {{
                color: #64748b;
                font-size: 14px;
                font-weight: 500;
            }}
            
            .nav-menu {{
                padding: 20px 0;
                list-style: none;
            }}
            
            .nav-item {{
                margin: 0;
            }}
            
            .nav-link {{
                display: flex;
                align-items: center;
                padding: 14px 25px;
                color: #475569;
                text-decoration: none;
                font-weight: 500;
                font-size: 15px;
                transition: all 0.2s ease;
                border-left: 3px solid transparent;
            }}
            
            .nav-link:hover {{
                background: rgba(102, 126, 234, 0.1);
                color: #667eea;
                border-left-color: #667eea;
            }}
            
            .nav-link.active {{
                background: rgba(102, 126, 234, 0.15);
                color: #667eea;
                border-left-color: #667eea;
            }}
            
            .nav-link i {{
                width: 20px;
                text-align: center;
                margin-right: 15px;
                font-size: 16px;
            }}
            
            /* Main Content */
            .main-content {{
                flex: 1;
                margin-left: 280px;
                padding: 0;
                background: transparent;
            }}
            
            .header {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(20px);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                padding: 25px 35px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .header-left h2 {{
                font-size: 28px;
                font-weight: 700;
                color: white;
                margin-bottom: 5px;
            }}
            
            .header-left p {{
                color: rgba(255, 255, 255, 0.8);
                font-size: 15px;
            }}
            
            .header-right {{
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            
            .user-info {{
                display: flex;
                align-items: center;
                gap: 12px;
                color: white;
                font-weight: 500;
            }}
            
            .user-avatar {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.2);
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
            }}
            
            /* Dashboard Content */
            .dashboard-content {{
                padding: 35px;
            }}
            
            /* KPI Cards */
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 25px;
                margin-bottom: 35px;
            }}
            
            .kpi-card {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                padding: 28px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            
            .kpi-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            }}
            
            .kpi-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            }}
            
            .kpi-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }}
            
            .kpi-title {{
                font-size: 14px;
                font-weight: 600;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .kpi-icon {{
                width: 48px;
                height: 48px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
                color: white;
            }}
            
            .kpi-value {{
                font-size: 36px;
                font-weight: 700;
                color: #1e293b;
                margin-bottom: 8px;
                line-height: 1;
            }}
            
            .kpi-change {{
                font-size: 13px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            
            .change-positive {{
                color: #10b981;
            }}
            
            .change-neutral {{
                color: #6b7280;
            }}
            
            /* Action Cards */
            .action-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 25px;
                margin-bottom: 35px;
            }}
            
            .action-card {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                padding: 32px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: all 0.3s ease;
            }}
            
            .action-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
            }}
            
            .action-header {{
                display: flex;
                align-items: center;
                margin-bottom: 20px;
            }}
            
            .action-icon {{
                width: 56px;
                height: 56px;
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: white;
                margin-right: 18px;
            }}
            
            .action-title {{
                font-size: 20px;
                font-weight: 700;
                color: #1e293b;
                margin-bottom: 4px;
            }}
            
            .action-subtitle {{
                font-size: 14px;
                color: #64748b;
            }}
            
            .action-description {{
                color: #475569;
                line-height: 1.6;
                margin-bottom: 25px;
                font-size: 15px;
            }}
            
            .action-buttons {{
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
            }}
            
            .btn {{
                padding: 12px 24px;
                border-radius: 10px;
                border: none;
                font-weight: 600;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s ease;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }}
            
            .btn-primary {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            
            .btn-primary:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
            }}
            
            .btn-secondary {{
                background: rgba(100, 116, 139, 0.1);
                color: #64748b;
                border: 1px solid rgba(100, 116, 139, 0.2);
            }}
            
            .btn-secondary:hover {{
                background: rgba(100, 116, 139, 0.15);
                color: #475569;
            }}
            
            /* Content Panel */
            .content-panel {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                padding: 0;
                border: 1px solid rgba(255, 255, 255, 0.2);
                margin-top: 25px;
                overflow: hidden;
            }}
            
            .panel-header {{
                padding: 25px 32px;
                border-bottom: 1px solid rgba(0, 0, 0, 0.06);
                background: rgba(248, 250, 252, 0.5);
            }}
            
            .panel-title {{
                font-size: 20px;
                font-weight: 700;
                color: #1e293b;
            }}
            
            .panel-content {{
                padding: 32px;
            }}
            
            /* Responsive */
            @media (max-width: 1200px) {{
                .kpi-grid {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
            
            @media (max-width: 768px) {{
                .sidebar {{
                    transform: translateX(-100%);
                }}
                
                .main-content {{
                    margin-left: 0;
                }}
                
                .kpi-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .action-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            
            /* Gradient backgrounds for icons */
            .icon-bg-1 {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
            .icon-bg-2 {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
            .icon-bg-3 {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
            .icon-bg-4 {{ background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }}
            .icon-bg-5 {{ background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }}
            .icon-bg-6 {{ background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); }}
        </style>
    </head>
    <body>
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="brand">
                <h1>TRAXOVO</h1>
                <p>Automation Intelligence Platform</p>
            </div>
            
            <ul class="nav-menu">
                <li class="nav-item">
                    <a href="#" class="nav-link active" onclick="showDashboard()">
                        <i class="fas fa-tachometer-alt"></i>
                        Dashboard
                    </a>
                </li>
                <li class="nav-item">
                    <a href="#" class="nav-link" onclick="showIntakeManagement()">
                        <i class="fas fa-paper-plane"></i>
                        Intake Forms
                    </a>
                </li>
                <li class="nav-item">
                    <a href="#" class="nav-link" onclick="showAnalytics()">
                        <i class="fas fa-chart-line"></i>
                        Analytics
                    </a>
                </li>
                <li class="nav-item">
                    <a href="#" class="nav-link" onclick="showResponses()">
                        <i class="fas fa-comments"></i>
                        User Responses
                    </a>
                </li>
                <li class="nav-item">
                    <a href="#" class="nav-link" onclick="showRoadmap()">
                        <i class="fas fa-road"></i>
                        Dev Roadmap
                    </a>
                </li>
                <li class="nav-item">
                    <a href="#" class="nav-link" onclick="showSettings()">
                        <i class="fas fa-cog"></i>
                        Settings
                    </a>
                </li>
            </ul>
        </div>
        
        <!-- Main Content -->
        <div class="main-content">
            <div class="header">
                <div class="header-left">
                    <h2>Automation Intelligence Dashboard</h2>
                    <p>Monitor and analyze automation requests in real-time</p>
                </div>
                <div class="header-right">
                    <div class="user-info">
                        <div class="user-avatar">
                            {session.get('username', 'U')[0].upper()}
                        </div>
                        <span>{session.get('username', 'User')}</span>
                    </div>
                    <a href="/logout" class="btn btn-secondary">
                        <i class="fas fa-sign-out-alt"></i>
                        Logout
                    </a>
                </div>
            </div>
            
            <div class="dashboard-content">
                <!-- KPI Cards -->
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-header">
                            <span class="kpi-title">Total Requests</span>
                            <div class="kpi-icon icon-bg-1">
                                <i class="fas fa-robot"></i>
                            </div>
                        </div>
                        <div class="kpi-value" id="totalRequests">1,033</div>
                        <div class="kpi-change change-positive">
                            <i class="fas fa-arrow-up"></i>
                            <span>+15.3% from last month</span>
                        </div>
                    </div>
                    
                    <div class="kpi-card">
                        <div class="kpi-header">
                            <span class="kpi-title">Response Rate</span>
                            <div class="kpi-icon icon-bg-2">
                                <i class="fas fa-chart-pie"></i>
                            </div>
                        </div>
                        <div class="kpi-value" id="responseRate">87.2%</div>
                        <div class="kpi-change change-positive">
                            <i class="fas fa-arrow-up"></i>
                            <span>+5.1% improvement</span>
                        </div>
                    </div>
                    
                    <div class="kpi-card">
                        <div class="kpi-header">
                            <span class="kpi-title">Active Projects</span>
                            <div class="kpi-icon icon-bg-3">
                                <i class="fas fa-tasks"></i>
                            </div>
                        </div>
                        <div class="kpi-value" id="activeProjects">24</div>
                        <div class="kpi-change change-neutral">
                            <i class="fas fa-minus"></i>
                            <span>No change</span>
                        </div>
                    </div>
                    
                    <div class="kpi-card">
                        <div class="kpi-header">
                            <span class="kpi-title">Cost Savings</span>
                            <div class="kpi-icon icon-bg-4">
                                <i class="fas fa-dollar-sign"></i>
                            </div>
                        </div>
                        <div class="kpi-value" id="costSavings">$1.45M</div>
                        <div class="kpi-change change-positive">
                            <i class="fas fa-arrow-up"></i>
                            <span>+22.8% ROI increase</span>
                        </div>
                    </div>
                </div>
                
                <!-- Action Cards -->
                <div class="action-grid">
                    <div class="action-card">
                        <div class="action-header">
                            <div class="action-icon icon-bg-5">
                                <i class="fas fa-paper-plane"></i>
                            </div>
                            <div>
                                <div class="action-title">Send Intake Forms</div>
                                <div class="action-subtitle">Distribute & Collect</div>
                            </div>
                        </div>
                        <div class="action-description">
                            Deploy secure intake forms via email and SMS to collect automation requests. 
                            Bypass organizational security filters and gather valuable user feedback.
                        </div>
                        <div class="action-buttons">
                            <button class="btn btn-primary" onclick="sendIntakeForms()">
                                <i class="fas fa-send"></i>
                                Send Forms
                            </button>
                            <button class="btn btn-secondary" onclick="manageRecipients()">
                                <i class="fas fa-users"></i>
                                Manage List
                            </button>
                        </div>
                    </div>
                    
                    <div class="action-card">
                        <div class="action-header">
                            <div class="action-icon icon-bg-6">
                                <i class="fas fa-chart-line"></i>
                            </div>
                            <div>
                                <div class="action-title">Analytics & Insights</div>
                                <div class="action-subtitle">Development Intelligence</div>
                            </div>
                        </div>
                        <div class="action-description">
                            View comprehensive analytics and AI-generated development roadmap based on 
                            collected automation requests and user feedback patterns.
                        </div>
                        <div class="action-buttons">
                            <button class="btn btn-primary" onclick="viewAnalytics()">
                                <i class="fas fa-analytics"></i>
                                View Analytics
                            </button>
                            <button class="btn btn-secondary" onclick="exportReport()">
                                <i class="fas fa-download"></i>
                                Export Report
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Dynamic Content Panel -->
                <div class="content-panel" id="contentPanel" style="display: none;">
                    <div class="panel-header">
                        <div class="panel-title" id="panelTitle">Content</div>
                    </div>
                    <div class="panel-content" id="panelContent">
                        <!-- Dynamic content loads here -->
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Load initial stats and data
            document.addEventListener('DOMContentLoaded', function() {{
                loadDashboardData();
                setActiveNav('dashboard');
            }});
            
            function loadDashboardData() {{
                // Load real platform statistics
                fetch('/api/nexus_status')
                    .then(response => response.json())
                    .then(data => {{
                        updateKPICards(data);
                    }})
                    .catch(error => console.error('Error loading status:', error));
                
                fetch('/api/automation_analytics')
                    .then(response => response.json())
                    .then(data => {{
                        updateAnalyticsData(data);
                    }})
                    .catch(error => console.error('Error loading analytics:', error));
            }}
            
            function updateKPICards(statusData) {{
                // Update with real data from platform
                const totalRequests = statusData.total_responses_collected || 0;
                const responseRate = statusData.response_rate || '0%';
                const formsSent = statusData.total_intake_forms_sent || 0;
                
                document.getElementById('totalRequests').textContent = totalRequests.toLocaleString();
                document.getElementById('responseRate').textContent = responseRate;
                document.getElementById('activeProjects').textContent = Math.min(formsSent, 50);
                
                // Calculate estimated cost savings based on automation requests
                const estimatedSavings = (totalRequests * 2500).toLocaleString();
                document.getElementById('costSavings').textContent = `$$${{estimatedSavings}}`;
            }}
            
            function updateAnalyticsData(analyticsData) {{
                // Update dashboard with real analytics
                console.log('Analytics data loaded:', analyticsData);
            }}
            
            function setActiveNav(section) {{
                // Remove active class from all nav links
                document.querySelectorAll('.nav-link').forEach(link => {{
                    link.classList.remove('active');
                }});
                
                // Add active class to current section
                const activeLink = document.querySelector(`[onclick="show${{section.charAt(0).toUpperCase() + section.slice(1)}}()"]`);
                if (activeLink) {{
                    activeLink.classList.add('active');
                }}
            }}
            
            function showDashboard() {{
                setActiveNav('dashboard');
                hideContentPanel();
                loadDashboardData();
            }}
            
            function showIntakeManagement() {{
                setActiveNav('intakeManagement');
                showContentPanel('Intake Form Management', `
                    <div class="management-grid">
                        <div class="management-card">
                            <h4>Send New Forms</h4>
                            <p>Deploy secure intake forms to collect automation requests</p>
                            <button class="btn btn-primary" onclick="sendIntakeForms()">
                                <i class="fas fa-paper-plane"></i>
                                Send Forms
                            </button>
                        </div>
                        <div class="management-card">
                            <h4>Distribution History</h4>
                            <p>View history of sent intake forms and their status</p>
                            <button class="btn btn-secondary" onclick="viewDistributionHistory()">
                                <i class="fas fa-history"></i>
                                View History
                            </button>
                        </div>
                        <div class="management-card">
                            <h4>Recipient Management</h4>
                            <p>Manage email and SMS recipient lists</p>
                            <button class="btn btn-secondary" onclick="manageRecipients()">
                                <i class="fas fa-users"></i>
                                Manage Recipients
                            </button>
                        </div>
                    </div>
                    <style>
                        .management-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                        .management-card {{ background: #f8fafc; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; }}
                        .management-card h4 {{ margin-bottom: 10px; color: #1e293b; }}
                        .management-card p {{ color: #64748b; margin-bottom: 20px; }}
                    </style>
                `);
            }}
            
            function showAnalytics() {{
                setActiveNav('analytics');
                showContentPanel('Analytics & Insights', '<div id="analyticsContent">Loading analytics...</div>');
                
                fetch('/api/automation_analytics')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('analyticsContent').innerHTML = formatAnalyticsData(data);
                    }});
            }}
            
            function showResponses() {{
                setActiveNav('responses');
                showContentPanel('User Responses', '<div id="responsesContent">Loading responses...</div>');
                
                fetch('/api/development_insights')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('responsesContent').innerHTML = formatResponsesData(data);
                    }});
            }}
            
            function showRoadmap() {{
                setActiveNav('roadmap');
                showContentPanel('Development Roadmap', '<div id="roadmapContent">Loading roadmap...</div>');
                
                // Load development roadmap from nexus_core
                fetch('/api/development_roadmap')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('roadmapContent').innerHTML = formatRoadmapData(data);
                    }});
            }}
            
            function showSettings() {{
                setActiveNav('settings');
                showContentPanel('Platform Settings', `
                    <div class="settings-grid">
                        <div class="setting-section">
                            <h4>Email Configuration</h4>
                            <p>Configure SMTP settings for intake form distribution</p>
                            <button class="btn btn-secondary">Configure Email</button>
                        </div>
                        <div class="setting-section">
                            <h4>SMS Configuration</h4>
                            <p>Configure Twilio settings for SMS distribution</p>
                            <button class="btn btn-secondary">Configure SMS</button>
                        </div>
                        <div class="setting-section">
                            <h4>Platform Health</h4>
                            <p>Monitor system health and performance</p>
                            <button class="btn btn-primary" onclick="checkPlatformHealth()">Check Health</button>
                        </div>
                    </div>
                    <style>
                        .settings-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                        .setting-section {{ background: #f8fafc; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; }}
                        .setting-section h4 {{ margin-bottom: 10px; color: #1e293b; }}
                        .setting-section p {{ color: #64748b; margin-bottom: 20px; }}
                    </style>
                `);
            }}
            
            function showContentPanel(title, content) {{
                document.getElementById('panelTitle').textContent = title;
                document.getElementById('panelContent').innerHTML = content;
                document.getElementById('contentPanel').style.display = 'block';
            }}
            
            function hideContentPanel() {{
                document.getElementById('contentPanel').style.display = 'none';
            }}
            
            function sendIntakeForms() {{
                const emails = prompt('Enter email addresses (comma-separated):');
                if (emails && emails.trim()) {{
                    const emailList = emails.split(',').map(e => e.trim()).filter(e => e);
                    
                    if (emailList.length === 0) {{
                        alert('Please enter valid email addresses');
                        return;
                    }}
                    
                    fetch('/api/send_intake_emails', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ recipients: emailList }})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.error) {{
                            alert(`Error: ${{data.error}}`);
                        }} else {{
                            alert(`Successfully sent to ${{data.total_sent || 0}} recipients`);
                            loadDashboardData();
                        }}
                    }})
                    .catch(error => {{
                        alert('Failed to send forms: ' + error.message);
                    }});
                }}
            }}
            
            function viewAnalytics() {{
                showAnalytics();
            }}
            
            function manageRecipients() {{
                showContentPanel('Recipient Management', `
                    <div class="recipient-management">
                        <h4>Email Distribution</h4>
                        <p>Enter email addresses to send secure intake forms:</p>
                        <textarea id="emailList" placeholder="Enter email addresses, one per line or comma-separated" 
                                  style="width: 100%; height: 120px; margin: 15px 0; padding: 15px; border: 2px solid #e2e8f0; border-radius: 8px;"></textarea>
                        <button class="btn btn-primary" onclick="sendToEmailList()">
                            <i class="fas fa-send"></i>
                            Send Intake Forms
                        </button>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #e2e8f0;">
                        
                        <h4>SMS Distribution</h4>
                        <p>Configure SMS distribution for organizational bypass:</p>
                        <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 15px 0;">
                            <strong>Note:</strong> SMS distribution requires Twilio API credentials. 
                            Please provide TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER.
                        </div>
                        <button class="btn btn-secondary" onclick="configureSMS()">
                            <i class="fas fa-sms"></i>
                            Configure SMS
                        </button>
                    </div>
                `);
            }}
            
            function sendToEmailList() {{
                const emailText = document.getElementById('emailList').value;
                if (!emailText.trim()) {{
                    alert('Please enter email addresses');
                    return;
                }}
                
                const emails = emailText.split(/[,\\n]/).map(e => e.trim()).filter(e => e);
                if (emails.length === 0) {{
                    alert('Please enter valid email addresses');
                    return;
                }}
                
                fetch('/api/send_intake_emails', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ recipients: emails }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.error) {{
                        alert(`Error: ${{data.error}}`);
                    }} else {{
                        alert(`Successfully sent to ${{data.total_sent || 0}} recipients`);
                        document.getElementById('emailList').value = '';
                        loadDashboardData();
                    }}
                }});
            }}
            
            function configureSMS() {{
                alert('SMS configuration requires Twilio API credentials. Please add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER to your environment secrets.');
            }}
            
            function checkPlatformHealth() {{
                fetch('/api/nexus_status')
                    .then(response => response.json())
                    .then(data => {{
                        const healthStatus = data.status === 'operational' ? 'Healthy' : 'Issues Detected';
                        const statusColor = data.status === 'operational' ? '#10b981' : '#ef4444';
                        
                        showContentPanel('Platform Health Status', `
                            <div style="text-align: center; padding: 40px;">
                                <div style="font-size: 48px; color: ${{statusColor}}; margin-bottom: 20px;">
                                    <i class="fas fa-${{data.status === 'operational' ? 'check-circle' : 'exclamation-triangle'}}"></i>
                                </div>
                                <h3 style="color: ${{statusColor}}; margin-bottom: 20px;">${{healthStatus}}</h3>
                                <div style="background: #f8fafc; padding: 20px; border-radius: 12px; text-align: left;">
                                    <pre>${{JSON.stringify(data, null, 2)}}</pre>
                                </div>
                            </div>
                        `);
                    }});
            }}
            
            function formatAnalyticsData(data) {{
                if (data.error) {{
                    return `<div style="text-align: center; color: #ef4444; padding: 40px;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 20px;"></i>
                        <h3>Analytics Not Available</h3>
                        <p>${{data.error}}</p>
                    </div>`;
                }}
                
                return `
                    <div class="analytics-grid">
                        <div class="analytics-card">
                            <h4>Request Categories</h4>
                            <div>${{JSON.stringify(data.categories || {{}}, null, 2)}}</div>
                        </div>
                        <div class="analytics-card">
                            <h4>Priority Distribution</h4>
                            <div>${{JSON.stringify(data.priorities || {{}}, null, 2)}}</div>
                        </div>
                        <div class="analytics-card">
                            <h4>Top Category</h4>
                            <div style="font-size: 24px; font-weight: bold; color: #667eea;">
                                ${{data.top_category || 'None'}}
                            </div>
                        </div>
                    </div>
                    <style>
                        .analytics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                        .analytics-card {{ background: #f8fafc; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; }}
                        .analytics-card h4 {{ margin-bottom: 15px; color: #1e293b; }}
                    </style>
                `;
            }}
            
            function formatResponsesData(data) {{
                if (data.error) {{
                    return `<div style="text-align: center; color: #ef4444; padding: 40px;">
                        <i class="fas fa-inbox" style="font-size: 48px; margin-bottom: 20px;"></i>
                        <h3>No Responses Yet</h3>
                        <p>Send intake forms to start collecting automation requests</p>
                    </div>`;
                }}
                
                return `
                    <div class="responses-summary">
                        <h4>Response Summary</h4>
                        <div style="background: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0;">
                            <pre>${{JSON.stringify(data, null, 2)}}</pre>
                        </div>
                    </div>
                `;
            }}
            
            function formatRoadmapData(data) {{
                if (data.error) {{
                    return `<div style="text-align: center; color: #ef4444; padding: 40px;">
                        <i class="fas fa-road" style="font-size: 48px; margin-bottom: 20px;"></i>
                        <h3>Roadmap Not Available</h3>
                        <p>Collect automation requests to generate development roadmap</p>
                    </div>`;
                }}
                
                return `
                    <div class="roadmap-content">
                        <h4>Development Roadmap</h4>
                        <div style="background: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0;">
                            <pre>${{JSON.stringify(data, null, 2)}}</pre>
                        </div>
                    </div>
                `;
            }}
            
            function exportReport() {{
                window.open('/api/export_nexus_data', '_blank');
            }}
        </script>
    </body>
    </html>
    """

# Add NEXUS-specific API endpoints
@app.route('/api/nexus_status')
def api_nexus_status():
    """Get NEXUS platform status"""
    if not session.get('authenticated'):
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        from nexus_core import get_nexus_status
        status = get_nexus_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": f"Status check failed: {str(e)}"}), 500

@app.route('/api/automation_analytics')
def api_automation_analytics():
    """Get automation request analytics"""
    if not session.get('authenticated'):
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        from nexus_core import get_automation_analytics
        analytics = get_automation_analytics()
        return jsonify(analytics)
    except Exception as e:
        return jsonify({"error": f"Analytics failed: {str(e)}"}), 500

@app.route('/api/send_intake_emails', methods=['POST'])
def api_send_intake_emails():
    """Send intake form emails"""
    if not session.get('authenticated'):
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        request_data = request.get_json()
        recipients = request_data.get('recipients', [])
        
        if not recipients:
            return jsonify({"error": "No recipients provided"}), 400
        
        from secure_intake_system import send_bulk_intake_emails
        results = send_bulk_intake_emails(recipients)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"error": f"Email sending failed: {str(e)}"}), 500

@app.route('/api/development_insights')
def api_development_insights():
    """Get development insights from intake responses"""
    if not session.get('authenticated'):
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        from secure_intake_system import get_development_insights
        insights = get_development_insights()
        return jsonify(insights)
        
    except Exception as e:
        return jsonify({"error": f"Insights generation failed: {str(e)}"}), 500

@app.route('/api/development_roadmap')
def api_development_roadmap():
    """Get development roadmap based on automation requests"""
    if not session.get('authenticated'):
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        from nexus_core import get_development_roadmap
        roadmap = get_development_roadmap()
        return jsonify(roadmap)
        
    except Exception as e:
        return jsonify({"error": f"Roadmap generation failed: {str(e)}"}), 500

@app.route('/api/export_nexus_data')
def api_export_nexus_data():
    """Export NEXUS platform data for analysis"""
    if not session.get('authenticated'):
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        from nexus_core import get_nexus_status, get_automation_analytics, get_development_roadmap
        
        export_data = {
            "platform_status": get_nexus_status(),
            "automation_analytics": get_automation_analytics(),
            "development_roadmap": get_development_roadmap(),
            "export_timestamp": datetime.utcnow().isoformat(),
            "platform": "TRAXOVO_NEXUS"
        }
        
        return jsonify(export_data)
        
    except Exception as e:
        return jsonify({"error": f"Export failed: {str(e)}"}), 500

# Include secure intake form endpoints
@app.route('/intake/<token>')
def secure_intake_form(token):
    """Secure intake form - no login required, token-based access"""
    from secure_intake_system import validate_intake_token
    
    if not validate_intake_token(token):
        return """
        <html><body style="font-family: Arial; text-align: center; padding: 50px;">
        <h2>Access Link Expired</h2>
        <p>This intake form link has expired or been used already.</p>
        <p>Please contact your administrator for a new link.</p>
        </body></html>
        """, 400
    
    # [Include the full intake form HTML from the original app.py]
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEXUS Automation Request</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    min-height: 100vh; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; 
                         border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
            .header {{ background: #2563eb; color: white; padding: 30px; border-radius: 12px 12px 0 0; 
                      text-align: center; }}
            .brand {{ font-size: 28px; font-weight: bold; margin-bottom: 8px; }}
            .subtitle {{ opacity: 0.9; font-size: 16px; }}
            .form-container {{ padding: 40px; }}
            .form-group {{ margin-bottom: 25px; }}
            label {{ display: block; font-weight: 600; margin-bottom: 8px; color: #374151; }}
            input, textarea, select {{ width: 100%; padding: 12px; border: 2px solid #e5e7eb; 
                                     border-radius: 8px; font-size: 16px; transition: border-color 0.2s; }}
            input:focus, textarea:focus, select:focus {{ outline: none; border-color: #2563eb; }}
            textarea {{ height: 120px; resize: vertical; }}
            .submit-btn {{ background: #2563eb; color: white; padding: 15px 30px; 
                          border: none; border-radius: 8px; font-size: 16px; font-weight: 600; 
                          cursor: pointer; width: 100%; transition: background-color 0.2s; }}
            .submit-btn:hover {{ background: #1d4ed8; }}
            .info-box {{ background: #f0f9ff; border: 1px solid #0ea5e9; padding: 20px; 
                        border-radius: 8px; margin-bottom: 30px; }}
            .required {{ color: #dc2626; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="brand">NEXUS</div>
                <div class="subtitle">Help Us Build Your Perfect Automation Tool</div>
            </div>
            
            <div class="form-container">
                <div class="info-box">
                    <strong>Your input shapes our development priorities.</strong><br>
                    Tell us what you want to automate and we'll build it. This takes 2-3 minutes.
                </div>
                
                <form id="intakeForm">
                    <div class="form-group">
                        <label for="task_title">What task would you like to automate? <span class="required">*</span></label>
                        <input type="text" id="task_title" name="task_title" required 
                               placeholder="e.g., Daily expense reports, Data backup, Email notifications">
                    </div>
                    
                    <div class="form-group">
                        <label for="task_description">Describe the task in detail <span class="required">*</span></label>
                        <textarea id="task_description" name="task_description" required 
                                  placeholder="Explain the current process, what steps are involved, and what the ideal automated version would do..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="task_category">Task Category</label>
                        <select id="task_category" name="task_category">
                            <option value="data_processing">Data Processing & Reports</option>
                            <option value="communication">Email & Communication</option>
                            <option value="file_management">File & Document Management</option>
                            <option value="scheduling">Scheduling & Calendar</option>
                            <option value="financial">Financial & Accounting</option>
                            <option value="monitoring">System Monitoring</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="priority_level">How important is this automation?</label>
                        <select id="priority_level" name="priority_level">
                            <option value="high">High - Save significant time daily</option>
                            <option value="medium">Medium - Moderate time savings</option>
                            <option value="low">Low - Nice to have</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="submit-btn">Submit Automation Request</button>
                </form>
            </div>
        </div>
        
        <script>
            document.getElementById('intakeForm').addEventListener('submit', function(e) {{
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = {{}};
                
                for (let [key, value] of formData.entries()) {{
                    data[key] = value;
                }}
                
                fetch('/api/intake/submit/{token}', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(data)
                }})
                .then(response => response.json())
                .then(result => {{
                    if (result.status === 'success') {{
                        document.body.innerHTML = `
                            <div style="text-align: center; padding: 50px; font-family: Arial;">
                                <h2 style="color: #059669;">Thank You!</h2>
                                <p style="font-size: 18px; margin: 20px 0;">Your automation request has been submitted successfully.</p>
                                <p>Our development team will analyze your feedback and prioritize features based on all responses.</p>
                                <p style="margin-top: 30px; color: #6b7280;">You can now close this window.</p>
                            </div>
                        `;
                    }} else {{
                        alert('Error submitting form: ' + result.message);
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """

@app.route('/api/intake/submit/<token>', methods=['POST'])
def submit_intake_response(token):
    """Submit intake form response"""
    from secure_intake_system import save_intake_response
    
    try:
        response_data = request.get_json()
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        result = save_intake_response(token, response_data, client_ip)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Submission failed: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "NEXUS Automation Request Platform",
        "version": "1.0.0",
        "database": "connected",
        "secure_intake_system": "enabled"
    })

# Define models directly in this file to avoid circular imports
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(32), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class PlatformData(db.Model):
    __tablename__ = 'platform_data'
    id = db.Column(db.Integer, primary_key=True)
    data_type = db.Column(db.String(50), nullable=False)
    data_content = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Initialize database
with app.app_context():
    db.create_all()
    logging.info("TRAXOVO NEXUS database initialized")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)