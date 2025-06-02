* Smart UI Resizer - Automatic viewport optimization for TRAXOVO Fleet Management
* Detects device type and optimizes UI/UX accordingly
*/
class SmartUIResizer {
constructor() {
this.init();
this.setupEventListeners();
}
init() {
this.detectDevice();
this.optimizeViewport();
this.adjustUIElements();
this.enableMobileGestures();
}
detectDevice() {
const width = window.innerWidth;
const height = window.innerHeight;
const userAgent = navigator.userAgent;
this.deviceInfo = {
width: width,
height: height,
isMobile: width <= 768,
isTablet: width > 768 && width <= 1024,
isDesktop: width > 1024,
isLandscape: width > height,
isTouch: 'ontouchstart' in window,
pixelRatio: window.devicePixelRatio || 1
};
document.body.className = document.body.className.replace(/device-\w+/g, '');
document.body.classList.add(
this.deviceInfo.isMobile ? 'device-mobile' :
this.deviceInfo.isTablet ? 'device-tablet' : 'device-desktop'
);
if (this.deviceInfo.isTouch) document.body.classList.add('device-touch');
if (this.deviceInfo.isLandscape) document.body.classList.add('device-landscape');
}
optimizeViewport() {
let viewport = document.querySelector('meta[name="viewport"]');
if (!viewport) {
viewport = document.createElement('meta');
viewport.name = 'viewport';
document.head.appendChild(viewport);
}
if (this.deviceInfo.isMobile) {
viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
} else {
viewport.content = 'width=device-width, initial-scale=1.0';
}
}
adjustUIElements() {
this.optimizeTableViews();
this.adjustButtonSizes();
this.optimizeNavigation();
this.adjustFontSizes();
this.optimizeCards();
}
optimizeTableViews() {
const tables = document.querySelectorAll('table');
tables.forEach(table => {
if (this.deviceInfo.isMobile) {
if (!table.parentElement&&.parentElement.querySelector('.table-responsive')) {
const wrapper = document.createElement('div');
wrapper.className = 'table-responsive';
table.parentNode.insertBefore(wrapper, table);
wrapper.appendChild(table);
}
this.addSwipeIndicator(table);
}
});
}
adjustButtonSizes() {
const buttons = document.querySelectorAll('.btn');
buttons.forEach(btn => {
if (this.deviceInfo.isMobile && this.deviceInfo.isTouch) {
btn.style.minHeight = '44px';
btn.style.minWidth = '44px';
if (!btn.classList.contains('btn-sm')) {
btn.classList.add('btn-lg');
}
}
});
}
optimizeNavigation() {
const navbar = document.querySelector('.navbar');
if (navbar && this.deviceInfo.isMobile) {
navbar.classList.add('navbar-expand-lg');
const toggle = navbar.querySelector('.navbar-toggler');
if (toggle) {
toggle.style.minHeight = '44px';
toggle.style.minWidth = '44px';
}
}
}
adjustFontSizes() {
if (this.deviceInfo.isMobile) {
document.documentElement.style.setProperty('--mobile-font-scale', '1.1');
const style = document.createElement('style');
style.textContent = `
@media (max-width: 768px) {
.table th, .table td { font-size: 0.9rem; }
.card-title { font-size: 1.1rem; }
.btn { font-size: 0.95rem; }
h1 { font-size: 1.8rem; }
h2 { font-size: 1.5rem; }
h3 { font-size: 1.3rem; }
}
`;
document.head.appendChild(style);
}
}
optimizeCards() {
const cards = document.querySelectorAll('.card');
cards.forEach(card => {
if (this.deviceInfo.isMobile) {
card.classList.add('mb-3');
const cardBody = card.querySelector('.card-body');
if (cardBody) {
cardBody.classList.add('p-2');
}
}
});
}
addSwipeIndicator(table) {
if (table.querySelector('.swipe-indicator')) return;
const indicator = document.createElement('div');
indicator.className = 'swipe-indicator';
indicator.innerHTML = '← Swipe to see more →';
indicator.style.cssText = `
text-align: center;
color: #6c757d;
font-size: 0.8rem;
padding: 5px;
background: #f8f9fa;
border-bottom: 1px solid #dee2e6;
`;
table.parentNode.insertBefore(indicator, table);
table.parentNode.addEventListener('scroll', () => {
indicator.style.display = 'none';
}, { once: true });
}
enableMobileGestures() {
if (!this.deviceInfo.isTouch) return;

let startY = 0;
let startX = 0;
let currentY = 0;
let currentX = 0;
let isPulling = false;
let isScrolling = false;

// Pull to refresh
document.addEventListener('touchstart', (e) => {
startY = e.touches[0].pageY;
startX = e.touches[0].pageX;
isScrolling = false;
}, { passive: true });

document.addEventListener('touchmove', (e) => {
currentY = e.touches[0].pageY;
currentX = e.touches[0].pageX;
const deltaY = currentY - startY;
const deltaX = currentX - startX;

// Determine scroll direction
if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > 10) {
isScrolling = true;
}

// Pull to refresh - only at top of page
if (window.scrollY === 0 && deltaY > 50 && !isPulling && isScrolling) {
isPulling = true;
this.showPullToRefresh();
}
}, { passive: true });

document.addEventListener('touchend', () => {
if (isPulling) {
isPulling = false;
this.hidePullToRefresh();
if (typeof refreshData === 'function') {
refreshData();
}
}
isScrolling = false;
}, { passive: true });

// Prevent zoom on double tap for form elements
document.addEventListener('touchend', (e) => {
if (e.target.matches('input, select, textarea, button')) {
e.preventDefault();
e.target.click();
}
}, { passive: false });

// Improve focus handling on mobile
document.addEventListener('focusin', (e) => {
if (this.deviceInfo.isMobile && e.target.matches('input, textarea, select')) {
setTimeout(() => {
e.target.scrollIntoView({ 
behavior: 'smooth', 
block: 'center',
inline: 'nearest'
});
}, 300);
}
});
}
showPullToRefresh() {
let indicator = document.getElementById('pull-refresh-indicator');
if (!indicator) {
indicator = document.createElement('div');
indicator.id = 'pull-refresh-indicator';
indicator.innerHTML = '↓ Release to refresh';
indicator.style.cssText = `
position: fixed;
top: 0;
left: 0;
right: 0;
background: #007bff;
color: white;
text-align: center;
padding: 10px;
z-index: 9999;
transform: translateY(-100%);
transition: transform 0.3s ease;
`;
document.body.appendChild(indicator);
}
setTimeout(() => {
indicator.style.transform = 'translateY(0)';
}, 10);
}
hidePullToRefresh() {
const indicator = document.getElementById('pull-refresh-indicator');
if (indicator) {
indicator.style.transform = 'translateY(-100%)';
setTimeout(() => {
indicator.remove();
}, 300);
}
}
setupEventListeners() {
let resizeTimer;
window.addEventListener('resize', () => {
clearTimeout(resizeTimer);
resizeTimer = setTimeout(() => {
this.detectDevice();
this.adjustUIElements();
}, 250);
});
window.addEventListener('orientationchange', () => {
setTimeout(() => {
this.detectDevice();
this.adjustUIElements();
}, 500);
});
if (this.deviceInfo.isTouch) {
document.addEventListener('focusin', (e) => {
if (e.target.matches('input, textarea, select')) {
setTimeout(() => {
e.target.scrollIntoView({ behavior: 'smooth', block: 'center' });
}, 300);
}
});
}
}
optimize() {
this.init();
}
}
if (document.readyState === 'loading') {
document.addEventListener('DOMContentLoaded', () => {
window.smartUIResizer = new SmartUIResizer();
});
} else {
window.smartUIResizer = new SmartUIResizer();
}
const mobileCSS = `
<style>
@media (max-width: 768px) {
.container { padding-left: 10px; padding-right: 10px; }
.card { margin-bottom: 1rem; }
.btn-group .btn { margin-bottom: 5px; }
.table-responsive { border: none; }
.navbar-brand { font-size: 1rem; }
.btn, .form-control, .dropdown-toggle {
min-height: 44px;
padding: 10px 15px;
}
.form-row .col, .row .col {
margin-bottom: 10px;
}
.modal-dialog {
margin: 10px;
max-width: calc(100% - 20px);
}
.badge {
font-size: 0.8rem;
padding: 4px 8px;
}
}
@media (max-width: 576px) {
.container-fluid { padding: 5px; }
.card-body { padding: 0.75rem; }
.btn-group { flex-direction: column; }
.btn-group .btn { width: 100%; margin-bottom: 5px; }
}
.device-touch .btn:hover {
transform: scale(1.02);
transition: transform 0.1s ease;
}
.device-touch .card:active {
transform: scale(0.98);
transition: transform 0.1s ease;
}
.device-landscape.device-mobile .container {
max-width: 100%;
}
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
.table th, .table td {
border-width: 0.5px;
}
}
</style>
`;
document.head.insertAdjacentHTML('beforeend', mobileCSS);