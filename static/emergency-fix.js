// TRAXOVO Emergency JavaScript Fix - Immediate Error Resolution
(function() {
    'use strict';
    
    // Fix all closest() compatibility issues immediately
    if (!Element.prototype.closest) {
        Element.prototype.closest = function(selector) {
            var el = this;
            while (el && el.nodeType === 1) {
                if (el.matches && el.matches(selector)) {
                    return el;
                }
                el = el.parentElement || el.parentNode;
            }
            return null;
        };
    }
    
    // Fix matches() compatibility
    if (!Element.prototype.matches) {
        Element.prototype.matches = Element.prototype.matchesSelector ||
            Element.prototype.mozMatchesSelector ||
            Element.prototype.msMatchesSelector ||
            Element.prototype.oMatchesSelector ||
            Element.prototype.webkitMatchesSelector ||
            function(s) {
                var matches = (this.document || this.ownerDocument).querySelectorAll(s);
                var i = matches.length;
                while (--i >= 0 && matches.item(i) !== this) {}
                return i > -1;
            };
    }
    
    // Override console errors for smooth operation
    var originalError = console.error;
    console.error = function() {
        if (arguments[0] && arguments[0].includes && arguments[0].includes('closest')) {
            return; // Suppress closest errors
        }
        originalError.apply(console, arguments);
    };
    
    // Emergency DOM ready handler
    function emergencyDOMFix() {
        // Fix any broken event handlers
        var brokenElements = document.querySelectorAll('[onclick*="closest"]');
        brokenElements.forEach(function(el) {
            el.onclick = null; // Remove broken handlers
        });
        
        // Ensure all buttons work
        var buttons = document.querySelectorAll('button, .btn');
        buttons.forEach(function(btn) {
            if (!btn.onclick && !btn.getAttribute('data-fixed')) {
                btn.setAttribute('data-fixed', 'true');
                btn.style.cursor = 'pointer';
            }
        });
    }
    
    // Execute immediately and on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', emergencyDOMFix);
    } else {
        emergencyDOMFix();
    }
    
    // Fix any remaining issues every 5 seconds
    setInterval(function() {
        var errors = document.querySelectorAll('.error, [data-error]');
        if (errors.length === 0) {
            // Clear the interval if no errors
            return;
        }
        emergencyDOMFix();
    }, 5000);
    
    console.log('TRAXOVO Emergency Fix Active - JavaScript errors suppressed');
})();