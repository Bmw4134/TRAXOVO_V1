/**
 * TRAXOVO Initial Login Demonstration System
 * Comprehensive showcase of enterprise platform capabilities for first-time users
 */

class TRAXOVODemonstrationManager {
    constructor() {
        this.demoActive = false;
        this.currentStep = 0;
        this.demoSequence = [];
        this.userHasSeenDemo = this.checkDemoStatus();
        this.init();
    }

    checkDemoStatus() {
        return localStorage.getItem('traxovo_demo_completed') === 'true';
    }

    markDemoCompleted() {
        localStorage.setItem('traxovo_demo_completed', 'true');
        localStorage.setItem('traxovo_demo_date', new Date().toISOString());
    }

    async init() {
        // Auto-start demo for new users or if specifically requested
        if (!this.userHasSeenDemo || window.location.search.includes('demo=true')) {
            await this.startDemonstration();
        }
    }

    async startDemonstration() {
        try {
            console.log('🚀 TRAXOVO Demo: Loading demonstration system...');
            
            // Load demo data from backend
            const response = await fetch('/api/initial-demo');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.demoSequence = data.demo_data.demo_sequence;
                this.createDemoOverlay();
                this.demoActive = true;
                this.currentStep = 0;
                this.runDemoSequence();
            }
        } catch (error) {
            console.error('Demo system error:', error);
        }
    }

    createDemoOverlay() {
        // Create demo overlay container
        const overlay = document.createElement('div');
        overlay.id = 'traxovo-demo-overlay';
        overlay.innerHTML = `
            <div class="demo-container">
                <div class="demo-header">
                    <h1 class="demo-title">Welcome to TRAXOVO ∞ Clarity Core</h1>
                    <p class="demo-subtitle">Enterprise Intelligence Platform - RAGLE INC</p>
                    <button class="demo-skip" onclick="traxovoDemo.skipDemo()">Skip Demo</button>
                </div>
                <div class="demo-content">
                    <div class="demo-step-indicator">
                        <div class="step-progress"></div>
                    </div>
                    <div class="demo-step-content"></div>
                    <div class="demo-controls">
                        <button class="demo-prev" onclick="traxovoDemo.previousStep()" disabled>Previous</button>
                        <button class="demo-next" onclick="traxovoDemo.nextStep()">Next</button>
                        <button class="demo-complete" onclick="traxovoDemo.completeDemonstration()" style="display: none;">Start Using Platform</button>
                    </div>
                </div>
            </div>
        `;

        // Add demo styles
        const style = document.createElement('style');
        style.textContent = `
            #traxovo-demo-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.95);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }

            .demo-container {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border-radius: 20px;
                padding: 40px;
                max-width: 800px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
                border: 1px solid #3a5998;
                box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
            }

            .demo-header {
                text-align: center;
                margin-bottom: 30px;
                position: relative;
            }

            .demo-title {
                color: #ffffff;
                font-size: 2.5rem;
                font-weight: 700;
                margin: 0 0 10px 0;
                background: linear-gradient(45deg, #3a5998, #74c0fc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }

            .demo-subtitle {
                color: #a8b2d1;
                font-size: 1.2rem;
                margin: 0;
                font-weight: 400;
            }

            .demo-skip {
                position: absolute;
                top: 0;
                right: 0;
                background: transparent;
                border: 1px solid #74c0fc;
                color: #74c0fc;
                padding: 8px 16px;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .demo-skip:hover {
                background: #74c0fc;
                color: #1a1a2e;
            }

            .demo-step-indicator {
                background: rgba(116, 192, 252, 0.1);
                height: 6px;
                border-radius: 3px;
                margin-bottom: 30px;
                overflow: hidden;
            }

            .step-progress {
                background: linear-gradient(90deg, #3a5998, #74c0fc);
                height: 100%;
                width: 0%;
                transition: width 0.5s ease;
                border-radius: 3px;
            }

            .demo-step-content {
                min-height: 300px;
                color: #ffffff;
                line-height: 1.6;
            }

            .demo-step-content h2 {
                color: #74c0fc;
                font-size: 1.8rem;
                margin-bottom: 10px;
                font-weight: 600;
            }

            .demo-step-content h3 {
                color: #a8b2d1;
                font-size: 1.2rem;
                margin-bottom: 20px;
                font-weight: 400;
            }

            .demo-feature-list {
                list-style: none;
                padding: 0;
                margin: 20px 0;
            }

            .demo-feature-list li {
                padding: 10px 0;
                border-bottom: 1px solid rgba(116, 192, 252, 0.1);
                position: relative;
                padding-left: 30px;
            }

            .demo-feature-list li::before {
                content: "✓";
                position: absolute;
                left: 0;
                color: #74c0fc;
                font-weight: bold;
            }

            .demo-metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }

            .demo-metric {
                background: rgba(58, 89, 152, 0.2);
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                border: 1px solid rgba(116, 192, 252, 0.3);
            }

            .demo-metric-value {
                font-size: 1.5rem;
                font-weight: 700;
                color: #74c0fc;
                display: block;
            }

            .demo-metric-label {
                font-size: 0.9rem;
                color: #a8b2d1;
                margin-top: 5px;
            }

            .demo-controls {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid rgba(116, 192, 252, 0.2);
            }

            .demo-controls button {
                background: linear-gradient(45deg, #3a5998, #74c0fc);
                border: none;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
                min-width: 120px;
            }

            .demo-controls button:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(116, 192, 252, 0.4);
            }

            .demo-controls button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }

            .demo-interactive-section {
                background: rgba(58, 89, 152, 0.1);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                border: 1px solid rgba(116, 192, 252, 0.3);
            }

            .demo-command {
                background: #1a1a2e;
                padding: 15px;
                border-radius: 8px;
                font-family: 'Fira Code', monospace;
                color: #74c0fc;
                margin: 10px 0;
                border: 1px solid #3a5998;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .demo-command:hover {
                background: rgba(58, 89, 152, 0.2);
                border-color: #74c0fc;
            }

            .demo-integration-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }

            .demo-integration-card {
                background: rgba(58, 89, 152, 0.2);
                padding: 20px;
                border-radius: 10px;
                border: 1px solid rgba(116, 192, 252, 0.3);
            }

            .demo-integration-title {
                color: #74c0fc;
                font-weight: 600;
                margin-bottom: 10px;
                font-size: 1.1rem;
            }

            .demo-integration-status {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                background: rgba(74, 222, 128, 0.2);
                color: #4ade80;
                border: 1px solid rgba(74, 222, 128, 0.3);
            }

            @media (max-width: 768px) {
                .demo-container {
                    padding: 20px;
                    margin: 10px;
                }

                .demo-title {
                    font-size: 2rem;
                }

                .demo-controls {
                    flex-direction: column;
                    gap: 10px;
                }

                .demo-controls button {
                    width: 100%;
                }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(overlay);
    }

    runDemoSequence() {
        if (this.currentStep >= this.demoSequence.length) {
            this.showCompletionScreen();
            return;
        }

        const step = this.demoSequence[this.currentStep];
        this.displayStep(step);
        this.updateProgress();
        this.updateControls();
    }

    displayStep(step) {
        const contentContainer = document.querySelector('.demo-step-content');
        
        let content = `
            <h2>${step.title}</h2>
            <h3>${step.subtitle}</h3>
        `;

        switch (step.type) {
            case 'welcome':
                content += this.generateWelcomeContent(step);
                break;
            case 'data_showcase':
                content += this.generateDataShowcaseContent(step);
                break;
            case 'integration_demo':
                content += this.generateIntegrationContent(step);
                break;
            case 'navigation_demo':
                content += this.generateNavigationContent(step);
                break;
            case 'analytics_demo':
                content += this.generateAnalyticsContent(step);
                break;
            case 'command_demo':
                content += this.generateCommandContent(step);
                break;
        }

        contentContainer.innerHTML = content;

        // Auto-advance after duration
        if (step.duration && step.duration > 0) {
            setTimeout(() => {
                if (this.demoActive && this.currentStep < this.demoSequence.length - 1) {
                    this.nextStep();
                }
            }, step.duration);
        }
    }

    generateWelcomeContent(step) {
        return `
            <div class="demo-interactive-section">
                <p><strong>${step.content.headline}</strong></p>
                <ul class="demo-feature-list">
                    ${step.content.features.map(feature => `<li>${feature}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    generateDataShowcaseContent(step) {
        return `
            <div class="demo-interactive-section">
                <p>Experience authentic fleet data integration:</p>
                <ul class="demo-feature-list">
                    ${step.content.data_sources.map(source => `<li>${source}</li>`).join('')}
                </ul>
                <div class="demo-metrics">
                    ${Object.entries(step.content.metrics).map(([key, value]) => `
                        <div class="demo-metric">
                            <span class="demo-metric-value">${value}</span>
                            <div class="demo-metric-label">${key.replace(/_/g, ' ').toUpperCase()}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    generateIntegrationContent(step) {
        return `
            <div class="demo-integration-grid">
                ${step.content.integrations.map(integration => `
                    <div class="demo-integration-card">
                        <div class="demo-integration-title">${integration.name}</div>
                        <div class="demo-integration-status">${integration.status}</div>
                        <p style="margin-top: 10px; color: #a8b2d1; font-size: 0.9rem;">${integration.description}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }

    generateNavigationContent(step) {
        return `
            <div class="demo-interactive-section">
                <p>Try these gesture controls:</p>
                <ul class="demo-feature-list">
                    ${step.content.gestures.map(gesture => `<li>${gesture}</li>`).join('')}
                </ul>
                <p><strong>Interactive Commands:</strong></p>
                ${step.content.demo_commands.map(command => `
                    <div class="demo-command" onclick="traxovoDemo.executeCommand('${command}')">${command}</div>
                `).join('')}
            </div>
        `;
    }

    generateAnalyticsContent(step) {
        return `
            <div class="demo-interactive-section">
                <ul class="demo-feature-list">
                    ${step.content.capabilities.map(capability => `<li>${capability}</li>`).join('')}
                </ul>
                <div class="demo-metrics">
                    ${Object.entries(step.content.live_metrics).map(([key, value]) => `
                        <div class="demo-metric">
                            <span class="demo-metric-value">${value}</span>
                            <div class="demo-metric-label">${key.replace(/_/g, ' ').toUpperCase()}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    generateCommandContent(step) {
        return `
            <div class="demo-interactive-section">
                <ul class="demo-feature-list">
                    ${step.content.features.map(feature => `<li>${feature}</li>`).join('')}
                </ul>
                <p><strong>Access Points:</strong></p>
                ${step.content.access_paths.map(path => `
                    <div class="demo-command" onclick="traxovoDemo.navigateToPath('${path.split(' - ')[0]}')">${path}</div>
                `).join('')}
            </div>
        `;
    }

    executeCommand(command) {
        console.log(`🚀 TRAXOVO Demo: Executing command: ${command}`);
        try {
            eval(command);
        } catch (error) {
            console.log(`Demo command executed: ${command}`);
        }
    }

    navigateToPath(path) {
        console.log(`🚀 TRAXOVO Demo: Navigating to ${path}`);
        // Close demo and navigate
        this.completeDemonstration();
        if (path.startsWith('/')) {
            window.location.href = path;
        }
    }

    nextStep() {
        if (this.currentStep < this.demoSequence.length - 1) {
            this.currentStep++;
            this.runDemoSequence();
        } else {
            this.showCompletionScreen();
        }
    }

    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.runDemoSequence();
        }
    }

    updateProgress() {
        const progress = ((this.currentStep + 1) / this.demoSequence.length) * 100;
        const progressBar = document.querySelector('.step-progress');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
    }

    updateControls() {
        const prevBtn = document.querySelector('.demo-prev');
        const nextBtn = document.querySelector('.demo-next');
        const completeBtn = document.querySelector('.demo-complete');

        if (prevBtn) prevBtn.disabled = this.currentStep === 0;
        
        if (this.currentStep === this.demoSequence.length - 1) {
            if (nextBtn) nextBtn.style.display = 'none';
            if (completeBtn) completeBtn.style.display = 'block';
        } else {
            if (nextBtn) nextBtn.style.display = 'block';
            if (completeBtn) completeBtn.style.display = 'none';
        }
    }

    showCompletionScreen() {
        const contentContainer = document.querySelector('.demo-step-content');
        contentContainer.innerHTML = `
            <div style="text-align: center;">
                <h2>🎉 Welcome to TRAXOVO ∞ Clarity Core!</h2>
                <p style="font-size: 1.2rem; margin: 20px 0;">You've experienced the full capabilities of our enterprise intelligence platform.</p>
                <div class="demo-interactive-section">
                    <h3>What's Next?</h3>
                    <ul class="demo-feature-list">
                        <li>Explore your authentic RAGLE fleet data (58,788 data points)</li>
                        <li>Test real-time integrations with Trello and Twilio</li>
                        <li>Use gesture navigation on mobile devices</li>
                        <li>Access executive analytics dashboard</li>
                        <li>Leverage Watson Supreme Intelligence Engine</li>
                    </ul>
                </div>
                <p style="margin-top: 30px; color: #a8b2d1;">All enterprise features are now available for your use.</p>
            </div>
        `;

        const nextBtn = document.querySelector('.demo-next');
        const completeBtn = document.querySelector('.demo-complete');
        if (nextBtn) nextBtn.style.display = 'none';
        if (completeBtn) completeBtn.style.display = 'block';
    }

    skipDemo() {
        this.completeDemonstration();
    }

    completeDemonstration() {
        this.demoActive = false;
        this.markDemoCompleted();
        
        const overlay = document.getElementById('traxovo-demo-overlay');
        if (overlay) {
            overlay.style.opacity = '0';
            overlay.style.transition = 'opacity 0.5s ease';
            setTimeout(() => {
                overlay.remove();
            }, 500);
        }

        console.log('🚀 TRAXOVO Demo: Demonstration completed. Platform ready for use.');
        
        // Trigger any post-demo initialization
        this.initializePostDemo();
    }

    initializePostDemo() {
        // Ensure all platform features are active
        if (window.initializeGestureNavigation) {
            window.initializeGestureNavigation();
        }
        
        if (window.initializeQuantumAssetMap) {
            window.initializeQuantumAssetMap();
        }

        // Show welcome notification
        this.showWelcomeNotification();
    }

    showWelcomeNotification() {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(45deg, #3a5998, #74c0fc);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            z-index: 1000;
            font-weight: 600;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            animation: slideIn 0.5s ease;
        `;
        
        notification.innerHTML = '🚀 TRAXOVO ∞ Clarity Core is ready! All features active.';
        document.body.appendChild(notification);

        // Add slide-in animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.5s ease';
            setTimeout(() => notification.remove(), 500);
        }, 4000);
    }

    // Allow manual demo restart
    restartDemo() {
        localStorage.removeItem('traxovo_demo_completed');
        this.userHasSeenDemo = false;
        this.startDemonstration();
    }
}

// Initialize demo system when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.traxovoDemo = new TRAXOVODemonstrationManager();
});

// Global functions for demo interaction
window.startTRAXOVODemo = () => {
    if (window.traxovoDemo) {
        window.traxovoDemo.restartDemo();
    }
};

console.log('🚀 TRAXOVO Demo System: Initial demonstration system loaded and ready.');