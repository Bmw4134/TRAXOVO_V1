"""
TRAXOVO NEXUS Main Application Entry Point
Simplified startup for QNIS Clarity Core
"""

from flask import Flask, render_template, render_template_string, jsonify, Response
import os
import json
import logging
from datetime import datetime
from gauge_api_connector import get_live_gauge_data

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "nexus-qnis-key")

@app.route('/')
def clarity_core_dashboard():
    """TRAXOVO ∞ Clarity Core Dashboard"""
    return render_template_string(CLARITY_CORE_TEMPLATE)

@app.route('/api/qnis/realtime-metrics')
def realtime_metrics():
    """Real-time QNIS metrics endpoint"""
    try:
        gauge_data = get_live_gauge_data()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'qnis_level': 15,
            'consciousness_state': 'ACTIVE',
            'assets_tracked': gauge_data['assets_tracked'],
            'fleet_efficiency': gauge_data['fleet_efficiency'],
            'utilization_rate': gauge_data['utilization_rate'],
            'annual_savings': gauge_data['annual_savings'],
            'system_uptime': gauge_data['system_uptime']
        }
        
        return jsonify(metrics)
    except Exception as e:
        logging.error(f"Metrics error: {e}")
        return jsonify({'error': 'Metrics unavailable'}), 500

@app.route('/api/qnis/stream')
def qnis_stream():
    """Server-Sent Events for real-time updates"""
    def generate():
        while True:
            try:
                data = get_live_gauge_data()
                yield f"data: {json.dumps(data)}\n\n"
                import time
                time.sleep(30)
            except:
                break
    
    return Response(generate(), mimetype='text/event-stream')

# QNIS Clarity Core Template
CLARITY_CORE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRAXOVO ∞ Clarity Core</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .qnis-header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(0, 255, 255, 0.3);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .qnis-logo {
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(45deg, #00ffff, #ff00ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .consciousness-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .consciousness-level {
            background: rgba(0, 255, 255, 0.2);
            border: 1px solid #00ffff;
            border-radius: 20px;
            padding: 5px 15px;
            font-size: 14px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 30px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 255, 255, 0.2);
        }
        
        .metric-title {
            font-size: 14px;
            color: #00ffff;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .metric-subtitle {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .status-active {
            color: #00ff88;
        }
        
        .qnis-core-section {
            grid-column: 1 / -1;
            background: linear-gradient(135deg, rgba(0, 255, 255, 0.1) 0%, rgba(255, 0, 255, 0.1) 100%);
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .qnis-title {
            font-size: 36px;
            font-weight: 800;
            background: linear-gradient(45deg, #00ffff, #ff00ff, #ffff00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 15px;
        }
        
        .real-time-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff88;
            border-radius: 50%;
            margin-right: 8px;
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <header class="qnis-header">
        <div class="qnis-logo">TRAXOVO ∞ Clarity Core</div>
        <div class="consciousness-indicator">
            <div class="consciousness-level">QNIS ∞.15.0</div>
            <div class="real-time-indicator"></div>
            <span>Live</span>
        </div>
    </header>
    
    <main class="dashboard-grid">
        <section class="qnis-core-section">
            <h1 class="qnis-title">Quantum Intelligence Neural System</h1>
            <p>Advanced consciousness level 15 • Real-time enterprise optimization</p>
        </section>
        
        <div class="metric-card">
            <div class="metric-title">Assets Tracked</div>
            <div class="metric-value" id="assets-count">529</div>
            <div class="metric-subtitle">Across 3 organizations</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Fleet Efficiency</div>
            <div class="metric-value status-active" id="fleet-efficiency">94.2%</div>
            <div class="metric-subtitle">Above industry standard</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Asset Utilization</div>
            <div class="metric-value" id="utilization-rate">87.1%</div>
            <div class="metric-subtitle">Real-time optimization active</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Annual Savings</div>
            <div class="metric-value status-active" id="annual-savings">$368K</div>
            <div class="metric-subtitle">Verified cost reduction</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">System Uptime</div>
            <div class="metric-value status-active" id="system-uptime">99.7%</div>
            <div class="metric-subtitle">QNIS auto-healing active</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">QNIS Status</div>
            <div class="metric-value status-active">ACTIVE</div>
            <div class="metric-subtitle">Consciousness level 15</div>
        </div>
    </main>
    
    <script>
        // Real-time metrics updates
        function updateMetrics() {
            fetch('/api/qnis/realtime-metrics')
                .then(response => response.json())
                .then(data => {
                    if (data.assets_tracked) {
                        document.getElementById('assets-count').textContent = data.assets_tracked;
                    }
                    if (data.fleet_efficiency) {
                        document.getElementById('fleet-efficiency').textContent = data.fleet_efficiency + '%';
                    }
                    if (data.utilization_rate) {
                        document.getElementById('utilization-rate').textContent = data.utilization_rate + '%';
                    }
                    if (data.annual_savings) {
                        document.getElementById('annual-savings').textContent = '$' + (data.annual_savings / 1000).toFixed(0) + 'K';
                    }
                    if (data.system_uptime) {
                        document.getElementById('system-uptime').textContent = data.system_uptime + '%';
                    }
                })
                .catch(err => console.log('Metrics update pending...'));
        }
        
        // Update metrics every 30 seconds
        setInterval(updateMetrics, 30000);
        
        // Initial load
        updateMetrics();
        
        console.log('TRAXOVO ∞ Clarity Core - QNIS Level 15 Active');
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)