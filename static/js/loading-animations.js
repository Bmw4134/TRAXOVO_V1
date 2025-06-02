/** TRAXORA Loading Animations
* Construction-themed animated loading indicators
*/
const loaderTypes = [
'excavator',
'bulldozer',
'crane',
'roadroller',
'mixer',
'progress-construction',
'hardhat-spinner'
];
* Create and show a construction-themed loader
*
* @param {string} containerId - ID of the container element to append loader to
* @param {string} type - Type of loader animation (excavator, bulldozer, etc.)
* @param {string} message - Message to display below the loader
* @param {boolean} fadeIn - Whether to fade in the loader
* @returns {void}
*/
function showLoader(containerId, type = 'excavator', message = 'Loading...', fadeIn = true) {
const container = document.getElementById(containerId);
if (!container) {
console.warn(`Container with ID '${containerId}' not found.`);
return;
}
container.innerHTML = '';
const loaderContainer = document.createElement('div');
loaderContainer.className = 'loader-container';
if (fadeIn) {
loaderContainer.classList.add('fade-in');
}
let loader;
switch (type) {
case 'excavator':
loader = createExcavatorLoader();
break;
case 'bulldozer':
loader = createBulldozerLoader();
break;
case 'crane':
loader = createCraneLoader();
break;
case 'roadroller':
loader = createRoadRollerLoader();
break;
case 'mixer':
loader = createMixerLoader();
break;
case 'progress-construction':
loader = createProgressConstructionLoader();
break;
case 'hardhat-spinner':
loader = createHardhatSpinner();
break;
default:
loader = createExcavatorLoader();
break;
}
const messageElement = document.createElement('div');
messageElement.className = 'loader-message';
messageElement.textContent = message;
if (message.endsWith('...')) {
messageElement.classList.add('loading-dots');
messageElement.textContent = message.substring(0, message.length - 3);
}
loaderContainer.appendChild(loader);
loaderContainer.appendChild(messageElement);
container.appendChild(loaderContainer);
}
* Hide the loader from a container
*
* @param {string} containerId - ID of the container element
* @returns {void}
*/
function hideLoader(containerId) {
const container = document.getElementById(containerId);
if (!container) {
console.warn(`Container with ID '${containerId}' not found.`);
return;
}
const loaderContainer = container.querySelector('.loader-container');
if (loaderContainer) {
loaderContainer.remove();
}
}
* Get a random loader type
*
* @returns {string} Random loader type
*/
function getRandomLoaderType() {
const randomIndex = Math.floor(Math.random() * loaderTypes.length);
return loaderTypes[randomIndex];
}
function createExcavatorLoader() {
const excavator = document.createElement('div');
excavator.className = 'excavator-loader';
const body = document.createElement('div');
body.className = 'excavator-body';
const cabin = document.createElement('div');
cabin.className = 'excavator-cabin';
const arm = document.createElement('div');
arm.className = 'excavator-arm';
const bucket = document.createElement('div');
bucket.className = 'excavator-bucket';
const track = document.createElement('div');
track.className = 'excavator-track';
arm.appendChild(bucket);
excavator.appendChild(body);
excavator.appendChild(cabin);
excavator.appendChild(arm);
excavator.appendChild(track);
return excavator;
}
function createBulldozerLoader() {
const bulldozer = document.createElement('div');
bulldozer.className = 'bulldozer-loader';
const body = document.createElement('div');
body.className = 'bulldozer-body';
const cabin = document.createElement('div');
cabin.className = 'bulldozer-cabin';
const blade = document.createElement('div');
blade.className = 'bulldozer-blade';
const tracks = document.createElement('div');
tracks.className = 'bulldozer-tracks';
bulldozer.appendChild(body);
bulldozer.appendChild(cabin);
bulldozer.appendChild(blade);
bulldozer.appendChild(tracks);
return bulldozer;
}
function createCraneLoader() {
const crane = document.createElement('div');
crane.className = 'crane-loader';
const base = document.createElement('div');
base.className = 'crane-base';
const cabin = document.createElement('div');
cabin.className = 'crane-cabin';
const arm = document.createElement('div');
arm.className = 'crane-arm';
const hook = document.createElement('div');
hook.className = 'crane-hook';
const load = document.createElement('div');
load.className = 'crane-load';
hook.appendChild(load);
arm.appendChild(hook);
crane.appendChild(base);
crane.appendChild(cabin);
crane.appendChild(arm);
return crane;
}
function createRoadRollerLoader() {
const roadroller = document.createElement('div');
roadroller.className = 'roadroller-loader';
const body = document.createElement('div');
body.className = 'roadroller-body';
const cabin = document.createElement('div');
cabin.className = 'roadroller-cabin';
const roller = document.createElement('div');
roller.className = 'roadroller-roller';
roadroller.appendChild(body);
roadroller.appendChild(cabin);
roadroller.appendChild(roller);
return roadroller;
}
function createMixerLoader() {
const mixer = document.createElement('div');
mixer.className = 'mixer-loader';
const body = document.createElement('div');
body.className = 'mixer-body';
const cabin = document.createElement('div');
cabin.className = 'mixer-cabin';
const drum = document.createElement('div');
drum.className = 'mixer-drum';
const wheels = document.createElement('div');
wheels.className = 'mixer-wheels';
for (let i = 0; i < 3; i++) {
const wheel = document.createElement('div');
wheel.className = 'mixer-wheel';
wheels.appendChild(wheel);
}
mixer.appendChild(body);
mixer.appendChild(cabin);
mixer.appendChild(drum);
mixer.appendChild(wheels);
return mixer;
}
function createProgressConstructionLoader() {
const progress = document.createElement('div');
progress.className = 'progress-construction';
const foundation = document.createElement('div');
foundation.className = 'progress-foundation';
const building = document.createElement('div');
building.className = 'progress-building';
progress.appendChild(foundation);
progress.appendChild(building);
return progress;
}
function createHardhatSpinner() {
const spinner = document.createElement('div');
spinner.className = 'hardhat-spinner';
return spinner;
}
* Replace all loading placeholder elements with animated loaders
* Looks for elements with class "loading-placeholder" and data-loader-type attribute
*/
function initializeLoaders() {
const placeholders = document.querySelectorAll('.loading-placeholder');
placeholders.forEach(placeholder => {
const containerId = placeholder.id;
const loaderType = placeholder.dataset.loaderType || getRandomLoaderType();
const message = placeholder.dataset.loaderMessage || 'Loading...';
showLoader(containerId, loaderType, message);
});
}
* Add loading animation to buttons that trigger server actions
* Looks for buttons with class "loading-button"
*/
function initializeLoadingButtons() {
const buttons = document.querySelectorAll('.loading-button');
buttons.forEach(button => {
button.addEventListener('click', function(e) {
if (this.disabled) {
return;
}
const originalContent = this.innerHTML;
const loadingText = this.dataset.loadingText || 'Processing...';
const loaderType = this.dataset.loaderType || 'hardhat-spinner';
const targetForm = this.dataset.targetForm;
if (targetForm) {
const form = document.getElementById(targetForm);
if (form && form.checkValidity() === false) {
form.reportValidity();
e.preventDefault();
return;
}
}
const loader = document.createElement('span');
loader.className = 'spinner-border spinner-border-sm me-2';
loader.setAttribute('role', 'status');
loader.setAttribute('aria-hidden', 'true');
this.disabled = true;
this.innerHTML = '';
this.appendChild(loader);
this.innerHTML += ` ${loadingText}`;
this.dataset.originalContent = originalContent;
});
});
}
* Initialize all loading effects and animations when DOM is loaded
*/
document.addEventListener('DOMContentLoaded', function() {
initializeLoaders();
initializeLoadingButtons();
if (typeof $ !== 'undefined') {
$(document).ajaxStart(function() {
if (document.getElementById('global-loader')) {
showLoader('global-loader', getRandomLoaderType(), 'Loading data...');
}
});
$(document).ajaxStop(function() {
if (document.getElementById('global-loader')) {
hideLoader('global-loader');
}
});
}
});
window.showLoader = showLoader;
window.hideLoader = hideLoader;
window.getRandomLoaderType = getRandomLoaderType;