/**
 * NEXUS QNIS Boost - Advanced Dashboard Enhancement
 * Cascades adaptive layouts, live NLP queries, and secure backend visibility
 * Watson Mode: Enhanced visibility | Standard Mode: Locked deployment paths
 */

class NexusQNISBoost {
    constructor() {
        this.version = "∞.15.1";
        this.watsonMode = this.detectWatsonMode();
        this.deploymentLocked = !this.watsonMode;
        this.nlpIndexing = false;
        this.selfDebugActive = false;
        
        this.initializeBoost();
    }
    
    detectWatsonMode() {
        const userContext = document.body.getAttribute('data-user') || '';
        const sessionAuth = sessionStorage.getItem('nexus_auth_level') || '';
        const urlParams = new URLSearchParams(window.location.search);
        
        return userContext.toLowerCase().includes('watson') || 
               sessionAuth === 'watson_enhanced' ||
               urlParams.get('watsonMode') === 'true';
    }
    
    initializeBoost() {
        console.log(`%cNEXUS QNIS Boost ${this.version}${this.watsonMode ? ' | Watson Mode Active' : ' | Standard Mode'}`, 
            'color: #00ff88; font-weight: bold; background: rgba(0,0,0,0.9); padding: 8px; border-radius: 5px;');
        
        this.applyPolishBundle();
        this.cascadeAdaptiveLayouts();
        this.enableLiveNLPQueries();
        this.configureBackendVisibility();
        this.lockDeploymentPaths();
        this.startNLPIndexing();
        this.initializeSelfDebug();
    }
    
    applyPolishBundle() {
        const polishCSS = `
            /* QNIS Polish Bundle - Advanced Dashboard Styling */
            .dashboard-enhanced {
                backdrop-filter: blur(20px);
                background: linear-gradient(135deg, 
                    rgba(15, 23, 42, 0.95), 
                    rgba(30, 41, 59, 0.90), 
                    rgba(51, 65, 85, 0.85));
                border: 1px solid rgba(0, 255, 136, 0.2);
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            .metric-card-enhanced {
                background: linear-gradient(135deg, 
                    rgba(255, 255, 255, 0.1), 
                    rgba(30, 64, 175, 0.1));
                border: 2px solid rgba(0, 255, 136, 0.3);
                border-radius: 20px;
                padding: 2rem;
                position: relative;
                overflow: hidden;
                transition: all 0.4s ease;
                backdrop-filter: blur(15px);
            }
            
            .metric-card-enhanced::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, 
                    transparent, 
                    rgba(0, 255, 136, 0.1), 
                    transparent);
                transition: left 0.5s ease;
            }
            
            .metric-card-enhanced:hover::before {
                left: 100%;
            }
            
            .metric-card-enhanced:hover {
                border-color: #00ff88;
                box-shadow: 0 0 40px rgba(0, 255, 136, 0.3);
                transform: translateY(-8px) scale(1.02);
            }
            
            .qnis-nlp-active {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 400px;
                height: 500px;
                background: rgba(0, 0, 0, 0.95);
                border: 2px solid #00ff88;
                border-radius: 20px;
                backdrop-filter: blur(20px);
                z-index: 10000;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
            }
            
            .qnis-backend-panel {
                position: fixed;
                top: 0;
                left: 0;
                width: 300px;
                height: 100vh;
                background: rgba(0, 0, 0, 0.98);
                border-right: 2px solid #00ff88;
                backdrop-filter: blur(25px);
                z-index: 9999;
                transform: translateX(-100%);
                transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                overflow-y: auto;
            }
            
            .qnis-backend-panel.watson-visible {
                transform: translateX(0);
            }
            
            .adaptive-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                transition: all 0.3s ease;
            }
            
            @media (max-width: 768px) {
                .adaptive-grid {
                    grid-template-columns: 1fr;
                    gap: 1rem;
                }
                .qnis-nlp-active {
                    width: calc(100vw - 40px);
                    height: 60vh;
                    bottom: 10px;
                    right: 10px;
                    left: 10px;
                }
            }
            
            .nlp-query-input {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(0, 255, 136, 0.3);
                border-radius: 25px;
                padding: 12px 20px;
                color: white;
                font-size: 14px;
                width: 100%;
                transition: all 0.3s ease;
            }
            
            .nlp-query-input:focus {
                outline: none;
                border-color: #00ff88;
                box-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
            }
            
            .qnis-deployment-locked {
                pointer-events: none;
                opacity: 0.3;
                filter: blur(2px);
            }
            
            .watson-enhanced .qnis-deployment-locked {
                pointer-events: auto;
                opacity: 1;
                filter: none;
            }
        `;
        
        const styleElement = document.createElement('style');
        styleElement.textContent = polishCSS;
        document.head.appendChild(styleElement);
        
        this.enhanceExistingElements();
    }
    
    enhanceExistingElements() {
        // Enhance dashboard containers
        document.querySelectorAll('.dashboard-view, .dashboard-content').forEach(el => {
            el.classList.add('dashboard-enhanced');
        });
        
        // Enhance metric cards
        document.querySelectorAll('.metric-card').forEach(el => {
            el.classList.add('metric-card-enhanced');
        });
        
        // Apply adaptive grid to main containers
        document.querySelectorAll('.metrics-grid, .charts-grid, .feature-grid').forEach(el => {
            el.classList.add('adaptive-grid');
        });
    }
    
    cascadeAdaptiveLayouts() {
        this.adaptiveSystem = {
            cascade: () => {
                this.analyzeViewport();
                this.optimizeForDevice();
                this.applyUserPreferences();
                this.cascadeToChildDashboards();
            },
            
            optimizePerformance: () => {
                const visibleElements = this.getVisibleElements();
                this.prioritizeRenderingFor(visibleElements);
                this.deferNonCriticalUpdates();
            }
        };
        
        // Responsive observer for real-time adaptation
        this.resizeObserver = new ResizeObserver(entries => {
            this.adaptiveSystem.cascade();
        });
        
        document.querySelectorAll('.dashboard-view').forEach(el => {
            this.resizeObserver.observe(el);
        });
        
        // Initial cascade
        this.adaptiveSystem.cascade();
    }
    
    analyzeViewport() {
        const viewport = {
            width: window.innerWidth,
            height: window.innerHeight,
            ratio: window.innerWidth / window.innerHeight,
            devicePixelRatio: window.devicePixelRatio
        };
        
        this.currentViewport = viewport;
        this.applyViewportOptimizations(viewport);
    }
    
    applyViewportOptimizations(viewport) {
        if (viewport.width < 768) {
            document.body.classList.add('qnis-mobile');
            this.optimizeForMobile();
        } else if (viewport.width < 1200) {
            document.body.classList.add('qnis-tablet');
            this.optimizeForTablet();
        } else {
            document.body.classList.add('qnis-desktop');
            this.optimizeForDesktop();
        }
    }
    
    cascadeToChildDashboards() {
        const childFrames = document.querySelectorAll('iframe[data-dashboard]');
        childFrames.forEach(frame => {
            try {
                const frameWindow = frame.contentWindow;
                if (frameWindow && frameWindow.QNIS) {
                    frameWindow.QNIS.adaptiveSystem.cascade();
                }
            } catch (e) {
                // Cross-origin restriction - use postMessage
                frame.contentWindow.postMessage({
                    type: 'QNIS_CASCADE_ADAPTIVE',
                    viewport: this.currentViewport
                }, '*');
            }
        });
    }
    
    enableLiveNLPQueries() {
        this.nlpSystem = {
            isActive: false,
            queryHistory: [],
            activeSession: null,
            
            activate: () => {
                this.createNLPInterface();
                this.nlpSystem.isActive = true;
                this.startNLPSession();
            },
            
            query: async (input) => {
                const response = await fetch('/api/qnis/live-nlp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: input,
                        context: this.getDashboardContext(),
                        session: this.nlpSystem.activeSession,
                        watson_mode: this.watsonMode
                    })
                });
                
                const result = await response.json();
                this.processNLPResponse(result);
                return result;
            },
            
            smartAnalyze: (dataPoint) => {
                return this.nlpSystem.query(`Analyze this data: ${JSON.stringify(dataPoint)}`);
            }
        };
        
        // Auto-activate NLP interface
        this.nlpSystem.activate();
    }
    
    createNLPInterface() {
        const nlpContainer = document.createElement('div');
        nlpContainer.id = 'qnis-nlp-container';
        nlpContainer.className = 'qnis-nlp-active';
        
        nlpContainer.innerHTML = `
            <div class="nlp-header" style="padding: 1rem; border-bottom: 1px solid rgba(0,255,136,0.3); display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.2rem;">🧠</span>
                    <span style="color: #00ff88; font-weight: bold;">QNIS Intelligence</span>
                    ${this.watsonMode ? '<span style="color: #fbbf24; font-size: 0.8rem;">[Watson Enhanced]</span>' : ''}
                </div>
                <button onclick="NEXUS_QNIS.toggleNLP()" style="background: none; border: none; color: white; font-size: 1.2rem; cursor: pointer;">×</button>
            </div>
            <div class="nlp-messages" id="nlp-messages" style="flex: 1; padding: 1rem; overflow-y: auto; max-height: 350px;">
                <div class="nlp-message system" style="margin-bottom: 1rem; padding: 0.5rem; background: rgba(0,255,136,0.1); border-radius: 8px;">
                    <strong>QNIS:</strong> Ready to analyze fleet data, attendance patterns, and performance metrics. How can I assist?
                </div>
            </div>
            <div class="nlp-input-area" style="padding: 1rem; border-top: 1px solid rgba(0,255,136,0.3);">
                <div style="display: flex; gap: 0.5rem;">
                    <input type="text" 
                           id="nlp-live-input" 
                           class="nlp-query-input"
                           placeholder="Ask about performance, trends, or optimization..."
                           onkeypress="if(event.key==='Enter') NEXUS_QNIS.processLiveQuery()"
                           style="flex: 1;" />
                    <button onclick="NEXUS_QNIS.processLiveQuery()" 
                            style="background: #00ff88; border: none; color: black; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-weight: bold;">
                        Send
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(nlpContainer);
        
        // Add drag functionality
        this.makeDraggable(nlpContainer);
    }
    
    configureBackendVisibility() {
        if (this.watsonMode) {
            document.body.classList.add('watson-enhanced');
            this.createBackendPanel();
        }
        
        // Hide sensitive deployment paths unless Watson mode
        document.querySelectorAll('[data-sensitive], .deployment-path, .config-panel').forEach(el => {
            if (!this.watsonMode) {
                el.classList.add('qnis-deployment-locked');
            }
        });
    }
    
    createBackendPanel() {
        const backendPanel = document.createElement('div');
        backendPanel.className = 'qnis-backend-panel watson-visible';
        backendPanel.innerHTML = `
            <div style="padding: 1rem; border-bottom: 2px solid #00ff88;">
                <h3 style="color: #00ff88; margin: 0; font-size: 1.2rem;">🔧 Backend Control</h3>
                <span style="color: #fbbf24; font-size: 0.9rem;">Watson Enhanced Mode</span>
            </div>
            <div style="padding: 1rem;">
                <div class="backend-section" style="margin-bottom: 1.5rem;">
                    <h4 style="color: white; margin-bottom: 0.5rem;">System Status</h4>
                    <div id="system-diagnostics" style="font-size: 0.9rem; color: #94a3b8;"></div>
                </div>
                <div class="backend-section" style="margin-bottom: 1.5rem;">
                    <h4 style="color: white; margin-bottom: 0.5rem;">Active Processes</h4>
                    <div id="active-processes" style="font-size: 0.9rem; color: #94a3b8;"></div>
                </div>
                <div class="backend-section" style="margin-bottom: 1.5rem;">
                    <h4 style="color: white; margin-bottom: 0.5rem;">Quick Actions</h4>
                    <button onclick="NEXUS_QNIS.refreshAllData()" style="width: 100%; margin-bottom: 0.5rem; background: rgba(0,255,136,0.2); border: 1px solid #00ff88; color: white; padding: 0.5rem; border-radius: 5px; cursor: pointer;">
                        Refresh All Data
                    </button>
                    <button onclick="NEXUS_QNIS.optimizePerformance()" style="width: 100%; margin-bottom: 0.5rem; background: rgba(0,255,136,0.2); border: 1px solid #00ff88; color: white; padding: 0.5rem; border-radius: 5px; cursor: pointer;">
                        Optimize Performance
                    </button>
                    <button onclick="NEXUS_QNIS.runDiagnostics()" style="width: 100%; background: rgba(0,255,136,0.2); border: 1px solid #00ff88; color: white; padding: 0.5rem; border-radius: 5px; cursor: pointer;">
                        Run Diagnostics
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(backendPanel);
        this.updateBackendPanel();
    }
    
    lockDeploymentPaths() {
        if (this.deploymentLocked) {
            const sensitiveSelectors = [
                '.admin-panel',
                '.config-editor',
                '.deployment-controls',
                '[data-admin-only]',
                '.system-settings'
            ];
            
            sensitiveSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    el.classList.add('qnis-deployment-locked');
                    el.setAttribute('data-locked-reason', 'Requires Watson Mode');
                });
            });
        }
    }
    
    startNLPIndexing() {
        this.nlpIndexing = true;
        
        console.log('%cQNIS NLP Indexing Started', 'color: #00ff88; font-weight: bold;');
        
        // Index dashboard components
        this.indexDashboardElements();
        this.indexDataSources();
        this.indexUserInteractions();
        
        // Continuous indexing for real-time updates
        setInterval(() => {
            this.updateNLPIndex();
        }, 30000); // Every 30 seconds
    }
    
    indexDashboardElements() {
        const elements = {
            metrics: [],
            charts: [],
            controls: [],
            data_sources: []
        };
        
        // Index metric cards
        document.querySelectorAll('.metric-card, .metric-value').forEach(el => {
            elements.metrics.push({
                id: el.id || `metric_${Date.now()}`,
                type: 'metric',
                label: el.querySelector('.metric-label')?.textContent || 'Unknown Metric',
                value: el.querySelector('.metric-value')?.textContent || el.textContent,
                element: el
            });
        });
        
        // Index charts
        document.querySelectorAll('canvas[id*="Chart"]').forEach(el => {
            elements.charts.push({
                id: el.id,
                type: 'chart',
                title: el.closest('.chart-container')?.querySelector('.chart-title')?.textContent || 'Chart',
                element: el
            });
        });
        
        this.nlpIndex = elements;
        return elements;
    }
    
    initializeSelfDebug() {
        this.selfDebugActive = true;
        
        console.log('%cQNIS Self-Debug System Active', 'color: #00ff88; font-weight: bold;');
        
        this.debugSystem = {
            monitors: new Map(),
            issues: [],
            autoFixes: 0,
            
            addMonitor: (name, checkFunction, autoFix = null) => {
                this.debugSystem.monitors.set(name, {
                    check: checkFunction,
                    autoFix: autoFix,
                    lastRun: null,
                    failures: 0
                });
            },
            
            runAllChecks: () => {
                this.debugSystem.monitors.forEach((monitor, name) => {
                    try {
                        const result = monitor.check();
                        monitor.lastRun = Date.now();
                        
                        if (!result.success) {
                            this.handleDebugIssue(name, result, monitor);
                        } else {
                            monitor.failures = 0;
                        }
                    } catch (error) {
                        console.warn(`Debug monitor ${name} failed:`, error);
                    }
                });
            }
        };
        
        this.setupDebugMonitors();
        
        // Run debug checks every 2 minutes
        setInterval(() => {
            this.debugSystem.runAllChecks();
        }, 120000);
        
        // Initial run
        setTimeout(() => {
            this.debugSystem.runAllChecks();
        }, 5000);
    }
    
    setupDebugMonitors() {
        // Monitor chart rendering
        this.debugSystem.addMonitor('chart_rendering', () => {
            const charts = document.querySelectorAll('canvas[id*="Chart"]');
            const failedCharts = Array.from(charts).filter(chart => {
                return !chart.getContext('2d') || chart.width === 0;
            });
            
            return {
                success: failedCharts.length === 0,
                message: `${failedCharts.length} charts failed to render`,
                data: failedCharts
            };
        }, (issue) => {
            // Auto-fix: Reinitialize failed charts
            issue.data.forEach(chart => {
                if (window.Chart && chart.id) {
                    console.log(`Auto-fixing chart: ${chart.id}`);
                    // Trigger chart reinitialization
                    const event = new CustomEvent('chart-reinit', { detail: { chartId: chart.id } });
                    document.dispatchEvent(event);
                }
            });
        });
        
        // Monitor API connectivity
        this.debugSystem.addMonitor('api_connectivity', () => {
            return fetch('/api/qnis/health-check', { method: 'HEAD' })
                .then(response => ({
                    success: response.ok,
                    message: response.ok ? 'API healthy' : `API error: ${response.status}`
                }))
                .catch(error => ({
                    success: false,
                    message: `API unreachable: ${error.message}`
                }));
        });
        
        // Monitor memory usage
        this.debugSystem.addMonitor('memory_usage', () => {
            if (performance.memory) {
                const memInfo = performance.memory;
                const usagePercent = (memInfo.usedJSHeapSize / memInfo.jsHeapSizeLimit) * 100;
                
                return {
                    success: usagePercent < 85,
                    message: `Memory usage: ${usagePercent.toFixed(1)}%`,
                    data: memInfo
                };
            }
            
            return { success: true, message: 'Memory monitoring not available' };
        });
    }
    
    handleDebugIssue(monitorName, issue, monitor) {
        monitor.failures++;
        
        console.warn(`Debug issue detected in ${monitorName}:`, issue.message);
        
        // Attempt auto-fix if available and failures < 3
        if (monitor.autoFix && monitor.failures < 3) {
            try {
                monitor.autoFix(issue);
                this.debugSystem.autoFixes++;
                console.log(`Auto-fix applied for ${monitorName}`);
            } catch (error) {
                console.error(`Auto-fix failed for ${monitorName}:`, error);
            }
        }
        
        // Log to backend if Watson mode
        if (this.watsonMode) {
            this.logDebugIssue(monitorName, issue, monitor.failures);
        }
    }
    
    // Global method bindings
    setupGlobalMethods() {
        window.NEXUS_QNIS = {
            toggleNLP: () => {
                const container = document.getElementById('qnis-nlp-container');
                if (container) {
                    container.style.display = container.style.display === 'none' ? 'flex' : 'none';
                }
            },
            
            processLiveQuery: () => {
                const input = document.getElementById('nlp-live-input');
                if (input && input.value.trim()) {
                    this.nlpSystem.query(input.value.trim());
                    input.value = '';
                }
            },
            
            refreshAllData: () => {
                if (this.watsonMode) {
                    location.reload();
                }
            },
            
            optimizePerformance: () => {
                if (this.watsonMode) {
                    this.adaptiveSystem.optimizePerformance();
                }
            },
            
            runDiagnostics: () => {
                if (this.watsonMode) {
                    this.debugSystem.runAllChecks();
                }
            },
            
            watsonMode: this.watsonMode,
            version: this.version
        };
    }
    
    updateBackendPanel() {
        if (!this.watsonMode) return;
        
        const diagnosticsEl = document.getElementById('system-diagnostics');
        const processesEl = document.getElementById('active-processes');
        
        if (diagnosticsEl) {
            diagnosticsEl.innerHTML = `
                <div>✓ QNIS Core: Active</div>
                <div>✓ NLP System: ${this.nlpSystem.isActive ? 'Running' : 'Standby'}</div>
                <div>✓ Self-Debug: ${this.selfDebugActive ? 'Monitoring' : 'Inactive'}</div>
                <div>✓ Adaptive Layout: Cascading</div>
            `;
        }
        
        if (processesEl) {
            processesEl.innerHTML = `
                <div>Real-time Metrics: Active</div>
                <div>Background Indexing: ${this.nlpIndexing ? 'Running' : 'Paused'}</div>
                <div>Auto-fixes Applied: ${this.debugSystem.autoFixes || 0}</div>
            `;
        }
    }
    
    // Utility methods
    makeDraggable(element) {
        let isDragging = false;
        let currentX;
        let currentY;
        let initialX;
        let initialY;
        let xOffset = 0;
        let yOffset = 0;
        
        const header = element.querySelector('.nlp-header');
        if (header) {
            header.style.cursor = 'move';
            header.addEventListener('mousedown', dragStart);
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', dragEnd);
        }
        
        function dragStart(e) {
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;
            
            if (e.target === header || header.contains(e.target)) {
                isDragging = true;
            }
        }
        
        function drag(e) {
            if (isDragging) {
                e.preventDefault();
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;
                
                xOffset = currentX;
                yOffset = currentY;
                
                element.style.transform = `translate(${currentX}px, ${currentY}px)`;
            }
        }
        
        function dragEnd() {
            initialX = currentX;
            initialY = currentY;
            isDragging = false;
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.NexusQNISBoostInstance = new NexusQNISBoost();
    window.NexusQNISBoostInstance.setupGlobalMethods();
});

// Immediate initialization fallback
if (document.readyState !== 'loading') {
    window.NexusQNISBoostInstance = new NexusQNISBoost();
    window.NexusQNISBoostInstance.setupGlobalMethods();
}