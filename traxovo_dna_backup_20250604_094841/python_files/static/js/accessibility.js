/**
 * TRAXOVO Accessibility Enhancement Module
 * Provides comprehensive accessibility features including high contrast,
 * screen reader support, and keyboard navigation
 */
class TRAXOVOAccessibility {
constructor() {
this.settings = {
highContrast: false,
fontSize: 'normal',
reducedMotion: false,
keyboardNav: false,
dyslexiaFont: false,
largeCursor: false
};
this.init();
this.loadSettings();
this.createAccessibilityToolbar();
this.setupKeyboardNavigation();
this.setupScreenReaderSupport();
}
init() {
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
this.settings.reducedMotion = true;
document.body.classList.add('reduced-motion');
}
if (window.matchMedia('(prefers-contrast: high)').matches) {
this.settings.highContrast = true;
document.body.classList.add('high-contrast');
}
window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
this.settings.reducedMotion = e.matches;
this.toggleReducedMotion(e.matches);
});
window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
this.settings.highContrast = e.matches;
this.toggleHighContrast(e.matches);
});
}
createAccessibilityToolbar() {
const toolbar = document.createElement('div');
toolbar.className = 'accessibility-toolbar';
toolbar.setAttribute('role', 'toolbar');
toolbar.setAttribute('aria-label', 'Accessibility Tools');
toolbar.innerHTML = `
<button class="toggle-btn" aria-label="Toggle accessibility toolbar" title="Toggle accessibility toolbar">
<i class="fas fa-universal-access" aria-hidden="true"></i>
</button>
<div class="toolbar-content">
<div style="margin-bottom: 10px;">
<strong>Accessibility</strong>
</div>
<button id="toggle-contrast" aria-label="Toggle high contrast mode" title="High Contrast">
<i class="fas fa-adjust" aria-hidden="true"></i> Contrast
</button>
<button id="increase-font" aria-label="Increase font size" title="Increase Font Size">
<i class="fas fa-plus" aria-hidden="true"></i> Font+
</button>
<button id="decrease-font" aria-label="Decrease font size" title="Decrease Font Size">
<i class="fas fa-minus" aria-hidden="true"></i> Font-
</button>
<button id="toggle-motion" aria-label="Toggle reduced motion" title="Reduce Motion">
<i class="fas fa-stop" aria-hidden="true"></i> Motion
</button>
<button id="toggle-dyslexia" aria-label="Toggle dyslexia-friendly font" title="Dyslexia Font">
<i class="fas fa-font" aria-hidden="true"></i> Dyslexia
</button>
<button id="toggle-cursor" aria-label="Toggle large cursor" title="Large Cursor">
<i class="fas fa-mouse-pointer" aria-hidden="true"></i> Cursor
</button>
<button id="toggle-keyboard-nav" aria-label="Toggle keyboard navigation indicators" title="Keyboard Navigation">
<i class="fas fa-keyboard" aria-hidden="true"></i> Keyboard
</button>
<button id="reset-accessibility" aria-label="Reset all accessibility settings" title="Reset All">
<i class="fas fa-undo" aria-hidden="true"></i> Reset
</button>
</div>
`;
document.body.appendChild(toolbar);
this.setupToolbarEvents();
}
setupToolbarEvents() {
document.querySelector('.toggle-btn').addEventListener('click', () => {
const toolbar = document.querySelector('.accessibility-toolbar');
toolbar.classList.toggle('collapsed');
});
document.getElementById('toggle-contrast').addEventListener('click', () => {
this.settings.highContrast = !this.settings.highContrast;
this.toggleHighContrast(this.settings.highContrast);
this.saveSettings();
this.announceChange(`High contrast ${this.settings.highContrast ? 'enabled' : 'disabled'}`);
});
document.getElementById('increase-font').addEventListener('click', () => {
this.changeFontSize('increase');
});
document.getElementById('decrease-font').addEventListener('click', () => {
this.changeFontSize('decrease');
});
document.getElementById('toggle-motion').addEventListener('click', () => {
this.settings.reducedMotion = !this.settings.reducedMotion;
this.toggleReducedMotion(this.settings.reducedMotion);
this.saveSettings();
this.announceChange(`Reduced motion ${this.settings.reducedMotion ? 'enabled' : 'disabled'}`);
});
document.getElementById('toggle-dyslexia').addEventListener('click', () => {
this.settings.dyslexiaFont = !this.settings.dyslexiaFont;
this.toggleDyslexiaFont(this.settings.dyslexiaFont);
this.saveSettings();
this.announceChange(`Dyslexia-friendly font ${this.settings.dyslexiaFont ? 'enabled' : 'disabled'}`);
});
document.getElementById('toggle-cursor').addEventListener('click', () => {
this.settings.largeCursor = !this.settings.largeCursor;
this.toggleLargeCursor(this.settings.largeCursor);
this.saveSettings();
this.announceChange(`Large cursor ${this.settings.largeCursor ? 'enabled' : 'disabled'}`);
});
document.getElementById('toggle-keyboard-nav').addEventListener('click', () => {
this.settings.keyboardNav = !this.settings.keyboardNav;
this.toggleKeyboardNavigation(this.settings.keyboardNav);
this.saveSettings();
this.announceChange(`Keyboard navigation indicators ${this.settings.keyboardNav ? 'enabled' : 'disabled'}`);
});
document.getElementById('reset-accessibility').addEventListener('click', () => {
this.resetAllSettings();
this.announceChange('All accessibility settings reset to default');
});
}
toggleHighContrast(enable) {
if (enable) {
document.body.classList.add('high-contrast');
document.body.classList.add('accessibility-focus');
} else {
document.body.classList.remove('high-contrast');
document.body.classList.remove('accessibility-focus');
}
}
changeFontSize(direction) {
const sizes = ['small', 'normal', 'large', 'extra-large'];
const currentIndex = sizes.indexOf(this.settings.fontSize);
let newIndex;
if (direction === 'increase' && currentIndex < sizes.length - 1) {
newIndex = currentIndex + 1;
} else if (direction === 'decrease' && currentIndex > 0) {
newIndex = currentIndex - 1;
} else {
return; // No change needed
}
document.body.classList.remove(`font-size-${this.settings.fontSize}`);
this.settings.fontSize = sizes[newIndex];
document.body.classList.add(`font-size-${this.settings.fontSize}`);
this.saveSettings();
this.announceChange(`Font size changed to ${this.settings.fontSize}`);
}
toggleReducedMotion(enable) {
if (enable) {
document.body.classList.add('reduced-motion');
} else {
document.body.classList.remove('reduced-motion');
}
}
toggleDyslexiaFont(enable) {
if (enable) {
document.body.classList.add('dyslexia-font');
} else {
document.body.classList.remove('dyslexia-font');
}
}
toggleLargeCursor(enable) {
if (enable) {
document.body.classList.add('large-cursor');
} else {
document.body.classList.remove('large-cursor');
}
}
toggleKeyboardNavigation(enable) {
if (enable) {
document.body.classList.add('keyboard-nav-visible');
} else {
document.body.classList.remove('keyboard-nav-visible');
}
}
setupKeyboardNavigation() {
document.addEventListener('keydown', (e) => {
if (e.key === 'Tab') {
document.body.classList.add('keyboard-nav-visible');
}
if (e.key === 'Escape') {
const modals = document.querySelectorAll('.modal.show');
modals.forEach(modal => {
const closeBtn = modal.querySelector('[data-bs-dismiss="modal"]');
if (closeBtn) closeBtn.click();
});
}
if (e.altKey && e.key === 'ArrowUp') {
e.preventDefault();
this.focusPreviousElement();
}
if (e.altKey && e.key === 'ArrowDown') {
e.preventDefault();
this.focusNextElement();
}
});
document.addEventListener('mousedown', () => {
document.body.classList.remove('keyboard-nav-visible');
});
}
setupScreenReaderSupport() {
this.addSkipLinks();
this.enhanceWithARIA();
this.createLiveRegion();
this.addLandmarkRoles();
}
addSkipLinks() {
const skipLinks = document.createElement('div');
skipLinks.innerHTML = `
<a href="#main-content" class="skip-link sr-only-focusable">Skip to main content</a>
<a href="#navigation" class="skip-link sr-only-focusable">Skip to navigation</a>
<a href="#footer" class="skip-link sr-only-focusable">Skip to footer</a>
`;
document.body.insertBefore(skipLinks, document.body.firstChild);
}
enhanceWithARIA() {
const iconButtons = document.querySelectorAll('button .fas, button .far, button .fab');
iconButtons.forEach(icon => {
const button = icon.parentElement&&.parentElement.querySelector('button');
if (!button.getAttribute('aria-label') && !button.textContent.trim()) {
const iconClass = Array.from(icon.classList).find(cls => cls.startsWith('fa-'));
if (iconClass) {
const label = this.getIconLabel(iconClass);
button.setAttribute('aria-label', label);
}
}
});
const tables = document.querySelectorAll('table');
tables.forEach(table => {
if (!table.getAttribute('role')) {
table.setAttribute('role', 'table');
}
if (!table.getAttribute('aria-label')) {
const caption = table.querySelector('caption');
const heading = table.parentElement&&.parentElement.querySelector('.card')?.querySelector('.card-header h5');
if (caption) {
table.setAttribute('aria-label', caption.textContent);
} else if (heading) {
table.setAttribute('aria-label', heading.textContent + ' data table');
}
}
});
const formControls = document.querySelectorAll('input, select, textarea');
formControls.forEach(control => {
if (!control.getAttribute('aria-label') && !control.getAttribute('aria-labelledby')) {
const label = control.parentElement&&.parentElement.querySelector('.form-group')?.querySelector('label');
if (label && !label.getAttribute('for')) {
const id = control.id || `input-${Math.random().toString(36).substr(2, 9)}`;
control.id = id;
label.setAttribute('for', id);
}
}
});
}
createLiveRegion() {
const liveRegion = document.createElement('div');
liveRegion.id = 'aria-live-region';
liveRegion.setAttribute('aria-live', 'polite');
liveRegion.setAttribute('aria-atomic', 'true');
liveRegion.className = 'sr-only';
document.body.appendChild(liveRegion);
}
addLandmarkRoles() {
const main = document.querySelector('main') || document.querySelector('[role="main"]');
if (!main) {
const container = document.querySelector('.container, .container-fluid');
if (container && !container.parentElement&&.parentElement.querySelector('nav, header, footer')) {
container.setAttribute('role', 'main');
container.id = 'main-content';
}
}
const navs = document.querySelectorAll('nav');
navs.forEach((nav, index) => {
if (!nav.getAttribute('aria-label')) {
nav.setAttribute('aria-label', index === 0 ? 'Main navigation' : `Navigation ${index + 1}`);
}
});
}
getIconLabel(iconClass) {
const iconLabels = {
'fa-home': 'Home',
'fa-user': 'User',
'fa-cog': 'Settings',
'fa-search': 'Search',
'fa-plus': 'Add',
'fa-minus': 'Remove',
'fa-edit': 'Edit',
'fa-trash': 'Delete',
'fa-save': 'Save',
'fa-cancel': 'Cancel',
'fa-close': 'Close',
'fa-menu': 'Menu',
'fa-bars': 'Menu',
'fa-download': 'Download',
'fa-upload': 'Upload',
'fa-refresh': 'Refresh',
'fa-sync': 'Sync',
'fa-arrow-left': 'Back',
'fa-arrow-right': 'Forward',
'fa-truck': 'Fleet',
'fa-map-marker-alt': 'Location',
'fa-clock': 'Time',
'fa-dollar-sign': 'Cost'
};
return iconLabels[iconClass] || 'Button';
}
announceChange(message) {
const liveRegion = document.getElementById('aria-live-region');
if (liveRegion) {
liveRegion.textContent = message;
}
}
focusNextElement() {
const focusableElements = this.getFocusableElements();
const currentIndex = focusableElements.indexOf(document.activeElement);
const nextIndex = (currentIndex + 1) % focusableElements.length;
focusableElements[nextIndex].focus();
}
focusPreviousElement() {
const focusableElements = this.getFocusableElements();
const currentIndex = focusableElements.indexOf(document.activeElement);
const prevIndex = currentIndex === 0 ? focusableElements.length - 1 : currentIndex - 1;
focusableElements[prevIndex].focus();
}
getFocusableElements() {
return Array.from(document.querySelectorAll(
'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
)).filter(el => {
return el.offsetWidth > 0 && el.offsetHeight > 0;
});
}
saveSettings() {
localStorage.setItem('traxovo-accessibility-settings', JSON.stringify(this.settings));
}
loadSettings() {
const saved = localStorage.getItem('traxovo-accessibility-settings');
if (saved) {
this.settings = { ...this.settings, ...JSON.parse(saved) };
this.applySettings();
}
}
applySettings() {
this.toggleHighContrast(this.settings.highContrast);
this.toggleReducedMotion(this.settings.reducedMotion);
this.toggleDyslexiaFont(this.settings.dyslexiaFont);
this.toggleLargeCursor(this.settings.largeCursor);
this.toggleKeyboardNavigation(this.settings.keyboardNav);
document.body.classList.add(`font-size-${this.settings.fontSize}`);
}
resetAllSettings() {
document.body.classList.remove(
'high-contrast', 'accessibility-focus', 'reduced-motion',
'dyslexia-font', 'large-cursor', 'keyboard-nav-visible',
'font-size-small', 'font-size-normal', 'font-size-large', 'font-size-extra-large'
);
this.settings = {
highContrast: false,
fontSize: 'normal',
reducedMotion: false,
keyboardNav: false,
dyslexiaFont: false,
largeCursor: false
};
document.body.classList.add('font-size-normal');
this.saveSettings();
}
}
document.addEventListener('DOMContentLoaded', () => {
window.traxovoAccessibility = new TRAXOVOAccessibility();
});
window.toggleAccessibilityFeature = (feature, state) => {
if (window.traxovoAccessibility) {
switch (feature) {
case 'highContrast':
window.traxovoAccessibility.settings.highContrast = state;
window.traxovoAccessibility.toggleHighContrast(state);
break;
case 'reducedMotion':
window.traxovoAccessibility.settings.reducedMotion = state;
window.traxovoAccessibility.toggleReducedMotion(state);
break;
}
window.traxovoAccessibility.saveSettings();
}
};
if ('Notification' in window) {
if (Notification.permission !== 'granted') {
Notification.requestPermission();
}
}
function notifyUser(message) {
if ('Notification' in window) {
new Notification('TRAXOVO Update', { body: message });
} else {
alert(message);
}
}
notifyUser('Dynamic content updated');