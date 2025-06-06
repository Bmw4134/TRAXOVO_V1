/**
 * NEXUS Relay Dashboard Server
 * Visual relay panel with real-time AI communication monitoring
 */

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

class RelayDashboard {
    constructor() {
        this.app = express();
        this.server = http.createServer(this.app);
        this.io = socketIo(this.server, {
            cors: {
                origin: "*",
                methods: ["GET", "POST"]
            }
        });
        
        this.relayStatus = {
            chatgpt: { status: 'unknown', lastResponse: null, responseTime: 0 },
            perplexity: { status: 'unknown', lastResponse: null, responseTime: 0 },
            replit: { status: 'unknown', lastResponse: null, responseTime: 0 }
        };
        
        this.activeSessions = new Map();
        this.setupMiddleware();
        this.setupRoutes();
        this.setupSocketHandlers();
    }

    setupMiddleware() {
        this.app.use(cors());
        this.app.use(express.json());
        this.app.use(express.static(path.join(__dirname, 'public')));
    }

    setupRoutes() {
        // Mount relay dashboard at /relay-agent
        this.app.get('/relay-agent', (req, res) => {
            res.send(this.generateDashboardHTML());
        });

        // API endpoints for relay control
        this.app.post('/api/relay/start', async (req, res) => {
            const { prompt, sessionId } = req.body;
            
            try {
                const NexusBot = require('./nexus-bot');
                const config = JSON.parse(fs.readFileSync('../relay.config.json', 'utf8'));
                const bot = new NexusBot(config);
                
                await bot.initialize();
                const result = await bot.startAICommLoop(sessionId || `session_${Date.now()}`, prompt);
                
                // Update relay status
                this.updateRelayStatus(result);
                
                // Broadcast to connected clients
                this.io.emit('relayUpdate', {
                    type: 'completion',
                    data: result
                });
                
                res.json(result);
                
            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        this.app.get('/api/relay/status', (req, res) => {
            res.json({
                relayStatus: this.relayStatus,
                activeSessions: Array.from(this.activeSessions.values()),
                trinitySync: this.checkTrinitySync()
            });
        });

        this.app.get('/api/relay/logs', (req, res) => {
            try {
                const logsDir = path.join(__dirname, '../logs');
                const logFiles = fs.readdirSync(logsDir)
                    .filter(file => file.endsWith('.json'))
                    .sort((a, b) => fs.statSync(path.join(logsDir, b)).mtime - fs.statSync(path.join(logsDir, a)).mtime)
                    .slice(0, 10);

                const logs = logFiles.map(file => {
                    const content = JSON.parse(fs.readFileSync(path.join(logsDir, file), 'utf8'));
                    return {
                        filename: file,
                        ...content
                    };
                });

                res.json(logs);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });
    }

    setupSocketHandlers() {
        this.io.on('connection', (socket) => {
            console.log('[RELAY] Client connected to dashboard');
            
            // Send current status
            socket.emit('relayStatus', this.relayStatus);
            
            socket.on('requestTrinityTest', async () => {
                try {
                    const testResult = await this.performTrinityTest();
                    socket.emit('trinityTestResult', testResult);
                } catch (error) {
                    socket.emit('trinityTestResult', {
                        success: false,
                        error: error.message
                    });
                }
            });
            
            socket.on('disconnect', () => {
                console.log('[RELAY] Client disconnected from dashboard');
            });
        });
    }

    updateRelayStatus(result) {
        if (result.responses) {
            result.responses.forEach(response => {
                if (this.relayStatus[response.agent]) {
                    this.relayStatus[response.agent] = {
                        status: 'operational',
                        lastResponse: response.timestamp,
                        responseTime: response.response.responseTime || 0
                    };
                }
            });
        }
    }

    checkTrinitySync() {
        const allOperational = Object.values(this.relayStatus).every(
            agent => agent.status === 'operational'
        );
        
        return {
            status: allOperational ? 'synced' : 'partial',
            timestamp: new Date().toISOString()
        };
    }

    async performTrinityTest() {
        const NexusBot = require('./nexus-bot');
        const config = JSON.parse(fs.readFileSync('../relay.config.json', 'utf8'));
        const bot = new NexusBot(config);
        
        await bot.initialize();
        return await bot.startAICommLoop('trinity_test', 'Perform trinity sync test');
    }

    generateDashboardHTML() {
        return `
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS Relay Trinity Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="/socket.io/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            background: #0a0a0a;
            color: #00ff00;
            padding: 20px;
            min-height: 100vh;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 1px solid #00ff00;
            padding-bottom: 20px;
        }
        .header h1 {
            font-size: 24px;
            color: #00ff00;
            text-shadow: 0 0 10px #00ff00;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        .agent-card {
            background: #111;
            border: 1px solid #00ff00;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        .agent-card h3 {
            margin-bottom: 15px;
            font-size: 16px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-operational { background: #00ff00; box-shadow: 0 0 10px #00ff00; }
        .status-error { background: #ff0000; box-shadow: 0 0 10px #ff0000; }
        .status-unknown { background: #666; }
        .control-panel {
            background: #111;
            border: 1px solid #00ff00;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .control-panel h3 {
            margin-bottom: 15px;
            color: #00ff00;
        }
        .input-group {
            margin-bottom: 15px;
        }
        .input-group input {
            width: 100%;
            padding: 10px;
            background: #222;
            border: 1px solid #00ff00;
            color: #00ff00;
            border-radius: 4px;
        }
        .btn {
            background: #003300;
            border: 1px solid #00ff00;
            color: #00ff00;
            padding: 10px 20px;
            cursor: pointer;
            border-radius: 4px;
            margin-right: 10px;
        }
        .btn:hover {
            background: #00ff00;
            color: #000;
        }
        .logs-panel {
            background: #111;
            border: 1px solid #00ff00;
            border-radius: 8px;
            padding: 20px;
            height: 300px;
            overflow-y: auto;
        }
        .log-entry {
            margin-bottom: 5px;
            font-size: 12px;
        }
        .trinity-status {
            text-align: center;
            margin-bottom: 20px;
            padding: 15px;
            background: #111;
            border: 1px solid #00ff00;
            border-radius: 8px;
        }
        .trinity-synced { border-color: #00ff00; color: #00ff00; }
        .trinity-partial { border-color: #ffff00; color: #ffff00; }
        .trinity-failed { border-color: #ff0000; color: #ff0000; }
        .response-time {
            font-size: 12px;
            color: #888;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>NEXUS RELAY TRINITY DASHBOARD</h1>
        <p>AI-to-AI Communication Network Monitor</p>
    </div>

    <div class="trinity-status" id="trinityStatus">
        <h3>Trinity Sync Status: <span id="trinityStatusText">Checking...</span></h3>
    </div>

    <div class="status-grid">
        <div class="agent-card">
            <h3>ChatGPT Agent</h3>
            <div><span class="status-indicator status-unknown" id="chatgptStatus"></span><span id="chatgptText">Unknown</span></div>
            <div class="response-time" id="chatgptTime">Response Time: --</div>
        </div>
        <div class="agent-card">
            <h3>Perplexity Agent</h3>
            <div><span class="status-indicator status-unknown" id="perplexityStatus"></span><span id="perplexityText">Unknown</span></div>
            <div class="response-time" id="perplexityTime">Response Time: --</div>
        </div>
        <div class="agent-card">
            <h3>Replit Agent</h3>
            <div><span class="status-indicator status-unknown" id="replitStatus"></span><span id="replitText">Unknown</span></div>
            <div class="response-time" id="replitTime">Response Time: --</div>
        </div>
    </div>

    <div class="control-panel">
        <h3>Relay Control</h3>
        <div class="input-group">
            <input type="text" id="promptInput" placeholder="Enter prompt to relay through AI network...">
        </div>
        <button class="btn" onclick="startRelay()">Start AI Relay</button>
        <button class="btn" onclick="performTrinityTest()">Trinity Test</button>
        <button class="btn" onclick="refreshStatus()">Refresh Status</button>
    </div>

    <div class="logs-panel">
        <h3>Real-time Relay Logs</h3>
        <div id="logsContainer"></div>
    </div>

    <script>
        const socket = io();
        
        socket.on('relayStatus', (status) => {
            updateAgentStatus('chatgpt', status.chatgpt);
            updateAgentStatus('perplexity', status.perplexity);
            updateAgentStatus('replit', status.replit);
        });

        socket.on('relayUpdate', (update) => {
            addLog(\`Relay Update: \${JSON.stringify(update)}\`);
        });

        socket.on('trinityTestResult', (result) => {
            addLog(\`Trinity Test: \${result.success ? 'PASSED' : 'FAILED'}\`);
            if (result.error) {
                addLog(\`Error: \${result.error}\`);
            }
        });

        function updateAgentStatus(agent, status) {
            const statusEl = document.getElementById(agent + 'Status');
            const textEl = document.getElementById(agent + 'Text');
            const timeEl = document.getElementById(agent + 'Time');
            
            statusEl.className = 'status-indicator status-' + status.status;
            textEl.textContent = status.status.charAt(0).toUpperCase() + status.status.slice(1);
            timeEl.textContent = \`Response Time: \${status.responseTime}ms\`;
        }

        function addLog(message) {
            const container = document.getElementById('logsContainer');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.textContent = \`[\${new Date().toLocaleTimeString()}] \${message}\`;
            container.appendChild(entry);
            container.scrollTop = container.scrollHeight;
        }

        async function startRelay() {
            const prompt = document.getElementById('promptInput').value;
            if (!prompt) return;
            
            addLog(\`Starting relay with prompt: \${prompt}\`);
            
            try {
                const response = await fetch('/api/relay/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt })
                });
                
                const result = await response.json();
                addLog(\`Relay \${result.success ? 'completed' : 'failed'}\`);
                
            } catch (error) {
                addLog(\`Relay error: \${error.message}\`);
            }
        }

        function performTrinityTest() {
            addLog('Performing Trinity sync test...');
            socket.emit('requestTrinityTest');
        }

        async function refreshStatus() {
            try {
                const response = await fetch('/api/relay/status');
                const data = await response.json();
                
                updateAgentStatus('chatgpt', data.relayStatus.chatgpt);
                updateAgentStatus('perplexity', data.relayStatus.perplexity);
                updateAgentStatus('replit', data.relayStatus.replit);
                
                const trinityEl = document.getElementById('trinityStatus');
                const trinityTextEl = document.getElementById('trinityStatusText');
                
                trinityEl.className = 'trinity-status trinity-' + data.trinitySync.status;
                trinityTextEl.textContent = data.trinitySync.status.toUpperCase();
                
                addLog('Status refreshed');
                
            } catch (error) {
                addLog(\`Status refresh error: \${error.message}\`);
            }
        }

        // Auto-refresh every 30 seconds
        setInterval(refreshStatus, 30000);
        refreshStatus();
    </script>
</body>
</html>
        `;
    }

    start(port = 4888) {
        this.server.listen(port, () => {
            console.log(`[RELAY] Dashboard server running on port ${port}`);
            console.log(`[RELAY] Access dashboard at: http://localhost:${port}/relay-agent`);
        });
    }
}

// Start the dashboard server
const dashboard = new RelayDashboard();
dashboard.start(4888);

module.exports = RelayDashboard;