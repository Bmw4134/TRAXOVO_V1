/**
 * Quantum NEXUS Dynamic UI Controller
 * Replaces all static elements with real-time API-driven components
 */

class QuantumNexusDynamicUI {
    constructor() {
        this.apiEndpoints = {
            fleetMetrics: '/api/fleet-metrics',
            dynamicDashboard: '/api/dynamic-dashboard',
            realTimeAssets: '/api/real-time-assets',
            externalConnections: '/api/external-connections',
            quantumStatus: '/api/quantum-nexus-status'
        };
        
        this.refreshInterval = 30000; // 30 seconds
        this.dataCache = new Map();
        this.activeConnections = new Set();
        
        this.initialize();
    }
    
    async initialize() {
        console.log('Quantum NEXUS Dynamic UI Initializing...');
        
        // Initialize dynamic data streams
        await this.initializeDynamicStreams();
        
        // Start real-time updates
        this.startRealTimeUpdates();
        
        // Setup dynamic event listeners
        this.setupDynamicEventListeners();
        
        console.log('✓ Quantum NEXUS Dynamic UI Active');
    }
    
    async initializeDynamicStreams() {
        try {
            // Load all dynamic data simultaneously
            const promises = Object.entries(this.apiEndpoints).map(async ([key, endpoint]) => {
                try {
                    const response = await fetch(endpoint);
                    if (response.ok) {
                        const data = await response.json();
                        this.dataCache.set(key, data);
                        this.activeConnections.add(key);
                        return { key, data, status: 'connected' };
                    } else {
                        console.warn(`API endpoint ${endpoint} returned ${response.status}`);
                        return { key, status: 'error', error: response.status };
                    }
                } catch (error) {
                    console.warn(`Failed to connect to ${endpoint}:`, error);
                    return { key, status: 'error', error: error.message };
                }
            });
            
            const results = await Promise.all(promises);
            
            // Update UI with dynamic data
            this.updateDynamicDashboard(results);
            
        } catch (error) {
            console.error('Dynamic streams initialization error:', error);
        }
    }
    
    updateDynamicDashboard(apiResults) {
        // Update fleet metrics dynamically
        const fleetData = this.dataCache.get('fleetMetrics');
        if (fleetData && fleetData.status === 'success') {
            this.updateFleetMetrics(fleetData.data);
        }
        
        // Update dynamic dashboard components
        const dashboardData = this.dataCache.get('dynamicDashboard');
        if (dashboardData && dashboardData.status === 'success') {
            this.updateDashboardComponents(dashboardData.data);
        }
        
        // Update real-time asset display
        const assetData = this.dataCache.get('realTimeAssets');
        if (assetData && assetData.status === 'success') {
            this.updateAssetDisplay(assetData.data);
        }
        
        // Update connection status
        const connectionData = this.dataCache.get('externalConnections');
        if (connectionData && connectionData.status === 'success') {
            this.updateConnectionStatus(connectionData.data);
        }
    }
    
    updateFleetMetrics(metrics) {
        // Update total assets (dynamic)
        const totalAssetsElement = document.querySelector('.metric-value');
        if (totalAssetsElement && metrics.total_ragle_assets) {
            totalAssetsElement.textContent = metrics.total_ragle_assets.toLocaleString();
        }
        
        // Update all metric cards dynamically
        const metricCards = document.querySelectorAll('.metric-card');
        metricCards.forEach((card, index) => {
            const valueElement = card.querySelector('.metric-value');
            if (valueElement) {
                switch(index) {
                    case 0:
                        valueElement.textContent = `~${metrics.total_ragle_assets}`;
                        break;
                    case 1:
                        valueElement.textContent = metrics.active_assets;
                        break;
                    case 2:
                        valueElement.textContent = `${metrics.utilization}%`;
                        break;
                    case 3:
                        valueElement.textContent = `$${(metrics.fleet_value / 1000000).toFixed(0)}M`;
                        break;
                }
            }
        });
        
        // Update data source indicator
        const dataSourceElement = document.getElementById('data-source-indicator');
        if (dataSourceElement) {
            dataSourceElement.textContent = `Data Source: ${metrics.data_source || 'quantum_nexus_dynamic'}`;
            dataSourceElement.style.color = '#00ff88';
        }
    }
    
    updateDashboardComponents(dashboardData) {
        if (!dashboardData || dashboardData.error) return;
        
        // Update fleet metrics section
        if (dashboardData.fleet_metrics) {
            this.updateFleetSection(dashboardData.fleet_metrics);
        }
        
        // Update operational metrics
        if (dashboardData.operational_metrics) {
            this.updateOperationalSection(dashboardData.operational_metrics);
        }
        
        // Update financial metrics
        if (dashboardData.financial_metrics) {
            this.updateFinancialSection(dashboardData.financial_metrics);
        }
    }
    
    updateFleetSection(fleetMetrics) {
        // Update geographic scope dynamically
        const geoScopeElement = document.querySelector('.map-placeholder small');
        if (geoScopeElement && fleetMetrics.geographic_scope) {
            geoScopeElement.innerHTML = geoScopeElement.innerHTML.replace(
                /Texas to Indiana Operations|DFW Operations/,
                fleetMetrics.geographic_scope
            );
        }
        
        // Update utilization rate
        const utilizationElements = document.querySelectorAll('[data-metric="utilization"]');
        utilizationElements.forEach(element => {
            if (fleetMetrics.utilization_rate) {
                element.textContent = `${fleetMetrics.utilization_rate}%`;
            }
        });
    }
    
    updateOperationalSection(operationalMetrics) {
        // Update employee 210013 status
        const employeeStatusElements = document.querySelectorAll('[data-employee="210013"]');
        employeeStatusElements.forEach(element => {
            if (operationalMetrics.employee_210013_status === 'ACTIVE') {
                element.style.color = '#00ff88';
                element.textContent = 'ACTIVE';
            }
        });
        
        // Update active projects count
        const projectElements = document.querySelectorAll('[data-metric="projects"]');
        projectElements.forEach(element => {
            if (operationalMetrics.active_projects) {
                element.textContent = operationalMetrics.active_projects;
            }
        });
    }
    
    updateFinancialSection(financialMetrics) {
        // Update fleet value
        const fleetValueElements = document.querySelectorAll('[data-metric="fleet-value"]');
        fleetValueElements.forEach(element => {
            if (financialMetrics.total_fleet_value) {
                const valueInMillions = (financialMetrics.total_fleet_value / 1000000).toFixed(0);
                element.textContent = `$${valueInMillions}M`;
            }
        });
        
        // Update revenue metrics
        if (financialMetrics.monthly_revenue) {
            const revenueElements = document.querySelectorAll('[data-metric="revenue"]');
            revenueElements.forEach(element => {
                const revenueInMillions = (financialMetrics.monthly_revenue / 1000000).toFixed(1);
                element.textContent = `$${revenueInMillions}M`;
            });
        }
    }
    
    updateAssetDisplay(assetData) {
        if (!assetData || assetData.error) return;
        
        // Update asset count display
        const assetCountElements = document.querySelectorAll('[data-asset-count]');
        assetCountElements.forEach(element => {
            if (assetData.total_assets) {
                element.textContent = assetData.total_assets;
                element.setAttribute('data-last-updated', assetData.last_updated);
            }
        });
        
        // Update asset efficiency
        if (assetData.utilization_rate) {
            const efficiencyElements = document.querySelectorAll('[data-metric="efficiency"]');
            efficiencyElements.forEach(element => {
                element.textContent = `${assetData.utilization_rate}%`;
            });
        }
    }
    
    updateConnectionStatus(connectionData) {
        const connectionIndicator = document.getElementById('connection-status');
        if (connectionIndicator) {
            const connectedCount = Object.values(connectionData).filter(status => 
                status === 'CONNECTED').length;
            const totalConnections = Object.keys(connectionData).length;
            
            connectionIndicator.innerHTML = `
                <span style="color: #00ff88;">API Connections: ${connectedCount}/${totalConnections}</span>
                <br><small>GAUGE: ${connectionData.gauge || 'Unknown'}</small>
                <br><small>OpenAI: ${connectionData.openai || 'Unknown'}</small>
                <br><small>SendGrid: ${connectionData.sendgrid || 'Unknown'}</small>
            `;
        }
    }
    
    startRealTimeUpdates() {
        setInterval(async () => {
            try {
                // Refresh dynamic data
                await this.initializeDynamicStreams();
                
                // Update timestamp
                const timestampElements = document.querySelectorAll('[data-timestamp]');
                timestampElements.forEach(element => {
                    element.textContent = new Date().toLocaleTimeString();
                });
                
            } catch (error) {
                console.error('Real-time update error:', error);
            }
        }, this.refreshInterval);
    }
    
    setupDynamicEventListeners() {
        // Add dynamic refresh button functionality
        const refreshButton = document.getElementById('dynamic-refresh');
        if (refreshButton) {
            refreshButton.addEventListener('click', async () => {
                refreshButton.textContent = 'Refreshing...';
                await this.initializeDynamicStreams();
                refreshButton.textContent = 'Refresh Data';
            });
        }
        
        // Add dynamic drill-down functionality
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('dynamic-drilldown')) {
                this.handleDynamicDrillDown(event.target);
            }
        });
    }
    
    async handleDynamicDrillDown(element) {
        const category = element.getAttribute('data-category');
        if (!category) return;
        
        try {
            // Load specific category data dynamically
            const response = await fetch(`/api/category-details/${category}`);
            if (response.ok) {
                const data = await response.json();
                this.displayCategoryDetails(data, element);
            }
        } catch (error) {
            console.error('Dynamic drill-down error:', error);
        }
    }
    
    displayCategoryDetails(data, triggerElement) {
        // Create dynamic modal or update section with real data
        const detailContainer = document.getElementById('dynamic-details');
        if (detailContainer) {
            detailContainer.innerHTML = `
                <h3>Real-time ${data.category} Details</h3>
                <div class="dynamic-content">
                    ${JSON.stringify(data.details, null, 2)}
                </div>
                <p><small>Last updated: ${data.timestamp}</small></p>
            `;
            detailContainer.style.display = 'block';
        }
    }
    
    // Public method to get current dynamic status
    getDynamicStatus() {
        return {
            activeConnections: Array.from(this.activeConnections),
            cacheSize: this.dataCache.size,
            lastUpdate: new Date().toISOString(),
            refreshInterval: this.refreshInterval
        };
    }
}

// Initialize dynamic UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.quantumNexusUI = new QuantumNexusDynamicUI();
    
    // Add global refresh function
    window.refreshDynamicData = () => {
        return window.quantumNexusUI.initializeDynamicStreams();
    };
    
    // Add global status check
    window.getDynamicStatus = () => {
        return window.quantumNexusUI.getDynamicStatus();
    };
    
    console.log('Quantum NEXUS Dynamic UI Loaded Successfully');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuantumNexusDynamicUI;
}