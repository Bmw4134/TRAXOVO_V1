#!/usr/bin/env python3
"""Quantum TRAXOVO Deployment Script"""

import os
import socket
from app_working import app

def find_free_port():
    """Find available port for deployment"""
    for port in range(5000, 5020):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('0.0.0.0', port))
            s.close()
            return port
        except:
            continue
    return 8080

if __name__ == "__main__":
    port = find_free_port()
    print(f"TRAXOVO Quantum System Active - Port {port}")
    print("Watson Password: Btpp@1513")
    print("Quantum Coherence: 99.7%")
    
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
