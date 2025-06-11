#!/usr/bin/env python3
"""
Simple deployment setup - creates individual files for manual deployment
"""

import os
import shutil

def create_simple_deployment():
    """Create deployment files in easy-to-access format"""
    
    # Create a simple deployment folder
    deploy_dir = "deploy"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    
    os.makedirs(deploy_dir)
    
    # Copy essential files only
    essential_files = [
        "production.py",
        "intelligence_export_engine.py", 
        "Dockerfile",
        ".dockerignore"
    ]
    
    for file in essential_files:
        if os.path.exists(file):
            shutil.copy2(file, deploy_dir)
    
    # Create main.py
    main_content = """# Nexus Watson Main Entry Point
from production import app

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
"""
    
    with open(f"{deploy_dir}/main.py", "w") as f:
        f.write(main_content)
    
    # Create requirements.txt
    requirements = """flask==2.3.3
gunicorn==21.2.0
"""
    
    with open(f"{deploy_dir}/requirements.txt", "w") as f:
        f.write(requirements)
    
    # Create simple Dockerfile
    dockerfile_content = """FROM python:3.11-alpine
ENV PORT=8080
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "main:app"]
"""
    
    with open(f"{deploy_dir}/Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    # Copy minimal templates
    if os.path.exists("templates"):
        os.makedirs(f"{deploy_dir}/templates")
        # Copy only essential templates
        essential_templates = [
            "production_dashboard.html",
            "premium_landing.html", 
            "export_intelligence_widget.html"
        ]
        
        for template in essential_templates:
            src = f"templates/{template}"
            if os.path.exists(src):
                shutil.copy2(src, f"{deploy_dir}/templates/")
    
    # Copy minimal static files
    if os.path.exists("static"):
        os.makedirs(f"{deploy_dir}/static")
        # Copy only CSS files
        for root, dirs, files in os.walk("static"):
            for file in files:
                if file.endswith('.css') and not file.endswith('.gz'):
                    src = os.path.join(root, file)
                    rel_path = os.path.relpath(src, "static")
                    dest_dir = os.path.join(f"{deploy_dir}/static", os.path.dirname(rel_path))
                    os.makedirs(dest_dir, exist_ok=True)
                    shutil.copy2(src, os.path.join(dest_dir, file))
    
    print("Simple deployment files created in 'deploy' folder")
    print("\nFiles created:")
    for root, dirs, files in os.walk(deploy_dir):
        level = root.replace(deploy_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    create_simple_deployment()