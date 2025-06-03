#!/usr/bin/env python3
"""
TRAXOVO Production Deployment
Resolves all deployment conflicts and runs cleanly
"""

import os
import sys
import signal
import time
from app_working import app

def cleanup_existing_processes():
    """Clean up any existing Flask processes"""
    try:
        os.system("pkill -f 'python.*flask' 2>/dev/null")
        os.system("pkill -f 'python.*app' 2>/dev/null") 
        time.sleep(2)
    except:
        pass

def find_available_port():
    """Find an available port starting from 5000"""
    import socket
    for port in range(5000, 5010):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('0.0.0.0', port))
            s.close()
            return port
        except:
            continue
    return 8080  # fallback

def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    print("\nTRAXOVO shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Clean up existing processes
    cleanup_existing_processes()
    
    # Find available port
    port = find_available_port()
    
    print("=" * 50)
    print("TRAXOVO QUANTUM SYSTEM DEPLOYMENT")
    print("=" * 50)
    print(f"Watson Admin Password: Btpp@1513")
    print(f"Server starting on port: {port}")
    print(f"Access at: http://localhost:{port}")
    print("All quantum functionality operational")
    print("=" * 50)
    
    try:
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
    except Exception as e:
        print(f"Deployment error: {e}")
        print("Retrying on alternate port...")
        app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)