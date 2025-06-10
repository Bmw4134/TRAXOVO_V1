/**
 * TRAXOVO ∞ Clarity Core - Intuitive Gesture-Based Navigation System
 * Premium enterprise gesture controls for enhanced user experience
 */

// Asset metadata parsing utility
function parseAssetMeta(assetId) {
    if (!assetId) return { driverName: "", rawId: "" };

    const matchParentheses = assetId.match(/\((.*?)\)/);
    const matchDash = assetId.split(" - ");

    const driverName = matchDash.length > 1
        ? matchDash[1].trim()
        : matchParentheses
        ? matchParentheses[1].trim()
        : assetId.trim();

    const rawId = matchDash[0].replace(/[^0-9]/g, "").trim();
    return { driverName, rawId };
}

// Check if GestureNavigationController already exists
if (typeof window.GestureNavigationController === 'undefined') {
    class GestureNavigationController {
        constructor() {
            this.isEnabled = true;
            this.gestureThreshold = 50;
            this.velocityThreshold = 0.5;
            this.touchStartX = 0;
            this.touchStartY = 0;
            this.touchEndX = 0;
            this.touchEndY = 0;
            this.touchStartTime = 0;
            this.currentSection = 0;
            this.sections = [];
            this.isDragging = false;
            this.dragStartX = 0;
            this.dragStartY = 0;
            
            this.init();
        }

    init() {
        this.identifySections();
        this.setupTouchEvents();
        this.setupMouseEvents();
        this.setupKeyboardShortcuts();
        this.createGestureIndicators();
        console.log('✓ Gesture navigation system activated');
    }

    identifySections() {
        // Identify main dashboard sections for navigation
        this.sections = [
            { element: document.querySelector('.qnis-dashboard-section'), name: 'QNIS Dashboard' },
            { element: document.querySelector('.sr-pm-section'), name: 'SR PM Portal' },
            { element: document.querySelector('.asset-tracking-section'), name: 'Asset Tracking' },
            { element: document.querySelector('.analytics-section'), name: 'Analytics' }
        ].filter(section => section.element);

        // Add KPI cards as navigable sections with enhanced asset metadata
        const kpiCards = document.querySelectorAll('.kpi-card, .metric-card, .metric-item');
        kpiCards.forEach((card, index) => {
            const assetId = card.dataset.assetId || card.querySelector('[data-asset-id]')?.dataset.assetId;
            const cardTitle = card.querySelector('h3, .metric-title, .kpi-title')?.textContent || `KPI Card ${index + 1}`;
            
            let sectionName = cardTitle;
            let assetMeta = null;
            
            if (assetId) {
                assetMeta = parseAssetMeta(assetId);
                if (assetMeta.driverName) {
                    sectionName = `${cardTitle} - ${assetMeta.driverName}`;
                }
            }
            
            this.sections.push({
                element: card,
                name: sectionName,
                type: 'kpi',
                assetId: assetId,
                assetMeta: assetMeta,
                originalTitle: cardTitle
            });
        });

        // Add asset-specific elements from tracking data
        const assetElements = document.querySelectorAll('[data-asset-id], .asset-item, .equipment-item');
        assetElements.forEach((element, index) => {
            if (!element.classList.contains('kpi-card') && !element.classList.contains('metric-card')) {
                const assetId = element.dataset.assetId || element.textContent;
                const assetMeta = parseAssetMeta(assetId);
                
                this.sections.push({
                    element: element,
                    name: assetMeta.driverName ? `Asset ${assetMeta.rawId} - ${assetMeta.driverName}` : `Asset ${index + 1}`,
                    type: 'asset',
                    assetId: assetId,
                    assetMeta: assetMeta
                });
            }
        });
    }

    setupTouchEvents() {
        document.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
        document.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
        document.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: false });
    }

    setupMouseEvents() {
        document.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        document.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        document.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (!this.isEnabled) return;

            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.navigateLeft();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.navigateRight();
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    this.navigateUp();
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    this.navigateDown();
                    break;
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    this.activateCurrentSection();
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.closeActiveModal();
                    break;
            }
        });
    }

    handleTouchStart(e) {
        if (!this.isEnabled) return;
        
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
        this.touchStartTime = Date.now();
        
        // Add visual feedback
        this.addTouchFeedback(e.touches[0].clientX, e.touches[0].clientY);
    }

    handleTouchMove(e) {
        if (!this.isEnabled) return;
        
        // Prevent default scrolling for gesture recognition
        if (Math.abs(e.touches[0].clientX - this.touchStartX) > 10) {
            e.preventDefault();
        }
    }

    handleTouchEnd(e) {
        if (!this.isEnabled) return;
        
        this.touchEndX = e.changedTouches[0].clientX;
        this.touchEndY = e.changedTouches[0].clientY;
        
        const deltaX = this.touchEndX - this.touchStartX;
        const deltaY = this.touchEndY - this.touchStartY;
        const deltaTime = Date.now() - this.touchStartTime;
        const velocity = Math.sqrt(deltaX * deltaX + deltaY * deltaY) / deltaTime;
        
        this.processGesture(deltaX, deltaY, velocity);
        this.removeTouchFeedback();
    }

    handleMouseDown(e) {
        if (!this.isEnabled || e.button !== 0) return;
        
        this.isDragging = true;
        this.dragStartX = e.clientX;
        this.dragStartY = e.clientY;
        
        // Add visual feedback for mouse gestures
        this.addTouchFeedback(e.clientX, e.clientY);
    }

    handleMouseMove(e) {
        if (!this.isEnabled || !this.isDragging) return;
        
        const deltaX = e.clientX - this.dragStartX;
        const deltaY = e.clientY - this.dragStartY;
        
        // Show gesture preview
        this.showGesturePreview(deltaX, deltaY);
    }

    handleMouseUp(e) {
        if (!this.isEnabled || !this.isDragging) return;
        
        const deltaX = e.clientX - this.dragStartX;
        const deltaY = e.clientY - this.dragStartY;
        
        this.isDragging = false;
        this.processGesture(deltaX, deltaY, 1);
        this.removeTouchFeedback();
        this.hideGesturePreview();
    }

    handleWheel(e) {
        if (!this.isEnabled) return;
        
        if (e.ctrlKey) {
            e.preventDefault();
            
            if (e.deltaY < 0) {
                this.zoomIn();
            } else {
                this.zoomOut();
            }
        }
    }

    processGesture(deltaX, deltaY, velocity) {
        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);
        
        // Require minimum gesture distance
        if (absX < this.gestureThreshold && absY < this.gestureThreshold) {
            return;
        }
        
        // Determine gesture type
        if (absX > absY) {
            // Horizontal gesture
            if (deltaX > 0) {
                this.handleSwipeRight(velocity);
            } else {
                this.handleSwipeLeft(velocity);
            }
        } else {
            // Vertical gesture
            if (deltaY > 0) {
                this.handleSwipeDown(velocity);
            } else {
                this.handleSwipeUp(velocity);
            }
        }
    }

    handleSwipeLeft(velocity) {
        console.log('Gesture: Swipe Left');
        this.showGestureNotification('← Swipe Left', 'Navigating to next section');
        this.navigateRight(); // Counter-intuitive but follows mobile convention
    }

    handleSwipeRight(velocity) {
        console.log('Gesture: Swipe Right');
        this.showGestureNotification('→ Swipe Right', 'Navigating to previous section');
        this.navigateLeft();
    }

    handleSwipeUp(velocity) {
        console.log('Gesture: Swipe Up');
        this.showGestureNotification('↑ Swipe Up', 'Opening drill-down view');
        this.navigateUp();
    }

    handleSwipeDown(velocity) {
        console.log('Gesture: Swipe Down');
        this.showGestureNotification('↓ Swipe Down', 'Closing active view');
        this.navigateDown();
    }

    navigateLeft() {
        if (this.sections.length === 0) return;
        
        this.currentSection = (this.currentSection - 1 + this.sections.length) % this.sections.length;
        this.highlightCurrentSection();
        this.scrollToSection(this.sections[this.currentSection]);
    }

    navigateRight() {
        if (this.sections.length === 0) return;
        
        this.currentSection = (this.currentSection + 1) % this.sections.length;
        this.highlightCurrentSection();
        this.scrollToSection(this.sections[this.currentSection]);
    }

    navigateUp() {
        const currentElement = this.sections[this.currentSection]?.element;
        if (currentElement) {
            // Try to open drill-down modal if it's a KPI card
            if (currentElement.classList.contains('kpi-card') || currentElement.classList.contains('metric-card')) {
                this.activateCurrentSection();
            } else {
                // Navigate to parent section
                this.navigateToParentSection();
            }
        }
    }

    navigateDown() {
        // Close any open modals or navigate to child sections
        const activeModal = document.querySelector('.enterprise-modal.show');
        if (activeModal) {
            this.closeActiveModal();
        } else {
            this.navigateToChildSection();
        }
    }

    activateCurrentSection() {
        const section = this.sections[this.currentSection];
        if (!section) return;
        
        const element = section.element;
        
        // Simulate click to activate drill-down
        if (element.classList.contains('kpi-card') || element.classList.contains('metric-card')) {
            const clickEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            element.dispatchEvent(clickEvent);
            this.showGestureNotification('⚡ Activated', `Opening ${section.name} details`);
        }
    }

    closeActiveModal() {
        const activeModal = document.querySelector('.enterprise-modal.show');
        if (activeModal) {
            const closeButton = activeModal.querySelector('.modal-close');
            if (closeButton) {
                closeButton.click();
            }
            this.showGestureNotification('✖ Closed', 'Modal view closed');
        }
    }

    highlightCurrentSection() {
        // Remove previous highlights
        document.querySelectorAll('.gesture-highlight').forEach(el => {
            el.classList.remove('gesture-highlight');
        });
        
        // Add highlight to current section
        const currentElement = this.sections[this.currentSection]?.element;
        if (currentElement) {
            currentElement.classList.add('gesture-highlight');
        }
    }

    scrollToSection(section) {
        if (!section || !section.element) return;
        
        section.element.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'center'
        });
    }

    zoomIn() {
        const dashboard = document.querySelector('.dashboard-container');
        if (dashboard) {
            const currentScale = parseFloat(dashboard.style.transform?.match(/scale\(([\d.]+)\)/)?.[1] || '1');
            const newScale = Math.min(currentScale * 1.1, 2);
            dashboard.style.transform = `scale(${newScale})`;
            dashboard.style.transformOrigin = 'center center';
            this.showGestureNotification('🔍 Zoom In', `Scale: ${Math.round(newScale * 100)}%`);
        }
    }

    zoomOut() {
        const dashboard = document.querySelector('.dashboard-container');
        if (dashboard) {
            const currentScale = parseFloat(dashboard.style.transform?.match(/scale\(([\d.]+)\)/)?.[1] || '1');
            const newScale = Math.max(currentScale * 0.9, 0.5);
            dashboard.style.transform = `scale(${newScale})`;
            dashboard.style.transformOrigin = 'center center';
            this.showGestureNotification('🔍 Zoom Out', `Scale: ${Math.round(newScale * 100)}%`);
        }
    }

    addTouchFeedback(x, y) {
        const feedback = document.createElement('div');
        feedback.className = 'gesture-touch-feedback';
        feedback.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            width: 40px;
            height: 40px;
            background: radial-gradient(circle, rgba(102, 126, 234, 0.3) 0%, transparent 70%);
            border: 2px solid rgba(102, 126, 234, 0.6);
            border-radius: 50%;
            pointer-events: none;
            z-index: 10000;
            transform: translate(-50%, -50%) scale(0);
            animation: gestureRipple 0.3s ease-out forwards;
        `;
        
        document.body.appendChild(feedback);
        
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.parentNode.removeChild(feedback);
            }
        }, 300);
    }

    removeTouchFeedback() {
        const feedbacks = document.querySelectorAll('.gesture-touch-feedback');
        feedbacks.forEach(feedback => {
            feedback.style.animation = 'gestureRippleOut 0.2s ease-out forwards';
        });
    }

    showGesturePreview(deltaX, deltaY) {
        let preview = document.querySelector('.gesture-preview');
        if (!preview) {
            preview = document.createElement('div');
            preview.className = 'gesture-preview';
            preview.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 20px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: 600;
                z-index: 10001;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s ease;
            `;
            document.body.appendChild(preview);
        }
        
        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);
        
        if (absX > this.gestureThreshold || absY > this.gestureThreshold) {
            let gesture = '';
            if (absX > absY) {
                gesture = deltaX > 0 ? '→ Navigate Previous' : '← Navigate Next';
            } else {
                gesture = deltaY > 0 ? '↓ Close View' : '↑ Open Details';
            }
            
            preview.textContent = gesture;
            preview.style.opacity = '1';
        }
    }

    hideGesturePreview() {
        const preview = document.querySelector('.gesture-preview');
        if (preview) {
            preview.style.opacity = '0';
            setTimeout(() => {
                if (preview.parentNode) {
                    preview.parentNode.removeChild(preview);
                }
            }, 200);
        }
    }

    showGestureNotification(gesture, description) {
        const notification = document.createElement('div');
        notification.className = 'gesture-notification';
        notification.innerHTML = `
            <div class="gesture-icon">${gesture}</div>
            <div class="gesture-description">${description}</div>
        `;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            z-index: 10002;
            font-weight: 600;
            transform: translateX(100%);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Animate out
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 2000);
    }

    createGestureIndicators() {
        const indicators = document.createElement('div');
        indicators.className = 'gesture-indicators';
        indicators.innerHTML = `
            <div class="gesture-help-button" onclick="gestureController.toggleHelp()">
                <span>🤚</span>
            </div>
            <div class="gesture-help-panel" id="gestureHelp" style="display: none;">
                <h3>Gesture Controls</h3>
                <div class="gesture-help-item">
                    <span class="gesture-symbol">←→</span>
                    <span class="gesture-text">Swipe left/right: Navigate sections</span>
                </div>
                <div class="gesture-help-item">
                    <span class="gesture-symbol">↑</span>
                    <span class="gesture-text">Swipe up: Open details</span>
                </div>
                <div class="gesture-help-item">
                    <span class="gesture-symbol">↓</span>
                    <span class="gesture-text">Swipe down: Close view</span>
                </div>
                <div class="gesture-help-item">
                    <span class="gesture-symbol">⌨️</span>
                    <span class="gesture-text">Arrow keys: Navigate</span>
                </div>
                <div class="gesture-help-item">
                    <span class="gesture-symbol">Ctrl+Wheel</span>
                    <span class="gesture-text">Zoom in/out</span>
                </div>
            </div>
        `;
        indicators.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10003;
        `;
        
        document.body.appendChild(indicators);
    }

    toggleHelp() {
        const helpPanel = document.getElementById('gestureHelp');
        if (helpPanel) {
            helpPanel.style.display = helpPanel.style.display === 'none' ? 'block' : 'none';
        }
    }

    navigateToParentSection() {
        // Implementation for navigating to parent sections
        console.log('Navigating to parent section');
    }

    navigateToChildSection() {
        // Implementation for navigating to child sections
        console.log('Navigating to child section');
    }

    disable() {
        this.isEnabled = false;
        console.log('Gesture navigation disabled');
    }

    enable() {
        this.isEnabled = true;
        console.log('Gesture navigation enabled');
    }
}

// CSS animations for gesture feedback
const gestureStyles = document.createElement('style');
gestureStyles.textContent = `
    @keyframes gestureRipple {
        0% {
            transform: translate(-50%, -50%) scale(0);
            opacity: 1;
        }
        100% {
            transform: translate(-50%, -50%) scale(1);
            opacity: 0.7;
        }
    }

    @keyframes gestureRippleOut {
        0% {
            transform: translate(-50%, -50%) scale(1);
            opacity: 0.7;
        }
        100% {
            transform: translate(-50%, -50%) scale(1.5);
            opacity: 0;
        }
    }

    .gesture-highlight {
        outline: 3px solid #667eea !important;
        outline-offset: 2px;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.4) !important;
    }

    .gesture-help-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }

    .gesture-help-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    .gesture-help-panel {
        position: absolute;
        bottom: 70px;
        right: 0;
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 20px;
        border-radius: 12px;
        min-width: 280px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .gesture-help-panel h3 {
        margin: 0 0 15px 0;
        color: #667eea;
        font-size: 18px;
    }

    .gesture-help-item {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        padding: 8px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.05);
    }

    .gesture-symbol {
        width: 60px;
        text-align: center;
        font-weight: bold;
        color: #667eea;
    }

    .gesture-text {
        flex: 1;
        font-size: 14px;
    }

    .gesture-notification .gesture-icon {
        font-size: 20px;
        margin-bottom: 4px;
    }

    .gesture-notification .gesture-description {
        font-size: 14px;
        opacity: 0.9;
    }
`;

document.head.appendChild(gestureStyles);

// Initialize gesture controller when DOM is ready
let gestureController;

function initializeGestureNavigation() {
    if (typeof GestureNavigationController !== 'undefined') {
        gestureController = new GestureNavigationController();
        window.gestureController = gestureController;
        console.log('✓ Intuitive gesture-based navigation prototype activated');
    }
}

    // Assign to window for global access
    window.GestureNavigationController = GestureNavigationController;
}

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeGestureNavigation);
} else {
    initializeGestureNavigation();
}