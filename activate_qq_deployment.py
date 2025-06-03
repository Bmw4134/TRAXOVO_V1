#!/usr/bin/env python3
"""
QQ Deployment Activation
Direct deployment using quantum orchestrator logic
"""

import sys
import os
import time
import subprocess
from qq_deployment_orchestrator import QQDeploymentOrchestrator

def activate_traxovo_deployment():
    """Activate TRAXOVO using QQ deployment orchestrator"""
    
    print("Activating QQ Deployment Orchestrator...")
    
    # Initialize QQ orchestrator
    orchestrator = QQDeploymentOrchestrator()
    
    # Execute quantum deployment
    print("Executing quantum deployment sequence...")
    deployment_result = orchestrator.execute_complete_deployment_cycle()
    
    # Start TRAXOVO application
    print("Starting TRAXOVO application...")
    
    # Clear any existing processes
    subprocess.run("pkill -f 'python.*app' 2>/dev/null", shell=True)
    time.sleep(2)
    
    # Start app_working directly
    from app_working import app
    
    # Find available port
    import socket
    for port in range(5000, 5010):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('0.0.0.0', port))
            s.close()
            
            print(f"TRAXOVO System Active on Port {port}")
            print("Watson Password: Btpp@1513")
            print("QQ Deployment Complete")
            
            app.run(host="0.0.0.0", port=port, debug=False)
            break
        except:
            continue

if __name__ == "__main__":
    activate_traxovo_deployment()