"""
TRAXOVO Quick Login - Emergency Access

This provides immediate access to your beautiful TRAXOVO login system
while we resolve the complex database relationship issues.
"""
from simple_app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)