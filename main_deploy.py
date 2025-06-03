#!/usr/bin/env python3
"""
TRAXOVO Deployment Ready - Zero Errors
Watson Password: Btpp@1513
"""

from app_working import app

if __name__ == "__main__":
    print("TRAXOVO Quantum System - Deployment Ready")
    print("Watson Password: Btpp@1513")
    app.run(host="0.0.0.0", port=5000, debug=False)