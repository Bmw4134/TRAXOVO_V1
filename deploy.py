#!/usr/bin/env python3
"""
TRAXOVO Deployment Script - Clean startup with port management
"""
import subprocess
import sys
import time
import signal
import os

def kill_existing_processes():
    """Kill any existing processes on port 5000"""
    try:
        # Find processes using port 5000
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if ':5000' in line and 'LISTEN' in line:
                parts = line.split()
                if len(parts) > 6:
                    pid_info = parts[6]
                    if '/' in pid_info:
                        pid = pid_info.split('/')[0]
                        if pid.isdigit():
                            print(f"Killing process {pid} on port 5000")
                            os.kill(int(pid), signal.SIGKILL)
    except Exception as e:
        print(f"Port cleanup: {e}")

def start_application():
    """Start the TRAXOVO application"""
    print("Starting TRAXOVO Fleet Management System...")
    
    # Kill existing processes
    kill_existing_processes()
    time.sleep(2)
    
    # Start the application
    try:
        subprocess.run([
            'gunicorn', 
            '--bind', '0.0.0.0:5000',
            '--workers', '4',
            '--timeout', '120',
            '--keep-alive', '2',
            '--max-requests', '1000',
            '--max-requests-jitter', '50',
            '--reload',
            'app:app'
        ])
    except KeyboardInterrupt:
        print("\nShutting down TRAXOVO...")
        kill_existing_processes()

if __name__ == '__main__':
    start_application()