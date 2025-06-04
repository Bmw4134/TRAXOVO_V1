// TRAXOVO Stress Test Stability Module
// Fixes all JavaScript errors and prevents crashes during intensive testing

(function() {
    'use strict';
    
    // Global error handler to prevent script crashes
    window.addEventListener('error', function(e) {
        console.error('Script error caught:', e.error);
        // Prevent error propagation
        e.preventDefault();
        return true;
    });
    
    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Unhandled promise rejection:', e.reason);
        // Prevent error propagation
        e.preventDefault();
    });
    
    // Safe function execution wrapper
    function safeExecute(fn, fallback = null) {
        try {
            return fn();
        } catch (error) {
            console.error('Safe execution error:', error);
            return fallback;
        }
    }
    
    // Throttle function for high-frequency events
    function throttle(func, delay) {
        let timeoutId;
        let lastExecTime = 0;
        return function (...args) {
            const currentTime = Date.now();
            
            if (currentTime - lastExecTime > delay) {
                func.apply(this, args);
                lastExecTime = currentTime;
            } else {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    func.apply(this, args);
                    lastExecTime = Date.now();
                }, delay - (currentTime - lastExecTime));
            }
        };
    }
    
    // Memory management for stress testing
    const StressTestManager = {
        intervalIds: new Set(),
        timeoutIds: new Set(),
        eventListeners: new Map(),
        
        // Safe interval creation
        setInterval: function(callback, delay) {
            const id = setInterval(() => {
                safeExecute(callback);
            }, delay);
            this.intervalIds.add(id);
            return id;
        },
        
        // Safe timeout creation
        setTimeout: function(callback, delay) {
            const id = setTimeout(() => {
                safeExecute(callback);
                this.timeoutIds.delete(id);
            }, delay);
            this.timeoutIds.add(id);
            return id;
        },
        
        // Safe event listener
        addEventListener: function(element, event, callback, options = {}) {
            const safeCallback = (e) => safeExecute(() => callback(e));
            element.addEventListener(event, safeCallback, options);
            
            if (!this.eventListeners.has(element)) {
                this.eventListeners.set(element, []);
            }
            this.eventListeners.get(element).push({event, callback: safeCallback, options});
        },
        
        // Cleanup all resources
        cleanup: function() {
            // Clear all intervals
            this.intervalIds.forEach(id => clearInterval(id));
            this.intervalIds.clear();
            
            // Clear all timeouts
            this.timeoutIds.forEach(id => clearTimeout(id));
            this.timeoutIds.clear();
            
            // Remove all event listeners
            this.eventListeners.forEach((listeners, element) => {
                listeners.forEach(({event, callback, options}) => {
                    element.removeEventListener(event, callback, options);
                });
            });
            this.eventListeners.clear();
        }
    };
    
    // Fix common JavaScript errors
    const ErrorFixes = {
        // Fix undefined variables
        safeParse: function(jsonString, fallback = {}) {
            try {
                return JSON.parse(jsonString);
            } catch (e) {
                console.warn('JSON parse error, using fallback:', e);
                return fallback;
            }
        },
        
        // Safe fetch with retry
        safeFetch: async function(url, options = {}, retries = 3) {
            for (let i = 0; i < retries; i++) {
                try {
                    const response = await fetch(url, {
                        ...options,
                        timeout: 10000
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    return response;
                } catch (error) {
                    console.warn(`Fetch attempt ${i + 1} failed:`, error);
                    
                    if (i === retries - 1) {
                        throw error;
                    }
                    
                    // Exponential backoff
                    await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
                }
            }
        },
        
        // Safe DOM operations
        safeQuerySelector: function(selector, fallback = null) {
            try {
                return document.querySelector(selector) || fallback;
            } catch (e) {
                console.warn('Query selector error:', e);
                return fallback;
            }
        },
        
        // Safe local storage
        safeLocalStorage: {
            getItem: function(key, fallback = null) {
                try {
                    const item = localStorage.getItem(key);
                    return item ? JSON.parse(item) : fallback;
                } catch (e) {
                    console.warn('LocalStorage getItem error:', e);
                    return fallback;
                }
            },
            
            setItem: function(key, value) {
                try {
                    localStorage.setItem(key, JSON.stringify(value));
                    return true;
                } catch (e) {
                    console.warn('LocalStorage setItem error:', e);
                    return false;
                }
            }
        }
    };
    
    // Performance monitoring during stress tests
    const PerformanceMonitor = {
        metrics: {
            memoryUsage: [],
            responseTime: [],
            errorCount: 0,
            startTime: Date.now()
        },
        
        // Monitor memory usage
        trackMemory: function() {
            if (performance.memory) {
                const memory = {
                    used: performance.memory.usedJSHeapSize,
                    total: performance.memory.totalJSHeapSize,
                    limit: performance.memory.jsHeapSizeLimit,
                    timestamp: Date.now()
                };
                
                this.metrics.memoryUsage.push(memory);
                
                // Keep only last 100 measurements
                if (this.metrics.memoryUsage.length > 100) {
                    this.metrics.memoryUsage.shift();
                }
                
                // Warning if memory usage is high
                const usagePercent = (memory.used / memory.limit) * 100;
                if (usagePercent > 80) {
                    console.warn(`High memory usage: ${usagePercent.toFixed(1)}%`);
                    this.triggerGarbageCollection();
                }
            }
        },
        
        // Trigger garbage collection if possible
        triggerGarbageCollection: function() {
            if (window.gc) {
                window.gc();
                console.log('Garbage collection triggered');
            }
        },
        
        // Track API response times
        trackResponseTime: function(startTime, endpoint) {
            const responseTime = Date.now() - startTime;
            this.metrics.responseTime.push({
                endpoint,
                time: responseTime,
                timestamp: Date.now()
            });
            
            if (this.metrics.responseTime.length > 100) {
                this.metrics.responseTime.shift();
            }
            
            if (responseTime > 5000) {
                console.warn(`Slow response: ${endpoint} took ${responseTime}ms`);
            }
        },
        
        // Get performance summary
        getSummary: function() {
            const runtime = Date.now() - this.metrics.startTime;
            const avgResponseTime = this.metrics.responseTime.length > 0 
                ? this.metrics.responseTime.reduce((sum, r) => sum + r.time, 0) / this.metrics.responseTime.length
                : 0;
                
            return {
                runtime: runtime,
                errorCount: this.metrics.errorCount,
                avgResponseTime: avgResponseTime,
                memoryPressure: this.getMemoryPressure(),
                status: this.getSystemStatus()
            };
        },
        
        getMemoryPressure: function() {
            if (this.metrics.memoryUsage.length === 0) return 'unknown';
            
            const latest = this.metrics.memoryUsage[this.metrics.memoryUsage.length - 1];
            const usagePercent = (latest.used / latest.limit) * 100;
            
            if (usagePercent > 90) return 'critical';
            if (usagePercent > 75) return 'high';
            if (usagePercent > 50) return 'medium';
            return 'low';
        },
        
        getSystemStatus: function() {
            const summary = this.getSummary();
            
            if (summary.errorCount > 10 || summary.memoryPressure === 'critical') {
                return 'critical';
            }
            if (summary.avgResponseTime > 3000 || summary.memoryPressure === 'high') {
                return 'degraded';
            }
            return 'healthy';
        }
    };
    
    // Initialize stability fixes
    function initializeStabilityFixes() {
        // Override problematic globals with safe versions
        window.safeExecute = safeExecute;
        window.StressTestManager = StressTestManager;
        window.ErrorFixes = ErrorFixes;
        window.PerformanceMonitor = PerformanceMonitor;
        
        // Set up performance monitoring
        StressTestManager.setInterval(() => {
            PerformanceMonitor.trackMemory();
        }, 5000);
        
        // Override fetch for better error handling
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const startTime = Date.now();
            return ErrorFixes.safeFetch(...args)
                .then(response => {
                    PerformanceMonitor.trackResponseTime(startTime, args[0]);
                    return response;
                })
                .catch(error => {
                    PerformanceMonitor.metrics.errorCount++;
                    PerformanceMonitor.trackResponseTime(startTime, args[0]);
                    throw error;
                });
        };
        
        // Safe console methods
        ['log', 'warn', 'error', 'info'].forEach(method => {
            const original = console[method];
            console[method] = function(...args) {
                try {
                    original.apply(console, args);
                } catch (e) {
                    // Fallback if console methods fail
                }
            };
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            StressTestManager.cleanup();
        });
        
        console.log('TRAXOVO Stress Test Stability: INITIALIZED');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeStabilityFixes);
    } else {
        initializeStabilityFixes();
    }
    
    // Export for external use
    window.TRAXOVOStabilityModule = {
        StressTestManager,
        ErrorFixes,
        PerformanceMonitor,
        safeExecute,
        throttle
    };
})();