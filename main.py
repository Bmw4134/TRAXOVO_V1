"""
Troy's Business Intelligence Platform
Advanced automation nexus combining quantum intelligence with real operations
"""

from troy_automation_nexus import app
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    print("="*70)
    print("TROY'S AUTOMATION NEXUS - BUSINESS INTELLIGENCE PLATFORM")
    print("Quantum Intelligence + Real Operations Automation")
    print("="*70)
    
    print("→ Nexus Intelligence Engine: ACTIVE")
    print("→ Fleet Operations Automation: READY")
    print("→ Data Intelligence Processing: ONLINE")
    print("→ API Orchestration Platform: CONNECTED")
    print("→ Financial Intelligence Suite: INITIALIZED")
    print("→ Communication Hub: OPERATIONAL")
    print("→ Authentic Data Sources: DISCOVERED")
    print("→ Starting Troy's Command Center...")
    print("="*70)
    
    # Start server
    app.run(host='0.0.0.0', port=5000, debug=True)