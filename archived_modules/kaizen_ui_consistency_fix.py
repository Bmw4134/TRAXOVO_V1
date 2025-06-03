#!/usr/bin/env python3
"""
KAIZEN UI Consistency Fix
Ensures all TRAXOVO pages have consistent navigation and layouts
"""

import os
import re
from datetime import datetime

class KaizenUIConsistencyFix:
    def __init__(self):
        self.templates_dir = "templates"
        self.fixed_pages = []
        self.missing_templates = []
        
    def get_critical_routes(self):
        """Get list of critical routes that need templates"""
        return {
            "/kaizen": "templates/kaizen/dashboard.html",
            "/drivers": "templates/drivers/index.html", 
            "/reports": "templates/reports/dashboard.html",
            "/equipment-billing": "templates/equipment_billing/dashboard.html",
            "/enhanced-weekly-reports": "templates/enhanced_weekly_reports/dashboard.html"
        }
    
    def create_missing_templates(self):
        """Create missing templates with consistent navigation"""
        critical_routes = self.get_critical_routes()
        
        for route, template_path in critical_routes.items():
            if not os.path.exists(template_path):
                self.create_template_with_navigation(template_path, route)
                self.missing_templates.append(template_path)
    
    def create_template_with_navigation(self, template_path, route):
        """Create template with consistent navigation structure"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        
        # Extract page name from route
        page_name = route.replace('/', '').replace('-', ' ').title()
        if not page_name:
            page_name = "Dashboard"
        
        template_content = f'''{{%% extends "base_navigation.html" %%}}

{{%% block title %%}}{page_name} - TRAXOVO{{%% endblock %%}}

{{%% block page_title %%}}{page_name}{{%% endblock %%}}

{{%% block content %%}}
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-cog me-2 text-primary"></i>
                    {page_name} Module
                </h5>
            </div>
            <div class="card-body">
                <div class="text-center py-5">
                    <i class="fas fa-tools fa-3x text-muted mb-3"></i>
                    <h5>{page_name} Ready for Configuration</h5>
                    <p class="text-muted">This module is prepared for your operational data and customization.</p>
                    <div class="mt-4">
                        <a href="/data-upload" class="btn btn-primary me-2">
                            <i class="fas fa-upload me-2"></i>Upload Data
                        </a>
                        <a href="/" class="btn btn-outline-secondary">
                            <i class="fas fa-arrow-left me-2"></i>Back to Dashboard
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{{%% endblock %%}}'''
        
        with open(template_path, 'w') as f:
            f.write(template_content)
    
    def fix_existing_templates(self):
        """Update existing templates to use consistent navigation"""
        # Key templates that need navigation updates
        templates_to_fix = [
            "templates/kaizen/dashboard.html",
            "templates/drivers/index.html",
            "templates/reports/dashboard.html"
        ]
        
        for template_path in templates_to_fix:
            if os.path.exists(template_path):
                self.add_navigation_to_template(template_path)
                self.fixed_pages.append(template_path)
    
    def add_navigation_to_template(self, template_path):
        """Add navigation to existing template if missing"""
        try:
            with open(template_path, 'r') as f:
                content = f.read()
            
            # Check if already extends base_navigation
            if 'extends "base_navigation.html"' in content:
                return
            
            # Simple fix: add navigation link at top if missing
            if '<body>' in content and 'navbar' not in content.lower():
                navigation_link = '''
<div class="container-fluid bg-primary text-white py-2">
    <div class="container">
        <a href="/" class="text-white text-decoration-none">
            <i class="fas fa-arrow-left me-2"></i>Back to Dashboard
        </a>
    </div>
</div>
'''
                content = content.replace('<body>', f'<body>{navigation_link}')
                
                with open(template_path, 'w') as f:
                    f.write(content)
                    
        except Exception as e:
            print(f"Could not update {template_path}: {e}")
    
    def run_consistency_fix(self):
        """Execute full UI consistency fix"""
        print("🎨 KAIZEN UI CONSISTENCY FIX")
        print("=" * 40)
        
        print("Creating missing templates...")
        self.create_missing_templates()
        
        print("Fixing existing templates...")
        self.fix_existing_templates()
        
        # Generate fix report
        fix_report = {
            "timestamp": datetime.now().isoformat(),
            "missing_templates_created": len(self.missing_templates),
            "existing_templates_fixed": len(self.fixed_pages),
            "created_templates": self.missing_templates,
            "fixed_templates": self.fixed_pages
        }
        
        with open("kaizen_ui_fix_report.json", "w") as f:
            import json
            json.dump(fix_report, f, indent=2)
        
        return fix_report
    
    def print_summary(self):
        """Display fix summary"""
        print(f"\n✅ UI CONSISTENCY FIX COMPLETE")
        print("=" * 40)
        print(f"Missing templates created: {len(self.missing_templates)}")
        print(f"Existing templates fixed: {len(self.fixed_pages)}")
        
        if self.missing_templates:
            print("\n📄 Created Templates:")
            for template in self.missing_templates:
                print(f"  • {template}")
        
        if self.fixed_pages:
            print("\n🔧 Fixed Templates:")
            for template in self.fixed_pages:
                print(f"  • {template}")

if __name__ == "__main__":
    fixer = KaizenUIConsistencyFix()
    fixer.run_consistency_fix()
    fixer.print_summary()