/*
TRAXOVO Dashboard Stability - ES5 Compatible
Ensures all interactive elements work across browsers
*/

// Replace problematic ES6 syntax with ES5 equivalents
(function() {
    'use strict';
    
    // Asset data management
    var assetDataCache = null;
    var lastFetchTime = 0;
    var cacheExpiry = 30000; // 30 seconds
    
    // Initialize dashboard when DOM is ready
    function initializeDashboard() {
        // Add loading states
        var loadingElements = document.querySelectorAll('.metric-card');
        for (var i = 0; i < loadingElements.length; i++) {
            loadingElements[i].style.transition = 'opacity 0.3s ease';
        }
        
        // Load asset data with error handling
        loadAssetData();
        
        // Set up navigation handlers
        setupNavigationHandlers();
        
        // Set up responsive handlers
        setupResponsiveHandlers();
    }
    
    function loadAssetData() {
        var currentTime = Date.now();
        
        // Use cached data if still valid
        if (assetDataCache && (currentTime - lastFetchTime) < cacheExpiry) {
            updateDashboardDisplay(assetDataCache);
            return;
        }
        
        // Fetch fresh data
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/api/fleet/assets', true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);
                        assetDataCache = data;
                        lastFetchTime = currentTime;
                        updateDashboardDisplay(data);
                    } catch (e) {
                        console.error('Error parsing asset data:', e);
                        showErrorState();
                    }
                } else {
                    console.error('Asset data fetch failed:', xhr.status);
                    showErrorState();
                }
            }
        };
        xhr.send();
    }
    
    function updateDashboardDisplay(data) {
        if (!data || !data.success) {
            showErrorState();
            return;
        }
        
        // Update metric displays safely
        var metrics = {
            'total-assets': data.total_assets || 0,
            'active-assets': data.active_assets || 0,
            'utilization-rate': ((data.active_assets || 0) / (data.total_assets || 1) * 100).toFixed(1) + '%'
        };
        
        for (var id in metrics) {
            var element = document.getElementById(id);
            if (element) {
                element.textContent = metrics[id];
                element.style.opacity = '1';
            }
        }
    }
    
    function showErrorState() {
        var errorElements = document.querySelectorAll('.metric-value');
        for (var i = 0; i < errorElements.length; i++) {
            errorElements[i].textContent = '--';
            errorElements[i].style.opacity = '0.7';
        }
    }
    
    function setupNavigationHandlers() {
        var navLinks = document.querySelectorAll('.sidebar a, .nav-link');
        for (var i = 0; i < navLinks.length; i++) {
            navLinks[i].addEventListener('click', function(e) {
                // Add loading state to target
                var target = e.target;
                if (target.getAttribute('href') && target.getAttribute('href').indexOf('#') !== 0) {
                    target.style.opacity = '0.7';
                    setTimeout(function() {
                        target.style.opacity = '1';
                    }, 300);
                }
            });
        }
    }
    
    function setupResponsiveHandlers() {
        // Handle mobile menu toggles
        var mobileToggle = document.querySelector('.navbar-toggler');
        if (mobileToggle) {
            mobileToggle.addEventListener('click', function() {
                var sidebar = document.querySelector('.sidebar');
                if (sidebar) {
                    sidebar.classList.toggle('mobile-visible');
                }
            });
        }
        
        // Handle window resize
        window.addEventListener('resize', function() {
            var sidebar = document.querySelector('.sidebar');
            if (sidebar && window.innerWidth > 768) {
                sidebar.classList.remove('mobile-visible');
            }
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDashboard);
    } else {
        initializeDashboard();
    }
    
    // Refresh data periodically
    setInterval(function() {
        if (document.visibilityState === 'visible') {
            loadAssetData();
        }
    }, 60000); // Every minute
    
})();