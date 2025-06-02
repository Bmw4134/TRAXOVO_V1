document.addEventListener('DOMContentLoaded', function() {
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
tooltipTriggerList.map(function(tooltipTriggerEl) {
return new bootstrap.Tooltip(tooltipTriggerEl);
});
const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
popoverTriggerList.map(function(popoverTriggerEl) {
return new bootstrap.Popover(popoverTriggerEl);
});
setTimeout(function() {
const alerts = document.querySelectorAll('.alert-auto-dismiss');
alerts.forEach(function(alert) {
const bsAlert = new bootstrap.Alert(alert);
bsAlert.close();
});
}, 5000);
const dataTables = document.querySelectorAll('.data-table');
if (dataTables.length > 0 && typeof $.fn.DataTable !== 'undefined') {
dataTables.forEach(function(table) {
$(table).DataTable({
responsive: true,
pageLength: 25
});
});
}
const fileInputs = document.querySelectorAll('.file-upload-input');
if (fileInputs.length > 0) {
handleFileUploads(fileInputs);
}
const forms = document.querySelectorAll('.needs-validation');
Array.from(forms).forEach(form => {
form.addEventListener('submit', event => {
if (!form.checkValidity()) {
event.preventDefault();
event.stopPropagation();
}
form.classList.add('was-validated');
}, false);
});
});
function handleFileUploads(fileInputs) {
fileInputs.forEach(function(input) {
const wrapper = input.parentElement;
while (wrapper && !wrapper.classList.contains('file-upload-wrapper')) {
    wrapper = wrapper.parentElement;
}
const fileDisplay = wrapper ? wrapper.querySelector('.file-display') : null;
const dropZone = wrapper;
input.addEventListener('change', function() {
if (input.files.length > 0) {
const file = input.files[0];
let sizeStr = '';
if (file.size < 1024) {
sizeStr = file.size + ' bytes';
} else if (file.size < 1024 * 1024) {
sizeStr = (file.size / 1024).toFixed(1) + ' KB';
} else {
sizeStr = (file.size / (1024 * 1024)).toFixed(1) + ' MB';
}
if (fileDisplay) {
fileDisplay.innerHTML = `
<div class="selected-file">
<div class="file-icon">
<i class="bi bi-file-earmark"></i>
</div>
<div class="file-info">
<div class="file-name">${file.name}</div>
<div class="file-size text-muted">${sizeStr}</div>
</div>
<button type="button" class="btn-close remove-file" aria-label="Remove file"></button>
</div>
`;
const removeBtn = fileDisplay.querySelector('.remove-file');
if (removeBtn) {
removeBtn.addEventListener('click', function(e) {
e.preventDefault();
input.value = '';
fileDisplay.innerHTML = '<div class="placeholder">No file selected</div>';
});
}
}
} else if (fileDisplay) {
fileDisplay.innerHTML = '<div class="placeholder">No file selected</div>';
}
});
if (dropZone) {
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
dropZone.addEventListener(eventName, preventDefaults, false);
});
function preventDefaults(e) {
e.preventDefault();
e.stopPropagation();
}
['dragenter', 'dragover'].forEach(eventName => {
dropZone.addEventListener(eventName, highlight, false);
});
['dragleave', 'drop'].forEach(eventName => {
dropZone.addEventListener(eventName, unhighlight, false);
});
function highlight() {
dropZone.classList.add('active');
}
function unhighlight() {
dropZone.classList.remove('active');
}
dropZone.addEventListener('drop', handleDrop, false);
function handleDrop(e) {
const dt = e.dataTransfer;
const files = dt.files;
input.files = files;
input.dispatchEvent(new Event('change'));
}
}
});
}
function formatNumber(num) {
return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
}
function formatDate(dateStr) {
const date = new Date(dateStr);
return date.toLocaleDateString('en-US', {
year: 'numeric',
month: 'short',
day: 'numeric'
});
}
function formatDateTime(dateStr) {
const date = new Date(dateStr);
return date.toLocaleDateString('en-US', {
year: 'numeric',
month: 'short',
day: 'numeric',
hour: '2-digit',
minute: '2-digit'
});
}
function toggleVisibility(elementId) {
const element = document.getElementById(elementId);
if (element) {
element.classList.toggle('d-none');
}
}
function confirmAction(message, callback) {
if (confirm(message)) {
callback();
}
}
function createChart(canvasId, type, data, options) {
if (typeof Chart === 'undefined') {
console.error('Chart.js not loaded');
return;
}
const ctx = document.getElementById(canvasId);
if (!ctx) {
console.error('Canvas element not found: ' + canvasId);
return;
}
return new Chart(ctx, {
type: type,
data: data,
options: options
});
}
function showLoading(containerId, message = 'Loading...') {
const container = document.getElementById(containerId);
if (container) {
container.innerHTML = `
<div class="text-center py-5">
<div class="spinner-border text-primary mb-3" role="status">
<span class="visually-hidden">Loading...</span>
</div>
<p>${message}</p>
</div>
`;
}
}
function hideLoading(containerId, content) {
const container = document.getElementById(containerId);
if (container) {
container.innerHTML = content;
}
}
function ajaxRequest(url, method, data, successCallback, errorCallback) {
const xhr = new XMLHttpRequest();
xhr.open(method, url, true);
xhr.setRequestHeader('Content-Type', 'application/json');
xhr.onload = function() {
if (xhr.status >= 200 && xhr.status < 300) {
try {
const response = JSON.parse(xhr.responseText);
successCallback(response);
} catch (e) {
successCallback(xhr.responseText);
}
} else {
errorCallback('Request failed with status ' + xhr.status);
}
};
xhr.onerror = function() {
errorCallback('Network error occurred');
};
xhr.send(JSON.stringify(data));
}
function showNotification(message, type = 'info') {
const notification = document.createElement('div');
notification.className = `toast align-items-center text-white bg-${type} border-0`;
notification.setAttribute('role', 'alert');
notification.setAttribute('aria-live', 'assertive');
notification.setAttribute('aria-atomic', 'true');
notification.innerHTML = `
<div class="d-flex">
<div class="toast-body">
${message}
</div>
<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
</div>
`;
const toastContainer = document.querySelector('.toast-container');
if (!toastContainer) {
const newContainer = document.createElement('div');
newContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
document.body.appendChild(newContainer);
newContainer.appendChild(notification);
} else {
toastContainer.appendChild(notification);
}
const toast = new bootstrap.Toast(notification);
toast.show();
setTimeout(function() {
notification.remove();
}, 5000);
}