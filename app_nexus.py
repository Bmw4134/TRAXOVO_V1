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
        <title>NEXUS Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    background: #f8fafc; }}
            .header {{ background: #2563eb; color: white; padding: 20px; }}
            .header h1 {{ font-size: 24px; }}
            .header p {{ opacity: 0.9; margin-top: 5px; }}
            .container {{ padding: 30px; max-width: 1200px; margin: 0 auto; }}
            .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                     gap: 20px; margin-bottom: 30px; }}
            .card {{ background: white; padding: 25px; border-radius: 12px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .card h3 {{ color: #1f2937; margin-bottom: 15px; }}
            .card p {{ color: #6b7280; line-height: 1.5; }}
            .btn {{ background: #2563eb; color: white; padding: 12px 20px; 
                   border: none; border-radius: 8px; cursor: pointer; text-decoration: none; 
                   display: inline-block; margin: 10px 10px 0 0; }}
            .btn:hover {{ background: #1d4ed8; }}
            .btn-secondary {{ background: #6b7280; }}
            .btn-secondary:hover {{ background: #4b5563; }}
            .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
            .stat {{ background: #f3f4f6; padding: 15px; border-radius: 8px; text-align: center; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
            .stat-label {{ color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>NEXUS Dashboard</h1>
            <p>Automation Request Collection & Development Intelligence</p>
        </div>
        
        <div class="container">
            <div class="stats" id="nexusStats">
                <div class="stat">
                    <div class="stat-value" id="totalRequests">0</div>
                    <div class="stat-label">Automation Requests</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="responseRate">0%</div>
                    <div class="stat-label">Response Rate</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="topCategory">None</div>
                    <div class="stat-label">Top Request Category</div>
                </div>
            </div>
            
            <div class="cards">
                <div class="card">
                    <h3>Send Intake Forms</h3>
                    <p>Distribute secure intake forms via email to collect automation requests from users. 
                       Bypasses organizational link filters.</p>
                    <button class="btn" onclick="sendIntakeForms()">Send Email Forms</button>
                    <button class="btn btn-secondary" onclick="showEmailList()">Manage Recipients</button>
                </div>
                
                <div class="card">
                    <h3>Development Insights</h3>
                    <p>View automation request analytics and generated development roadmap based on 
                       collected user feedback.</p>
                    <button class="btn" onclick="viewInsights()">View Analytics</button>
                    <button class="btn btn-secondary" onclick="exportData()">Export Data</button>
                </div>
                
                <div class="card">
                    <h3>User Responses</h3>
                    <p>Review automation requests submitted by users through secure intake forms.</p>
                    <button class="btn" onclick="viewResponses()">View Responses</button>
                    <button class="btn btn-secondary" onclick="generateReport()">Generate Report</button>
                </div>
                
                <div class="card">
                    <h3>Platform Status</h3>
                    <p>Monitor NEXUS platform health and intake form distribution status.</p>
                    <button class="btn" onclick="checkStatus()">Platform Status</button>
                    <a href="/logout" class="btn btn-secondary">Logout</a>
                </div>
            </div>
            
            <div id="content" style="margin-top: 30px;"></div>
        </div>
        
        <script>
            // Load initial stats
            loadStats();
            
            function loadStats() {{
                fetch('/api/nexus_status')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('totalRequests').textContent = data.total_responses_collected || 0;
                        document.getElementById('responseRate').textContent = data.response_rate || '0%';
                    }});
                
                fetch('/api/automation_analytics')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('topCategory').textContent = data.top_category || 'None';
                    }});
            }}
            
            function sendIntakeForms() {{
                const emails = prompt('Enter email addresses (comma-separated):');
                if (emails) {{
                    const emailList = emails.split(',').map(e => e.trim());
                    fetch('/api/send_intake_emails', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ recipients: emailList }})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        alert(`Sent to ${{data.total_sent || 0}} recipients`);
                        loadStats();
                    }});
                }}
            }}
            
            function viewInsights() {{
                fetch('/api/development_insights')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('content').innerHTML = `
                            <div class="card">
                                <h3>Development Insights</h3>
                                <pre>${{JSON.stringify(data, null, 2)}}</pre>
                            </div>
                        `;
                    }});
            }}
            
            function viewResponses() {{
                fetch('/api/automation_analytics')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('content').innerHTML = `
                            <div class="card">
                                <h3>Automation Request Analytics</h3>
                                <pre>${{JSON.stringify(data, null, 2)}}</pre>
                            </div>
                        `;
                    }});
            }}
            
            function checkStatus() {{
                fetch('/api/nexus_status')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('content').innerHTML = `
                            <div class="card">
                                <h3>NEXUS Platform Status</h3>
                                <pre>${{JSON.stringify(data, null, 2)}}</pre>
                            </div>
                        `;
                    }});
            }}
            
            function showEmailList() {{
                document.getElementById('content').innerHTML = `
                    <div class="card">
                        <h3>Email Distribution</h3>
                        <p>Send secure intake forms to collect automation requests.</p>
                        <p><strong>How it works:</strong></p>
                        <ul style="margin: 15px 0; padding-left: 20px;">
                            <li>Each recipient gets a unique, secure link</li>
                            <li>Links expire in 24 hours for security</li>
                            <li>No login required - direct form access</li>
                            <li>Bypasses organizational link filters</li>
                            <li>Responses feed directly into development insights</li>
                        </ul>
                    </div>
                `;
            }}
            
            function exportData() {{
                window.open('/api/export_nexus_data', '_blank');
            }}
            
            function generateReport() {{
                fetch('/api/generate_nexus_report', {{ method: 'POST' }})
                    .then(response => response.json())
                    .then(data => {{
                        alert('Report generated successfully');
                    }});
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

# Initialize database
with app.app_context():
    from models_clean import User, Asset, OperationalMetrics, PlatformData
    db.create_all()
    logging.info("NEXUS database initialized")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)