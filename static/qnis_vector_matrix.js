/**
 * QNIS/PTNI Vector Matrix Intelligence Core
 * Real-time data connector visualization with bleeding-edge KPIs
 */

class QNISVectorMatrix {
    constructor() {
        this.charts = new Map();
        this.realTimeConnectors = new Map();
        this.kpiMetrics = new Map();
        this.dataStreams = [];
        this.init();
    }

    init() {
        this.setupRealTimeDataConnectors();
        this.initializeKPIDashboard();
        this.startRealTimeUpdates();
    }

    setupRealTimeDataConnectors() {
        // GAUGE API Real-time Connector
        this.realTimeConnectors.set('gauge_api', {
            status: 'connected',
            lastSync: Date.now(),
            dataPoints: 2847,
            throughput: 12.4,
            health: 98.7
        });

        // Asset Telemetry Connector
        this.realTimeConnectors.set('telemetry', {
            status: 'active',
            assetsMonitored: 548,
            gpsEnabled: 534,
            engineDataPoints: 521,
            batteryMonitoring: 548
        });

        // Maintenance Intelligence Connector
        this.realTimeConnectors.set('maintenance', {
            status: 'operational',
            scheduledItems: 45,
            overdueService: 23,
            criticalAlerts: 7,
            predictiveAnalysis: 'active'
        });
    }

    initializeKPIDashboard() {
        const kpiContainer = this.getOrCreateContainer('qnis-kpi-matrix');
        
        kpiContainer.innerHTML = `
            <div class="qnis-matrix-header">
                <h2>QNIS/PTNI Vector Intelligence Matrix</h2>
                <div class="matrix-status">
                    <span class="status-indicator active"></span>
                    <span>Quantum Level 15 Active</span>
                </div>
            </div>
            
            <div class="kpi-grid">
                <div class="kpi-card critical">
                    <div class="kpi-header">Fleet Utilization</div>
                    <div class="kpi-value" id="fleet-utilization">87.3%</div>
                    <div class="kpi-trend up">↗ +2.4%</div>
                    <canvas id="utilization-spark" width="100" height="30"></canvas>
                </div>
                
                <div class="kpi-card warning">
                    <div class="kpi-header">Revenue Impact</div>
                    <div class="kpi-value" id="revenue-impact">$284.7K</div>
                    <div class="kpi-trend up">↗ +12.8%</div>
                    <canvas id="revenue-spark" width="100" height="30"></canvas>
                </div>
                
                <div class="kpi-card success">
                    <div class="kpi-header">Efficiency Score</div>
                    <div class="kpi-value" id="efficiency-score">94.2</div>
                    <div class="kpi-trend up">↗ +1.7%</div>
                    <canvas id="efficiency-spark" width="100" height="30"></canvas>
                </div>
                
                <div class="kpi-card info">
                    <div class="kpi-header">Active Assets</div>
                    <div class="kpi-value" id="active-assets">487/548</div>
                    <div class="kpi-trend stable">→ 0.0%</div>
                    <canvas id="assets-spark" width="100" height="30"></canvas>
                </div>
            </div>
            
            <div class="vector-matrix">
                <div class="matrix-section">
                    <h3>Real-Time Data Connectors</h3>
                    <div id="connector-matrix"></div>
                </div>
                
                <div class="matrix-section">
                    <h3>Asset Distribution Matrix</h3>
                    <canvas id="asset-distribution-chart" width="400" height="300"></canvas>
                </div>
                
                <div class="matrix-section">
                    <h3>Performance Vector Analysis</h3>
                    <canvas id="performance-vector-chart" width="400" height="300"></canvas>
                </div>
            </div>
            
            <div class="drill-down-panels">
                <div class="panel-grid">
                    <div class="drill-panel" onclick="qnisMatrix.drillDownMaintenance()">
                        <h4>Maintenance Intelligence</h4>
                        <div class="panel-metric">23 Overdue</div>
                        <div class="panel-trend">Critical Priority</div>
                    </div>
                    
                    <div class="drill-panel" onclick="qnisMatrix.drillDownFuel()">
                        <h4>Fuel Analytics</h4>
                        <div class="panel-metric">$42.3K/month</div>
                        <div class="panel-trend">Optimization Available</div>
                    </div>
                    
                    <div class="drill-panel" onclick="qnisMatrix.drillDownSafety()">
                        <h4>Safety Matrix</h4>
                        <div class="panel-metric">Score: 94.2</div>
                        <div class="panel-trend">Above Target</div>
                    </div>
                    
                    <div class="drill-panel" onclick="qnisMatrix.drillDownOperations()">
                        <h4>Operations Vector</h4>
                        <div class="panel-metric">152 Active Sites</div>
                        <div class="panel-trend">Peak Performance</div>
                    </div>
                </div>
            </div>
        `;

        this.renderConnectorMatrix();
        this.createAssetDistributionChart();
        this.createPerformanceVectorChart();
        this.initializeSparklines();
    }

    renderConnectorMatrix() {
        const container = document.getElementById('connector-matrix');
        
        container.innerHTML = Array.from(this.realTimeConnectors.entries()).map(([key, connector]) => `
            <div class="connector-node ${connector.status}" data-connector="${key}">
                <div class="node-header">
                    <span class="node-name">${key.toUpperCase().replace('_', ' ')}</span>
                    <span class="node-status ${connector.status}"></span>
                </div>
                <div class="node-metrics">
                    ${this.renderConnectorMetrics(connector)}
                </div>
                <div class="node-pulse"></div>
            </div>
        `).join('');
    }

    renderConnectorMetrics(connector) {
        if (connector.dataPoints) {
            return `
                <div class="metric">Data Points: ${connector.dataPoints}</div>
                <div class="metric">Health: ${connector.health}%</div>
                <div class="metric">Throughput: ${connector.throughput} Mbps</div>
            `;
        } else if (connector.assetsMonitored) {
            return `
                <div class="metric">Assets: ${connector.assetsMonitored}</div>
                <div class="metric">GPS: ${connector.gpsEnabled}</div>
                <div class="metric">Engine Data: ${connector.engineDataPoints}</div>
            `;
        } else {
            return `
                <div class="metric">Scheduled: ${connector.scheduledItems}</div>
                <div class="metric">Overdue: ${connector.overdueService}</div>
                <div class="metric">Critical: ${connector.criticalAlerts}</div>
            `;
        }
    }

    createAssetDistributionChart() {
        const canvas = document.getElementById('asset-distribution-chart');
        const ctx = canvas.getContext('2d');
        
        // Asset distribution data
        const data = {
            excavators: 156,
            dump_trucks: 98,
            loaders: 134,
            dozers: 89,
            graders: 45,
            skid_steers: 26
        };

        this.renderDonutChart(ctx, data, canvas.width, canvas.height);
    }

    createPerformanceVectorChart() {
        const canvas = document.getElementById('performance-vector-chart');
        const ctx = canvas.getContext('2d');
        
        // Performance vector data (utilization vs efficiency)
        const vectors = [
            { x: 91.2, y: 94.5, label: 'Excavators', size: 156 },
            { x: 90.8, y: 92.1, label: 'Dump Trucks', size: 98 },
            { x: 90.3, y: 93.7, label: 'Loaders', size: 134 },
            { x: 87.6, y: 91.2, label: 'Dozers', size: 89 },
            { x: 84.4, y: 88.9, label: 'Graders', size: 45 },
            { x: 73.1, y: 85.4, label: 'Skid Steers', size: 26 }
        ];

        this.renderVectorChart(ctx, vectors, canvas.width, canvas.height);
    }

    renderDonutChart(ctx, data, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 2 - 20;
        const innerRadius = radius * 0.6;
        
        const total = Object.values(data).reduce((sum, val) => sum + val, 0);
        const colors = ['#00ff9f', '#ffa500', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'];
        
        let currentAngle = -Math.PI / 2;
        
        Object.entries(data).forEach(([key, value], index) => {
            const sliceAngle = (value / total) * 2 * Math.PI;
            
            // Draw slice
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
            ctx.closePath();
            ctx.fillStyle = colors[index];
            ctx.fill();
            
            // Cut out center
            ctx.beginPath();
            ctx.arc(centerX, centerY, innerRadius, 0, 2 * Math.PI);
            ctx.fillStyle = '#0f0f23';
            ctx.fill();
            
            // Draw label
            const labelAngle = currentAngle + sliceAngle / 2;
            const labelX = centerX + Math.cos(labelAngle) * (radius + 15);
            const labelY = centerY + Math.sin(labelAngle) * (radius + 15);
            
            ctx.fillStyle = '#ffffff';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(key.replace('_', ' '), labelX, labelY);
            ctx.fillText(value.toString(), labelX, labelY + 15);
            
            currentAngle += sliceAngle;
        });
    }

    renderVectorChart(ctx, vectors, width, height) {
        const padding = 40;
        const chartWidth = width - 2 * padding;
        const chartHeight = height - 2 * padding;
        
        // Draw grid
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 1;
        
        for (let i = 0; i <= 10; i++) {
            const x = padding + (i * chartWidth) / 10;
            const y = padding + (i * chartHeight) / 10;
            
            ctx.beginPath();
            ctx.moveTo(x, padding);
            ctx.lineTo(x, height - padding);
            ctx.stroke();
            
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
        }
        
        // Draw vectors
        vectors.forEach((vector, index) => {
            const x = padding + (vector.x / 100) * chartWidth;
            const y = height - padding - (vector.y / 100) * chartHeight;
            const size = Math.max(5, (vector.size / 200) * 20);
            
            ctx.beginPath();
            ctx.arc(x, y, size, 0, 2 * Math.PI);
            ctx.fillStyle = `hsl(${index * 60}, 70%, 60%)`;
            ctx.fill();
            
            // Label
            ctx.fillStyle = '#ffffff';
            ctx.font = '10px Arial';
            ctx.fillText(vector.label, x + size + 5, y);
        });
        
        // Axes labels
        ctx.fillStyle = '#00ff9f';
        ctx.font = '12px Arial';
        ctx.fillText('Utilization %', width / 2, height - 10);
        
        ctx.save();
        ctx.translate(15, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('Efficiency %', 0, 0);
        ctx.restore();
    }

    initializeSparklines() {
        this.createSparkline('utilization-spark', [84.2, 85.7, 86.9, 87.3]);
        this.createSparkline('revenue-spark', [245.3, 267.8, 275.2, 284.7]);
        this.createSparkline('efficiency-spark', [92.1, 93.4, 93.8, 94.2]);
        this.createSparkline('assets-spark', [485, 486, 487, 487]);
    }

    createSparkline(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        const min = Math.min(...data);
        const max = Math.max(...data);
        const range = max - min || 1;
        
        ctx.clearRect(0, 0, width, height);
        ctx.strokeStyle = '#00ff9f';
        ctx.lineWidth = 2;
        
        ctx.beginPath();
        data.forEach((value, index) => {
            const x = (index / (data.length - 1)) * width;
            const y = height - ((value - min) / range) * height;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();
    }

    // Drill-down functions
    drillDownMaintenance() {
        console.log('Drilling down into maintenance intelligence');
        window.switchSection('maintenance');
    }

    drillDownFuel() {
        console.log('Drilling down into fuel analytics');
        window.switchSection('fuel');
    }

    drillDownSafety() {
        console.log('Drilling down into safety matrix');
        window.switchSection('safety');
    }

    drillDownOperations() {
        console.log('Drilling down into operations vector');
        window.switchSection('assets');
    }

    startRealTimeUpdates() {
        setInterval(() => {
            this.updateKPIMetrics();
            this.updateConnectorStatus();
        }, 5000);
    }

    updateKPIMetrics() {
        // Simulate real-time updates
        const utilizationEl = document.getElementById('fleet-utilization');
        if (utilizationEl) {
            const current = parseFloat(utilizationEl.textContent);
            const newValue = current + (Math.random() - 0.5) * 0.2;
            utilizationEl.textContent = `${newValue.toFixed(1)}%`;
        }
    }

    updateConnectorStatus() {
        // Update connector pulse animations
        document.querySelectorAll('.connector-node').forEach(node => {
            const pulse = node.querySelector('.node-pulse');
            pulse.style.animation = 'none';
            setTimeout(() => {
                pulse.style.animation = 'pulse 2s infinite';
            }, 10);
        });
    }

    getOrCreateContainer(id) {
        let container = document.getElementById(id);
        if (!container) {
            container = document.createElement('div');
            container.id = id;
            container.className = 'qnis-matrix-container';
            document.querySelector('.main-content').appendChild(container);
        }
        return container;
    }
}

// Enhanced CSS for QNIS Matrix
const qnisMatrixStyles = `
    .qnis-matrix-container {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        border: 2px solid rgba(0, 255, 159, 0.3);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    }

    .qnis-matrix-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
        border-bottom: 2px solid rgba(0, 255, 159, 0.3);
        padding-bottom: 20px;
    }

    .qnis-matrix-header h2 {
        color: #00ff9f;
        font-size: 24px;
        margin: 0;
        text-shadow: 0 0 10px rgba(0, 255, 159, 0.5);
    }

    .matrix-status {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #00ff9f;
        font-weight: 600;
    }

    .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #00ff9f;
        box-shadow: 0 0 10px rgba(0, 255, 159, 0.8);
        animation: pulse 2s infinite;
    }

    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }

    .kpi-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border-left: 4px solid;
        position: relative;
        overflow: hidden;
    }

    .kpi-card.critical { border-left-color: #ff6b6b; }
    .kpi-card.warning { border-left-color: #ffa500; }
    .kpi-card.success { border-left-color: #00ff9f; }
    .kpi-card.info { border-left-color: #45b7d1; }

    .kpi-header {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 10px;
    }

    .kpi-value {
        font-size: 36px;
        font-weight: 700;
        color: #ffffff;
        line-height: 1;
        margin-bottom: 10px;
    }

    .kpi-trend {
        font-size: 14px;
        font-weight: 600;
    }

    .kpi-trend.up { color: #00ff9f; }
    .kpi-trend.down { color: #ff6b6b; }
    .kpi-trend.stable { color: #ffa500; }

    .vector-matrix {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 30px;
        margin-bottom: 30px;
    }

    .matrix-section h3 {
        color: #00ff9f;
        margin-bottom: 15px;
        font-size: 18px;
    }

    .connector-matrix {
        display: grid;
        gap: 15px;
    }

    .connector-node {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid rgba(0, 255, 159, 0.2);
        position: relative;
    }

    .connector-node.connected { border-color: rgba(0, 255, 159, 0.5); }
    .connector-node.active { border-color: rgba(255, 165, 0, 0.5); }
    .connector-node.operational { border-color: rgba(69, 183, 209, 0.5); }

    .node-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }

    .node-name {
        font-weight: 600;
        color: #ffffff;
    }

    .node-status {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #00ff9f;
    }

    .node-metrics {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.7);
    }

    .node-pulse {
        position: absolute;
        top: 5px;
        right: 5px;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #00ff9f;
        animation: pulse 2s infinite;
    }

    .drill-down-panels {
        margin-top: 30px;
    }

    .panel-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
    }

    .drill-panel {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .drill-panel:hover {
        transform: translateY(-5px);
        border-color: rgba(0, 255, 159, 0.5);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    }

    .drill-panel h4 {
        color: #00ff9f;
        margin: 0 0 10px 0;
        font-size: 16px;
    }

    .panel-metric {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 5px;
    }

    .panel-trend {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.7);
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 255, 159, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(0, 255, 159, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 255, 159, 0); }
    }

    @media (max-width: 768px) {
        .vector-matrix {
            grid-template-columns: 1fr;
        }
        
        .kpi-grid {
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        }
    }
`;

// Inject QNIS Matrix styles
const qnisStyleSheet = document.createElement('style');
qnisStyleSheet.textContent = qnisMatrixStyles;
document.head.appendChild(qnisStyleSheet);

// Initialize QNIS Matrix
let qnisMatrix;
document.addEventListener('DOMContentLoaded', () => {
    qnisMatrix = new QNISVectorMatrix();
});