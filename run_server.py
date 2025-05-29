#!/usr/bin/env python3
"""
TRAXOVO Server Launcher with Port Management
"""
import os
import sys
import time
import subprocess
import signal
from datetime import datetime

def kill_existing_processes():
    """Clean up any existing server processes"""
    try:
        # Kill any existing gunicorn processes
        subprocess.run(['pkill', '-f', 'gunicorn'], check=False)
        time.sleep(2)
        
        # Kill any Python processes running main.py
        subprocess.run(['pkill', '-f', 'python.*main'], check=False)
        time.sleep(1)
        
        print("✓ Cleaned up existing processes")
    except Exception as e:
        print(f"Process cleanup warning: {e}")

def start_server():
    """Start the TRAXOVO server"""
    print(f"🚀 Starting TRAXOVO at {datetime.now().strftime('%H:%M:%S')}")
    
    # Clean up first
    kill_existing_processes()
    
    # Start with gunicorn for production stability
    cmd = [
        'gunicorn', 
        '--bind', '0.0.0.0:5000',
        '--workers', '2',
        '--timeout', '120',
        '--reload',
        'main:app'
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        kill_existing_processes()
    except Exception as e:
        print(f"❌ Server error: {e}")
        # Fallback to Flask dev server
        print("🔄 Falling back to development server...")
        os.system('python main.py')

if __name__ == "__main__":
    start_server()