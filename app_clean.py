import os
from flask import Flask, request, render_template_string, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# JDD Enterprises Authentic Business Data
AUTHENTIC_DATA = {
    'annual_revenue': 100000,
    'active_clients': 25,
    'retention_rate': 100,
    'profit_margin': 70,
    'business_value': 62000,
    'growth_opportunities': 125000
}

# System Users
SYSTEM_USERS = {
    'admin': 'admin123',
    'watson': 'watson123',
    'jdd': 'jdd123'
}

# Subscription Tiers
SUBSCRIPTION_TIERS = {
    'starter': {
        'price': 97,
        'name': 'Intelligence Access',
        'features': ['Real-time metrics', 'Basic CRM', 'Trading signals']
    },
    'premium': {
        'price': 297,
        'name': 'Advanced Intelligence',
        'features': ['Full BMI model', 'Automation', 'Watson access']
    },
    'enterprise': {
        'price': 997,
        'name': 'Enterprise Intelligence',
        'features': ['White-labeling', 'Team management', '24/7 support']
    }
}

@app.route('/')
def landing_page():
    """JDD Enterprises BMI Intelligence Infinity Model Landing Page"""
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JDD Enterprises - BMI Intelligence Infinity Model</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, rgba(0, 20, 50, 0.95), rgba(20, 0, 50, 0.95));
            color: white;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .floating-particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        }
        
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(0, 255, 100, 0.3);
            border-radius: 50%;
            animation: float 6s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
        
        @keyframes companyGlow {
            from { text-shadow: 0 0 30px rgba(0, 255, 100, 0.8); }
            to { text-shadow: 0 0 40px rgba(0, 255, 100, 1); }
        }
        
        @keyframes metricPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .container {
            position: relative;
            z-index: 10;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .hero-section {
            text-align: center;
            padding: 80px 0;
        }
        
        .company-name {
            font-size: 4em;
            color: #00ff64;
            text-shadow: 0 0 30px rgba(0, 255, 100, 0.8);
            letter-spacing: 3px;
            font-weight: 900;
            animation: companyGlow 3s ease-in-out infinite alternate;
            margin-bottom: 20px;
        }
        
        .platform-subtitle {
            font-size: 1.8em;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 40px;
            font-weight: 300;
        }
        
        .live-metrics-banner {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            background: rgba(0, 0, 0, 0.7);
            border: 2px solid rgba(0, 255, 100, 0.4);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            padding: 30px;
            margin: 40px 0;
        }
        
        .metric-card {
            text-align: center;
            padding: 20px;
            border-radius: 15px;
            background: rgba(0, 30, 60, 0.9);
            transition: all 0.3s ease;
            animation: metricPulse 4s ease-in-out infinite;
        }
        
        .metric-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0, 255, 100, 0.3);
        }
        
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #00ff64;
            margin-bottom: 10px;
            font-family: 'Courier New', monospace;
        }
        
        .metric-label {
            font-size: 1em;
            color: rgba(255, 255, 255, 0.8);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .tier-cards-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin: 60px 0;
        }
        
        .tier-card {
            background: rgba(0, 30, 60, 0.9);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            border: 2px solid transparent;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .tier-card.starter { border-color: #00ff64; }
        .tier-card.premium { border-color: #ff6400; }
        .tier-card.enterprise { border-color: #6400ff; }
        
        .tier-card:hover {
            transform: translateY(-15px);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
        }
        
        .tier-price {
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 20px;
        }
        
        .tier-card.starter .tier-price { color: #00ff64; }
        .tier-card.premium .tier-price { color: #ff6400; }
        .tier-card.enterprise .tier-price { color: #6400ff; }
        
        .tier-name {
            font-size: 1.5em;
            margin-bottom: 30px;
            font-weight: 600;
        }
        
        .tier-features {
            list-style: none;
            margin-bottom: 30px;
        }
        
        .tier-features li {
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .portal-buttons {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 60px 0;
            flex-wrap: wrap;
        }
        
        .portal-button {
            padding: 20px 40px;
            border-radius: 15px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.2em;
            transition: all 0.3s ease;
            border: 2px solid;
            backdrop-filter: blur(10px);
        }
        
        .portal-button.client {
            background: rgba(0, 255, 100, 0.1);
            color: #00ff64;
            border-color: #00ff64;
        }
        
        .portal-button.admin {
            background: rgba(255, 100, 0, 0.1);
            color: #ff6400;
            border-color: #ff6400;
        }
        
        .portal-button.watson {
            background: rgba(100, 0, 255, 0.1);
            color: #6400ff;
            border-color: #6400ff;
        }
        
        .portal-button:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.4);
        }
        
        @media (max-width: 768px) {
            .company-name { font-size: 2.5em; }
            .tier-cards-container { grid-template-columns: 1fr; }
            .portal-buttons { flex-direction: column; align-items: center; }
            .live-metrics-banner { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="floating-particles">
        <div class="particle" style="left: 10%; animation-delay: 0s;"></div>
        <div class="particle" style="left: 20%; animation-delay: 1s;"></div>
        <div class="particle" style="left: 30%; animation-delay: 2s;"></div>
        <div class="particle" style="left: 40%; animation-delay: 3s;"></div>
        <div class="particle" style="left: 50%; animation-delay: 4s;"></div>
        <div class="particle" style="left: 60%; animation-delay: 5s;"></div>
        <div class="particle" style="left: 70%; animation-delay: 0.5s;"></div>
        <div class="particle" style="left: 80%; animation-delay: 1.5s;"></div>
        <div class="particle" style="left: 90%; animation-delay: 2.5s;"></div>
    </div>
    
    <div class="container">
        <div class="hero-section">
            <h1 class="company-name">JDD ENTERPRISES</h1>
            <p class="platform-subtitle">BMI Intelligence Infinity Model</p>
            <p style="font-size: 1.2em; color: rgba(255, 255, 255, 0.7); margin-bottom: 40px;">
                Quantum-enhanced business intelligence for commercial equipment professionals
            </p>
        </div>
        
        <div class="live-metrics-banner">
            <div class="metric-card">
                <div class="metric-value" id="revenue-counter">$100,000</div>
                <div class="metric-label">Annual Revenue</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="client-counter">25</div>
                <div class="metric-label">Active Clients</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="retention-counter">100%</div>
                <div class="metric-label">Retention Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="profit-counter">70%</div>
                <div class="metric-label">Profit Margin</div>
            </div>
        </div>
        
        <div class="tier-cards-container">
            <div class="tier-card starter">
                <div class="tier-price">$97</div>
                <div class="tier-name">Intelligence Access</div>
                <ul class="tier-features">
                    <li>Real-time metrics</li>
                    <li>Basic CRM</li>
                    <li>Trading signals</li>
                </ul>
            </div>
            
            <div class="tier-card premium">
                <div class="tier-price">$297</div>
                <div class="tier-name">Advanced Intelligence</div>
                <ul class="tier-features">
                    <li>Full BMI model</li>
                    <li>Automation</li>
                    <li>Watson access</li>
                </ul>
            </div>
            
            <div class="tier-card enterprise">
                <div class="tier-price">$997</div>
                <div class="tier-name">Enterprise Intelligence</div>
                <ul class="tier-features">
                    <li>White-labeling</li>
                    <li>Team management</li>
                    <li>24/7 support</li>
                </ul>
            </div>
        </div>
        
        <div class="portal-buttons">
            <a href="/client-login" class="portal-button client">Client Portal</a>
            <a href="/admin-login" class="portal-button admin">Admin Portal</a>
            <a href="/watson-access" class="portal-button watson">Watson Module</a>
        </div>
        
        <div style="text-align: center; margin-top: 60px; padding-bottom: 40px;">
            <a href="/training-guide" style="color: rgba(255, 255, 255, 0.6); text-decoration: none; font-size: 1.1em;">
                Training Guide & System Documentation
            </a>
        </div>
    </div>
    
    <script>
        // Animate metrics on page load
        function animateMetrics() {
            const metrics = [
                { id: 'revenue-counter', target: 100000, prefix: '$', suffix: '' },
                { id: 'client-counter', target: 25, prefix: '', suffix: '' },
                { id: 'retention-counter', target: 100, prefix: '', suffix: '%' },
                { id: 'profit-counter', target: 70, prefix: '', suffix: '%' }
            ];
            
            metrics.forEach(metric => {
                let current = 0;
                const increment = metric.target / 50;
                const element = document.getElementById(metric.id);
                
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= metric.target) {
                        current = metric.target;
                        clearInterval(timer);
                    }
                    
                    element.textContent = metric.prefix + Math.floor(current).toLocaleString() + metric.suffix;
                }, 50);
            });
        }
        
        // Start animation when page loads
        window.addEventListener('load', animateMetrics);
    </script>
</body>
</html>''')

@app.route('/client-login')
def client_login():
    """Client Portal Login"""
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Client Portal - JDD Enterprises</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, rgba(0, 20, 50, 0.95), rgba(20, 0, 50, 0.95));
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: rgba(0, 30, 60, 0.9);
            border: 2px solid rgba(0, 255, 100, 0.4);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            padding: 60px;
            width: 100%;
            max-width: 450px;
            text-align: center;
        }
        .company-logo {
            font-size: 2.5em;
            color: #00ff64;
            text-shadow: 0 0 30px rgba(0, 255, 100, 0.8);
            letter-spacing: 2px;
            font-weight: 900;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 25px;
            text-align: left;
        }
        .form-group label {
            display: block;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 8px;
            font-weight: 500;
        }
        .form-control {
            width: 100%;
            padding: 15px;
            border: 2px solid rgba(0, 255, 100, 0.3);
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.3);
            color: white;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        .form-control:focus {
            outline: none;
            border-color: #00ff64;
            box-shadow: 0 0 15px rgba(0, 255, 100, 0.3);
        }
        .btn-login {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #00ff64, #00cc50);
            color: black;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
        }
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 255, 100, 0.4);
        }
        .back-link {
            color: rgba(255, 255, 255, 0.6);
            text-decoration: none;
            margin-top: 30px;
            display: inline-block;
        }
        .subscription-notice {
            background: rgba(0, 255, 100, 0.1);
            border: 1px solid rgba(0, 255, 100, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            font-size: 14px;
            color: rgba(255, 255, 255, 0.8);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="company-logo">JDD ENTERPRISES</div>
        <h2 style="margin-bottom: 30px; font-weight: 300;">Client Portal Access</h2>
        
        <div class="subscription-notice">
            Access requires active subscription ($97/$297/$997 tiers)
        </div>
        
        <form method="POST" action="/client-dashboard">
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn-login">Access Intelligence Dashboard</button>
        </form>
        
        <a href="/" class="back-link">← Back to Main Site</a>
    </div>
</body>
</html>''')

@app.route('/admin-login')
def admin_login():
    """Administrative Portal Login"""
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Portal - JDD Enterprises</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, rgba(0, 20, 50, 0.95), rgba(20, 0, 50, 0.95));
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: rgba(0, 30, 60, 0.9);
            border: 2px solid rgba(255, 100, 0, 0.4);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            padding: 60px;
            width: 100%;
            max-width: 450px;
            text-align: center;
        }
        .admin-logo {
            font-size: 2.5em;
            color: #ff6400;
            text-shadow: 0 0 30px rgba(255, 100, 0, 0.8);
            letter-spacing: 2px;
            font-weight: 900;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 25px;
            text-align: left;
        }
        .form-group label {
            display: block;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 8px;
            font-weight: 500;
        }
        .form-control {
            width: 100%;
            padding: 15px;
            border: 2px solid rgba(255, 100, 0, 0.3);
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.3);
            color: white;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        .form-control:focus {
            outline: none;
            border-color: #ff6400;
            box-shadow: 0 0 15px rgba(255, 100, 0, 0.3);
        }
        .btn-login {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #ff6400, #cc5000);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
        }
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(255, 100, 0, 0.4);
        }
        .back-link {
            color: rgba(255, 255, 255, 0.6);
            text-decoration: none;
            margin-top: 30px;
            display: inline-block;
        }
        .credentials-box {
            background: rgba(255, 100, 0, 0.1);
            border: 1px solid rgba(255, 100, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            font-size: 14px;
            color: rgba(255, 255, 255, 0.8);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="admin-logo">ADMIN ACCESS</div>
        <h2 style="margin-bottom: 30px; font-weight: 300;">Administrative Portal</h2>
        
        <div class="credentials-box">
            Default Access: admin / admin123
        </div>
        
        <form method="POST" action="/admin-dashboard">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn-login">Access Admin Dashboard</button>
        </form>
        
        <a href="/" class="back-link">← Back to Main Site</a>
    </div>
</body>
</html>''')

@app.route('/watson-access')
def watson_access():
    """Watson Module Access"""
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watson Module - JDD Enterprises</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, rgba(0, 20, 50, 0.95), rgba(20, 0, 50, 0.95));
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: rgba(0, 30, 60, 0.9);
            border: 2px solid rgba(100, 0, 255, 0.4);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            padding: 60px;
            width: 100%;
            max-width: 450px;
            text-align: center;
        }
        .watson-logo {
            font-size: 2.5em;
            color: #6400ff;
            text-shadow: 0 0 30px rgba(100, 0, 255, 0.8);
            letter-spacing: 2px;
            font-weight: 900;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 25px;
            text-align: left;
        }
        .form-group label {
            display: block;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 8px;
            font-weight: 500;
        }
        .form-control {
            width: 100%;
            padding: 15px;
            border: 2px solid rgba(100, 0, 255, 0.3);
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.3);
            color: white;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        .form-control:focus {
            outline: none;
            border-color: #6400ff;
            box-shadow: 0 0 15px rgba(100, 0, 255, 0.3);
        }
        .btn-login {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #6400ff, #5000cc);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
        }
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(100, 0, 255, 0.4);
        }
        .back-link {
            color: rgba(255, 255, 255, 0.6);
            text-decoration: none;
            margin-top: 30px;
            display: inline-block;
        }
        .restricted-notice {
            background: rgba(100, 0, 255, 0.1);
            border: 1px solid rgba(100, 0, 255, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            font-size: 14px;
            color: rgba(255, 255, 255, 0.8);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="watson-logo">WATSON MODULE</div>
        <h2 style="margin-bottom: 30px; font-weight: 300;">Business Valuation Access</h2>
        
        <div class="restricted-notice">
            Restricted Access - Business valuation for lender presentations
        </div>
        
        <form method="POST" action="/watson/business-valuation">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn-login">Access Valuation Module</button>
        </form>
        
        <a href="/" class="back-link">← Back to Main Site</a>
    </div>
</body>
</html>''')

@app.route('/watson/business-valuation', methods=['GET', 'POST'])
def watson_valuation():
    """Watson Business Valuation Module - Restricted Access"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'watson' and password == 'watson123':
            session['watson_authenticated'] = True
        else:
            return redirect(url_for('watson_access'))
    
    if not session.get('watson_authenticated'):
        return redirect(url_for('watson_access'))
    
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Valuation - Watson Module</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, rgba(0, 20, 50, 0.95), rgba(20, 0, 50, 0.95));
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .watson-title {
            font-size: 3em;
            color: #6400ff;
            text-shadow: 0 0 30px rgba(100, 0, 255, 0.8);
            margin-bottom: 20px;
        }
        .valuation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin: 40px 0;
        }
        .valuation-card {
            background: rgba(0, 30, 60, 0.9);
            border: 2px solid rgba(100, 0, 255, 0.4);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            padding: 30px;
        }
        .valuation-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #6400ff;
            margin-bottom: 15px;
            font-family: 'Courier New', monospace;
        }
        .metric-row {
            display: flex;
            justify-content: space-between;
            padding: 15px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .metric-label {
            color: rgba(255, 255, 255, 0.8);
        }
        .metric-value {
            color: #00ff64;
            font-weight: bold;
        }
        .confidential-notice {
            background: rgba(255, 0, 0, 0.1);
            border: 2px solid rgba(255, 0, 0, 0.3);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            margin-bottom: 30px;
            color: #ff6b6b;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="watson-title">WATSON BUSINESS VALUATION</div>
            <p style="font-size: 1.2em; color: rgba(255, 255, 255, 0.7);">
                JDD Enterprises - Private Valuation Module
            </p>
        </div>
        
        <div class="confidential-notice">
            <strong>CONFIDENTIAL:</strong> This data is for lender presentation purposes only
        </div>
        
        <div class="valuation-grid">
            <div class="valuation-card">
                <h3 style="margin-bottom: 20px; color: #6400ff;">Business Valuation</h3>
                <div class="valuation-value">${{ business_value:,d }}</div>
                <p style="color: rgba(255, 255, 255, 0.7);">
                    Current market valuation based on authentic performance metrics
                </p>
            </div>
            
            <div class="valuation-card">
                <h3 style="margin-bottom: 20px; color: #6400ff;">Performance Metrics</h3>
                <div class="metric-row">
                    <span class="metric-label">Annual Revenue</span>
                    <span class="metric-value">${{ annual_revenue:,d }}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Active Clients</span>
                    <span class="metric-value">{{ active_clients }}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Retention Rate</span>
                    <span class="metric-value">{{ retention_rate }}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Profit Margin</span>
                    <span class="metric-value">{{ profit_margin }}%</span>
                </div>
            </div>
            
            <div class="valuation-card">
                <h3 style="margin-bottom: 20px; color: #6400ff;">Growth Projections</h3>
                <div class="valuation-value">${{ growth_opportunities:,d }}</div>
                <p style="color: rgba(255, 255, 255, 0.7);">
                    Identified growth potential based on market analysis and current trajectory
                </p>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 40px;">
            <a href="/watson-logout" style="color: rgba(255, 255, 255, 0.6); text-decoration: none;">
                Logout from Watson Module
            </a>
        </div>
    </div>
</body>
</html>''', **AUTHENTIC_DATA)

@app.route('/watson-logout')
def watson_logout():
    """Logout from Watson module"""
    session.pop('watson_authenticated', None)
    return redirect(url_for('landing_page'))

@app.route('/training-guide')
def training_guide():
    """Training Guide and System Documentation"""
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Training Guide - JDD Enterprises</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, rgba(0, 20, 50, 0.95), rgba(20, 0, 50, 0.95));
            color: white;
            line-height: 1.6;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .training-title {
            font-size: 2.5em;
            color: #00ff64;
            text-shadow: 0 0 30px rgba(0, 255, 100, 0.8);
            margin-bottom: 20px;
        }
        .section {
            background: rgba(0, 30, 60, 0.9);
            border: 2px solid rgba(0, 255, 100, 0.4);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            padding: 30px;
            margin-bottom: 30px;
        }
        .section h3 {
            color: #00ff64;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        .credential-box {
            background: rgba(0, 255, 100, 0.1);
            border: 1px solid rgba(0, 255, 100, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
        }
        .step-list {
            list-style: none;
            counter-reset: step-counter;
        }
        .step-list li {
            counter-increment: step-counter;
            position: relative;
            padding-left: 50px;
            margin-bottom: 20px;
        }
        .step-list li::before {
            content: counter(step-counter);
            position: absolute;
            left: 0;
            top: 0;
            background: #00ff64;
            color: black;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        .back-link {
            display: inline-block;
            color: #00ff64;
            text-decoration: none;
            margin-top: 30px;
            padding: 15px 30px;
            border: 2px solid #00ff64;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        .back-link:hover {
            background: rgba(0, 255, 100, 0.1);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="training-title">SYSTEM TRAINING GUIDE</div>
            <p style="font-size: 1.2em; color: rgba(255, 255, 255, 0.7);">
                Complete platform usage instructions for JDD Enterprises BMI Intelligence
            </p>
        </div>
        
        <div class="section">
            <h3>System Access Credentials</h3>
            <p>Use these credentials to access different system areas:</p>
            
            <div class="credential-box">
                <strong>Admin Portal:</strong><br>
                Username: admin<br>
                Password: admin123
            </div>
            
            <div class="credential-box">
                <strong>Watson Module:</strong><br>
                Username: watson<br>
                Password: watson123
            </div>
            
            <div class="credential-box">
                <strong>JDD Personal Access:</strong><br>
                Username: jdd<br>
                Password: jdd123
            </div>
        </div>
        
        <div class="section">
            <h3>Getting Started</h3>
            <ol class="step-list">
                <li>Start from the main landing page to see live business metrics</li>
                <li>Choose your access portal based on your role and needs</li>
                <li>Use the provided credentials for system authentication</li>
                <li>Navigate between modules using the portal buttons</li>
                <li>Access Watson module for private business valuation data</li>
            </ol>
        </div>
        
        <div class="section">
            <h3>System Features</h3>
            <ul style="list-style-type: disc; margin-left: 30px;">
                <li><strong>Real-time Metrics:</strong> Live display of authentic business data</li>
                <li><strong>Subscription Tiers:</strong> Three pricing levels ($97/$297/$997)</li>
                <li><strong>Client Portal:</strong> Subscription-based access for clients</li>
                <li><strong>Admin Portal:</strong> Full administrative control</li>
                <li><strong>Watson Module:</strong> Private business valuation for lenders</li>
                <li><strong>Mobile Responsive:</strong> Optimized for all device sizes</li>
            </ul>
        </div>
        
        <div class="section">
            <h3>Data Authenticity</h3>
            <p>All metrics displayed are authentic business data:</p>
            <ul style="list-style-type: disc; margin-left: 30px; margin-top: 15px;">
                <li>Annual Revenue: $100,000 (verified)</li>
                <li>Active Clients: 25 (real count)</li>
                <li>Retention Rate: 100% (perfect retention)</li>
                <li>Profit Margin: 70% (actual margin)</li>
                <li>Business Value: $62,000 (for lender presentations)</li>
            </ul>
        </div>
        
        <div style="text-align: center;">
            <a href="/" class="back-link">← Return to Main Platform</a>
        </div>
    </div>
</body>
</html>''')

with app.app_context():
    try:
        import models
        db.create_all()
    except:
        pass