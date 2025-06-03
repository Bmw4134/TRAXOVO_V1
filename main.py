#!/usr/bin/env python3
from app_core import app

if __name__ == "__main__":
    print("Starting TRAXOVO Quantum System...")
    app.run(host="0.0.0.0", port=5000, debug=True)
