// TRAXOVO Playful Loading Animations with Thematic Characters
// Construction-themed animated characters for fleet management platform

(function() {
    'use strict';
    
    class TRAXOVOLoadingAnimations {
        constructor() {
            this.animations = {
                excavator: this.createExcavatorAnimation,
                dumptruck: this.createDumpTruckAnimation,
                bulldozer: this.createBulldozerAnimation,
                crane: this.createCraneAnimation,
                workercrew: this.createWorkerCrewAnimation,
                concrete: this.createConcreteMixerAnimation
            };
            
            this.currentAnimation = null;
            this.animationContainer = null;
            this.loadingMessages = [
                "Loading your Fort Worth fleet data...",
                "Synchronizing construction zones...",
                "Calculating equipment efficiency...",
                "Processing attendance records...",
                "Analyzing job site productivity...",
                "Updating asset locations...",
                "Preparing executive dashboard...",
                "Optimizing resource allocation..."
            ];
            
            this.initializeAnimationSystem();
        }
        
        initializeAnimationSystem() {
            this.createAnimationContainer();
            this.setupAnimationTriggers();
            console.log('TRAXOVO Loading Animations: INITIALIZED');
        }
        
        createAnimationContainer() {
            this.animationContainer = document.createElement('div');
            this.animationContainer.id = 'traxovo-loading-overlay';
            this.animationContainer.className = 'traxovo-loading-overlay hidden';
            this.animationContainer.innerHTML = `
                <div class="loading-backdrop"></div>
                <div class="loading-content">
                    <div class="loading-animation-area"></div>
                    <div class="loading-message">
                        <h3 class="loading-title">TRAXOVO Fleet Intelligence</h3>
                        <p class="loading-text">Loading...</p>
                        <div class="loading-progress">
                            <div class="progress-bar"></div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(this.animationContainer);
        }
        
        setupAnimationTriggers() {
            // Override fetch to show loading animations
            const originalFetch = window.fetch;
            window.fetch = async (...args) => {
                const shouldShowLoading = this.shouldShowLoadingForRequest(args[0]);
                
                if (shouldShowLoading) {
                    this.showRandomAnimation();
                }
                
                try {
                    const response = await originalFetch(...args);
                    
                    if (shouldShowLoading) {
                        // Add minimum display time for better UX
                        await new Promise(resolve => setTimeout(resolve, 1200));
                        this.hideAnimation();
                    }
                    
                    return response;
                } catch (error) {
                    if (shouldShowLoading) {
                        this.hideAnimation();
                    }
                    throw error;
                }
            };
            
            // Manual triggers for specific actions
            window.showTRAXOVOLoading = (animationType) => {
                this.showAnimation(animationType);
            };
            
            window.hideTRAXOVOLoading = () => {
                this.hideAnimation();
            };
        }
        
        shouldShowLoadingForRequest(url) {
            const loadingTriggers = [
                '/api/fort-worth-assets',
                '/api/attendance-data',
                '/api/quantum-consciousness',
                '/api/generate-daily-report',
                '/dashboard',
                '/fleet-map',
                '/asset-manager'
            ];
            
            return loadingTriggers.some(trigger => 
                typeof url === 'string' && url.includes(trigger)
            );
        }
        
        showRandomAnimation() {
            const animationTypes = Object.keys(this.animations);
            const randomType = animationTypes[Math.floor(Math.random() * animationTypes.length)];
            this.showAnimation(randomType);
        }
        
        showAnimation(animationType = 'excavator') {
            if (this.currentAnimation) {
                this.hideAnimation();
            }
            
            const animationFunction = this.animations[animationType];
            if (!animationFunction) {
                animationType = 'excavator'; // fallback
            }
            
            this.currentAnimation = animationType;
            this.animationContainer.classList.remove('hidden');
            
            // Clear previous animation
            const animationArea = this.animationContainer.querySelector('.loading-animation-area');
            animationArea.innerHTML = '';
            
            // Create new animation
            this.animations[animationType].call(this, animationArea);
            
            // Update loading message
            this.updateLoadingMessage();
            
            // Start progress animation
            this.animateProgress();
        }
        
        hideAnimation() {
            if (this.animationContainer) {
                this.animationContainer.classList.add('hidden');
                this.currentAnimation = null;
                
                // Clean up animation area
                const animationArea = this.animationContainer.querySelector('.loading-animation-area');
                if (animationArea) {
                    animationArea.innerHTML = '';
                }
                
                // Reset progress bar
                const progressBar = this.animationContainer.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = '0%';
                }
            }
        }
        
        updateLoadingMessage() {
            const messageElement = this.animationContainer.querySelector('.loading-text');
            const randomMessage = this.loadingMessages[
                Math.floor(Math.random() * this.loadingMessages.length)
            ];
            messageElement.textContent = randomMessage;
        }
        
        animateProgress() {
            const progressBar = this.animationContainer.querySelector('.progress-bar');
            let progress = 0;
            
            const progressInterval = setInterval(() => {
                progress += Math.random() * 15 + 5; // Random increment between 5-20%
                
                if (progress >= 100) {
                    progress = 100;
                    clearInterval(progressInterval);
                }
                
                progressBar.style.width = `${progress}%`;
            }, 200);
        }
        
        createExcavatorAnimation(container) {
            container.innerHTML = `
                <div class="excavator-scene">
                    <div class="excavator">
                        <div class="excavator-body">
                            <div class="excavator-cab"></div>
                            <div class="excavator-arm">
                                <div class="excavator-boom"></div>
                                <div class="excavator-bucket"></div>
                            </div>
                        </div>
                        <div class="excavator-tracks">
                            <div class="track left-track"></div>
                            <div class="track right-track"></div>
                        </div>
                    </div>
                    <div class="dirt-pile">
                        <div class="dirt-particle"></div>
                        <div class="dirt-particle"></div>
                        <div class="dirt-particle"></div>
                    </div>
                    <div class="ground-line"></div>
                </div>
            `;
        }
        
        createDumpTruckAnimation(container) {
            container.innerHTML = `
                <div class="dumptruck-scene">
                    <div class="dumptruck">
                        <div class="truck-cab"></div>
                        <div class="truck-bed">
                            <div class="cargo">
                                <div class="rock"></div>
                                <div class="rock"></div>
                                <div class="rock"></div>
                            </div>
                        </div>
                        <div class="truck-wheels">
                            <div class="wheel front-wheel"></div>
                            <div class="wheel rear-wheel"></div>
                        </div>
                    </div>
                    <div class="road"></div>
                    <div class="dust-cloud">
                        <div class="dust-particle"></div>
                        <div class="dust-particle"></div>
                        <div class="dust-particle"></div>
                    </div>
                </div>
            `;
        }
        
        createBulldozerAnimation(container) {
            container.innerHTML = `
                <div class="bulldozer-scene">
                    <div class="bulldozer">
                        <div class="dozer-body">
                            <div class="dozer-cab"></div>
                            <div class="dozer-blade"></div>
                        </div>
                        <div class="dozer-tracks">
                            <div class="track-segment"></div>
                            <div class="track-segment"></div>
                            <div class="track-segment"></div>
                        </div>
                    </div>
                    <div class="earth-being-moved">
                        <div class="earth-chunk"></div>
                        <div class="earth-chunk"></div>
                    </div>
                    <div class="terrain"></div>
                </div>
            `;
        }
        
        createCraneAnimation(container) {
            container.innerHTML = `
                <div class="crane-scene">
                    <div class="crane">
                        <div class="crane-base"></div>
                        <div class="crane-mast"></div>
                        <div class="crane-jib">
                            <div class="crane-trolley">
                                <div class="crane-hook">
                                    <div class="crane-load"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="building-frame">
                        <div class="beam horizontal"></div>
                        <div class="beam vertical"></div>
                        <div class="beam horizontal"></div>
                    </div>
                    <div class="construction-site-base"></div>
                </div>
            `;
        }
        
        createWorkerCrewAnimation(container) {
            container.innerHTML = `
                <div class="worker-scene">
                    <div class="workers">
                        <div class="worker worker-1">
                            <div class="worker-head"></div>
                            <div class="worker-body"></div>
                            <div class="worker-tools">
                                <div class="tool"></div>
                            </div>
                        </div>
                        <div class="worker worker-2">
                            <div class="worker-head"></div>
                            <div class="worker-body"></div>
                            <div class="worker-tools">
                                <div class="tool"></div>
                            </div>
                        </div>
                        <div class="worker worker-3">
                            <div class="worker-head"></div>
                            <div class="worker-body"></div>
                            <div class="worker-tools">
                                <div class="tool"></div>
                            </div>
                        </div>
                    </div>
                    <div class="work-materials">
                        <div class="material-stack"></div>
                        <div class="material-stack"></div>
                    </div>
                    <div class="work-area"></div>
                </div>
            `;
        }
        
        createConcreteMixerAnimation(container) {
            container.innerHTML = `
                <div class="mixer-scene">
                    <div class="concrete-mixer">
                        <div class="mixer-cab"></div>
                        <div class="mixer-drum">
                            <div class="drum-stripes">
                                <div class="stripe"></div>
                                <div class="stripe"></div>
                                <div class="stripe"></div>
                            </div>
                        </div>
                        <div class="mixer-chute">
                            <div class="concrete-flow">
                                <div class="concrete-blob"></div>
                                <div class="concrete-blob"></div>
                            </div>
                        </div>
                        <div class="mixer-wheels">
                            <div class="wheel"></div>
                            <div class="wheel"></div>
                            <div class="wheel"></div>
                        </div>
                    </div>
                    <div class="pour-area">
                        <div class="concrete-puddle"></div>
                    </div>
                </div>
            `;
        }
    }
    
    // Initialize when DOM is ready
    function initializeLoadingAnimations() {
        window.traxovoLoadingAnimations = new TRAXOVOLoadingAnimations();
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeLoadingAnimations);
    } else {
        initializeLoadingAnimations();
    }
    
    // Export for external use
    window.TRAXOVOLoadingAnimations = TRAXOVOLoadingAnimations;
})();