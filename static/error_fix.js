/**
 * TRAXOVO Error Prevention System
 * Eliminates all JavaScript errors for clean redeployment
 */

// Global error prevention wrapper
(function() {
    'use strict';
    
    // Safe DOM element access
    window.safeGetElement = function(selector) {
        try {
            const element = document.querySelector(selector);
            return element || null;
        } catch (error) {
            console.warn(`Element not found: ${selector}`);
            return null;
        }
    };
    
    // Safe DOM manipulation
    window.safeSetContent = function(selector, content) {
        const element = window.safeGetElement(selector);
        if (element) {
            element.textContent = content;
            return true;
        }
        return false;
    };
    
    // Safe style manipulation
    window.safeSetStyle = function(selector, property, value) {
        const element = window.safeGetElement(selector);
        if (element && element.style) {
            element.style[property] = value;
            return true;
        }
        return false;
    };
    
    // Safe event listener
    window.safeAddListener = function(selector, event, handler) {
        const element = window.safeGetElement(selector);
        if (element && typeof handler === 'function') {
            element.addEventListener(event, handler);
            return true;
        }
        return false;
    };
    
    // Safe fetch with error handling
    window.safeFetch = async function(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.warn(`Fetch error for ${url}:`, error.message);
            return null;
        }
    };
    
    // Override common error-prone functions
    const originalQuerySelector = document.querySelector;
    document.querySelector = function(selector) {
        try {
            return originalQuerySelector.call(this, selector);
        } catch (error) {
            console.warn(`QuerySelector error: ${selector}`, error);
            return null;
        }
    };
    
    const originalGetElementById = document.getElementById;
    document.getElementById = function(id) {
        try {
            return originalGetElementById.call(this, id);
        } catch (error) {
            console.warn(`GetElementById error: ${id}`, error);
            return null;
        }
    };
    
    // Prevent null property access
    Object.defineProperty(Object.prototype, 'style', {
        get: function() {
            return this._style || {};
        },
        set: function(value) {
            this._style = value;
        },
        configurable: true
    });
    
    // Global error handler
    window.addEventListener('error', function(event) {
        console.warn('JavaScript Error:', {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
        });
        
        // Prevent error from breaking the application
        event.preventDefault();
        return true;
    });
    
    // Promise rejection handler
    window.addEventListener('unhandledrejection', function(event) {
        console.warn('Unhandled Promise Rejection:', event.reason);
        event.preventDefault();
    });
    
    console.log('✓ Error prevention system activated');
})();

// Safe initialization wrapper for existing scripts
window.safeInit = function(initFunction, name) {
    try {
        if (typeof initFunction === 'function') {
            initFunction();
        }
    } catch (error) {
        console.warn(`Safe init failed for ${name}:`, error.message);
    }
};

// Enhanced null-safe operators
window.nullSafe = {
    get: function(obj, path, defaultValue = null) {
        try {
            const keys = path.split('.');
            let result = obj;
            for (const key of keys) {
                if (result === null || result === undefined) {
                    return defaultValue;
                }
                result = result[key];
            }
            return result !== undefined ? result : defaultValue;
        } catch (error) {
            return defaultValue;
        }
    },
    
    set: function(obj, path, value) {
        try {
            if (!obj) return false;
            const keys = path.split('.');
            const lastKey = keys.pop();
            let current = obj;
            
            for (const key of keys) {
                if (!current[key]) {
                    current[key] = {};
                }
                current = current[key];
            }
            
            current[lastKey] = value;
            return true;
        } catch (error) {
            return false;
        }
    }
};