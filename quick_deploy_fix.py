#!/usr/bin/env python3
"""
Quick deployment fix - bypass Git issues
"""

import os
import shutil
import zipfile

def create_clean_deployment():
    """Create clean deployment without Git dependencies"""
    
    # Remove any Git artifacts from deploy folder
    deploy_dir = "clean_deploy"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    
    os.makedirs(deploy_dir)
    
    # Copy files from existing deploy folder
    if os.path.exists("deploy"):
        for item in os.listdir("deploy"):
            if item != ".git":
                src = os.path.join("deploy", item)
                dst = os.path.join(deploy_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
    
    # Create .gcloudignore to exclude Git files
    gcloudignore = """.git/
*.log
*.db
__pycache__/
*.pyc
attendance_data/
eq_idle_report.csv
payroll_log.json
qq_*.db
qq_*.json
archived_modules/
"""
    
    with open(f"{deploy_dir}/.gcloudignore", "w") as f:
        f.write(gcloudignore)
    
    # Create deployment script without Git
    deploy_script = """#!/bin/bash
# Direct Cloud Run deployment without Git

gcloud run deploy nexus-watson \\
    --source . \\
    --platform managed \\
    --region us-central1 \\
    --allow-unauthenticated \\
    --port 8080 \\
    --memory 1Gi \\
    --cpu 1 \\
    --set-env-vars "SESSION_SECRET=nexus_watson_supreme_production"

echo "Deployment complete - check Cloud Run console for URL"
"""
    
    with open(f"{deploy_dir}/deploy_clean.sh", "w") as f:
        f.write(deploy_script)
    
    os.chmod(f"{deploy_dir}/deploy_clean.sh", 0o755)
    
    # Create ZIP without Git artifacts
    zip_name = "nexus_clean_deploy.zip"
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            # Skip .git directories
            dirs[:] = [d for d in dirs if d != '.git']
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arcname)
    
    print(f"Clean deployment created: {deploy_dir}")
    print(f"ZIP package: {zip_name}")
    print("Ready for Cloud Run deployment without Git dependencies")
    
    return deploy_dir, zip_name

if __name__ == "__main__":
    create_clean_deployment()