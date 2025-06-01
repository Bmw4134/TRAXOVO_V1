/**
 * GENIUS Performance Optimization Engine
 * Comprehensive system acceleration for TRAXOVO
 */

// Performance optimization configurations
const GENIUS_CONFIG = {
    cacheTimeout: 300000, // 5 minutes
    debounceDelay: 150,
    lazyLoadThreshold: 100,
    batchSize: 50,
    maxConcurrentRequests: 3
};

class GeniusPerformanceEngine {
    constructor() {
        this.cache = new Map();
        this.requestQueue = [];
        this.activeRequests = 0;
        this.observers = new Map();
        this.init();
    }

    init() {
        this.setupRequestInterceptor();
        this.setupLazyLoading();
        this.setupIntelligentCaching();
        this.optimizeRendering();
        this.setupConnectionOptimization();
    }

    // Intelligent Request Queue Management
    setupRequestInterceptor() {
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            return this.queueRequest(() => originalFetch(...args));
        };
    }

    async queueRequest(requestFn) {
        return new Promise((resolve, reject) => {
            this.requestQueue.push({ requestFn, resolve, reject });
            this.processQueue();
        });
    }

    async processQueue() {
        if (this.activeRequests >= GENIUS_CONFIG.maxConcurrentRequests || this.requestQueue.length === 0) {
            return;
        }

        const { requestFn, resolve, reject } = this.requestQueue.shift();
        this.activeRequests++;

        try {
            const result = await requestFn();
            resolve(result);
        } catch (error) {
            reject(error);
        } finally {
            this.activeRequests--;
            this.processQueue();
        }
    }

    // Intelligent Caching System
    setupIntelligentCaching() {
        this.cacheKey = (url, params) => {
            return `${url}_${JSON.stringify(params || {})}_${Math.floor(Date.now() / GENIUS_CONFIG.cacheTimeout)}`;
        };

        this.getCached = (key) => {
            const cached = this.cache.get(key);
            if (cached && Date.now() - cached.timestamp < GENIUS_CONFIG.cacheTimeout) {
                return cached.data;
            }
            return null;
        };

        this.setCache = (key, data) => {
            this.cache.set(key, {
                data,
                timestamp: Date.now()
            });
        };
    }

    // Advanced Lazy Loading
    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadElement(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '50px'
            });

            this.lazyObserver = observer;
        }
    }

    loadElement(element) {
        if (element.dataset.src) {
            element.src = element.dataset.src;
        }
        if (element.dataset.load) {
            this.executeDelayedAction(element.dataset.load);
        }
    }

    // Rendering Optimization
    optimizeRendering() {
        // Batch DOM updates
        this.batchUpdates = [];
        this.updateScheduled = false;

        this.scheduleUpdate = (updateFn) => {
            this.batchUpdates.push(updateFn);
            if (!this.updateScheduled) {
                this.updateScheduled = true;
                requestAnimationFrame(() => {
                    this.batchUpdates.forEach(fn => fn());
                    this.batchUpdates = [];
                    this.updateScheduled = false;
                });
            }
        };
    }

    // Connection Optimization
    setupConnectionOptimization() {
        // Prefetch critical resources
        this.prefetchCriticalResources();
        
        // Setup service worker for caching
        if ('serviceWorker' in navigator) {
            this.registerServiceWorker();
        }
    }

    prefetchCriticalResources() {
        const criticalAPIs = [
            '/api/fleet/assets',
            '/api/performance/metrics'
        ];

        criticalAPIs.forEach(url => {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = url;
            document.head.appendChild(link);
        });
    }

    async registerServiceWorker() {
        try {
            await navigator.serviceWorker.register('/static/genius-sw.js');
            console.log('GENIUS ServiceWorker registered');
        } catch (error) {
            console.log('ServiceWorker registration failed');
        }
    }

    // API Performance Wrapper
    async optimizedFetch(url, options = {}) {
        const cacheKey = this.cacheKey(url, options);
        const cached = this.getCached(cacheKey);
        
        if (cached) {
            return Promise.resolve({
                json: () => Promise.resolve(cached),
                ok: true
            });
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Cache-Control': 'max-age=300',
                    ...options.headers
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.setCache(cacheKey, data);
                return {
                    json: () => Promise.resolve(data),
                    ok: true
                };
            }
            return response;
        } catch (error) {
            console.error('Optimized fetch error:', error);
            throw error;
        }
    }

    // Memory Management
    cleanup() {
        // Clear old cache entries
        const now = Date.now();
        for (const [key, value] of this.cache.entries()) {
            if (now - value.timestamp > GENIUS_CONFIG.cacheTimeout * 2) {
                this.cache.delete(key);
            }
        }
    }

    // Performance Monitoring
    startMonitoring() {
        setInterval(() => {
            this.cleanup();
            this.logPerformanceMetrics();
        }, 60000); // Every minute
    }

    logPerformanceMetrics() {
        const metrics = {
            cacheSize: this.cache.size,
            activeRequests: this.activeRequests,
            queueLength: this.requestQueue.length,
            memoryUsage: performance.memory ? performance.memory.usedJSHeapSize : 'N/A'
        };
        console.log('GENIUS Performance Metrics:', metrics);
    }
}

// Initialize GENIUS Performance Engine
const genius = new GeniusPerformanceEngine();
genius.startMonitoring();

// Export for global use
window.GENIUS = genius;

// Performance enhancement for existing functions
document.addEventListener('DOMContentLoaded', function() {
    // Debounce scroll events
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            // Process scroll-dependent operations
        }, GENIUS_CONFIG.debounceDelay);
    });

    // Optimize image loading
    document.querySelectorAll('img[data-src]').forEach(img => {
        if (genius.lazyObserver) {
            genius.lazyObserver.observe(img);
        }
    });

    // Preload critical content
    setTimeout(() => {
        genius.optimizedFetch('/api/fleet/assets');
    }, 1000);
});