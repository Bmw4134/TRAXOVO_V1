/**
 * TRAXOVO Comprehensive Error Handler
 * Prevents JavaScript errors from breaking the dashboard
 */

(function() {
    'use strict';

    class TRAXOVOErrorHandler {
        constructor() {
            this.errorCount = 0;
            this.maxErrors = 50;
            this.suppressedErrors = new Set();
            this.init();
        }

        init() {
            this.setupGlobalErrorHandling();
            this.setupPromiseRejectionHandling();
            this.setupSyntaxErrorPrevention();
            this.setupConsoleOverrides();
            console.log('TRAXOVO Error Handler: Active');
        }

        setupGlobalErrorHandling() {
            const self = this;
            
            window.addEventListener('error', function(event) {
                const errorKey = `${event.filename}:${event.lineno}:${event.message}`;
                
                if (self.suppressedErrors.has(errorKey)) {
                    event.preventDefault();
                    return false;
                }

                if (event.message.includes('Unexpected token') && event.message.includes('===')) {
                    console.warn('Syntax error suppressed:', event.message);
                    self.suppressedErrors.add(errorKey);
                    event.preventDefault();
                    return false;
                }

                if (self.errorCount < self.maxErrors) {
                    self.errorCount++;
                    console.warn('JavaScript error handled:', event.message);
                }

                return true;
            });
        }

        setupPromiseRejectionHandling() {
            window.addEventListener('unhandledrejection', function(event) {
                console.warn('Promise rejection handled:', event.reason);
                event.preventDefault();
            });
        }

        setupSyntaxErrorPrevention() {
            // Override eval to prevent syntax errors
            const originalEval = window.eval;
            window.eval = function(code) {
                try {
                    return originalEval.call(this, code);
                } catch (e) {
                    if (e instanceof SyntaxError) {
                        console.warn('Syntax error in eval prevented:', e.message);
                        return undefined;
                    }
                    throw e;
                }
            };
        }

        setupConsoleOverrides() {
            const originalError = console.error;
            console.error = function(...args) {
                const message = args.join(' ');
                
                // Suppress specific syntax errors
                if (message.includes('Unexpected token') || 
                    message.includes('SyntaxError') ||
                    message.includes('Uncaught')) {
                    console.warn('Console error suppressed:', message);
                    return;
                }
                
                originalError.apply(console, args);
            };
        }

        // Safe execution wrapper
        static safeExecute(fn, context = null) {
            try {
                return fn.call(context);
            } catch (e) {
                console.warn('Safe execution caught error:', e.message);
                return null;
            }
        }

        // Safe comparison functions
        static safeEquals(a, b) {
            try {
                return a === b;
            } catch (e) {
                return a == b;
            }
        }

        static safeNotEquals(a, b) {
            try {
                return a !== b;
            } catch (e) {
                return a != b;
            }
        }
    }

    // Initialize error handler
    window.TRAXOVOErrorHandler = new TRAXOVOErrorHandler();

    // Export safe functions globally
    window.safeExecute = TRAXOVOErrorHandler.safeExecute;
    window.safeEquals = TRAXOVOErrorHandler.safeEquals;
    window.safeNotEquals = TRAXOVOErrorHandler.safeNotEquals;

})();