"""
Micro-Animation Feedback Layer for User Interactions
Provides immediate visual feedback for all user actions with subtle, meaningful animations
"""
from flask import render_template_string

class MicroAnimationFeedbackSystem:
    def __init__(self):
        self.animation_library = self._initialize_animation_library()
        self.feedback_types = {
            'click': 'ripple_effect',
            'hover': 'elevation_lift',
            'focus': 'glow_outline',
            'success': 'checkmark_bounce',
            'error': 'shake_attention',
            'loading': 'pulse_breathe',
            'navigation': 'slide_transition',
            'form_submit': 'progress_fill',
            'data_update': 'refresh_spin',
            'modal_open': 'scale_fade_in',
            'modal_close': 'scale_fade_out',
            'notification': 'slide_down_bounce'
        }
    
    def _initialize_animation_library(self):
        """Initialize comprehensive animation library"""
        return {
            'css_animations': self._get_css_animations(),
            'javascript_interactions': self._get_javascript_interactions(),
            'transition_effects': self._get_transition_effects(),
            'feedback_states': self._get_feedback_states()
        }
    
    def _get_css_animations(self):
        """Core CSS animation definitions"""
        return """
        /* Micro-Animation Feedback Layer CSS */
        
        /* Click Feedback - Ripple Effect */
        .ripple-container {
            position: relative;
            overflow: hidden;
        }
        
        .ripple-effect {
            position: absolute;
            border-radius: 50%;
            background: rgba(0, 255, 136, 0.3);
            transform: scale(0);
            animation: ripple-animation 0.6s ease-out;
            pointer-events: none;
        }
        
        @keyframes ripple-animation {
            0% {
                transform: scale(0);
                opacity: 1;
            }
            100% {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        /* Hover Feedback - Elevation Lift */
        .hover-lift {
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .hover-lift:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        /* Focus Feedback - Glow Outline */
        .focus-glow:focus {
            outline: none;
            box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.3);
            transition: box-shadow 0.2s ease-in-out;
        }
        
        /* Success Feedback - Checkmark Bounce */
        .success-checkmark {
            display: inline-block;
            animation: checkmark-bounce 0.6s ease-in-out;
        }
        
        @keyframes checkmark-bounce {
            0% { transform: scale(0); }
            50% { transform: scale(1.2); }
            100% { transform: scale(1); }
        }
        
        /* Error Feedback - Shake Attention */
        .error-shake {
            animation: shake-attention 0.5s ease-in-out;
        }
        
        @keyframes shake-attention {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        /* Loading Feedback - Pulse Breathe */
        .loading-pulse {
            animation: pulse-breathe 2s ease-in-out infinite;
        }
        
        @keyframes pulse-breathe {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.05); }
        }
        
        /* Navigation Transition - Slide */
        .slide-transition {
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .slide-in-left {
            animation: slide-in-left 0.3s ease-out;
        }
        
        @keyframes slide-in-left {
            0% { transform: translateX(-100%); opacity: 0; }
            100% { transform: translateX(0); opacity: 1; }
        }
        
        .slide-in-right {
            animation: slide-in-right 0.3s ease-out;
        }
        
        @keyframes slide-in-right {
            0% { transform: translateX(100%); opacity: 0; }
            100% { transform: translateX(0); opacity: 1; }
        }
        
        /* Form Submit Feedback - Progress Fill */
        .progress-fill {
            position: relative;
            overflow: hidden;
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 255, 136, 0.3), transparent);
            animation: progress-sweep 1.5s ease-in-out;
        }
        
        @keyframes progress-sweep {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        /* Data Update Feedback - Refresh Spin */
        .refresh-spin {
            animation: refresh-rotation 1s ease-in-out;
        }
        
        @keyframes refresh-rotation {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Modal Animations */
        .modal-scale-fade-in {
            animation: modal-scale-fade-in 0.3s ease-out;
        }
        
        @keyframes modal-scale-fade-in {
            0% {
                opacity: 0;
                transform: scale(0.8) translateY(-20px);
            }
            100% {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }
        
        .modal-scale-fade-out {
            animation: modal-scale-fade-out 0.2s ease-in forwards;
        }
        
        @keyframes modal-scale-fade-out {
            0% {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
            100% {
                opacity: 0;
                transform: scale(0.8) translateY(-20px);
            }
        }
        
        /* Notification Slide Down */
        .notification-slide-down {
            animation: notification-slide-down 0.4s ease-out;
        }
        
        @keyframes notification-slide-down {
            0% {
                transform: translateY(-100px);
                opacity: 0;
            }
            100% {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        /* Button State Animations */
        .btn-interactive {
            position: relative;
            overflow: hidden;
            transition: all 0.2s ease;
        }
        
        .btn-interactive:active {
            transform: scale(0.98);
        }
        
        .btn-interactive.loading {
            pointer-events: none;
            opacity: 0.7;
        }
        
        .btn-interactive.loading::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 16px;
            height: 16px;
            margin: -8px 0 0 -8px;
            border: 2px solid transparent;
            border-top: 2px solid currentColor;
            border-radius: 50%;
            animation: button-loading-spin 1s linear infinite;
        }
        
        @keyframes button-loading-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Status Indicator Animations */
        .status-indicator {
            position: relative;
        }
        
        .status-indicator.pulsing::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 100%;
            height: 100%;
            transform: translate(-50%, -50%);
            border-radius: 50%;
            background: currentColor;
            opacity: 0.3;
            animation: status-pulse 2s ease-in-out infinite;
        }
        
        @keyframes status-pulse {
            0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.3; }
            50% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
        }
        
        /* Data Loading Skeleton */
        .skeleton-loader {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: skeleton-loading 1.5s ease-in-out infinite;
        }
        
        @keyframes skeleton-loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        /* Smooth Page Transitions */
        .page-transition-enter {
            animation: page-fade-in 0.4s ease-out;
        }
        
        @keyframes page-fade-in {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        
        /* Interactive Element Highlights */
        .interactive-highlight {
            position: relative;
        }
        
        .interactive-highlight::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 255, 136, 0.1);
            opacity: 0;
            transition: opacity 0.2s ease;
            pointer-events: none;
        }
        
        .interactive-highlight:hover::before {
            opacity: 1;
        }
        
        /* Reduced Motion Support */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        """
    
    def _get_javascript_interactions(self):
        """JavaScript for interactive feedback"""
        return """
        // Micro-Animation Feedback JavaScript
        
        class MicroAnimationFeedback {
            constructor() {
                this.init();
            }
            
            init() {
                this.addRippleEffect();
                this.addHoverEffects();
                this.addFormFeedback();
                this.addNavigationTransitions();
                this.addStatusIndicators();
            }
            
            // Ripple effect for clicks
            addRippleEffect() {
                document.addEventListener('click', (e) => {
                    const target = e.target.closest('.ripple-container');
                    if (!target) return;
                    
                    const ripple = document.createElement('span');
                    const rect = target.getBoundingClientRect();
                    const size = Math.max(rect.width, rect.height);
                    const x = e.clientX - rect.left - size / 2;
                    const y = e.clientY - rect.top - size / 2;
                    
                    ripple.className = 'ripple-effect';
                    ripple.style.width = ripple.style.height = size + 'px';
                    ripple.style.left = x + 'px';
                    ripple.style.top = y + 'px';
                    
                    target.appendChild(ripple);
                    
                    setTimeout(() => {
                        ripple.remove();
                    }, 600);
                });
            }
            
            // Enhanced hover effects
            addHoverEffects() {
                const hoverElements = document.querySelectorAll('.hover-lift, .interactive-highlight');
                hoverElements.forEach(element => {
                    element.addEventListener('mouseenter', () => {
                        element.style.transform = 'translateY(-2px)';
                    });
                    
                    element.addEventListener('mouseleave', () => {
                        element.style.transform = 'translateY(0)';
                    });
                });
            }
            
            // Form submission feedback
            addFormFeedback() {
                document.addEventListener('submit', (e) => {
                    const form = e.target;
                    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                    
                    if (submitBtn) {
                        this.showButtonLoading(submitBtn);
                        form.classList.add('progress-fill');
                    }
                });
            }
            
            // Navigation transitions
            addNavigationTransitions() {
                const navLinks = document.querySelectorAll('a[href^="/"], .nav-item');
                navLinks.forEach(link => {
                    link.addEventListener('click', (e) => {
                        if (link.href && !link.href.includes('#')) {
                            document.body.style.opacity = '0.8';
                            document.body.style.transform = 'translateX(10px)';
                        }
                    });
                });
            }
            
            // Status indicators
            addStatusIndicators() {
                const statusElements = document.querySelectorAll('.status-indicator');
                statusElements.forEach(element => {
                    if (element.textContent.includes('OPERATIONAL') || 
                        element.textContent.includes('Active') ||
                        element.textContent.includes('Connected')) {
                        element.classList.add('pulsing');
                    }
                });
            }
            
            // Show button loading state
            showButtonLoading(button) {
                const originalText = button.textContent;
                button.classList.add('loading');
                button.disabled = true;
                
                setTimeout(() => {
                    button.classList.remove('loading');
                    button.classList.add('success-checkmark');
                    button.textContent = '✓ Success';
                    button.disabled = false;
                    
                    setTimeout(() => {
                        button.classList.remove('success-checkmark');
                        button.textContent = originalText;
                    }, 2000);
                }, 1500);
            }
            
            // Show success feedback
            showSuccess(message, element = null) {
                const notification = this.createNotification(message, 'success');
                document.body.appendChild(notification);
                
                if (element) {
                    element.classList.add('success-checkmark');
                    setTimeout(() => element.classList.remove('success-checkmark'), 600);
                }
                
                setTimeout(() => notification.remove(), 3000);
            }
            
            // Show error feedback
            showError(message, element = null) {
                const notification = this.createNotification(message, 'error');
                document.body.appendChild(notification);
                
                if (element) {
                    element.classList.add('error-shake');
                    setTimeout(() => element.classList.remove('error-shake'), 500);
                }
                
                setTimeout(() => notification.remove(), 4000);
            }
            
            // Create notification element
            createNotification(message, type) {
                const notification = document.createElement('div');
                notification.className = `notification notification-${type} notification-slide-down`;
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 15px 20px;
                    border-radius: 8px;
                    color: white;
                    font-weight: 500;
                    z-index: 10000;
                    max-width: 300px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                    ${type === 'success' ? 'background: #28a745;' : 'background: #dc3545;'}
                `;
                notification.textContent = message;
                return notification;
            }
            
            // Show loading state
            showLoading(element) {
                element.classList.add('loading-pulse');
            }
            
            // Hide loading state
            hideLoading(element) {
                element.classList.remove('loading-pulse');
            }
            
            // Animate data refresh
            animateDataRefresh(element) {
                element.classList.add('refresh-spin');
                setTimeout(() => element.classList.remove('refresh-spin'), 1000);
            }
            
            // Add skeleton loading to containers
            addSkeletonLoading(container) {
                const skeleton = document.createElement('div');
                skeleton.className = 'skeleton-loader';
                skeleton.style.cssText = `
                    width: 100%;
                    height: 20px;
                    border-radius: 4px;
                    margin: 10px 0;
                `;
                container.appendChild(skeleton);
                return skeleton;
            }
        }
        
        // Initialize micro-animations when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            window.microAnimations = new MicroAnimationFeedback();
            console.log('Micro-Animation Feedback Layer initialized');
        });
        
        // Export for external use
        window.MicroAnimationFeedback = MicroAnimationFeedback;
        """
    
    def _get_transition_effects(self):
        """Page and component transition effects"""
        return """
        /* Transition Effects */
        
        .fade-transition {
            opacity: 0;
            transition: opacity 0.3s ease-in-out;
        }
        
        .fade-transition.active {
            opacity: 1;
        }
        
        .slide-up-transition {
            transform: translateY(20px);
            opacity: 0;
            transition: all 0.3s ease-out;
        }
        
        .slide-up-transition.active {
            transform: translateY(0);
            opacity: 1;
        }
        
        .scale-transition {
            transform: scale(0.95);
            opacity: 0;
            transition: all 0.2s ease-out;
        }
        
        .scale-transition.active {
            transform: scale(1);
            opacity: 1;
        }
        """
    
    def _get_feedback_states(self):
        """Visual feedback state definitions"""
        return """
        /* Feedback States */
        
        .state-success {
            border-left: 4px solid #28a745;
            background: rgba(40, 167, 69, 0.1);
            animation: success-glow 0.5s ease-out;
        }
        
        .state-error {
            border-left: 4px solid #dc3545;
            background: rgba(220, 53, 69, 0.1);
            animation: error-pulse 0.5s ease-out;
        }
        
        .state-warning {
            border-left: 4px solid #ffc107;
            background: rgba(255, 193, 7, 0.1);
            animation: warning-fade 0.5s ease-out;
        }
        
        .state-info {
            border-left: 4px solid #17a2b8;
            background: rgba(23, 162, 184, 0.1);
            animation: info-slide 0.5s ease-out;
        }
        
        @keyframes success-glow {
            0% { box-shadow: 0 0 0 rgba(40, 167, 69, 0.5); }
            50% { box-shadow: 0 0 20px rgba(40, 167, 69, 0.3); }
            100% { box-shadow: 0 0 0 rgba(40, 167, 69, 0); }
        }
        
        @keyframes error-pulse {
            0%, 100% { background: rgba(220, 53, 69, 0.1); }
            50% { background: rgba(220, 53, 69, 0.2); }
        }
        
        @keyframes warning-fade {
            0% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        @keyframes info-slide {
            0% { transform: translateX(-10px); }
            100% { transform: translateX(0); }
        }
        """
    
    def generate_enhanced_template_with_animations(self, base_template):
        """Enhance any template with micro-animation feedback"""
        animations_css = self.animation_library['css_animations']
        animations_js = self.animation_library['javascript_interactions']
        transitions = self.animation_library['transition_effects']
        feedback_states = self.animation_library['feedback_states']
        
        enhanced_template = base_template.replace(
            '</style>',
            animations_css + transitions + feedback_states + '</style>'
        )
        
        enhanced_template = enhanced_template.replace(
            '</body>',
            f'<script>{animations_js}</script></body>'
        )
        
        return enhanced_template
    
    def get_component_classes(self, component_type):
        """Get appropriate animation classes for component types"""
        class_mappings = {
            'button': 'btn-interactive ripple-container hover-lift focus-glow',
            'card': 'hover-lift interactive-highlight',
            'nav_item': 'hover-lift slide-transition',
            'form': 'focus-glow',
            'modal': 'modal-scale-fade-in',
            'notification': 'notification-slide-down',
            'status': 'status-indicator pulsing',
            'loading': 'loading-pulse skeleton-loader'
        }
        return class_mappings.get(component_type, 'interactive-highlight')

def get_micro_animation_system():
    """Get micro-animation feedback system instance"""
    return MicroAnimationFeedbackSystem()

def enhance_template_with_animations(template):
    """Enhance template with micro-animation feedback"""
    system = MicroAnimationFeedbackSystem()
    return system.generate_enhanced_template_with_animations(template)