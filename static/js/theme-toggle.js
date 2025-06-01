
// Advanced Theme Toggle for TRAXOVO
class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme() || this.getPreferredTheme();
        this.initTheme();
        this.setupToggle();
        this.watchSystemTheme();
    }

    getStoredTheme() {
        return localStorage.getItem('traxovo-theme');
    }

    getPreferredTheme() {
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    setTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('traxovo-theme', theme);
        
        // Update theme toggle button
        this.updateToggleButton();
        
        // Dispatch theme change event
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: theme }));
        
        // Update charts and other components
        this.updateComponents();
    }

    initTheme() {
        this.setTheme(this.currentTheme);
    }

    setupToggle() {
        // Create theme toggle button
        const toggleHTML = `
            <div class="theme-toggle-container">
                <button class="btn btn-outline-secondary btn-sm theme-toggle" 
                        id="themeToggle" 
                        title="Toggle theme">
                    <i class="fas fa-moon" id="themeIcon"></i>
                </button>
            </div>
        `;
        
        // Add to navbar
        const navbar = document.querySelector('.navbar-nav');
        if (navbar) {
            navbar.insertAdjacentHTML('beforeend', toggleHTML);
        }

        // Add event listener
        const toggleBtn = document.getElementById('themeToggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleTheme());
        }
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
        
        // Add smooth transition
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    updateToggleButton() {
        const icon = document.getElementById('themeIcon');
        const button = document.getElementById('themeToggle');
        
        if (icon && button) {
            if (this.currentTheme === 'dark') {
                icon.className = 'fas fa-sun';
                button.title = 'Switch to light mode';
            } else {
                icon.className = 'fas fa-moon';
                button.title = 'Switch to dark mode';
            }
        }
    }

    watchSystemTheme() {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addListener((e) => {
            if (!this.getStoredTheme()) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    updateComponents() {
        // Update Chart.js charts if they exist
        if (window.Chart && window.Chart.instances) {
            Object.values(window.Chart.instances).forEach(chart => {
                if (chart && chart.options) {
                    this.updateChartTheme(chart);
                }
            });
        }

        // Update map theme if it exists
        if (window.mapInstance) {
            this.updateMapTheme();
        }
    }

    updateChartTheme(chart) {
        const isDark = this.currentTheme === 'dark';
        const textColor = isDark ? '#e9ecef' : '#495057';
        const gridColor = isDark ? '#495057' : '#dee2e6';

        if (chart.options.plugins && chart.options.plugins.legend) {
            chart.options.plugins.legend.labels.color = textColor;
        }

        if (chart.options.scales) {
            Object.values(chart.options.scales).forEach(scale => {
                if (scale.ticks) scale.ticks.color = textColor;
                if (scale.grid) scale.grid.color = gridColor;
            });
        }

        chart.update('none');
    }

    updateMapTheme() {
        // Update map theme based on current theme
        const isDark = this.currentTheme === 'dark';
        if (window.mapInstance && window.mapInstance.setStyle) {
            const style = isDark ? 'mapbox://styles/mapbox/dark-v10' : 'mapbox://styles/mapbox/light-v10';
            window.mapInstance.setStyle(style);
        }
    }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// CSS for theme toggle
const themeToggleCSS = `
.theme-toggle-container {
    display: flex;
    align-items: center;
    margin-left: 8px;
}

.theme-toggle {
    border-radius: 50%;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    border: 1px solid var(--bs-border-color);
}

.theme-toggle:hover {
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.theme-toggle i {
    font-size: 14px;
    transition: transform 0.3s ease;
}

.theme-toggle:hover i {
    transform: rotate(15deg);
}

@media (max-width: 768px) {
    .theme-toggle {
        width: 32px;
        height: 32px;
    }
    
    .theme-toggle i {
        font-size: 12px;
    }
}
`;

// Add CSS to document
const style = document.createElement('style');
style.textContent = themeToggleCSS;
document.head.appendChild(style);
