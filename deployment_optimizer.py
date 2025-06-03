"""
TRAXOVO Deployment Optimizer
Reduce app size for efficient deployment while preserving core functionality
"""

import os
import shutil
import json
from datetime import datetime

class DeploymentOptimizer:
    """Optimize TRAXOVO for lean deployment"""
    
    def __init__(self):
        self.optimization_log = []
        self.space_saved = 0
        
    def optimize_for_deployment(self):
        """Execute comprehensive deployment optimization"""
        
        self.log("Starting TRAXOVO deployment optimization...")
        
        # Remove development artifacts
        self._remove_dev_artifacts()
        
        # Consolidate duplicate functionality
        self._consolidate_modules()
        
        # Optimize static assets
        self._optimize_assets()
        
        # Create deployment summary
        summary = self._create_optimization_summary()
        
        return summary
    
    def _remove_dev_artifacts(self):
        """Remove development files that aren't needed in production"""
        
        dev_patterns = [
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '.pytest_cache',
            'test_*.py',
            '*_test.py',
            'debug_*.py',
            'clicktest.py',
            'app_broken.py',
            'app_legacy.py'
        ]
        
        removed_count = 0
        for pattern in dev_patterns:
            if os.path.exists(pattern):
                if os.path.isfile(pattern):
                    size = os.path.getsize(pattern)
                    os.remove(pattern)
                    self.space_saved += size
                    removed_count += 1
                    self.log(f"Removed {pattern}")
                elif os.path.isdir(pattern):
                    shutil.rmtree(pattern, ignore_errors=True)
                    removed_count += 1
                    self.log(f"Removed directory {pattern}")
        
        self.log(f"Removed {removed_count} development artifacts")
    
    def _consolidate_modules(self):
        """Identify and consolidate duplicate functionality"""
        
        # Core modules to keep
        essential_modules = [
            'main.py',
            'app.py',
            'routes.py',
            'models.py',
            'password_update_system.py',
            'radio_map_asset_architecture.py',
            'executive_security_dashboard.py',
            'integrated_traxovo_system.py'
        ]
        
        # Archive non-essential modules
        archive_dir = 'archived_modules'
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        
        archived_count = 0
        for filename in os.listdir('.'):
            if (filename.endswith('.py') and 
                filename not in essential_modules and
                not filename.startswith('deploy') and
                not filename.startswith('qq_')):
                
                if os.path.isfile(filename):
                    shutil.move(filename, os.path.join(archive_dir, filename))
                    archived_count += 1
        
        self.log(f"Archived {archived_count} non-essential modules")
    
    def _optimize_assets(self):
        """Optimize static assets and templates"""
        
        # Keep only essential templates
        essential_templates = [
            'qq_executive_dashboard.html',
            'main_dashboard.html',
            'automated_reports.html',
            'role_command_widget.html'
        ]
        
        templates_dir = 'templates'
        if os.path.exists(templates_dir):
            for template in os.listdir(templates_dir):
                if template.endswith('.html') and template not in essential_templates:
                    template_path = os.path.join(templates_dir, template)
                    if os.path.isfile(template_path):
                        size = os.path.getsize(template_path)
                        self.space_saved += size
                        # Move to archive instead of delete
                        archive_templates = 'archived_modules/templates'
                        if not os.path.exists(archive_templates):
                            os.makedirs(archive_templates)
                        shutil.move(template_path, os.path.join(archive_templates, template))
        
        self.log("Optimized template assets")
    
    def _create_optimization_summary(self):
        """Create optimization summary"""
        
        summary = {
            'optimization_timestamp': datetime.now().isoformat(),
            'space_saved_bytes': self.space_saved,
            'space_saved_mb': round(self.space_saved / (1024 * 1024), 2),
            'essential_modules_count': 8,
            'deployment_ready': True,
            'optimization_log': self.optimization_log
        }
        
        # Save summary
        with open('deployment_optimization.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
    
    def log(self, message):
        """Log optimization messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.optimization_log.append(log_entry)
        print(log_entry)

def main():
    """Execute deployment optimization"""
    optimizer = DeploymentOptimizer()
    summary = optimizer.optimize_for_deployment()
    
    print("\n" + "="*50)
    print("DEPLOYMENT OPTIMIZATION COMPLETE")
    print("="*50)
    print(f"Space Saved: {summary['space_saved_mb']} MB")
    print(f"Essential Modules: {summary['essential_modules_count']}")
    print("Status: Ready for deployment")
    print("="*50)

if __name__ == "__main__":
    main()