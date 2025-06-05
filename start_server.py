#!/usr/bin/env python3
"""
TRAXOVO Server Startup Script
Starts the Node.js server for the executive dashboard deployment
"""
import subprocess
import sys
import os

def main():
    """Start the Node.js server"""
    try:
        print("Starting TRAXOVO Node.js server...")
        # Start Node.js server directly
        subprocess.run(["node", "server.js"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Server startup failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Server shutdown requested")
        sys.exit(0)

if __name__ == "__main__":
    main()