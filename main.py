"""
Universal Automation Assistant - For Troy
A comprehensive tool to automate any business task
"""

from automation_assistant import app
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    print("="*60)
    print("UNIVERSAL AUTOMATION ASSISTANT")
    print("Automate Everything, Simplify Everything")
    print("="*60)
    
    print("→ Automation Engine: Ready")
    print("→ API Integration: Active")
    print("→ AI Assistance: Available")
    print("→ Starting Automation Server...")
    print("="*60)
    
    # Start server
    app.run(host='0.0.0.0', port=5000, debug=True)