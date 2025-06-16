
/**
 * TRAXOVO Enterprise Interaction Engine
 * Billion-dollar enterprise UI/UX interaction patterns
 */

(function() {
    'use strict';
    
    class EnterpriseInteractions {
        constructor() {
            this.init();
        }
        
        init() {
            this.addMicroInteractions();
            this.addSmartTooltips();
            this.addKeyboardShortcuts();
            this.addContextMenus();
            this.addProgressiveDisclosure();
            this.addEnterpriseAnimations();
            this.addAccessibilityEnhancements();
            
            console.log('Enterprise Interactions: Initialized');
        }
        
        addMicroInteractions() {
            // Premium button interactions
            document.addEventListener('click', (e) => {
                if (e.target.matches('.enterprise-btn, .traxovo-btn')) {
                    this.createRippleEffect(e.target, e);
                }
            });
            
            // Sophisticated hover states
            const interactiveElements = document.querySelectorAll(
                '.enterprise-card, .enterprise-metric, .metric-card, .modern-card'
            );
            
            interactiveElements.forEach(element => {
                element.addEventListener('mouseenter', () => {
                    element.style.transform = 'translateY(-4px) scale(1.02)';
                    element.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                });
                
                element.addEventListener('mouseleave', () => {
                    element.style.transform = 'translateY(0) scale(1)';
                });
            });
        }
        
        createRippleEffect(element, event) {
            const ripple = document.createElement('div');
            const rect = element.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = event.clientX - rect.left - size / 2;
            const y = event.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple-effect 0.6s linear;
                pointer-events: none;
                z-index: 1000;
            `;
            
            element.style.position = 'relative';
            element.style.overflow = 'hidden';
            element.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        }
        
        addSmartTooltips() {
            // Create tooltip container
            const tooltipContainer = document.createElement('div');
            tooltipContainer.id = 'enterprise-tooltip-container';
            tooltipContainer.style.cssText = `
                position: absolute;
                z-index: 10000;
                pointer-events: none;
                background: #1f2937;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                opacity: 0;
                transition: opacity 0.2s ease;
                max-width: 200px;
                word-wrap: break-word;
            `;
            document.body.appendChild(tooltipContainer);
            
            // Add tooltips to elements with data-tooltip
            document.addEventListener('mouseenter', (e) => {
                const tooltip = e.target.getAttribute('data-tooltip') || 
                               e.target.getAttribute('title') ||
                               e.target.getAttribute('aria-label');
                
                if (tooltip && e.target.matches('.enterprise-btn, .metric-card, [data-tooltip]')) {
                    this.showTooltip(e.target, tooltip);
                }
            }, true);
            
            document.addEventListener('mouseleave', (e) => {
                if (e.target.hasAttribute('data-tooltip') || e.target.hasAttribute('title')) {
                    this.hideTooltip();
                }
            }, true);
        }
        
        showTooltip(element, text) {
            const container = document.getElementById('enterprise-tooltip-container');
            const rect = element.getBoundingClientRect();
            
            container.textContent = text;
            container.style.left = rect.left + (rect.width / 2) + 'px';
            container.style.top = rect.top - 40 + 'px';
            container.style.transform = 'translateX(-50%)';
            container.style.opacity = '1';
        }
        
        hideTooltip() {
            const container = document.getElementById('enterprise-tooltip-container');
            container.style.opacity = '0';
        }
        
        addKeyboardShortcuts() {
            const shortcuts = {
                'Escape': () => this.closeAllModals(),
                'ctrl+k': (e) => {
                    e.preventDefault();
                    this.openCommandPalette();
                },
                'ctrl+/': (e) => {
                    e.preventDefault();
                    this.showShortcutsModal();
                },
                'alt+d': (e) => {
                    e.preventDefault();
                    this.focusDashboard();
                }
            };
            
            document.addEventListener('keydown', (e) => {
                const key = e.ctrlKey ? `ctrl+${e.key.toLowerCase()}` : 
                           e.altKey ? `alt+${e.key.toLowerCase()}` : e.key;
                
                if (shortcuts[key]) {
                    shortcuts[key](e);
                }
            });
        }
        
        addContextMenus() {
            document.addEventListener('contextmenu', (e) => {
                if (e.target.matches('.enterprise-card, .metric-card')) {
                    e.preventDefault();
                    this.showContextMenu(e);
                }
            });
            
            document.addEventListener('click', () => {
                this.hideContextMenu();
            });
        }
        
        showContextMenu(event) {
            this.hideContextMenu();
            
            const menu = document.createElement('div');
            menu.id = 'enterprise-context-menu';
            menu.style.cssText = `
                position: fixed;
                left: ${event.clientX}px;
                top: ${event.clientY}px;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                z-index: 10000;
                min-width: 160px;
                animation: fadeIn 0.15s ease;
            `;
            
            const menuItems = [
                { label: 'View Details', action: () => console.log('View Details') },
                { label: 'Export Data', action: () => console.log('Export Data') },
                { label: 'Share', action: () => console.log('Share') },
                { label: 'Refresh', action: () => location.reload() }
            ];
            
            menuItems.forEach(item => {
                const menuItem = document.createElement('div');
                menuItem.textContent = item.label;
                menuItem.style.cssText = `
                    padding: 8px 16px;
                    cursor: pointer;
                    font-size: 14px;
                    border-bottom: 1px solid #f3f4f6;
                `;
                
                menuItem.addEventListener('mouseenter', () => {
                    menuItem.style.backgroundColor = '#f9fafb';
                });
                
                menuItem.addEventListener('mouseleave', () => {
                    menuItem.style.backgroundColor = 'transparent';
                });
                
                menuItem.addEventListener('click', () => {
                    item.action();
                    this.hideContextMenu();
                });
                
                menu.appendChild(menuItem);
            });
            
            document.body.appendChild(menu);
        }
        
        hideContextMenu() {
            const menu = document.getElementById('enterprise-context-menu');
            if (menu) menu.remove();
        }
        
        addProgressiveDisclosure() {
            // Collapsible sections
            document.addEventListener('click', (e) => {
                if (e.target.matches('[data-toggle="collapse"]')) {
                    const targetId = e.target.getAttribute('data-target');
                    const target = document.querySelector(targetId);
                    
                    if (target) {
                        const isExpanded = target.style.maxHeight;
                        
                        if (isExpanded) {
                            target.style.maxHeight = null;
                            target.style.opacity = '0';
                            e.target.setAttribute('aria-expanded', 'false');
                        } else {
                            target.style.maxHeight = target.scrollHeight + 'px';
                            target.style.opacity = '1';
                            e.target.setAttribute('aria-expanded', 'true');
                        }
                    }
                }
            });
        }
        
        addEnterpriseAnimations() {
            // Staggered animations for lists
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry, index) => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            entry.target.style.opacity = '1';
                            entry.target.style.transform = 'translateY(0)';
                        }, index * 100);
                    }
                });
            }, observerOptions);
            
            // Observe cards and metrics
            const animatedElements = document.querySelectorAll(
                '.enterprise-card, .enterprise-metric, .metric-card'
            );
            
            animatedElements.forEach(element => {
                element.style.opacity = '0';
                element.style.transform = 'translateY(20px)';
                element.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                observer.observe(element);
            });
        }
        
        addAccessibilityEnhancements() {
            // Focus management
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    document.body.classList.add('keyboard-navigation');
                }
            });
            
            document.addEventListener('mousedown', () => {
                document.body.classList.remove('keyboard-navigation');
            });
            
            // Screen reader announcements
            this.createLiveRegion();
        }
        
        createLiveRegion() {
            const liveRegion = document.createElement('div');
            liveRegion.id = 'enterprise-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.style.cssText = `
                position: absolute;
                left: -10000px;
                width: 1px;
                height: 1px;
                overflow: hidden;
            `;
            document.body.appendChild(liveRegion);
        }
        
        announce(message) {
            const liveRegion = document.getElementById('enterprise-live-region');
            if (liveRegion) {
                liveRegion.textContent = message;
            }
        }
        
        // Modal management
        closeAllModals() {
            const modals = document.querySelectorAll('.enterprise-modal-overlay, .modal');
            modals.forEach(modal => {
                modal.style.opacity = '0';
                setTimeout(() => modal.remove(), 200);
            });
        }
        
        openCommandPalette() {
            // Implementation for command palette would go here
            this.announce('Command palette opened');
        }
        
        showShortcutsModal() {
            // Implementation for shortcuts modal would go here
            this.announce('Keyboard shortcuts displayed');
        }
        
        focusDashboard() {
            const dashboard = document.querySelector('[role="main"], .dashboard, main');
            if (dashboard) {
                dashboard.focus();
                this.announce('Dashboard focused');
            }
        }
    }
    
    // Add required CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple-effect {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .keyboard-navigation *:focus {
            outline: 2px solid #0070f3 !important;
            outline-offset: 2px !important;
        }
    `;
    document.head.appendChild(style);
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            new EnterpriseInteractions();
        });
    } else {
        new EnterpriseInteractions();
    }
    
    // Export for external access
    window.EnterpriseInteractions = EnterpriseInteractions;
    
})();
