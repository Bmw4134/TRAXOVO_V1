/**
 * QQ AI-Powered Accessibility Enhancer JavaScript
 * Interactive accessibility features and real-time enhancements
 */

class AccessibilityEnhancer {
    constructor() {
        this.isEnabled = false;
        this.currentEnhancements = new Set();
        this.keyboardShortcuts = {
            'Alt+KeyA': () => this.toggleAccessibilityToolbar(),
            'Alt+KeyC': () => this.toggleHighContrast(),
            'Alt+KeyF': () => this.increaseFontSize(),
            'Alt+KeyK': () => this.enableKeyboardNavigation(),
            'Alt+KeyH': () => this.focusMainHeading(),
            'Alt+KeyM': () => this.focusMainContent(),
            'Alt+KeyN': () => this.focusNavigation()
        };
        this.init();
    }

    init() {
        this.createAccessibilityToolbar();
        this.setupKeyboardShortcuts();
        this.addSkipLinks();
        this.enhanceImages();
        this.addLiveRegions();
        this.monitorFocusTraps();
        this.checkInitialState();
        console.log('QQ AI Accessibility Enhancer: Initialized');
    }

    createAccessibilityToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'accessibility-toolbar';
        toolbar.id = 'accessibility-toolbar';
        toolbar.setAttribute('role', 'toolbar');
        toolbar.setAttribute('aria-label', 'Accessibility enhancement tools');
        
        toolbar.innerHTML = `
            <div class="accessibility-toolbar-header">
                <span>Accessibility Tools</span>
                <button id="accessibility-close" aria-label="Close accessibility toolbar">×</button>
            </div>
            <div class="accessibility-toolbar-controls">
                <button id="toggle-contrast" data-enhancement="contrast" aria-pressed="false">
                    High Contrast
                </button>
                <button id="toggle-font-size" data-enhancement="font-size" aria-pressed="false">
                    Large Text
                </button>
                <button id="toggle-keyboard-nav" data-enhancement="keyboard" aria-pressed="false">
                    Keyboard Nav
                </button>
                <button id="toggle-screen-reader" data-enhancement="screen-reader" aria-pressed="false">
                    Screen Reader
                </button>
                <button id="toggle-motion" data-enhancement="motion" aria-pressed="false">
                    Reduce Motion
                </button>
                <button id="analyze-page" aria-label="Analyze page accessibility">
                    Analyze Page
                </button>
            </div>
        `;
        
        document.body.appendChild(toolbar);
        this.bindToolbarEvents();
    }

    bindToolbarEvents() {
        const toolbar = document.getElementById('accessibility-toolbar');
        
        // Close button
        document.getElementById('accessibility-close').addEventListener('click', () => {
            this.hideAccessibilityToolbar();
        });

        // Enhancement toggles
        toolbar.querySelectorAll('[data-enhancement]').forEach(button => {
            button.addEventListener('click', (e) => {
                const enhancement = e.target.dataset.enhancement;
                this.toggleEnhancement(enhancement);
                this.updateButtonState(e.target);
            });
        });

        // Analyze page button
        document.getElementById('analyze-page').addEventListener('click', () => {
            this.analyzePageAccessibility();
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            const shortcut = `${e.altKey ? 'Alt+' : ''}${e.ctrlKey ? 'Ctrl+' : ''}${e.code}`;
            
            if (this.keyboardShortcuts[shortcut]) {
                e.preventDefault();
                this.keyboardShortcuts[shortcut]();
                this.announceToScreenReader(`Activated ${shortcut} shortcut`);
            }
        });

        // Add keyboard shortcut help
        this.addShortcutHelp();
    }

    addSkipLinks() {
        const skipLinks = document.createElement('div');
        skipLinks.className = 'accessibility-skip-links';
        skipLinks.innerHTML = `
            <a href="#main-content" class="accessibility-skip-link">Skip to main content</a>
            <a href="#navigation" class="accessibility-skip-link">Skip to navigation</a>
            <a href="#footer" class="accessibility-skip-link">Skip to footer</a>
        `;
        
        document.body.insertBefore(skipLinks, document.body.firstChild);
    }

    enhanceImages() {
        document.querySelectorAll('img').forEach(img => {
            if (!img.alt && !img.getAttribute('aria-label')) {
                // Generate AI-powered alt text
                this.generateAltText(img);
            }
            
            // Add loading indicators for screen readers
            if (img.loading === 'lazy') {
                img.setAttribute('aria-label', `${img.alt || 'Image'} (loading)`);
                img.addEventListener('load', () => {
                    img.setAttribute('aria-label', img.alt || 'Image');
                });
            }
        });
    }

    generateAltText(img) {
        // Simulate AI-generated alt text based on context
        const context = this.getImageContext(img);
        let altText = '';

        if (context.isChart) {
            altText = 'Chart or graph displaying data visualization';
        } else if (context.isMap) {
            altText = 'Interactive map showing location data';
        } else if (context.isEquipment) {
            altText = 'Construction equipment or machinery';
        } else if (context.isLogo) {
            altText = 'Company or application logo';
        } else {
            altText = 'Image content';
        }

        img.alt = altText;
        img.setAttribute('data-ai-generated-alt', 'true');
    }

    getImageContext(img) {
        const src = img.src.toLowerCase();
        const className = img.className.toLowerCase();
        const parentText = img.parentElement?.textContent?.toLowerCase() || '';

        return {
            isChart: src.includes('chart') || className.includes('chart') || parentText.includes('chart'),
            isMap: src.includes('map') || className.includes('map') || parentText.includes('map'),
            isEquipment: src.includes('equipment') || className.includes('equipment') || parentText.includes('equipment'),
            isLogo: src.includes('logo') || className.includes('logo') || parentText.includes('logo')
        };
    }

    addLiveRegions() {
        // Create ARIA live regions for dynamic content updates
        const liveRegions = document.createElement('div');
        liveRegions.innerHTML = `
            <div id="accessibility-announcements" aria-live="polite" aria-atomic="true" class="accessibility-live-region"></div>
            <div id="accessibility-alerts" aria-live="assertive" aria-atomic="true" class="accessibility-live-region"></div>
        `;
        
        document.body.appendChild(liveRegions);
    }

    toggleEnhancement(type) {
        const body = document.body;
        
        switch (type) {
            case 'contrast':
                body.classList.toggle('accessibility-high-contrast');
                this.currentEnhancements.has('contrast') 
                    ? this.currentEnhancements.delete('contrast')
                    : this.currentEnhancements.add('contrast');
                this.announceToScreenReader('High contrast mode toggled');
                break;
                
            case 'font-size':
                if (body.classList.contains('accessibility-font-large')) {
                    body.classList.remove('accessibility-font-large');
                    body.classList.add('accessibility-font-xlarge');
                } else if (body.classList.contains('accessibility-font-xlarge')) {
                    body.classList.remove('accessibility-font-xlarge');
                    body.classList.add('accessibility-font-xxlarge');
                } else if (body.classList.contains('accessibility-font-xxlarge')) {
                    body.classList.remove('accessibility-font-xxlarge');
                } else {
                    body.classList.add('accessibility-font-large');
                }
                this.announceToScreenReader('Font size adjusted');
                break;
                
            case 'keyboard':
                body.classList.toggle('accessibility-keyboard-nav');
                body.classList.toggle('accessibility-enhanced');
                this.enhanceKeyboardNavigation();
                this.announceToScreenReader('Keyboard navigation enhanced');
                break;
                
            case 'screen-reader':
                this.enhanceForScreenReaders();
                this.announceToScreenReader('Screen reader enhancements applied');
                break;
                
            case 'motion':
                body.classList.toggle('accessibility-motion-reduced');
                this.announceToScreenReader('Motion reduced');
                break;
        }
        
        this.saveUserPreferences();
    }

    enhanceKeyboardNavigation() {
        // Add tab indexes to interactive elements
        document.querySelectorAll('button, a, input, select, textarea, [onclick]').forEach((element, index) => {
            if (!element.hasAttribute('tabindex')) {
                element.setAttribute('tabindex', '0');
            }
        });

        // Enhance focus management
        this.manageFocusTraps();
        this.addFocusIndicators();
    }

    enhanceForScreenReaders() {
        // Add missing ARIA labels
        document.querySelectorAll('button, input, select').forEach(element => {
            if (!element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')) {
                const label = this.generateAriaLabel(element);
                if (label) {
                    element.setAttribute('aria-label', label);
                }
            }
        });

        // Add landmarks
        this.addLandmarks();
        
        // Enhance table accessibility
        this.enhanceTableAccessibility();
    }

    generateAriaLabel(element) {
        const tagName = element.tagName.toLowerCase();
        const type = element.type;
        const className = element.className;
        const text = element.textContent?.trim();

        if (tagName === 'button') {
            return text || 'Button';
        } else if (tagName === 'input') {
            return `${type} input`;
        } else if (tagName === 'select') {
            return 'Select dropdown';
        }

        return null;
    }

    addLandmarks() {
        // Add main landmark
        const mainContent = document.querySelector('main') || document.querySelector('.main-content') || document.querySelector('#main');
        if (mainContent && !mainContent.getAttribute('role')) {
            mainContent.setAttribute('role', 'main');
            mainContent.id = 'main-content';
        }

        // Add navigation landmark
        const nav = document.querySelector('nav') || document.querySelector('.navbar');
        if (nav && !nav.getAttribute('role')) {
            nav.setAttribute('role', 'navigation');
            nav.id = 'navigation';
        }
    }

    enhanceTableAccessibility() {
        document.querySelectorAll('table').forEach(table => {
            if (!table.querySelector('caption')) {
                const caption = document.createElement('caption');
                caption.textContent = 'Data table';
                table.insertBefore(caption, table.firstChild);
            }

            // Add scope attributes to headers
            table.querySelectorAll('th').forEach(th => {
                if (!th.getAttribute('scope')) {
                    th.setAttribute('scope', 'col');
                }
            });
        });
    }

    manageFocusTraps() {
        // Implement focus trap for modals
        document.querySelectorAll('.modal, .dialog').forEach(modal => {
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length > 0) {
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
                modal.addEventListener('keydown', (e) => {
                    if (e.key === 'Tab') {
                        if (e.shiftKey && document.activeElement === firstElement) {
                            e.preventDefault();
                            lastElement.focus();
                        } else if (!e.shiftKey && document.activeElement === lastElement) {
                            e.preventDefault();
                            firstElement.focus();
                        }
                    }
                });
            }
        });
    }

    addFocusIndicators() {
        document.querySelectorAll('*:focus').forEach(element => {
            element.style.outline = '3px solid #2563eb';
            element.style.outlineOffset = '2px';
        });
    }

    monitorFocusTraps() {
        // Monitor for focus traps and escape routes
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal.show, .dialog[open]');
                if (activeModal) {
                    this.closeModal(activeModal);
                }
            }
        });
    }

    closeModal(modal) {
        modal.style.display = 'none';
        modal.removeAttribute('open');
        modal.classList.remove('show');
        
        // Return focus to trigger element
        const trigger = modal.getAttribute('data-trigger');
        if (trigger) {
            document.getElementById(trigger)?.focus();
        }
    }

    analyzePageAccessibility() {
        this.announceToScreenReader('Analyzing page accessibility...');
        
        // Collect page HTML for analysis
        const pageHtml = document.documentElement.outerHTML;
        const pageUrl = window.location.href;
        
        // Send to backend for AI analysis
        fetch('/api/analyze-accessibility', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                html: pageHtml,
                url: pageUrl
            })
        })
        .then(response => response.json())
        .then(data => {
            this.displayAccessibilityResults(data);
            this.announceToScreenReader(`Analysis complete. Found ${data.issues?.length || 0} accessibility issues.`);
        })
        .catch(error => {
            console.error('Accessibility analysis error:', error);
            this.announceToScreenReader('Analysis failed. Please try again.');
        });
    }

    displayAccessibilityResults(results) {
        const resultsPanel = this.createResultsPanel();
        resultsPanel.innerHTML = `
            <div class="accessibility-results">
                <h3>Accessibility Analysis Results</h3>
                <div class="accessibility-score">
                    <span class="score-value">${results.accessibility_score || 0}</span>
                    <span class="score-label">Accessibility Score</span>
                </div>
                <div class="issues-summary">
                    <h4>Issues Found: ${results.issues?.length || 0}</h4>
                    ${this.renderIssuesList(results.issues || [])}
                </div>
                <div class="enhancement-suggestions">
                    <h4>AI Enhancement Suggestions</h4>
                    ${this.renderSuggestions(results.enhancement_suggestions || [])}
                </div>
                <div class="auto-fix-section">
                    <button id="apply-auto-fixes" ${results.auto_fixes_available ? '' : 'disabled'}>
                        Apply ${results.auto_fixes_available || 0} Auto-Fixes
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(resultsPanel);
        this.bindResultsEvents(resultsPanel);
    }

    createResultsPanel() {
        const panel = document.createElement('div');
        panel.className = 'accessibility-results-panel';
        panel.setAttribute('role', 'dialog');
        panel.setAttribute('aria-labelledby', 'accessibility-results-title');
        panel.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border: 2px solid #374151;
            border-radius: 8px;
            padding: 20px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            z-index: 10000;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        `;
        
        return panel;
    }

    renderIssuesList(issues) {
        return issues.map(issue => `
            <div class="accessibility-issue ${issue.severity}">
                <div class="issue-header">
                    <span class="issue-type">${issue.issue_type}</span>
                    <span class="issue-severity">${issue.severity}</span>
                </div>
                <div class="issue-description">${issue.description}</div>
                <div class="issue-suggestion">${issue.suggestion}</div>
                ${issue.can_auto_fix ? '<span class="auto-fix-badge">Auto-fixable</span>' : ''}
            </div>
        `).join('');
    }

    renderSuggestions(suggestions) {
        return suggestions.map(suggestion => `
            <div class="enhancement-suggestion">
                <div class="suggestion-header">
                    <span class="suggestion-type">${suggestion.type}</span>
                    <span class="suggestion-priority">${suggestion.priority}</span>
                </div>
                <div class="suggestion-description">${suggestion.description}</div>
                <div class="suggestion-improvement">${suggestion.estimated_improvement}</div>
            </div>
        `).join('');
    }

    bindResultsEvents(panel) {
        // Apply auto-fixes button
        const autoFixButton = panel.querySelector('#apply-auto-fixes');
        if (autoFixButton && !autoFixButton.disabled) {
            autoFixButton.addEventListener('click', () => {
                this.applyAutoFixes();
            });
        }
        
        // Close panel on escape
        panel.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeResultsPanel(panel);
            }
        });
        
        // Focus management
        panel.focus();
    }

    applyAutoFixes() {
        this.announceToScreenReader('Applying accessibility fixes...');
        
        fetch('/api/apply-accessibility-fixes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            this.announceToScreenReader(`Applied ${data.enhancements_applied || 0} accessibility enhancements.`);
            
            // Apply CSS enhancements
            if (data.enhancements) {
                this.applyCSSEnhancements(data.enhancements);
            }
            
            // Refresh the page analysis
            setTimeout(() => {
                this.analyzePageAccessibility();
            }, 1000);
        })
        .catch(error => {
            console.error('Auto-fix error:', error);
            this.announceToScreenReader('Auto-fix failed. Please try again.');
        });
    }

    applyCSSEnhancements(enhancements) {
        enhancements.forEach(enhancement => {
            if (enhancement.css_changes) {
                this.applyDynamicCSS(enhancement.css_changes);
            }
        });
    }

    applyDynamicCSS(cssChanges) {
        const style = document.createElement('style');
        style.id = 'accessibility-dynamic-enhancements';
        
        let css = '';
        for (const [selector, properties] of Object.entries(cssChanges)) {
            css += `${selector} {\n`;
            for (const [property, value] of Object.entries(properties)) {
                css += `  ${property}: ${value} !important;\n`;
            }
            css += '}\n';
        }
        
        style.textContent = css;
        document.head.appendChild(style);
    }

    closeResultsPanel(panel) {
        panel.remove();
        this.announceToScreenReader('Results panel closed');
    }

    toggleAccessibilityToolbar() {
        const toolbar = document.getElementById('accessibility-toolbar');
        if (toolbar.style.display === 'none') {
            this.showAccessibilityToolbar();
        } else {
            this.hideAccessibilityToolbar();
        }
    }

    showAccessibilityToolbar() {
        const toolbar = document.getElementById('accessibility-toolbar');
        toolbar.style.display = 'block';
        toolbar.focus();
        this.announceToScreenReader('Accessibility toolbar opened');
    }

    hideAccessibilityToolbar() {
        const toolbar = document.getElementById('accessibility-toolbar');
        toolbar.style.display = 'none';
        this.announceToScreenReader('Accessibility toolbar closed');
    }

    toggleHighContrast() {
        this.toggleEnhancement('contrast');
    }

    increaseFontSize() {
        this.toggleEnhancement('font-size');
    }

    enableKeyboardNavigation() {
        this.toggleEnhancement('keyboard');
    }

    focusMainHeading() {
        const heading = document.querySelector('h1');
        if (heading) {
            heading.focus();
            this.announceToScreenReader('Focused main heading');
        }
    }

    focusMainContent() {
        const main = document.querySelector('#main-content, main, .main-content');
        if (main) {
            main.focus();
            this.announceToScreenReader('Focused main content');
        }
    }

    focusNavigation() {
        const nav = document.querySelector('#navigation, nav, .navbar');
        if (nav) {
            nav.focus();
            this.announceToScreenReader('Focused navigation');
        }
    }

    updateButtonState(button) {
        const isActive = button.classList.toggle('active');
        button.setAttribute('aria-pressed', isActive.toString());
    }

    announceToScreenReader(message) {
        const announcements = document.getElementById('accessibility-announcements');
        if (announcements) {
            announcements.textContent = message;
            
            // Clear after a short delay
            setTimeout(() => {
                announcements.textContent = '';
            }, 1000);
        }
    }

    saveUserPreferences() {
        const preferences = {
            enhancements: Array.from(this.currentEnhancements),
            timestamp: Date.now()
        };
        
        localStorage.setItem('traxovo-accessibility-preferences', JSON.stringify(preferences));
    }

    loadUserPreferences() {
        const saved = localStorage.getItem('traxovo-accessibility-preferences');
        if (saved) {
            try {
                const preferences = JSON.parse(saved);
                preferences.enhancements.forEach(enhancement => {
                    this.toggleEnhancement(enhancement);
                });
            } catch (error) {
                console.error('Error loading accessibility preferences:', error);
            }
        }
    }

    checkInitialState() {
        // Check for user preferences
        this.loadUserPreferences();
        
        // Check for URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('accessibility') === 'true') {
            this.showAccessibilityToolbar();
        }
        
        // Check for reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.body.classList.add('accessibility-motion-reduced');
        }
        
        // Check for high contrast preference
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            document.body.classList.add('accessibility-high-contrast');
        }
    }

    addShortcutHelp() {
        const helpButton = document.createElement('button');
        helpButton.id = 'accessibility-help';
        helpButton.className = 'accessibility-help-button';
        helpButton.textContent = '?';
        helpButton.setAttribute('aria-label', 'Accessibility help and keyboard shortcuts');
        helpButton.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #2563eb;
            color: white;
            border: none;
            font-size: 18px;
            cursor: pointer;
            z-index: 9998;
        `;
        
        helpButton.addEventListener('click', () => {
            this.showKeyboardShortcuts();
        });
        
        document.body.appendChild(helpButton);
    }

    showKeyboardShortcuts() {
        const shortcuts = [
            { key: 'Alt+A', description: 'Open accessibility toolbar' },
            { key: 'Alt+C', description: 'Toggle high contrast' },
            { key: 'Alt+F', description: 'Increase font size' },
            { key: 'Alt+K', description: 'Enable keyboard navigation' },
            { key: 'Alt+H', description: 'Focus main heading' },
            { key: 'Alt+M', description: 'Focus main content' },
            { key: 'Alt+N', description: 'Focus navigation' }
        ];
        
        const helpPanel = document.createElement('div');
        helpPanel.className = 'accessibility-help-panel';
        helpPanel.setAttribute('role', 'dialog');
        helpPanel.setAttribute('aria-labelledby', 'shortcuts-title');
        helpPanel.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border: 2px solid #374151;
            border-radius: 8px;
            padding: 20px;
            max-width: 400px;
            z-index: 10001;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        `;
        
        helpPanel.innerHTML = `
            <h3 id="shortcuts-title">Keyboard Shortcuts</h3>
            <ul>
                ${shortcuts.map(shortcut => `
                    <li><kbd>${shortcut.key}</kbd> - ${shortcut.description}</li>
                `).join('')}
            </ul>
            <button id="close-help" style="margin-top: 15px;">Close</button>
        `;
        
        document.body.appendChild(helpPanel);
        
        // Close button
        helpPanel.querySelector('#close-help').addEventListener('click', () => {
            helpPanel.remove();
        });
        
        // Close on escape
        helpPanel.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                helpPanel.remove();
            }
        });
        
        helpPanel.focus();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.accessibilityEnhancer = new AccessibilityEnhancer();
    });
} else {
    window.accessibilityEnhancer = new AccessibilityEnhancer();
}