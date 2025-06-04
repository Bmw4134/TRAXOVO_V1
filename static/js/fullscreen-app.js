
        // QQ Universal Fullscreen App Experience JavaScript
        
        class QQUniversalFullscreen {
            constructor() {
                this.isFullscreen = false;
                this.currentModule = null;
                this.deviceType = this.detectDeviceType();
                this.originalContent = null;
                this.fullscreenContainer = null;
                
                this.init();
            }
            
            init() {
                this.createFullscreenContainer();
                this.setupEventListeners();
                this.registerServiceWorker();
                this.setupPWAFeatures();
                this.initializeAppLikeFeatures();
            }
            
            detectDeviceType() {
                const width = window.innerWidth;
                const height = window.innerHeight;
                const isTouch = 'ontouchstart' in window;
                const orientation = width > height ? 'landscape' : 'portrait';
                
                if (isTouch && width <= 768) {
                    return `mobile_${orientation}`;
                } else if (isTouch && width <= 1024) {
                    return `tablet_${orientation}`;
                } else if (width <= 1920) {
                    return 'desktop';
                } else {
                    return 'large_desktop';
                }
            }
            
            createFullscreenContainer() {
                this.fullscreenContainer = document.createElement('div');
                this.fullscreenContainer.className = 'qq-fullscreen-container';
                this.fullscreenContainer.innerHTML = `
                    <div class="qq-fullscreen-header">
                        <div class="qq-fullscreen-title">TRAXOVO Fleet Intelligence</div>
                        <div class="qq-fullscreen-controls">
                            <button class="qq-fullscreen-btn" onclick="qqFullscreen.toggleOrientation()" title="Rotate">
                                <i class="fas fa-mobile-alt"></i>
                            </button>
                            <button class="qq-fullscreen-btn" onclick="qqFullscreen.toggleImmersive()" title="Immersive">
                                <i class="fas fa-expand-arrows-alt"></i>
                            </button>
                            <button class="qq-fullscreen-btn" onclick="qqFullscreen.exitFullscreen()" title="Exit">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                    <div class="qq-fullscreen-content"></div>
                `;
                
                document.body.appendChild(this.fullscreenContainer);
                
                // Create toggle button
                const toggleBtn = document.createElement('button');
                toggleBtn.className = 'qq-universal-fullscreen-toggle';
                toggleBtn.innerHTML = '<i class="fas fa-expand"></i>';
                toggleBtn.onclick = () => this.enterFullscreen();
                toggleBtn.title = 'Enter App Mode';
                
                document.body.appendChild(toggleBtn);
                this.toggleButton = toggleBtn;
            }
            
            setupEventListeners() {
                // Handle fullscreen change events
                document.addEventListener('fullscreenchange', this.handleFullscreenChange.bind(this));
                document.addEventListener('webkitfullscreenchange', this.handleFullscreenChange.bind(this));
                document.addEventListener('mozfullscreenchange', this.handleFullscreenChange.bind(this));
                document.addEventListener('MSFullscreenChange', this.handleFullscreenChange.bind(this));
                
                // Handle orientation changes
                window.addEventListener('orientationchange', this.handleOrientationChange.bind(this));
                window.addEventListener('resize', this.handleResize.bind(this));
                
                // Handle keyboard shortcuts
                document.addEventListener('keydown', this.handleKeyDown.bind(this));
                
                // Handle back button (mobile)
                window.addEventListener('popstate', this.handlePopState.bind(this));
                
                // Handle visibility changes
                document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
            }
            
            enterFullscreen(moduleName = null) {
                if (this.isFullscreen) return;
                
                this.currentModule = moduleName || this.getCurrentModuleName();
                this.originalContent = document.body.innerHTML;
                
                // Get current page content
                const mainContent = document.querySelector('.main-content') || document.body;
                const contentClone = mainContent.cloneNode(true);
                
                // Update fullscreen container
                const contentArea = this.fullscreenContainer.querySelector('.qq-fullscreen-content');
                contentArea.innerHTML = '';
                contentArea.appendChild(contentClone);
                
                // Apply device-specific optimizations
                this.applyDeviceOptimizations();
                
                // Show fullscreen container
                this.fullscreenContainer.classList.add('active');
                this.isFullscreen = true;
                
                // Update toggle button
                this.toggleButton.innerHTML = '<i class="fas fa-compress"></i>';
                this.toggleButton.title = 'Exit App Mode';
                this.toggleButton.classList.add('active');
                this.toggleButton.onclick = () => this.exitFullscreen();
                
                // Request native fullscreen if supported
                this.requestNativeFullscreen();
                
                // Update page title
                document.title = `TRAXOVO - ${this.currentModule || 'App Mode'}`;
                
                // Track session
                this.trackFullscreenSession('enter');
                
                console.log('QQ Universal Fullscreen: ENTERED - App-like experience active');
            }
            
            exitFullscreen() {
                if (!this.isFullscreen) return;
                
                // Hide fullscreen container
                this.fullscreenContainer.classList.remove('active');
                this.isFullscreen = false;
                
                // Update toggle button
                this.toggleButton.innerHTML = '<i class="fas fa-expand"></i>';
                this.toggleButton.title = 'Enter App Mode';
                this.toggleButton.classList.remove('active');
                this.toggleButton.onclick = () => this.enterFullscreen();
                
                // Exit native fullscreen
                this.exitNativeFullscreen();
                
                // Restore original title
                document.title = 'TRAXOVO Fleet Intelligence';
                
                // Track session
                this.trackFullscreenSession('exit');
                
                console.log('QQ Universal Fullscreen: EXITED - Standard view restored');
            }
            
            applyDeviceOptimizations() {
                const container = this.fullscreenContainer;
                const content = container.querySelector('.qq-fullscreen-content');
                
                // Apply device-specific classes
                container.classList.add(`qq-device-${this.deviceType}`);
                
                // Mobile optimizations
                if (this.deviceType.includes('mobile')) {
                    content.classList.add('qq-native-scroll', 'qq-touch-optimized');
                    
                    // Hide address bar on mobile
                    setTimeout(() => {
                        window.scrollTo(0, 1);
                    }, 100);
                }
                
                // Tablet optimizations
                if (this.deviceType.includes('tablet')) {
                    content.classList.add('qq-native-scroll', 'qq-touch-optimized');
                }
                
                // Apply app-like transitions
                content.classList.add('qq-app-transition');
                
                // Optimize viewport
                this.optimizeViewport();
            }
            
            optimizeViewport() {
                let viewport = document.querySelector('meta[name="viewport"]');
                if (!viewport) {
                    viewport = document.createElement('meta');
                    viewport.name = 'viewport';
                    document.head.appendChild(viewport);
                }
                
                if (this.deviceType.includes('mobile')) {
                    viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover';
                } else {
                    viewport.content = 'width=device-width, initial-scale=1.0';
                }
            }
            
            requestNativeFullscreen() {
                const element = this.fullscreenContainer;
                
                if (element.requestFullscreen) {
                    element.requestFullscreen();
                } else if (element.webkitRequestFullscreen) {
                    element.webkitRequestFullscreen();
                } else if (element.mozRequestFullScreen) {
                    element.mozRequestFullScreen();
                } else if (element.msRequestFullscreen) {
                    element.msRequestFullscreen();
                }
            }
            
            exitNativeFullscreen() {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                } else if (document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                }
            }
            
            toggleOrientation() {
                if (screen.orientation && screen.orientation.lock) {
                    const currentOrientation = screen.orientation.angle;
                    const newOrientation = currentOrientation === 0 ? 'landscape' : 'portrait';
                    screen.orientation.lock(newOrientation).catch(console.log);
                }
            }
            
            toggleImmersive() {
                const container = this.fullscreenContainer;
                const header = container.querySelector('.qq-fullscreen-header');
                
                if (header.style.display === 'none') {
                    header.style.display = 'flex';
                    container.classList.remove('qq-immersive-mode');
                } else {
                    header.style.display = 'none';
                    container.classList.add('qq-immersive-mode');
                }
            }
            
            getCurrentModuleName() {
                const path = window.location.pathname;
                if (path.includes('quantum-dashboard')) return 'Quantum Dashboard';
                if (path.includes('fleet-map')) return 'Fleet Map';
                if (path.includes('attendance-matrix')) return 'Attendance Matrix';
                if (path.includes('asset-manager')) return 'Asset Manager';
                if (path.includes('executive-dashboard')) return 'Executive Dashboard';
                if (path.includes('smart-po')) return 'Smart PO System';
                if (path.includes('dispatch-system')) return 'Dispatch System';
                if (path.includes('estimating-system')) return 'Estimating System';
                return 'TRAXOVO Platform';
            }
            
            registerServiceWorker() {
                if ('serviceWorker' in navigator) {
                    navigator.serviceWorker.register('/static/sw.js')
                        .then(registration => {
                            console.log('Service Worker registered:', registration);
                        })
                        .catch(error => {
                            console.log('Service Worker registration failed:', error);
                        });
                }
            }
            
            setupPWAFeatures() {
                // Add to home screen prompt
                let deferredPrompt;
                
                window.addEventListener('beforeinstallprompt', (e) => {
                    e.preventDefault();
                    deferredPrompt = e;
                    
                    // Show install button
                    this.showInstallPrompt(deferredPrompt);
                });
                
                // Handle app installed
                window.addEventListener('appinstalled', () => {
                    console.log('TRAXOVO PWA installed successfully');
                    deferredPrompt = null;
                });
            }
            
            showInstallPrompt(deferredPrompt) {
                const installBtn = document.createElement('button');
                installBtn.className = 'qq-install-btn';
                installBtn.innerHTML = '<i class="fas fa-download"></i> Install App';
                installBtn.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 80px;
                    background: linear-gradient(45deg, #27ae60, #2ecc71);
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 6px;
                    cursor: pointer;
                    z-index: 9998;
                    font-size: 14px;
                    font-weight: 600;
                `;
                
                installBtn.onclick = () => {
                    deferredPrompt.prompt();
                    deferredPrompt.userChoice.then((result) => {
                        if (result.outcome === 'accepted') {
                            console.log('User accepted the install prompt');
                        }
                        installBtn.remove();
                        deferredPrompt = null;
                    });
                };
                
                document.body.appendChild(installBtn);
                
                // Auto-hide after 10 seconds
                setTimeout(() => {
                    if (installBtn.parentNode) {
                        installBtn.remove();
                    }
                }, 10000);
            }
            
            initializeAppLikeFeatures() {
                // Prevent zoom on double tap (mobile)
                let lastTouchEnd = 0;
                document.addEventListener('touchend', (e) => {
                    const now = (new Date()).getTime();
                    if (now - lastTouchEnd <= 300) {
                        e.preventDefault();
                    }
                    lastTouchEnd = now;
                }, false);
                
                // Prevent context menu on long press (mobile)
                document.addEventListener('contextmenu', (e) => {
                    if (this.isFullscreen) {
                        e.preventDefault();
                    }
                });
                
                // Handle pull-to-refresh
                this.setupPullToRefresh();
            }
            
            setupPullToRefresh() {
                let startY = 0;
                let currentY = 0;
                let pullDistance = 0;
                
                document.addEventListener('touchstart', (e) => {
                    if (this.isFullscreen && window.scrollY === 0) {
                        startY = e.touches[0].clientY;
                    }
                });
                
                document.addEventListener('touchmove', (e) => {
                    if (this.isFullscreen && startY > 0) {
                        currentY = e.touches[0].clientY;
                        pullDistance = currentY - startY;
                        
                        if (pullDistance > 100) {
                            // Show pull to refresh indicator
                            console.log('Pull to refresh triggered');
                            this.refreshContent();
                            startY = 0;
                        }
                    }
                });
            }
            
            refreshContent() {
                // Refresh current module content
                if (this.currentModule) {
                    window.location.reload();
                }
            }
            
            trackFullscreenSession(action) {
                // Track fullscreen usage analytics
                fetch('/api/fullscreen-analytics', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        action: action,
                        module: this.currentModule,
                        device_type: this.deviceType,
                        timestamp: new Date().toISOString()
                    })
                }).catch(() => {
                    // Silent fail - analytics are non-critical
                });
            }
            
            // Event handlers
            handleFullscreenChange() {
                // Handle native fullscreen changes
            }
            
            handleOrientationChange() {
                setTimeout(() => {
                    this.deviceType = this.detectDeviceType();
                    if (this.isFullscreen) {
                        this.applyDeviceOptimizations();
                    }
                }, 100);
            }
            
            handleResize() {
                this.deviceType = this.detectDeviceType();
            }
            
            handleKeyDown(e) {
                if (this.isFullscreen) {
                    // F11 or Escape to exit fullscreen
                    if (e.key === 'F11' || e.key === 'Escape') {
                        e.preventDefault();
                        this.exitFullscreen();
                    }
                }
            }
            
            handlePopState(e) {
                if (this.isFullscreen) {
                    e.preventDefault();
                    this.exitFullscreen();
                }
            }
            
            handleVisibilityChange() {
                if (document.hidden && this.isFullscreen) {
                    // App went to background
                    console.log('App backgrounded');
                } else if (!document.hidden && this.isFullscreen) {
                    // App came to foreground
                    console.log('App foregrounded');
                }
            }
        }
        
        // Initialize QQ Universal Fullscreen
        let qqFullscreen;
        document.addEventListener('DOMContentLoaded', () => {
            qqFullscreen = new QQUniversalFullscreen();
            console.log('QQ Universal Fullscreen App Experience: INITIALIZED');
        });
        
        // Global functions
        function enterFullscreenMode(moduleName) {
            if (qqFullscreen) {
                qqFullscreen.enterFullscreen(moduleName);
            }
        }
        
        function exitFullscreenMode() {
            if (qqFullscreen) {
                qqFullscreen.exitFullscreen();
            }
        }
        