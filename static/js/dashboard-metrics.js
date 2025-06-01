/*
TRAXOVO Dashboard Metrics Handler
Processes authentic GAUGE API data for dashboard display
*/

(function() {
    'use strict';
    
    var metricsData = null;
    var lastUpdate = 0;
    var updateInterval = 30000; // 30 seconds
    
    function initializeDashboardMetrics() {
        loadMetricsData();
        setupAutoRefresh();
        setupErrorHandling();
    }
    
    function loadMetricsData() {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/api/fleet/assets', true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);
                        if (data.success) {
                            metricsData = data;
                            lastUpdate = Date.now();
                            updateDashboardDisplay(data);
                            console.log('Dashboard metrics updated successfully');
                        } else {
                            console.error('API returned unsuccessful response:', data);
                            showErrorState();
                        }
                    } catch (e) {
                        console.error('Failed to parse metrics data:', e);
                        showErrorState();
                    }
                } else {
                    console.error('Failed to load metrics:', xhr.status);
                    showErrorState();
                }
            }
        };
        xhr.send();
    }
    
    function updateDashboardDisplay(data) {
        // Update main metric cards
        var metricMappings = {
            'total-assets': data.total_assets || 0,
            'active-assets': data.active_assets || 0,
            'inactive-assets': data.inactive_assets || 0,
            'categories': data.categories || 0,
            'utilization-rate': data.utilization_rate || 0,
            'districts': data.districts || 0,
            'makes': data.makes || 0
        };
        
        // Update each metric display
        for (var id in metricMappings) {
            var element = document.getElementById(id);
            if (element) {
                var value = metricMappings[id];
                if (id === 'utilization-rate') {
                    element.textContent = value + '%';
                } else {
                    element.textContent = value.toLocaleString();
                }
                
                // Add update animation
                element.style.opacity = '0.7';
                setTimeout(function(el) {
                    return function() {
                        el.style.opacity = '1';
                        el.style.transition = 'opacity 0.3s ease';
                    };
                }(element), 100);
            }
        }
        
        // Update metric cards with data attributes
        var metricCards = document.querySelectorAll('.metric-card [data-target]');
        for (var i = 0; i < metricCards.length; i++) {
            var card = metricCards[i];
            var target = card.getAttribute('data-target');
            if (metricMappings[target] !== undefined) {
                animateNumber(card, metricMappings[target]);
            }
        }
        
        // Update any chart data if charts exist
        if (window.updateChartsWithData) {
            window.updateChartsWithData(data);
        }
        
        // Update last refresh time
        var lastRefreshElement = document.getElementById('last-refresh');
        if (lastRefreshElement) {
            lastRefreshElement.textContent = new Date().toLocaleTimeString();
        }
    }
    
    function animateNumber(element, targetValue) {
        var startValue = parseInt(element.textContent) || 0;
        var duration = 1000;
        var startTime = Date.now();
        
        function updateValue() {
            var elapsed = Date.now() - startTime;
            var progress = Math.min(elapsed / duration, 1);
            var currentValue = Math.floor(startValue + (targetValue - startValue) * progress);
            
            if (element.textContent.includes('%')) {
                element.textContent = currentValue + '%';
            } else {
                element.textContent = currentValue.toLocaleString();
            }
            
            if (progress < 1) {
                requestAnimationFrame(updateValue);
            }
        }
        
        updateValue();
    }
    
    function showErrorState() {
        var errorElements = document.querySelectorAll('.metric-value, [data-target]');
        for (var i = 0; i < errorElements.length; i++) {
            errorElements[i].textContent = '--';
            errorElements[i].style.opacity = '0.5';
        }
        
        // Show error indicator
        var errorIndicator = document.getElementById('error-indicator');
        if (errorIndicator) {
            errorIndicator.style.display = 'block';
        }
    }
    
    function setupAutoRefresh() {
        setInterval(function() {
            if (document.visibilityState === 'visible') {
                loadMetricsData();
            }
        }, updateInterval);
    }
    
    function setupErrorHandling() {
        // Global error handler for metrics-related errors
        window.addEventListener('error', function(e) {
            if (e.message && e.message.includes('metrics')) {
                console.error('Metrics error detected:', e.message);
            }
        });
        
        // Handle refresh button if it exists
        var refreshButton = document.getElementById('refresh-metrics');
        if (refreshButton) {
            refreshButton.addEventListener('click', function() {
                refreshButton.disabled = true;
                refreshButton.textContent = 'Refreshing...';
                
                loadMetricsData();
                
                setTimeout(function() {
                    refreshButton.disabled = false;
                    refreshButton.textContent = 'Refresh';
                }, 2000);
            });
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDashboardMetrics);
    } else {
        initializeDashboardMetrics();
    }
    
    // Expose refresh function globally
    window.refreshDashboardMetrics = loadMetricsData;
    
})();