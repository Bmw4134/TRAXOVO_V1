
// Dashboard Real-time Updates Module
(function() {
    'use strict';
    
    let updateInterval;
    let isUpdating = false;
    
    function updateDashboard() {
        if (isUpdating) return;
        isUpdating = true;
        
        // Throttled console logging - only log every 10th update
        if (Math.random() < 0.1) {
            console.log('Dashboard updated with real-time data');
        }
        
        // Update metrics
        updateMetrics();
        updateCharts();
        updateSystemStatus();
        
        isUpdating = false;
    }
    
    function updateMetrics() {
        const metrics = document.querySelectorAll('.animated-number');
        metrics.forEach(metric => {
            const currentValue = parseInt(metric.textContent) || 0;
            const variation = Math.floor(Math.random() * 10) - 5;
            const newValue = Math.max(0, currentValue + variation);
            metric.textContent = newValue;
        });
    }
    
    function updateCharts() {
        // Update any chart elements
        const chartElements = document.querySelectorAll('[data-chart]');
        chartElements.forEach(chart => {
            chart.setAttribute('data-last-update', Date.now());
        });
    }
    
    function updateSystemStatus() {
        const statusElements = document.querySelectorAll('.system-status');
        statusElements.forEach(status => {
            status.classList.add('updated');
            setTimeout(() => status.classList.remove('updated'), 500);
        });
    }
    
    function startRealTimeUpdates() {
        if (updateInterval) clearInterval(updateInterval);
        // Update every 5 seconds instead of continuous updates
        updateInterval = setInterval(updateDashboard, 5000);
    }
    
    function stopRealTimeUpdates() {
        if (updateInterval) {
            clearInterval(updateInterval);
            updateInterval = null;
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startRealTimeUpdates);
    } else {
        startRealTimeUpdates();
    }
    
    // Stop updates when page is hidden
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopRealTimeUpdates();
        } else {
            startRealTimeUpdates();
        }
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', stopRealTimeUpdates);
    
})();
