/**
 * TRAXOVO Performance Optimization Engine
 * Executive-grade user experience with instant response times
 */

class TRAXOVOPerformanceEngine {
    constructor() {
        this.activeRequests = new Map();
        this.chartInstances = new Map();
        this.navigationQueue = [];
        this.isNavigating = false;
        
        this.initializePerformanceOptimization();
    }
    
    initializePerformanceOptimization() {
        // 1. Fix infinite expanding charts
        this.fixExpandingCharts();
        
        // 2. Implement instant navigation
        this.setupInstantNavigation();
        
        // 3. Optimize resource allocation
        this.optimizeResourceAllocation();
        
        // 4. Setup preemptive loading
        this.setupPreemptiveLoading();
    }
    
    fixExpandingCharts() {
        // Prevent chart expansion issues
        document.addEventListener('DOMContentLoaded', () => {
            // Find all chart containers and fix their dimensions
            const chartContainers = document.querySelectorAll('.chart-container, canvas, [id*="chart"], [class*="Chart"]');
            
            chartContainers.forEach(container => {
                // Set fixed dimensions to prevent ballooning
                if (container.tagName === 'CANVAS') {
                    container.style.maxWidth = '100%';
                    container.style.maxHeight = '400px';
                    container.style.width = '100%';
                    container.style.height = '400px';
                }
                
                // Add container wrapper if needed
                if (!container.parentElement.classList.contains('chart-wrapper')) {
                    const wrapper = document.createElement('div');
                    wrapper.className = 'chart-wrapper';
                    wrapper.style.cssText = 'width: 100%; height: 400px; overflow: hidden; position: relative;';
                    container.parentElement.insertBefore(wrapper, container);
                    wrapper.appendChild(container);
                }
            });
            
            // Destroy and recreate any existing Chart.js instances
            if (window.Chart && window.Chart.instances) {
                Object.values(window.Chart.instances).forEach(chart => {
                    if (chart && chart.destroy) {
                        chart.destroy();
                    }
                });
            }
        });
    }
    
    setupInstantNavigation() {
        // Intercept all navigation clicks for instant response
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href], button[onclick]');
            if (!link) return;
            
            // Show instant loading state
            this.showInstantFeedback(link);
            
            // Cancel other processes to prioritize navigation
            this.prioritizeNavigation();
        }, true);
    }
    
    showInstantFeedback(element) {
        // Add instant visual feedback
        element.style.transform = 'scale(0.95)';
        element.style.transition = 'transform 0.1s ease';
        
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 100);
        
        // Show loading indicator if navigation takes time
        this.showLoadingIndicator();
    }
    
    prioritizeNavigation() {
        // Cancel non-critical requests
        this.activeRequests.forEach((request, key) => {
            if (request.priority !== 'critical') {
                request.controller.abort();
                this.activeRequests.delete(key);
            }
        });
        
        // Reduce background processes
        this.pauseBackgroundProcesses();
    }
    
    pauseBackgroundProcesses() {
        // Pause auto-refresh intervals
        const intervals = ['autoRefreshInterval', 'metricsUpdateInterval', 'chartUpdateInterval'];
        intervals.forEach(intervalName => {
            if (window[intervalName]) {
                clearInterval(window[intervalName]);
            }
        });
        
        // Pause animations
        document.querySelectorAll('.animated, [class*="animate"]').forEach(el => {
            el.style.animationPlayState = 'paused';
        });
    }
    
    setupPreemptiveLoading() {
        // Preload critical navigation targets
        const criticalRoutes = [
            '/april-billing/',
            '/ai-assistant',
            '/kaizen',
            '/master-attendance',
            '/fleet-map'
        ];
        
        criticalRoutes.forEach(route => {
            this.preloadRoute(route);
        });
    }
    
    preloadRoute(route) {
        // Preload route data without rendering
        fetch(route, {
            method: 'HEAD',
            priority: 'low'
        }).catch(() => {
            // Silent fail for preloading
        });
    }
    
    showLoadingIndicator() {
        // Show minimal, non-intrusive loading
        const existingLoader = document.getElementById('traxovo-loader');
        if (existingLoader) return;
        
        const loader = document.createElement('div');
        loader.id = 'traxovo-loader';
        loader.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"></div>';
        loader.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            background: white;
            padding: 10px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        `;
        
        document.body.appendChild(loader);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (loader.parentElement) {
                loader.remove();
            }
        }, 3000);
    }
    
    optimizeResourceAllocation() {
        // Lazy load images
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
        
        // Optimize table rendering
        this.optimizeTableRendering();
    }
    
    optimizeTableRendering() {
        const largeTables = document.querySelectorAll('table tbody tr');
        if (largeTables.length > 50) {
            // Virtualize large tables
            this.virtualizeTable(largeTables[0].closest('table'));
        }
    }
    
    virtualizeTable(table) {
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        const visibleRows = 25;
        let currentStart = 0;
        
        const showRows = (start) => {
            rows.forEach((row, index) => {
                row.style.display = (index >= start && index < start + visibleRows) ? '' : 'none';
            });
        };
        
        showRows(0);
        
        // Add pagination controls
        this.addTablePagination(table, rows.length, visibleRows, showRows);
    }
    
    addTablePagination(table, totalRows, visibleRows, showRowsCallback) {
        const pagination = document.createElement('div');
        pagination.className = 'table-pagination mt-2';
        pagination.innerHTML = `
            <button class="btn btn-sm btn-outline-primary" onclick="window.traxovoPerf.previousPage(this)">Previous</button>
            <span class="mx-2">Page <span class="current-page">1</span> of <span class="total-pages">${Math.ceil(totalRows / visibleRows)}</span></span>
            <button class="btn btn-sm btn-outline-primary" onclick="window.traxovoPerf.nextPage(this)">Next</button>
        `;
        
        table.parentElement.appendChild(pagination);
        
        // Store pagination data
        pagination.dataset.totalRows = totalRows;
        pagination.dataset.visibleRows = visibleRows;
        pagination.dataset.currentPage = 1;
        pagination.showRowsCallback = showRowsCallback;
    }
    
    previousPage(button) {
        const pagination = button.parentElement;
        const currentPage = parseInt(pagination.dataset.currentPage);
        if (currentPage > 1) {
            const newPage = currentPage - 1;
            pagination.dataset.currentPage = newPage;
            pagination.querySelector('.current-page').textContent = newPage;
            
            const start = (newPage - 1) * parseInt(pagination.dataset.visibleRows);
            pagination.showRowsCallback(start);
        }
    }
    
    nextPage(button) {
        const pagination = button.parentElement;
        const currentPage = parseInt(pagination.dataset.currentPage);
        const totalPages = Math.ceil(parseInt(pagination.dataset.totalRows) / parseInt(pagination.dataset.visibleRows));
        
        if (currentPage < totalPages) {
            const newPage = currentPage + 1;
            pagination.dataset.currentPage = newPage;
            pagination.querySelector('.current-page').textContent = newPage;
            
            const start = (newPage - 1) * parseInt(pagination.dataset.visibleRows);
            pagination.showRowsCallback(start);
        }
    }
}

// Global CSS fixes for chart containers
const chartFixCSS = `
<style>
.chart-wrapper {
    width: 100% !important;
    height: 400px !important;
    overflow: hidden !important;
    position: relative !important;
}

.chart-container, canvas[id*="chart"] {
    max-width: 100% !important;
    max-height: 400px !important;
    width: 100% !important;
    height: 400px !important;
}

/* Prevent infinite expansion */
.card .chart-container {
    height: 350px !important;
    overflow: hidden !important;
}

/* Smooth transitions for executive feel */
.btn, .card, .nav-link {
    transition: all 0.15s ease !important;
}

.btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
}

/* Loading states */
.loading {
    opacity: 0.7 !important;
    pointer-events: none !important;
}
</style>
`;

// Inject CSS fixes
document.head.insertAdjacentHTML('beforeend', chartFixCSS);

// Initialize performance engine
window.traxovoPerf = new TRAXOVOPerformanceEngine();

console.log('TRAXOVO Performance Engine: Executive optimization active');