
/**
 * TRAXOVO Real Data Dashboard
 * Handles real-time updates with integrated data
 */

(function() {
    'use strict';
    
    class RealDataDashboard {
        constructor() {
            this.isRealDataMode = true;
            this.dataCache = new Map();
            this.updateInterval = 10000; // 10 seconds for real data
            this.init();
        }
        
        init() {
            this.checkDataIntegrationStatus();
            this.startRealTimeUpdates();
            this.addDataSourceIndicators();
        }
        
        async checkDataIntegrationStatus() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                if (status.modules_active) {
                    this.displayDataIntegrationStatus('active');
                } else {
                    this.displayDataIntegrationStatus('integrating');
                }
            } catch (error) {
                console.warn('Could not check integration status:', error);
                this.displayDataIntegrationStatus('unknown');
            }
        }
        
        displayDataIntegrationStatus(status) {
            const statusElement = document.createElement('div');
            statusElement.className = 'data-integration-status';
            statusElement.innerHTML = `
                <div class="alert alert-${status === 'active' ? 'success' : 'warning'} alert-dismissible fade show">
                    <i class="fas fa-database me-2"></i>
                    <strong>Real Data Integration:</strong> 
                    ${status === 'active' ? 'Active - Using live data from 16GB dataset' : 'Processing - Integrating real data files'}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            
            const container = document.querySelector('.container-fluid') || document.body;
            container.insertBefore(statusElement, container.firstChild);
        }
        
        async updateRealTimeData() {
            const endpoints = [
                { url: '/ragle/api/data', target: 'ragle-metrics' },
                { url: '/api/attendance', target: 'attendance-metrics' },
                { url: '/api/equipment', target: 'equipment-metrics' },
                { url: '/api/geofences', target: 'geofences-metrics' }
            ];
            
            for (const endpoint of endpoints) {
                try {
                    const response = await fetch(endpoint.url);
                    const data = await response.json();
                    
                    this.dataCache.set(endpoint.target, data);
                    this.updateDashboardMetrics(endpoint.target, data);
                    
                } catch (error) {
                    console.warn(`Failed to update ${endpoint.target}:`, error);
                }
            }
        }
        
        updateDashboardMetrics(target, data) {
            // Update metric cards based on real data
            if (target === 'ragle-metrics' && data.systems) {
                this.updateMetricCard('processing-units', data.systems.processing_units);
                this.updateMetricCard('active-connections', data.systems.active_connections);
                this.updateMetricCard('efficiency-rating', data.systems.efficiency_rating);
            }
            
            if (target === 'attendance-metrics') {
                this.updateMetricCard('personnel-present', data.personnel_present || data.status);
                this.updateMetricCard('total-hours', data.total_hours_today || data.hours_today);
                this.updateMetricCard('weekly-hours', data.weekly_hours);
            }
            
            if (target === 'equipment-metrics') {
                this.updateMetricCard('total-equipment', data.total_equipment);
                this.updateMetricCard('active-rentals', data.active_rentals);
                this.updateMetricCard('monthly-revenue', data.monthly_revenue);
                this.updateMetricCard('utilization-rate', data.utilization_rate);
            }
            
            if (target === 'geofences-metrics') {
                this.updateMetricCard('active-geofences', data.active_geofences);
                this.updateMetricCard('assets-tracked', data.assets_tracked);
                this.updateMetricCard('compliance-rate', data.compliance_rate);
            }
        }
        
        updateMetricCard(metricId, value) {
            const elements = document.querySelectorAll(`[data-metric="${metricId}"], .${metricId}, #${metricId}`);
            
            elements.forEach(element => {
                if (element) {
                    // Add real data indicator
                    element.classList.add('real-data-active');
                    
                    // Update the value
                    if (typeof value === 'number') {
                        this.animateNumberChange(element, value);
                    } else {
                        element.textContent = value;
                    }
                    
                    // Add pulsing effect for real-time updates
                    element.classList.add('data-updated');
                    setTimeout(() => element.classList.remove('data-updated'), 1000);
                }
            });
        }
        
        animateNumberChange(element, newValue) {
            const currentValue = parseInt(element.textContent) || 0;
            const difference = newValue - currentValue;
            const steps = 20;
            const stepValue = difference / steps;
            let currentStep = 0;
            
            const animation = setInterval(() => {
                currentStep++;
                const displayValue = Math.round(currentValue + (stepValue * currentStep));
                element.textContent = displayValue;
                
                if (currentStep >= steps) {
                    clearInterval(animation);
                    element.textContent = newValue;
                }
            }, 50);
        }
        
        addDataSourceIndicators() {
            // Add indicators showing data is real
            const style = document.createElement('style');
            style.textContent = `
                .real-data-active::after {
                    content: "●";
                    color: #28a745;
                    margin-left: 5px;
                    animation: pulse 2s infinite;
                }
                
                .data-updated {
                    background-color: rgba(40, 167, 69, 0.1) !important;
                    border-left: 3px solid #28a745;
                    transition: all 0.3s ease;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                
                .data-integration-status {
                    position: sticky;
                    top: 0;
                    z-index: 1000;
                    margin-bottom: 1rem;
                }
            `;
            document.head.appendChild(style);
        }
        
        startRealTimeUpdates() {
            // Initial update
            this.updateRealTimeData();
            
            // Set up interval for real-time updates
            setInterval(() => {
                this.updateRealTimeData();
            }, this.updateInterval);
            
            console.log('TRAXOVO Real Data Dashboard: Started with live data integration');
        }
        
        // Method to trigger manual data refresh
        refreshData() {
            this.updateRealTimeData();
            this.checkDataIntegrationStatus();
        }
        
        // Get cached data for external use
        getCachedData(target) {
            return this.dataCache.get(target);
        }
    }
    
    // Initialize real data dashboard
    window.TRAXOVORealDataDashboard = new RealDataDashboard();
    
    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('TRAXOVO Real Data Dashboard: Fully operational with integrated data');
        });
    }
    
})();
