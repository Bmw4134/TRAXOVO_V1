#!/bin/bash
# TRAXOVO Intelligent Build Script

echo "🚀 Starting TRAXOVO optimized build..."

# Run deployment optimizer
python3 -c "
from deployment_optimizer import DeploymentOptimizer
optimizer = DeploymentOptimizer()
strategy = optimizer.optimize_deployment()
print(f'Build strategy: {strategy["build_type"]}')
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
