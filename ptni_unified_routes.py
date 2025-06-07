"""
PTNI Unified Routes - Consolidating All Functionality
Single interface leveraging existing components instead of stacking
"""

from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from nexus_unified_platform import get_unified_interface, nexus_unified
import logging

def register_ptni_routes(app):
    """Register all PTNI unified routes that consolidate existing functionality"""
    
    @app.route('/ptni')
    @app.route('/ptni-dashboard')
    def ptni_unified_dashboard():
        """Single unified dashboard that replaces all separate interfaces"""
        user_level = "demo"
        
        # Determine access level from existing session data
        if 'authenticated' in session and session['authenticated']:
            user_level = "executive"
        elif 'wow_authenticated' in session and session['wow_authenticated']:
            user_level = "demo"
        
        return get_unified_interface(user_level)
    
    @app.route('/api/ptni-switch-view', methods=['POST'])
    def ptni_switch_view():
        """Switch between different views in the unified interface"""
        try:
            data = request.get_json()
            view = data.get('view', 'dashboard')
            
            # Generate content based on view using existing functionality
            if view == 'automation':
                content = '''
                <h2>Automation Center</h2>
                <iframe src="/browser-automation" style="width: 100%; height: 600px; border: none; border-radius: 10px;"></iframe>
                '''
            elif view == 'browser':
                content = '''
                <h2>Browser Automation Suite</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <iframe src="/browser-automation" style="width: 100%; height: 400px; border: none;"></iframe>
                    <div style="background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px;">
                        <h3>Active Sessions</h3>
                        <p>Browser automation sessions running...</p>
                    </div>
                </div>
                '''
            elif view == 'trading':
                content = '''
                <h2>Trading Platform</h2>
                <div style="background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px;">
                    <h3>Live Market Data</h3>
                    <p>Real-time trading intelligence...</p>
                </div>
                '''
            elif view == 'intelligence':
                content = '''
                <h2>AI Intelligence Center</h2>
                <div style="background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px;">
                    <h3>OpenAI Integration Active</h3>
                    <p>AI processing and analysis running...</p>
                </div>
                '''
            else:
                content = '''
                <h2>Executive Dashboard</h2>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                    <div style="background: rgba(0,212,170,0.1); padding: 20px; border-radius: 10px;">
                        <h3>Platform Status</h3>
                        <p>All systems operational</p>
                    </div>
                    <div style="background: rgba(0,212,170,0.1); padding: 20px; border-radius: 10px;">
                        <h3>Automation Queue</h3>
                        <p>Active workflows running</p>
                    </div>
                    <div style="background: rgba(0,212,170,0.1); padding: 20px; border-radius: 10px;">
                        <h3>AI Processing</h3>
                        <p>OpenAI integration active</p>
                    </div>
                </div>
                '''
            
            return jsonify({"content": content, "success": True})
            
        except Exception as e:
            logging.error(f"PTNI view switch error: {e}")
            return jsonify({"error": str(e), "success": False})
    
    @app.route('/api/process-ai-prompt', methods=['POST'])
    def process_ai_prompt():
        """Process AI prompts through unified platform"""
        try:
            data = request.get_json()
            prompt = data.get('prompt', '')
            
            if nexus_unified:
                result = nexus_unified.process_ai_prompt(prompt)
                return jsonify(result)
            else:
                return jsonify({
                    "automation_html": "<div>AI processing service initializing...</div>",
                    "success": False
                })
                
        except Exception as e:
            logging.error(f"AI prompt processing error: {e}")
            return jsonify({
                "automation_html": f"<div style='color: #ff6b6b;'>Error: {str(e)}</div>",
                "success": False
            })
    
    @app.route('/api/analyze-file', methods=['POST'])
    def analyze_file():
        """Analyze uploaded files through unified platform"""
        try:
            if 'file' not in request.files:
                return jsonify({"error": "No file uploaded", "success": False})
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected", "success": False})
            
            if nexus_unified:
                result = nexus_unified.analyze_uploaded_file(file)
                return jsonify(result)
            else:
                return jsonify({
                    "analysis_html": "<div>File analysis service initializing...</div>",
                    "opportunities": "0",
                    "success": False
                })
                
        except Exception as e:
            logging.error(f"File analysis error: {e}")
            return jsonify({
                "analysis_html": f"<div style='color: #ff6b6b;'>Error: {str(e)}</div>",
                "opportunities": "0",
                "success": False
            })
    
    @app.route('/unified-demo')
    def unified_demo():
        """Demo interface that consolidates WOW tester functionality"""
        return get_unified_interface("demo")
    
    @app.route('/unified-executive')
    def unified_executive():
        """Executive interface that consolidates all admin functionality"""
        if 'authenticated' not in session or not session['authenticated']:
            return redirect(url_for('login'))
        return get_unified_interface("executive")

def redirect_legacy_routes(app):
    """Redirect all legacy routes to unified PTNI interface"""
    
    @app.route('/ptni-dashboard')
    def legacy_ptni_redirect():
        return redirect(url_for('ptni_unified_dashboard'))
    
    @app.route('/wow-tester-dashboard')
    def legacy_wow_redirect():
        return redirect(url_for('unified_demo'))
    
    @app.route('/admin-direct')
    def legacy_admin_redirect():
        return redirect(url_for('unified_executive'))
    
    @app.route('/executive-dashboard')
    def legacy_executive_redirect():
        return redirect(url_for('unified_executive'))