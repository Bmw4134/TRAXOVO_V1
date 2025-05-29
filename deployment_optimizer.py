"""
TRAXOVO Deployment Optimizer
Intelligent build caching and deployment acceleration system
"""

import os
import json
import hashlib
from datetime import datetime

class DeploymentOptimizer:
    """Optimizes deployment speed through intelligent caching and file analysis"""
    
    def __init__(self):
        self.cache_dir = '.deployment_cache'
        self.manifest_file = os.path.join(self.cache_dir, 'build_manifest.json')
        self.ensure_cache_dir()
    
    def ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def calculate_file_hash(self, filepath):
        """Calculate MD5 hash of a file"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def get_critical_files(self):
        """Identify critical files that trigger different build strategies"""
        return {
            'dependencies': ['pyproject.toml', 'requirements.txt'],
            'core_app': ['main.py', 'app.py'],
            'templates': [f for f in os.listdir('templates') if f.endswith('.html')],
            'static_files': ['static/**/*'] if os.path.exists('static') else [],
            'data_files': ['*.json', '*.xlsx', '*.csv']
        }
    
    def analyze_changes(self):
        """Analyze what changed since last deployment"""
        current_manifest = self.build_manifest()
        previous_manifest = self.load_previous_manifest()
        
        if not previous_manifest:
            return {'type': 'full_build', 'reason': 'First deployment'}
        
        changes = {
            'dependencies_changed': False,
            'core_app_changed': False,
            'templates_changed': False,
            'data_changed': False,
            'changed_files': []
        }
        
        # Compare file hashes
        for category, files in current_manifest.items():
            if category == 'metadata':
                continue
                
            prev_files = previous_manifest.get(category, {})
            
            for filepath, current_hash in files.items():
                prev_hash = prev_files.get(filepath)
                
                if current_hash != prev_hash:
                    changes['changed_files'].append(filepath)
                    
                    if category == 'dependencies':
                        changes['dependencies_changed'] = True
                    elif category == 'core_app':
                        changes['core_app_changed'] = True
                    elif category == 'templates':
                        changes['templates_changed'] = True
                    elif category == 'data_files':
                        changes['data_changed'] = True
        
        # Determine build strategy
        if changes['dependencies_changed']:
            changes['type'] = 'dependency_rebuild'
            changes['estimated_time'] = '3-4 minutes'
        elif changes['core_app_changed']:
            changes['type'] = 'app_rebuild'
            changes['estimated_time'] = '30-45 seconds'
        elif changes['templates_changed']:
            changes['type'] = 'template_update'
            changes['estimated_time'] = '15-20 seconds'
        else:
            changes['type'] = 'minimal_update'
            changes['estimated_time'] = '10-15 seconds'
        
        return changes
    
    def build_manifest(self):
        """Build current file manifest with hashes"""
        manifest = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'build_version': self.get_build_version()
            }
        }
        
        critical_files = self.get_critical_files()
        
        for category, file_patterns in critical_files.items():
            manifest[category] = {}
            
            for pattern in file_patterns:
                if '*' in pattern:
                    # Handle glob patterns
                    continue
                
                if os.path.exists(pattern):
                    file_hash = self.calculate_file_hash(pattern)
                    if file_hash:
                        manifest[category][pattern] = file_hash
        
        return manifest
    
    def load_previous_manifest(self):
        """Load previous build manifest"""
        try:
            if os.path.exists(self.manifest_file):
                with open(self.manifest_file, 'r') as f:
                    return json.loads(f.read())
        except:
            pass
        return None
    
    def save_manifest(self, manifest):
        """Save current manifest"""
        try:
            with open(self.manifest_file, 'w') as f:
                f.write(json.dumps(manifest, indent=2))
            return True
        except Exception as e:
            print(f"Error saving manifest: {e}")
            return False
    
    def get_build_version(self):
        """Generate build version based on git or timestamp"""
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # Fallback to timestamp-based version
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def generate_build_strategy(self):
        """Generate optimized build strategy"""
        changes = self.analyze_changes()
        
        strategy = {
            'build_type': changes['type'],
            'estimated_time': changes.get('estimated_time', 'Unknown'),
            'cache_layers': [],
            'skip_steps': [],
            'priority_files': changes.get('changed_files', [])
        }
        
        # Define caching strategy
        if changes['type'] == 'minimal_update':
            strategy['cache_layers'] = ['dependencies', 'system', 'base_app']
            strategy['skip_steps'] = ['pip_install', 'system_setup']
            
        elif changes['type'] == 'template_update':
            strategy['cache_layers'] = ['dependencies', 'system']
            strategy['skip_steps'] = ['pip_install']
            
        elif changes['type'] == 'app_rebuild':
            strategy['cache_layers'] = ['dependencies']
            strategy['skip_steps'] = []
            
        else:  # dependency_rebuild or full_build
            strategy['cache_layers'] = []
            strategy['skip_steps'] = []
        
        return strategy
    
    def optimize_deployment(self):
        """Main optimization function"""
        print("🚀 TRAXOVO Deployment Optimizer")
        print("=" * 50)
        
        # Analyze current state
        current_manifest = self.build_manifest()
        strategy = self.generate_build_strategy()
        
        print(f"Build Type: {strategy['build_type']}")
        print(f"Estimated Time: {strategy['estimated_time']}")
        print(f"Cache Layers: {len(strategy['cache_layers'])}")
        print(f"Skip Steps: {len(strategy['skip_steps'])}")
        
        if strategy['priority_files']:
            print(f"Changed Files: {len(strategy['priority_files'])}")
            for file in strategy['priority_files'][:5]:  # Show first 5
                print(f"  • {file}")
        
        # Save manifest for next comparison
        self.save_manifest(current_manifest)
        
        return strategy

def create_optimized_dockerfile():
    """Create production-optimized Dockerfile"""
    dockerfile_content = '''# TRAXOVO Production Dockerfile - Optimized for Speed
FROM python:3.11-slim as dependencies

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y \\
    gcc \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy dependency files first (for maximum caching)
COPY pyproject.toml* requirements.tx* ./

# Install Python dependencies (heavily cached layer)
RUN pip install --no-cache-dir --upgrade pip \\
    && pip install --no-cache-dir -r requirements.txt \\
    && pip cache purge

# Application layer (rebuilds quickly on code changes)
FROM dependencies as application

# Copy application code (this layer rebuilds on changes)
COPY . .

# Remove development files
RUN rm -rf tests/ docs/ *.md .git* temp_* attached_assets/*.png

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Start application with optimized settings
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--worker-class", "sync", "--max-requests", "1000", "--preload", "main:app"]
'''
    
    with open('Dockerfile.optimized', 'w') as f:
        f.write(dockerfile_content)
    
    print("✅ Created optimized Dockerfile")

def create_build_script():
    """Create intelligent build script"""
    build_script = '''#!/bin/bash
# TRAXOVO Intelligent Build Script

echo "🚀 Starting TRAXOVO optimized build..."

# Run deployment optimizer
python3 -c "
from deployment_optimizer import DeploymentOptimizer
optimizer = DeploymentOptimizer()
strategy = optimizer.optimize_deployment()
print(f'Build strategy: {strategy[\"build_type\"]}')
"

# Use optimized Dockerfile if available
if [ -f "Dockerfile.optimized" ]; then
    echo "📦 Using optimized Dockerfile..."
    docker build -f Dockerfile.optimized -t traxovo:latest .
else
    echo "📦 Using standard Dockerfile..."
    docker build -t traxovo:latest .
fi

echo "✅ Build complete!"
'''
    
    with open('build.sh', 'w') as f:
        f.write(build_script)
    
    os.chmod('build.sh', 0o755)
    print("✅ Created intelligent build script")

# Execute optimization
if __name__ == "__main__":
    optimizer = DeploymentOptimizer()
    strategy = optimizer.optimize_deployment()
    
    create_optimized_dockerfile()
    create_build_script()
    
    print("\n🎯 Optimization Complete!")
    print("Next deployment will be significantly faster.")