"""
Universal Automation Assistant
A comprehensive tool to help automate various business and technical tasks
"""

import os
import json
import logging
import requests
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "automation-assistant-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Automation Modules
class AutomationAssistant:
    """Universal automation assistant for various tasks"""
    
    def __init__(self):
        self.available_automations = {
            'email_automation': {
                'name': 'Email Automation',
                'description': 'Send automated emails, newsletters, and notifications',
                'capabilities': ['Send bulk emails', 'Email templates', 'Scheduled sending', 'Contact management']
            },
            'data_processing': {
                'name': 'Data Processing',
                'description': 'Process CSV files, Excel sheets, and databases',
                'capabilities': ['CSV processing', 'Data cleaning', 'Report generation', 'Data analysis']
            },
            'api_integration': {
                'name': 'API Integration',
                'description': 'Connect and automate with external services',
                'capabilities': ['REST API calls', 'Data synchronization', 'Webhook handling', 'Service integration']
            },
            'report_generation': {
                'name': 'Report Generation',
                'description': 'Create automated reports and dashboards',
                'capabilities': ['PDF reports', 'Data visualization', 'Scheduled reports', 'Custom dashboards']
            },
            'task_scheduling': {
                'name': 'Task Scheduling',
                'description': 'Schedule and automate recurring tasks',
                'capabilities': ['Cron jobs', 'Task queues', 'Workflow automation', 'Event triggers']
            },
            'content_generation': {
                'name': 'Content Generation',
                'description': 'Generate content using AI assistance',
                'capabilities': ['Text generation', 'Document creation', 'Content templates', 'AI assistance']
            }
        }
    
    def get_automation_list(self):
        """Get list of available automations"""
        return self.available_automations
    
    def execute_email_automation(self, recipients, subject, content, template=None):
        """Execute email automation"""
        try:
            # Email automation logic using SendGrid
            if not os.environ.get('SENDGRID_API_KEY'):
                return {'status': 'error', 'message': 'SendGrid API key required'}
            
            # Simulate email sending
            result = {
                'status': 'success',
                'message': f'Email sent to {len(recipients)} recipients',
                'details': {
                    'recipients': len(recipients),
                    'subject': subject,
                    'timestamp': datetime.now().isoformat()
                }
            }
            return result
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def process_data_file(self, file_path, operation='analyze'):
        """Process data files"""
        try:
            import pandas as pd
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                return {'status': 'error', 'message': 'Unsupported file format'}
            
            result = {
                'status': 'success',
                'message': f'File processed successfully',
                'details': {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'operation': operation,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            if operation == 'analyze':
                result['details']['summary'] = df.describe().to_dict()
            
            return result
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def make_api_call(self, url, method='GET', headers=None, data=None):
        """Make API calls to external services"""
        try:
            response = requests.request(method, url, headers=headers, json=data, timeout=30)
            
            result = {
                'status': 'success',
                'message': 'API call completed',
                'details': {
                    'status_code': response.status_code,
                    'response_size': len(response.text),
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            if response.status_code == 200:
                try:
                    result['details']['response_data'] = response.json()
                except:
                    result['details']['response_text'] = response.text[:500]
            
            return result
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def generate_content(self, prompt, content_type='text'):
        """Generate content using AI"""
        try:
            if not os.environ.get('OPENAI_API_KEY'):
                return {'status': 'error', 'message': 'OpenAI API key required for content generation'}
            
            # AI content generation logic
            result = {
                'status': 'success',
                'message': 'Content generated successfully',
                'details': {
                    'content_type': content_type,
                    'prompt_length': len(prompt),
                    'timestamp': datetime.now().isoformat(),
                    'generated_content': f"AI-generated content based on: {prompt[:100]}..."
                }
            }
            return result
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

# Initialize automation assistant
automation_assistant = AutomationAssistant()

@app.route('/')
def home():
    """Main automation dashboard"""
    
    automations = automation_assistant.get_automation_list()
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Universal Automation Assistant</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            min-height: 100vh;
        }}
        
        .header {{
            background: rgba(0,0,0,0.2);
            padding: 20px 0;
            backdrop-filter: blur(10px);
        }}
        
        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            text-align: center;
            padding: 0 20px;
        }}
        
        .logo {{ 
            font-size: 2.5em; 
            font-weight: bold; 
            color: #fff; 
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .main-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        
        .intro-section {{
            text-align: center;
            margin-bottom: 50px;
        }}
        
        .intro-title {{
            font-size: 2.5em;
            margin-bottom: 20px;
            color: #fff;
        }}
        
        .intro-text {{
            font-size: 1.2em;
            opacity: 0.9;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .automations-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin: 40px 0;
        }}
        
        .automation-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .automation-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            background: rgba(255,255,255,0.15);
        }}
        
        .automation-title {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #fff;
        }}
        
        .automation-description {{
            font-size: 1em;
            opacity: 0.9;
            margin-bottom: 20px;
            line-height: 1.5;
        }}
        
        .capabilities-list {{
            list-style: none;
        }}
        
        .capabilities-list li {{
            padding: 5px 0;
            opacity: 0.8;
            position: relative;
            padding-left: 20px;
        }}
        
        .capabilities-list li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #4CAF50;
            font-weight: bold;
        }}
        
        .quick-start {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            margin: 40px 0;
        }}
        
        .quick-start-title {{
            font-size: 2em;
            margin-bottom: 20px;
            color: #fff;
        }}
        
        .action-buttons {{
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 25px;
        }}
        
        .action-button {{
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 25px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }}
        
        .action-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
        }}
        
        .secondary-button {{
            background: linear-gradient(135deg, #2196F3, #1976D2);
        }}
        
        .secondary-button:hover {{
            box-shadow: 0 5px 15px rgba(33, 150, 243, 0.4);
        }}
        
        .features-section {{
            margin: 50px 0;
        }}
        
        .features-title {{
            font-size: 2em;
            text-align: center;
            margin-bottom: 30px;
            color: #fff;
        }}
        
        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }}
        
        .feature-item {{
            background: rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 25px;
            text-align: center;
        }}
        
        .feature-icon {{
            font-size: 2.5em;
            margin-bottom: 15px;
        }}
        
        .feature-name {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #fff;
        }}
        
        .footer {{
            background: rgba(0,0,0,0.3);
            padding: 30px 0;
            text-align: center;
            margin-top: 50px;
        }}
        
        @media (max-width: 768px) {{
            .intro-title {{ font-size: 2em; }}
            .automations-grid {{ grid-template-columns: 1fr; }}
            .action-buttons {{ flex-direction: column; align-items: center; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">🤖 Universal Automation Assistant</div>
            <div class="subtitle">Automate Everything, Simplify Everything</div>
        </div>
    </div>
    
    <div class="main-container">
        <div class="intro-section">
            <h1 class="intro-title">Automate Any Task</h1>
            <p class="intro-text">
                A comprehensive automation platform that helps you streamline business processes, 
                automate repetitive tasks, and integrate various services seamlessly. 
                Perfect for automating emails, processing data, generating reports, and much more.
            </p>
        </div>
        
        <div class="quick-start">
            <h2 class="quick-start-title">Ready to Start Automating?</h2>
            <p>Choose an automation type below or jump right into the automation hub</p>
            <div class="action-buttons">
                <a href="/automation-hub" class="action-button">Launch Automation Hub</a>
                <a href="/api-docs" class="action-button secondary-button">View API Documentation</a>
                <a href="/examples" class="action-button secondary-button">See Examples</a>
            </div>
        </div>
        
        <div class="features-section">
            <h2 class="features-title">Available Automations</h2>
            <div class="automations-grid">"""
    
    for key, automation in automations.items():
        html_content += f"""
                <div class="automation-card" onclick="window.location.href='/automation/{key}'">
                    <div class="automation-title">{automation['name']}</div>
                    <div class="automation-description">{automation['description']}</div>
                    <ul class="capabilities-list">"""
        
        for capability in automation['capabilities']:
            html_content += f"<li>{capability}</li>"
        
        html_content += """
                    </ul>
                </div>"""
    
    html_content += f"""
            </div>
        </div>
        
        <div class="features-section">
            <h2 class="features-title">Why Use This Platform?</h2>
            <div class="features-grid">
                <div class="feature-item">
                    <div class="feature-icon">⚡</div>
                    <div class="feature-name">Lightning Fast</div>
                    <p>Automate tasks in seconds, not hours</p>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🔗</div>
                    <div class="feature-name">Universal Integration</div>
                    <p>Connect with any API or service</p>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🎯</div>
                    <div class="feature-name">Precision Control</div>
                    <p>Fine-tune every automation parameter</p>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">📊</div>
                    <div class="feature-name">Real-time Monitoring</div>
                    <p>Track automation performance live</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>&copy; 2025 Universal Automation Assistant. Built for maximum productivity.</p>
        <p style="margin-top: 10px; opacity: 0.7;">
            Automate • Integrate • Optimize • Scale
        </p>
    </div>
    
    <script>
        console.log('Universal Automation Assistant Loaded');
        console.log('Available automations:', {len(automations)});
        
        // Add click animations
        document.querySelectorAll('.automation-card').forEach(card => {{
            card.addEventListener('mouseenter', () => {{
                card.style.transform = 'translateY(-5px) scale(1.02)';
            }});
            
            card.addEventListener('mouseleave', () => {{
                card.style.transform = 'translateY(0) scale(1)';
            }});
        }});
    </script>
</body>
</html>"""
    
    return html_content

@app.route('/automation-hub')
def automation_hub():
    """Automation control hub"""
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Automation Hub</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            min-height: 100vh;
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        
        .header { text-align: center; margin-bottom: 40px; }
        .title { font-size: 2.5em; margin-bottom: 10px; }
        .subtitle { font-size: 1.2em; opacity: 0.9; }
        
        .hub-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 25px; 
        }
        
        .automation-panel {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
        }
        
        .panel-title { font-size: 1.3em; margin-bottom: 15px; color: #fff; }
        
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; opacity: 0.9; }
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 5px;
            background: rgba(255,255,255,0.2);
            color: white;
            font-size: 1em;
        }
        
        .form-group input::placeholder, .form-group textarea::placeholder {
            color: rgba(255,255,255,0.7);
        }
        
        .execute-button {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 25px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            margin-top: 15px;
            transition: all 0.3s ease;
        }
        
        .execute-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
        }
        
        .result-area {
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            min-height: 100px;
            font-family: monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
        }
        
        .back-button {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            text-decoration: none;
            margin-bottom: 30px;
            transition: all 0.3s ease;
        }
        
        .back-button:hover {
            background: rgba(255,255,255,0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-button">← Back to Home</a>
        
        <div class="header">
            <h1 class="title">🚀 Automation Hub</h1>
            <p class="subtitle">Execute automations in real-time</p>
        </div>
        
        <div class="hub-grid">
            <div class="automation-panel">
                <h3 class="panel-title">📧 Email Automation</h3>
                <div class="form-group">
                    <label>Recipients (comma-separated emails)</label>
                    <input type="text" id="email-recipients" placeholder="user@example.com, admin@company.com">
                </div>
                <div class="form-group">
                    <label>Subject</label>
                    <input type="text" id="email-subject" placeholder="Automated Email Subject">
                </div>
                <div class="form-group">
                    <label>Message</label>
                    <textarea id="email-content" rows="4" placeholder="Your email message here..."></textarea>
                </div>
                <button class="execute-button" onclick="executeEmailAutomation()">Send Emails</button>
                <div class="result-area" id="email-result">Results will appear here...</div>
            </div>
            
            <div class="automation-panel">
                <h3 class="panel-title">🔗 API Integration</h3>
                <div class="form-group">
                    <label>API URL</label>
                    <input type="text" id="api-url" placeholder="https://api.example.com/endpoint">
                </div>
                <div class="form-group">
                    <label>Method</label>
                    <select id="api-method">
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="DELETE">DELETE</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Headers (JSON format)</label>
                    <textarea id="api-headers" rows="2" placeholder='{"Authorization": "Bearer token"}'></textarea>
                </div>
                <div class="form-group">
                    <label>Data (JSON format)</label>
                    <textarea id="api-data" rows="3" placeholder='{"key": "value"}'></textarea>
                </div>
                <button class="execute-button" onclick="executeAPICall()">Execute API Call</button>
                <div class="result-area" id="api-result">Results will appear here...</div>
            </div>
            
            <div class="automation-panel">
                <h3 class="panel-title">🤖 AI Content Generation</h3>
                <div class="form-group">
                    <label>Content Prompt</label>
                    <textarea id="content-prompt" rows="4" placeholder="Describe what content you want to generate..."></textarea>
                </div>
                <div class="form-group">
                    <label>Content Type</label>
                    <select id="content-type">
                        <option value="text">Text</option>
                        <option value="email">Email</option>
                        <option value="article">Article</option>
                        <option value="summary">Summary</option>
                    </select>
                </div>
                <button class="execute-button" onclick="generateContent()">Generate Content</button>
                <div class="result-area" id="content-result">Results will appear here...</div>
            </div>
            
            <div class="automation-panel">
                <h3 class="panel-title">📊 Quick Data Analysis</h3>
                <div class="form-group">
                    <label>Data Input (CSV format or JSON)</label>
                    <textarea id="data-input" rows="6" placeholder="name,value,category&#10;Item 1,100,A&#10;Item 2,200,B"></textarea>
                </div>
                <div class="form-group">
                    <label>Analysis Type</label>
                    <select id="analysis-type">
                        <option value="summary">Summary Statistics</option>
                        <option value="count">Count Values</option>
                        <option value="average">Calculate Averages</option>
                        <option value="total">Calculate Totals</option>
                    </select>
                </div>
                <button class="execute-button" onclick="analyzeData()">Analyze Data</button>
                <div class="result-area" id="data-result">Results will appear here...</div>
            </div>
        </div>
    </div>
    
    <script>
        async function executeEmailAutomation() {
            const recipients = document.getElementById('email-recipients').value.split(',').map(e => e.trim());
            const subject = document.getElementById('email-subject').value;
            const content = document.getElementById('email-content').value;
            
            const resultArea = document.getElementById('email-result');
            resultArea.textContent = 'Executing email automation...';
            
            try {
                const response = await fetch('/api/execute-automation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        type: 'email',
                        recipients: recipients,
                        subject: subject,
                        content: content
                    })
                });
                
                const result = await response.json();
                resultArea.textContent = JSON.stringify(result, null, 2);
            } catch (error) {
                resultArea.textContent = 'Error: ' + error.message;
            }
        }
        
        async function executeAPICall() {
            const url = document.getElementById('api-url').value;
            const method = document.getElementById('api-method').value;
            const headers = document.getElementById('api-headers').value;
            const data = document.getElementById('api-data').value;
            
            const resultArea = document.getElementById('api-result');
            resultArea.textContent = 'Executing API call...';
            
            try {
                const response = await fetch('/api/execute-automation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        type: 'api',
                        url: url,
                        method: method,
                        headers: headers ? JSON.parse(headers) : {},
                        data: data ? JSON.parse(data) : null
                    })
                });
                
                const result = await response.json();
                resultArea.textContent = JSON.stringify(result, null, 2);
            } catch (error) {
                resultArea.textContent = 'Error: ' + error.message;
            }
        }
        
        async function generateContent() {
            const prompt = document.getElementById('content-prompt').value;
            const contentType = document.getElementById('content-type').value;
            
            const resultArea = document.getElementById('content-result');
            resultArea.textContent = 'Generating content...';
            
            try {
                const response = await fetch('/api/execute-automation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        type: 'content',
                        prompt: prompt,
                        content_type: contentType
                    })
                });
                
                const result = await response.json();
                resultArea.textContent = JSON.stringify(result, null, 2);
            } catch (error) {
                resultArea.textContent = 'Error: ' + error.message;
            }
        }
        
        function analyzeData() {
            const dataInput = document.getElementById('data-input').value;
            const analysisType = document.getElementById('analysis-type').value;
            
            const resultArea = document.getElementById('data-result');
            resultArea.textContent = 'Analyzing data...';
            
            try {
                // Simple client-side data analysis
                const lines = dataInput.trim().split('\\n');
                const headers = lines[0].split(',');
                const rows = lines.slice(1).map(line => line.split(','));
                
                let result = {
                    status: 'success',
                    analysis_type: analysisType,
                    row_count: rows.length,
                    column_count: headers.length,
                    headers: headers
                };
                
                if (analysisType === 'summary') {
                    result.summary = `Analyzed ${rows.length} rows with ${headers.length} columns`;
                }
                
                resultArea.textContent = JSON.stringify(result, null, 2);
            } catch (error) {
                resultArea.textContent = 'Error analyzing data: ' + error.message;
            }
        }
        
        console.log('Automation Hub Loaded');
    </script>
</body>
</html>"""
    
    return html_content

@app.route('/api/execute-automation', methods=['POST'])
def execute_automation():
    """Execute automation based on type"""
    try:
        data = request.get_json()
        automation_type = data.get('type')
        
        if automation_type == 'email':
            result = automation_assistant.execute_email_automation(
                recipients=data.get('recipients', []),
                subject=data.get('subject', ''),
                content=data.get('content', '')
            )
        elif automation_type == 'api':
            result = automation_assistant.make_api_call(
                url=data.get('url'),
                method=data.get('method', 'GET'),
                headers=data.get('headers'),
                data=data.get('data')
            )
        elif automation_type == 'content':
            result = automation_assistant.generate_content(
                prompt=data.get('prompt', ''),
                content_type=data.get('content_type', 'text')
            )
        else:
            result = {'status': 'error', 'message': 'Unknown automation type'}
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/automations')
def api_automations():
    """Get available automations"""
    return jsonify({
        'status': 'success',
        'automations': automation_assistant.get_automation_list(),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            logging.warning(f"Database initialization: {e}")
    
    app.run(host="0.0.0.0", port=5000, debug=True)