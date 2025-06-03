"""
Simple Deployment Optimizer - Aggressive Size Reduction
"""

import os
import shutil

def optimize_deployment():
    """Aggressively optimize for deployment"""
    
    # Core files that must stay
    core_files = [
        'main.py',
        'app.py', 
        'routes.py',
        'models.py',
        'quantum_asi_excellence.py',
        'radio_map_asset_architecture.py'
    ]
    
    print("Starting aggressive deployment optimization...")
    
    # Create archive directory
    if not os.path.exists('deployment_archive'):
        os.makedirs('deployment_archive')
    
    # Move all non-core Python files
    moved_count = 0
    for filename in os.listdir('.'):
        if (filename.endswith('.py') and 
            filename not in core_files and
            filename != 'simple_deployment_optimizer.py'):
            
            try:
                shutil.move(filename, f'deployment_archive/{filename}')
                moved_count += 1
                print(f"Archived: {filename}")
            except:
                pass
    
    # Keep only essential templates
    templates_dir = 'templates'
    essential_templates = [
        'qq_executive_dashboard.html',
        'main_dashboard.html'
    ]
    
    if os.path.exists(templates_dir):
        archive_templates = 'deployment_archive/templates'
        if not os.path.exists(archive_templates):
            os.makedirs(archive_templates)
            
        for template in os.listdir(templates_dir):
            if template not in essential_templates:
                try:
                    shutil.move(f'{templates_dir}/{template}', f'{archive_templates}/{template}')
                except:
                    pass
    
    print(f"Optimization complete. Archived {moved_count} files.")
    print(f"Core system maintained with {len(core_files)} essential files.")
    
    return moved_count

if __name__ == "__main__":
    optimize_deployment()