/**
 * TRAXOVO Enterprise Sidebar Navigation
 * Unified collapsible sidebar with mobile optimization
 */

class EnterpriseSidebar {
    constructor() {
        this.isOpen = false;
        this.isMobile = window.innerWidth <= 768;
        this.init();
    }

    init() {
        this.createSidebar();
        this.createToggleButton();
        this.setupEventListeners();
    }

    createSidebar() {
        // Remove existing sidebar if present
        const existingSidebar = document.getElementById('enterprise-sidebar');
        if (existingSidebar) existingSidebar.remove();

        const sidebar = document.createElement('div');
        sidebar.id = 'enterprise-sidebar';
        sidebar.className = 'enterprise-sidebar';
        
        sidebar.innerHTML = `
            <div class="sidebar-header">
                <h3>TRAXOVO</h3>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem; margin: 5px 0 0 0;">Fleet Intelligence</p>
            </div>
            <nav class="sidebar-menu">
                <a href="/dashboard" class="sidebar-link">
                    <i class="icon">📊</i> Dashboard
                </a>
                <a href="/fleet-map" class="sidebar-link">
                    <i class="icon">🗺️</i> Fleet Map
                </a>
                <a href="/asset-manager" class="sidebar-link">
                    <i class="icon">🏗️</i> Asset Manager
                </a>
                <a href="/attendance-matrix" class="sidebar-link">
                    <i class="icon">👥</i> Attendance Matrix
                </a>
                <a href="/billing" class="sidebar-link">
                    <i class="icon">💰</i> Billing Intelligence
                </a>
                <a href="/executive-intelligence" class="sidebar-link">
                    <i class="icon">📈</i> Executive Intelligence
                </a>
                <div class="sidebar-divider"></div>
                <a href="/watson-admin" class="sidebar-link admin-only" style="color: #ffc107;">
                    <i class="icon">⚙️</i> Watson Admin
                </a>
                <a href="/logout" class="sidebar-link logout-link">
                    <i class="icon">🚪</i> Logout
                </a>
            </nav>
        `;

        // Add additional styles
        const style = document.createElement('style');
        style.textContent = `
            .sidebar-divider {
                height: 1px;
                background: rgba(255,255,255,0.1);
                margin: 15px 25px;
            }
            .sidebar-link {
                display: flex;
                align-items: center;
                color: rgba(255, 255, 255, 0.8);
                text-decoration: none;
                padding: 15px 25px;
                transition: all 0.3s ease;
                border-left: 3px solid transparent;
            }
            .sidebar-link:hover {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border-left-color: #667eea;
                text-decoration: none;
            }
            .sidebar-link.active {
                background: rgba(102, 126, 234, 0.2);
                color: white;
                border-left-color: #667eea;
            }
            .sidebar-link .icon {
                margin-right: 12px;
                font-size: 1.1rem;
            }
            .admin-only {
                border-top: 1px solid rgba(255,255,255,0.1);
                margin-top: 10px;
                padding-top: 20px;
            }
            .logout-link {
                border-top: 1px solid rgba(255,255,255,0.1);
                margin-top: 10px;
                color: rgba(255, 100, 100, 0.8);
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(sidebar);
        this.sidebar = sidebar;
    }

    createToggleButton() {
        // Remove existing toggle if present
        const existingToggle = document.getElementById('sidebar-toggle');
        if (existingToggle) existingToggle.remove();

        const toggle = document.createElement('button');
        toggle.id = 'sidebar-toggle';
        toggle.className = 'mobile-toggle';
        toggle.innerHTML = '☰';
        toggle.setAttribute('aria-label', 'Toggle navigation menu');
        
        document.body.appendChild(toggle);
        this.toggle = toggle;
    }

    setupEventListeners() {
        // Toggle button click
        this.toggle.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleSidebar();
        });

        // Close sidebar when clicking outside (mobile)
        document.addEventListener('click', (e) => {
            if (this.isMobile && this.isOpen && 
                !this.sidebar.contains(e.target) && 
                !this.toggle.contains(e.target)) {
                this.closeSidebar();
            }
        });

        // Close sidebar when navigating (mobile)
        this.sidebar.querySelectorAll('.sidebar-link').forEach(link => {
            link.addEventListener('click', () => {
                if (this.isMobile) {
                    this.closeSidebar();
                }
            });
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth <= 768;
            
            if (wasMobile !== this.isMobile) {
                if (!this.isMobile && this.isOpen) {
                    // Desktop view - keep sidebar open
                    this.sidebar.style.transform = 'translateX(0)';
                } else if (this.isMobile) {
                    // Mobile view - close sidebar
                    this.closeSidebar();
                }
            }
        });

        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeSidebar();
            }
        });

        // Set active link based on current page
        this.setActiveLink();
    }

    toggleSidebar() {
        if (this.isOpen) {
            this.closeSidebar();
        } else {
            this.openSidebar();
        }
    }

    openSidebar() {
        this.sidebar.classList.add('show');
        this.sidebar.style.transform = 'translateX(0)';
        this.isOpen = true;
        
        // Add overlay for mobile
        if (this.isMobile) {
            this.createOverlay();
        }
        
        // Update toggle button
        this.toggle.innerHTML = '✕';
        this.toggle.setAttribute('aria-expanded', 'true');
    }

    closeSidebar() {
        this.sidebar.classList.remove('show');
        this.sidebar.style.transform = 'translateX(-100%)';
        this.isOpen = false;
        
        // Remove overlay
        this.removeOverlay();
        
        // Update toggle button
        this.toggle.innerHTML = '☰';
        this.toggle.setAttribute('aria-expanded', 'false');
    }

    createOverlay() {
        if (document.getElementById('sidebar-overlay')) return;
        
        const overlay = document.createElement('div');
        overlay.id = 'sidebar-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
            transition: opacity 0.3s ease;
        `;
        
        overlay.addEventListener('click', () => this.closeSidebar());
        document.body.appendChild(overlay);
    }

    removeOverlay() {
        const overlay = document.getElementById('sidebar-overlay');
        if (overlay) overlay.remove();
    }

    setActiveLink() {
        const currentPath = window.location.pathname;
        const links = this.sidebar.querySelectorAll('.sidebar-link');
        
        links.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }
}

// Initialize sidebar when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.enterpriseSidebar = new EnterpriseSidebar();
});

// Export for global use
window.EnterpriseSidebar = EnterpriseSidebar;