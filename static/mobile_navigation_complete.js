/**
 * TRAXOVO Mobile Navigation Complete - Enterprise Mobile Experience
 * Comprehensive mobile interaction and navigation system
 */

class TRAXOVOMobileNavigation {
    constructor() {
        this.isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        this.viewport = this.getViewportDimensions();
        this.gestureHandlers = new Map();
        this.activeElements = new Set();
        this.init();
    }

    init() {
        this.setupViewport();
        this.createMobileNavigation();
        this.setupTouchHandlers();
        this.setupResponsiveElements();
        this.setupMobileOptimizations();
        this.setupSwipeGestures();
        this.monitorOrientationChanges();
        this.setupViewToggle();
    }

    setupViewport() {
        // Force proper mobile viewport
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.setAttribute('content', 
                'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover'
            );
        }

        // Prevent zoom on input focus
        document.addEventListener('touchstart', (e) => {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        }, { passive: false });

        // Handle safe areas for devices with notches
        this.handleSafeAreas();
    }

    createMobileNavigation() {
        if (window.innerWidth <= 768) {
            this.createBottomNavigation();
            this.createHamburgerMenu();
            this.createMobileHeader();
        }
    }

    createBottomNavigation() {
        // Remove existing navigation if present
        const existingNav = document.querySelector('.mobile-bottom-nav');
        if (existingNav) existingNav.remove();

        const nav = document.createElement('div');
        nav.className = 'mobile-bottom-nav';
        nav.innerHTML = `
            <div class="nav-container">
                <div class="nav-items">
                    <div class="nav-item active" data-target="dashboard">
                        <i class="fas fa-tachometer-alt"></i>
                        <span>Dashboard</span>
                    </div>
                    <div class="nav-item" data-target="assets">
                        <i class="fas fa-cube"></i>
                        <span>Assets</span>
                    </div>
                    <div class="nav-item" data-target="analytics">
                        <i class="fas fa-chart-line"></i>
                        <span>Analytics</span>
                    </div>
                    <div class="nav-item" data-target="alerts">
                        <i class="fas fa-bell"></i>
                        <span>Alerts</span>
                    </div>
                    <div class="nav-item" data-target="menu">
                        <i class="fas fa-bars"></i>
                        <span>Menu</span>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(nav);
        this.attachNavigationHandlers(nav);
    }

    createHamburgerMenu() {
        const hamburger = document.createElement('div');
        hamburger.className = 'mobile-hamburger';
        hamburger.innerHTML = `
            <div class="hamburger-icon">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;

        const header = document.querySelector('.header-section');
        if (header) {
            header.appendChild(hamburger);
        }

        hamburger.addEventListener('click', this.toggleMobileMenu.bind(this));
    }

    createMobileHeader() {
        const header = document.querySelector('.header-section');
        if (header && window.innerWidth <= 768) {
            header.classList.add('mobile-optimized');
            
            // Add mobile-specific header elements
            const mobileControls = document.createElement('div');
            mobileControls.className = 'mobile-header-controls';
            mobileControls.innerHTML = `
                <div class="status-indicators">
                    <div class="connection-status online">
                        <i class="fas fa-wifi"></i>
                    </div>
                    <div class="qnis-status active">
                        <i class="fas fa-brain"></i>
                    </div>
                </div>
            `;
            
            header.appendChild(mobileControls);
        }
    }

    setupTouchHandlers() {
        // Enhanced touch handling for mobile elements
        const cards = document.querySelectorAll('.metric-card, .card');
        cards.forEach(card => {
            this.makeTouchFriendly(card);
        });

        // Handle tap highlights
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
    }

    makeTouchFriendly(element) {
        element.style.cursor = 'pointer';
        element.style.webkitTapHighlightColor = 'rgba(0, 212, 255, 0.2)';
        
        // Add touch feedback
        element.addEventListener('touchstart', (e) => {
            element.style.transform = 'scale(0.98)';
            element.style.transition = 'transform 0.1s ease';
        }, { passive: true });

        element.addEventListener('touchend', (e) => {
            setTimeout(() => {
                element.style.transform = 'scale(1)';
            }, 100);
        }, { passive: true });
    }

    setupResponsiveElements() {
        // Fix card layouts for mobile
        const cards = document.querySelectorAll('.metric-card, .card');
        cards.forEach(card => {
            if (window.innerWidth <= 768) {
                card.classList.add('mobile-card');
                this.optimizeCardContent(card);
            }
        });

        // Fix table responsiveness
        this.makeTablesResponsive();
        
        // Fix chart containers
        this.optimizeCharts();
    }

    optimizeCardContent(card) {
        // Ensure all text is readable on mobile
        const texts = card.querySelectorAll('*');
        texts.forEach(text => {
            const computedStyle = window.getComputedStyle(text);
            const fontSize = parseFloat(computedStyle.fontSize);
            
            if (fontSize < 14) {
                text.style.fontSize = '14px';
            }
        });

        // Ensure adequate touch targets
        const clickables = card.querySelectorAll('button, a, [onclick], [data-action]');
        clickables.forEach(element => {
            const rect = element.getBoundingClientRect();
            if (rect.height < 44) {
                element.style.minHeight = '44px';
                element.style.display = 'flex';
                element.style.alignItems = 'center';
                element.style.justifyContent = 'center';
            }
        });
    }

    makeTablesResponsive() {
        const tables = document.querySelectorAll('table');
        tables.forEach(table => {
            if (!table.closest('.table-container')) {
                const container = document.createElement('div');
                container.className = 'table-container';
                table.parentNode.insertBefore(container, table);
                container.appendChild(table);
            }
        });
    }

    optimizeCharts() {
        const chartContainers = document.querySelectorAll('.chart-container, [id*="chart"]');
        chartContainers.forEach(container => {
            if (window.innerWidth <= 768) {
                container.style.width = '100%';
                container.style.overflowX = 'auto';
                
                const canvas = container.querySelector('canvas');
                if (canvas) {
                    canvas.style.maxWidth = '100%';
                    canvas.style.height = 'auto';
                }
            }
        });
    }

    setupMobileOptimizations() {
        // Prevent rubber band scrolling
        document.body.addEventListener('touchmove', (e) => {
            if (e.target === document.body) {
                e.preventDefault();
            }
        }, { passive: false });

        // Fix iOS Safari viewport issues
        if (this.isIOS()) {
            this.fixIOSViewport();
        }

        // Optimize for Android Chrome
        if (this.isAndroid()) {
            this.optimizeForAndroid();
        }
    }

    setupSwipeGestures() {
        let startX, startY, currentX, currentY;
        
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (!startX || !startY) return;
            
            currentX = e.touches[0].clientX;
            currentY = e.touches[0].clientY;
        }, { passive: true });

        document.addEventListener('touchend', (e) => {
            if (!startX || !startY || !currentX || !currentY) return;
            
            const diffX = startX - currentX;
            const diffY = startY - currentY;
            
            // Horizontal swipe detection
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                if (diffX > 0) {
                    this.handleSwipeLeft();
                } else {
                    this.handleSwipeRight();
                }
            }
            
            // Reset values
            startX = startY = currentX = currentY = null;
        }, { passive: true });
    }

    handleSwipeLeft() {
        // Navigate to next section or close menu
        const menu = document.querySelector('.mobile-menu.active');
        if (menu) {
            this.closeMobileMenu();
        }
    }

    handleSwipeRight() {
        // Navigate to previous section or open menu
        if (!document.querySelector('.mobile-menu.active')) {
            this.openMobileMenu();
        }
    }

    toggleMobileMenu() {
        const menu = document.querySelector('.mobile-menu');
        if (menu) {
            if (menu.classList.contains('active')) {
                this.closeMobileMenu();
            } else {
                this.openMobileMenu();
            }
        } else {
            this.createMobileMenu();
        }
    }

    createMobileMenu() {
        const menu = document.createElement('div');
        menu.className = 'mobile-menu';
        menu.innerHTML = `
            <div class="menu-overlay"></div>
            <div class="menu-content">
                <div class="menu-header">
                    <h3>TRAXOVO Menu</h3>
                    <button class="close-menu">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="menu-items">
                    <a href="/dashboard" class="menu-item">
                        <i class="fas fa-tachometer-alt"></i>
                        <span>Dashboard</span>
                    </a>
                    <a href="/assets" class="menu-item">
                        <i class="fas fa-cube"></i>
                        <span>Asset Management</span>
                    </a>
                    <a href="/analytics" class="menu-item">
                        <i class="fas fa-chart-line"></i>
                        <span>Analytics</span>
                    </a>
                    <a href="/reports" class="menu-item">
                        <i class="fas fa-file-alt"></i>
                        <span>Reports</span>
                    </a>
                    <a href="/settings" class="menu-item">
                        <i class="fas fa-cog"></i>
                        <span>Settings</span>
                    </a>
                </div>
            </div>
        `;

        document.body.appendChild(menu);
        
        // Add event listeners
        menu.querySelector('.close-menu').addEventListener('click', this.closeMobileMenu.bind(this));
        menu.querySelector('.menu-overlay').addEventListener('click', this.closeMobileMenu.bind(this));
        
        // Show menu
        setTimeout(() => {
            menu.classList.add('active');
        }, 10);
    }

    openMobileMenu() {
        const menu = document.querySelector('.mobile-menu');
        if (menu) {
            menu.classList.add('active');
            document.body.style.overflow = 'hidden';
        } else {
            this.createMobileMenu();
        }
    }

    closeMobileMenu() {
        const menu = document.querySelector('.mobile-menu');
        if (menu) {
            menu.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    attachNavigationHandlers(nav) {
        const navItems = nav.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                // Remove active class from all items
                navItems.forEach(navItem => navItem.classList.remove('active'));
                
                // Add active class to clicked item
                item.classList.add('active');
                
                // Handle navigation
                const target = item.dataset.target;
                this.handleNavigation(target);
            });
        });
    }

    handleNavigation(target) {
        switch (target) {
            case 'dashboard':
                this.scrollToSection('.dashboard-grid');
                break;
            case 'assets':
                this.scrollToSection('.asset-overview');
                break;
            case 'analytics':
                this.scrollToSection('.analytics-section');
                break;
            case 'alerts':
                this.showAlerts();
                break;
            case 'menu':
                this.toggleMobileMenu();
                break;
        }
    }

    scrollToSection(selector) {
        const section = document.querySelector(selector);
        if (section) {
            section.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }
    }

    showAlerts() {
        // Implementation for showing alerts
        console.log('Showing alerts');
    }

    monitorOrientationChanges() {
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });

        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    handleOrientationChange() {
        this.viewport = this.getViewportDimensions();
        
        // Adjust layout for orientation
        if (window.innerHeight < window.innerWidth) {
            // Landscape mode
            document.body.classList.add('landscape');
            document.body.classList.remove('portrait');
        } else {
            // Portrait mode
            document.body.classList.add('portrait');
            document.body.classList.remove('landscape');
        }

        // Re-optimize elements
        this.setupResponsiveElements();
    }

    handleResize() {
        if (window.innerWidth > 768) {
            // Switch to desktop mode
            const mobileNav = document.querySelector('.mobile-bottom-nav');
            if (mobileNav) mobileNav.remove();
            
            const mobileMenu = document.querySelector('.mobile-menu');
            if (mobileMenu) mobileMenu.remove();
        } else if (window.innerWidth <= 768) {
            // Ensure mobile navigation exists
            if (!document.querySelector('.mobile-bottom-nav')) {
                this.createBottomNavigation();
            }
        }
    }

    handleTouchStart(e) {
        const element = e.target.closest('.metric-card, .card, button, a');
        if (element) {
            element.classList.add('touch-active');
        }
    }

    handleTouchEnd(e) {
        const elements = document.querySelectorAll('.touch-active');
        elements.forEach(element => {
            setTimeout(() => {
                element.classList.remove('touch-active');
            }, 150);
        });
    }

    getViewportDimensions() {
        return {
            width: window.innerWidth,
            height: window.innerHeight,
            orientation: window.innerHeight > window.innerWidth ? 'portrait' : 'landscape'
        };
    }

    isIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent);
    }

    isAndroid() {
        return /Android/.test(navigator.userAgent);
    }

    fixIOSViewport() {
        // Fix iOS Safari viewport issues
        const setViewportHeight = () => {
            document.documentElement.style.setProperty('--vh', `${window.innerHeight * 0.01}px`);
        };
        
        setViewportHeight();
        window.addEventListener('resize', setViewportHeight);
    }

    optimizeForAndroid() {
        // Android Chrome optimizations
        document.body.classList.add('android-optimized');
    }

    handleSafeAreas() {
        // Handle iPhone notch and other safe areas
        if (CSS.supports('padding: env(safe-area-inset-top)')) {
            document.documentElement.style.setProperty('--safe-top', 'env(safe-area-inset-top)');
            document.documentElement.style.setProperty('--safe-bottom', 'env(safe-area-inset-bottom)');
            document.documentElement.style.setProperty('--safe-left', 'env(safe-area-inset-left)');
            document.documentElement.style.setProperty('--safe-right', 'env(safe-area-inset-right)');
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new TRAXOVOMobileNavigation();
    });
} else {
    new TRAXOVOMobileNavigation();
}