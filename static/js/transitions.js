* Smooth Page Transitions
*
* This script provides smooth transitions between pages and enhances
* the UI with animations for a more polished user experience.
*/
document.addEventListener('DOMContentLoaded', function() {
initPageTransitions();
initCardAnimations();
initNavigationHighlighting();
});
* Initialize page transition effects
*/
function initPageTransitions() {
const contentSections = document.querySelectorAll('.page-transition-container > div, .page-transition-container > section');
contentSections.forEach(section => {
if (!section.classList.contains('fade-transition') &&
!section.classList.contains('slide-transition')) {
section.classList.add('slide-transition');
}
});
const pageLinks = document.querySelectorAll('a:not([target="_blank"]):not([href^="#"]):not([href^="javascript"])');
pageLinks.forEach(link => {
link.addEventListener('click', function(e) {
if (e.metaKey || e.ctrlKey || e.shiftKey || this.getAttribute('target') === '_blank' ||
this.getAttribute('href').indexOf('://') > -1) {
return;
}
if (this.getAttribute('href').charAt(0) === '/' ||
this.getAttribute('href').charAt(0) === '.' ||
this.getAttribute('href').indexOf('://') === -1) {
e.preventDefault();
document.querySelector('.page-transition-container').style.opacity = 0;
document.querySelector('.page-transition-container').style.transition = 'opacity 0.3s ease';
setTimeout(() => {
window.location.href = this.getAttribute('href');
}, 300);
}
});
});
}
* Initialize card hover animations
*/
function initCardAnimations() {
const cards = document.querySelectorAll('.card:not(.hover-card)');
cards.forEach(card => {
if (!(card.parentElement && card.parentElement.classList.contains('no-animation')) &&
!card.classList.contains('no-animation')) {
card.classList.add('scale-transition');
}
});
const progressBars = document.querySelectorAll('.progress');
progressBars.forEach(progress => {
progress.classList.add('animated-progress');
});
}
* Initialize navigation highlighting for current page
*/
function initNavigationHighlighting() {
const currentPath = window.location.pathname;
const navLinks = document.querySelectorAll('.navbar .nav-link');
navLinks.forEach(link => {
const href = link.getAttribute('href');
if (href === currentPath ||
(href !== '/' && currentPath.startsWith(href))) {
link.classList.add('active');
let dropdown = link.parentElement;
while (dropdown && !dropdown.classList.contains('dropdown')) {
    dropdown = dropdown.parentElement;
}
if (dropdown) {
const dropdownToggle = dropdown.querySelector('.dropdown-toggle');
if (dropdownToggle) {
dropdownToggle.classList.add('active');
}
}
}
});
}