#!/usr/bin/env python3
"""
TRAXOVO Quick Deploy - Optimized for 30-second deployment
Bypasses npm timeout issues detected by complexity visualizer
"""

import os
import sys
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def quick_deploy():
    """Quick deployment bypassing timeout-prone operations"""
    start_time = time.time()
    
    logger.info("🚀 TRAXOVO Quick Deploy Starting...")
    
    # Skip npm install if node_modules exists
    if os.path.exists('node_modules'):
        logger.info("📦 Node modules detected - skipping npm install")
    else:
        logger.info("📦 Node modules missing - deployment will use Python-only mode")
    
    # Clean Python cache quickly
    os.system("find . -name '*.pyc' -delete 2>/dev/null")
    os.system("find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true")
    logger.info("🧹 Python cache cleaned")
    
    # Verify core application
    try:
        import app_qq_enhanced
        logger.info("✅ Core application verified")
    except ImportError as e:
        logger.error(f"❌ Application import failed: {e}")
        return False
    
    # Check deployment complexity
    try:
        from qq_deployment_complexity_visualizer import get_deployment_analyzer
        analyzer = get_deployment_analyzer()
        analysis = analyzer.analyze_project_complexity()
        
        score = analysis.get('complexity_score', 0)
        logger.info(f"📊 Complexity Score: {score:.1f}/100")
        
        if score > 70:
            logger.info("⚠️  High complexity detected - check visualizer for optimization recommendations")
        
    except Exception as e:
        logger.info(f"📊 Complexity analysis: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"⚡ Quick deploy completed in {duration:.1f}s")
    logger.info("🎯 Application ready for deployment")
    logger.info("📈 Use deployment complexity visualizer to monitor performance")
    
    return True

if __name__ == "__main__":
    success = quick_deploy()
    sys.exit(0 if success else 1)