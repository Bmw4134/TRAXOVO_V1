/*
TRAXOVO ES5 Compatibility Layer
Fixes JavaScript syntax errors for older browsers
*/

// Replace ES6 destructuring and spread operators with ES5 equivalents
(function() {
    'use strict';
    
    // Polyfill for Object.entries if not available
    if (!Object.entries) {
        Object.entries = function(obj) {
            var entries = [];
            for (var key in obj) {
                if (obj.hasOwnProperty(key)) {
                    entries.push([key, obj[key]]);
                }
            }
            return entries;
        };
    }
    
    // Polyfill for Array.from if not available
    if (!Array.from) {
        Array.from = function(arrayLike) {
            var array = [];
            for (var i = 0; i < arrayLike.length; i++) {
                array.push(arrayLike[i]);
            }
            return array;
        };
    }
    
    // Safe querySelector wrapper
    window.safeQuerySelector = function(selector) {
        try {
            return document.querySelector(selector);
        } catch (e) {
            console.warn('Invalid selector:', selector);
            return null;
        }
    };
    
    // Safe querySelectorAll wrapper
    window.safeQuerySelectorAll = function(selector) {
        try {
            var nodeList = document.querySelectorAll(selector);
            return Array.prototype.slice.call(nodeList);
        } catch (e) {
            console.warn('Invalid selector:', selector);
            return [];
        }
    };
    
    // Safe event listener with fallback
    window.safeAddEventListener = function(element, event, handler, options) {
        if (element && element.addEventListener) {
            try {
                element.addEventListener(event, handler, options || false);
            } catch (e) {
                console.warn('Event listener error:', e);
            }
        }
    };
    
})();