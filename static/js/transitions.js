/**
 * Smooth Page Transitions
 * 
 * This script provides smooth transitions between pages and enhances
 * the UI with animations for a more polished user experience.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize page transitions
  initPageTransitions();
  
  // Add hover animations to cards
  initCardAnimations();
  
  // Handle navigation animations
  initNavigationHighlighting();
});

/**
 * Initialize page transition effects
 */
function initPageTransitions() {
  // Add slide-in animation to main content sections
  const contentSections = document.querySelectorAll('.page-transition-container > div, .page-transition-container > section');
  
  contentSections.forEach(section => {
    if (!section.classList.contains('fade-transition') && 
        !section.classList.contains('slide-transition')) {
      section.classList.add('slide-transition');
    }
  });
  
  // Add transition effect to page navigation
  const pageLinks = document.querySelectorAll('a:not([target="_blank"]):not([href^="#"]):not([href^="javascript"])');
  
  pageLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      // Don't handle if modifier keys are pressed or it's an external link
      if (e.metaKey || e.ctrlKey || e.shiftKey || this.getAttribute('target') === '_blank' || 
          this.getAttribute('href').indexOf('://') > -1) {
        return;
      }
      
      // Only handle internal page links
      if (this.getAttribute('href').charAt(0) === '/' || 
          this.getAttribute('href').charAt(0) === '.' || 
          this.getAttribute('href').indexOf('://') === -1) {
        
        e.preventDefault();
        
        // Fade out current page
        document.querySelector('.page-transition-container').style.opacity = 0;
        document.querySelector('.page-transition-container').style.transition = 'opacity 0.3s ease';
        
        // Navigate after animation completes
        setTimeout(() => {
          window.location.href = this.getAttribute('href');
        }, 300);
      }
    });
  });
}

/**
 * Initialize card hover animations
 */
function initCardAnimations() {
  // Add hover animations to cards that don't already have them
  const cards = document.querySelectorAll('.card:not(.hover-card)');
  
  cards.forEach(card => {
    // Don't add to special-purpose cards
    if (!card.closest('.no-animation') && 
        !card.classList.contains('no-animation')) {
      card.classList.add('scale-transition');
    }
  });
  
  // Initialize any progress bars with animation
  const progressBars = document.querySelectorAll('.progress');
  progressBars.forEach(progress => {
    progress.classList.add('animated-progress');
  });
}

/**
 * Initialize navigation highlighting for current page
 */
function initNavigationHighlighting() {
  // Highlight current page in navigation
  const currentPath = window.location.pathname;
  
  const navLinks = document.querySelectorAll('.navbar .nav-link');
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    
    // Check if this is the current page or section
    if (href === currentPath || 
        (href !== '/' && currentPath.startsWith(href))) {
      link.classList.add('active');
      
      // If it's in a dropdown, highlight the parent too
      const dropdown = link.closest('.dropdown');
      if (dropdown) {
        const dropdownToggle = dropdown.querySelector('.dropdown-toggle');
        if (dropdownToggle) {
          dropdownToggle.classList.add('active');
        }
      }
    }
  });
}