/**
 * TRAXOVO Gesture-Based Navigation System
 * Intuitive touch, mouse, and keyboard navigation for enterprise dashboard
 */

class GestureNavigationSystem {
    constructor() {
        this.isEnabled = true;
        this.touchStartPos = { x: 0, y: 0 };
        this.touchEndPos = { x: 0, y: 0 };
        this.gestureThreshold = 50; // Minimum distance for gesture recognition
        this.currentSection = 'overview';
        this.sections = ['overview', 'analytics', 'maintenance', 'safety', 'billing', 'assets'];
        this.activeGesture = null;
        this.gestureStartTime = 0;
        this.isMultiTouch = false;
        this.lastTapTime = 0;
        this.tapThreshold = 300; // Double tap threshold
        
        this.initializeGestures();
        this.createGestureIndicators();
        this.setupKeyboardShortcuts();
    }
    
    initializeGestures() {
        console.log('Initializing TRAXOVO gesture navigation system...');
        
        // Touch gestures for mobile/tablet
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        
        // Mouse gestures for desktop
        document.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Wheel gestures
        document.addEventListener('wheel', this.handleWheel.bind(this), { passive: false });
        
        // Pinch zoom gestures
        document.addEventListener('gesturestart', this.handleGestureStart.bind(this), { passive: false });
        document.addEventListener('gesturechange', this.handleGestureChange.bind(this), { passive: false });
        document.addEventListener('gestureend', this.handleGestureEnd.bind(this), { passive: false });
        
        console.log('✓ Gesture navigation system active');
    }
    
    // Touch Gesture Handlers
    handleTouchStart(e) {
        if (!this.isEnabled) return;
        
        this.gestureStartTime = Date.now();
        
        if (e.touches.length === 1) {
            // Single touch
            this.touchStartPos = {
                x: e.touches[0].clientX,
                y: e.touches[0].clientY
            };
            this.isMultiTouch = false;
            
            // Check for double tap
            const currentTime = Date.now();
            if (currentTime - this.lastTapTime < this.tapThreshold) {
                this.handleDoubleTap(e);
            }
            this.lastTapTime = currentTime;
            
        } else if (e.touches.length === 2) {
            // Two finger gestures
            this.isMultiTouch = true;
            this.handleTwoFingerStart(e);
        } else if (e.touches.length === 3) {
            // Three finger gestures
            this.handleThreeFingerStart(e);
        }
        
        this.showGestureIndicator('touch-start');
    }
    
    handleTouchMove(e) {
        if (!this.isEnabled || e.touches.length === 0) return;
        
        if (e.touches.length === 1 && !this.isMultiTouch) {
            // Single finger swipe
            this.touchEndPos = {
                x: e.touches[0].clientX,
                y: e.touches[0].clientY
            };
            
            const deltaX = this.touchEndPos.x - this.touchStartPos.x;
            const deltaY = this.touchEndPos.y - this.touchStartPos.y;
            
            // Show swipe direction indicator
            if (Math.abs(deltaX) > 20 || Math.abs(deltaY) > 20) {
                this.showSwipeIndicator(deltaX, deltaY);
            }
        } else if (e.touches.length === 2) {
            // Two finger gestures (pinch/rotate)
            this.handleTwoFingerMove(e);
        }
    }
    
    handleTouchEnd(e) {
        if (!this.isEnabled) return;
        
        const gestureTime = Date.now() - this.gestureStartTime;
        
        if (!this.isMultiTouch && e.changedTouches.length === 1) {
            const deltaX = this.touchEndPos.x - this.touchStartPos.x;
            const deltaY = this.touchEndPos.y - this.touchStartPos.y;
            
            this.processSwipeGesture(deltaX, deltaY, gestureTime);
        }
        
        this.hideGestureIndicator();
        this.activeGesture = null;
    }
    
    processSwipeGesture(deltaX, deltaY, gestureTime) {
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        if (distance < this.gestureThreshold) return; // Not a significant gesture
        
        const isHorizontal = Math.abs(deltaX) > Math.abs(deltaY);
        const velocity = distance / gestureTime;
        
        if (isHorizontal) {
            if (deltaX > 0) {
                // Swipe right - Previous section
                this.navigateToPreviousSection();
                this.showGestureResult('← Previous Section');
            } else {
                // Swipe left - Next section
                this.navigateToNextSection();
                this.showGestureResult('Next Section →');
            }
        } else {
            if (deltaY > 0) {
                // Swipe down - Show main menu
                this.showMainMenu();
                this.showGestureResult('↓ Main Menu');
            } else {
                // Swipe up - Quick actions
                this.showQuickActions();
                this.showGestureResult('↑ Quick Actions');
            }
        }
    }
    
    // Two Finger Gestures
    handleTwoFingerStart(e) {
        e.preventDefault();
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        
        this.initialDistance = this.getDistance(touch1, touch2);
        this.initialAngle = this.getAngle(touch1, touch2);
    }
    
    handleTwoFingerMove(e) {
        if (e.touches.length !== 2) return;
        
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        
        const currentDistance = this.getDistance(touch1, touch2);
        const currentAngle = this.getAngle(touch1, touch2);
        
        // Pinch to zoom
        const scaleChange = currentDistance / this.initialDistance;
        if (scaleChange > 1.2) {
            this.handlePinchOut();
        } else if (scaleChange < 0.8) {
            this.handlePinchIn();
        }
        
        // Rotation gesture
        const angleChange = currentAngle - this.initialAngle;
        if (Math.abs(angleChange) > 15) {
            this.handleRotation(angleChange);
        }
    }
    
    handlePinchOut() {
        // Zoom in / Expand current section
        this.expandCurrentSection();
        this.showGestureResult('🔍 Expanded View');
    }
    
    handlePinchIn() {
        // Zoom out / Return to overview
        this.returnToOverview();
        this.showGestureResult('📋 Overview Mode');
    }
    
    handleRotation(angle) {
        if (angle > 0) {
            // Clockwise rotation - Next metric
            this.navigateToNextMetric();
            this.showGestureResult('↻ Next Metric');
        } else {
            // Counter-clockwise rotation - Previous metric
            this.navigateToPreviousMetric();
            this.showGestureResult('↺ Previous Metric');
        }
    }
    
    // Three Finger Gestures
    handleThreeFingerStart(e) {
        e.preventDefault();
        this.activeGesture = 'three-finger';
    }
    
    handleThreeFingerSwipe(deltaX, deltaY) {
        if (Math.abs(deltaY) > Math.abs(deltaX)) {
            if (deltaY > 0) {
                // Three finger swipe down - Dashboard settings
                this.openDashboardSettings();
                this.showGestureResult('⚙️ Dashboard Settings');
            } else {
                // Three finger swipe up - System status
                this.showSystemStatus();
                this.showGestureResult('📊 System Status');
            }
        } else {
            if (deltaX > 0) {
                // Three finger swipe right - Previous dashboard
                this.switchToPreviousDashboard();
                this.showGestureResult('← Previous Dashboard');
            } else {
                // Three finger swipe left - Next dashboard
                this.switchToNextDashboard();
                this.showGestureResult('Next Dashboard →');
            }
        }
    }
    
    // Mouse Gesture Handlers
    handleMouseDown(e) {
        if (!this.isEnabled || e.button !== 2) return; // Right mouse button
        
        this.mouseStartPos = { x: e.clientX, y: e.clientY };
        this.isMouseGestureActive = true;
        e.preventDefault();
    }
    
    handleMouseMove(e) {
        if (!this.isMouseGestureActive) return;
        
        const deltaX = e.clientX - this.mouseStartPos.x;
        const deltaY = e.clientY - this.mouseStartPos.y;
        
        this.showMouseGestureTrail(e.clientX, e.clientY);
    }
    
    handleMouseUp(e) {
        if (!this.isMouseGestureActive) return;
        
        const deltaX = e.clientX - this.mouseStartPos.x;
        const deltaY = e.clientY - this.mouseStartPos.y;
        
        this.processMouseGesture(deltaX, deltaY);
        this.isMouseGestureActive = false;
        this.clearMouseGestureTrail();
    }
    
    processMouseGesture(deltaX, deltaY) {
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        if (distance < 30) return; // Too small to be a gesture
        
        // Recognize common mouse gesture patterns
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            // Horizontal gestures
            if (deltaX > 0) {
                this.navigateBack();
                this.showGestureResult('← Back');
            } else {
                this.navigateForward();
                this.showGestureResult('Forward →');
            }
        } else {
            // Vertical gestures
            if (deltaY > 0) {
                this.refreshCurrentView();
                this.showGestureResult('↻ Refresh');
            } else {
                this.minimizeCurrentView();
                this.showGestureResult('↑ Minimize');
            }
        }
        
        // Complex gesture patterns
        if (this.isCircularGesture(deltaX, deltaY)) {
            this.openContextMenu();
            this.showGestureResult('⚙️ Context Menu');
        }
    }
    
    // Wheel Gesture Handler
    handleWheel(e) {
        if (!this.isEnabled) return;
        
        if (e.ctrlKey) {
            // Ctrl + Wheel = Zoom
            e.preventDefault();
            if (e.deltaY < 0) {
                this.zoomIn();
                this.showGestureResult('🔍 Zoom In');
            } else {
                this.zoomOut();
                this.showGestureResult('🔍 Zoom Out');
            }
        } else if (e.shiftKey) {
            // Shift + Wheel = Horizontal scroll
            e.preventDefault();
            if (e.deltaY < 0) {
                this.scrollLeft();
            } else {
                this.scrollRight();
            }
        }
    }
    
    // Keyboard Shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (!this.isEnabled) return;
            
            // Check for modifier combinations
            const isCtrl = e.ctrlKey || e.metaKey;
            const isShift = e.shiftKey;
            const isAlt = e.altKey;
            
            // Navigation shortcuts
            switch(e.key) {
                case 'ArrowLeft':
                    if (isCtrl) {
                        this.navigateToPreviousSection();
                        this.showGestureResult('← Previous Section');
                        e.preventDefault();
                    }
                    break;
                    
                case 'ArrowRight':
                    if (isCtrl) {
                        this.navigateToNextSection();
                        this.showGestureResult('Next Section →');
                        e.preventDefault();
                    }
                    break;
                    
                case 'ArrowUp':
                    if (isCtrl) {
                        this.showQuickActions();
                        this.showGestureResult('↑ Quick Actions');
                        e.preventDefault();
                    }
                    break;
                    
                case 'ArrowDown':
                    if (isCtrl) {
                        this.showMainMenu();
                        this.showGestureResult('↓ Main Menu');
                        e.preventDefault();
                    }
                    break;
                    
                case 'Escape':
                    this.returnToOverview();
                    this.showGestureResult('📋 Overview Mode');
                    e.preventDefault();
                    break;
                    
                case 'Space':
                    if (isCtrl) {
                        this.openCommandPalette();
                        this.showGestureResult('⌘ Command Palette');
                        e.preventDefault();
                    }
                    break;
            }
            
            // Quick access shortcuts (Alt + Number)
            if (isAlt && !isNaN(e.key)) {
                const sectionIndex = parseInt(e.key) - 1;
                if (sectionIndex >= 0 && sectionIndex < this.sections.length) {
                    this.navigateToSection(this.sections[sectionIndex]);
                    this.showGestureResult(`${e.key} ${this.sections[sectionIndex]}`);
                    e.preventDefault();
                }
            }
        });
    }
    
    // Navigation Actions
    navigateToNextSection() {
        const currentIndex = this.sections.indexOf(this.currentSection);
        const nextIndex = (currentIndex + 1) % this.sections.length;
        this.navigateToSection(this.sections[nextIndex]);
    }
    
    navigateToPreviousSection() {
        const currentIndex = this.sections.indexOf(this.currentSection);
        const prevIndex = currentIndex === 0 ? this.sections.length - 1 : currentIndex - 1;
        this.navigateToSection(this.sections[prevIndex]);
    }
    
    navigateToSection(section) {
        this.currentSection = section;
        
        // Trigger navigation based on section
        switch(section) {
            case 'overview':
                if (typeof showSection === 'function') showSection('overview');
                break;
            case 'analytics':
                if (typeof showSection === 'function') showSection('analytics');
                break;
            case 'maintenance':
                if (typeof showSection === 'function') showSection('maintenance');
                break;
            case 'safety':
                if (typeof showSection === 'function') showSection('safety');
                break;
            case 'billing':
                if (typeof showSection === 'function') showSection('billing');
                break;
            case 'assets':
                if (typeof showSection === 'function') showSection('assets');
                break;
        }
        
        this.updateSectionIndicator(section);
    }
    
    showMainMenu() {
        // Show/hide main navigation menu
        const sidebar = document.querySelector('.qnis-sidebar-zone');
        if (sidebar) {
            sidebar.classList.toggle('expanded');
        }
    }
    
    showQuickActions() {
        // Show quick actions overlay
        this.createQuickActionsOverlay();
    }
    
    expandCurrentSection() {
        // Expand current section to fullscreen
        const mainZone = document.querySelector('.qnis-main-zone');
        if (mainZone) {
            mainZone.classList.toggle('expanded-view');
        }
    }
    
    returnToOverview() {
        this.navigateToSection('overview');
    }
    
    // Visual Feedback
    createGestureIndicators() {
        // Create gesture indicator container
        const indicatorContainer = document.createElement('div');
        indicatorContainer.id = 'gesture-indicators';
        indicatorContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10001;
            pointer-events: none;
        `;
        document.body.appendChild(indicatorContainer);
        
        // Create gesture result display
        const resultDisplay = document.createElement('div');
        resultDisplay.id = 'gesture-result';
        resultDisplay.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 255, 159, 0.9);
            color: white;
            padding: 15px 25px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            z-index: 10002;
            opacity: 0;
            pointer-events: none;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 255, 255, 0.3);
        `;
        document.body.appendChild(resultDisplay);
    }
    
    showGestureIndicator(type) {
        const indicator = document.getElementById('gesture-indicators');
        if (!indicator) return;
        
        indicator.innerHTML = `
            <div style="
                background: rgba(0, 255, 159, 0.2);
                border: 2px solid rgba(0, 255, 159, 0.6);
                border-radius: 50%;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #00ff9f;
                font-size: 18px;
                animation: pulse 1s infinite;
            ">
                ⚡
            </div>
        `;
    }
    
    showSwipeIndicator(deltaX, deltaY) {
        let arrow = '→';
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            arrow = deltaX > 0 ? '→' : '←';
        } else {
            arrow = deltaY > 0 ? '↓' : '↑';
        }
        
        const indicator = document.getElementById('gesture-indicators');
        if (indicator) {
            indicator.innerHTML = `
                <div style="
                    background: rgba(0, 212, 255, 0.2);
                    border: 2px solid rgba(0, 212, 255, 0.6);
                    border-radius: 25px;
                    padding: 10px 15px;
                    color: #00d4ff;
                    font-size: 20px;
                    font-weight: bold;
                ">
                    ${arrow}
                </div>
            `;
        }
    }
    
    showGestureResult(message) {
        const resultDisplay = document.getElementById('gesture-result');
        if (!resultDisplay) return;
        
        resultDisplay.textContent = message;
        resultDisplay.style.opacity = '1';
        resultDisplay.style.transform = 'translate(-50%, -50%) scale(1.1)';
        
        setTimeout(() => {
            resultDisplay.style.opacity = '0';
            resultDisplay.style.transform = 'translate(-50%, -50%) scale(1)';
        }, 2000);
    }
    
    hideGestureIndicator() {
        const indicator = document.getElementById('gesture-indicators');
        if (indicator) {
            indicator.innerHTML = '';
        }
    }
    
    updateSectionIndicator(section) {
        // Update UI to show current section
        const sidebarItems = document.querySelectorAll('.qnis-sidebar-item');
        sidebarItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.section === section) {
                item.classList.add('active');
            }
        });
    }
    
    createQuickActionsOverlay() {
        // Remove existing overlay
        const existing = document.getElementById('quick-actions-overlay');
        if (existing) existing.remove();
        
        const overlay = document.createElement('div');
        overlay.id = 'quick-actions-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        overlay.innerHTML = `
            <div style="
                background: linear-gradient(135deg, rgba(26, 26, 46, 0.98), rgba(15, 15, 35, 0.98));
                border: 2px solid rgba(0, 255, 159, 0.4);
                border-radius: 20px;
                padding: 40px;
                max-width: 600px;
                width: 90%;
            ">
                <h2 style="color: #00ff9f; margin-bottom: 30px; text-align: center;">Quick Actions</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                    <button onclick="openFleetAssetsDrillDown(); document.getElementById('quick-actions-overlay').remove();" style="
                        background: rgba(0, 255, 159, 0.1);
                        border: 1px solid rgba(0, 255, 159, 0.3);
                        color: white;
                        padding: 15px;
                        border-radius: 10px;
                        cursor: pointer;
                    ">📊 Fleet Analysis</button>
                    <button onclick="openAnomalyDrillDown(); document.getElementById('quick-actions-overlay').remove();" style="
                        background: rgba(255, 165, 0, 0.1);
                        border: 1px solid rgba(255, 165, 0, 0.3);
                        color: white;
                        padding: 15px;
                        border-radius: 10px;
                        cursor: pointer;
                    ">⚠️ Anomaly Detection</button>
                    <button onclick="openRevenueDrillDown(); document.getElementById('quick-actions-overlay').remove();" style="
                        background: rgba(0, 212, 255, 0.1);
                        border: 1px solid rgba(0, 212, 255, 0.3);
                        color: white;
                        padding: 15px;
                        border-radius: 10px;
                        cursor: pointer;
                    ">💰 Revenue Analysis</button>
                    <button onclick="openUtilizationDrillDown(); document.getElementById('quick-actions-overlay').remove();" style="
                        background: rgba(0, 255, 159, 0.1);
                        border: 1px solid rgba(0, 255, 159, 0.3);
                        color: white;
                        padding: 15px;
                        border-radius: 10px;
                        cursor: pointer;
                    ">⚡ Utilization Metrics</button>
                </div>
                <button onclick="document.getElementById('quick-actions-overlay').remove();" style="
                    position: absolute;
                    top: 15px;
                    right: 15px;
                    background: none;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    color: white;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    cursor: pointer;
                ">✕</button>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.remove();
            }
        }, 10000);
    }
    
    // Utility Functions
    getDistance(touch1, touch2) {
        const dx = touch2.clientX - touch1.clientX;
        const dy = touch2.clientY - touch1.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    getAngle(touch1, touch2) {
        const dx = touch2.clientX - touch1.clientX;
        const dy = touch2.clientY - touch1.clientY;
        return Math.atan2(dy, dx) * 180 / Math.PI;
    }
    
    isCircularGesture(deltaX, deltaY) {
        // Simple circular gesture detection
        return Math.abs(deltaX) > 50 && Math.abs(deltaY) > 50;
    }
    
    // Additional Navigation Methods
    navigateBack() {
        window.history.back();
    }
    
    navigateForward() {
        window.history.forward();
    }
    
    refreshCurrentView() {
        window.location.reload();
    }
    
    minimizeCurrentView() {
        // Implementation for minimizing current view
        console.log('Minimizing current view...');
    }
    
    zoomIn() {
        document.body.style.zoom = parseFloat(document.body.style.zoom || 1) + 0.1;
    }
    
    zoomOut() {
        document.body.style.zoom = Math.max(0.5, parseFloat(document.body.style.zoom || 1) - 0.1);
    }
    
    scrollLeft() {
        window.scrollBy(-100, 0);
    }
    
    scrollRight() {
        window.scrollBy(100, 0);
    }
    
    openCommandPalette() {
        // Implementation for command palette
        console.log('Opening command palette...');
    }
    
    openDashboardSettings() {
        // Implementation for dashboard settings
        console.log('Opening dashboard settings...');
    }
    
    showSystemStatus() {
        // Implementation for system status
        console.log('Showing system status...');
    }
    
    switchToPreviousDashboard() {
        // Implementation for switching dashboards
        console.log('Switching to previous dashboard...');
    }
    
    switchToNextDashboard() {
        // Implementation for switching dashboards
        console.log('Switching to next dashboard...');
    }
    
    openContextMenu() {
        // Implementation for context menu
        console.log('Opening context menu...');
    }
    
    handleDoubleTap(e) {
        // Double tap to toggle fullscreen mode
        this.expandCurrentSection();
        this.showGestureResult('⛶ Toggle Fullscreen');
    }
    
    navigateToNextMetric() {
        // Navigate to next metric card
        console.log('Navigating to next metric...');
    }
    
    navigateToPreviousMetric() {
        // Navigate to previous metric card
        console.log('Navigating to previous metric...');
    }
    
    // Enable/Disable Gestures
    enable() {
        this.isEnabled = true;
        console.log('Gesture navigation enabled');
    }
    
    disable() {
        this.isEnabled = false;
        console.log('Gesture navigation disabled');
    }
    
    // Mouse trail for gesture visualization
    showMouseGestureTrail(x, y) {
        const trail = document.createElement('div');
        trail.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            width: 4px;
            height: 4px;
            background: rgba(0, 255, 159, 0.8);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            animation: fadeOut 1s forwards;
        `;
        
        document.body.appendChild(trail);
        
        setTimeout(() => {
            if (trail.parentNode) {
                trail.remove();
            }
        }, 1000);
    }
    
    clearMouseGestureTrail() {
        // Trails are automatically cleared by their timeout
    }
}

// Initialize gesture navigation system
let gestureNav;

document.addEventListener('DOMContentLoaded', function() {
    gestureNav = new GestureNavigationSystem();
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.7; }
        }
        
        @keyframes fadeOut {
            0% { opacity: 1; transform: scale(1); }
            100% { opacity: 0; transform: scale(0.5); }
        }
        
        .qnis-main-zone.expanded-view {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 9998;
            background: rgba(13, 13, 23, 0.98);
            backdrop-filter: blur(20px);
        }
        
        .qnis-sidebar-zone.expanded {
            transform: translateX(0);
        }
        
        .gesture-hint {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 255, 159, 0.1);
            border: 1px solid rgba(0, 255, 159, 0.3);
            color: #00ff9f;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 12px;
            z-index: 10001;
            opacity: 0.8;
        }
    `;
    document.head.appendChild(style);
    
    // Show initial gesture hint
    setTimeout(() => {
        const hint = document.createElement('div');
        hint.className = 'gesture-hint';
        hint.textContent = 'Swipe left/right to navigate • Pinch to zoom • Double tap for fullscreen';
        document.body.appendChild(hint);
        
        setTimeout(() => {
            if (hint.parentNode) {
                hint.remove();
            }
        }, 5000);
    }, 2000);
});

// Export for external use
window.GestureNavigationSystem = GestureNavigationSystem;
window.gestureNav = gestureNav;