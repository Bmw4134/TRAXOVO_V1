/**
 * TRAXORA Theme Switcher
 * 
 * This module manages the theme switching between light and dark modes.
 * It remembers user preferences and applies appropriate Bootstrap theme classes.
 */

class ThemeSwitcher {
    constructor() {
        this.currentTheme = this.loadSavedTheme() || 'dark';
        this.init();
    }
    
    init() {
        // Apply current theme
        this.applyTheme(this.currentTheme);
        
        // Set up theme toggle button event listeners
        document.addEventListener('click', (e) => {
            if (e.target.closest('#theme-toggle')) {
                this.toggleTheme();
            }
        });
        
        // Add keyboard shortcut (Alt+T)
        document.addEventListener('keydown', (e) => {
            if (e.altKey && e.key === 't') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }
    
    // Load theme preference from localStorage
    loadSavedTheme() {
        return localStorage.getItem('traxora_theme');
    }
    
    // Save theme preference to localStorage
    saveTheme(theme) {
        localStorage.setItem('traxora_theme', theme);
    }
    
    // Toggle between light and dark themes
    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        this.saveTheme(newTheme);
        this.currentTheme = newTheme;
        
        // Show feedback
        this.showThemeToggleFeedback();
        
        // Dispatch theme change event
        document.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: newTheme }
        }));
    }
    
    // Apply the specified theme
    applyTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        
        // Update toggle button appearance
        const toggleButton = document.getElementById('theme-toggle');
        if (toggleButton) {
            if (theme === 'dark') {
                toggleButton.innerHTML = '<i class="bi bi-sun-fill"></i>';
                toggleButton.setAttribute('title', 'Switch to Light Mode');
                toggleButton.classList.remove('btn-dark');
                toggleButton.classList.add('btn-light');
            } else {
                toggleButton.innerHTML = '<i class="bi bi-moon-fill"></i>';
                toggleButton.setAttribute('title', 'Switch to Dark Mode');
                toggleButton.classList.remove('btn-light');
                toggleButton.classList.add('btn-dark');
            }
        }
    }
    
    // Show theme toggle feedback
    showThemeToggleFeedback() {
        // Check if feedback function exists
        if (typeof showFeedback === 'function') {
            const themeText = this.currentTheme === 'light' ? 'Dark' : 'Light';
            showFeedback('Theme Changed', `Switched to ${themeText} Mode`, 'info');
        }
    }
    
    // Get current theme
    getTheme() {
        return this.currentTheme;
    }
}

// Initialize the theme switcher when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Create theme toggle button if it doesn't exist
    if (!document.getElementById('theme-toggle')) {
        const navbar = document.querySelector('.navbar-nav.ms-auto');
        if (navbar) {
            const themeToggleLi = document.createElement('li');
            themeToggleLi.className = 'nav-item mx-2 d-flex align-items-center';
            
            const themeToggleBtn = document.createElement('button');
            themeToggleBtn.id = 'theme-toggle';
            themeToggleBtn.className = 'btn btn-sm btn-light rounded-circle';
            themeToggleBtn.style.width = '38px';
            themeToggleBtn.style.height = '38px';
            themeToggleBtn.innerHTML = '<i class="bi bi-sun-fill"></i>';
            themeToggleBtn.setAttribute('title', 'Switch to Light Mode');
            
            themeToggleLi.appendChild(themeToggleBtn);
            navbar.insertBefore(themeToggleLi, navbar.firstChild);
        }
    }
    
    // Initialize theme switcher
    window.themeSwitcher = new ThemeSwitcher();
});