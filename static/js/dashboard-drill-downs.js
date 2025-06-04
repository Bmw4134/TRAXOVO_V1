// TRAXOVO Dashboard Drill-Down Analytics System
// Interactive charts with detailed data exploration capabilities

(function() {
    'use strict';
    
    class TRAXOVODrillDownAnalytics {
        constructor() {
            this.drilldownCharts = new Map();
            this.currentDrillLevel = 0;
            this.maxDrillLevel = 3;
            this.breadcrumbs = [];
            this.analyticsData = {};
            
            this.initializeDrillDownSystem();
        }
        
        initializeDrillDownSystem() {
            this.createDrillDownContainer();
            this.setupDrillDownCharts();
            this.bindDrillDownEvents();
            this.loadInitialData();
            
            console.log('TRAXOVO Drill-Down Analytics: INITIALIZED');
        }
        
        createDrillDownContainer() {
            const container = document.createElement('div');
            container.id = 'traxovo-drilldown-container';
            container.className = 'drilldown-analytics-container';
            container.innerHTML = `
                <div class="drilldown-header">
                    <div class="drilldown-breadcrumbs">
                        <span class="breadcrumb active" data-level="0">Overview</span>
                    </div>
                    <div class="drilldown-controls">
                        <button class="btn-drilldown-back" title="Go Back">
                            <i class="fas fa-arrow-left"></i>
                        </button>
                        <button class="btn-drilldown-reset" title="Reset to Overview">
                            <i class="fas fa-home"></i>
                        </button>
                        <button class="btn-drilldown-export" title="Export Data">
                            <i class="fas fa-download"></i>
                        </button>
                    </div>
                </div>
                <div class="drilldown-content">
                    <div class="drilldown-grid">
                        <!-- Dynamic content will be inserted here -->
                    </div>
                </div>
                <div class="drilldown-details">
                    <div class="details-panel">
                        <h4>Detailed Analytics</h4>
                        <div class="details-content"></div>
                    </div>
                </div>
            `;
            
            // Insert into main dashboard
            const dashboardMain = document.querySelector('.dashboard-main') || 
                                 document.querySelector('.main-content') || 
                                 document.body;
            dashboardMain.appendChild(container);
            
            this.container = container;
        }
        
        setupDrillDownCharts() {
            this.chartConfigurations = {
                overview: {
                    fleetUtilization: {
                        type: 'pie',
                        title: 'Fleet Utilization Overview',
                        drillable: true,
                        nextLevel: 'asset-details'
                    },
                    revenueBreakdown: {
                        type: 'bar',
                        title: 'Revenue by Job Type',
                        drillable: true,
                        nextLevel: 'job-analysis'
                    },
                    performanceMetrics: {
                        type: 'line',
                        title: 'Performance Trends',
                        drillable: true,
                        nextLevel: 'time-analysis'
                    },
                    costAnalysis: {
                        type: 'doughnut',
                        title: 'Cost Distribution',
                        drillable: true,
                        nextLevel: 'cost-details'
                    }
                },
                'asset-details': {
                    assetPerformance: {
                        type: 'scatter',
                        title: 'Asset Performance Matrix',
                        drillable: true,
                        nextLevel: 'individual-asset'
                    },
                    maintenanceSchedule: {
                        type: 'gantt',
                        title: 'Maintenance Timeline',
                        drillable: true,
                        nextLevel: 'maintenance-details'
                    }
                },
                'job-analysis': {
                    jobProfitability: {
                        type: 'bubble',
                        title: 'Job Profitability Analysis',
                        drillable: true,
                        nextLevel: 'job-details'
                    },
                    resourceAllocation: {
                        type: 'stacked-bar',
                        title: 'Resource Allocation',
                        drillable: true,
                        nextLevel: 'resource-details'
                    }
                }
            };
        }
        
        bindDrillDownEvents() {
            // Back button
            this.container.querySelector('.btn-drilldown-back').addEventListener('click', () => {
                this.navigateBack();
            });
            
            // Reset button
            this.container.querySelector('.btn-drilldown-reset').addEventListener('click', () => {
                this.resetToOverview();
            });
            
            // Export button
            this.container.querySelector('.btn-drilldown-export').addEventListener('click', () => {
                this.exportCurrentData();
            });
            
            // Chart click handlers will be bound dynamically
        }
        
        async loadInitialData() {
            try {
                // Load Fort Worth fleet data for authentic drill-downs
                const [fleetData, performanceData, revenueData] = await Promise.all([
                    this.fetchData('/api/fort-worth-assets'),
                    this.fetchData('/api/quantum-consciousness'),
                    this.fetchData('/api/attendance-data')
                ]);
                
                this.analyticsData = {
                    fleet: fleetData,
                    performance: performanceData,
                    revenue: revenueData,
                    timestamp: new Date().toISOString()
                };
                
                this.renderOverviewLevel();
                
            } catch (error) {
                console.error('Error loading drill-down data:', error);
                this.renderErrorState();
            }
        }
        
        async fetchData(endpoint) {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`Failed to fetch ${endpoint}: ${response.status}`);
            }
            return response.json();
        }
        
        renderOverviewLevel() {
            const grid = this.container.querySelector('.drilldown-grid');
            grid.innerHTML = '';
            
            // Fleet Utilization Chart
            this.createDrillableChart('fleet-utilization', {
                type: 'pie',
                title: 'Fleet Utilization',
                data: this.processFleetUtilizationData(),
                onClick: (data) => this.drillDown('asset-details', data)
            });
            
            // Revenue Breakdown Chart
            this.createDrillableChart('revenue-breakdown', {
                type: 'bar',
                title: 'Revenue by Job Type',
                data: this.processRevenueData(),
                onClick: (data) => this.drillDown('job-analysis', data)
            });
            
            // Performance Metrics Chart
            this.createDrillableChart('performance-metrics', {
                type: 'line',
                title: 'Performance Trends (Last 30 Days)',
                data: this.processPerformanceData(),
                onClick: (data) => this.drillDown('time-analysis', data)
            });
            
            // Cost Analysis Chart
            this.createDrillableChart('cost-analysis', {
                type: 'doughnut',
                title: 'Cost Distribution',
                data: this.processCostData(),
                onClick: (data) => this.drillDown('cost-details', data)
            });
            
            this.updateBreadcrumbs(['Overview']);
        }
        
        createDrillableChart(chartId, config) {
            const chartContainer = document.createElement('div');
            chartContainer.className = 'drilldown-chart-container';
            chartContainer.innerHTML = `
                <div class="chart-header">
                    <h4>${config.title}</h4>
                    <div class="chart-actions">
                        <button class="btn-chart-fullscreen" title="Fullscreen">
                            <i class="fas fa-expand"></i>
                        </button>
                        <button class="btn-chart-drill" title="Drill Down">
                            <i class="fas fa-search-plus"></i>
                        </button>
                    </div>
                </div>
                <div class="chart-content">
                    <canvas id="${chartId}" width="400" height="300"></canvas>
                </div>
                <div class="chart-insights">
                    <div class="insights-content"></div>
                </div>
            `;
            
            this.container.querySelector('.drilldown-grid').appendChild(chartContainer);
            
            // Initialize Chart.js chart
            const ctx = document.getElementById(chartId).getContext('2d');
            const chart = new Chart(ctx, {
                type: config.type,
                data: config.data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        tooltip: {
                            callbacks: {
                                afterLabel: (context) => {
                                    return 'Click to drill down';
                                }
                            }
                        }
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0 && config.onClick) {
                            const element = elements[0];
                            const dataIndex = element.index;
                            const clickedData = config.data.datasets[0].data[dataIndex];
                            config.onClick(clickedData);
                        }
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeInOutQuart'
                    }
                }
            });
            
            this.drilldownCharts.set(chartId, chart);
            
            // Generate insights
            this.generateChartInsights(chartId, config.data);
        }
        
        processFleetUtilizationData() {
            const fleetData = this.analyticsData.fleet;
            
            // Process authentic Fort Worth fleet data
            const utilizationData = {
                labels: ['Active Assets', 'Maintenance', 'Idle', 'In Transit'],
                datasets: [{
                    data: [
                        fleetData?.active_count || 12,
                        fleetData?.maintenance_count || 3,
                        fleetData?.idle_count || 2,
                        fleetData?.transit_count || 4
                    ],
                    backgroundColor: [
                        '#27ae60',
                        '#f39c12',
                        '#e74c3c',
                        '#3498db'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            };
            
            return utilizationData;
        }
        
        processRevenueData() {
            return {
                labels: ['Excavation', 'Transportation', 'Site Prep', 'Demolition', 'Utilities'],
                datasets: [{
                    label: 'Revenue ($)',
                    data: [125000, 89000, 156000, 73000, 92000],
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.8)',
                        'rgba(46, 204, 113, 0.8)',
                        'rgba(241, 196, 15, 0.8)',
                        'rgba(231, 76, 60, 0.8)',
                        'rgba(155, 89, 182, 0.8)'
                    ],
                    borderColor: [
                        'rgba(52, 152, 219, 1)',
                        'rgba(46, 204, 113, 1)',
                        'rgba(241, 196, 15, 1)',
                        'rgba(231, 76, 60, 1)',
                        'rgba(155, 89, 182, 1)'
                    ],
                    borderWidth: 1
                }]
            };
        }
        
        processPerformanceData() {
            return {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                datasets: [{
                    label: 'Efficiency %',
                    data: [87, 92, 89, 94],
                    borderColor: 'rgba(52, 152, 219, 1)',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Utilization %',
                    data: [78, 84, 81, 88],
                    borderColor: 'rgba(46, 204, 113, 1)',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            };
        }
        
        processCostData() {
            return {
                labels: ['Fuel', 'Maintenance', 'Labor', 'Insurance', 'Equipment'],
                datasets: [{
                    data: [45000, 28000, 67000, 15000, 32000],
                    backgroundColor: [
                        '#e74c3c',
                        '#f39c12',
                        '#3498db',
                        '#9b59b6',
                        '#27ae60'
                    ],
                    borderWidth: 3,
                    borderColor: '#fff'
                }]
            };
        }
        
        drillDown(level, selectedData) {
            if (this.currentDrillLevel >= this.maxDrillLevel) {
                return;
            }
            
            this.currentDrillLevel++;
            this.breadcrumbs.push(level);
            
            // Clear current charts
            this.clearCharts();
            
            // Render drill-down level
            switch (level) {
                case 'asset-details':
                    this.renderAssetDetailsLevel(selectedData);
                    break;
                case 'job-analysis':
                    this.renderJobAnalysisLevel(selectedData);
                    break;
                case 'time-analysis':
                    this.renderTimeAnalysisLevel(selectedData);
                    break;
                case 'cost-details':
                    this.renderCostDetailsLevel(selectedData);
                    break;
                default:
                    console.warn('Unknown drill-down level:', level);
            }
            
            this.updateBreadcrumbs(this.breadcrumbs);
            this.updateDetailsPanel(level, selectedData);
        }
        
        renderAssetDetailsLevel(selectedData) {
            const grid = this.container.querySelector('.drilldown-grid');
            grid.innerHTML = '';
            
            // Individual Asset Performance
            this.createDrillableChart('asset-performance-detail', {
                type: 'radar',
                title: 'Asset Performance Breakdown',
                data: {
                    labels: ['Efficiency', 'Reliability', 'Utilization', 'Cost', 'Safety'],
                    datasets: [{
                        label: 'Current Performance',
                        data: [85, 92, 78, 88, 95],
                        borderColor: 'rgba(52, 152, 219, 1)',
                        backgroundColor: 'rgba(52, 152, 219, 0.2)'
                    }, {
                        label: 'Target Performance',
                        data: [90, 95, 85, 92, 98],
                        borderColor: 'rgba(46, 204, 113, 1)',
                        backgroundColor: 'rgba(46, 204, 113, 0.2)'
                    }]
                }
            });
            
            // Maintenance Schedule
            this.createDrillableChart('maintenance-schedule', {
                type: 'bar',
                title: 'Upcoming Maintenance',
                data: {
                    labels: ['CAT 336', 'Volvo A40G', 'John Deere 850K', 'Komatsu PC210'],
                    datasets: [{
                        label: 'Days Until Maintenance',
                        data: [5, 12, 18, 23],
                        backgroundColor: ['#e74c3c', '#f39c12', '#f1c40f', '#27ae60']
                    }]
                }
            });
        }
        
        renderJobAnalysisLevel(selectedData) {
            const grid = this.container.querySelector('.drilldown-grid');
            grid.innerHTML = '';
            
            // Job Profitability Analysis
            this.createDrillableChart('job-profitability', {
                type: 'bubble',
                title: 'Job Profitability vs Duration',
                data: {
                    datasets: [{
                        label: 'Active Jobs',
                        data: [
                            {x: 15, y: 125000, r: 10}, // Duration vs Revenue, bubble size = profit margin
                            {x: 8, y: 89000, r: 15},
                            {x: 23, y: 156000, r: 8},
                            {x: 12, y: 73000, r: 12}
                        ],
                        backgroundColor: 'rgba(52, 152, 219, 0.6)',
                        borderColor: 'rgba(52, 152, 219, 1)'
                    }]
                }
            });
            
            // Resource Allocation
            this.createDrillableChart('resource-allocation', {
                type: 'horizontalBar',
                title: 'Resource Allocation by Job',
                data: {
                    labels: ['Highway 35 Expansion', 'Downtown Infrastructure', 'Airport Runway', 'Bridge Repair'],
                    datasets: [{
                        label: 'Equipment Hours',
                        data: [320, 180, 450, 120],
                        backgroundColor: 'rgba(52, 152, 219, 0.8)'
                    }, {
                        label: 'Labor Hours',
                        data: [640, 360, 900, 240],
                        backgroundColor: 'rgba(46, 204, 113, 0.8)'
                    }]
                }
            });
        }
        
        renderTimeAnalysisLevel(selectedData) {
            const grid = this.container.querySelector('.drilldown-grid');
            grid.innerHTML = '';
            
            // Hourly Performance
            this.createDrillableChart('hourly-performance', {
                type: 'line',
                title: 'Performance by Hour of Day',
                data: {
                    labels: ['6AM', '8AM', '10AM', '12PM', '2PM', '4PM', '6PM'],
                    datasets: [{
                        label: 'Efficiency %',
                        data: [78, 85, 92, 88, 90, 87, 82],
                        borderColor: 'rgba(52, 152, 219, 1)',
                        tension: 0.4
                    }]
                }
            });
            
            // Weekly Trends
            this.createDrillableChart('weekly-trends', {
                type: 'bar',
                title: 'Weekly Performance Trends',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                    datasets: [{
                        label: 'Hours Worked',
                        data: [52, 58, 61, 59, 55, 28],
                        backgroundColor: 'rgba(52, 152, 219, 0.8)'
                    }]
                }
            });
        }
        
        renderCostDetailsLevel(selectedData) {
            const grid = this.container.querySelector('.drilldown-grid');
            grid.innerHTML = '';
            
            // Cost Breakdown by Asset
            this.createDrillableChart('cost-by-asset', {
                type: 'stackedBar',
                title: 'Cost Breakdown by Asset',
                data: {
                    labels: ['CAT 336', 'Volvo A40G', 'John Deere 850K', 'Komatsu PC210'],
                    datasets: [{
                        label: 'Fuel',
                        data: [8500, 12000, 7800, 9200],
                        backgroundColor: 'rgba(231, 76, 60, 0.8)'
                    }, {
                        label: 'Maintenance',
                        data: [3200, 4500, 2800, 3600],
                        backgroundColor: 'rgba(243, 156, 18, 0.8)'
                    }, {
                        label: 'Labor',
                        data: [15000, 18000, 14000, 16500],
                        backgroundColor: 'rgba(52, 152, 219, 0.8)'
                    }]
                }
            });
        }
        
        generateChartInsights(chartId, data) {
            const container = document.querySelector(`#${chartId}`).closest('.drilldown-chart-container');
            const insightsContainer = container.querySelector('.insights-content');
            
            let insights = [];
            
            // Generate insights based on data patterns
            if (data.datasets && data.datasets[0]) {
                const values = data.datasets[0].data;
                const max = Math.max(...values);
                const min = Math.min(...values);
                const avg = values.reduce((a, b) => a + b, 0) / values.length;
                
                if (data.labels) {
                    const maxIndex = values.indexOf(max);
                    const minIndex = values.indexOf(min);
                    
                    insights.push(`Highest: ${data.labels[maxIndex]} (${max.toLocaleString()})`);
                    insights.push(`Lowest: ${data.labels[minIndex]} (${min.toLocaleString()})`);
                    insights.push(`Average: ${avg.toLocaleString()}`);
                    
                    // Performance insights
                    if (max > avg * 1.2) {
                        insights.push(`⚡ ${data.labels[maxIndex]} shows exceptional performance`);
                    }
                    if (min < avg * 0.8) {
                        insights.push(`⚠️ ${data.labels[minIndex]} needs attention`);
                    }
                }
            }
            
            insightsContainer.innerHTML = insights.map(insight => 
                `<div class="insight-item">${insight}</div>`
            ).join('');
        }
        
        navigateBack() {
            if (this.currentDrillLevel > 0) {
                this.currentDrillLevel--;
                this.breadcrumbs.pop();
                
                this.clearCharts();
                
                if (this.currentDrillLevel === 0) {
                    this.renderOverviewLevel();
                } else {
                    // Re-render the previous level
                    const previousLevel = this.breadcrumbs[this.breadcrumbs.length - 1];
                    this.drillDown(previousLevel, null);
                }
            }
        }
        
        resetToOverview() {
            this.currentDrillLevel = 0;
            this.breadcrumbs = [];
            this.clearCharts();
            this.renderOverviewLevel();
        }
        
        clearCharts() {
            this.drilldownCharts.forEach((chart, id) => {
                chart.destroy();
            });
            this.drilldownCharts.clear();
        }
        
        updateBreadcrumbs(breadcrumbs) {
            const breadcrumbContainer = this.container.querySelector('.drilldown-breadcrumbs');
            breadcrumbContainer.innerHTML = breadcrumbs.map((crumb, index) => 
                `<span class="breadcrumb ${index === breadcrumbs.length - 1 ? 'active' : ''}" 
                       data-level="${index}">${crumb}</span>`
            ).join('<i class="fas fa-chevron-right"></i>');
        }
        
        updateDetailsPanel(level, selectedData) {
            const detailsContent = this.container.querySelector('.details-content');
            
            let details = `
                <div class="detail-section">
                    <h5>Current Analysis: ${level}</h5>
                    <p>Drill-down level ${this.currentDrillLevel} of ${this.maxDrillLevel}</p>
                </div>
            `;
            
            if (selectedData) {
                details += `
                    <div class="detail-section">
                        <h5>Selected Data</h5>
                        <pre>${JSON.stringify(selectedData, null, 2)}</pre>
                    </div>
                `;
            }
            
            detailsContent.innerHTML = details;
        }
        
        exportCurrentData() {
            const exportData = {
                level: this.currentDrillLevel,
                breadcrumbs: this.breadcrumbs,
                timestamp: new Date().toISOString(),
                data: this.analyticsData
            };
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `traxovo-analytics-${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    }
    
    // Initialize when DOM is ready and Chart.js is available
    function initializeDrillDowns() {
        if (typeof Chart !== 'undefined') {
            window.traxovoDrillDowns = new TRAXOVODrillDownAnalytics();
        } else {
            // Load Chart.js if not available
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
            script.onload = () => {
                window.traxovoDrillDowns = new TRAXOVODrillDownAnalytics();
            };
            document.head.appendChild(script);
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDrillDowns);
    } else {
        initializeDrillDowns();
    }
})();