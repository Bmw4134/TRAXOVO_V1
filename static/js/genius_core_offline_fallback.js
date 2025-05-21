/**
 * TRAXORA GENIUS CORE | Offline Fallback System
 * 
 * This module provides offline capability to store and retrieve
 * asset locations when the API is disconnected.
 */

class OfflineFallbackSystem {
    constructor() {
        // Check if required components exist
        if (!window.GeniusCore) {
            console.error('GENIUS CORE not available. Offline Fallback System initialization aborted.');
            return;
        }
        
        this.geniusCore = window.GeniusCore;
        this.storageName = 'traxora_asset_fallback';
        this.lastSuccessfulFetch = null;
        this.assetCache = this.loadFromLocalStorage();
        
        // Register with GENIUS CORE
        this.fallbackAgent = {
            id: 'OfflineFallback',
            
            handleMessage(message) {
                switch (message.type) {
                    case 'store-assets':
                        return window.OfflineFallback.storeAssets(
                            message.payload.assets,
                            message.payload.timestamp
                        );
                        
                    case 'get-fallback-assets':
                        return {
                            status: 'fallback-assets',
                            assets: window.OfflineFallback.getFallbackAssets(),
                            lastUpdated: window.OfflineFallback.getLastSuccessfulFetch()
                        };
                        
                    case 'clear-asset-cache':
                        return window.OfflineFallback.clearAssetCache();
                        
                    default:
                        return { status: 'unknown-message-type' };
                }
            }
        };
        
        this.geniusCore.registerAgent('OfflineFallback', this.fallbackAgent);
        
        // Intercept asset loading to provide fallback
        this.setupAssetLoadingIntercept();
        
        console.log('Offline Fallback System initialized');
    }
    
    setupAssetLoadingIntercept() {
        // Wait for EnhancedMap to be available
        const checkMap = setInterval(() => {
            if (window.EnhancedMap) {
                clearInterval(checkMap);
                
                // Intercept loadAssets method
                if (window.EnhancedMap.loadAssets) {
                    const originalLoadAssets = window.EnhancedMap.loadAssets;
                    window.EnhancedMap.loadAssets = async function() {
                        try {
                            // Try original loading
                            const result = await originalLoadAssets.apply(this, arguments);
                            
                            // If successful, store assets for fallback
                            if (result && result.length > 0) {
                                window.OfflineFallback.storeAssets(result, new Date().toISOString());
                            }
                            
                            return result;
                        } catch (error) {
                            console.error('Error loading assets from API:', error);
                            
                            // Log to event timeline
                            if (window.VisualDiagnostics) {
                                window.VisualDiagnostics.logEvent('OfflineFallback', 'api-error', {
                                    error: error.toString(),
                                    message: 'Error loading assets from API, using fallback data'
                                });
                            }
                            
                            // Use fallback assets
                            const fallbackAssets = window.OfflineFallback.getFallbackAssets();
                            
                            if (fallbackAssets && fallbackAssets.length > 0) {
                                console.log(`Using ${fallbackAssets.length} fallback assets from ${window.OfflineFallback.getLastSuccessfulFetch()}`);
                                return fallbackAssets;
                            }
                            
                            // Re-throw if no fallback
                            throw error;
                        }
                    };
                    
                    console.log('Asset loading interception set up');
                }
                
                // Also intercept the error handler to show fallback message
                if (window.EnhancedMap.handleLoadError) {
                    const originalHandleError = window.EnhancedMap.handleLoadError;
                    window.EnhancedMap.handleLoadError = function(error) {
                        const fallbackAssets = window.OfflineFallback.getFallbackAssets();
                        
                        if (fallbackAssets && fallbackAssets.length > 0) {
                            // Show fallback message
                            const fallbackTime = window.OfflineFallback.getLastSuccessfulFetch();
                            this.showFallbackMessage(fallbackTime);
                            
                            // Call original with modified message
                            return originalHandleError.call(this, {
                                message: `Using offline data from ${fallbackTime}`,
                                originalError: error
                            });
                        }
                        
                        // Call original error handler if no fallback
                        return originalHandleError.apply(this, arguments);
                    };
                    
                    // Add method to show fallback message
                    window.EnhancedMap.showFallbackMessage = function(timestamp) {
                        // Create banner if not exists
                        let fallbackBanner = document.getElementById('fallback-banner');
                        
                        if (!fallbackBanner) {
                            fallbackBanner = document.createElement('div');
                            fallbackBanner.id = 'fallback-banner';
                            fallbackBanner.className = 'fallback-banner';
                            document.body.appendChild(fallbackBanner);
                            
                            // Add styles if not already added
                            if (!document.getElementById('fallback-styles')) {
                                const style = document.createElement('style');
                                style.id = 'fallback-styles';
                                style.textContent = `
                                    .fallback-banner {
                                        position: fixed;
                                        top: 0;
                                        left: 0;
                                        right: 0;
                                        background-color: rgba(243, 156, 18, 0.9);
                                        color: #fff;
                                        padding: 8px 15px;
                                        text-align: center;
                                        font-size: 13px;
                                        z-index: 9999;
                                        display: flex;
                                        justify-content: space-between;
                                        align-items: center;
                                    }
                                    
                                    .fallback-message {
                                        flex: 1;
                                    }
                                    
                                    .fallback-close {
                                        background: none;
                                        border: none;
                                        color: white;
                                        cursor: pointer;
                                        font-size: 16px;
                                        padding: 0 0 0 10px;
                                    }
                                    
                                    .fallback-banner.hidden {
                                        display: none;
                                    }
                                `;
                                document.head.appendChild(style);
                            }
                        }
                        
                        // Set message and show banner
                        fallbackBanner.innerHTML = `
                            <div class="fallback-message">
                                <i class="bi bi-wifi-off"></i> 
                                API disconnected. Using offline asset data from ${this.formatTimestamp(timestamp)}
                            </div>
                            <button class="fallback-close" title="Dismiss">&times;</button>
                        `;
                        
                        fallbackBanner.classList.remove('hidden');
                        
                        // Add close button behavior
                        const closeBtn = fallbackBanner.querySelector('.fallback-close');
                        if (closeBtn) {
                            closeBtn.addEventListener('click', () => {
                                fallbackBanner.classList.add('hidden');
                            });
                        }
                    };
                    
                    // Add helper to format timestamp
                    window.EnhancedMap.formatTimestamp = function(timestamp) {
                        if (!timestamp) return 'unknown time';
                        
                        // Create relative time description
                        const now = new Date();
                        const then = new Date(timestamp);
                        const diffMs = now - then;
                        const diffMins = Math.floor(diffMs / (1000 * 60));
                        
                        if (diffMins < 60) {
                            return `${diffMins} minutes ago`;
                        } else if (diffMins < 24 * 60) {
                            const hours = Math.floor(diffMins / 60);
                            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
                        } else {
                            const days = Math.floor(diffMins / (60 * 24));
                            return `${days} day${days > 1 ? 's' : ''} ago`;
                        }
                    };
                }
            }
        }, 100);
    }
    
    storeAssets(assets, timestamp) {
        if (!assets || !Array.isArray(assets) || assets.length === 0) {
            return { status: 'error', message: 'No valid assets to store' };
        }
        
        // Update cache
        this.assetCache = assets;
        this.lastSuccessfulFetch = timestamp || new Date().toISOString();
        
        // Store in local storage
        try {
            this.saveToLocalStorage();
            console.log(`Stored ${assets.length} assets for offline fallback`);
            
            // Log to event timeline
            if (window.VisualDiagnostics) {
                window.VisualDiagnostics.logEvent('OfflineFallback', 'assets-stored', {
                    count: assets.length,
                    timestamp: this.lastSuccessfulFetch,
                    message: `Stored ${assets.length} assets for offline use`
                });
            }
            
            return {
                status: 'assets-stored',
                count: assets.length,
                timestamp: this.lastSuccessfulFetch
            };
        } catch (error) {
            console.error('Error storing assets for offline use:', error);
            return { status: 'error', message: error.toString() };
        }
    }
    
    getFallbackAssets() {
        return this.assetCache;
    }
    
    getLastSuccessfulFetch() {
        return this.lastSuccessfulFetch;
    }
    
    clearAssetCache() {
        this.assetCache = [];
        this.lastSuccessfulFetch = null;
        localStorage.removeItem(this.storageName);
        
        // Log to event timeline
        if (window.VisualDiagnostics) {
            window.VisualDiagnostics.logEvent('OfflineFallback', 'cache-cleared', {
                message: 'Asset cache cleared'
            });
        }
        
        return { status: 'cache-cleared' };
    }
    
    saveToLocalStorage() {
        const data = {
            assets: this.assetCache,
            timestamp: this.lastSuccessfulFetch
        };
        
        try {
            localStorage.setItem(this.storageName, JSON.stringify(data));
        } catch (error) {
            console.error('Error saving to local storage:', error);
            
            // If storage is full, try removing some non-essential asset properties
            if (error.name === 'QuotaExceededError') {
                const compressedAssets = this.assetCache.map(asset => {
                    // Keep only essential properties
                    return {
                        asset_id: asset.asset_id || asset.id,
                        id: asset.id || asset.asset_id,
                        make: asset.make,
                        model: asset.model,
                        name: asset.name,
                        type: asset.type,
                        location: asset.location,
                        latitude: asset.latitude,
                        longitude: asset.longitude,
                        last_update: asset.last_update
                    };
                });
                
                const compressedData = {
                    assets: compressedAssets,
                    timestamp: this.lastSuccessfulFetch
                };
                
                try {
                    localStorage.setItem(this.storageName, JSON.stringify(compressedData));
                    console.log('Stored compressed asset data');
                } catch (innerError) {
                    console.error('Error saving compressed data:', innerError);
                }
            }
        }
    }
    
    loadFromLocalStorage() {
        try {
            const data = localStorage.getItem(this.storageName);
            if (data) {
                const parsed = JSON.parse(data);
                this.lastSuccessfulFetch = parsed.timestamp;
                return parsed.assets || [];
            }
        } catch (error) {
            console.error('Error loading from local storage:', error);
        }
        
        return [];
    }
}

// Wait for GENIUS CORE to be available
document.addEventListener('DOMContentLoaded', function() {
    // Check if GENIUS CORE is loaded every 100ms
    const checkGeniusCore = setInterval(() => {
        if (window.GeniusCore) {
            clearInterval(checkGeniusCore);
            window.OfflineFallback = new OfflineFallbackSystem();
            console.log('Offline Fallback System connected to GENIUS CORE');
        }
    }, 100);
});

console.log('GENIUS CORE Offline Fallback System Loaded');