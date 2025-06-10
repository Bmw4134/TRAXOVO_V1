#!/usr/bin/env python3
"""
Create deployable package for Nexus Watson Intelligence Platform
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_deployment_package():
    """Create a complete deployment package"""
    
    # Create deployment directory
    deploy_dir = "nexus_watson_deployment"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    
    os.makedirs(deploy_dir)
    
    # Essential files to include
    essential_files = [
        "production.py",
        "intelligence_export_engine.py",
        "Dockerfile",
        ".dockerignore",
        "deploy-nexus.sh",
        "export_integration_guide.md",
        "app.yaml",
        "cloudbuild.yaml"
    ]
    
    # Copy essential files
    for file in essential_files:
        if os.path.exists(file):
            shutil.copy2(file, deploy_dir)
            print(f"✓ Copied {file}")
    
    # Copy templates directory
    if os.path.exists("templates"):
        shutil.copytree("templates", f"{deploy_dir}/templates")
        print("✓ Copied templates directory")
    
    # Copy static directory
    if os.path.exists("static"):
        shutil.copytree("static", f"{deploy_dir}/static")
        print("✓ Copied static directory")
    
    # Create main.py as alias to production.py
    with open(f"{deploy_dir}/main.py", "w") as f:
        f.write('from production import app\n\nif __name__ == "__main__":\n    app.run()\n')
    
    # Create requirements.txt for deployment
    requirements = """flask==2.3.3
gunicorn==21.2.0
werkzeug==2.3.7
jinja2==3.1.2
markupsafe==2.1.3
itsdangerous==2.1.2
click==8.1.7
blinker==1.6.3"""
    
    with open(f"{deploy_dir}/requirements.txt", "w") as f:
        f.write(requirements)
    
    # Create deployment instructions
    instructions = """# Nexus Watson Deployment Instructions

## Quick Deploy to Google Cloud Run

1. Upload this entire folder to Google Cloud Console
2. In Cloud Run, select "Deploy one revision from source"
3. Upload this folder as ZIP
4. Configure:
   - Port: 8080
   - Memory: 1Gi
   - Environment: SESSION_SECRET=nexus_watson_supreme_production

## Alternative: Command Line Deploy

1. Install Google Cloud SDK
2. Run: gcloud auth login
3. Run: ./deploy-nexus.sh YOUR_PROJECT_ID

## Files Included

- production.py: Main application
- intelligence_export_engine.py: Export functionality
- Dockerfile: Optimized container configuration
- templates/: HTML templates
- static/: CSS, JS, and assets
- requirements.txt: Python dependencies

## Features Available After Deployment

- Watson Command Dashboard
- Intelligence Export Hub (JSON, CSV, XML, Bundle)
- Real-time API endpoints
- Dashboard integration configs for Grafana, Tableau, Power BI

## API Endpoints

- /api/status - System status
- /api/export/json - JSON export
- /api/export/csv - CSV export
- /api/export/dashboard-bundle - Complete bundle
- /api/export/full-intelligence - Real-time intelligence data

Login credentials:
- Username: watson, Password: Btpp@1513
- Username: demo, Password: demo123
"""
    
    with open(f"{deploy_dir}/DEPLOYMENT_INSTRUCTIONS.md", "w") as f:
        f.write(instructions)
    
    # Create ZIP package
    zip_filename = "nexus_watson_deployment.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arcname)
    
    print(f"\n✅ Deployment package created: {zip_filename}")
    print(f"📁 Deployment folder: {deploy_dir}")
    print(f"📦 ZIP package: {zip_filename}")
    
    # List contents
    print("\n📋 Package contents:")
    for root, dirs, files in os.walk(deploy_dir):
        level = root.replace(deploy_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    create_deployment_package()