* TRAXOVO Employee Ideas Widget
* Floating idea submission available on every page
*/
class TRAXOVOIdeasWidget {
constructor() {
this.isVisible = false;
this.init();
}
init() {
this.createWidget();
this.attachEventListeners();
}
createWidget() {
const widget = document.createElement('div');
widget.id = 'traxovo-ideas-widget';
widget.innerHTML = `
<div class="ideas-fab" title="Submit an idea">
<i class="fas fa-lightbulb"></i>
</div>
<div class="ideas-panel" style="display: none;">
<div class="ideas-header">
<h4>💡 Share Your Ideas</h4>
<button class="close-ideas" title="Close">×</button>
</div>
<div class="ideas-form">
<input type="text" id="quick-idea-title" placeholder="Idea title..." maxlength="100">
<textarea id="quick-idea-description" placeholder="Describe your idea..." rows="3"></textarea>
<select id="quick-idea-category">
<option value="ui_ux">UI/UX Improvement</option>
<option value="fleet_management">Fleet Management</option>
<option value="billing_finance">Billing & Finance</option>
<option value="attendance_workforce">Attendance & Workforce</option>
<option value="reporting_analytics">Reporting & Analytics</option>
<option value="general">General</option>
</select>
<div class="form-row">
<input type="text" id="quick-idea-name" placeholder="Your name (optional)" style="width: 48%;">
<select id="quick-idea-priority" style="width: 48%;">
<option value="medium">Medium Priority</option>
<option value="high">High Priority</option>
<option value="low">Low Priority</option>
</select>
</div>
<button class="submit-quick-idea">Submit Idea</button>
</div>
<div class="ideas-success" style="display: none;">
<i class="fas fa-check-circle"></i>
<p>Thank you! Your idea has been submitted.</p>
</div>
</div>
`;
const style = document.createElement('style');
style.textContent = `
#traxovo-ideas-widget {
position: fixed;
bottom: 20px;
right: 20px;
z-index: 1000;
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.ideas-fab {
width: 56px;
height: 56px;
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
border-radius: 50%;
display: flex;
align-items: center;
justify-content: center;
cursor: pointer;
box-shadow: 0 4px 12px rgba(0,0,0,0.2);
color: white;
font-size: 24px;
transition: all 0.3s ease;
}
.ideas-fab:hover {
transform: scale(1.1);
box-shadow: 0 6px 20px rgba(0,0,0,0.3);
}
.ideas-panel {
position: absolute;
bottom: 70px;
right: 0;
width: 320px;
background: white;
border-radius: 12px;
box-shadow: 0 8px 32px rgba(0,0,0,0.2);
overflow: hidden;
transform: translateY(20px);
opacity: 0;
transition: all 0.3s ease;
}
.ideas-panel.visible {
transform: translateY(0);
opacity: 1;
}
.ideas-header {
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
padding: 16px;
display: flex;
justify-content: space-between;
align-items: center;
}
.ideas-header h4 {
margin: 0;
font-size: 16px;
font-weight: 600;
}
.close-ideas {
background: none;
border: none;
color: white;
font-size: 20px;
cursor: pointer;
padding: 0;
width: 24px;
height: 24px;
display: flex;
align-items: center;
justify-content: center;
}
.ideas-form {
padding: 20px;
}
.ideas-form input,
.ideas-form textarea,
.ideas-form select {
width: 100%;
margin-bottom: 12px;
padding: 10px;
border: 2px solid #e1e5e9;
border-radius: 6px;
font-size: 14px;
font-family: inherit;
box-sizing: border-box;
}
.ideas-form input:focus,
.ideas-form textarea:focus,
.ideas-form select:focus {
outline: none;
border-color: #667eea;
}
.form-row {
display: flex;
gap: 8px;
}
.submit-quick-idea {
width: 100%;
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
border: none;
padding: 12px;
border-radius: 6px;
font-weight: 600;
cursor: pointer;
transition: opacity 0.2s ease;
}
.submit-quick-idea:hover {
opacity: 0.9;
}
.ideas-success {
padding: 20px;
text-align: center;
color: #22c55e;
}
.ideas-success i {
font-size: 48px;
margin-bottom: 12px;
}
.ideas-success p {
margin: 0;
font-weight: 500;
}
@media (max-width: 768px) {
.ideas-panel {
width: 280px;
right: -10px;
}
}
`;
document.head.appendChild(style);
document.body.appendChild(widget);
}
attachEventListeners() {
const fab = document.querySelector('.ideas-fab');
const panel = document.querySelector('.ideas-panel');
const closeBtn = document.querySelector('.close-ideas');
const submitBtn = document.querySelector('.submit-quick-idea');
fab.addEventListener('click', () => this.togglePanel());
closeBtn.addEventListener('click', () => this.hidePanel());
submitBtn.addEventListener('click', () => this.submitIdea());
document.addEventListener('click', (e) => {
if (!document.getElementById('traxovo-ideas-widget').contains(e.target)) {
this.hidePanel();
}
});
}
togglePanel() {
const panel = document.querySelector('.ideas-panel');
if (this.isVisible) {
this.hidePanel();
} else {
this.showPanel();
}
}
showPanel() {
const panel = document.querySelector('.ideas-panel');
panel.style.display = 'block';
setTimeout(() => {
panel.classList.add('visible');
}, 10);
this.isVisible = true;
}
hidePanel() {
const panel = document.querySelector('.ideas-panel');
panel.classList.remove('visible');
setTimeout(() => {
panel.style.display = 'none';
}, 300);
this.isVisible = false;
}
async submitIdea() {
const title = document.getElementById('quick-idea-title').value.trim();
const description = document.getElementById('quick-idea-description').value.trim();
const category = document.getElementById('quick-idea-category').value;
const name = document.getElementById('quick-idea-name').value.trim();
const priority = document.getElementById('quick-idea-priority').value;
if (!title || !description) {
alert('Please fill in the title and description');
return;
}
const ideaData = {
title,
description,
category,
priority,
employee_name: name || 'Anonymous',
module: this.getCurrentModule(),
page_url: window.location.pathname
};
try {
const response = await fetch('/api/submit-idea', {
method: 'POST',
headers: {
'Content-Type': 'application/json',
},
body: JSON.stringify(ideaData)
});
if (response.ok) {
this.showSuccess();
this.clearForm();
} else {
alert('Failed to submit idea. Please try again.');
}
} catch (error) {
console.error('Error submitting idea:', error);
alert('Error submitting idea. Please try again.');
}
}
getCurrentModule() {
const path = window.location.pathname;
const moduleMap = {
'/enhanced-dashboard': 'Executive Dashboard',
'/fleet-map': 'Fleet Map & GPS Tracking',
'/billing-consolidation': 'Billing & Financial Analysis',
'/attendance-matrix': 'Attendance & Workforce',
'/asset-manager': 'Asset Management',
'/predictive-dashboard': 'Predictive Analytics',
'/project-accountability': 'Project Accountability',
'/cost-simulator': 'Cost Savings Tools'
};
return moduleMap[path] || 'General';
}
showSuccess() {
const form = document.querySelector('.ideas-form');
const success = document.querySelector('.ideas-success');
form.style.display = 'none';
success.style.display = 'block';
setTimeout(() => {
form.style.display = 'block';
success.style.display = 'none';
this.hidePanel();
}, 2000);
}
clearForm() {
document.getElementById('quick-idea-title').value = '';
document.getElementById('quick-idea-description').value = '';
document.getElementById('quick-idea-category').value = 'ui_ux';
document.getElementById('quick-idea-priority').value = 'medium';
}
}
document.addEventListener('DOMContentLoaded', () => {
new TRAXOVOIdeasWidget();
});