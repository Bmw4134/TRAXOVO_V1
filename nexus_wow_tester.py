"""
NEXUS WOW Tester - Public Demo System
Secure sandbox environment for prospect demonstrations
"""

import logging
import sqlite3
import json
import uuid
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session, redirect
import os

class NexusWowTester:
    """Public demo system with secure sandbox"""
    
    def __init__(self):
        self.demo_db = 'demo_logs.db'
        self.init_demo_database()
        self.test_credentials = {
            'username': 'wow_tester',
            'password': 'nexus_demo_2025'
        }
        
    def init_demo_database(self):
        """Initialize demo logging database"""
        conn = sqlite3.connect(self.demo_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS demo_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            total_interactions INTEGER DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS demo_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            interaction_type TEXT,
            content TEXT,
            ai_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES demo_sessions (session_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Demo database initialized")
    
    def get_welcome_landing(self):
        """Generate branded landing page"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Experience the Future of Intelligence - Built with Nexus</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .container {
            text-align: center;
            max-width: 600px;
            padding: 40px;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 25px 45px rgba(0,0,0,0.2);
        }
        .logo {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: pulse 2s ease-in-out infinite;
        }
        .tagline {
            font-size: 1.5rem;
            margin-bottom: 30px;
            opacity: 0.9;
            font-weight: 300;
        }
        .description {
            font-size: 1.1rem;
            margin-bottom: 40px;
            line-height: 1.6;
            opacity: 0.8;
        }
        .launch-btn {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            border: none;
            padding: 15px 40px;
            font-size: 1.2rem;
            font-weight: 600;
            color: white;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        .launch-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
        }
        .features {
            margin-top: 40px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
        }
        .feature {
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">NEXUS</div>
        <div class="tagline">✨ Experience the Future of Intelligence</div>
        <div class="description">
            Discover autonomous AI that thinks, learns, and executes with unprecedented intelligence. 
            See how Nexus transforms complex workflows into simple conversations.
        </div>
        <a href="/wow-tester/login" class="launch-btn">Launch Intelligence Demo</a>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">🤖</div>
                <div>AI Automation</div>
            </div>
            <div class="feature">
                <div class="feature-icon">🧠</div>
                <div>Smart Learning</div>
            </div>
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <div>Instant Results</div>
            </div>
        </div>
    </div>
</body>
</html>
        '''
    
    def get_login_screen(self):
        """Generate secure login screen"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus Autonomous Intelligence Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0e27;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .login-container {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 40px;
            border-radius: 15px;
            border: 1px solid #00d4aa;
            box-shadow: 0 25px 45px rgba(0,212,170,0.1);
            width: 100%;
            max-width: 400px;
        }
        .logo-container {
            text-align: center;
            margin-bottom: 30px;
        }
        .nexus-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(45deg, #00d4aa, #00b894);
            border-radius: 50%;
            margin: 0 auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            font-weight: bold;
            animation: glow 2s ease-in-out infinite alternate;
        }
        .welcome-text {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 10px;
            color: #00d4aa;
        }
        .subtitle {
            opacity: 0.8;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #00d4aa;
        }
        .form-group input {
            width: 100%;
            padding: 12px;
            background: rgba(255,255,255,0.1);
            border: 1px solid #00d4aa;
            border-radius: 8px;
            color: white;
            font-size: 1rem;
        }
        .form-group input:focus {
            outline: none;
            border-color: #00b894;
            box-shadow: 0 0 10px rgba(0,212,170,0.3);
        }
        .login-btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(45deg, #00d4aa, #00b894);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,212,170,0.3);
        }
        .theme-toggle {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255,255,255,0.1);
            border: 1px solid #00d4aa;
            border-radius: 25px;
            padding: 8px 15px;
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .theme-toggle:hover {
            background: rgba(0,212,170,0.2);
        }
        @keyframes glow {
            0% { box-shadow: 0 0 20px rgba(0,212,170,0.5); }
            100% { box-shadow: 0 0 30px rgba(0,212,170,0.8); }
        }
    </style>
</head>
<body>
    <div class="theme-toggle" onclick="toggleTheme()">🌓 Toggle Theme</div>
    
    <div class="login-container">
        <div class="logo-container">
            <div class="nexus-icon">N</div>
            <div class="welcome-text">Welcome to Nexus</div>
            <div class="subtitle">Autonomous Intelligence Portal</div>
        </div>
        
        <form action="/wow-tester/authenticate" method="post">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required placeholder="Enter demo username">
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required placeholder="Enter demo password">
            </div>
            <button type="submit" class="login-btn">Access Intelligence Portal</button>
        </form>
    </div>
    
    <script>
        function toggleTheme() {
            document.body.style.background = document.body.style.background === 'rgb(240, 240, 240)' ? '#0a0e27' : '#f0f0f0';
            document.body.style.color = document.body.style.color === 'rgb(51, 51, 51)' ? 'white' : '#333';
        }
    </script>
</body>
</html>
        '''
    
    def get_demo_dashboard(self, session_id):
        """Generate eye-popper demo dashboard"""
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus Intelligence Playground</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1a2e 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: rgba(0,212,170,0.1);
            border-radius: 15px;
            border: 1px solid #00d4aa;
        }}
        .header h1 {{
            font-size: 2.5rem;
            color: #00d4aa;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 1.2rem;
            opacity: 0.8;
        }}
        .playground-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .playground-card {{
            background: rgba(255,255,255,0.05);
            border: 1px solid #00d4aa;
            border-radius: 15px;
            padding: 30px;
            transition: all 0.3s ease;
        }}
        .playground-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,212,170,0.2);
        }}
        .card-title {{
            font-size: 1.5rem;
            color: #00d4aa;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .file-drop-zone {{
            border: 2px dashed #00d4aa;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin-bottom: 20px;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        .file-drop-zone:hover {{
            background: rgba(0,212,170,0.1);
            border-color: #00b894;
        }}
        .ai-prompt-box {{
            width: 100%;
            min-height: 120px;
            background: rgba(255,255,255,0.1);
            border: 1px solid #00d4aa;
            border-radius: 10px;
            padding: 15px;
            color: white;
            font-size: 1rem;
            resize: vertical;
            margin-bottom: 15px;
        }}
        .ai-prompt-box:focus {{
            outline: none;
            border-color: #00b894;
            box-shadow: 0 0 15px rgba(0,212,170,0.3);
        }}
        .action-btn {{
            background: linear-gradient(45deg, #00d4aa, #00b894);
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            color: white;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-bottom: 10px;
        }}
        .action-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,212,170,0.3);
        }}
        .demo-output {{
            background: rgba(0,0,0,0.3);
            border: 1px solid #00d4aa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            font-family: monospace;
            font-size: 0.9rem;
            max-height: 300px;
            overflow-y: auto;
        }}
        .status-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00d4aa;
            border-radius: 50%;
            margin-right: 10px;
            animation: pulse 2s ease-in-out infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1><span class="status-indicator"></span>Nexus Intelligence Playground</h1>
        <p>Experience AI automation that thinks and executes like a human expert</p>
    </div>
    
    <div class="playground-grid">
        <div class="playground-card">
            <div class="card-title">🗂️ Instant File Automation</div>
            <div class="file-drop-zone" onclick="document.getElementById('fileInput').click()">
                <div style="font-size: 3rem; margin-bottom: 15px;">📁</div>
                <div>Drop a file here or click to upload</div>
                <div style="font-size: 0.9rem; opacity: 0.7; margin-top: 10px;">
                    Watch AI analyze and automate your document instantly
                </div>
            </div>
            <input type="file" id="fileInput" style="display: none;" onchange="processFile(this)">
            <button class="action-btn" onclick="runFileAutomation()">🚀 Run File Automation</button>
            <div id="fileOutput" class="demo-output" style="display: none;"></div>
        </div>
        
        <div class="playground-card">
            <div class="card-title">💬 Ask the AI Anything</div>
            <textarea class="ai-prompt-box" id="aiPrompt" placeholder="Ask me to automate any task, analyze data, or solve complex problems...

Examples:
• Analyze this sales data and find trends
• Create a customer onboarding workflow
• Write code to process invoices
• Generate a marketing strategy"></textarea>
            <button class="action-btn" onclick="askAI()">🧠 Ask Nexus AI</button>
            <div id="aiOutput" class="demo-output" style="display: none;"></div>
        </div>
        
        <div class="playground-card">
            <div class="card-title">⚡ Quick AI Flow Test</div>
            <div style="margin-bottom: 20px;">
                <p>Experience a complete AI workflow in action:</p>
                <ul style="margin: 15px 0; padding-left: 20px; opacity: 0.8;">
                    <li>AI analyzes sample business data</li>
                    <li>Generates actionable insights</li>
                    <li>Creates automation recommendations</li>
                    <li>Executes workflow in real-time</li>
                </ul>
            </div>
            <button class="action-btn" onclick="runQuickFlow()">⚡ Test AI Flow Now</button>
            <div id="flowOutput" class="demo-output" style="display: none;"></div>
        </div>
    </div>
    
    <script>
        const sessionId = "{session_id}";
        
        function processFile(input) {{
            if (input.files && input.files[0]) {{
                const file = input.files[0];
                document.querySelector('.file-drop-zone').innerHTML = `
                    <div style="font-size: 2rem; margin-bottom: 10px;">✅</div>
                    <div>File loaded: ${{file.name}}</div>
                    <div style="font-size: 0.9rem; opacity: 0.7; margin-top: 5px;">
                        Ready for AI analysis
                    </div>
                `;
            }}
        }}
        
        function runFileAutomation() {{
            const output = document.getElementById('fileOutput');
            output.style.display = 'block';
            output.innerHTML = `
                <div style="color: #00d4aa;">🔄 AI Processing File...</div>
                <div style="margin: 10px 0;">📊 Analyzing document structure...</div>
                <div style="margin: 10px 0;">🧠 Extracting key data points...</div>
                <div style="margin: 10px 0;">⚙️ Generating automation workflow...</div>
                <div style="margin: 10px 0; color: #00d4aa;">✅ Automation Complete!</div>
                <div style="margin-top: 15px; padding: 10px; background: rgba(0,212,170,0.1); border-radius: 5px;">
                    <strong>Results:</strong> Identified 23 actionable data points, created 3 automation workflows, 
                    generated executive summary with 89% confidence score.
                </div>
            `;
            logInteraction('file_automation', 'File automation demo executed');
        }}
        
        function askAI() {{
            const prompt = document.getElementById('aiPrompt').value;
            if (!prompt.trim()) {{
                alert('Please enter a question or task for the AI');
                return;
            }}
            
            const output = document.getElementById('aiOutput');
            output.style.display = 'block';
            output.innerHTML = `
                <div style="color: #00d4aa;">🧠 Nexus AI Processing...</div>
                <div style="margin: 10px 0;"><strong>Your Request:</strong> ${{prompt}}</div>
                <div style="margin: 10px 0;">🔍 Analyzing requirements...</div>
                <div style="margin: 10px 0;">💡 Generating intelligent response...</div>
                <div style="margin: 10px 0; color: #00d4aa;">✅ AI Response Ready!</div>
                <div style="margin-top: 15px; padding: 15px; background: rgba(0,212,170,0.1); border-radius: 5px;">
                    <strong>AI Analysis:</strong> I understand you want to ${{prompt.toLowerCase()}}. 
                    Based on advanced pattern recognition, I recommend a 3-step automated approach:
                    <br><br>
                    1. Data collection and preprocessing (automated)
                    2. Intelligent analysis using machine learning
                    3. Action execution with human oversight
                    <br><br>
                    <em>Confidence Score: 94% | Estimated Time Savings: 85%</em>
                </div>
            `;
            logInteraction('ai_prompt', prompt);
        }}
        
        function runQuickFlow() {{
            const output = document.getElementById('flowOutput');
            output.style.display = 'block';
            output.innerHTML = `
                <div style="color: #00d4aa;">⚡ Quick Flow Initiated...</div>
            `;
            
            let step = 0;
            const steps = [
                "📊 Loading sample business data...",
                "🔍 AI analyzing customer patterns...", 
                "💡 Identifying optimization opportunities...",
                "⚙️ Building automation workflow...",
                "🚀 Executing intelligent actions...",
                "✅ Flow Complete - Results Generated!"
            ];
            
            const interval = setInterval(() => {{
                if (step < steps.length) {{
                    output.innerHTML += `<div style="margin: 5px 0;">${{steps[step]}}</div>`;
                    step++;
                }} else {{
                    clearInterval(interval);
                    output.innerHTML += `
                        <div style="margin-top: 15px; padding: 15px; background: rgba(0,212,170,0.1); border-radius: 5px;">
                            <strong>Quick Flow Results:</strong>
                            <br>• Processed 1,247 data points in 0.3 seconds
                            <br>• Identified 12 optimization opportunities  
                            <br>• Generated 4 automated workflows
                            <br>• Projected ROI: 340% over 6 months
                            <br><br><em>This is just a preview of Nexus capabilities!</em>
                        </div>
                    `;
                }}
            }}, 800);
            
            logInteraction('quick_flow', 'Quick AI flow demonstration');
        }}
        
        function logInteraction(type, content) {{
            fetch('/wow-tester/log-interaction', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    session_id: sessionId,
                    interaction_type: type,
                    content: content
                }})
            }});
        }}
    </script>
</body>
</html>
        '''
    
    def log_demo_interaction(self, session_id, interaction_type, content, ai_response=""):
        """Log demo interaction to database"""
        conn = sqlite3.connect(self.demo_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO demo_interactions 
        (session_id, interaction_type, content, ai_response) 
        VALUES (?, ?, ?, ?)
        ''', (session_id, interaction_type, content, ai_response))
        
        # Update session interaction count
        cursor.execute('''
        UPDATE demo_sessions 
        SET total_interactions = total_interactions + 1 
        WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
        
    def create_demo_session(self, ip_address, user_agent):
        """Create new demo session"""
        session_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.demo_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO demo_sessions (session_id, ip_address, user_agent) 
        VALUES (?, ?, ?)
        ''', (session_id, ip_address, user_agent))
        
        conn.commit()
        conn.close()
        
        return session_id

# Global instance
wow_tester = NexusWowTester()