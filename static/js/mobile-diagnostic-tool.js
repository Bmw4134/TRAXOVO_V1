// TRAXOVO Mobile Diagnostic Tool
// Comprehensive mobile display issue detection and auto-fix system

(function() {
    'use strict';
    
    class TRAXOVOMobileDiagnostic {
        constructor() {
            this.issues = [];
            this.fixes = [];
            this.deviceInfo = {};
            this.isRunning = false;
            
            this.initializeDiagnostic();
        }
        
        initializeDiagnostic() {
            this.detectDevice();
            this.runDiagnostic();
            this.applyFixes();
            this.createDiagnosticPanel();
            
            console.log('TRAXOVO Mobile Diagnostic: ACTIVE');
        }
        
        detectDevice() {
            const ua = navigator.userAgent;
            const viewport = {
                width: window.innerWidth,
                height: window.innerHeight,
                devicePixelRatio: window.devicePixelRatio || 1,
                orientation: window.orientation || 0
            };
            
            this.deviceInfo = {
                userAgent: ua,
                viewport: viewport,
                isMobile: /Mobi|Android/i.test(ua),
                isIOS: /iPad|iPhone|iPod/.test(ua),
                isAndroid: /Android/.test(ua),
                isTablet: /iPad/.test(ua) || (window.innerWidth >= 768 && window.innerWidth <= 1024),
                touchSupport: 'ontouchstart' in window,
                standalone: window.navigator.standalone || window.matchMedia('(display-mode: standalone)').matches,
                safeArea: {
                    top: this.getCSSEnvValue('safe-area-inset-top'),
                    bottom: this.getCSSEnvValue('safe-area-inset-bottom'),
                    left: this.getCSSEnvValue('safe-area-inset-left'),
                    right: this.getCSSEnvValue('safe-area-inset-right')
                }
            };
        }
        
        getCSSEnvValue(property) {
            const testEl = document.createElement('div');
            testEl.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 1px;
                height: 1px;
                pointer-events: none;
                visibility: hidden;
                padding-top: env(${property});
            `;
            document.body.appendChild(testEl);
            const value = parseInt(getComputedStyle(testEl).paddingTop) || 0;
            document.body.removeChild(testEl);
            return value;
        }
        
        runDiagnostic() {
            this.issues = [];
            
            // Check for overflow issues
            this.checkOverflowIssues();
            
            // Check for viewport issues
            this.checkViewportIssues();
            
            // Check for touch target sizes
            this.checkTouchTargets();
            
            // Check for safe area issues
            this.checkSafeAreaIssues();
            
            // Check for performance issues
            this.checkPerformanceIssues();
            
            // Check for loading animation issues
            this.checkLoadingAnimationIssues();
            
            console.log(`Mobile Diagnostic: Found ${this.issues.length} issues`);
        }
        
        checkOverflowIssues() {
            const elements = document.querySelectorAll('*');
            let overflowCount = 0;
            
            elements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > window.innerWidth) {
                    overflowCount++;
                    this.addIssue('overflow', `Element wider than viewport: ${el.tagName}${el.className ? '.' + el.className.split(' ')[0] : ''}`, el);
                }
            });
            
            if (overflowCount > 5) {
                this.addIssue('critical', `${overflowCount} elements causing horizontal overflow`, null);
            }
        }
        
        checkViewportIssues() {
            const viewportMeta = document.querySelector('meta[name="viewport"]');
            
            if (!viewportMeta) {
                this.addIssue('critical', 'Missing viewport meta tag', null);
                return;
            }
            
            const content = viewportMeta.getAttribute('content');
            const hasDeviceWidth = content.includes('width=device-width');
            const hasInitialScale = content.includes('initial-scale=1');
            const hasUserScalable = content.includes('user-scalable=no');
            
            if (!hasDeviceWidth) {
                this.addIssue('warning', 'Viewport missing width=device-width', viewportMeta);
            }
            
            if (!hasInitialScale) {
                this.addIssue('warning', 'Viewport missing initial-scale=1', viewportMeta);
            }
            
            if (this.deviceInfo.viewport.width !== screen.width && this.deviceInfo.isMobile) {
                this.addIssue('warning', 'Viewport width mismatch', null);
            }
        }
        
        checkTouchTargets() {
            const clickableElements = document.querySelectorAll('button, a, input, select, textarea, [onclick], [role="button"]');
            let smallTargetCount = 0;
            
            clickableElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                const minSize = 44; // Apple's recommended minimum touch target size
                
                if ((rect.width < minSize || rect.height < minSize) && rect.width > 0 && rect.height > 0) {
                    smallTargetCount++;
                    this.addIssue('accessibility', `Touch target too small: ${rect.width}x${rect.height}px`, el);
                }
            });
            
            if (smallTargetCount > 0) {
                this.addIssue('warning', `${smallTargetCount} touch targets smaller than 44px`, null);
            }
        }
        
        checkSafeAreaIssues() {
            if (!this.deviceInfo.isIOS) return;
            
            const hasSafeAreaSupport = document.body.style.paddingTop.includes('env(safe-area-inset-top)') ||
                                    getComputedStyle(document.body).paddingTop !== '0px';
            
            if (!hasSafeAreaSupport && (this.deviceInfo.safeArea.top > 0 || this.deviceInfo.safeArea.bottom > 0)) {
                this.addIssue('warning', 'iOS safe area not properly handled', null);
            }
        }
        
        checkPerformanceIssues() {
            const startTime = performance.now();
            
            // Check for too many DOM elements
            const elementCount = document.querySelectorAll('*').length;
            if (elementCount > 1000) {
                this.addIssue('performance', `High DOM element count: ${elementCount}`, null);
            }
            
            // Check for missing transform optimizations
            const animatedElements = document.querySelectorAll('[style*="animation"], .animated, .loading-animation-area *');
            let missingOptimizations = 0;
            
            animatedElements.forEach(el => {
                const style = getComputedStyle(el);
                if (!style.transform.includes('translateZ') && !style.willChange.includes('transform')) {
                    missingOptimizations++;
                }
            });
            
            if (missingOptimizations > 5) {
                this.addIssue('performance', `${missingOptimizations} animated elements missing GPU acceleration`, null);
            }
            
            const diagnosticTime = performance.now() - startTime;
            if (diagnosticTime > 100) {
                this.addIssue('performance', `Slow diagnostic performance: ${diagnosticTime.toFixed(1)}ms`, null);
            }
        }
        
        checkLoadingAnimationIssues() {
            const loadingContainer = document.getElementById('traxovo-loading-overlay');
            const demoButtons = document.getElementById('loading-animation-demos');
            
            if (loadingContainer) {
                const rect = loadingContainer.getBoundingClientRect();
                if (rect.width > window.innerWidth) {
                    this.addIssue('animation', 'Loading overlay wider than viewport', loadingContainer);
                }
            }
            
            if (demoButtons && this.deviceInfo.isMobile) {
                const rect = demoButtons.getBoundingClientRect();
                if (rect.width > window.innerWidth * 0.9) {
                    this.addIssue('animation', 'Demo buttons too wide for mobile', demoButtons);
                }
            }
        }
        
        addIssue(type, description, element) {
            this.issues.push({
                type: type,
                description: description,
                element: element,
                timestamp: Date.now()
            });
        }
        
        applyFixes() {
            this.fixes = [];
            
            // Apply emergency mobile fixes
            this.applyEmergencyMobileFixes();
            
            // Fix overflow issues
            this.fixOverflowIssues();
            
            // Fix touch targets
            this.fixTouchTargets();
            
            // Fix loading animations
            this.fixLoadingAnimations();
            
            // Fix safe area issues
            this.fixSafeAreaIssues();
            
            console.log(`Applied ${this.fixes.length} mobile fixes`);
        }
        
        applyEmergencyMobileFixes() {
            if (!this.deviceInfo.isMobile) return;
            
            // Add emergency mobile class to body
            document.body.classList.add('mobile-emergency-fix');
            
            // Force viewport meta tag if missing
            let viewportMeta = document.querySelector('meta[name="viewport"]');
            if (!viewportMeta) {
                viewportMeta = document.createElement('meta');
                viewportMeta.name = 'viewport';
                document.head.appendChild(viewportMeta);
            }
            
            viewportMeta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover';
            
            // Add emergency CSS
            const emergencyCSS = document.createElement('style');
            emergencyCSS.id = 'mobile-emergency-css';
            emergencyCSS.textContent = `
                /* Emergency Mobile Fixes */
                * { 
                    max-width: 100vw !important; 
                    box-sizing: border-box !important; 
                }
                body, html { 
                    overflow-x: hidden !important; 
                    width: 100% !important; 
                    position: relative !important;
                }
                .widget, .metric-card, .chart-container { 
                    max-width: calc(100vw - 20px) !important; 
                    margin: 0 10px 15px 10px !important; 
                }
                #loading-animation-demos { 
                    max-width: calc(100vw - 20px) !important; 
                    left: 10px !important; 
                    right: 10px !important; 
                }
                button { 
                    min-height: 44px !important; 
                    min-width: 44px !important; 
                    touch-action: manipulation !important; 
                }
                .loading-animation-area { 
                    max-width: 90% !important; 
                    max-height: 40vh !important; 
                }
            `;
            document.head.appendChild(emergencyCSS);
            
            this.addFix('emergency', 'Applied emergency mobile layout fixes');
        }
        
        fixOverflowIssues() {
            const overflowElements = document.querySelectorAll('*');
            let fixedCount = 0;
            
            overflowElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > window.innerWidth) {
                    el.style.maxWidth = '100vw';
                    el.style.boxSizing = 'border-box';
                    el.style.overflowX = 'hidden';
                    fixedCount++;
                }
            });
            
            if (fixedCount > 0) {
                this.addFix('overflow', `Fixed ${fixedCount} overflow elements`);
            }
        }
        
        fixTouchTargets() {
            const clickableElements = document.querySelectorAll('button, a, input, select, textarea, [onclick], [role="button"]');
            let fixedCount = 0;
            
            clickableElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width < 44 || rect.height < 44) {
                    el.style.minHeight = '44px';
                    el.style.minWidth = '44px';
                    el.style.touchAction = 'manipulation';
                    fixedCount++;
                }
            });
            
            if (fixedCount > 0) {
                this.addFix('accessibility', `Fixed ${fixedCount} touch targets`);
            }
        }
        
        fixLoadingAnimations() {
            const demoButtons = document.getElementById('loading-animation-demos');
            if (demoButtons && this.deviceInfo.isMobile) {
                demoButtons.style.maxWidth = 'calc(100vw - 20px)';
                demoButtons.style.left = '10px';
                demoButtons.style.right = '10px';
                
                const buttons = demoButtons.querySelectorAll('button');
                buttons.forEach(btn => {
                    btn.style.fontSize = '10px';
                    btn.style.padding = '8px 6px';
                    btn.style.flex = '1';
                    btn.style.minWidth = 'auto';
                });
                
                this.addFix('animation', 'Fixed loading animation demo buttons for mobile');
            }
            
            const loadingArea = document.querySelector('.loading-animation-area');
            if (loadingArea && this.deviceInfo.isMobile) {
                loadingArea.style.maxWidth = '90%';
                loadingArea.style.maxHeight = '40vh';
                this.addFix('animation', 'Fixed loading animation area sizing');
            }
        }
        
        fixSafeAreaIssues() {
            if (!this.deviceInfo.isIOS) return;
            
            if (this.deviceInfo.safeArea.top > 0 || this.deviceInfo.safeArea.bottom > 0) {
                const safeAreaCSS = document.createElement('style');
                safeAreaCSS.id = 'safe-area-fixes';
                safeAreaCSS.textContent = `
                    body { 
                        padding-top: env(safe-area-inset-top, 0px) !important; 
                        padding-bottom: env(safe-area-inset-bottom, 0px) !important; 
                        padding-left: env(safe-area-inset-left, 0px) !important; 
                        padding-right: env(safe-area-inset-right, 0px) !important; 
                    }
                    .traxovo-loading-overlay { 
                        padding-top: env(safe-area-inset-top, 0px) !important; 
                        padding-bottom: env(safe-area-inset-bottom, 0px) !important; 
                    }
                `;
                document.head.appendChild(safeAreaCSS);
                
                this.addFix('ios', 'Applied iOS safe area fixes');
            }
        }
        
        addFix(type, description) {
            this.fixes.push({
                type: type,
                description: description,
                timestamp: Date.now()
            });
        }
        
        createDiagnosticPanel() {
            if (!this.deviceInfo.isMobile) return;
            
            const panel = document.createElement('div');
            panel.id = 'mobile-diagnostic-panel';
            panel.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-size: 12px;
                max-width: 200px;
                z-index: 10000;
                display: none;
            `;
            
            const summary = `
                <div style="font-weight: bold; margin-bottom: 8px;">Mobile Diagnostic</div>
                <div>Device: ${this.deviceInfo.isIOS ? 'iOS' : this.deviceInfo.isAndroid ? 'Android' : 'Mobile'}</div>
                <div>Viewport: ${this.deviceInfo.viewport.width}x${this.deviceInfo.viewport.height}</div>
                <div>Issues: ${this.issues.length}</div>
                <div>Fixes: ${this.fixes.length}</div>
                <div style="margin-top: 8px;">
                    <button onclick="this.parentElement.parentElement.style.display='none'" 
                            style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 10px;">
                        Close
                    </button>
                </div>
            `;
            
            panel.innerHTML = summary;
            document.body.appendChild(panel);
            
            // Show panel for 5 seconds if there are issues
            if (this.issues.length > 0) {
                panel.style.display = 'block';
                setTimeout(() => {
                    panel.style.display = 'none';
                }, 5000);
            }
        }
        
        runRealTimeMonitoring() {
            let stableCount = 0;
            const monitoringInterval = setInterval(() => {
                const previousIssueCount = this.issues.length;
                this.detectDevice();
                this.runDiagnostic();
                
                if (this.issues.length > 0) {
                    this.applyFixes();
                }
                
                // If issues are stable for 3 checks, reduce monitoring frequency
                if (this.issues.length === previousIssueCount) {
                    stableCount++;
                    if (stableCount >= 3) {
                        clearInterval(monitoringInterval);
                        // Switch to less frequent monitoring
                        setInterval(() => {
                            this.runDiagnostic();
                            if (this.issues.length > 0) {
                                this.applyFixes();
                            }
                        }, 30000); // Check every 30 seconds instead
                        console.log('Mobile Diagnostic: Switched to optimized monitoring');
                    }
                } else {
                    stableCount = 0;
                }
            }, 10000); // Initial check every 10 seconds
        }
        
        getDiagnosticReport() {
            return {
                deviceInfo: this.deviceInfo,
                issues: this.issues,
                fixes: this.fixes,
                timestamp: new Date().toISOString()
            };
        }
    }
    
    // Initialize mobile diagnostic
    function initializeMobileDiagnostic() {
        window.traxovoMobileDiagnostic = new TRAXOVOMobileDiagnostic();
        
        // Start real-time monitoring
        window.traxovoMobileDiagnostic.runRealTimeMonitoring();
        
        // Expose diagnostic function
        window.runMobileDiagnostic = () => {
            return window.traxovoMobileDiagnostic.getDiagnosticReport();
        };
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeMobileDiagnostic);
    } else {
        initializeMobileDiagnostic();
    }
    
    // Handle orientation changes
    window.addEventListener('orientationchange', () => {
        setTimeout(() => {
            if (window.traxovoMobileDiagnostic) {
                window.traxovoMobileDiagnostic.runDiagnostic();
                window.traxovoMobileDiagnostic.applyFixes();
            }
        }, 500);
    });
    
    // Handle resize events
    window.addEventListener('resize', () => {
        if (window.traxovoMobileDiagnostic) {
            clearTimeout(window.mobileResizeTimeout);
            window.mobileResizeTimeout = setTimeout(() => {
                window.traxovoMobileDiagnostic.runDiagnostic();
                window.traxovoMobileDiagnostic.applyFixes();
            }, 250);
        }
    });
})();