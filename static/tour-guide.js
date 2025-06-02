// TRAXOVO Tour Guide - Enterprise Platform Navigation
class TourGuide {
    constructor() {
        this.currentStep = 0;
        this.isActive = false;
        this.init();
    }
    
    init() {
        // Tour guide functionality for new users
        if (localStorage.getItem('traxovo_tour_completed') !== 'true') {
            this.createTourButton();
        }
    }
    
    createTourButton() {
        const tourBtn = document.createElement('button');
        tourBtn.innerHTML = 'Take Tour';
        tourBtn.className = 'btn btn-outline-primary btn-sm tour-btn';
        tourBtn.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1000;';
        tourBtn.addEventListener('click', () => this.startTour());
        document.body.appendChild(tourBtn);
    }
    
    startTour() {
        this.isActive = true;
        this.showStep(0);
    }
    
    showStep(stepIndex) {
        const steps = [
            { element: '.sidebar', text: 'Navigate between different modules using this sidebar' },
            { element: '.metric-card', text: 'View real-time fleet metrics and performance data' },
            { element: '.btn-module', text: 'Access detailed reports and analytics' }
        ];
        
        if (stepIndex >= steps.length) {
            this.endTour();
            return;
        }
        
        const step = steps[stepIndex];
        const element = document.querySelector(step.element);
        
        if (element) {
            this.highlightElement(element, step.text, stepIndex);
        } else {
            this.showStep(stepIndex + 1);
        }
    }
    
    highlightElement(element, text, stepIndex) {
        const overlay = document.createElement('div');
        overlay.className = 'tour-overlay';
        overlay.innerHTML = `
            <div class="tour-tooltip">
                <p>${text}</p>
                <button onclick="tourGuide.nextStep()" class="btn btn-primary btn-sm">Next</button>
                <button onclick="tourGuide.endTour()" class="btn btn-secondary btn-sm">Skip</button>
            </div>
        `;
        document.body.appendChild(overlay);
        
        element.style.position = 'relative';
        element.style.zIndex = '1001';
    }
    
    nextStep() {
        this.clearHighlight();
        this.currentStep++;
        this.showStep(this.currentStep);
    }
    
    endTour() {
        this.clearHighlight();
        this.isActive = false;
        localStorage.setItem('traxovo_tour_completed', 'true');
        const tourBtn = document.querySelector('.tour-btn');
        if (tourBtn) tourBtn.remove();
    }
    
    clearHighlight() {
        const overlay = document.querySelector('.tour-overlay');
        if (overlay) overlay.remove();
    }
}

const tourGuide = new TourGuide();