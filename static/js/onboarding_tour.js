* TRAXOVO Quick Onboarding Tour
* Interactive guided tour for new users
*/
class OnboardingTour {
constructor() {
this.currentStep = 0;
this.tourSteps = [
{
target: '.dashboard-header',
title: 'Welcome to TRAXOVO',
content: 'Your comprehensive fleet management intelligence platform. This dashboard shows real-time data from your 717 assets worth $1.88M.',
position: 'bottom'
},
{
target: '.metric-card:first-child',
title: 'Total Assets',
content: 'Track your complete fleet inventory. Currently showing 717 total assets from your Foundation registry.',
position: 'bottom'
},
{
target: '.metric-card:nth-child(2)',
title: 'Active Assets',
content: 'Monitor equipment currently deployed. Your utilization rate is 91.7% with 614 active assets.',
position: 'bottom'
},
{
target: '.metric-card:nth-child(3)',
title: 'Revenue Tracking',
content: 'View monthly revenue from billable assets. Current revenue: $847.2K from Foundation accounting data.',
position: 'bottom'
},
{
target: '[href="/attendance"]',
title: 'Driver Management',
content: 'Access comprehensive driver attendance tracking for your 92 drivers. Monitor late starts, early ends, and no-shows.',
position: 'right'
},
{
target: '[href="/asset-manager"]',
title: 'Asset Manager',
content: 'Manage your entire equipment fleet. Track maintenance, utilization, and profitability by asset.',
position: 'right'
},
{
target: '[href="/fleet-map"]',
title: 'Fleet Tracking',
content: 'Real-time GPS tracking of your assets. Monitor location, geofences, and job site assignments.',
position: 'right'
},
{
target: '[href="/billing"]',
title: 'Billing Intelligence',
content: 'Revenue analytics using authentic Foundation cost data. Track profitability and billing accuracy.',
position: 'right'
},
{
target: '[href="/executive-reports"]',
title: 'Executive Reports',
content: 'VP and Controller-ready reports with KPI dashboards and exportable analytics.',
position: 'right'
}
];
this.overlay = null;
this.tooltip = null;
}
start() {
if (localStorage.getItem('traxovo_tour_completed') === 'true') {
return;
}
this.createOverlay();
this.showStep(0);
this.trackEvent('tour_started');
}
createOverlay() {
this.overlay = document.createElement('div');
this.overlay.className = 'tour-overlay';
this.overlay.innerHTML = `
<div class="tour-backdrop"></div>
`;
document.body.appendChild(this.overlay);
this.tooltip = document.createElement('div');
this.tooltip.className = 'tour-tooltip';
document.body.appendChild(this.tooltip);
}
showStep(stepIndex) {
if (stepIndex >= this.tourSteps.length) {
this.completeTour();
return;
}
this.currentStep = stepIndex;
const step = this.tourSteps[stepIndex];
const target = document.querySelector(step.target);
if (!target) {
this.showStep(stepIndex + 1);
return;
}
this.highlightElement(target);
this.showTooltip(step, target);
this.trackEvent('tour_step_viewed', { step: stepIndex + 1 });
}
highlightElement(element) {
document.querySelectorAll('.tour-highlight').forEach(el => {
el.classList.remove('tour-highlight');
});
element.classList.add('tour-highlight');
element.scrollIntoView({ behavior: 'smooth', block: 'center' });
}
showTooltip(step, target) {
const rect = target.getBoundingClientRect();
const tooltip = this.tooltip;
tooltip.innerHTML = `
<div class="tour-tooltip-content">
<div class="tour-tooltip-header">
<h4>${step.title}</h4>
<span class="tour-step-counter">${this.currentStep + 1} of ${this.tourSteps.length}</span>
</div>
<div class="tour-tooltip-body">
<p>${step.content}</p>
</div>
<div class="tour-tooltip-actions">
<button class="btn btn-outline-secondary btn-sm" onclick="tour.skip()">Skip Tour</button>
${this.currentStep > 0 ? '<button class="btn btn-outline-primary btn-sm" onclick="tour.previousStep()">Previous</button>' : ''}
<button class="btn btn-primary btn-sm" onclick="tour.nextStep()">
${this.currentStep === this.tourSteps.length - 1 ? 'Finish' : 'Next'}
</button>
</div>
</div>
`;
this.positionTooltip(tooltip, target, step.position);
tooltip.style.display = 'block';
}
positionTooltip(tooltip, target, position) {
const rect = target.getBoundingClientRect();
const tooltipRect = tooltip.getBoundingClientRect();
let top, left;
switch (position) {
case 'bottom':
top = rect.bottom + 10;
left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
break;
case 'top':
top = rect.top - tooltipRect.height - 10;
left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
break;
case 'right':
top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
left = rect.right + 10;
break;
case 'left':
top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
left = rect.left - tooltipRect.width - 10;
break;
default:
top = rect.bottom + 10;
left = rect.left;
}
const maxLeft = window.innerWidth - tooltipRect.width - 20;
const maxTop = window.innerHeight - tooltipRect.height - 20;
left = Math.max(20, Math.min(left, maxLeft));
top = Math.max(20, Math.min(top, maxTop));
tooltip.style.top = `${top + window.scrollY}px`;
tooltip.style.left = `${left}px`;
}
nextStep() {
this.showStep(this.currentStep + 1);
}
previousStep() {
if (this.currentStep > 0) {
this.showStep(this.currentStep - 1);
}
}
skip() {
this.trackEvent('tour_skipped', { step: this.currentStep + 1 });
this.completeTour();
}
completeTour() {
document.querySelectorAll('.tour-highlight').forEach(el => {
el.classList.remove('tour-highlight');
});
if (this.overlay) {
this.overlay.remove();
}
if (this.tooltip) {
this.tooltip.remove();
}
localStorage.setItem('traxovo_tour_completed', 'true');
this.showCompletionMessage();
this.trackEvent('tour_completed');
}
showCompletionMessage() {
const message = document.createElement('div');
message.className = 'tour-completion-message';
message.innerHTML = `
<div class="alert alert-success alert-dismissible fade show" role="alert">
<h5><i class="fas fa-check-circle"></i> Welcome to TRAXOVO!</h5>
<p>You're ready to manage your fleet with real-time intelligence. Explore the features and contact support if you need assistance.</p>
<button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>
`;
document.querySelector('.main-content').insertBefore(message, document.querySelector('.main-content').firstChild);
setTimeout(() => {
if (message.parentNode) {
message.remove();
}
}, 5000);
}
reset() {
localStorage.removeItem('traxovo_tour_completed');
location.reload();
}
trackEvent(eventName, data = {}) {
try {
if (typeof gtag !== 'undefined') {
gtag('event', eventName, {
event_category: 'onboarding',
...data
});
}
console.log('Tour Event:', eventName, data);
} catch (e) {
}
}
}
let tour;
document.addEventListener('DOMContentLoaded', function() {
tour = new OnboardingTour();
if (document.querySelector('.dashboard-header')) {
setTimeout(() => tour.start(), 1000);
}
});
window.startTour = function() {
if (tour) {
tour.reset();
}
};
window.tour = tour;