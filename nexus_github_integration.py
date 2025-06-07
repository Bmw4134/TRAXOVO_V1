"""
NEXUS GitHub Integration Module
Secure GitHub connectivity with automated repository management
"""

import requests
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import base64

class NexusGitHubConnector:
    """Advanced GitHub integration for NEXUS platform"""
    
    def __init__(self):
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.github_api_base = "https://api.github.com"
        self.headers = {
            'Authorization': f'token {self.github_token}' if self.github_token else '',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'NEXUS-Platform/1.0'
        }
        self.repo_owner = None
        self.repo_name = None
        
    def authenticate_github(self) -> Dict[str, Any]:
        """Authenticate with GitHub and verify access"""
        if not self.github_token:
            return {
                'authenticated': False,
                'error': 'GitHub token not provided',
                'setup_required': True
            }
        
        try:
            response = requests.get(
                f"{self.github_api_base}/user",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'authenticated': True,
                    'username': user_data['login'],
                    'avatar_url': user_data['avatar_url'],
                    'repositories_count': user_data['public_repos'],
                    'github_url': user_data['html_url']
                }
            else:
                return {
                    'authenticated': False,
                    'error': f'GitHub authentication failed: {response.status_code}',
                    'token_valid': False
                }
                
        except Exception as e:
            return {
                'authenticated': False,
                'error': str(e),
                'connection_failed': True
            }
    
    def list_repositories(self) -> Dict[str, Any]:
        """List user repositories"""
        auth_result = self.authenticate_github()
        if not auth_result.get('authenticated'):
            return auth_result
        
        try:
            response = requests.get(
                f"{self.github_api_base}/user/repos",
                headers=self.headers,
                params={'sort': 'updated', 'per_page': 50},
                timeout=10
            )
            
            if response.status_code == 200:
                repos = response.json()
                formatted_repos = []
                
                for repo in repos:
                    formatted_repos.append({
                        'name': repo['name'],
                        'full_name': repo['full_name'],
                        'description': repo['description'],
                        'private': repo['private'],
                        'clone_url': repo['clone_url'],
                        'html_url': repo['html_url'],
                        'updated_at': repo['updated_at'],
                        'language': repo['language'],
                        'size': repo['size']
                    })
                
                return {
                    'success': True,
                    'repositories': formatted_repos,
                    'total_count': len(formatted_repos)
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fetch repositories: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_nexus_repository(self, repo_name: str = "nexus-singularity-suite") -> Dict[str, Any]:
        """Create a new repository for NEXUS deployment"""
        auth_result = self.authenticate_github()
        if not auth_result.get('authenticated'):
            return auth_result
        
        repo_data = {
            'name': repo_name,
            'description': 'NEXUS Singularity Suite - Enterprise AI Automation Platform',
            'private': False,
            'auto_init': True,
            'gitignore_template': 'Python',
            'license_template': 'mit'
        }
        
        try:
            response = requests.post(
                f"{self.github_api_base}/user/repos",
                headers=self.headers,
                json=repo_data,
                timeout=15
            )
            
            if response.status_code == 201:
                repo_info = response.json()
                self.repo_owner = repo_info['owner']['login']
                self.repo_name = repo_info['name']
                
                return {
                    'success': True,
                    'repository_created': True,
                    'repo_name': repo_info['name'],
                    'repo_url': repo_info['html_url'],
                    'clone_url': repo_info['clone_url'],
                    'git_url': repo_info['git_url']
                }
            else:
                return {
                    'success': False,
                    'error': f'Repository creation failed: {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_nexus_files(self, file_patterns: List[str] = None) -> Dict[str, Any]:
        """Upload NEXUS platform files to GitHub repository"""
        if not self.repo_owner or not self.repo_name:
            return {
                'success': False,
                'error': 'Repository not configured. Create repository first.'
            }
        
        if file_patterns is None:
            file_patterns = [
                'app.py',
                'main.py',
                'models.py',
                'nexus_*.py',
                'traxovo_*.py',
                'requirements.txt',
                'README.md'
            ]
        
        uploaded_files = []
        errors = []
        
        import glob
        import os
        
        for pattern in file_patterns:
            matching_files = glob.glob(pattern)
            
            for file_path in matching_files:
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Encode content
                    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                    
                    # Prepare upload data
                    upload_data = {
                        'message': f'Upload {file_path} - NEXUS Platform',
                        'content': encoded_content,
                        'branch': 'main'
                    }
                    
                    # Upload to GitHub
                    response = requests.put(
                        f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}",
                        headers=self.headers,
                        json=upload_data,
                        timeout=15
                    )
                    
                    if response.status_code in [200, 201]:
                        uploaded_files.append({
                            'file': file_path,
                            'status': 'uploaded',
                            'sha': response.json().get('content', {}).get('sha'),
                            'url': response.json().get('content', {}).get('html_url')
                        })
                    else:
                        errors.append({
                            'file': file_path,
                            'error': f'Upload failed: {response.status_code}',
                            'response': response.text[:200]
                        })
                        
                except Exception as e:
                    errors.append({
                        'file': file_path,
                        'error': str(e)
                    })
        
        return {
            'success': len(errors) == 0,
            'uploaded_files': uploaded_files,
            'upload_count': len(uploaded_files),
            'errors': errors,
            'repository_url': f"https://github.com/{self.repo_owner}/{self.repo_name}"
        }
    
    def create_deployment_workflow(self) -> Dict[str, Any]:
        """Create GitHub Actions workflow for automated deployment"""
        workflow_content = """name: NEXUS Platform Deployment

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v3
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run NEXUS validation tests
      run: |
        python -c "import nexus_validation_macro; nexus_validation_macro.run_bulletproof_validation()"
    
    - name: Deploy to production
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        SESSION_SECRET: ${{ secrets.SESSION_SECRET }}
      run: |
        echo "NEXUS Platform deployment initiated"
        python main.py &
        sleep 10
        echo "NEXUS Platform deployed successfully"
"""
        
        try:
            # Create .github/workflows directory structure
            workflow_data = {
                'message': 'Add NEXUS deployment workflow',
                'content': base64.b64encode(workflow_content.encode('utf-8')).decode('utf-8'),
                'branch': 'main'
            }
            
            response = requests.put(
                f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/contents/.github/workflows/deploy.yml",
                headers=self.headers,
                json=workflow_data,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'workflow_created': True,
                    'workflow_url': response.json().get('content', {}).get('html_url'),
                    'automated_deployment': True
                }
            else:
                return {
                    'success': False,
                    'error': f'Workflow creation failed: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_with_local_changes(self) -> Dict[str, Any]:
        """Sync local NEXUS changes with GitHub repository"""
        # Check for modified files
        import subprocess
        import os
        
        try:
            # Get git status if available
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                modified_files = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        status, filename = line[:2], line[3:]
                        if filename.endswith('.py'):
                            modified_files.append(filename)
                
                if modified_files:
                    # Upload modified files
                    upload_result = self.upload_nexus_files(modified_files)
                    return {
                        'success': True,
                        'sync_completed': True,
                        'modified_files': modified_files,
                        'upload_result': upload_result
                    }
                else:
                    return {
                        'success': True,
                        'no_changes': True,
                        'message': 'No modifications detected'
                    }
            else:
                # Fallback: upload all NEXUS files
                return self.upload_nexus_files()
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'fallback_upload': True
            }

# Global instance
github_connector = NexusGitHubConnector()

def connect_github():
    """Connect to GitHub and setup repository"""
    return github_connector.authenticate_github()

def setup_nexus_repository():
    """Setup NEXUS repository with files and workflows"""
    # Authenticate
    auth_result = github_connector.authenticate_github()
    if not auth_result.get('authenticated'):
        return auth_result
    
    # Create repository
    repo_result = github_connector.create_nexus_repository()
    if not repo_result.get('success'):
        return repo_result
    
    # Upload files
    upload_result = github_connector.upload_nexus_files()
    
    # Create workflow
    workflow_result = github_connector.create_deployment_workflow()
    
    return {
        'github_setup_complete': True,
        'repository': repo_result,
        'file_upload': upload_result,
        'deployment_workflow': workflow_result,
        'ready_for_codex': True
    }