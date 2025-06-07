"""
NEXUS Unified Platform - PTNI Enhanced Single Interface
Consolidates all existing functionality into one intelligent system
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Import existing modules for consolidation
from nexus_ptni_interface import NexusPTNIInterface
from nexus_browser_automation import NexusBrowserAutomation
from automation_engine import AutomationEngine
from data_connectors import update_platform_data

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class NexusUnifiedPlatform:
    """Unified NEXUS platform with PTNI intelligence and consolidated functionality"""
    
    def __init__(self, app):
        self.app = app
        self.ptni = NexusPTNIInterface()
        self.browser_automation = NexusBrowserAutomation()
        self.automation_engine = AutomationEngine()
        self.active_users = {}
        self.unified_sessions = {}
        
    def generate_unified_interface(self, user_level="demo"):
        """Generate unified interface based on user access level"""
        if user_level == "demo":
            return self.generate_demo_interface()
        elif user_level == "executive":
            return self.generate_executive_interface()
        elif user_level == "admin":
            return self.generate_admin_interface()
        else:
            return self.generate_landing_interface()
    
    def generate_demo_interface(self):
        """Demo interface with sandbox automation and AI prompts"""
        return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NEXUS Demo - AI Automation Playground</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: white;
                }}
                .unified-container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .ptni-header {{
                    background: rgba(0, 0, 0, 0.2);
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .component-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .component-bucket {{
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 25px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }}
                .ai-prompt-box {{
                    width: 100%;
                    padding: 15px;
                    border: none;
                    border-radius: 10px;
                    background: rgba(255, 255, 255, 0.9);
                    color: #333;
                    font-size: 16px;
                    margin-bottom: 15px;
                }}
                .demo-button {{
                    background: #00d4aa;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 16px;
                    transition: all 0.3s;
                }}
                .demo-button:hover {{
                    background: #00b894;
                    transform: translateY(-2px);
                }}
                .file-upload-area {{
                    border: 2px dashed rgba(255, 255, 255, 0.5);
                    border-radius: 10px;
                    padding: 40px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s;
                }}
                .file-upload-area:hover {{
                    border-color: #00d4aa;
                    background: rgba(0, 212, 170, 0.1);
                }}
                .workflow-preview {{
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 10px;
                    padding: 20px;
                    margin-top: 20px;
                }}
                .demo-log {{
                    background: rgba(0, 0, 0, 0.5);
                    border-radius: 10px;
                    padding: 20px;
                    font-family: monospace;
                    font-size: 14px;
                    max-height: 200px;
                    overflow-y: auto;
                }}
            </style>
        </head>
        <body>
            <div class="unified-container">
                <div class="ptni-header">
                    <h1>🚀 NEXUS AI Automation Playground</h1>
                    <p>Experience the future of enterprise automation - Drag, Drop, and Let AI Handle the Rest</p>
                </div>
                
                <div class="component-grid">
                    <div class="component-bucket">
                        <h3>💬 Ask the AI Anything</h3>
                        <textarea class="ai-prompt-box" placeholder="Ask me to automate any business process... 
                        
Examples:
• 'Create a weekly sales report automation'
• 'Set up customer onboarding workflow'
• 'Build a data entry robot for invoices'"></textarea>
                        <button class="demo-button" onclick="processAIPrompt()">Generate Automation</button>
                    </div>
                    
                    <div class="component-bucket">
                        <h3>📁 Smart File Automation</h3>
                        <div class="file-upload-area" onclick="document.getElementById('fileInput').click()">
                            <p>Drop any Excel, CSV, or document here</p>
                            <p style="font-size: 14px; opacity: 0.8;">AI will analyze and suggest automations</p>
                        </div>
                        <input type="file" id="fileInput" style="display: none;" onchange="handleFileUpload(this)">
                    </div>
                </div>
                
                <div class="workflow-preview">
                    <h3>🔄 Live Automation Preview</h3>
                    <div id="automationPreview">
                        <p>Upload a file or ask the AI to see automation workflows here...</p>
                    </div>
                </div>
                
                <div class="demo-log">
                    <div id="demoLog">
                        <div>NEXUS Demo System Online - Ready for automation requests</div>
                        <div>AI models loaded: GPT-4, automation engine active</div>
                        <div>Waiting for user input...</div>
                    </div>
                </div>
            </div>
            
            <script>
                function processAIPrompt() {{
                    const prompt = document.querySelector('.ai-prompt-box').value;
                    if (!prompt.trim()) return;
                    
                    addToLog('Processing AI request: ' + prompt.substring(0, 50) + '...');
                    
                    fetch('/api/process-ai-prompt', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{prompt: prompt}})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('automationPreview').innerHTML = data.automation_html;
                        addToLog('✅ Automation workflow generated successfully');
                    }});
                }}
                
                function handleFileUpload(input) {{
                    const file = input.files[0];
                    if (!file) return;
                    
                    addToLog('Analyzing file: ' + file.name);
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    fetch('/api/analyze-file', {{
                        method: 'POST',
                        body: formData
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('automationPreview').innerHTML = data.analysis_html;
                        addToLog('📊 File analysis complete - ' + data.opportunities + ' automation opportunities found');
                    }});
                }}
                
                function addToLog(message) {{
                    const log = document.getElementById('demoLog');
                    const timestamp = new Date().toLocaleTimeString();
                    log.innerHTML += '<div>[' + timestamp + '] ' + message + '</div>';
                    log.scrollTop = log.scrollHeight;
                }}
            </script>
        </body>
        </html>
        '''
    
    def generate_executive_interface(self):
        """Executive interface with real-time intelligence and embedded browsers"""
        return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NEXUS Executive Command Center</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #0a0a0a;
                    color: white;
                    overflow-x: hidden;
                }}
                .executive-grid {{
                    display: grid;
                    grid-template-columns: 300px 1fr 400px;
                    height: 100vh;
                }}
                .sidebar {{
                    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
                    padding: 20px;
                    border-right: 2px solid #00d4aa;
                }}
                .main-dashboard {{
                    padding: 20px;
                    overflow-y: auto;
                }}
                .intelligence-feed {{
                    background: linear-gradient(180deg, #16213e 0%, #1a1a2e 100%);
                    padding: 20px;
                    border-left: 2px solid #00d4aa;
                }}
                .embedded-browser {{
                    width: 100%;
                    height: 400px;
                    border: 1px solid #00d4aa;
                    border-radius: 10px;
                    background: white;
                }}
                .metric-card {{
                    background: rgba(0, 212, 170, 0.1);
                    border: 1px solid #00d4aa;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .nav-item {{
                    padding: 12px;
                    margin: 8px 0;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s;
                }}
                .nav-item:hover {{
                    background: rgba(0, 212, 170, 0.2);
                }}
                .feed-item {{
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 15px;
                    border-left: 3px solid #00d4aa;
                }}
            </style>
        </head>
        <body>
            <div class="executive-grid">
                <div class="sidebar">
                    <h2 style="color: #00d4aa; margin-bottom: 30px;">NEXUS Control</h2>
                    <div class="nav-item" onclick="switchView('dashboard')">📊 Executive Dashboard</div>
                    <div class="nav-item" onclick="switchView('automation')">🤖 Automation Center</div>
                    <div class="nav-item" onclick="switchView('browser')">🌐 Browser Automation</div>
                    <div class="nav-item" onclick="switchView('intelligence')">🧠 AI Intelligence</div>
                    <div class="nav-item" onclick="switchView('trading')">💹 Trading Platform</div>
                    <div class="nav-item" onclick="switchView('analytics')">📈 Real-time Analytics</div>
                </div>
                
                <div class="main-dashboard">
                    <div id="dashboardContent">
                        <h1>Executive Command Center</h1>
                        <div class="metric-card">
                            <h3>Platform Status</h3>
                            <p>All systems operational - AI engines active</p>
                        </div>
                        <iframe class="embedded-browser" src="/browser-automation" title="Browser Automation"></iframe>
                    </div>
                </div>
                
                <div class="intelligence-feed">
                    <h3 style="color: #00d4aa; margin-bottom: 20px;">Live Intelligence</h3>
                    <div class="feed-item">
                        <strong>Market Analysis</strong><br>
                        Real-time market data processing active
                    </div>
                    <div class="feed-item">
                        <strong>Automation Queue</strong><br>
                        3 workflows running, 0 errors
                    </div>
                    <div class="feed-item">
                        <strong>AI Processing</strong><br>
                        OpenAI integration operational
                    </div>
                </div>
            </div>
            
            <script>
                function switchView(view) {{
                    fetch('/api/ptni-switch-view', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{view: view}})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('dashboardContent').innerHTML = data.content;
                    }});
                }}
            </script>
        </body>
        </html>
        '''
    
    def process_ai_prompt(self, prompt):
        """Process AI automation prompts and generate workflows"""
        try:
            # Use existing OpenAI integration
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a business automation expert. Generate a visual workflow description and implementation steps for the user's automation request."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            automation_steps = response.choices[0].message.content
            
            # Generate visual workflow HTML
            workflow_html = f'''
            <div style="background: rgba(0, 212, 170, 0.1); border-radius: 10px; padding: 20px;">
                <h3>🔄 Generated Automation Workflow</h3>
                <div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 15px; margin: 15px 0;">
                    <pre style="white-space: pre-wrap; font-size: 14px;">{automation_steps}</pre>
                </div>
                <button onclick="implementWorkflow()" style="background: #00d4aa; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                    Implement This Workflow
                </button>
            </div>
            '''
            
            return {
                "automation_html": workflow_html,
                "success": True
            }
        except Exception as e:
            return {
                "automation_html": f"<div style='color: #ff6b6b;'>Error processing prompt: {str(e)}</div>",
                "success": False
            }
    
    def analyze_uploaded_file(self, file):
        """Analyze uploaded files and suggest automations"""
        try:
            # Process file based on type
            filename = file.filename.lower()
            
            if filename.endswith('.csv') or filename.endswith('.xlsx'):
                opportunities = "Data processing, automated reporting, validation workflows"
            elif filename.endswith('.pdf'):
                opportunities = "Document extraction, approval workflows, archival automation"
            else:
                opportunities = "Custom processing workflow"
            
            analysis_html = f'''
            <div style="background: rgba(0, 212, 170, 0.1); border-radius: 10px; padding: 20px;">
                <h3>📊 File Analysis: {file.filename}</h3>
                <div style="margin: 15px 0;">
                    <strong>Detected Automation Opportunities:</strong>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>{opportunities}</li>
                        <li>Automated data entry and validation</li>
                        <li>Scheduled processing and reporting</li>
                        <li>Error detection and alerting</li>
                    </ul>
                </div>
                <button onclick="createAutomation()" style="background: #00d4aa; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                    Create Automation
                </button>
            </div>
            '''
            
            return {
                "analysis_html": analysis_html,
                "opportunities": "4",
                "success": True
            }
        except Exception as e:
            return {
                "analysis_html": f"<div style='color: #ff6b6b;'>Error analyzing file: {str(e)}</div>",
                "opportunities": "0",
                "success": False
            }

# Initialize unified platform
nexus_unified = None

def initialize_unified_platform(app):
    """Initialize the unified NEXUS platform"""
    global nexus_unified
    nexus_unified = NexusUnifiedPlatform(app)
    return nexus_unified

def get_unified_interface(user_level="demo"):
    """Get unified interface for user level"""
    if nexus_unified:
        return nexus_unified.generate_unified_interface(user_level)
    return "<div>Platform initializing...</div>"