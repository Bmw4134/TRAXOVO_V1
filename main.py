import subprocess
import threading
import time
from flask import Flask

# Create a minimal Flask app for gunicorn compatibility
app = Flask(__name__)

@app.route('/')
def redirect_to_node():
    return '<script>window.location.href = "http://localhost:3000";</script>'

def start_node_server():
    """Start the Node.js server in a separate thread"""
    try:
        subprocess.run(["node", "server.js"], cwd=".", check=True)
    except subprocess.CalledProcessError as e:
        print(f"Node.js server error: {e}")

if __name__ == "__main__":
    # Start Node.js server in background
    node_thread = threading.Thread(target=start_node_server, daemon=True)
    node_thread.start()
    time.sleep(2)  # Give Node.js time to start
    
    app.run(host="0.0.0.0", port=5000, debug=True)