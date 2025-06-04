"""
QQ Widget Optimization Engine
Removes aggressive in-your-face widget displays and implements clean collapsible system
"""

import os
import re
import glob
from pathlib import Path

class WidgetOptimizer:
    def __init__(self):
        self.templates_dir = "templates"
        self.static_dir = "static"
        
    def optimize_all_widgets(self):
        """Remove aggressive widget displays from all templates"""
        print("🎯 Removing aggressive widget displays...")
        
        # Find and optimize all templates
        template_files = glob.glob(f"{self.templates_dir}/**/*.html", recursive=True)
        
        for template_file in template_files:
            self.optimize_template_widgets(template_file)
            
        # Hide existing widget CSS that's too aggressive
        self.hide_aggressive_widget_styles()
        
        print("✅ Widget optimization complete - clean collapsible system active")
        
    def optimize_template_widgets(self, template_path):
        """Remove aggressive widget containers from template"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Patterns for aggressive widget displays
            aggressive_patterns = [
                # Nudges containers that appear immediately
                r'<div[^>]*class="[^"]*nudges-container[^"]*"[^>]*>.*?</div>',
                r'<div[^>]*class="[^"]*productivity-nudges[^"]*"[^>]*>.*?</div>',
                r'<div[^>]*class="[^"]*dashboard-widgets[^"]*"[^>]*>.*?</div>',
                r'<div[^>]*class="[^"]*widget-grid[^"]*"[^>]*>.*?</div>',
                
                # Auto-loading widget scripts
                r'<script[^>]*>.*?loadContextualNudges.*?</script>',
                r'<script[^>]*>.*?loadNudgesData.*?</script>',
                
                # Aggressive CSS for widgets
                r'\.nudges-container\s*\{[^}]*display:\s*block[^}]*\}',
                r'\.productivity-nudges\s*\{[^}]*position:\s*fixed[^}]*\}',
            ]
            
            # Remove aggressive patterns
            for pattern in aggressive_patterns:
                content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
            
            # Add widget hiding CSS if not already present
            if 'collapsible-widgets.css' not in content:
                # Find the head section and add our CSS
                head_pattern = r'(<head[^>]*>)'
                if re.search(head_pattern, content):
                    content = re.sub(
                        head_pattern,
                        r'\1\n    <style>\n        .nudges-container:not(.collapsible), .productivity-nudges:not(.collapsible), .dashboard-widgets:not(.collapsible) {\n            display: none !important;\n            opacity: 0 !important;\n            pointer-events: none !important;\n        }\n    </style>',
                        content
                    )
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"⚠️ Could not optimize {template_path}: {e}")
            
    def hide_aggressive_widget_styles(self):
        """Add CSS to hide aggressive widget displays"""
        css_override = """
/* Hide Aggressive Widget Displays */
.nudges-container:not(.collapsible),
.productivity-nudges:not(.collapsible),
.dashboard-widgets:not(.collapsible),
.widget-grid:not(.collapsible) {
    display: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
    position: absolute !important;
    left: -9999px !important;
}

/* Ensure only collapsible widgets show */
.widget-container.collapsible {
    display: block !important;
}
"""
        
        # Write to override CSS file
        override_path = f"{self.static_dir}/css/widget-override.css"
        os.makedirs(os.path.dirname(override_path), exist_ok=True)
        
        with open(override_path, 'w') as f:
            f.write(css_override)
            
    def apply_to_main_dashboard(self):
        """Specifically apply to main dashboard template"""
        dashboard_path = f"{self.templates_dir}/quantum_dashboard_corporate.html"
        
        if os.path.exists(dashboard_path):
            # Add widget override CSS link
            try:
                with open(dashboard_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add widget override CSS if not present
                if 'widget-override.css' not in content:
                    css_link = '<link rel="stylesheet" href="/static/css/widget-override.css">'
                    
                    # Insert before closing head tag
                    content = content.replace('</head>', f'    {css_link}\n</head>')
                    
                    with open(dashboard_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                print("✅ Main dashboard optimized for clean widget display")
                
            except Exception as e:
                print(f"⚠️ Dashboard optimization error: {e}")

def optimize_widgets():
    """Main optimization function"""
    optimizer = WidgetOptimizer()
    optimizer.optimize_all_widgets()
    optimizer.apply_to_main_dashboard()
    return True

if __name__ == "__main__":
    optimize_widgets()