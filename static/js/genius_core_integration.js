/**
 * TRAXORA GENIUS CORE | Data Integration Manager
 * 
 * This module connects the GENIUS CORE agent architecture to real data from
 * the asset map and other system modules.
 */

class GeniusCoreIntegration {
    constructor() {
        // Check if the required components are available
        if (!window.GeniusCore) {
            console.error('GENIUS CORE not available. Integration aborted.');
            return;
        }
        
        this.geniusCore = window.GeniusCore;
        this.assetData = {};
        this.jobSiteData = {};
        
        // Setup integration points
        this.setupMapIntegration();
        this.setupAssetDataListener();
        this.setupJobSiteListener();
        
        // Register with GENIUS CORE
        this.integrationAgent = {
            id: 'IntegrationManager',
            
            handleMessage(message) {
                switch (message.type) {
                    case 'sync-status':
                        return {
                            status: 'sync-status',
                            assetCount: Object.keys(window.Integration.assetData).length,
                            jobSiteCount: Object.keys(window.Integration.jobSiteData).length,
                            lastSync: new Date().toISOString()
                        };
                        
                    default:
                        return { status: 'unknown-message-type' };
                }
            }
        };
        
        this.geniusCore.registerAgent('IntegrationManager', this.integrationAgent);
        
        // Update module status
        if (window.ModuleStatus) {
            window.ModuleStatus.updateModuleStatus('asset-map', 'connected', 95, {
                assetsLoaded: true,
                jobSitesLoaded: true,
                recommendationsActive: true
            });
        }
        
        console.log('GENIUS CORE Integration Manager initialized');
    }
    
    setupMapIntegration() {
        // Monitor when the map loads and assets are displayed
        const originalLoadAssets = window.loadAssets;
        
        if (originalLoadAssets) {
            window.loadAssets = function() {
                // Call the original function
                const result = originalLoadAssets.apply(this, arguments);
                
                // Capture data for GENIUS CORE
                if (window.Integration && window.assetData) {
                    window.Integration.captureAssetData(window.assetData);
                }
                
                return result;
            };
        }
        
        const originalLoadJobSites = window.loadJobSites;
        
        if (originalLoadJobSites) {
            window.loadJobSites = function() {
                // Call the original function
                const result = originalLoadJobSites.apply(this, arguments);
                
                // Capture data for GENIUS CORE
                if (window.Integration && window.jobSites) {
                    window.Integration.captureJobSiteData(window.jobSites);
                }
                
                return result;
            };
        }
    }
    
    setupAssetDataListener() {
        // Create a MutationObserver to watch for asset data changes in the DOM
        // This is a fallback in case direct function interception doesn't work
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (mutation.type === 'childList' && 
                    mutation.target.id === 'map-container' &&
                    window.assetData) {
                    
                    this.captureAssetData(window.assetData);
                }
            }
        });
        
        // Start observing the document body
        observer.observe(document.body, { childList: true, subtree: true });
    }
    
    setupJobSiteListener() {
        // Create a MutationObserver to watch for job site data changes in the DOM
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (mutation.type === 'childList' && 
                    mutation.target.id === 'map-container' &&
                    window.jobSites) {
                    
                    this.captureJobSiteData(window.jobSites);
                }
            }
        });
        
        // Start observing the document body
        observer.observe(document.body, { childList: true, subtree: true });
    }
    
    captureAssetData(assetData) {
        if (!Array.isArray(assetData)) return;
        
        console.log(`Capturing ${assetData.length} assets for GENIUS CORE`);
        
        // Store asset data locally
        assetData.forEach(asset => {
            this.assetData[asset.id] = asset;
            
            // Send asset to AssetTracker agent
            this.geniusCore.sendMessage(
                'IntegrationManager',
                'AssetTracker',
                'asset-update',
                asset
            );
            
            // Check for anomalies
            if (asset.last_update) {
                const lastUpdateDate = new Date(asset.last_update);
                const currentDate = new Date();
                const diffTime = Math.abs(currentDate - lastUpdateDate);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                
                // Check for long inactive assets
                if (diffDays > 30) {
                    this.geniusCore.sendMessage(
                        'IntegrationManager',
                        'AnomalyDetector',
                        'check-anomaly',
                        {
                            type: 'asset-inactive',
                            assetId: asset.id,
                            inactiveDays: diffDays,
                            assetType: asset.type
                        }
                    );
                }
            }
            
            // Look for site conflicts (assets that could be at multiple job sites)
            if (asset.latitude && asset.longitude && Object.keys(this.jobSiteData).length > 0) {
                this.checkForSiteConflicts(asset);
            }
        });
        
        // Update module status
        if (window.ModuleStatus) {
            window.ModuleStatus.updateModuleStatus('asset-map', 'operational', 100, {
                assetsLoaded: true,
                assetCount: Object.keys(this.assetData).length,
                lastUpdate: new Date().toISOString()
            });
        }
    }
    
    captureJobSiteData(jobSiteData) {
        if (!Array.isArray(jobSiteData)) return;
        
        console.log(`Capturing ${jobSiteData.length} job sites for GENIUS CORE`);
        
        // Store job site data locally
        jobSiteData.forEach(site => {
            this.jobSiteData[site.id] = site;
            
            // Send job site to JobSiteMonitor agent
            this.geniusCore.sendMessage(
                'IntegrationManager',
                'JobSiteMonitor',
                'site-update',
                site
            );
        });
        
        // Now that we have job sites, check all assets for site conflicts
        Object.values(this.assetData).forEach(asset => {
            if (asset.latitude && asset.longitude) {
                this.checkForSiteConflicts(asset);
            }
        });
    }
    
    checkForSiteConflicts(asset) {
        // Find all job sites that contain this asset
        const matchingSites = [];
        
        Object.values(this.jobSiteData).forEach(site => {
            if (!site.latitude || !site.longitude || !site.radius) return;
            
            // Calculate distance between asset and site center
            const distance = this.calculateDistance(
                asset.latitude, asset.longitude,
                site.latitude, site.longitude
            );
            
            // If asset is within radius, add to matching sites
            if (distance <= site.radius) {
                matchingSites.push({
                    site: site,
                    distance: distance
                });
                
                // Record asset at this site
                this.geniusCore.sendMessage(
                    'IntegrationManager',
                    'JobSiteMonitor',
                    'asset-at-site',
                    {
                        assetId: asset.id,
                        siteId: site.id
                    }
                );
            }
        });
        
        // If there are multiple matching sites, check for conflicts
        if (matchingSites.length > 1) {
            // Sort by distance (closest first)
            matchingSites.sort((a, b) => a.distance - b.distance);
            
            // Request recommendations
            this.geniusCore.sendMessage(
                'IntegrationManager',
                'RecommendationEngine',
                'request-recommendation',
                {
                    assetId: asset.id,
                    assetType: asset.type,
                    sites: matchingSites.map(match => match.site)
                }
            );
            
            // Record potential conflict
            this.geniusCore.sendMessage(
                'IntegrationManager',
                'AnomalyDetector',
                'check-anomaly',
                {
                    type: 'site-conflict',
                    assetId: asset.id,
                    sites: matchingSites.map(match => match.site.id),
                    timestamp: new Date().toISOString()
                }
            );
        }
    }
    
    calculateDistance(lat1, lon1, lat2, lon2) {
        // Haversine formula to calculate distance between two points
        const R = 6371000; // Radius of the earth in meters
        const dLat = this.deg2rad(lat2 - lat1);
        const dLon = this.deg2rad(lon2 - lon1);
        const a = 
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(this.deg2rad(lat1)) * Math.cos(this.deg2rad(lat2)) * 
            Math.sin(dLon/2) * Math.sin(dLon/2); 
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
        const distance = R * c; // Distance in meters
        return distance;
    }
    
    deg2rad(deg) {
        return deg * (Math.PI/180);
    }
}

// Wait for GENIUS CORE to be available before initializing
document.addEventListener('DOMContentLoaded', function() {
    // Check for GENIUS CORE every 100ms
    const checkInterval = setInterval(() => {
        if (window.GeniusCore) {
            clearInterval(checkInterval);
            window.Integration = new GeniusCoreIntegration();
            console.log('GENIUS CORE Integration initialized');
        }
    }, 100);
});

console.log('GENIUS CORE Integration Manager Loaded');