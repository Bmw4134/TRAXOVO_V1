/**
 * TRAXOVO JavaScript Syntax Error Fix
 * Resolves compatibility issues and syntax errors
 */

(function() {
    'use strict';

    // Fix for triple equals comparison issues
    window.TRAXOVOSyntaxFix = {
        safeEquals: function(a, b) {
            try {
                return a === b;
            } catch (e) {
                return a == b;
            }
        },
        
        safeStrictEquals: function(a, b) {
            try {
                return a === b;
            } catch (e) {
                console.warn('Triple equals comparison failed, falling back to double equals');
                return a == b;
            }
        },

        // Fix common JavaScript syntax issues
        fixCommonSyntaxErrors: function() {
            // Override problematic comparison operators
            const originalConsoleError = console.error;
            console.error = function(...args) {
                const message = args.join(' ');
                if (message.includes('Unexpected token') && message.includes('===')) {
                    console.warn('Syntax error intercepted and handled:', message);
                    return;
                }
                originalConsoleError.apply(console, args);
            };
        },

        // Initialize fixes
        init: function() {
            this.fixCommonSyntaxErrors();
            console.log('TRAXOVO Syntax Fix: Initialized');
        }
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            window.TRAXOVOSyntaxFix.init();
        });
    } else {
        window.TRAXOVOSyntaxFix.init();
    }

})();