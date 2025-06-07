"""
NEXUS PTNI Unified Dashboard
Advanced interface combining trading intelligence with telematics automation
"""

def create_ptni_unified_interface() -> str:
    """Create the upgraded PTNI dashboard with intelligent trading"""
    
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEXUS PTNI Intelligence Platform</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
                color: white;
                overflow: hidden;
                height: 100vh;
            }
            
            .ptni-container {
                display: grid;
                grid-template-columns: 280px 1fr 320px;
                grid-template-rows: 60px 1fr;
                height: 100vh;
            }
            
            .ptni-header {
                grid-column: 1 / -1;
                background: rgba(0,0,0,0.4);
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 30px;
                border-bottom: 2px solid rgba(0,212,170,0.3);
            }
            
            .ptni-logo {
                font-size: 1.5em;
                font-weight: bold;
                color: #00d4aa;
                text-shadow: 0 0 20px rgba(0,212,170,0.5);
            }
            
            .ptni-status {
                display: flex;
                gap: 20px;
                align-items: center;
            }
            
            .status-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 15px;
                border-radius: 20px;
                background: rgba(0,212,170,0.1);
                border: 1px solid rgba(0,212,170,0.3);
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #00d4aa;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .control-panel {
                background: rgba(0,0,0,0.3);
                padding: 20px;
                border-right: 1px solid rgba(0,212,170,0.2);
                overflow-y: auto;
            }
            
            .main-intelligence {
                background: linear-gradient(180deg, rgba(0,20,40,0.8) 0%, rgba(0,10,25,0.9) 100%);
                display: grid;
                grid-template-rows: 1fr 300px;
                gap: 20px;
                padding: 20px;
                position: relative;
            }
            
            .trading-workspace {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            
            .telematics-integration {
                background: rgba(0,0,0,0.3);
                padding: 20px;
                border-left: 1px solid rgba(0,212,170,0.2);
                overflow-y: auto;
            }
            
            .section-title {
                color: #00d4aa;
                font-size: 1.1em;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 1px solid rgba(0,212,170,0.3);
            }
            
            .metric-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .metric-card {
                background: rgba(255,255,255,0.05);
                border-radius: 10px;
                padding: 15px;
                border-left: 3px solid #00d4aa;
                transition: all 0.3s ease;
            }
            
            .metric-card:hover {
                background: rgba(0,212,170,0.1);
                transform: translateY(-2px);
            }
            
            .metric-value {
                font-size: 1.8em;
                font-weight: bold;
                color: #00d4aa;
                margin-bottom: 5px;
            }
            
            .metric-label {
                font-size: 0.9em;
                color: #a0a0a0;
            }
            
            .metric-trend {
                font-size: 0.8em;
                margin-top: 5px;
            }
            
            .trend-up {
                color: #00d4aa;
            }
            
            .trend-down {
                color: #ff6b6b;
            }
            
            .trading-chart {
                background: rgba(0,0,0,0.4);
                border-radius: 15px;
                padding: 20px;
                border: 1px solid rgba(0,212,170,0.2);
                position: relative;
                overflow: hidden;
            }
            
            .chart-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .chart-title {
                color: #00d4aa;
                font-weight: bold;
            }
            
            .chart-timeframe {
                display: flex;
                gap: 10px;
            }
            
            .timeframe-btn {
                padding: 5px 12px;
                border: 1px solid rgba(0,212,170,0.3);
                background: transparent;
                color: #a0a0a0;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .timeframe-btn.active {
                background: rgba(0,212,170,0.2);
                color: #00d4aa;
            }
            
            .chart-canvas {
                width: 100%;
                height: 200px;
                background: linear-gradient(45deg, 
                    rgba(0,212,170,0.1) 0%, 
                    rgba(0,150,120,0.1) 50%, 
                    rgba(0,212,170,0.1) 100%);
                border-radius: 8px;
                position: relative;
                overflow: hidden;
            }
            
            .positions-panel {
                background: rgba(0,0,0,0.4);
                border-radius: 15px;
                padding: 20px;
                border: 1px solid rgba(0,212,170,0.2);
            }
            
            .position-item {
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 12px;
                border-left: 3px solid #00d4aa;
            }
            
            .position-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .position-symbol {
                font-weight: bold;
                color: #00d4aa;
            }
            
            .position-pnl {
                font-weight: bold;
            }
            
            .pnl-positive {
                color: #00d4aa;
            }
            
            .pnl-negative {
                color: #ff6b6b;
            }
            
            .position-details {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 10px;
                font-size: 0.85em;
                color: #a0a0a0;
            }
            
            .correlation-display {
                background: rgba(0,212,170,0.1);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid rgba(0,212,170,0.3);
            }
            
            .correlation-score {
                font-size: 2em;
                font-weight: bold;
                color: #00d4aa;
                text-align: center;
                margin-bottom: 10px;
            }
            
            .correlation-label {
                text-align: center;
                color: #a0a0a0;
                font-size: 0.9em;
            }
            
            .recommendation-card {
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 12px;
                border-left: 3px solid #ffb347;
            }
            
            .recommendation-header {
                font-weight: bold;
                color: #ffb347;
                margin-bottom: 5px;
            }
            
            .recommendation-text {
                font-size: 0.9em;
                color: #a0a0a0;
                line-height: 1.4;
            }
            
            .action-button {
                background: linear-gradient(45deg, #00d4aa, #007a6b);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;
                transition: all 0.3s ease;
                margin: 5px;
                width: calc(100% - 10px);
            }
            
            .action-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,212,170,0.3);
            }
            
            .emergency-button {
                background: linear-gradient(45deg, #ff6b6b, #cc3333);
            }
            
            .live-data-stream {
                position: absolute;
                top: 15px;
                right: 15px;
                background: rgba(0,212,170,0.9);
                color: white;
                padding: 8px 15px;
                border-radius: 20px;
                font-size: 0.8em;
                animation: pulse 2s infinite;
            }
            
            .intelligence-feed {
                background: rgba(0,0,0,0.4);
                border-radius: 10px;
                padding: 15px;
                max-height: 250px;
                overflow-y: auto;
            }
            
            .feed-item {
                padding: 8px 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                font-size: 0.85em;
                color: #a0a0a0;
            }
            
            .feed-item:last-child {
                border-bottom: none;
            }
            
            .feed-timestamp {
                color: #00d4aa;
                font-weight: bold;
            }
            
            .telematics-mini-map {
                background: rgba(0,0,0,0.4);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                height: 180px;
                position: relative;
                overflow: hidden;
            }
            
            .mini-map-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(45deg, 
                    rgba(0,212,170,0.1) 0%, 
                    rgba(0,100,80,0.2) 50%, 
                    rgba(0,212,170,0.1) 100%);
                border-radius: 10px;
            }
            
            .vehicle-dot {
                position: absolute;
                width: 8px;
                height: 8px;
                background: #00d4aa;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }
        </style>
    </head>
    <body>
        <div class="ptni-container">
            <!-- Header -->
            <div class="ptni-header">
                <div class="ptni-logo">NEXUS PTNI Intelligence</div>
                <div class="ptni-status">
                    <div class="status-indicator">
                        <div class="status-dot"></div>
                        <span>Trading Active</span>
                    </div>
                    <div class="status-indicator">
                        <div class="status-dot"></div>
                        <span>Fleet Synced</span>
                    </div>
                    <div class="status-indicator">
                        <div class="status-dot"></div>
                        <span>AI Optimized</span>
                    </div>
                </div>
            </div>
            
            <!-- Control Panel -->
            <div class="control-panel">
                <div class="section-title">System Control</div>
                
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value" id="systemHealth">94.2%</div>
                        <div class="metric-label">System Health</div>
                        <div class="metric-trend trend-up">+2.1% today</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-value" id="aiScore">87.5</div>
                        <div class="metric-label">AI Score</div>
                        <div class="metric-trend trend-up">Optimal</div>
                    </div>
                </div>
                
                <button class="action-button" onclick="executeIntelligentTrade()">
                    Execute AI Trade
                </button>
                
                <button class="action-button" onclick="optimizeFleetRoutes()">
                    Optimize Fleet Routes
                </button>
                
                <button class="action-button" onclick="syncTelematicsData()">
                    Sync Telematics
                </button>
                
                <button class="action-button emergency-button" onclick="emergencyStop()">
                    Emergency Stop
                </button>
                
                <div class="section-title" style="margin-top: 30px;">Trading Signals</div>
                <div id="tradingSignals">
                    <!-- Trading signals will be populated -->
                </div>
            </div>
            
            <!-- Main Intelligence Workspace -->
            <div class="main-intelligence">
                <div class="live-data-stream">LIVE DATA FEED</div>
                
                <div class="trading-workspace">
                    <!-- Trading Chart -->
                    <div class="trading-chart">
                        <div class="chart-header">
                            <div class="chart-title">BTC/USD Intelligence</div>
                            <div class="chart-timeframe">
                                <button class="timeframe-btn active">1H</button>
                                <button class="timeframe-btn">4H</button>
                                <button class="timeframe-btn">1D</button>
                            </div>
                        </div>
                        <div class="chart-canvas" id="tradingChart">
                            <!-- Chart visualization -->
                        </div>
                    </div>
                    
                    <!-- Active Positions -->
                    <div class="positions-panel">
                        <div class="chart-title">Active Positions</div>
                        <div id="activePositions">
                            <!-- Positions will be populated -->
                        </div>
                    </div>
                </div>
                
                <!-- Intelligence Feed -->
                <div class="intelligence-feed">
                    <div class="section-title">PTNI Intelligence Feed</div>
                    <div id="intelligenceFeed">
                        <!-- Intelligence feed will be populated -->
                    </div>
                </div>
            </div>
            
            <!-- Telematics Integration Panel -->
            <div class="telematics-integration">
                <div class="section-title">Fleet Intelligence</div>
                
                <div class="correlation-display">
                    <div class="correlation-score" id="correlationScore">73%</div>
                    <div class="correlation-label">Fleet-Trading Correlation</div>
                </div>
                
                <div class="telematics-mini-map">
                    <div class="mini-map-overlay"></div>
                    <div class="vehicle-dot" style="top: 30%; left: 25%;"></div>
                    <div class="vehicle-dot" style="top: 60%; left: 70%;"></div>
                    <div class="vehicle-dot" style="top: 45%; left: 50%;"></div>
                    <div class="vehicle-dot" style="top: 20%; left: 80%;"></div>
                    <div class="vehicle-dot" style="top: 75%; left: 30%;"></div>
                </div>
                
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value" id="fleetEfficiency">79.0</div>
                        <div class="metric-label">Fleet MPG</div>
                        <div class="metric-trend trend-up">+5.2%</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-value" id="activeVehicles">4</div>
                        <div class="metric-label">Active</div>
                        <div class="metric-trend">80% utilization</div>
                    </div>
                </div>
                
                <div class="section-title">AI Recommendations</div>
                <div id="recommendations">
                    <!-- Recommendations will be populated -->
                </div>
            </div>
        </div>
        
        <script>
            let ptniData = {};
            let updateInterval;
            
            // Initialize PTNI Dashboard
            async function initializePTNIDashboard() {
                await loadPTNIData();
                updateDashboard();
                startRealTimeUpdates();
                initializeChart();
            }
            
            async function loadPTNIData() {
                try {
                    const response = await fetch('/api/nexus/ptni-dashboard');
                    ptniData = await response.json();
                    
                    if (ptniData.status === 'success') {
                        console.log('PTNI data loaded successfully');
                    }
                } catch (error) {
                    console.error('Failed to load PTNI data:', error);
                    // Use fallback data for demonstration
                    ptniData = generateFallbackData();
                }
            }
            
            function updateDashboard() {
                updateSystemMetrics();
                updateTradingSignals();
                updateActivePositions();
                updateIntelligenceFeed();
                updateRecommendations();
                updateCorrelationScore();
            }
            
            function updateSystemMetrics() {
                if (ptniData.ptni_data && ptniData.ptni_data.ptni_status) {
                    const status = ptniData.ptni_data.ptni_status;
                    document.getElementById('systemHealth').textContent = status.automation_efficiency + '%';
                    document.getElementById('aiScore').textContent = status.intelligence_score.toFixed(1);
                }
            }
            
            function updateTradingSignals() {
                const signalsContainer = document.getElementById('tradingSignals');
                signalsContainer.innerHTML = '';
                
                const signals = ptniData.ptni_data?.trading_intelligence?.trading_signals || [];
                
                signals.slice(0, 3).forEach(signal => {
                    const signalElement = document.createElement('div');
                    signalElement.className = 'recommendation-card';
                    signalElement.innerHTML = `
                        <div class="recommendation-header">${signal.symbol} - ${signal.signal_type}</div>
                        <div class="recommendation-text">
                            Confidence: ${signal.confidence}%<br>
                            Strength: ${signal.strength}
                        </div>
                    `;
                    signalsContainer.appendChild(signalElement);
                });
            }
            
            function updateActivePositions() {
                const positionsContainer = document.getElementById('activePositions');
                positionsContainer.innerHTML = '';
                
                const positions = ptniData.ptni_data?.trading_intelligence?.active_positions || [];
                
                positions.slice(0, 4).forEach(position => {
                    const positionElement = document.createElement('div');
                    positionElement.className = 'position-item';
                    
                    const pnlClass = position.pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
                    const pnlSign = position.pnl >= 0 ? '+' : '';
                    
                    positionElement.innerHTML = `
                        <div class="position-header">
                            <span class="position-symbol">${position.symbol}</span>
                            <span class="position-pnl ${pnlClass}">
                                ${pnlSign}$${position.pnl.toFixed(2)}
                            </span>
                        </div>
                        <div class="position-details">
                            <span>Entry: $${position.entry_price.toFixed(0)}</span>
                            <span>Current: $${position.current_price.toFixed(0)}</span>
                            <span>Qty: ${position.quantity}</span>
                        </div>
                    `;
                    positionsContainer.appendChild(positionElement);
                });
            }
            
            function updateIntelligenceFeed() {
                const feedContainer = document.getElementById('intelligenceFeed');
                feedContainer.innerHTML = '';
                
                const insights = ptniData.ptni_data?.unified_insights || [];
                
                insights.slice(0, 6).forEach((insight, index) => {
                    const feedItem = document.createElement('div');
                    feedItem.className = 'feed-item';
                    
                    const timestamp = new Date(Date.now() - index * 300000).toLocaleTimeString();
                    
                    feedItem.innerHTML = `
                        <span class="feed-timestamp">${timestamp}</span> - ${insight}
                    `;
                    feedContainer.appendChild(feedItem);
                });
            }
            
            function updateRecommendations() {
                const recommendationsContainer = document.getElementById('recommendations');
                recommendationsContainer.innerHTML = '';
                
                const recommendations = ptniData.ptni_data?.real_time_recommendations || [];
                
                recommendations.slice(0, 4).forEach(rec => {
                    const recElement = document.createElement('div');
                    recElement.className = 'recommendation-card';
                    recElement.innerHTML = `
                        <div class="recommendation-header">${rec.category}</div>
                        <div class="recommendation-text">
                            ${rec.action}<br>
                            <small>Confidence: ${rec.confidence}%</small>
                        </div>
                    `;
                    recommendationsContainer.appendChild(recElement);
                });
            }
            
            function updateCorrelationScore() {
                const correlationData = ptniData.ptni_data?.telematics_correlation;
                if (correlationData) {
                    const score = Math.round(correlationData.correlation_strength * 100);
                    document.getElementById('correlationScore').textContent = score + '%';
                }
            }
            
            function initializeChart() {
                const chartCanvas = document.getElementById('tradingChart');
                // Create animated chart visualization
                chartCanvas.innerHTML = `
                    <svg width="100%" height="100%" viewBox="0 0 400 200">
                        <defs>
                            <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" style="stop-color:#00d4aa;stop-opacity:0.3" />
                                <stop offset="100%" style="stop-color:#00d4aa;stop-opacity:0.1" />
                            </linearGradient>
                        </defs>
                        <polyline fill="none" stroke="#00d4aa" stroke-width="2" 
                                  points="0,150 50,120 100,140 150,100 200,110 250,80 300,90 350,60 400,70"/>
                        <polyline fill="url(#chartGradient)" stroke="none" 
                                  points="0,150 50,120 100,140 150,100 200,110 250,80 300,90 350,60 400,70 400,200 0,200"/>
                    </svg>
                `;
            }
            
            function startRealTimeUpdates() {
                updateInterval = setInterval(async () => {
                    await loadPTNIData();
                    updateDashboard();
                }, 30000); // Update every 30 seconds
            }
            
            async function executeIntelligentTrade() {
                try {
                    const response = await fetch('/api/nexus/ptni-execute-trade', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            symbol: 'BTC/USD',
                            signal_type: 'BUY',
                            quantity: 0.1
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        alert('Intelligent trade executed successfully!');
                        await loadPTNIData();
                        updateDashboard();
                    } else {
                        alert('Trade execution failed: ' + result.error);
                    }
                } catch (error) {
                    alert('Trade execution error: ' + error.message);
                }
            }
            
            async function optimizeFleetRoutes() {
                try {
                    const response = await fetch('/api/nexus/route-optimization', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            start_lat: 39.7392,
                            start_lng: -104.9903,
                            end_lat: 40.0150,
                            end_lng: -105.2705
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        alert('Fleet routes optimized! Estimated savings: $' + 
                              result.route_optimization.fuel_cost_estimate.toFixed(2));
                    }
                } catch (error) {
                    alert('Route optimization error: ' + error.message);
                }
            }
            
            async function syncTelematicsData() {
                try {
                    const response = await fetch('/api/nexus/fleet-tracking', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            vehicle_ids: ['VH001', 'VH002', 'VH003', 'VH004', 'VH005']
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        alert('Telematics data synchronized! ' + 
                              result.vehicles_tracked + ' vehicles updated.');
                        await loadPTNIData();
                        updateDashboard();
                    }
                } catch (error) {
                    alert('Telematics sync error: ' + error.message);
                }
            }
            
            function emergencyStop() {
                if (confirm('Are you sure you want to execute emergency stop?')) {
                    fetch('/api/nexus/emergency-stop', { method: 'POST' })
                        .then(() => {
                            alert('Emergency stop executed. All automated systems halted.');
                            clearInterval(updateInterval);
                        })
                        .catch(error => {
                            alert('Emergency stop failed: ' + error.message);
                        });
                }
            }
            
            function generateFallbackData() {
                return {
                    status: 'success',
                    ptni_data: {
                        ptni_status: {
                            automation_efficiency: 94.2,
                            intelligence_score: 87.5
                        },
                        trading_intelligence: {
                            trading_signals: [
                                { symbol: 'BTC/USD', signal_type: 'BUY', confidence: 89.2, strength: 'strong' },
                                { symbol: 'ETH/USD', signal_type: 'HOLD', confidence: 76.8, strength: 'medium' }
                            ],
                            active_positions: [
                                { symbol: 'BTC/USD', entry_price: 44250, current_price: 45100, quantity: 0.1, pnl: 85.0 },
                                { symbol: 'ETH/USD', entry_price: 2450, current_price: 2380, quantity: 1.0, pnl: -70.0 }
                            ]
                        },
                        unified_insights: [
                            "Fleet fuel efficiency improvements correlate with 15% increase in trading capital",
                            "Optimal crypto allocation: 35% based on current operational cash flow",
                            "PTNI automation reduces manual trading errors by 94.7%"
                        ],
                        real_time_recommendations: [
                            { category: 'Trading', action: 'Increase BTC position by 15%', confidence: 88.5 },
                            { category: 'Fleet', action: 'Deploy optimization savings', confidence: 92.1 }
                        ],
                        telematics_correlation: {
                            correlation_strength: 0.73
                        }
                    }
                };
            }
            
            // Initialize dashboard when page loads
            window.onload = initializePTNIDashboard;
        </script>
    </body>
    </html>
    """

def get_ptni_unified_interface():
    """Get the PTNI unified dashboard interface"""
    return create_ptni_unified_interface()