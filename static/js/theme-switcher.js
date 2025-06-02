* TRAXORA Theme Switcher
*
* This module manages the theme switching between light and dark modes.
* It remembers user preferences and applies appropriate Bootstrap theme classes.
*/
class ThemeSwitcher {
constructor() {
this.currentTheme = this.loadSavedTheme() || 'dark';
this.init();
}
init() {
this.applyTheme(this.currentTheme);
document.addEventListener('click', (e) => {
if (e.target && (e.target.id === 'theme-toggle' || e.target.parentElement && e.target.parentElement.id === 'theme-toggle')) {
this.toggleTheme();
}
});
document.addEventListener('keydown', (e) => {
if (e.altKey && e.key === 't') {
e.preventDefault();
this.toggleTheme();
}
});
}
loadSavedTheme() {
return localStorage.getItem('traxora_theme');
}
saveTheme(theme) {
localStorage.setItem('traxora_theme', theme);
}
toggleTheme() {
const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
this.applyTheme(newTheme);
this.saveTheme(newTheme);
this.currentTheme = newTheme;
this.showThemeToggleFeedback();
document.dispatchEvent(new CustomEvent('themeChanged', {
detail: { theme: newTheme }
}));
}
applyTheme(theme) {
document.documentElement.setAttribute('data-bs-theme', theme);
const toggleButton = document.getElementById('theme-toggle');
if (toggleButton) {
if (theme === 'dark') {
toggleButton.innerHTML = '<i class="bi bi-sun-fill"></i>';
toggleButton.setAttribute('title', 'Switch to Light Mode');
toggleButton.classList.remove('btn-dark');
toggleButton.classList.add('btn-light');
} else {
toggleButton.innerHTML = '<i class="bi bi-moon-fill"></i>';
toggleButton.setAttribute('title', 'Switch to Dark Mode');
toggleButton.classList.remove('btn-light');
toggleButton.classList.add('btn-dark');
}
}
}
showThemeToggleFeedback() {
if (typeof showFeedback === 'function') {
const themeText = this.currentTheme === 'light' ? 'Dark' : 'Light';
showFeedback('Theme Changed', `Switched to ${themeText} Mode`, 'info');
}
}
getTheme() {
return this.currentTheme;
}
}
document.addEventListener('DOMContentLoaded', function() {
if (!document.getElementById('theme-toggle')) {
const navbar = document.querySelector('.navbar-nav.ms-auto');
if (navbar) {
const themeToggleLi = document.createElement('li');
themeToggleLi.className = 'nav-item mx-2 d-flex align-items-center';
const themeToggleBtn = document.createElement('button');
themeToggleBtn.id = 'theme-toggle';
themeToggleBtn.className = 'btn btn-sm btn-light rounded-circle';
themeToggleBtn.style.width = '38px';
themeToggleBtn.style.height = '38px';
themeToggleBtn.innerHTML = '<i class="bi bi-sun-fill"></i>';
themeToggleBtn.setAttribute('title', 'Switch to Light Mode');
themeToggleLi.appendChild(themeToggleBtn);
navbar.insertBefore(themeToggleLi, navbar.firstChild);
}
}
window.themeSwitcher = new ThemeSwitcher();
});