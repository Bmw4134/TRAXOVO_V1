/*
TRAXOVO Performance Optimization - ES5 Compatible
Fixes syntax errors and improves dashboard responsiveness
*/

// Asset data caching to reduce API calls
var assetCache = {
    data: null,
    timestamp: null,
    expiry: 30000 // 30 seconds
};

// Check if cached data is still valid
function isCacheValid() {
    if (!assetCache.data || !assetCache.timestamp) {
        return false;
    }
    return (Date.now() - assetCache.timestamp) < assetCache.expiry;
}

// Get asset data with caching
function getCachedAssetData() {
    return new Promise(function(resolve, reject) {
        if (isCacheValid()) {
            resolve(assetCache.data);
            return;
        }
        
        fetch('/api/fleet/assets')
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                assetCache.data = data;
                assetCache.timestamp = Date.now();
                resolve(data);
            })
            .catch(function(error) {
                reject(error);
            });
    });
}

// Lazy load dashboard components
function initializeDashboard() {
    var loadingSpinner = document.getElementById('loading-spinner');
    var dashboardContent = document.getElementById('dashboard-content');
    
    if (loadingSpinner) {
        loadingSpinner.style.display = 'block';
    }
    
    getCachedAssetData()
        .then(function(data) {
            if (dashboardContent) {
                dashboardContent.style.opacity = '1';
            }
            if (loadingSpinner) {
                loadingSpinner.style.display = 'none';
            }
            updateDashboardMetrics(data);
        })
        .catch(function(error) {
            console.error('Dashboard loading error:', error);
            if (loadingSpinner) {
                loadingSpinner.style.display = 'none';
            }
        });
}

// Update dashboard metrics efficiently
function updateDashboardMetrics(data) {
    if (!data || !data.assets) return;
    
    var totalAssets = data.total_assets || 0;
    var activeAssets = data.active_assets || 0;
    var utilization = activeAssets > 0 ? ((activeAssets / totalAssets) * 100).toFixed(1) : 0;
    
    // Update metric displays
    var elements = {
        'total-assets': totalAssets,
        'active-assets': activeAssets,
        'utilization-rate': utilization + '%'
    };
    
    for (var id in elements) {
        var element = document.getElementById(id);
        if (element) {
            element.textContent = elements[id];
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    initializeDashboard();
}