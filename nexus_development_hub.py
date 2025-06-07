"""
NEXUS Development Hub
Unified interface for GitHub and ChatGPT Codex integration
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

class NexusDevelopmentHub:
    """Centralized development hub for GitHub and AI integration"""
    
    def __init__(self):
        self.github_status = None
        self.codex_status = None
        self.last_check = None
        
    def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'github': self._check_github_status(),
            'codex': self._check_codex_status(),
            'development_ready': False,
            'available_features': []
        }
        
        # Determine development readiness
        github_ready = status['github'].get('authenticated', False)
        codex_ready = status['codex'].get('authenticated', False)
        
        if github_ready and codex_ready:
            status['development_ready'] = True
            status['integration_level'] = 'full'
            status['available_features'] = [
                'AI-powered code generation',
                'Repository management',
                'Automated testing',
                'Code optimization',
                'Documentation generation',
                'Continuous deployment'
            ]
        elif codex_ready:
            status['development_ready'] = True
            status['integration_level'] = 'ai_only'
            status['available_features'] = [
                'AI-powered code generation',
                'Code optimization',
                'Documentation generation',
                'Codebase analysis'
            ]
        elif github_ready:
            status['integration_level'] = 'github_only'
            status['available_features'] = [
                'Repository management',
                'Version control',
                'Code backup'
            ]
        else:
            status['integration_level'] = 'none'
            status['setup_required'] = True
        
        return status
    
    def _check_github_status(self) -> Dict[str, Any]:
        """Check GitHub connection status"""
        try:
            from nexus_github_integration import connect_github
            return connect_github()
        except Exception as e:
            return {
                'authenticated': False,
                'error': str(e),
                'setup_required': True
            }
    
    def _check_codex_status(self) -> Dict[str, Any]:
        """Check ChatGPT Codex connection status"""
        try:
            from nexus_chatgpt_codex_integration import connect_chatgpt_codex
            return connect_chatgpt_codex()
        except Exception as e:
            return {
                'authenticated': False,
                'error': str(e),
                'setup_required': True
            }
    
    def generate_setup_instructions(self) -> Dict[str, Any]:
        """Generate setup instructions for missing integrations"""
        status = self.get_integration_status()
        instructions = {
            'setup_required': [],
            'completion_steps': []
        }
        
        if not status['github'].get('authenticated'):
            instructions['setup_required'].append({
                'service': 'GitHub',
                'environment_variable': 'GITHUB_TOKEN',
                'instructions': [
                    'Go to GitHub.com → Settings → Developer settings → Personal access tokens',
                    'Generate new token with repo, workflow, and admin permissions',
                    'Add GITHUB_TOKEN to your environment variables',
                    'Restart NEXUS platform to activate GitHub integration'
                ],
                'benefits': [
                    'Automated repository management',
                    'Code backup and version control',
                    'Continuous deployment workflows',
                    'Team collaboration features'
                ]
            })
        
        if not status['codex'].get('authenticated'):
            instructions['setup_required'].append({
                'service': 'ChatGPT Codex',
                'environment_variable': 'OPENAI_API_KEY',
                'instructions': [
                    'Visit platform.openai.com and create an account',
                    'Generate API key from API keys section',
                    'Add OPENAI_API_KEY to your environment variables',
                    'Restart NEXUS platform to activate AI development features'
                ],
                'benefits': [
                    'AI-powered code generation',
                    'Intelligent code optimization',
                    'Automated documentation creation',
                    'Advanced codebase analysis'
                ]
            })
        
        if status['development_ready']:
            instructions['completion_steps'] = [
                'Access development features via /api/nexus/codex-connect',
                'Generate code using /api/nexus/generate-code',
                'Analyze codebase with /api/nexus/analyze-codebase',
                'Sync with GitHub using /api/nexus/sync-github'
            ]
        
        return instructions
    
    def create_development_dashboard(self) -> str:
        """Create HTML dashboard for development hub"""
        status = self.get_integration_status()
        
        github_status_color = "#00d4aa" if status['github'].get('authenticated') else "#ff6b6b"
        codex_status_color = "#00d4aa" if status['codex'].get('authenticated') else "#ff6b6b"
        
        dashboard_html = f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="max-width: 1200px; margin: 0 auto;">
                
                <!-- Header -->
                <div style="text-align: center; margin-bottom: 40px;">
                    <h1 style="color: #00d4aa; font-size: 2.5em; margin: 0; text-shadow: 0 0 20px rgba(0,212,170,0.3);">
                        NEXUS Development Hub
                    </h1>
                    <p style="color: #a0a0a0; font-size: 1.2em; margin: 10px 0;">
                        Advanced AI-Powered Development Platform
                    </p>
                </div>
                
                <!-- Integration Status Cards -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 40px;">
                    
                    <!-- GitHub Integration -->
                    <div style="background: rgba(255,255,255,0.05); border-radius: 15px; padding: 25px; border-left: 4px solid {github_status_color};">
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <div style="width: 12px; height: 12px; background: {github_status_color}; border-radius: 50%; margin-right: 10px;"></div>
                            <h3 style="color: white; margin: 0;">GitHub Integration</h3>
                        </div>
                        <p style="color: #a0a0a0; margin: 10px 0;">
                            Status: {'Connected' if status['github'].get('authenticated') else 'Setup Required'}
                        </p>
                        {'<p style="color: #00d4aa;">Repository management active</p>' if status['github'].get('authenticated') else '<p style="color: #ff6b6b;">Requires GITHUB_TOKEN</p>'}
                    </div>
                    
                    <!-- ChatGPT Codex Integration -->
                    <div style="background: rgba(255,255,255,0.05); border-radius: 15px; padding: 25px; border-left: 4px solid {codex_status_color};">
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <div style="width: 12px; height: 12px; background: {codex_status_color}; border-radius: 50%; margin-right: 10px;"></div>
                            <h3 style="color: white; margin: 0;">ChatGPT Codex</h3>
                        </div>
                        <p style="color: #a0a0a0; margin: 10px 0;">
                            Status: {'Connected' if status['codex'].get('authenticated') else 'Setup Required'}
                        </p>
                        {'<p style="color: #00d4aa;">AI development ready</p>' if status['codex'].get('authenticated') else '<p style="color: #ff6b6b;">Requires OPENAI_API_KEY</p>'}
                    </div>
                </div>
                
                <!-- Available Features -->
                <div style="background: rgba(255,255,255,0.05); border-radius: 15px; padding: 25px; margin-bottom: 30px;">
                    <h3 style="color: #00d4aa; margin-bottom: 20px;">Available Development Features</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
        """
        
        for feature in status.get('available_features', []):
            dashboard_html += f"""
                        <div style="background: rgba(0,212,170,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #00d4aa;">
                            <p style="color: white; margin: 0;">{feature}</p>
                        </div>
            """
        
        if not status.get('available_features'):
            dashboard_html += """
                        <div style="background: rgba(255,107,107,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #ff6b6b;">
                            <p style="color: #ff6b6b; margin: 0;">Setup GitHub and OpenAI API keys to unlock development features</p>
                        </div>
            """
        
        dashboard_html += """
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div style="background: rgba(255,255,255,0.05); border-radius: 15px; padding: 25px;">
                    <h3 style="color: #00d4aa; margin-bottom: 20px;">Development Actions</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
        """
        
        if status['codex'].get('authenticated'):
            dashboard_html += """
                        <button onclick="generateCode()" style="background: linear-gradient(45deg, #00d4aa, #007a6b); color: white; border: none; padding: 15px; border-radius: 8px; cursor: pointer; font-weight: bold;">
                            Generate AI Code
                        </button>
                        <button onclick="analyzeCodebase()" style="background: linear-gradient(45deg, #4ecdc4, #2980b9); color: white; border: none; padding: 15px; border-radius: 8px; cursor: pointer; font-weight: bold;">
                            Analyze Codebase
                        </button>
            """
        
        if status['github'].get('authenticated'):
            dashboard_html += """
                        <button onclick="syncGitHub()" style="background: linear-gradient(45deg, #333, #555); color: white; border: none; padding: 15px; border-radius: 8px; cursor: pointer; font-weight: bold;">
                            Sync with GitHub
                        </button>
                        <button onclick="viewRepositories()" style="background: linear-gradient(45deg, #6c5ce7, #a29bfe); color: white; border: none; padding: 15px; border-radius: 8px; cursor: pointer; font-weight: bold;">
                            View Repositories
                        </button>
            """
        
        dashboard_html += """
                    </div>
                </div>
                
            </div>
            
            <script>
                function generateCode() {
                    const description = prompt('Describe the code you want to generate:');
                    if (description) {
                        fetch('/api/nexus/generate-code', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ description: description })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success') {
                                alert('Code generated successfully!');
                                location.reload();
                            } else {
                                alert('Generation failed: ' + data.error);
                            }
                        });
                    }
                }
                
                function analyzeCodebase() {
                    fetch('/api/nexus/analyze-codebase')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            alert('Codebase analysis complete!');
                        } else {
                            alert('Analysis failed: ' + data.error);
                        }
                    });
                }
                
                function syncGitHub() {
                    fetch('/api/nexus/sync-github', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            alert('GitHub sync complete!');
                        } else {
                            alert('Sync failed: ' + data.error);
                        }
                    });
                }
                
                function viewRepositories() {
                    fetch('/api/nexus/github-repositories')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            const repos = data.repositories.repositories || [];
                            alert(`Found ${repos.length} repositories`);
                        } else {
                            alert('Failed to fetch repositories: ' + data.error);
                        }
                    });
                }
            </script>
        </div>
        """
        
        return dashboard_html

# Global instance
development_hub = NexusDevelopmentHub()

def get_development_status():
    """Get current development integration status"""
    return development_hub.get_integration_status()

def get_setup_instructions():
    """Get setup instructions for missing integrations"""
    return development_hub.generate_setup_instructions()

def get_development_dashboard():
    """Get development dashboard HTML"""
    return development_hub.create_development_dashboard()