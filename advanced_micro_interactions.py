"""
Advanced Micro-Interaction Feedback Animations
Provides comprehensive interactive feedback for all user interactions
"""

class MicroInteractionSystem:
    """
    Advanced micro-interaction system for enhanced user experience
    """
    
    def __init__(self):
        self.animation_styles = self._generate_animation_styles()
        self.interaction_scripts = self._generate_interaction_scripts()
        self.feedback_system = self._generate_feedback_system()
    
    def _generate_animation_styles(self):
        """Generate comprehensive CSS animations for micro-interactions"""
        return """
        /* Advanced Micro-Interaction Animations */
        @keyframes ripple {
            0% {
                transform: scale(0);
                opacity: 1;
            }
            100% {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        @keyframes pulse {
            0%, 100% {
                transform: scale(1);
            }
            50% {
                transform: scale(1.05);
            }
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {
                transform: translateY(0);
            }
            40% {
                transform: translateY(-10px);
            }
            60% {
                transform: translateY(-5px);
            }
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(-100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes fadeInUp {
            from {
                transform: translateY(30px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        @keyframes shimmer {
            0% {
                background-position: -468px 0;
            }
            100% {
                background-position: 468px 0;
            }
        }
        
        @keyframes glow {
            0%, 100% {
                box-shadow: 0 0 5px rgba(0, 255, 100, 0.3);
            }
            50% {
                box-shadow: 0 0 20px rgba(0, 255, 100, 0.6);
            }
        }
        
        /* Interactive Elements */
        .interactive-element {
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
        }
        
        .interactive-element:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 255, 100, 0.15);
        }
        
        .interactive-element:active {
            transform: translateY(0);
            transition: transform 0.1s;
        }
        
        /* Ripple Effect */
        .ripple-container {
            position: relative;
            overflow: hidden;
        }
        
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(0, 255, 100, 0.3);
            pointer-events: none;
            animation: ripple 0.6s linear;
        }
        
        /* Button Micro-Interactions */
        .micro-btn {
            position: relative;
            background: linear-gradient(45deg, #00ff64, #00ccff);
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            color: #000;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            overflow: hidden;
        }
        
        .micro-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }
        
        .micro-btn:hover::before {
            left: 100%;
        }
        
        .micro-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 255, 100, 0.3);
        }
        
        .micro-btn:active {
            transform: scale(0.98);
            transition: transform 0.1s;
        }
        
        /* Card Interactions */
        .interactive-card {
            background: rgba(26, 26, 46, 0.8);
            border: 1px solid rgba(0, 255, 100, 0.2);
            border-radius: 15px;
            padding: 20px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .interactive-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 30%, rgba(0, 255, 100, 0.1) 50%, transparent 70%);
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .interactive-card:hover::before {
            opacity: 1;
        }
        
        .interactive-card:hover {
            transform: translateY(-5px);
            border-color: rgba(0, 255, 100, 0.5);
            box-shadow: 0 15px 35px rgba(0, 255, 100, 0.1);
        }
        
        /* Loading States */
        .loading-shimmer {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: shimmer 2s infinite;
        }
        
        .loading-pulse {
            animation: pulse 2s infinite;
        }
        
        /* Notification Animations */
        .notification-slide {
            animation: slideIn 0.5s ease-out;
        }
        
        .notification-bounce {
            animation: bounce 1s;
        }
        
        /* Progress Indicators */
        .progress-glow {
            animation: glow 2s infinite;
        }
        
        /* Form Element Interactions */
        .interactive-input {
            border: 2px solid rgba(0, 255, 100, 0.3);
            border-radius: 8px;
            padding: 12px;
            background: rgba(42, 42, 78, 0.8);
            color: white;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .interactive-input:focus {
            border-color: #00ff64;
            box-shadow: 0 0 15px rgba(0, 255, 100, 0.3);
            outline: none;
        }
        
        .interactive-input:focus::placeholder {
            transform: translateY(-20px);
            font-size: 12px;
            color: #00ff64;
        }
        
        /* Navigation Micro-Interactions */
        .nav-item-micro {
            position: relative;
            padding: 12px 20px;
            border-radius: 8px;
            transition: all 0.3s ease;
            overflow: hidden;
        }
        
        .nav-item-micro::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            width: 0;
            height: 3px;
            background: #00ff64;
            transition: all 0.3s ease;
            transform: translateX(-50%);
        }
        
        .nav-item-micro:hover::after {
            width: 100%;
        }
        
        .nav-item-micro:hover {
            background: rgba(0, 255, 100, 0.1);
            transform: translateX(5px);
        }
        
        /* Icon Animations */
        .icon-bounce:hover {
            animation: bounce 0.6s;
        }
        
        .icon-pulse:hover {
            animation: pulse 1s;
        }
        
        /* Status Indicators */
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online {
            background: #00ff64;
            animation: pulse 2s infinite;
        }
        
        .status-offline {
            background: #ff4444;
        }
        
        .status-warning {
            background: #ffaa00;
            animation: glow 1.5s infinite;
        }
        
        /* Chart Interactions */
        .chart-container {
            transition: transform 0.3s ease;
        }
        
        .chart-container:hover {
            transform: scale(1.02);
        }
        
        /* Advanced Hover States */
        .hover-lift {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .hover-lift:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        
        .hover-glow:hover {
            box-shadow: 0 0 30px rgba(0, 255, 100, 0.4);
        }
        
        .hover-scale:hover {
            transform: scale(1.05);
        }
        
        /* Entrance Animations */
        .fade-in-up {
            animation: fadeInUp 0.6s ease-out;
        }
        
        .slide-in {
            animation: slideIn 0.5s ease-out;
        }
        
        /* Mobile Optimizations */
        @media (max-width: 768px) {
            .interactive-element:hover {
                transform: none;
            }
            
            .interactive-card:hover {
                transform: none;
            }
            
            .hover-lift:hover {
                transform: none;
            }
        }
        """
    
    def _generate_interaction_scripts(self):
        """Generate JavaScript for micro-interactions"""
        return """
        // Advanced Micro-Interaction System
        class MicroInteractionManager {
            constructor() {
                this.initializeRippleEffect();
                this.initializeHoverEffects();
                this.initializeClickFeedback();
                this.initializeFormInteractions();
                this.initializeLoadingStates();
                this.initializeNotifications();
            }
            
            initializeRippleEffect() {
                document.addEventListener('click', (e) => {
                    const element = e.target.closest('.ripple-container');
                    if (!element) return;
                    
                    const ripple = document.createElement('span');
                    const rect = element.getBoundingClientRect();
                    const size = Math.max(rect.width, rect.height);
                    const x = e.clientX - rect.left - size / 2;
                    const y = e.clientY - rect.top - size / 2;
                    
                    ripple.style.width = ripple.style.height = size + 'px';
                    ripple.style.left = x + 'px';
                    ripple.style.top = y + 'px';
                    ripple.classList.add('ripple');
                    
                    element.appendChild(ripple);
                    
                    setTimeout(() => {
                        ripple.remove();
                    }, 600);
                });
            }
            
            initializeHoverEffects() {
                const interactiveElements = document.querySelectorAll('.interactive-element');
                
                interactiveElements.forEach(element => {
                    element.addEventListener('mouseenter', () => {
                        element.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                    });
                    
                    element.addEventListener('mouseleave', () => {
                        element.style.transform = '';
                        element.style.boxShadow = '';
                    });
                });
            }
            
            initializeClickFeedback() {
                const clickableElements = document.querySelectorAll('button, .btn, .clickable');
                
                clickableElements.forEach(element => {
                    element.addEventListener('mousedown', () => {
                        element.style.transform = 'scale(0.98)';
                        element.style.transition = 'transform 0.1s';
                    });
                    
                    element.addEventListener('mouseup', () => {
                        element.style.transform = '';
                        element.style.transition = 'transform 0.3s';
                    });
                    
                    element.addEventListener('mouseleave', () => {
                        element.style.transform = '';
                    });
                });
            }
            
            initializeFormInteractions() {
                const inputs = document.querySelectorAll('input, textarea');
                
                inputs.forEach(input => {
                    input.addEventListener('focus', () => {
                        input.parentElement?.classList.add('focused');
                        this.createFocusRing(input);
                    });
                    
                    input.addEventListener('blur', () => {
                        input.parentElement?.classList.remove('focused');
                        this.removeFocusRing(input);
                    });
                });
            }
            
            createFocusRing(element) {
                const ring = document.createElement('div');
                ring.classList.add('focus-ring');
                ring.style.cssText = `
                    position: absolute;
                    top: -3px;
                    left: -3px;
                    right: -3px;
                    bottom: -3px;
                    border: 2px solid #00ff64;
                    border-radius: 8px;
                    pointer-events: none;
                    animation: pulse 2s infinite;
                `;
                
                element.style.position = 'relative';
                element.parentElement.appendChild(ring);
            }
            
            removeFocusRing(element) {
                const ring = element.parentElement?.querySelector('.focus-ring');
                if (ring) {
                    ring.remove();
                }
            }
            
            initializeLoadingStates() {
                const loadingElements = document.querySelectorAll('.loading');
                
                loadingElements.forEach(element => {
                    element.classList.add('loading-shimmer');
                });
            }
            
            initializeNotifications() {
                const notifications = document.querySelectorAll('.notification');
                
                notifications.forEach(notification => {
                    notification.classList.add('notification-slide');
                    
                    setTimeout(() => {
                        notification.classList.add('notification-bounce');
                    }, 500);
                });
            }
            
            // Utility methods for dynamic interactions
            addRippleEffect(element) {
                element.classList.add('ripple-container');
            }
            
            addHoverEffect(element, type = 'lift') {
                element.classList.add(`hover-${type}`);
            }
            
            addEntranceAnimation(element, type = 'fadeInUp') {
                element.classList.add(type);
            }
            
            showNotification(message, type = 'success') {
                const notification = document.createElement('div');
                notification.className = `notification notification-${type} notification-slide`;
                notification.textContent = message;
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: ${type === 'success' ? '#00ff64' : '#ff4444'};
                    color: ${type === 'success' ? '#000' : '#fff'};
                    padding: 15px 20px;
                    border-radius: 8px;
                    z-index: 10000;
                    animation: slideIn 0.5s ease-out;
                `;
                
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.remove();
                }, 3000);
            }
            
            addLoadingState(element) {
                element.classList.add('loading-shimmer');
                element.style.pointerEvents = 'none';
            }
            
            removeLoadingState(element) {
                element.classList.remove('loading-shimmer');
                element.style.pointerEvents = '';
            }
            
            animateCounter(element, targetValue, duration = 2000) {
                const startValue = 0;
                const increment = targetValue / (duration / 16);
                let currentValue = startValue;
                
                const counter = setInterval(() => {
                    currentValue += increment;
                    element.textContent = Math.floor(currentValue);
                    
                    if (currentValue >= targetValue) {
                        element.textContent = targetValue;
                        clearInterval(counter);
                    }
                }, 16);
            }
            
            createProgressBar(container, progress) {
                const progressBar = document.createElement('div');
                progressBar.style.cssText = `
                    width: 100%;
                    height: 6px;
                    background: rgba(0, 255, 100, 0.2);
                    border-radius: 3px;
                    overflow: hidden;
                `;
                
                const progressFill = document.createElement('div');
                progressFill.style.cssText = `
                    height: 100%;
                    background: linear-gradient(90deg, #00ff64, #00ccff);
                    border-radius: 3px;
                    width: 0%;
                    transition: width 1s ease;
                    animation: glow 2s infinite;
                `;
                
                progressBar.appendChild(progressFill);
                container.appendChild(progressBar);
                
                setTimeout(() => {
                    progressFill.style.width = progress + '%';
                }, 100);
            }
        }
        
        // Initialize micro-interactions when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            window.microInteractions = new MicroInteractionManager();
            console.log('Advanced micro-interaction system initialized');
        });
        """
    
    def _generate_feedback_system(self):
        """Generate feedback system for user actions"""
        return """
        // Real-time Feedback System
        class FeedbackSystem {
            constructor() {
                this.initializeFeedbackSystem();
            }
            
            initializeFeedbackSystem() {
                this.setupButtonFeedback();
                this.setupFormFeedback();
                this.setupNavigationFeedback();
                this.setupSystemFeedback();
            }
            
            setupButtonFeedback() {
                document.addEventListener('click', (e) => {
                    const button = e.target.closest('button, .btn');
                    if (!button) return;
                    
                    this.showButtonFeedback(button);
                });
            }
            
            showButtonFeedback(button) {
                const feedback = document.createElement('span');
                feedback.textContent = '✓';
                feedback.style.cssText = `
                    position: absolute;
                    color: #00ff64;
                    font-size: 16px;
                    font-weight: bold;
                    pointer-events: none;
                    animation: bounce 0.6s ease-out;
                    z-index: 1000;
                `;
                
                const rect = button.getBoundingClientRect();
                feedback.style.left = (rect.right + 10) + 'px';
                feedback.style.top = (rect.top + rect.height / 2 - 8) + 'px';
                
                document.body.appendChild(feedback);
                
                setTimeout(() => {
                    feedback.remove();
                }, 600);
            }
            
            setupFormFeedback() {
                const forms = document.querySelectorAll('form');
                
                forms.forEach(form => {
                    form.addEventListener('submit', (e) => {
                        this.showFormFeedback('Form submitted successfully!', 'success');
                    });
                });
            }
            
            showFormFeedback(message, type) {
                window.microInteractions?.showNotification(message, type);
            }
            
            setupNavigationFeedback() {
                const navItems = document.querySelectorAll('.nav-item, a[href]');
                
                navItems.forEach(item => {
                    item.addEventListener('click', () => {
                        this.showNavigationFeedback(item);
                    });
                });
            }
            
            showNavigationFeedback(item) {
                item.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    item.style.transform = '';
                }, 150);
            }
            
            setupSystemFeedback() {
                // Monitor system status updates
                setInterval(() => {
                    this.updateSystemStatus();
                }, 5000);
            }
            
            updateSystemStatus() {
                const statusIndicators = document.querySelectorAll('.status-indicator');
                statusIndicators.forEach(indicator => {
                    indicator.classList.add('status-online');
                });
            }
        }
        
        // Initialize feedback system
        document.addEventListener('DOMContentLoaded', () => {
            window.feedbackSystem = new FeedbackSystem();
            console.log('Real-time feedback system initialized');
        });
        """
    
    def get_complete_micro_interaction_system(self):
        """Get the complete micro-interaction system"""
        return {
            'styles': self.animation_styles,
            'scripts': self.interaction_scripts,
            'feedback': self.feedback_system
        }
    
    def enhance_template_with_micro_interactions(self, template_content):
        """Enhance existing template with micro-interaction classes"""
        # Add micro-interaction classes to common elements
        enhanced_content = template_content.replace(
            'class="btn', 'class="btn micro-btn ripple-container'
        ).replace(
            'class="card', 'class="card interactive-card'
        ).replace(
            'class="nav-item', 'class="nav-item nav-item-micro'
        ).replace(
            '<input', '<input class="interactive-input"'
        ).replace(
            '<button', '<button class="micro-btn ripple-container"'
        )
        
        return enhanced_content

# Global micro-interaction system
micro_interaction_system = MicroInteractionSystem()

def get_micro_interaction_styles():
    """Get micro-interaction CSS styles"""
    return micro_interaction_system.animation_styles

def get_micro_interaction_scripts():
    """Get micro-interaction JavaScript"""
    return micro_interaction_system.interaction_scripts + micro_interaction_system.feedback_system

def enhance_with_micro_interactions(template):
    """Enhance template with micro-interactions"""
    return micro_interaction_system.enhance_template_with_micro_interactions(template)