// Smooth Transition Effects JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeTransitions();
    initializePageAnimations();
    initializeCounterAnimations();
    initializeScrollAnimations();
});

function initializeTransitions() {
    // Add page enter animation to main content
    const mainContent = document.querySelector('main') || document.body;
    if (mainContent) {
        mainContent.classList.add('page-enter');
        setTimeout(() => {
            mainContent.classList.add('page-enter-active');
        }, 50);
    }

    // Add section animations
    const sections = document.querySelectorAll('.dashboard-section, .metric-grid, .billing-grid, .nav-grid');
    sections.forEach(section => {
        section.classList.add('dashboard-section');
    });
}

function initializePageAnimations() {
    // Stagger card animations
    const cards = document.querySelectorAll('.metric-card, .billing-card, .fleet-card, .nav-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.4s ease-out';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 + (index * 100));
    });
}

function initializeCounterAnimations() {
    // Animate numbers on page load
    const numberElements = document.querySelectorAll('.metric-value, .amount, .revenue-amount');
    
    numberElements.forEach(element => {
        const text = element.textContent;
        const number = parseFloat(text.replace(/[$,]/g, ''));
        
        if (!isNaN(number) && number > 0) {
            animateNumber(element, 0, number, 1500);
        }
    });
}

function animateNumber(element, start, end, duration) {
    const originalText = element.textContent;
    const isMoneyFormat = originalText.includes('$');
    const hasCommas = originalText.includes(',');
    
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Use easing function for smooth animation
        const easeOutCubic = 1 - Math.pow(1 - progress, 3);
        const currentValue = start + (end - start) * easeOutCubic;
        
        let displayValue = Math.round(currentValue);
        
        if (isMoneyFormat) {
            displayValue = '$' + displayValue.toLocaleString();
        } else if (hasCommas) {
            displayValue = displayValue.toLocaleString();
        }
        
        element.textContent = displayValue;
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        } else {
            element.textContent = originalText; // Ensure final value is exact
        }
    }
    
    requestAnimationFrame(updateNumber);
}

function initializeScrollAnimations() {
    // Intersection Observer for scroll-triggered animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements that should animate on scroll
    const scrollElements = document.querySelectorAll('.billing-card, .fleet-card, .revenue-card');
    scrollElements.forEach(el => observer.observe(el));
}

// Navigation transitions
function initializeNavTransitions() {
    const navLinks = document.querySelectorAll('.nav-links a, .nav-card');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Add click ripple effect
            const ripple = document.createElement('span');
            ripple.classList.add('nav-ripple');
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

// Tab switching animations
function switchTab(targetId) {
    const allTabs = document.querySelectorAll('.tab-content');
    const targetTab = document.getElementById(targetId);
    
    if (!targetTab) return;
    
    // Fade out current tabs
    allTabs.forEach(tab => {
        tab.classList.remove('active');
        tab.style.opacity = '0';
        tab.style.transform = 'translateX(-20px)';
    });
    
    // Fade in target tab
    setTimeout(() => {
        targetTab.classList.add('active');
        targetTab.style.opacity = '1';
        targetTab.style.transform = 'translateX(0)';
    }, 150);
}

// Modal animations
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        setTimeout(() => {
            modal.classList.add('show');
        }, 50);
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
}

// Loading state management
function setLoadingState(element, isLoading) {
    if (isLoading) {
        element.classList.add('loading-state');
    } else {
        element.classList.remove('loading-state');
    }
}

// Page transition on navigation
function transitionToPage(url) {
    const mainContent = document.querySelector('main') || document.body;
    
    // Fade out current page
    mainContent.style.opacity = '0';
    mainContent.style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        window.location.href = url;
    }, 300);
}

// Initialize navigation transitions when DOM is ready
document.addEventListener('DOMContentLoaded', initializeNavTransitions);

// CSS for additional animations
const additionalCSS = `
.nav-ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255,255,255,0.3);
    transform: scale(0);
    animation: ripple 0.6s linear;
    pointer-events: none;
}

@keyframes ripple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

.animate-in {
    animation: slideInUp 0.6s ease-out;
}

@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
`;

// Inject additional CSS
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style);